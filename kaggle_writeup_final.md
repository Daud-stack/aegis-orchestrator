# Title: Project Aegis: Disaster Relief Resource Orchestrator
**Subtitle:** A production-grade, zero-trust multi-agent system for autonomous emergency logistics.
**Track:** Agents for Good

## 1. Core Concept & Value

### The Problem
During natural disasters, Emergency Operations Centers (EOCs) are overwhelmed by incoming data. Logistics coordinators struggle to rapidly assess infrastructure damage, map available medical resources, and route evacuation teams simultaneously. The delay in human coordination costs critical response time. 

### The Solution
Project Aegis is a "Disaster Relief Resource Orchestrator"—a robust, highly-visual multi-agent system designed to automate emergency logistics. When a disaster is reported, the system leverages an Orchestrator Agent that delegates tasks to specialized domain agents (e.g., Medical Agent, Shelter Agent). Crucially, the system operates under a Zero-Trust architecture, ensuring Personally Identifiable Information (PII) is masked and all final dispatches require human authorization via a "Vibe Diff."

## 2. Technical Architecture

Project Aegis moves away from simple "vibe coding" and embraces true Agentic Engineering. 

*   **Frontend Interface:** A custom-built Vite + React dashboard featuring a live radar and A2A communication logs, offering immediate visual feedback of the agent's internal reasoning.
*   **Agent Core (FastAPI):** A Python-based orchestration engine that manages state, delegates tasks, and applies middleware guardrails before executing tool calls.

### Deep Dive into Course Concepts Utilized

Our implementation rigorously applies the concepts taught in the 5-Day Intensive course:

**1. Agent-to-Agent (A2A) Protocol & The Factory Model**
Instead of relying on a monolithic agent, Aegis acts as an Orchestrator. It delegates domain-specific tasks using a universal communication layer. For example, when a flood is detected, the Orchestrator delegates medical kit estimation to the "Medical Agent" and evacuation routing to the "Shelter Agent."

**2. Model Context Protocol (MCP)**
The Orchestrator agent does not hallucinate environmental data. We implemented an MCP Server integration that the agent queries to retrieve live Weather and Traffic data. This guarantees that resource routing decisions are based on deterministic, real-world context rather than LLM guesswork.

**3. Context Hygiene & Zero-Trust Architecture**
In an emergency, citizens often report disasters using their real names and phone numbers. To ensure PII is never leaked to a remote LLM, we implemented a **Context Resolver Middleware**. Before the Orchestrator processes a user's location input, the middleware scrubs and replaces sensitive strings (e.g., swapping a phone number for `[REDACTED_PHONE]`).

**4. The "Vibe Diff" and Cryptographic MFA**
To combat confirmation fatigue and the "Confused Deputy" problem, the orchestrator is sandboxed from taking direct action. Before any medical supplies are deployed or evacuation routes are finalized, the agent compiles a human-readable "Vibe Diff." This presents a plain-English summary of the context retrieved and the intended actions. The human operator must manually click "Approve (MFA)" to execute the dispatch.

**5. Spec-Driven Development (SDD)**
Our repository includes a `specs/` directory housing the system's architectural integrity. We use a hybrid Markdown + YAML format for deeply nested payload schemas and Gherkin syntax (Behavior-Driven Development) to formally define the agent's expected trajectory.

## 3. The Build Journey

Building Aegis was a journey in applying constraints. Initially, we wanted the agent to do everything at once, but we quickly realized the value of progressive disclosure. By isolating the Medical and Shelter logic into domain agents and forcing the Orchestrator to rely on the MCP server for context, we dramatically reduced hallucinations. Implementing the Vibe Diff was the most rewarding part, as it perfectly bridged the gap between autonomous AI power and necessary human oversight.

## 4. Links & Assets

**Video Demo [Required]**
[Insert YouTube Link Here - Reminder: Max 5 minutes]

**Public Code Repository [Required]**
https://github.com/Daud-stack/aegis-orchestrator

### Local Setup Instructions for Judges
1. Clone the repository: `git clone https://github.com/Daud-stack/aegis-orchestrator.git`
2. **Start the Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # (or .\venv\Scripts\activate on Windows)
   pip install fastapi uvicorn pydantic
   uvicorn main:app --reload
   ```
3. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open the provided localhost URL to view the Orchestrator Dashboard.
