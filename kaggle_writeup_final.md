# Title: Project Aegis: Disaster Relief Resource Orchestrator
**Subtitle:** A production-grade, zero-trust multi-agent system for autonomous emergency logistics.
**Track:** Agents for Good

## 1. Core Concept & Value

### The Problem
During natural disasters, Emergency Operations Centers (EOCs) are overwhelmed by incoming data. Logistics coordinators struggle to rapidly assess infrastructure damage, map available medical resources, and route evacuation teams simultaneously. When disaster strikes resource-constrained environments—such as the devastating 2019 Cyclone Idai in Southern Africa—the delay in human coordination costs critical response time and lives.

### The Solution
Project Aegis is a "Disaster Relief Resource Orchestrator"—a robust, highly-visual multi-agent system designed to automate emergency logistics. When a disaster is reported, the system leverages an Orchestrator Agent that delegates tasks to specialized domain agents (Medical, Logistics, and Shelter). Crucially, the system operates under a Zero-Trust architecture, ensuring Personally Identifiable Information (PII) is masked and all final dispatches require human authorization via a "Vibe Diff" approval interface.

## 2. Technical Architecture

Project Aegis moves away from simple "vibe coding" and embraces true Agentic Engineering. 

*   **Frontend Interface:** A custom-built React + Leaflet map dashboard (using CartoDB Dark Matter tiles) featuring live geographic plotting and A2A communication logs, offering immediate visual feedback of the agent's internal reasoning.
*   **Agent Core (FastAPI):** A Python-based orchestration engine that manages state, delegates tasks, injects deterministic census data, and applies middleware guardrails before executing tool calls.

### Deep Dive into Course Concepts Utilized

Our implementation rigorously applies the concepts taught in the 5-Day Intensive course:

**1. Agent-to-Agent (A2A) Protocol & The Factory Model**
Instead of relying on a monolithic agent, Aegis acts as an Orchestrator. It delegates domain-specific tasks using a universal communication layer. For example, when a Cyclone is detected in Chimanimani, the Orchestrator pulls the specific "Disaster Resource Manifest", delegates medical kit calculations to the "Medical Agent", routes logistics to the "Logistics Agent", and finds safe paths via the "Shelter Agent."

**2. Model Context Protocol (MCP) & Deterministic Grounding**
The Orchestrator agent does not hallucinate environmental data or demographics. We integrated:
*   **Real-time MCP Server:** Fetches actual geographic coordinates and context (weather/traffic conditions on real, distinct local streets).
*   **Census-Based Demographics:** Bypasses LLM hallucination by injecting real population data (e.g., accurately reflecting the younger, highly pediatric populations of Zimbabwe and Mozambique compared to US baseline models).

**3. Context Hygiene & Zero-Trust Architecture**
In an emergency, citizens often report disasters using their real names and phone numbers. To ensure PII is never leaked to a remote LLM, we implemented a **Context Resolver Middleware**. Before the Orchestrator processes input, the middleware scrubs sensitive strings (e.g., swapping a phone number for `[REDACTED_PHONE]`).

**4. The "Vibe Diff" and Cryptographic MFA**
To combat confirmation fatigue and the "Confused Deputy" problem, the orchestrator is sandboxed from taking direct action. Before supplies are deployed, the agent compiles a human-readable "Vibe Diff." This presents a plain-English summary of the context retrieved, the exact resource manifest (medical supplies, heavy equipment, personnel), and the intended routing actions. The human operator must manually click "Approve (MFA)" to execute the dispatch.

## 3. The Build Journey

Building Aegis was a journey in applying constraints. Initially, we wanted the agent to do everything at once (guessing populations, hallucinating streets, and improvising medical supplies). We quickly realized the value of deterministic grounding. 

By hardcoding real census data, generating strict resource manifests per disaster type, and forcing the Orchestrator to rely on the MCP server for context, we dramatically reduced hallucinations and latency. Transitioning from a fake CSS radar to a real, interactive Leaflet map grounded the project in reality. The most rewarding part was implementing the Vibe Diff—it perfectly bridges the gap between autonomous AI power and necessary human oversight.

## 4. Links & Assets

**Video Demo [Required]**
`[PLACEHOLDER: Insert YouTube Link Here - Reminder: Max 5 minutes]`

**Public Code Repository [Required]**
https://github.com/Daud-stack/aegis-orchestrator

### Local Setup Instructions for Judges
1. Clone the repository: `git clone https://github.com/Daud-stack/aegis-orchestrator.git`
2. **Start the Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # (or .\venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open the provided localhost URL (usually `http://localhost:5173`) to view the Orchestrator Dashboard.
