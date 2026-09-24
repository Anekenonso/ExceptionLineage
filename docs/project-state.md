# Project State

## Current Stage

**Stage 17.5** — Real LLM Decision Layer COMPLETE.

## What Works

- FastAPI backend with `GET /health` and full investigations API endpoints:
  - `POST /api/investigations`: End-to-end investigation execution through agentic tool selection, deterministic validation, and state machine transition.
  - `GET /api/investigations/{id}`: Retrieval of investigation state, findings, validation results, cited evidence, and agent execution metrics.
  - `GET /api/investigations/{id}/events`: Retrieval of immutable chronological audit event timeline (with optional `include_agent_events=True` parameter).
- Real LLM Decision Layer & Controlled Agentic Loop (`app.agent`):
  - Strict architectural authority boundary: *"AI handles ambiguity. Code handles authority"*
  - Real LLM decision adapter (`LLMDecisionModel` in `app.agent.llm_model.py`) connecting to any OpenAI-compatible provider/proxy:
    - Structured JSON output enforcement (`AgentAction`: `action`, `arguments`, `reason`)
    - Dynamic machine-readable tool schemas (`ToolRegistry.get_tool_definitions()`) passed in system prompt
    - Compact, leak-free state formatting (`_format_state`)
    - Upfront tool argument validation (`ToolRegistry.validate_action`) checking existence, argument names, types, and rejecting unexpected arguments
    - Single bounded retry for malformed JSON or invalid schema
    - Strict technical failure semantics (timeouts, HTTP 401/403/429/500 raise `AgentToolExecutionError` $\rightarrow$ `FAILED`)
  - Pluggable Agent Models via `app.agent.factory`:
    - `HeuristicAgentModel`: Preserved as the default baseline (`AGENT_MODEL=heuristic`)
    - `ScriptedAgentModel`: Deterministic mock sequences for testing
    - `LLMDecisionModel`: Configured via `AGENT_MODEL=llm`, `AGENT_LLM_PROVIDER`, `AGENT_LLM_MODEL`, `AGENT_LLM_API_KEY`, `AGENT_LLM_BASE_URL`
  - Explicit typed tool abstraction (`app.agent.tools.base.BaseTool`, `ToolRegistry`)
  - 7 deterministic tools interfacing with `LineageRepository`:
    1. `get_invoice`
    2. `find_contract`
    3. `get_contract_amendments`
    4. `get_sows`
    5. `find_approvals`
    6. `get_related_evidence`
    7. `validate_investigation`
  - Explicit Agent State (`AgentState`) tracking observations, gathered entities, tool call history, and missing evidence
  - Bounded agent loop (`InvestigationAgent`) with configurable `MAX_AGENT_STEPS` (default: 10)
  - Loop exhaustion error handling (`AgentStepLimitExceededError` $\rightarrow$ `FAILED` with `AGENT_STEP_LIMIT_EXCEEDED`)
  - Agent-specific operational and LLM metrics (`AgentMetrics`: `total_agent_steps`, `tool_calls`, `successful_tool_calls`, `failed_tool_calls`, `investigation_duration_ms`, `evidence_items_collected`, `duplicate_tool_calls`, `termination_reason`, `llm_calls`, `llm_failures`, `llm_retries`, `malformed_actions`, `prompt_tokens`, `completion_tokens`, `total_tokens`)
  - Comprehensive audit logging recording every `AGENT_DECISION` (including model name/provider) and `TOOL_CALL` event
  - Benchmark comparison suite (`test_agent_benchmark_comparison.py`) capturing steps, tool calls, evidence, duration, and status across all 8 cases
  - Live LLM integration test (`test_llm_integration.py`) gated behind `RUN_LLM_AGENT_TESTS=true`
- Next.js frontend with system status page (production build verified clean)
- Backend test suite with 237 passing unit/integration tests and 2 conditional live tests (pytest)
- Core domain models and contracts in `app.models`:
  - `Customer`
  - `Contract`, `Amendment`, `SOW`
  - `Exception` (aliased as `TransactionException`), `Approval`
  - `Invoice` (exact Decimal money representation)
  - `Evidence` (source tracking, locator, confidence bounded $[0.0, 1.0]$, effective date ranges)
  - `Investigation` (lifecycle statuses, `investigation_id`, `current_state`, `created_at`, `updated_at`, `validation_results`, `cited_evidence_ids`, `agent_metrics`)
  - `InvestigationEvent` (immutable audit trail, `from_state`, `to_state`, `reason`, `timestamp`, `event_type`, `metadata`)
  - `ValidationResult` (tri-state: `PASS`, `FAIL`, `UNKNOWN`)
- Controlled simulated dataset (`data/seed/`)
- 8 controlled investigation cases (`data/cases/cases.json`)
- Explicit machine-verifiable ground truth determinations (`data/ground_truth/ground_truth.json`)
- Neo4j Graph Integration (`app.graph`)
- Deterministic Validation Engine (`app.validation`)
- Controlled Investigation State Machine (`app.investigations`)
- End-to-End Vertical Slice with Agent Loop (`app/investigations/router.py`, `app/investigations/service.py`)

## Current Limitations

- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. Durable persistence (PostgreSQL/Neo4j) will be introduced in future persistence milestones.
- **Simulated Seed Dataset**: All evidence, contracts, invoices, and approvals are synthetic simulated records created for testing and evaluation. No live enterprise connections exist.
- **Heuristic Baseline Default**: `AGENT_MODEL=heuristic` is active by default so CI and tests remain 100% deterministic and offline. External LLM requires explicit configuration or test flags.
- **Neo4j Offline by Default in CI/Local**: Tests utilize `InMemoryLineageRepository` or mocks so Neo4j is not strictly required for local development or automated verification.

## What Does Not Exist Yet (Intentionally)

- Persistent memory / Meterless H-MEM
- Multi-agent systems / Zetaris data integration
- Evidence ingestion pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization
- Full investigation web dashboard UI
- Background Celery/Redis workers

## Next Steps

**Stage 18**: Persistence Layer & Multi-Source Ingestion — durable database storage for investigations/events and external evidence connectors.


