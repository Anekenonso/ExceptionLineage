# Project State

## Current Stage

**Stage 16** — First Real Vertical Slice COMPLETE.

## What Works

- FastAPI backend with `GET /health` and full investigations API endpoints:
  - `POST /api/investigations`: End-to-end investigation execution from HTTP request to verified determination.
  - `GET /api/investigations/{id}`: Retrieval of investigation state, findings, validation results, and evidence citations.
  - `GET /api/investigations/{id}/events`: Retrieval of immutable chronological audit event timeline.
- Next.js frontend with system status page
- Backend test suite with 204 passing unit/integration tests and 1 conditional live test (pytest)
- Core domain models and contracts in `app.models`:
  - `Customer`
  - `Contract`, `Amendment`, `SOW`
  - `Exception` (aliased as `TransactionException`), `Approval`
  - `Invoice` (exact Decimal money representation)
  - `Evidence` (source tracking, locator, confidence bounded $[0.0, 1.0]$, effective date ranges)
  - `Investigation` (lifecycle statuses, `investigation_id`, `current_state`, `created_at`, `updated_at`, `validation_results`, `cited_evidence_ids`)
  - `InvestigationEvent` (immutable audit trail, `from_state`, `to_state`, `reason`, `timestamp`)
  - `ValidationResult` (tri-state: `PASS`, `FAIL`, `UNKNOWN`)
- Controlled simulated dataset (`data/seed/`):
  - Customers, contracts, amendments, SOWs, exceptions, approvals, invoices, and evidence records
- 8 controlled investigation cases (`data/cases/cases.json`)
- Explicit machine-verifiable ground truth determinations (`data/ground_truth/ground_truth.json`)
- Neo4j Graph Integration (`app.graph`):
  - Graph schema with deterministic labels, unique constraints, and multi-hop indexes (`app.graph.schema`)
  - Direct official Neo4j Python client wrapper with connection management (`app.graph.client`)
  - Idempotent, deterministic seed data loader (`app.graph.loader`) with exact decimal preservation (`amount: str`, `amount_cents: int`)
  - Deterministic graph queries for investigation traversal (`app.graph.queries`)
  - Graph lineage retrieval abstraction (`LineageRepository`, `Neo4jLineageRepository`, `InMemoryLineageRepository` in `app.graph.lineage`)
  - Ground truth verifier validating graph state across all 8 benchmark cases (`app.graph.verifier`)
  - Docker Compose Neo4j 5 community service configuration with health-ready ports
  - Test suites runnable without Docker or live database dependency
- Deterministic Validation Engine (`app.validation`):
  - Clean separation of retrieval and evaluation via `InvestigationContext`
  - 8 core deterministic rules (`CustomerGoverningContractRule`, `ContractApplicabilityRule`, `ConflictingAuthorityRule`, `ApplicableAmendmentRule`, `AmendmentEffectivenessRule`, `AmendmentScopeRule`, `ApprovalAuthorizationRule`, `AuthorizedAmountRule`)
  - Tri-state verification (`PASS`, `FAIL`, `UNKNOWN`)
  - Conflict-aware outcome aggregation into `InvestigationOutcome` (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`)
  - Zero runtime dependence on ground-truth files or hardcoded case IDs
  - Automated benchmark test suite confirming 100% accuracy on all 8 ground-truth cases (`tests/test_validation_benchmark.py`)
- Controlled Investigation State Machine (`app.investigations`):
  - Strict lifecycle authority boundary implementing *"AI handles ambiguity. Code handles authority"*
  - Explicit valid transitions:
    - `QUEUED → INVESTIGATING`
    - `INVESTIGATING → VALIDATING | FAILED`
    - `VALIDATING → VERIFIED | NOT_VERIFIED | INSUFFICIENT_EVIDENCE | NEEDS_REVIEW | FAILED`
  - Explicit terminal states (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, `FAILED`) that reject any subsequent transition
  - Deterministic transition rejection with `InvalidStateTransitionError` identifying investigation ID, current state, and requested state
  - Immutable audit event history (`InvestigationEvent`) capturing every state change with `from_state`, `to_state`, `reason`, and `timestamp`
  - Direct 1:1 mapping from deterministic validation outcomes (`ValidationOutcome`) to terminal investigation states
  - Strict distinction between business investigation results (`INSUFFICIENT_EVIDENCE` / `NOT_VERIFIED`) and technical failures (`FAILED`)
  - In-memory repository abstraction (`InvestigationRepository`, `InMemoryInvestigationRepository`)
  - Non-agent investigation skeleton orchestration via `InvestigationService`
- End-to-End Vertical Slice (`apps/api/app/investigations/router.py`, `apps/api/app/investigations/service.py`):
  - Complete execution flow: `HTTP POST /api/investigations` $\rightarrow$ `QUEUED` $\rightarrow$ `INVESTIGATING` $\rightarrow$ Graph traversal via `LineageRepository` $\rightarrow$ `InvestigationContext` $\rightarrow$ `VALIDATING` $\rightarrow$ `ValidationEngine.validate` $\rightarrow$ `ValidationOutcome` $\rightarrow$ `InvestigationStateMachine` $\rightarrow$ Terminal outcome $\rightarrow$ `InvestigationResponse`
  - Infrastructure failure handling cleanly maps graph retrieval exceptions to `FAILED` (2 events, no fabricated evidence)
  - 100% accuracy verified across all 8 controlled benchmark cases through both HTTP API and service interfaces
  - Zero runtime dependency or leakage from ground truth datasets
- Automated dataset consistency and schema validation test suite (`apps/api/tests/test_dataset_consistency.py`)
- Data contract documentation (`docs/data-contracts.md`), dataset specification (`data/README.md`), and ADRs (`docs/decisions.md`)

## Current Limitations

- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. It does not persist across application restarts. Durable persistence (PostgreSQL/Neo4j) will be introduced in future persistence milestones.
- **Simulated Seed Dataset**: All evidence, contracts, invoices, and approvals are synthetic simulated records created for testing and evaluation. No live enterprise connections exist.
- **No LLM Agent Yet**: The system orchestrates graph retrieval and deterministic validation through code. Autonomous agent planning and natural language reasoning will be integrated on top of this state boundary in subsequent stages.
- **Neo4j Offline by Default in CI/Local**: Tests utilize `InMemoryLineageRepository` or mocks so Neo4j is not strictly required for local development or automated verification.

## What Does Not Exist Yet (Intentionally)

- Autonomous investigation agent & LLM prompts
- Zetaris data integration
- Evidence ingestion and automated multi-source retrieval pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization
- Full investigation web dashboard UI

## Next Steps

**Stage 17**: Investigation Agent Foundation — introducing LLM-driven planning and reasoning while strictly preserving the Stage 15/16 state machine authority boundary (*AI handles ambiguity. Code handles authority*).

