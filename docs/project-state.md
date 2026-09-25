# Project State

## Current Stage

**Stage 18.5** — ARCHITECTURAL PROOF COMPLETE — Agent Necessity + Neo4j Necessity + End-to-End Evidence Chain Proven

## What Works

- **Stage 18.5 Architectural Proof Suite (`evaluation/runner.py --stage-18-5`)**:
  - Main CLI entry point: `evaluation/runner.py --stage-18-5`.
  - Machine-readable JSON output: `evaluation/reports/stage-18-5-latest.json`.
  - Human-readable Markdown output: `evaluation/reports/stage-18-5-latest.md`.
  - **Claim A (Agent Necessity) — PROVEN**:
    - Evaluated across 5 controlled branching scenarios (`adaptive-v1`): `BRANCH-001` through `BRANCH-005`.
    - Adaptive agent achieved **100.0% accuracy** (vs 80.0% fixed heuristic), **24 tool calls** (vs 32 calls, 25% reduction), **0 unnecessary calls** (avoiding 7 wasted calls), and **3 dynamic early stops**.
    - Proves agentic loop is necessary for non-linear enterprise exception discovery, dead-end backtracking, and query minimization.
  - **Claim B (Neo4j Load-Bearing Role) — PROVEN**:
    - Architectural ablation study comparing Knowledge Graph (`DeterministicValidationAdapter`) vs Flat Relational Mock (`FlatRetrievalAdapter`) across the 8-case benchmark suite.
    - Flat retrieval caused accuracy to drop to **87.5%** (false amendment rate conflicts), returned **37 irrelevant records**, degraded provenance completeness to **20.0%** (vs 100%), and required **8.25 retrieval operations/case** (vs 1.0 graph query).
    - Proves directional graph relationships (`Contract -[:AMENDED_BY]-> Amendment`) are load-bearing to prevent customer-wide context pollution.
  - **Claim C (End-to-End Evidence Chain) — PROVEN**:
    - Machine-readable trace generator (`app/investigations/trace.py`) and API endpoint `GET /api/investigations/{id}/trace`.
    - Produces complete, unbroken 30-event audit trace: `INPUT -> AGENT_DECISION -> TOOL_CALL -> GRAPH_RETRIEVAL -> VALIDATION -> OUTCOME`.
    - Verifies secret redaction (credentials/tokens sanitized to `[REDACTED]`), timestamp preservation, tri-state check semantics (`PASS`, `FAIL`, `UNKNOWN`), and strict preservation of the authority boundary (*"AI handles ambiguity. Code handles authority."*).
- **Backend test suite with 277 passing tests and 2 conditional live tests (pytest)**.
- **Reproducible Evaluation Harness (`evaluation/`)**:
  - Main CLI entry point: `evaluation/runner.py` executable via `python evaluation/runner.py`.
  - Explicit status taxonomy (`COMPLETED`, `BLOCKED_PROVIDER`, `PARTIAL`, `FAILED_SYSTEM`, `SKIPPED`) to rigorously distinguish model reasoning outcomes from external provider/network/system failures.
  - Machine-readable JSON output: `evaluation/reports/latest.json`.
  - Human-readable Markdown output: `evaluation/reports/latest.md`.
  - Structured Pydantic schemas (`evaluation/schemas.py`).
  - Evaluated Baselines (`evaluation/adapters/`).
- **Ground-Truth Isolation Law**:
  - Automated AST import validation (`tests/test_ground_truth_isolation.py`) rigorously confirms zero imports of `ground_truth`, `tests`, or benchmark datasets in `app/`.
  - Zero hardcoded `CASE-` identifiers in production request-serving code.
- **Controlled Failure-Mode Tests (`tests/test_failure_modes.py`, `tests/test_neo4j_removal_experiment.py`, `tests/test_agent_necessity_experiment.py`, `tests/test_evidence_chain_trace.py`)**:
  - 14 dedicated failure and architectural proof tests.
- **FastAPI backend with `GET /health` and full investigations API endpoints**:
  - `POST /api/investigations`: End-to-end investigation execution through agentic tool selection, deterministic validation, and state machine transition.
  - `GET /api/investigations/{id}`: Retrieval of investigation state, findings, validation results, cited evidence, and agent execution metrics.
  - `GET /api/investigations/{id}/events`: Retrieval of immutable chronological audit event timeline.
  - `GET /api/investigations/{id}/trace`: Retrieval of machine-readable evidence trace for audit and verification.
- **Controlled Agentic Loop (`app.agent`)**:
  - Strict architectural authority boundary: *"AI handles ambiguity. Code handles authority"*.
  - Real LLM decision adapter (`LLMDecisionModel` in `app.agent.llm_model.py`) connecting to any OpenAI-compatible provider/proxy.
  - Pluggable Agent Models (`HeuristicAgentModel`, `ScriptedAgentModel`, `LLMDecisionModel`, `AdaptiveAgentModel`).
  - 7 deterministic tools interfacing with `LineageRepository`.
  - Comprehensive audit logging recording every `AGENT_DECISION`, `TOOL_CALL`, and `EVIDENCE_FOUND` event.
- **Next.js frontend with system status page**.

## Current Limitations

- **Live LLM Reasoning Benchmark Pending Active Provider Run**: While evaluation infrastructure, schemas, adapters, and fail-closed handling are fully implemented and verified, live LLM reasoning accuracy, tool-selection accuracy, evidence recall, and token efficiency remain unmeasured due to provider quota exhaustion (HTTP 429). A live run with active provider credits is required before making any claims regarding model reasoning performance.
- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. Durable persistence (PostgreSQL/Neo4j) will be introduced in future persistence milestones.
- **Simulated Seed Dataset**: All evidence, contracts, invoices, and approvals are synthetic simulated records created for testing and evaluation. No live enterprise connections exist.
- **Heuristic Baseline Default**: `AGENT_MODEL=heuristic` is active by default so CI and tests remain 100% deterministic and offline. External LLM requires explicit configuration or test flags.
- **Live LLM Unevaluated in Default Runner**: Default `python evaluation/runner.py` evaluates Baseline A and Baseline B, explicitly marking live LLM as unevaluated to avoid fabricated claims or uncredited external API calls.

## What Does Not Exist Yet (Intentionally)

- Persistent memory / Meterless H-MEM
- Multi-agent systems / Zetaris data integration
- Evidence ingestion pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization
- Full investigation web dashboard UI
- Background Celery/Redis workers

## Next Steps

**Stage 19**: Persistence Layer & Multi-Source Ingestion — durable database storage for investigations/events and external evidence connectors.
