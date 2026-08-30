# FleetPanda Voice & Chat Support Agent

> A production-grade **Voice and Chat Multi-Tenant Support Agent** built for FleetPanda's fuel dispatch platform. Integrates natural language Text-to-SQL dispatch queries, automated 5-source support ticket triage, neural speech-in/speech-out voice mode, JWT authentication, and a custom **Model Context Protocol (MCP)** server for strict multi-tenant data segregation.

---

## System Architecture

```
+---------------------------------------------------------------------------------+
|                         React 18 + TypeScript Frontend                          |
|   - Vite Build + Nginx Alpine Container                                         |
|   - shadcn/ui Components + Tailwind CSS + Lucide Icons                          |
|   - Dual Modality: Conversational Chat & Interactive Voice HUD                  |
|   - Triage Studio (5-Source Briefs) & Dispatch SQL Explorer (8 Benchmarks)       |
|   - JWT Access & Refresh Token Management + 1-Click Demo Profiles               |
+----------------------------------------+----------------------------------------+
                                         | HTTPS (Bearer Token Auth)
                                         v
+---------------------------------------------------------------------------------+
|                              FastAPI Backend                                    |
|   - Poetry Dependency Management & Python 3.11                                  |
|   - LangChain Multi-Provider LLM Factory (Ollama [default], OpenAI, Gemini,     |
|     Anthropic) with Deterministic Offline Fallback                              |
|   - Full-Duplex Audio Engine (Web Speech STT + edge-tts Neural Voice MP3)       |
|   - Multi-Tiered Fuzzy Entity Resolver (Canonical, Aliases, Domains, Tokens)    |
|   - Forwards request with Authorization: Bearer <token> to MCP Server           |
+----------------------------------------+----------------------------------------+
                                         | JSON-RPC / HTTP (Bearer Token)
                                         v
+---------------------------------------------------------------------------------+
|                            FleetPanda MCP Server                                |
|   - Authenticates JWT Claims (tenant_id, role, permissions)                     |
|   - Multi-Tenant Data Segregation Enforcer (AST inspection & tenant scoping)   |
|   - DDL/DML Guardrails & SQLite Read-Only Authorizer Hook                       |
|   - MCP Tools: execute_sql_query, triage_ticket, get_context, search_kb, etc.   |
+-------------------+--------------------+--------------------+-------------------+
                    |                    |                    |
                    v                    v                    v
            +---------------+    +---------------+    +---------------+
            |  dispatch.db  |    | JSON Datasets |    | KnowledgeBase |
            |  (SQLite RO)  |    |  (Customers,  |    |  (12 Articles)|
            |               |    |   Tickets,    |    |               |
            |               |    |  Transcripts) |    |               |
            +---------------+    +---------------+    +---------------+
```

---

## Key Features

1. **Dispatch Database Queries (Text-to-SQL)**:
   - Queries 90 days of operational data (~10K deliveries, shifts, tank readings, trucks, drivers).
   - Generates valid SQL, executes via MCP, and formats clean, human-readable answers.
   - Handles all 8 assignment benchmark questions with 100% precision.
2. **Support Ticket Triage**:
   - Synthesizes **all 5 data sources**: (1) Customer Profile (`customers.json`), (2) Dispatch Telemetry (`dispatch.db`), (3) Past Tickets (`tickets.json`), (4) Call History & Sentiments (`call_transcripts.json`), (5) Knowledge Base (`knowledge_base.json`).
   - Automatically flags **High Churn Risk** (health < 40 + expiring contract), **Duplicate Tickets**, and **Inactive Module Misconfigurations**.
   - Generates actionable escalation recommendations and context-aware customer response drafts.
3. **Full-Duplex Voice & Chat Modes**:
   - **Voice Mode**: Microphone recording (STT) $\rightarrow$ Agent processing $\rightarrow$ Neural voice audio synthesis (TTS via `edge-tts`) with real-time waveform visualizer.
   - **Chat Mode**: Rich markdown chat timeline, copyable code blocks, and inline SQL execution drawers.
4. **Hard Multi-Tenant Isolation & DDL/DML Protection**:
   - **AST Verification**: `sqlglot` validates queries, blocks multiple statements, and enforces `tenant_id` scoping.
   - **SQLite Read-Only Authorizer**: Blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ATTACH`, `PRAGMA` at the database engine level.
   - **MCP Bearer Token Segregation**: Scoped users can never query cross-tenant data.
5. **Flexible LLM Provider Factory**:
   - Configurable via `LLM_PROVIDER=ollama|openai|gemini|anthropic`.
   - Built-in deterministic offline fallback model for air-gapped test environments.

---

## Quick Start with Docker Compose

Launch the entire stack (Backend + Frontend + MCP Server + SQLite) with a single command:

```bash
docker compose up --build
```

- **Frontend Web UI**: Open `http://localhost:3000`
- **FastAPI OpenAPI Swagger Docs**: Open `http://localhost:8000/docs`

---

## Local Development Setup

### 1. Prerequisites
- Python 3.9+ / 3.11
- Node.js 18+ & npm
- [Optional] Ollama with `llama3.2` running locally (`http://localhost:11434`)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies with Poetry or Pip
poetry install
# or: pip install -r requirements.txt

# Run the FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

---

## Pre-Configured Demo Accounts for Testing

The login screen provides **1-click quick login pills** for testing multi-tenant segregation:

| Account | Email | Password | Scope / Role |
| :--- | :--- | :--- | :--- |
| **Lead CSM Arcadio** | `csm@fleetpanda.com` | `password123` | Global Cross-Tenant (All 12 Tenants) |
| **Support Agent Maria**| `support@fleetpanda.com` | `password123` | Global Support (Cross-Tenant) |
| **Cascade Fuel Admin** | `admin@cascadefuel.com` | `password123` | **Tenant 1 Strictly Scoped** |
| **Heartland Dispatcher**| `dispatcher@heartland.com`| `password123` | **Tenant 2 Strictly Scoped** |
| **Summit Energy Ops** | `ops@summitenergy.com` | `password123` | **Tenant 3 Strictly Scoped** |
| **Desert Sun Petro** | `admin@desertsun.com` | `password123` | **Tenant 4 Strictly Scoped** (Health 28) |
| **Timber Ridge Oil** | `manager@timberridge.com`| `password123` | **Tenant 8 Strictly Scoped** (Health 39) |

---

## Running the Automated Test Suite

The test suite contains **33 comprehensive automated tests** covering all assignment requirements:

```bash
# Run pytest from root or backend directory
pytest backend/tests/ -v
```

### Test Coverage Breakdown:
1. `test_auth.py` (5 tests): Password hashing, access/refresh token generation, validation, and refresh rotation.
2. `test_mcp_server.py` (4 tests): MCP tool catalog, Bearer authorization, tenant data segregation, and DDL/DML blocking.
3. `test_entity_resolver.py` (5 tests): Canonical names, acronyms (`CFS`, `DSP`, `TRO`), email domains, and fuzzy match resolution.
4. `test_tenant_isolation.py` (5 tests): AST tenant filter injection, cross-tenant denial, and SQLite engine read-only authorizer hooks.
5. `test_sql_benchmark.py` (8 tests): **Validates all 8 benchmark SQL questions from the assignment**:
   - Q1: Deliveries completed in last 7 days across all tenants
   - Q2: Tenant delivering most gallons of diesel last month
   - Q3: Top 5 drivers by total deliveries for tenant 3
   - Q4: Average gallons per delivery for propane orders
   - Q5: Emergency orders for tenant 4 in past 30 days
   - Q6: Trucks currently in maintenance status
   - Q7: Fill rate (gallons delivered / gallons ordered) by tenant
   - Q8: Tenants with declining delivery volume (last 30d vs previous 30d)
6. `test_ticket_triage.py` (3 tests): **Validates all 3 required test ticket scenarios**:
   - Low-health customer (health < 40) with expiring contract (Desert Sun, Health 28, Contract 2026-07-15)
   - Duplicate ticket detection (Ticket #1083 / #1027)
   - Inactive module ticket (filing ticket on `tank_monitor` when account only has `dispatch` and `pricing`)
7. `test_security_fixes.py` (3 tests): Verifies protection against all 3 vulnerabilities in `SECURITY.md`.

---

## Deliverables Summary

- [x] **`README.md`**: Complete setup, architecture, and testing guide.
- [x] **`DECISIONS.md`**: Engineering journal with 5 architectural trade-offs, data observations, token cost math, scaling blueprints, and end-customer isolation.
- [x] **`SECURITY.md`**: Code review challenge analysis of the 3 vulnerabilities with attack vectors and hardened production code.
- [x] **`backend/`**: FastAPI backend with Poetry, LangChain LLM factory, AST security, and custom MCP Server.
- [x] **`frontend/`**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui frontend with Chat, Voice HUD, Triage Studio, and SQL Explorer.
- [x] **`tests/`**: 33 Pytest unit and integration tests.
- [x] **`docker-compose.yml`**: Production container orchestration.
