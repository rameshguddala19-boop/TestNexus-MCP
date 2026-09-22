import streamlit as st

from llm import run_agent, resume_agent
from mcp_manager import list_tools, server_status


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TestNexus MCP",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

if "recent_activity" not in st.session_state:
    st.session_state.recent_activity = []


# ============================================================
# PROFESSIONAL THEME
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .stApp {
        background-color: #f8fafc;
    }

    h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
        letter-spacing: -0.7px;
    }

    h2, h3 {
        color: #0f172a !important;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 12px !important;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800 !important;
    }

    div.stButton > button {
        min-height: 42px;
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid #dbe3ec;
        background-color: #ffffff;
    }

    div.stButton > button:hover {
        border-color: #64748b;
    }

    div[data-testid="stChatMessage"] {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        background-color: #ffffff;
        margin-bottom: 10px;
    }

    div[data-testid="stChatMessage"] p {
        line-height: 1.65;
    }

    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
    }

    section[data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    section[data-testid="stSidebar"] .stCaption {
        color: #94a3b8 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMetric"] {
        background-color: #172033;
        border-color: #26334a;
    }

    section[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SERVER DEFINITIONS
# ============================================================

SERVERS = [
    ("🧪", "QA", "qa", "QA testing and test generation"),
    ("📚", "RAG", "rag", "Document search and retrieval"),
    ("📌", "Jira", "jira", "Jira issue management"),
    ("✉️", "Gmail", "gmail", "Email operations"),
]


# ============================================================
# MCP STATUS
# ============================================================

try:
    statuses = server_status()
except Exception:
    statuses = {
        "qa": "not configured",
        "rag": "not configured",
        "jira": "not configured",
        "gmail": "not configured",
    }


try:
    tools = list_tools()
except Exception:
    tools = []


def get_tool_count(server_key):
    return sum(
        1
        for tool in tools
        if tool.get("server") == server_key
    )


ready_servers = sum(
    1
    for _, _, key, _ in SERVERS
    if statuses.get(key) == "ready"
)

total_tools = len(tools)


# ============================================================
# HELPERS
# ============================================================

def add_message(role, content):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
        }
    )


def add_activity(message, icon="🔹"):
    st.session_state.recent_activity.insert(
        0,
        {
            "message": message,
            "icon": icon,
        },
    )

    st.session_state.recent_activity = (
        st.session_state.recent_activity[:8]
    )


def execute_agent(prompt):
    """
    Run a user request through the TestNexus AI agent.
    """

    add_message(
        "user",
        prompt,
    )

    try:

        result = run_agent(prompt)

        if result.get("status") == "pending_confirmation":

            st.session_state.pending_action = result

            add_activity(
                "Action waiting for human approval",
                "⚠️",
            )

            return

        answer = result.get(
            "answer",
            "No answer returned.",
        )

        add_message(
            "assistant",
            answer,
        )

        add_activity(
            "Agent completed the request",
            "✅",
        )

    except Exception as error:

        add_message(
            "assistant",
            f"Agent execution failed: {error}",
        )

        add_activity(
            "Agent request failed",
            "❌",
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🧪 TestNexus MCP"
    )

    st.caption(
        "AI-powered QA & automation assistant"
    )

    st.divider()

    st.markdown(
        "### 🔌 Connected Servers"
    )

    for icon, name, key, description in SERVERS:

        ready = statuses.get(key) == "ready"

        count = get_tool_count(key)

        with st.container(border=True):

            st.markdown(
                f"**{icon} {name}**"
            )

            st.caption(
                description
            )

            if ready:
                st.success("Ready")
            else:
                st.warning("Not configured")

            st.caption(
                f"{count} tools available"
            )

    st.divider()

    st.markdown(
        "### 📊 System Overview"
    )

    side_col1, side_col2 = st.columns(2)

    with side_col1:

        st.metric(
            "Servers",
            f"{ready_servers}/4",
        )

    with side_col2:

        st.metric(
            "Tools",
            total_tools,
        )

    st.caption(
        "Human approval is enabled for real-world write actions."
    )

    st.divider()

    st.markdown(
        "### 🛠 Tool Registry"
    )

    grouped_tools = {}

    for tool in tools:

        server_name = tool.get(
            "server",
            "unknown",
        )

        grouped_tools.setdefault(
            server_name,
            [],
        ).append(
            tool.get(
                "name",
                "unknown",
            )
        )

    if grouped_tools:

        for server_name, tool_names in grouped_tools.items():

            with st.expander(
                f"{server_name.upper()} · {len(tool_names)} tools"
            ):

                for tool_name in tool_names:

                    st.caption(
                        f"• {tool_name}"
                    )

    else:

        st.caption(
            "No MCP tools available."
        )

    st.divider()

    st.caption(
        "QA • RAG • Jira • Gmail"
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "🧪 TestNexus MCP"
)

st.caption(
    "AI-powered QA & automation assistant using Model Context Protocol"
)

if ready_servers == 4:

    st.success(
        "All 4 MCP services are connected and ready."
    )

else:

    st.info(
        f"{ready_servers}/4 MCP services are currently connected."
    )


# ============================================================
# SYSTEM OVERVIEW
# ============================================================

with st.container(border=True):

    st.markdown(
        "### 🤖 One AI Agent. Multiple MCP Services."
    )

    st.caption(
        "Ask in plain English. TestNexus understands the request "
        "and selects the appropriate MCP tool."
    )

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:

        st.metric(
            "MCP Servers",
            f"{ready_servers}/4",
        )

    with metric2:

        st.metric(
            "Available Tools",
            total_tools,
        )

    with metric3:

        st.metric(
            "Approval",
            "Enabled",
        )

    with metric4:

        st.metric(
            "Agent",
            "Ready",
        )


# ============================================================
# QUICK ACTIONS
# ============================================================

st.markdown(
    "### ⚡ Quick Actions"
)

st.caption(
    "Start common QA and automation tasks."
)


QUICK_ACTIONS = [
    (
        "🐞 Bug Report",
        "Format this as a bug report: login button does nothing on Chrome, severity high",
    ),
    (
        "🧪 Test Case",
        "Generate test cases for the Login feature.",
    ),
    (
        "📚 Document Search",
        "What is the expected result for wrong credentials?",
    ),
    (
        "📌 Jira",
        "Show the latest Jira issues.",
    ),
    (
        "✉️ Gmail",
        "List my 5 most recent Gmail messages.",
    ),
]


quick_columns = st.columns(5)


for column, (label, prompt) in zip(
    quick_columns,
    QUICK_ACTIONS,
):

    with column:

        if st.button(
            label,
            use_container_width=True,
            key=f"quick_{label}",
            disabled=(
                st.session_state.pending_action is not None
            ),
        ):

            with st.spinner(
                "TestNexus is working..."
            ):

                execute_agent(prompt)

            st.rerun()


# ============================================================
# EXAMPLE PROMPTS
# ============================================================

with st.expander(
    "💡 Example Prompts",
    expanded=True,
):

    example_col1, example_col2 = st.columns(2)

    with example_col1:

        st.markdown(
            "**🐞 QA / Bug Reports**"
        )

        st.caption(
            "Format this as a bug report: "
            "login button is not working."
        )

        st.markdown(
            "**🧪 Test Cases**"
        )

        st.caption(
            "Generate test cases for the Login feature."
        )

        st.markdown(
            "**📚 RAG**"
        )

        st.caption(
            "What is the expected result for wrong credentials?"
        )

    with example_col2:

        st.markdown(
            "**📌 Jira**"
        )

        st.caption(
            "Show the latest Jira issues."
        )

        st.markdown(
            "**✉️ Gmail**"
        )

        st.caption(
            "Search my Gmail for recent QA emails."
        )

        st.markdown(
            "**🔗 Multi-server workflow**"
        )

        st.caption(
            "Find the login bug in the documents "
            "and format it as a bug report."
        )

    st.info(
        "Jira write operations and Gmail sending require human approval."
    )


# ============================================================
# WORKSPACE
# ============================================================

st.divider()

agent_column, activity_column = st.columns(
    [2.3, 1],
    gap="large",
)


# ============================================================
# AI AGENT
# ============================================================

with agent_column:

    st.markdown(
        "### 🤖 TestNexus AI Agent"
    )

    st.caption(
        "Ask questions, generate QA artifacts, search documents, "
        "work with Jira or interact with Gmail."
    )

    # --------------------------------------------------------
    # WELCOME SCREEN
    # --------------------------------------------------------

    if not st.session_state.messages:

        with st.container(border=True):

            st.markdown(
                "## 👋 Welcome to TestNexus"
            )

            st.write(
                "Your AI-powered QA assistant is ready."
            )

            st.caption(
                "Choose a quick action above or type your own request below."
            )

            welcome1, welcome2, welcome3, welcome4 = (
                st.columns(4)
            )

            with welcome1:

                st.markdown(
                    "**🐞 QA**"
                )

                st.caption(
                    "Bug reports and test cases"
                )

            with welcome2:

                st.markdown(
                    "**📚 RAG**"
                )

                st.caption(
                    "Document questions"
                )

            with welcome3:

                st.markdown(
                    "**📌 Jira**"
                )

                st.caption(
                    "Issue operations"
                )

            with welcome4:

                st.markdown(
                    "**✉️ Gmail**"
                )

                st.caption(
                    "Email operations"
                )

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    pending = st.session_state.pending_action

    if pending is not None:

        st.warning(
            "Human approval is required before this "
            "real-world action can run."
        )

        st.markdown(
            f"**Tool:** `{pending.get('tool_name', 'unknown')}`"
        )

        with st.expander(
            "🔍 Review action details",
            expanded=True,
        ):

            st.json(
                pending.get(
                    "arguments",
                    {},
                )
            )

        approve_column, cancel_column = st.columns(2)

        with approve_column:

            approve = st.button(
                "✅ Approve Action",
                type="primary",
                use_container_width=True,
                key="approve_action",
            )

        with cancel_column:

            cancel = st.button(
                "❌ Cancel Action",
                use_container_width=True,
                key="cancel_action",
            )

        if approve or cancel:

            with st.spinner(
                "Processing action..."
            ):

                result = resume_agent(
                    pending,
                    approved=approve,
                )

            st.session_state.pending_action = None

            if (
                result.get("status")
                == "pending_confirmation"
            ):

                st.session_state.pending_action = result

                add_activity(
                    "Another action requires approval",
                    "⚠️",
                )

            else:

                answer = result.get(
                    "answer",
                    "No answer returned.",
                )

                add_message(
                    "assistant",
                    answer,
                )

                if approve:

                    add_activity(
                        "Approved action completed",
                        "✅",
                    )

                else:

                    add_activity(
                        "Action cancelled",
                        "🛑",
                    )

            st.rerun()

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    user_prompt = st.chat_input(
        "Ask TestNexus about QA, documents, Jira or Gmail...",
        disabled=(
            st.session_state.pending_action is not None
        ),
    )

    if user_prompt:

        with st.spinner(
            "TestNexus Agent is thinking..."
        ):

            execute_agent(
                user_prompt
            )

        st.rerun()


# ============================================================
# RECENT ACTIVITY
# ============================================================

with activity_column:

    st.markdown(
        "### 🛠 Recent Activity"
    )

    st.caption(
        "Latest actions performed by TestNexus."
    )

    if st.session_state.recent_activity:

        for activity in st.session_state.recent_activity:

            with st.container(
                border=True
            ):

                st.write(
                    f"{activity['icon']} "
                    f"{activity['message']}"
                )

    else:

        with st.container(
            border=True
        ):

            st.caption(
                "No activity yet."
            )

            st.caption(
                "Completed MCP actions will appear here."
            )

    st.markdown(
        "### 🔐 Safety"
    )

    with st.container(
        border=True
    ):

        st.success(
            "Human approval enabled"
        )

        st.caption(
            "Real-world Jira and Gmail write actions "
            "are paused until approval."
        )


# ============================================================
# PLATFORM CAPABILITIES
# ============================================================

st.divider()

st.markdown(
    "### 🚀 Platform Capabilities"
)

st.caption(
    "TestNexus combines four MCP services through one AI agent."
)


capability_columns = st.columns(4)


CAPABILITIES = [
    (
        "🐞 QA Automation",
        "Generate bug reports, test cases, "
        "test scenarios and QA checklists.",
    ),
    (
        "📚 Document Intelligence",
        "Search indexed documents and "
        "answer questions using RAG.",
    ),
    (
        "📌 Jira Integration",
        "Search, read, create, update, "
        "comment and transition Jira issues.",
    ),
    (
        "✉️ Gmail Integration",
        "Search, read, draft, send and "
        "manage Gmail messages.",
    ),
]


for column, (title, description) in zip(
    capability_columns,
    CAPABILITIES,
):

    with column:

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{title}**"
            )

            st.caption(
                description
            )


# ============================================================
# ARCHITECTURE
# ============================================================

with st.expander(
    "🏗️ How TestNexus Works"
):

    st.code(
        """QA Tester
    ↓
TestNexus AI Agent
    ↓
Model Context Protocol
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│   QA    │   RAG   │  Jira   │  Gmail  │
└─────────┴─────────┴─────────┴─────────┘
    ↓
Correct MCP Tool
    ↓
Result
    ↓
QA Tester""",
        language="text",
    )

    st.caption(
        "MCP connects the AI agent with the tools exposed by each server."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "TestNexus MCP • OpenAI Agent • Model Context Protocol • "
    "QA • RAG • Jira • Gmail"
)