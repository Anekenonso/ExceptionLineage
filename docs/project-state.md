# Project State

## Current Stage

**Stage 15** — Investigation State Machine COMPLETE.

## What Works

- FastAPI backend with `GET /health` endpoint
- Next.js frontend with system status page
- Backend test suite with 187 passing unit/integration tests and 1 conditional live test (pytest)
- Core domain models and contracts in `app.models`:
  - `Customer`
  - `Contract`, `Amendment`, `SOW`
  - `Exception` (aliased as `TransactionException`), `Approval`
  - `Invoice` (exact Decimal money representation)
  - `Evidence` (source tracking, locator, confidence bounded $[0.0, 1.0]$, effective date ranges)
  - `Investigation` (lifecycle statuses, `investigation_id`, `current_state`, `created_at`, `updated_at`)
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
  - 100% benchmark compliance verified across all 8 cases through `InvestigationService.run_investigation`
  - Zero runtime dependency or leakage from ground truth datasets
- Automated dataset consistency and schema validation test suite (`apps/api/tests/test_dataset_consistency.py`)
- Data contract documentation (`docs/data-contracts.md`), dataset specification (`data/README.md`), and ADRs (`docs/decisions.md`)

## Current Limitations

- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. It does not persist across application restarts. Durable persistence (PostgreSQL/Neo4j) will be introduced in future persistence milestones.
- **No LLM Agent Yet**: The system orchestrates graph retrieval and deterministic validation through code. Autonomous agent planning and natural language reasoning will be integrated on top of this state boundary in subsequent stages.

## What Does Not Exist Yet (Intentionally)

- Autonomous investigation agent & LLM prompts
- Zetaris data integration
- Evidence ingestion and automated multi-source retrieval pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization

## Next Steps

**Stage 16**: Vertical Slice Integration — connecting the API, state machine, graph retrieval, and deterministic validation engine into an end-to-end executable pipeline.

