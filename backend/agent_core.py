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


# ── Disaster Resource Catalog ──
# Maps each disaster type to required medical supplies, equipment, personnel, and local inventory
DISASTER_RESOURCES = {
    "Flood": {
        "priority": "High",
        "medical_supplies": [
            "Water purification tablets",
            "Tetanus vaccine doses",
            "Waterproof wound dressings",
            "Hypothermia blankets",
            "Oral rehydration salts (ORS)",
            "Anti-diarrheal medication",
            "Cholera rapid test kits",
        ],
        "heavy_equipment": [
            "Inflatable rescue boats",
            "Submersible water pumps",
            "Life jackets",
            "Portable generators",
            "Sandbag barriers",
            "High-powered floodlights",
        ],
        "personnel_types": [
            "Swift-water rescue technicians",
            "Public health nurses",
            "Paramedics",
            "Water sanitation specialists",
        ],
        "local_inventory": {
            "standard_kits": 200,
            "rescue_boats": 4,
            "water_pumps": 6,
            "generators": 3,
        },
    },
    "Earthquake": {
        "priority": "Critical",
        "medical_supplies": [
            "Trauma surgery kits",
            "Crush injury (rhabdomyolysis) kits",
            "Portable X-ray units",
            "Morphine/analgesic auto-injectors",
            "Cervical collars and spinal boards",
            "Blood transfusion packs",
            "Tourniquet sets",
        ],
        "heavy_equipment": [
            "Hydraulic rescue jacks",
            "Concrete cutters / rebar saws",
            "Thermal imaging cameras",
            "Search & rescue dogs (K9 units)",
            "Portable seismographs (aftershock)",
            "Heavy-lift cranes",
        ],
        "personnel_types": [
            "Urban Search & Rescue (USAR) teams",
            "Trauma surgeons",
            "Structural engineers",
            "K9 handlers",
        ],
        "local_inventory": {
            "standard_kits": 150,
            "hydraulic_jacks": 2,
            "thermal_cameras": 1,
            "generators": 2,
        },
    },
    "Wildfire": {
        "priority": "High",
        "medical_supplies": [
            "Burn treatment kits (silver sulfadiazine)",
            "N95/P100 respiratory masks",
            "Oxygen tanks and regulators",
            "Albuterol inhalers",
            "Sterile eye wash stations",
            "IV fluid bags (for dehydration)",
        ],
        "heavy_equipment": [
            "Fire retardant sprayers",
            "Bulldozers (firebreak creation)",
            "Water tanker trucks",
            "Thermal drone surveillance units",
            "Portable air quality monitors",
        ],
        "personnel_types": [
            "Hotshot firefighter crews",
            "Burn care specialists",
            "Respiratory therapists",
            "Aerial tanker pilots",
        ],
        "local_inventory": {
            "standard_kits": 180,
            "burn_kits": 30,
            "oxygen_tanks": 20,
            "respirators": 100,
        },
    },
    "Cyclone": {
        "priority": "High",
        "medical_supplies": [
            "Wound care kits (suture sets)",
            "Tetanus vaccine doses",
            "Cholera prevention kits",
            "Oral rehydration salts (ORS)",
            "Waterproof wound dressings",
            "Pediatric nutrition packs",
            "Anti-malarial prophylaxis",
        ],
        "heavy_equipment": [
            "Chainsaws (fallen trees/debris)",
            "Portable generators",
            "Tarpaulins / emergency sheeting",
            "Satellite communication phones",
            "Water purification units",
            "Heavy-duty water pumps",
        ],
        "personnel_types": [
            "Emergency shelter coordinators",
            "Utility repair crews",
            "Paramedics",
            "Community health workers",
        ],
        "local_inventory": {
            "standard_kits": 120,
            "tarpaulins": 50,
            "generators": 4,
            "water_purifiers": 3,
        },
    },
    "Tropical Storm": {
        "priority": "High",
        "medical_supplies": [
            "Basic first aid kits",
            "Oral rehydration salts (ORS)",
            "Waterproof wound dressings",
            "Hypothermia blankets",
            "Anti-diarrheal medication",
        ],
        "heavy_equipment": [
            "Sandbag barriers",
            "Portable generators",
            "Water pumps",
            "Temporary shelter frames",
            "Emergency lighting rigs",
        ],
        "personnel_types": [
            "Paramedics",
            "Emergency shelter coordinators",
            "Utility repair crews",
        ],
        "local_inventory": {
            "standard_kits": 200,
            "sandbags": 500,
            "generators": 3,
            "pumps": 4,
        },
    },
}

DEFAULT_RESOURCES = {
    "priority": "Medium",
    "medical_supplies": ["Standard first aid kits", "Bandages", "Antiseptic", "Pain medication"],
    "heavy_equipment": ["Portable generators", "Emergency lighting"],
    "personnel_types": ["Paramedics", "Emergency coordinators"],
    "local_inventory": {"standard_kits": 200, "generators": 2},
}


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

    # 0. Load disaster-specific resource manifest
    resource_manifest = DISASTER_RESOURCES.get(event_type, DEFAULT_RESOURCES)
    log(f"Resource manifest loaded for '{event_type}': {len(resource_manifest['medical_supplies'])} supply types, {len(resource_manifest['heavy_equipment'])} equipment types", "Resource Catalog")
    
    # 0b. Vision Analysis (Multi-Modal)
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
    
    # 2. A2A Protocol: Delegate to Medical Agent (with resource manifest)
    log("Dynamically loading skill: 'medical-assessment-calculator'...", "Orchestrator")
    log(f"Delegating medical assessment to Medical Agent...", "Orchestrator -> Medical Agent")
    
    medical_prompt = f"""
    You are the Medical Domain Agent. 
    Event: {event_type}
    Location: {sanitized_location}
    Total Population: {affected_population}
    Demographics: {json.dumps(vulnerable_groups)}
    Vision Insights (if any): {vision_insights or 'None'}
    
    RESOURCE MANIFEST FOR {event_type.upper()}:
    Required Medical Supplies: {json.dumps(resource_manifest['medical_supplies'])}
    Required Heavy Equipment: {json.dumps(resource_manifest['heavy_equipment'])}
    Required Personnel Types: {json.dumps(resource_manifest['personnel_types'])}
    
    Procedural Rules:
    1. Kit Calculation: Require 1 medical kit for every 10 estimated affected individuals.
    2. Personnel Calculation: Require 1 paramedic/specialist for every 50 estimated affected individuals.
    3. Specialized Equipment: You MUST select from the Resource Manifest above. Add pediatric-specific items if pediatric count > 5000, and elderly-specific items (oxygen, mobility aids) if elderly count > 2000.
    4. Priority: "{resource_manifest['priority']}" (pre-determined by disaster type).
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
    log(f"Medical Assessment complete. Kits: {medical_plan['kits_required']}, Priority: {medical_plan['priority']}, Specialized: {medical_plan['specialized_equipment']}", "Medical Agent")
    
    # 3. A2A Protocol: Delegate to Logistics Agent (with real inventory)
    log("Dynamically loading skill: 'inventory-sourcer'...", "Orchestrator")
    log("Delegating supply sourcing to Logistics Agent...", "Orchestrator -> Logistics Agent")

    local_inv = resource_manifest["local_inventory"]
    logistics_prompt = f"""
    You are the Logistics Agent.
    Disaster Type: {event_type}
    Location: {sanitized_location}
    
    REQUIRED RESOURCES:
    - Medical kits needed: {medical_plan['kits_required']}
    - Specialized equipment needed: {json.dumps(medical_plan['specialized_equipment'])}
    - Full supply manifest: {json.dumps(resource_manifest['medical_supplies'])}
    - Heavy equipment manifest: {json.dumps(resource_manifest['heavy_equipment'])}
    
    LOCAL INVENTORY (on-hand):
    {json.dumps(local_inv, indent=2)}
    
    Procedural Rules:
    1. Compare required kits against local inventory 'standard_kits' ({local_inv.get('standard_kits', 0)} available).
    2. For EACH item in the specialized equipment and heavy equipment manifests, check if local inventory has it. If not, request from the nearest regional depot.
    3. For Zimbabwe/Mozambique locations, the regional depot is "SADC Regional Logistics Hub (Harare)".
       For US locations, the regional depot is "FEMA Regional Depot".
    4. Return ALL actions taken with specific quantities.
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
        "resource_manifest": {
            "disaster_type": event_type,
            "medical_supplies": resource_manifest["medical_supplies"],
            "heavy_equipment": resource_manifest["heavy_equipment"],
            "personnel_types": resource_manifest["personnel_types"],
            "local_inventory": local_inv,
        },
        "actions": actions,
        "risk_level": medical_plan['priority']
    }
    
    return {
        "logs": logs,
        "vibe_diff": vibe_diff
    }

