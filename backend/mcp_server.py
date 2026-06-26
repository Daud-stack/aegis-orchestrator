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
        
    # 3. Simulate Realistic Traffic
    random.seed(location)
    incident_types = ["Accident", "Roadworks", "Flooding", "Debris", "Heavy Congestion"]
    road_names = ["Main St", "Highway 9", "Route 4", "I-95", "Broad St", "Oak Ave"]
    
    num_incidents = random.randint(0, 2)
    if num_incidents == 0:
        traffic_str = "Normal Traffic in the area."
    else:
        incidents = []
        for _ in range(num_incidents):
            inc = random.choice(incident_types)
            road = random.choice(road_names)
            incidents.append(f"{road} Blocked due to {inc}")
        traffic_str = ", ".join(incidents)

    return {
        "weather": weather_str,
        "traffic": traffic_str,
        "coordinates": {"lat": lat, "lng": lon}
    }
