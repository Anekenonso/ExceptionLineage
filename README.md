# ExceptionLineage

Evidence-backed investigation system for enterprise transaction exceptions.

## Overview

ExceptionLineage investigates relationships across contracts, amendments, SOWs, approvals and invoices to produce evidence-backed determinations for enterprise transaction exceptions.

## Project Structure

```
ExceptionLineage/
├── apps/
│   ├── web/          # Next.js frontend (TypeScript + Tailwind CSS)
│   └── api/          # FastAPI backend (Python)
├── data/             # Data files (future)
├── evaluation/       # Evaluation framework (future)
├── neo4j/            # Graph database config (future)
├── docs/             # Project documentation
├── .env.example      # Environment variable template
├── .gitignore        # Git ignore rules
├── README.md         # This file
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- npm

### Backend

```bash
cd apps/api
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Running Tests

```bash
cd apps/api
python -m pytest tests/ -v
```

## Documentation

- [Project State](docs/project-state.md)
- [Decisions](docs/decisions.md)
- [Traps](docs/traps.md)
- [Failure Modes](docs/failure-modes.md)
- [Evaluation](docs/evaluation.md)

## Current Status

**Stage 17** — Controlled Agentic Investigation Loop COMPLETE.

ExceptionLineage executes an end-to-end investigation pipeline connecting the FastAPI boundary to an agentic tool selection loop and deterministic rule validation:
- **HTTP Ingress**: `POST /api/investigations`, `GET /api/investigations/{id}`, `GET /api/investigations/{id}/events`.
- **Service Orchestration**: `InvestigationService` coordinates lifecycle progression (`QUEUED` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `VALIDATING` $\rightarrow$ terminal outcome).
- **Controlled Agentic Loop (`app.agent`)**: `InvestigationAgent` dynamically plans and executes tool calls (`get_invoice`, `find_contract`, `get_contract_amendments`, `get_sows`, `find_approvals`, `get_related_evidence`, `validate_investigation`) within a bounded step limit (`MAX_AGENT_STEPS = 10`).
- **Auditability & Metrics**: Every agent decision and tool execution is recorded as an immutable event with fine-grained execution metrics (`AgentMetrics`).
- **Lineage Retrieval Abstraction**: Decoupled graph traversal (`LineageRepository`) with production Neo4j implementation (`Neo4jLineageRepository`) and deterministic test doubles (`InMemoryLineageRepository`).
- **Deterministic Validation Engine**: Evaluates 8 contractual compliance rules against normalized `InvestigationContext` to yield auditable determinations (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`).
- **Authority Boundary**: Follows *"AI handles ambiguity. Code handles authority"*. 100% benchmark compliance verified across all 8 controlled cases (using synthetic SIMULATED datasets) without runtime ground-truth shortcuts.


