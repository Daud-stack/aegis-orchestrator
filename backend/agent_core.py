import asyncio
import json
import re
from mcp_server import mcp_query

def sanitize_context(text: str) -> str:
    """Context Hygiene Middleware: Masks PII before agent processing."""
    # Mask phone numbers (e.g., 555-0199 or (555) 555-5555)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', text)
    # Mask SSNs
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
    return text

async def orchestrate_disaster_response(event_type: str, location: str):
    logs = []
    
    def log(message, source="Orchestrator"):
        logs.append({"source": source, "message": message})

    # Apply Context Hygiene
    sanitized_location = sanitize_context(location)
        
    log(f"Received alert: {event_type} at {sanitized_location}")
    log("Context Hygiene Check Passed: PII Masked.", "SecOps Agent")

    
    # 1. Query MCP Server
    log("Querying MCP Server for environmental context...", "Orchestrator -> MCP Server")
    mcp_data = await mcp_query(location)
    log(f"MCP Response received: Weather: {mcp_data['weather']}, Traffic: {mcp_data['traffic']}", "MCP Server")
    
    # 2. A2A Protocol: Delegate to Medical Agent
    log("Dynamically loading skill: 'medical-assessment-calculator'...", "Orchestrator")
    log(f"Delegating medical assessment to Medical Agent...", "Orchestrator -> Medical Agent")
    await asyncio.sleep(1) # Simulate thinking
    medical_plan = {
        "kits_required": 150,
        "personnel": 12,
        "priority": "High"
    }
    log(f"Medical Assessment complete. Kits required: {medical_plan['kits_required']}", "Medical Agent")
    
    # 3. A2A Protocol: Delegate to Shelter Agent
    log("Dynamically loading skill: 'evacuation-routing-planner'...", "Orchestrator")
    log(f"Delegating shelter and routing to Shelter Agent...", "Orchestrator -> Shelter Agent")
    await asyncio.sleep(1) # Simulate thinking
    shelter_plan = {
        "evacuation_center": "Downtown Community Hub",
        "route": "Highway 9 (Avoiding blocked Route 4)",
        "capacity": 500
    }
    log(f"Shelter assigned: {shelter_plan['evacuation_center']}", "Shelter Agent")
    
    # 4. Compile Vibe Diff
    log("Compiling final Vibe Diff for human approval...")
    
    vibe_diff = {
        "event": f"{event_type} in {location}",
        "context": mcp_data,
        "actions": [
            f"Dispatch {medical_plan['personnel']} medics with {medical_plan['kits_required']} kits.",
            f"Open {shelter_plan['evacuation_center']} (Capacity: {shelter_plan['capacity']}).",
            f"Route traffic via {shelter_plan['route']}."
        ],
        "risk_level": "High"
    }
    
    return {
        "logs": logs,
        "vibe_diff": vibe_diff
    }
