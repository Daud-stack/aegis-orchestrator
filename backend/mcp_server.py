import asyncio
import requests
import random

async def mcp_query(location: str):
    """
    Real MCP Server simulating context retrieval.
    Fetches real weather using Open-Meteo API.
    Simulates traffic realistically and deterministically.
    """
    weather_str = "Clear (Location not found)"
    lat = 0.0
    lon = 0.0
    
    # 1. Geocoding (get lat/long for location)
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geocode_resp = requests.get(geocode_url)
        geocode_data = geocode_resp.json()
        
        if "results" in geocode_data and len(geocode_data["results"]) > 0:
            lat = geocode_data["results"][0]["latitude"]
            lon = geocode_data["results"][0]["longitude"]
            
            # 2. Fetch Weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation&temperature_unit=fahrenheit&wind_speed_unit=mph"
            weather_resp = requests.get(weather_url)
            weather_data = weather_resp.json()
            
            current = weather_data.get("current", {})
            temp = current.get("temperature_2m", "Unknown")
            wind = current.get("wind_speed_10m", "Unknown")
            precip = current.get("precipitation", 0)
            
            weather_str = f"Temp: {temp}°F, Wind: {wind} mph, Precip: {precip} mm"
            
    except Exception as e:
        weather_str = f"Error fetching weather: {str(e)}"
        
    # 3. Location-specific road data and realistic traffic simulation
    random.seed(location)

    LOCATION_ROADS = {
        # ── United States ──
        "Sector 4": {
            "roads": ["Wilshire Blvd", "Santa Monica Blvd", "I-405 Southbound", "US-101 Freeway", "Sunset Blvd", "La Brea Ave", "Venice Blvd", "Crenshaw Blvd"],
            "incidents": ["Accident", "Roadworks", "Debris", "Heavy Congestion", "Power Line Down", "Sinkhole"],
        },
        "Downtown": {
            "roads": ["Broadway", "5th Ave", "FDR Drive", "I-278 (BQE)", "Canal St", "Houston St", "West Side Highway", "Park Ave"],
            "incidents": ["Accident", "Roadworks", "Flooding", "Subway Disruption", "Heavy Congestion", "Water Main Break"],
        },
        "North Ridge": {
            "roads": ["Reseda Blvd", "Tampa Ave", "Nordhoff St", "Roscoe Blvd", "CA-118 Ronald Reagan Fwy", "Devonshire St", "Balboa Blvd", "White Oak Ave"],
            "incidents": ["Accident", "Debris", "Gas Leak", "Structural Collapse", "Heavy Congestion", "Roadworks"],
        },
        # ── Zimbabwe ──
        "Harare": {
            "roads": ["Samora Machel Ave", "Julius Nyerere Way", "Rekayi Tangwena Ave", "Kwame Nkrumah Ave", "Simon Mazorodze Rd", "Borrowdale Rd", "Lomagundi Rd", "Enterprise Rd"],
            "incidents": ["Flooding", "Pothole Collapse", "Roadworks", "Kombi Accident", "Fallen Tree", "Power Line Down"],
        },
        "Bulawayo": {
            "roads": ["Joshua Mqabuko Nkomo St", "Fife St", "George Silundika St", "Josiah Tongogara St", "8th Ave", "Old Esigodini Rd", "Khami Rd", "Samuel Parirenyatwa St"],
            "incidents": ["Accident", "Water Pipe Burst", "Debris", "Heavy Congestion", "Fallen Tree", "Sewer Collapse"],
        },
        "Chimanimani": {
            "roads": ["Chimanimani-Mutare Rd", "Ngangu Access Rd", "Charleswood Rd", "Outward Bound Rd", "Tilbury Estate Rd", "Cashel Valley Rd"],
            "incidents": ["Landslide", "Bridge Washout", "Flooding", "Mudslide", "Road Collapse", "Boulder Fall"],
        },
        "Mutare": {
            "roads": ["Herbert Chitepo St", "Victory Ave", "Christmas Pass Rd", "Aerodrome Rd", "Forbes Rd", "Vumba Rd", "Hobhouse Ave", "D Avenue"],
            "incidents": ["Flooding", "Accident", "Rockfall", "Fallen Tree", "Pothole Collapse", "Heavy Congestion"],
        },
        # ── Mozambique ──
        "Beira": {
            "roads": ["EN1 Nacional", "EN6 Beira Corridor", "Avenida do Poder Popular", "Rua Costa Serrão", "Rua Major Serpa Pinto", "Avenida Eduardo Mondlane", "Rua Correia de Brito", "Rua do Armazém"],
            "incidents": ["Flooding", "Bridge Washout", "Storm Surge Debris", "Road Collapse", "Fallen Power Lines", "Tidal Inundation"],
        },
    }

    # Fallback for unknown locations
    default_data = {
        "roads": ["Main Rd", "Highway 1", "Central Ave", "River Rd", "Bridge St", "Market Rd"],
        "incidents": ["Accident", "Flooding", "Roadworks", "Debris", "Heavy Congestion"],
    }

    loc_data = LOCATION_ROADS.get(location, default_data)
    roads = loc_data["roads"]
    incidents_pool = loc_data["incidents"]

    num_incidents = random.randint(1, 3)
    used_roads = random.sample(roads, min(num_incidents, len(roads)))
    incidents = []
    for road in used_roads:
        inc = random.choice(incidents_pool)
        incidents.append(f"{road} Blocked due to {inc}")
    traffic_str = ", ".join(incidents)

    return {
        "weather": weather_str,
        "traffic": traffic_str,
        "coordinates": {"lat": lat, "lng": lon}
    }
