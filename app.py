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
# PROFESSIONAL UI CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1400px;
        padding-top: 2.2rem;
        padding-bottom: 2rem;
    }

    .app-subtitle {
        color: #6b7280;
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 16px;
    }

    .section-title {
        font-size: 19px;
        font-weight: 800;
        color: #111827;
        margin-top: 4px;
        margin-bottom: 6px;
    }

    .section-subtitle {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 10px;
    }

    /* Metrics */

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 10px 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 12px !important;
    }

    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 24px !important;
        font-weight: 800 !important;
    }

    /* Buttons */

    div.stButton > button {
        min-height: 40px;
        border-radius: 9px;
        font-weight: 600;
    }

    /* Chat */

    div[data-testid="stChatMessage"] {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        margin-bottom: 8px;
    }

    /* Sidebar */

    section[data-testid="stSidebar"] {
        background: #111827 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #f9fafb !important;
    }

    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #cbd5e1 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stAlert"] p {
        color: #f9fafb !important;
    }

    section[data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"] h1,
    section[data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"] h3 {
        color: #f9fafb !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD SERVER STATUS
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


# ============================================================
# SERVER INFORMATION
# ============================================================

servers = [
    ("🧪", "QA", "qa"),
    ("📚", "RAG", "rag"),
    ("📌", "Jira", "jira"),
    ("✉️", "Gmail", "gmail"),
]


def get_tool_count(server_name):
    return sum(
        1
        for tool in tools
        if tool.get("server") == server_name
    )


ready_servers = sum(
    1
    for value in statuses.values()
    if value == "ready"
)

total_tools = len(tools)


# ============================================================
# HEADER
# ============================================================

st.title("🧪 TestNexus MCP")

st.markdown(
    """
    <div class="app-subtitle">
        AI-powered QA & automation assistant using Model Context Protocol
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONNECTED MCP SERVICES
# ============================================================

st.markdown(
    """
    <div class="section-title">
        🔌 Connected MCP Services
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-subtitle">
        QA, RAG, Jira and Gmail are connected to one AI agent.
    </div>
    """,
    unsafe_allow_html=True,
)


service_columns = st.columns(4, gap="medium")


for column, (icon, name, key) in zip(
    service_columns,
    servers,
):

    with column:

        with st.container(border=True):

            st.markdown(
                f"### {icon} {name}"
            )

            if statuses.get(key) == "ready":

                st.success(
                    "Ready",
                    icon="✅",
                )

            else:

                st.info(
                    "Not Configured",
                    icon="⚪",
                )

            st.caption(
                f"{get_tool_count(key)} tools available"
            )


# ============================================================
# TOOL SUMMARY
# ============================================================

metric1, metric2, metric3 = st.columns(
    3,
    gap="medium",
)


with metric1:

    st.metric(
        "Connected Servers",
        f"{ready_servers}/4",
    )


with metric2:

    st.metric(
        "Available Tools",
        total_tools,
    )


with metric3:

    st.metric(
        "Active Integrations",
        ready_servers,
    )


st.divider()


# ============================================================
# MAIN LAYOUT
# ============================================================

left_column, right_column = st.columns(
    [2.1, 1],
    gap="large",
)


# ============================================================
# AI AGENT
# ============================================================

with left_column:

    st.markdown(
        """
        <div class="section-title">
            🤖 TestNexus AI Agent
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-subtitle">
            Ask questions about QA, documents, Jira, or Gmail.
        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    if not st.session_state.messages:

        with st.container(border=True):

            st.markdown(
                "### 👋 Welcome to TestNexus"
            )

            st.caption(
                "Your AI agent is ready. "
                "Choose a quick action or type your own request."
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
            "⚠️ Human approval required before this action runs."
        )

        st.write(
            f"**Tool:** `{pending['tool_name']}`"
        )

        with st.expander(
            "Review action details",
            expanded=True,
        ):

            st.json(
                pending["arguments"]
            )


        approve_col, cancel_col = st.columns(2)


        with approve_col:

            approve = st.button(
                "✅ Approve",
                type="primary",
                use_container_width=True,
                key="approve_action",
            )


        with cancel_col:

            cancel = st.button(
                "❌ Cancel",
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

            else:

                answer = result.get(
                    "answer",
                    "No answer returned.",
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            st.rerun()


    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    user_prompt = st.chat_input(
        "Ask TestNexus anything..."
    )


    if (
        user_prompt
        and st.session_state.pending_action is None
    ):

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )


        with st.chat_message("user"):

            st.markdown(
                user_prompt
            )


        with st.chat_message("assistant"):

            with st.spinner(
                "TestNexus Agent is thinking..."
            ):

                try:

                    result = run_agent(
                        user_prompt
                    )


                    if (
                        result.get("status")
                        == "pending_confirmation"
                    ):

                        st.session_state.pending_action = (
                            result
                        )

                        st.rerun()


                    answer = result.get(
                        "answer",
                        "No answer returned.",
                    )


                    st.markdown(
                        answer
                    )


                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )


                except Exception as error:

                    error_message = (
                        f"Agent execution failed: {error}"
                    )

                    st.error(
                        error_message
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )


# ============================================================
# QUICK ACTIONS
# ============================================================

with right_column:

    st.markdown(
        """
        <div class="section-title">
            ⚡ Quick Actions
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-subtitle">
            Common TestNexus tasks
        </div>
        """,
        unsafe_allow_html=True,
    )


    quick_actions = [
        (
            "🐞 Bug Report",
            "Create a bug report for a login issue.",
        ),
        (
            "🧪 Test Case",
            "Generate a test case for the Login feature.",
        ),
        (
            "📚 Document Search",
            "Search the uploaded documents.",
        ),
        (
            "📌 Jira",
            "Show the latest Jira issues in project KAN.",
        ),
        (
            "✉️ Gmail",
            "List my 5 most recent Gmail messages.",
        ),
    ]


    for label, prompt in quick_actions:

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )


            try:

                result = run_agent(
                    prompt
                )


                if (
                    result.get("status")
                    == "pending_confirmation"
                ):

                    st.session_state.pending_action = (
                        result
                    )

                else:

                    answer = result.get(
                        "answer",
                        "No answer returned.",
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )


            except Exception as error:

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"Action failed: {error}"
                        ),
                    }
                )


            st.rerun()


# ============================================================
# AVAILABLE CAPABILITIES
# ============================================================

st.divider()


st.markdown(
    """
    <div class="section-title">
        🚀 Available Capabilities
    </div>
    """,
    unsafe_allow_html=True,
)


capability_columns = st.columns(
    4,
    gap="medium",
)


capabilities = [
    (
        "🐞 Bug Reports",
        "Generate structured QA bug reports.",
    ),
    (
        "🧪 Test Cases",
        "Generate detailed test cases.",
    ),
    (
        "📚 RAG Search",
        "Search uploaded PDF documents.",
    ),
    (
        "🔗 Multi-MCP Agent",
        "Use QA, RAG, Jira and Gmail together.",
    ),
]


for column, (title, description) in zip(
    capability_columns,
    capabilities,
):

    with column:

        with st.container(border=True):

            st.markdown(
                f"**{title}**"
            )

            st.caption(
                description
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🧪 TestNexus"
    )

    st.caption(
        "MCP-powered AI QA assistant"
    )


    st.divider()


    # --------------------------------------------------------
    # SERVER STATUS
    # --------------------------------------------------------

    st.markdown(
        "### Server Status"
    )


    for icon, name, key in servers:

        if statuses.get(key) == "ready":

            st.success(
                f"{icon} {name} — Ready"
            )

        else:

            st.info(
                f"{icon} {name} — Not Configured"
            )


    st.divider()


    # --------------------------------------------------------
    # TOOL SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### Tool Summary"
    )


    for icon, name, key in servers:

        st.write(
            f"{icon} {name}: **{get_tool_count(key)}**"
        )


    st.divider()


    st.caption(
        "QA • RAG • Jira • Gmail"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#9ca3af;
        font-size:12px;
        margin-top:18px;
    ">
        TestNexus MCP • OpenAI Agent • QA • RAG • Jira • Gmail
    </div>
    """,
    unsafe_allow_html=True,
)