import os
import requests

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer


load_dotenv()

mcp = MCPServer("TestNexus Jira Server")


JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")


def jira_request(method, endpoint, **kwargs):
    if not JIRA_BASE_URL:
        raise ValueError("JIRA_BASE_URL is not configured")

    if not JIRA_EMAIL:
        raise ValueError("JIRA_EMAIL is not configured")

    if not JIRA_API_TOKEN:
        raise ValueError("JIRA_API_TOKEN is not configured")

    url = f"{JIRA_BASE_URL}{endpoint}"

    response = requests.request(
        method,
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30,
        **kwargs,
    )

    if not response.ok:
        raise RuntimeError(
            f"Jira API error {response.status_code}: "
            f"{response.text}"
        )

    if not response.text:
        return {}

    return response.json()


@mcp.tool()
def jira_get_issue(
    issue_key: str,
) -> str:
    """Get details of a Jira issue."""

    data = jira_request(
        "GET",
        f"/rest/api/3/issue/{issue_key}",
    )

    fields = data.get("fields", {})

    return (
        f"Issue: {data.get('key', issue_key)}\n"
        f"Summary: {fields.get('summary', '')}\n"
        f"Status: {fields.get('status', {}).get('name', '')}\n"
        f"Priority: {fields.get('priority', {}).get('name', '')}\n"
        f"Assignee: "
        f"{fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
        f"Description: {fields.get('description', '')}"
    )


@mcp.tool()
def jira_search(
    jql: str,
    max_results: int = 10,
) -> str:
    """Search Jira issues using JQL."""

    data = jira_request(
        "GET",
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": max_results,
        },
    )

    issues = data.get("issues", [])

    if not issues:
        return "No Jira issues found."

    lines = ["JIRA SEARCH RESULTS", "==================="]

    for issue in issues:
        fields = issue.get("fields", {})

        lines.append(
            f"{issue.get('key')}: "
            f"{fields.get('summary', '')} | "
            f"Status: "
            f"{fields.get('status', {}).get('name', '')}"
        )

    return "\n".join(lines)


@mcp.tool()
def jira_create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str = "Medium",
) -> str:
    """Create a Jira issue."""

    payload = {
        "fields": {
            "project": {
                "key": project_key,
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description,
                            }
                        ],
                    }
                ],
            },
            "issuetype": {
                "name": issue_type,
            },
            "priority": {
                "name": priority,
            },
        }
    }

    data = jira_request(
        "POST",
        "/rest/api/3/issue",
        json=payload,
    )

    return (
        f"Jira issue created successfully.\n"
        f"Issue Key: {data.get('key')}\n"
        f"Issue ID: {data.get('id')}"
    )


@mcp.tool()
def jira_update_issue(
    issue_key: str,
    summary: str = "",
    description: str = "",
) -> str:
    """Update an existing Jira issue."""

    fields = {}

    if summary:
        fields["summary"] = summary

    if description:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description,
                        }
                    ],
                }
            ],
        }

    if not fields:
        return "No fields were provided for update."

    jira_request(
        "PUT",
        f"/rest/api/3/issue/{issue_key}",
        json={"fields": fields},
    )

    return f"Issue {issue_key} updated successfully."


@mcp.tool()
def jira_add_comment(
    issue_key: str,
    comment: str,
) -> str:
    """Add a comment to a Jira issue."""

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment,
                        }
                    ],
                }
            ],
        }
    }

    jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/comment",
        json=payload,
    )

    return f"Comment added successfully to {issue_key}."


@mcp.tool()
def jira_transition_issue(
    issue_key: str,
    transition_id: str,
) -> str:
    """Transition a Jira issue using a transition ID."""

    payload = {
        "transition": {
            "id": transition_id,
        }
    }

    jira_request(
        "POST",
        f"/rest/api/3/issue/{issue_key}/transitions",
        json=payload,
    )

    return (
        f"Issue {issue_key} transitioned "
        f"using transition ID {transition_id}."
    )


if __name__ == "__main__":
    mcp.run()