import asyncio

async def mcp_query(location: str):
    """
    Mock MCP (Model Context Protocol) Server.
    In a real app, this would be a separate server communicating via stdio or SSE.
    """
    await asyncio.sleep(1) # Simulate network latency
    
    if "Sector 4" in location:
        return {
            "weather": "Heavy Rain, 45mph winds",
            "traffic": "Route 4 Blocked, Highway 9 Clear"
        }
    else:
        return {
            "weather": "Clear",
            "traffic": "Normal"
        }
