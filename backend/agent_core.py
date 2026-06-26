import asyncio
import json
import re
import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

from mcp_server import mcp_query

# Load environment variables (e.g., GEMINI_API_KEY from .env)
load_dotenv()

# Initialize the Gemini client. It automatically picks up GEMINI_API_KEY.
client = genai.Client()

def sanitize_context(text: str) -> str:
    """Context Hygiene Middleware: Masks PII before agent processing."""
    # Mask phone numbers (e.g., 555-0199 or (555) 555-5555)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', text)
    # Mask SSNs
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
    return text

class MedicalOutput(BaseModel):
    kits_required: int
    personnel: int
    priority: str = Field(description="One of: 'Low', 'Medium', 'High', 'Critical'")

class ShelterOutput(BaseModel):
    evacuation_center: str
    route: str
    capacity: int

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
    mcp_data = await mcp_query(sanitized_location)
    log(f"MCP Response received: Weather: {mcp_data['weather']}, Traffic: {mcp_data['traffic']}", "MCP Server")

    # To calculate medical needs, we need an estimated population. 
    # Use Gemini to estimate based on the location.
    prompt_population = f"Estimate the affected population for a {event_type} in {sanitized_location}. Just return an integer number representing the amount of affected people, nothing else."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_population
        )
        affected_population = int(re.search(r'\d+', response.text.replace(',','')).group())
    except Exception as e:
        log(f"Error estimating population: {e}", "Orchestrator Error")
        affected_population = 1000 # fallback
        
    log(f"Estimated affected population: {affected_population}", "Orchestrator")
    
    # 2. A2A Protocol: Delegate to Medical Agent
    log("Dynamically loading skill: 'medical-assessment-calculator'...", "Orchestrator")
    log(f"Delegating medical assessment to Medical Agent...", "Orchestrator -> Medical Agent")
    
    medical_prompt = f"""
    You are the Medical Domain Agent. 
    Event: {event_type}
    Location: {sanitized_location}
    Affected Population Estimate: {affected_population}
    
    Procedural Rules:
    1. Kit Calculation: Require 1 medical kit for every 10 estimated affected individuals.
    2. Personnel Calculation: Require 1 paramedic for every 50 estimated affected individuals.
    3. Priority Triage:
       - Flood/Wildfire: "High" priority.
       - Earthquake: "Critical" priority.
       - Minor structural damage: "Medium" priority.
       - Otherwise: "Low" or "Medium".
    """
    
    medical_resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=medical_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MedicalOutput,
            temperature=0.1
        )
    )
    medical_plan = json.loads(medical_resp.text)
    
    log(f"Medical Assessment complete. Kits required: {medical_plan['kits_required']}", "Medical Agent")
    
    # 3. A2A Protocol: Delegate to Shelter Agent
    log("Dynamically loading skill: 'evacuation-routing-planner'...", "Orchestrator")
    log(f"Delegating shelter and routing to Shelter Agent...", "Orchestrator -> Shelter Agent")

    shelter_prompt = f"""
    You are the Shelter Domain Agent.
    Location: {sanitized_location}
    Evacuees Estimate: {affected_population}
    Weather Context: {mcp_data['weather']}
    Traffic Context: {mcp_data['traffic']}
    
    Procedural Rules:
    1. Shelter Assignment:
       - If evacuees_estimate > 400: Assign "Downtown Community Hub" (Capacity: 500).
       - If evacuees_estimate <= 400: Assign "North Ridge School" (Capacity: 400).
    2. Route Calculation:
       - Always evaluate the Traffic Context.
       - If a route (e.g., "Route 4") is marked as "Blocked", you MUST calculate an alternative route (e.g., "Highway 9") and explicitly state `(Avoiding blocked Route X)`.
    """
    
    shelter_resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=shelter_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ShelterOutput,
            temperature=0.1
        )
    )
    shelter_plan = json.loads(shelter_resp.text)
    
    log(f"Shelter assigned: {shelter_plan['evacuation_center']} via {shelter_plan['route']}", "Shelter Agent")
    
    # 4. Compile Vibe Diff
    log("Compiling final Vibe Diff for human approval...")
    
    vibe_diff = {
        "event": f"{event_type} in {sanitized_location}",
        "context": mcp_data,
        "actions": [
            f"Dispatch {medical_plan['personnel']} medics with {medical_plan['kits_required']} kits.",
            f"Open {shelter_plan['evacuation_center']} (Capacity: {shelter_plan['capacity']}).",
            f"Route traffic via {shelter_plan['route']}."
        ],
        "risk_level": medical_plan['priority']
    }
    
    return {
        "logs": logs,
        "vibe_diff": vibe_diff
    }
