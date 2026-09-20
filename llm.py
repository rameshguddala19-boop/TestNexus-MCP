import json
import os
from copy import deepcopy

from dotenv import load_dotenv
from openai import OpenAI

from mcp_manager import list_tools, call_tool


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are TestNexus MCP, an AI-powered QA assistant.

Available MCP servers:
- QA
- RAG
- Jira
- Gmail

Rules:

- Use RAG tools for document questions.
- For document questions, answer ONLY from information returned by the RAG tools.
- Do NOT use general knowledge to answer document questions.
- Do NOT add information that is not present in the uploaded documents.
- Do NOT guess or assume missing information.
- If the RAG results do not contain enough information to answer the question, say:
  "I couldn't find this information in the uploaded documents."
- Never invent tool results.

- Use QA tools for QA tasks.
- Use Jira tools for Jira requests.
- Use Gmail tools for email requests.

- Use only ONE tool call per model turn.
- For real-world write actions, wait for human approval.

Jira create issue rules:
- project_key is required.
- summary is required.
- issue_type is required.
- If priority is requested, put it inside additional_fields.
- additional_fields must be a JSON string.
- Example:
  {"priority": {"name": "High"}}
"""


# ============================================================
# TOOLS REQUIRING HUMAN APPROVAL
# ============================================================

CONFIRMATION_TOOLS = {
    "jira_create_issue",
    "jira_update_issue",
    "jira_add_comment",
    "jira_transition_issue",
}


def needs_confirmation(tool_name):
    return (
        tool_name in CONFIRMATION_TOOLS
        or tool_name.startswith("gmail_send")
    )


# ============================================================
# JIRA ARGUMENT NORMALIZATION
# ============================================================

def normalize_tool_arguments(
    tool_name,
    arguments,
):

    arguments = dict(arguments)

    if tool_name != "jira_create_issue":
        return arguments

    # --------------------------------------------------------
    # Priority should be inside additional_fields
    # --------------------------------------------------------

    priority = arguments.pop(
        "priority",
        None,
    )

    additional_fields = arguments.get(
        "additional_fields"
    )

    # Convert dictionary -> JSON string
    if isinstance(
        additional_fields,
        dict,
    ):
        additional_fields = json.dumps(
            additional_fields
        )

    # Convert JSON string -> dictionary temporarily
    if isinstance(
        additional_fields,
        str,
    ):
        try:
            additional_fields_dict = json.loads(
                additional_fields
            )

            if not isinstance(
                additional_fields_dict,
                dict,
            ):
                additional_fields_dict = {}

        except json.JSONDecodeError:
            additional_fields_dict = {}

    else:
        additional_fields_dict = {}

    # Add priority if model supplied it separately
    if priority:

        if isinstance(
            priority,
            str,
        ):
            additional_fields_dict[
                "priority"
            ] = {
                "name": priority
            }

        elif isinstance(
            priority,
            dict,
        ):
            additional_fields_dict[
                "priority"
            ] = priority

    # Put back as JSON STRING because
    # mcp-atlassian expects JSON string.
    if additional_fields_dict:
        arguments[
            "additional_fields"
        ] = json.dumps(
            additional_fields_dict
        )

    elif "additional_fields" in arguments:
        arguments[
            "additional_fields"
        ] = "{}"

    return arguments


# ============================================================
# OPENAI TOOL DEFINITIONS
# ============================================================

def get_openai_tools():

    mcp_tools = list_tools()

    tools = []

    for tool in mcp_tools:

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": (
                        tool["description"]
                        or ""
                    ),
                    "parameters": (
                        tool["input_schema"]
                    ),
                },
            }
        )

    return tools


# ============================================================
# ASSISTANT MESSAGE SERIALIZATION
# ============================================================

def assistant_message_to_dict(
    assistant_message
):
    """
    Build an explicit assistant message containing
    the exact tool_calls returned by OpenAI.

    This is important because the next role='tool'
    message must directly follow this message.
    """

    message = {
        "role": "assistant",
        "content": assistant_message.content,
    }

    if assistant_message.tool_calls:

        message["tool_calls"] = []

        for tool_call in (
            assistant_message.tool_calls
        ):

            message["tool_calls"].append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": (
                            tool_call.function.name
                        ),
                        "arguments": (
                            tool_call.function.arguments
                            or "{}"
                        ),
                    },
                }
            )

    return message


# ============================================================
# SERIALIZE TOOL RESULT
# ============================================================

def serialize_result(result):

    if isinstance(
        result,
        (dict, list),
    ):

        return json.dumps(
            result,
            ensure_ascii=False,
        )

    return str(result)


# ============================================================
# CONTINUE AGENT
# ============================================================

def _continue_agent(
    messages,
    max_steps=8,
    current_step=0,
):

    tools = get_openai_tools()

    for step in range(
        current_step,
        max_steps,
    ):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,

            # Force sequential tool calling.
            parallel_tool_calls=False,
        )

        assistant_message = (
            response.choices[0].message
        )

        # ----------------------------------------------------
        # FINAL ANSWER
        # ----------------------------------------------------

        if not assistant_message.tool_calls:

            return {
                "status": "success",
                "answer": (
                    assistant_message.content
                    or ""
                ),
                "steps": step,
            }

        # ----------------------------------------------------
        # EXACT ASSISTANT TOOL-CALL MESSAGE
        # ----------------------------------------------------

        assistant_dict = (
            assistant_message_to_dict(
                assistant_message
            )
        )

        # ----------------------------------------------------
        # Process one tool call
        # ----------------------------------------------------

        tool_call = (
            assistant_message.tool_calls[0]
        )

        tool_name = (
            tool_call.function.name
        )

        raw_arguments = (
            tool_call.function.arguments
            or "{}"
        )

        try:

            arguments = json.loads(
                raw_arguments
            )

        except json.JSONDecodeError:

            arguments = {}

        arguments = normalize_tool_arguments(
            tool_name,
            arguments,
        )

        # ----------------------------------------------------
        # HUMAN APPROVAL REQUIRED
        # ----------------------------------------------------

        if needs_confirmation(
            tool_name
        ):

            return {
                "status": "pending_confirmation",

                # IMPORTANT:
                # Keep messages BEFORE assistant tool call.
                "messages_before_tool_call": (
                    deepcopy(messages)
                ),

                # Save exact assistant tool-call message.
                "assistant_message": (
                    assistant_dict
                ),

                "tool_name": tool_name,

                "arguments": arguments,

                "tool_call_id": (
                    tool_call.id
                ),

                "steps": step,
            }

        # ----------------------------------------------------
        # SAFE TOOL
        # ----------------------------------------------------

        messages.append(
            assistant_dict
        )

        try:

            result = call_tool(
                tool_name,
                arguments,
            )

            tool_result = (
                serialize_result(
                    result
                )
            )

        except Exception as error:

            tool_result = (
                f"Tool execution failed: "
                f"{error}"
            )

        # Tool message DIRECTLY follows assistant tool_calls
        messages.append(
            {
                "role": "tool",
                "tool_call_id": (
                    tool_call.id
                ),
                "content": tool_result,
            }
        )

    return {
        "status": "error",
        "answer": (
            "The agent reached the maximum "
            "number of tool-calling steps."
        ),
        "steps": max_steps,
    }


# ============================================================
# START AGENT
# ============================================================

def run_agent(
    user_prompt,
    max_steps=8,
):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    return _continue_agent(
        messages,
        max_steps=max_steps,
        current_step=0,
    )


# ============================================================
# RESUME AFTER APPROVAL
# ============================================================

def resume_agent(
    pending_state,
    approved,
    max_steps=8,
):

    # Start with messages BEFORE the tool call
    messages = deepcopy(
        pending_state[
            "messages_before_tool_call"
        ]
    )

    # Restore exact assistant tool-call message
    assistant_message = deepcopy(
        pending_state[
            "assistant_message"
        ]
    )

    messages.append(
        assistant_message
    )

    tool_name = pending_state[
        "tool_name"
    ]

    arguments = pending_state[
        "arguments"
    ]

    tool_call_id = pending_state[
        "tool_call_id"
    ]

    current_step = pending_state.get(
        "steps",
        0,
    )

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    if approved:

        try:

            result = call_tool(
                tool_name,
                arguments,
            )

            tool_result = (
                serialize_result(
                    result
                )
            )

        except Exception as error:

            tool_result = (
                f"Tool execution failed: "
                f"{error}"
            )

    # --------------------------------------------------------
    # CANCELLED
    # --------------------------------------------------------

    else:

        tool_result = (
            "ACTION CANCELLED BY USER. "
            "The requested action was not executed."
        )

    # --------------------------------------------------------
    # IMPORTANT:
    # Tool response immediately follows
    # assistant tool_calls.
    # --------------------------------------------------------

    messages.append(
        {
            "role": "tool",
            "tool_call_id": (
                tool_call_id
            ),
            "content": tool_result,
        }
    )

    # Continue the agent loop
    return _continue_agent(
        messages,
        max_steps=max_steps,
        current_step=current_step + 1,
    )


# ============================================================
# SIMPLE HELPER
# ============================================================

def ask(prompt):

    result = run_agent(
        prompt
    )

    return result.get(
        "answer",
        "",
    )