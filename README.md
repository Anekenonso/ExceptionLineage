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

### Running the Evaluation Harness (Stage 18)

Execute reproducible evaluation across the controlled benchmark cases:

```bash
# Default: Runs Baseline A (ValidationEngine) and Baseline B (HeuristicAgentModel)
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
- `evaluation/reports/latest.json`
- `evaluation/reports/latest.md`

## Documentation

- [Project State](docs/project-state.md)
- [Decisions](docs/decisions.md)
- [Traps](docs/traps.md)
- [Failure Modes](docs/failure-modes.md)
- [Evaluation Framework](docs/evaluation.md)

## Current Status

**Stage 18** — ENGINEERING COMPLETE — LIVE LLM PERFORMANCE PENDING ACTIVE PROVIDER RUN

ExceptionLineage features an end-to-end reproducible evaluation harness quantitatively testing whether the investigation architecture correctly investigates contract/invoice exceptions, retrieves required evidence, terminates safely, and uses agent tools efficiently:
- **Status Taxonomy**: Rigorously categorizes evaluation runs (`COMPLETED`, `BLOCKED_PROVIDER`, `PARTIAL`, `FAILED_SYSTEM`, `SKIPPED`) to avoid conflating external provider quota/network errors with model reasoning ability.
- **Baseline A (Deterministic Validation Engine)**: Direct rule evaluation achieving **100.0% accuracy** and **100.0% evidence recall** across all 8 controlled benchmark cases.
- **Baseline B (Heuristic Agent Model)**: Deterministic, rational agent loop achieving **100.0% accuracy**, **100.0% evidence recall**, 6.38 mean steps, and 51 total tool calls.
- **System Under Evaluation (LLM Decision Model)**: Autonomous planning layer using OpenAI-compatible APIs or deterministic mock execution (**62.5% accuracy in mock mode**; explicitly skipped in default runs to prevent external API dependencies).
- **Live LLM Evaluation (gpt-4o-mini)**: Status `BLOCKED_PROVIDER`. Initial run was rejected on 8/8 cases due to provider quota exhaustion (HTTP 429 `credit_balance_exhausted`), correctly classified as **UNMEASURABLE** (accuracy and recall set to null). Confirmed safe fail-closed architecture: 0 tool executions, 0 hallucinations, and all cases safely terminated as `FAILED`.
- **Metric Rigor**: Evaluates outcome accuracy, evidence recall, fine-grained tool usage, termination breakdowns, failure counters, and token tracking without fabricated composite scores.
- **Ground-Truth Isolation Law**: Verified by automated AST tests ensuring production modules (`app/agent`, `app/graph`, `app/investigations`, `app/api`, `app/validation`, `app/models`) contain zero imports or dependencies on ground truth.
- **Controlled Failure Modes**: 11 dedicated failure-mode tests confirming safe handling of unknown tools, missing/invalid arguments, malformed outputs, timeouts, retry exhaustion, missing evidence (`INSUFFICIENT_EVIDENCE`), conflicting amendments (`NEEDS_REVIEW`), and step limits.
- **Test Suite**: 265 passing unit and integration tests (2 skipped conditional live tests).

