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
├── data/             # Seed records, cases, and evaluation ground truth
├── evaluation/       # Quantitative evaluation harness & reporting (Stage 18)
│   ├── adapters/     # Baseline evaluation adapters (Deterministic, Heuristic, LLM)
│   ├── reports/      # Machine-readable JSON and human-readable Markdown reports
│   ├── dataset.py    # Controlled dataset and scenario loader
│   ├── metrics.py    # Transparent accuracy, recall, tool, and failure formulas
│   ├── runner.py     # CLI evaluation runner
│   └── schemas.py    # Structured Pydantic evaluation schemas
├── neo4j/            # Graph database config
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

### Running the Evaluation Harness (Stage 18 & 18.5)

Execute reproducible evaluation across the controlled benchmark and branching cases:

```bash
# Stage 18.5 Architectural Proof (Claims A, B, and C):
python evaluation/runner.py --stage-18-5

# Stage 18 Default: Runs Baseline A (ValidationEngine) and Baseline B (HeuristicAgentModel)
python evaluation/runner.py

# Offline Mock LLM Evaluation:
python evaluation/runner.py --mock-llm

# Live LLM Evaluation (requires API key):
export AGENT_LLM_API_KEY="your-api-key"
python evaluation/runner.py --with-llm

# Specific Baseline:
python evaluation/runner.py --baseline deterministic
python evaluation/runner.py --baseline heuristic
```

Generated reports are saved to:
- `evaluation/reports/stage-18-5-latest.json` (Stage 18.5 Proof Report)
- `evaluation/reports/stage-18-5-latest.md` (Stage 18.5 Proof Markdown)
- `evaluation/reports/latest.json` (Stage 18 Suite Report)
- `evaluation/reports/latest.md` (Stage 18 Markdown)

## Documentation

- [Architecture & Proof](docs/architecture.md)
- [Project State](docs/project-state.md)
- [Decisions](docs/decisions.md)
- [Traps](docs/traps.md)
- [Failure Modes](docs/failure-modes.md)
- [Evaluation Framework](docs/evaluation.md)

## Current Status

**Stage 18.5** — ARCHITECTURAL PROOF COMPLETE — Agent Necessity + Neo4j Necessity + End-to-End Evidence Chain Proven

ExceptionLineage provides empirical proof for its core architectural components:
- **Claim A (Agent Necessity) — PROVEN**: On non-linear branching workflows (`adaptive-v1`), the adaptive agent achieves **100.0% accuracy** (vs 80.0% fixed heuristic), reduces tool calls by **25.0%** (24 vs 32 calls), eliminates **all 7 unnecessary tool calls**, and executes **3 dynamic early stops**.
- **Claim B (Neo4j Load-Bearing Role) — PROVEN**: Removing graph relationship traversal and using flat relational lookups drops validation accuracy to **87.5%** (false amendment conflicts), returns **37 irrelevant records**, reduces provenance completeness to **20.0%**, and multiplies queries to **8.25 operations/case**. Directional graph traversal is load-bearing to prevent customer-wide context pollution.
- **Claim C (End-to-End Evidence Chain) — PROVEN**: Produces complete, machine-readable 30-event audit traces (`GET /api/investigations/{id}/trace`) linking `INPUT -> AGENT_DECISION -> TOOL_CALL -> GRAPH_RETRIEVAL -> VALIDATION -> OUTCOME`, with complete secret sanitization and tri-state check semantics.
- **Authority Invariant**: *"AI handles ambiguity. Code handles authority."*
- **Test Suite**: 277 passing unit and integration tests (2 skipped conditional live tests).


