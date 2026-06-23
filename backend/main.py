from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_core import orchestrate_disaster_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DisasterRequest(BaseModel):
    event_type: str
    location: str

@app.post("/api/report-disaster")
async def report_disaster(request: DisasterRequest):
    plan = await orchestrate_disaster_response(request.event_type, request.location)
    return {"status": "success", "plan": plan}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
