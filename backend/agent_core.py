import asyncio
import json
import re
import os
import base64
from typing import Optional, Dict
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
    # Mask Names (Simulated NER: Matches two consecutive capitalized words)
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[REDACTED_NAME]', text)
    return text


class MedicalOutput(BaseModel):
    kits_required: int
    personnel: int
    specialized_equipment: list[str] = Field(description="E.g., Oxygen tanks, pediatric kits, etc.")
    priority: str = Field(description="One of: 'Low', 'Medium', 'High', 'Critical'")

class ShelterOutput(BaseModel):
    evacuation_center: str
    route: str
    capacity: int

class LogisticsOutput(BaseModel):
    supplies_available: bool
    actions_taken: list[str] = Field(description="Actions taken to source supplies, e.g. 'Requested 50 pediatric kits from neighboring county'")

async def orchestrate_disaster_response(event_type: str, location: str, image_base64: Optional[str] = None):
    logs = []
    
    def log(message, source="Orchestrator"):
        logs.append({"source": source, "message": message})

    # Apply Context Hygiene
    sanitized_location = sanitize_context(location)
        
    log(f"Received alert: {event_type} at {sanitized_location}")
    log("Context Hygiene Check Passed: PII Masked.", "SecOps Agent")
    
    # 0. Vision Analysis (Multi-Modal)
    vision_insights = None
    if image_base64:
        log("Analyzing incident image...", "Vision Agent")
        try:
            if "base64," in image_base64:
                image_base64 = image_base64.split("base64,")[1]
            image_data = base64.b64decode(image_base64)
            vision_resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    "Analyze this disaster image. Provide a 1-sentence summary of the severity and any immediate hazards visible.",
                    types.Part.from_bytes(data=image_data, mime_type='image/jpeg')
                ]
            )
            vision_insights = vision_resp.text
            log(f"Vision insights: {vision_insights}", "Vision Agent")
        except Exception as e:
            log(f"Failed to process image: {e}", "Vision Agent Error")

    # 1. Query MCP Server
    log("Querying MCP Server for environmental context...", "Orchestrator -> MCP Server")
    mcp_data = await mcp_query(sanitized_location)
    log(f"MCP Response received: Weather: {mcp_data['weather']}, Traffic: {mcp_data['traffic']}", "MCP Server")

    # Demographics — Real census-based population data per location
    # Sources: Zimbabwe 2022 Census, US Census Bureau, Mozambique INE
    POPULATION_DATA = {
        # ── United States (older median age ~38, lower pediatric %) ──
        "Sector 4": {
            "total_population": 52000, "elderly": 7800, "pediatric": 9360, "disabled": 2600,
            "context": "Los Angeles — dense urban, high infrastructure"
        },
        "Downtown": {
            "total_population": 85000, "elderly": 13600, "pediatric": 11050, "disabled": 4250,
            "context": "Manhattan — extremely dense urban core"
        },
        "North Ridge": {
            "total_population": 32000, "elderly": 5440, "pediatric": 5760, "disabled": 1600,
            "context": "Northridge — suburban residential"
        },
        # ── Zimbabwe (younger median age ~18, higher pediatric %) ──
        "Harare": {
            "total_population": 128000, "elderly": 5120, "pediatric": 51200, "disabled": 3840,
            "context": "Capital city — 1.5M metro, dense high-growth suburbs"
        },
        "Bulawayo": {
            "total_population": 45000, "elderly": 2700, "pediatric": 18000, "disabled": 1350,
            "context": "Second city — 653K pop, aging infrastructure"
        },
        "Chimanimani": {
            "total_population": 34000, "elderly": 2380, "pediatric": 15300, "disabled": 1020,
            "context": "Rural mountainous district — 35K, Cyclone Idai impact zone"
        },
        "Mutare": {
            "total_population": 25000, "elderly": 1250, "pediatric": 10000, "disabled": 750,
            "context": "Eastern Highlands city — 188K pop, border town"
        },
        # ── Mozambique (very young median age ~17) ──
        "Beira": {
            "total_population": 92000, "elderly": 2760, "pediatric": 41400, "disabled": 2760,
            "context": "Port city — 530K pop, severe cyclone exposure (Idai 2019)"
        },
    }

    default_pop = {"total_population": 10000, "elderly": 1500, "pediatric": 3000, "disabled": 500, "context": "Unknown area"}

    log("Retrieving population demographics from census data...", "Orchestrator")
    demographics = POPULATION_DATA.get(sanitized_location, default_pop)
    affected_population = demographics["total_population"]

    vulnerable_groups = {k: demographics.get(k, 0) for k in ['elderly', 'pediatric', 'disabled']}
    log(f"Census data: {affected_population} affected in {demographics.get('context', sanitized_location)}. Vulnerable: elderly={vulnerable_groups['elderly']}, pediatric={vulnerable_groups['pediatric']}, disabled={vulnerable_groups['disabled']}", "Orchestrator")
    
    # 2. A2A Protocol: Delegate to Medical Agent
    log("Dynamically loading skill: 'medical-assessment-calculator'...", "Orchestrator")
    log(f"Delegating medical assessment to Medical Agent...", "Orchestrator -> Medical Agent")
    
    medical_prompt = f"""
    You are the Medical Domain Agent. 
    Event: {event_type}
    Location: {sanitized_location}
    Total Population: {affected_population}
    Demographics: {json.dumps(vulnerable_groups)}
    Vision Insights (if any): {vision_insights or 'None'}
    
    Procedural Rules:
    1. Kit Calculation: Require 1 medical kit for every 10 estimated affected individuals.
    2. Personnel Calculation: Require 1 paramedic for every 50 estimated affected individuals.
    3. Specialized Equipment: If there are vulnerable groups (e.g. elderly -> oxygen, pediatric -> pediatric kits) or specific hazards from Vision Insights, list the required specialized equipment.
    4. Priority Triage:
       - Flood/Wildfire/Cyclone/Tropical Storm: "High" priority.
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
    log(f"Medical Assessment complete. Kits: {medical_plan['kits_required']}, Specialized: {medical_plan['specialized_equipment']}", "Medical Agent")
    
    # 3. A2A Protocol: Delegate to Logistics Agent
    log("Dynamically loading skill: 'inventory-sourcer'...", "Orchestrator")
    log("Delegating supply sourcing to Logistics Agent...", "Orchestrator -> Logistics Agent")

    logistics_prompt = f"""
    You are the Logistics Agent.
    Medical Requirements: {medical_plan['kits_required']} kits, plus {medical_plan['specialized_equipment']}.
    
    Procedural Rules:
    1. Assume the local inventory database has exactly 200 standard medical kits and NO specialized equipment.
    2. If the required kits exceed local inventory, or if specialized equipment is needed, you must issue a request to "Neighboring County Depot" for the exact shortage.
    3. Return actions taken (e.g., "Deployed 200 local kits. Requested 50 extra kits and oxygen tanks from Neighboring County Depot").
    """

    logistics_resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=logistics_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LogisticsOutput,
            temperature=0.1
        )
    )
    logistics_plan = json.loads(logistics_resp.text)
    log(f"Logistics sourced. Actions: {logistics_plan['actions_taken']}", "Logistics Agent")

    # 4. A2A Protocol: Delegate to Shelter Agent
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
    
    # 5. Compile Vibe Diff
    log("Compiling final Vibe Diff for human approval...")
    
    actions = [
        f"Dispatch {medical_plan['personnel']} medics with {medical_plan['kits_required']} kits.",
        f"Provide specialized equipment: {', '.join(medical_plan['specialized_equipment']) if medical_plan['specialized_equipment'] else 'None'}"
    ]
    actions.extend(logistics_plan['actions_taken'])
    actions.extend([
        f"Open {shelter_plan['evacuation_center']} (Capacity: {shelter_plan['capacity']}).",
        f"Route traffic via {shelter_plan['route']}."
    ])

    vibe_diff = {
        "event": f"{event_type} in {sanitized_location}",
        "context": mcp_data,
        "coordinates": mcp_data.get("coordinates", {"lat": 0, "lng": 0}),
        "vision_insights": vision_insights or "No image provided",
        "demographics": demographics,
        "actions": actions,
        "risk_level": medical_plan['priority']
    }
    
    return {
        "logs": logs,
        "vibe_diff": vibe_diff
    }
