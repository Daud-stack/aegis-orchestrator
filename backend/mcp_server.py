import asyncio
import requests

async def mcp_query(location: str):
    """
    Real MCP Server simulating context retrieval.
    Fetches real weather using Open-Meteo API.
    Simulates traffic deterministically based on location name length.
    """
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
        else:
            weather_str = "Clear (Location not found)"
            
    except Exception as e:
        weather_str = f"Error fetching weather: {str(e)}"
        
    # Simulate traffic based on location name length to have some determinism
    traffic_str = "Route 4 Blocked, Highway 9 Clear" if len(location) % 2 == 0 else "Normal Traffic"

    return {
        "weather": weather_str,
        "traffic": traffic_str
    }

