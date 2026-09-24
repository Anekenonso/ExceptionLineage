# Project State

## Current Stage

**Stage 14** — Deterministic Validation Engine COMPLETE.

## What Works

- FastAPI backend with `GET /health` endpoint
- Next.js frontend with system status page
- Backend test suite with 144 passing unit/integration tests and 1 conditional live test (pytest)
- Core domain models and contracts in `app.models`:
  - `Customer`
  - `Contract`, `Amendment`, `SOW`
  - `Exception` (aliased as `TransactionException`), `Approval`
  - `Invoice` (exact Decimal money representation)
  - `Evidence` (source tracking, locator, confidence bounded $[0.0, 1.0]$, effective date ranges)
  - `Investigation` (8 lifecycle statuses), `InvestigationEvent` (audit trail)
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
- Automated dataset consistency and schema validation test suite (`apps/api/tests/test_dataset_consistency.py`)
- Data contract documentation (`docs/data-contracts.md`), dataset specification (`data/README.md`), and ADRs (`docs/decisions.md`)

## What Does Not Exist Yet (Intentionally)

- Investigation agent engine & LLM prompts
- Zetaris data integration
- Evidence ingestion and automated retrieval pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization

## Next Steps

**Stage 15**: Investigation Agent Engine & Orchestration to bridge AI ambiguity handling with deterministic code authority.

