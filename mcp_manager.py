import asyncio
import json
import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client, StdioServerParameters


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config" / "servers.json"


# Load .env
load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# LOAD SERVER CONFIGURATION
# ============================================================

def load_config():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# ENVIRONMENT VARIABLE EXPANSION
# ============================================================

def expand_env(value):
    """
    Convert:
        ${OPENAI_API_KEY}

    into the actual environment value.
    """

    if not isinstance(value, str):
        return value

    pattern = r"\$\{([^}]+)\}"

    def replace(match):
        variable_name = match.group(1)

        return os.getenv(
            variable_name,
            "",
        )

    return re.sub(
        pattern,
        replace,
        value,
    )


# ============================================================
# GET SERVER CONFIG
# ============================================================

def get_server_config(server_name):

    config = load_config()

    if server_name not in config:
        raise ValueError(
            f"Unknown MCP server: {server_name}"
        )

    return config[server_name]


# ============================================================
# CHECK COMMAND
# ============================================================

def command_available(command):

    if command == "python":
        return True

    return shutil.which(command) is not None


# ============================================================
# CHECK SERVER READINESS
# ============================================================

def is_server_ready(server_name):

    config = get_server_config(
        server_name
    )

    command = config.get(
        "command",
        ""
    )

    # --------------------------------------------------------
    # Check executable first
    # --------------------------------------------------------

    if not command_available(command):
        return False

    # --------------------------------------------------------
    # QA / RAG
    # --------------------------------------------------------

    if server_name in (
        "qa",
        "rag",
    ):

        return bool(
            os.getenv(
                "OPENAI_API_KEY"
            )
        )

    # --------------------------------------------------------
    # JIRA
    # --------------------------------------------------------

    if server_name == "jira":

        jira_url = os.getenv(
            "JIRA_URL",
            ""
        ).strip()

        jira_username = os.getenv(
            "JIRA_USERNAME",
            ""
        ).strip()

        jira_token = os.getenv(
            "JIRA_API_TOKEN",
            ""
        ).strip()

        # Ignore placeholders
        if (
            not jira_url
            or "YOUR-" in jira_url.upper()
            or "your_jira" in jira_url.lower()
        ):
            return False

        if (
            not jira_username
            or "YOUR-" in jira_username.upper()
            or "your_" in jira_username.lower()
        ):
            return False

        if (
            not jira_token
            or "YOUR-" in jira_token.upper()
            or "your_" in jira_token.lower()
        ):
            return False

        return True

    # --------------------------------------------------------
    # GMAIL
    # --------------------------------------------------------

    if server_name == "gmail":

        credentials_path = os.getenv(
            "GMAIL_CREDENTIALS_PATH",
            ""
        ).strip()

        if not credentials_path:
            return False

        path = Path(
            credentials_path
        )

        if not path.is_absolute():
            path = (
                PROJECT_ROOT
                / path
            )

        return path.exists()

    return False


# ============================================================
# GET READY SERVERS
# ============================================================

def get_ready_servers():

    config = load_config()

    ready_servers = []

    for server_name in config:

        if is_server_ready(
            server_name
        ):
            ready_servers.append(
                server_name
            )

    return ready_servers


# ============================================================
# BUILD STDIO PARAMETERS
# ============================================================

def build_server_parameters(
    server_name
):

    server_config = get_server_config(
        server_name
    )

    command = server_config[
        "command"
    ]

    args = server_config.get(
        "args",
        [],
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Use the CURRENT virtual-environment Python
    # instead of a broken system Python path.
    # --------------------------------------------------------

    if command == "python":
        command = sys.executable

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    environment = os.environ.copy()

    configured_env = (
        server_config.get(
            "env",
            {}
        )
    )

    for key, value in (
        configured_env.items()
    ):

        environment[key] = (
            expand_env(value)
        )

    return StdioServerParameters(
        command=command,
        args=args,
        env=environment,
        cwd=str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# LIST TOOLS FROM ONE SERVER
# ============================================================

async def _list_server_tools(
    server_name
):

    parameters = (
        build_server_parameters(
            server_name
        )
    )

    async with Client(
        parameters
    ) as client:

        result = (
            await client.list_tools()
        )

        return result.tools


def list_server_tools(
    server_name
):

    return asyncio.run(
        _list_server_tools(
            server_name
        )
    )


# ============================================================
# LIST ALL AVAILABLE TOOLS
# ============================================================

def list_tools():

    all_tools = []

    ready_servers = (
        get_ready_servers()
    )

    for server_name in (
        ready_servers
    ):

        tools = (
            list_server_tools(
                server_name
            )
        )

        for tool in tools:

            all_tools.append(
                {
                    "server": server_name,
                    "name": tool.name,
                    "description": (
                        tool.description
                    ),
                    "input_schema": (
                        tool.input_schema
                    ),
                }
            )

    return all_tools


# ============================================================
# FIND SERVER FOR TOOL
# ============================================================

def find_server_for_tool(
    tool_name
):

    ready_servers = (
        get_ready_servers()
    )

    for server_name in (
        ready_servers
    ):

        tools = (
            list_server_tools(
                server_name
            )
        )

        for tool in tools:

            if tool.name == tool_name:
                return server_name

    raise ValueError(
        f"No MCP server found for tool: "
        f"{tool_name}"
    )


# ============================================================
# CALL MCP TOOL
# ============================================================

async def _call_tool(
    server_name,
    tool_name,
    arguments,
):

    parameters = (
        build_server_parameters(
            server_name
        )
    )

    async with Client(
        parameters
    ) as client:

        result = (
            await client.call_tool(
                tool_name,
                arguments=arguments,
            )
        )

        # ----------------------------------------------------
        # Text response
        # ----------------------------------------------------

        if result.content:

            text_parts = []

            for item in (
                result.content
            ):

                if hasattr(
                    item,
                    "text"
                ):

                    text_parts.append(
                        item.text
                    )

            if text_parts:

                return "\n".join(
                    text_parts
                )

        # ----------------------------------------------------
        # Structured response
        # ----------------------------------------------------

        if result.structured_content:

            return (
                result.structured_content
            )

        return str(result)


def call_tool(
    tool_name,
    arguments,
):

    server_name = (
        find_server_for_tool(
            tool_name
        )
    )

    return asyncio.run(
        _call_tool(
            server_name,
            tool_name,
            arguments,
        )
    )


# ============================================================
# SERVER STATUS
# ============================================================

def server_status():

    config = load_config()

    status = {}

    for server_name in config:

        if is_server_ready(
            server_name
        ):
            status[
                server_name
            ] = "ready"

        else:
            status[
                server_name
            ] = "not configured"

    return status