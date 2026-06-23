# Project Aegis: Disaster Relief Resource Orchestrator

![Dashboard UI](https://github.com/Daud-stack/aegis-orchestrator/raw/main/orchestrator_dashboard_mockup_1782213536769.png)

## Overview
Project Aegis is a production-grade, zero-trust multi-agent system designed to automate emergency logistics during natural disasters. By utilizing an Orchestrator Agent that delegates tasks to specialized domain agents (Medical & Shelter), Aegis rapidly assesses infrastructure damage and routes resources safely.

## Course Concepts Implemented
This project was built for the Kaggle AI Agents Intensive Capstone and strictly implements the following concepts:
1. **Agent-to-Agent (A2A) Protocols:** Decentralized orchestration rather than a monolithic LLM.
2. **Model Context Protocol (MCP):** Connects to external weather/traffic tools to prevent hallucination.
3. **Context Hygiene (Zero-Trust):** PII Masking middleware strips sensitive data (SSNs/Phone numbers) before hitting the LLM context window.
4. **The Vibe Diff:** A Cryptographic MFA authorization gate ensuring the agent is sandboxed and requires human approval before executing dispatches.
5. **Spec-Driven Development:** Uses BDD Gherkin specs and YAML schemas (found in `/specs`) to ensure structural integrity.
6. **Deployability:** Fully containerized using Docker Compose.

## Architecture

```mermaid
graph TD
    UI[Frontend Dashboard (React/Vite)] -->|Trigger Request| FA[FastAPI Backend]
    FA --> OA[Orchestrator Agent]
    
    OA -->|Query| MCP[MCP Server: Weather & Traffic]
    
    OA -->|A2A Protocol| MA[Medical Domain Agent]
    OA -->|A2A Protocol| SA[Shelter Domain Agent]
    
    OA -->|Generate| VD[Vibe Diff Modal]
    VD --> UI
```

## Setup Instructions

### Option A: Docker (Recommended)
This project is fully containerized for instant deployability.
1. Make sure Docker is installed.
2. Run `docker-compose up --build`
3. Access the dashboard at `http://localhost:5173`

### Option B: Manual Setup
**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (Windows: .\venv\Scripts\activate)
pip install fastapi uvicorn pydantic
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.
