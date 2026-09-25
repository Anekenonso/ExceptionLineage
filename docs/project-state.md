# Project State

## Current Stage

**Stage 18** — ENGINEERING COMPLETE — LIVE LLM PERFORMANCE PENDING ACTIVE PROVIDER RUN

## What Works

- **Reproducible Evaluation Harness (`evaluation/`)**:
  - Main CLI entry point: `evaluation/runner.py` executable via `python evaluation/runner.py`.
  - Explicit status taxonomy (`COMPLETED`, `BLOCKED_PROVIDER`, `PARTIAL`, `FAILED_SYSTEM`, `SKIPPED`) to rigorously distinguish model reasoning outcomes from external provider/network/system failures.
  - Machine-readable JSON output: `evaluation/reports/latest.json`.
  - Human-readable Markdown output: `evaluation/reports/latest.md`.
  - Structured Pydantic schemas (`evaluation/schemas.py`):
    - `CaseResult`: per-case metrics, actual vs expected status, evidence recall, tool execution counts, failure counters, provider failure classification, tokens.
    - `AggregateMetrics`: measurability flag (`is_measurable`), unmeasurable reason, provider failure counters/categories, accuracy, mean/overall evidence recall, tool usage rollups, termination breakdown, error breakdown, duration, tokens.
    - `EvaluationRun`: complete baseline run results with sanitized configuration (no secrets) and explicit status.
    - `EvaluationSuiteReport`: multi-baseline comparative report with overall status.
  - Transparent metric calculations (`evaluation/metrics.py`):
    - Outcome accuracy: $\text{Correct} / \text{Total}$ (reported as null / unmeasurable when run is blocked by provider).
    - Evidence recall: $\frac{|\text{Retrieved} \cap \text{Required}|}{|\text{Required}|}$ (reported as null / unmeasurable when model never executed).
    - Fine-grained tool and failure metrics without misleading composite weights.
  - Evaluated Baselines (`evaluation/adapters/`):
    - **Baseline A (`deterministic_baseline`)**: Direct `ValidationEngine` execution across simulated lineages (**100.0% accuracy, 100.0% evidence recall**).
    - **Baseline B (`heuristic_baseline`)**: `InvestigationService` + `HeuristicAgentModel` (**100.0% accuracy, 100.0% evidence recall, 6.38 mean steps, 51 tool calls**).
    - **System Under Evaluation (`llm_decision_model`)**: Evaluates `LLMDecisionModel`. Operates in live mode when `--with-llm` and API keys are provided, or controlled deterministic mock mode via `--mock-llm` (**62.5% accuracy in mock mode**). Explicitly skipped/unevaluated when unconfigured to avoid external API dependency.
    - **Live LLM Provider Evaluation Attempt**: First live run against OpenAI `gpt-4o-mini` (suite `suite-b16fb5f27789`) was rejected on 8/8 cases with HTTP 429 (`insufficient_quota` / `credit_balance_exhausted`). The harness classified the run as `BLOCKED_PROVIDER` and reported model reasoning as `UNMEASURABLE`. Confirmed safe fail-closed architecture: 0 tool executions, 0 hallucinations, 0 false verifications, and all investigations safely terminated as `FAILED`.
  - Controlled dataset loader (`evaluation/dataset.py`) for the 8 benchmark cases (`CASE-001` through `CASE-008`) and extended edge cases (`CASE-009`, `CASE-010`).
- **Ground-Truth Isolation Law**:
  - Automated AST import validation (`tests/test_ground_truth_isolation.py`) rigorously confirms zero imports of `ground_truth`, `tests`, or benchmark datasets in:
    - `app/agent/`
    - `app/graph/`
    - `app/investigations/`
    - `app/api/`
    - `app/validation/`
    - `app/models/`
  - Zero hardcoded `CASE-` identifiers in production request-serving code.
- **Controlled Failure-Mode Tests (`tests/test_failure_modes.py`)**:
  - 11 dedicated tests covering all critical failure modes:
    1. Unknown tool
    2. Missing argument
    3. Invalid argument type
    4. Malformed LLM output
    5. LLM timeout
    6. Bounded retry exhaustion
    7. Tool infrastructure failure
    8. Missing evidence $\rightarrow$ `INSUFFICIENT_EVIDENCE` (never `NOT_VERIFIED`)
    9. Conflicting amendments $\rightarrow$ `NEEDS_REVIEW` (never `VERIFIED`)
    10. Expired authority $\rightarrow$ `NOT_VERIFIED`
    11. Step-limit exhaustion $\rightarrow$ `FAILED` with `AGENT_STEP_LIMIT_EXCEEDED`
- **FastAPI backend with `GET /health` and full investigations API endpoints**:
  - `POST /api/investigations`: End-to-end investigation execution through agentic tool selection, deterministic validation, and state machine transition.
  - `GET /api/investigations/{id}`: Retrieval of investigation state, findings, validation results, cited evidence, and agent execution metrics.
  - `GET /api/investigations/{id}/events`: Retrieval of immutable chronological audit event timeline (with optional `include_agent_events=True` parameter).
- **Controlled Agentic Loop (`app.agent`)**:
  - Strict architectural authority boundary: *"AI handles ambiguity. Code handles authority"*.
  - Real LLM decision adapter (`LLMDecisionModel` in `app.agent.llm_model.py`) connecting to any OpenAI-compatible provider/proxy.
  - Pluggable Agent Models (`HeuristicAgentModel`, `ScriptedAgentModel`, `LLMDecisionModel`).
  - 7 deterministic tools interfacing with `LineageRepository`.
  - Comprehensive audit logging recording every `AGENT_DECISION` and `TOOL_CALL` event.
- **Backend test suite with 265 passing tests and 2 conditional live tests (pytest)**.
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
