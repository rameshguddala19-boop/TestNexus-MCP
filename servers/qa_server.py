from mcp.server.mcpserver import MCPServer

mcp = MCPServer("TestNexus QA Server")


@mcp.tool()
def format_bug_report(
    title: str,
    description: str,
    severity: str = "Medium",
    priority: str = "Medium",
) -> str:
    """Create a professional QA bug report from the provided details."""

    return f"""
BUG REPORT
==========

Title: {title}

Description:
{description}

Severity: {severity}
Priority: {priority}

Suggested Sections:
- Environment
- Steps to Reproduce
- Expected Result
- Actual Result
- Evidence / Screenshots
- Logs
- Additional Notes
"""


@mcp.tool()
def generate_test_case(
    feature: str,
    scenario: str,
) -> str:
    """Generate a structured manual test case for a feature."""

    return f"""
TEST CASE
=========

Feature: {feature}
Scenario: {scenario}

Test Case ID: TC-{feature.upper().replace(" ", "-")}

Preconditions:
- Application is available
- Required test data is available
- User has the required access

Test Steps:
1. Open the application.
2. Navigate to the {feature} feature.
3. Perform the following scenario:
   {scenario}
4. Observe the application behavior.

Expected Result:
The application should behave according to the expected business
requirement for the scenario.

Test Data:
- Valid data
- Invalid data
- Boundary values

Status:
Not Executed
"""


@mcp.tool()
def generate_test_scenarios(
    feature: str,
) -> str:
    """Generate positive, negative, boundary, and security test scenarios."""

    return f"""
TEST SCENARIOS
==============

Feature: {feature}

Positive Scenarios:
1. Verify {feature} with valid input.
2. Verify successful execution of {feature}.
3. Verify expected result with normal data.

Negative Scenarios:
4. Verify {feature} with invalid input.
5. Verify behavior when required input is missing.
6. Verify proper error handling.

Boundary Scenarios:
7. Verify minimum allowed value.
8. Verify maximum allowed value.
9. Verify values just below and above the boundary.

Security Scenarios:
10. Verify unauthorized access is rejected.
11. Verify invalid authentication is handled safely.
12. Verify user input is validated properly.
"""


@mcp.tool()
def qa_checklist(
    project_type: str = "Web Application",
) -> str:
    """Return a comprehensive QA checklist for a project type."""

    return f"""
QA CHECKLIST
============

Project Type: {project_type}

Functional Testing
[ ] Requirements verified
[ ] Positive scenarios tested
[ ] Negative scenarios tested
[ ] Boundary conditions tested

UI Testing
[ ] Layout verified
[ ] Buttons and links verified
[ ] Forms validated
[ ] Error messages verified

API Testing
[ ] Status codes verified
[ ] Request validation verified
[ ] Response validation verified
[ ] Authentication verified

Compatibility
[ ] Chrome tested
[ ] Edge tested
[ ] Firefox tested
[ ] Responsive behavior tested

Regression
[ ] Existing functionality verified
[ ] Fixed defects retested
[ ] Regression suite executed

Release Readiness
[ ] Critical defects closed
[ ] Test execution completed
[ ] Regression completed
[ ] Final QA sign-off completed
"""


if __name__ == "__main__":
    mcp.run()