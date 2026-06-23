Feature: Disaster Resource Orchestration
  As an emergency response coordinator
  I want the orchestrator agent to automatically assess disasters and propose resources
  So that I can approve deployments via a Vibe Diff

  Scenario: A flood is reported in Sector 4
    Given a disaster report is received for "Flood" at "Sector 4"
    And the report contains PII "Contact reporter John Doe at 555-0199"
    When the Context Hygiene middleware processes the request
    Then the PII should be masked to "Contact reporter [REDACTED_NAME] at [REDACTED_PHONE]"
    When the Orchestrator queries the MCP Server
    Then the MCP Server should return "Heavy Rain, 45mph winds" for weather
    And the MCP Server should return "Route 4 Blocked, Highway 9 Clear" for traffic
    When the Orchestrator delegates to the Medical Agent and Shelter Agent
    Then the system should generate a Vibe Diff containing the proposed actions
    And the system should require Cryptographic MFA before execution
