---
name: evacuation-routing-planner
description: Determines the optimal evacuation center and safe routes based on weather and traffic context.
---

# Evacuation Routing Skill

## Purpose
This skill gives the Shelter Domain Agent the logic required to assign evacuation centers and find safe routes, bypassing blocked roads.

## Procedural Rules
1. **Shelter Assignment:**
   - If `evacuees_estimate` > 400: Assign "Downtown Community Hub" (Capacity: 500).
   - If `evacuees_estimate` <= 400: Assign "North Ridge School" (Capacity: 400).
2. **Route Calculation:**
   - Always evaluate the MCP Server's `traffic` payload. 
   - If a route (e.g., "Route 4") is marked as "Blocked", you MUST calculate an alternative route (e.g., "Highway 9") and explicitly state `(Avoiding blocked Route X)`.
3. **Data Contract:** You must return the output matching the `ShelterAgent` expected_output schema defined in `specs/disaster_response.md`.
