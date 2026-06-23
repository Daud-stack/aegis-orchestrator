---
name: medical-assessment-calculator
description: Calculates required medical kits, personnel, and priority based on disaster population and event type.
---

# Medical Assessment Skill

## Purpose
This skill provides the Medical Domain Agent with the exact procedural memory required to calculate medical logistics during a disaster. 
By utilizing progressive disclosure, the main Orchestrator Agent only loads this logic when a medical assessment is required, reducing token context rot.

## Procedural Rules
1. **Kit Calculation:** Require 1 medical kit for every 10 estimated affected individuals.
2. **Personnel Calculation:** Require 1 paramedic for every 50 estimated affected individuals.
3. **Priority Triage:** 
   - Flood/Wildfire: "High" priority.
   - Earthquake: "Critical" priority.
   - Minor structural damage: "Medium" priority.
4. **Data Contract:** You must return the output matching the `MedicalAgent` expected_output schema defined in `specs/disaster_response.md`.
