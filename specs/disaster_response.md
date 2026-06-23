# Disaster Response API & Agent Specifications

This document acts as the single source of truth for the Agent's architectural integrity, following the Spec-Driven Development (SDD) principles from Day 5.

## 1. Domain Agent Delegation Protocol

The Orchestrator agent delegates tasks to domain-specific agents using the following payload schema. Complex nested structures are defined in YAML below to prevent agent hallucination.

```yaml
schema_version: "1.0"
domain_agents:
  MedicalAgent:
    input_schema:
      type: object
      properties:
        event_type: { type: string }
        location: { type: string }
        affected_population_estimate: { type: integer }
    expected_output:
      type: object
      properties:
        kits_required: { type: integer }
        personnel: { type: integer }
        priority: { type: string, enum: ["Low", "Medium", "High", "Critical"] }
  ShelterAgent:
    input_schema:
      type: object
      properties:
        location: { type: string }
        weather_conditions: { type: string }
        evacuees_estimate: { type: integer }
    expected_output:
      type: object
      properties:
        evacuation_center: { type: string }
        route: { type: string }
        capacity: { type: integer }
```

## 2. Context Hygiene (PII Masking)

All incoming requests to the orchestrator MUST pass through the Context Resolver. The Context Resolver ensures zero-trust development by sanitizing personal information before it enters the agent's context window.

*   **Social Security Numbers** must be replaced with `[REDACTED_SSN]`
*   **Phone Numbers** must be replaced with `[REDACTED_PHONE]`
*   **Names** (if flagged by NER) must be replaced with `[REDACTED_NAME]`
