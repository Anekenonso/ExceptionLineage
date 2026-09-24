# Project State

## Current Stage

**Stage 12** — Controlled Data + Ground Truth established.

## What Works

- FastAPI backend with `GET /health` endpoint
- Next.js frontend with system status page
- Backend test suite with 85 passing tests (pytest)
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
- Automated dataset consistency and schema validation test suite (`apps/api/tests/test_dataset_consistency.py`)
- Data contract documentation (`docs/data-contracts.md`), dataset specification (`data/README.md`), and ADRs (`docs/decisions.md`)

## What Does Not Exist Yet (Intentionally)

- Neo4j graph database integration / queries
- Investigation agent engine & LLM prompts
- Deterministic validation engine logic
- Zetaris data integration
- Evidence ingestion and automated retrieval pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization

## Next Steps

**Stage 13**: Graph Schema & Seed Loader (or Deterministic Validation Rules) to map seed records into graph nodes and relationships in Neo4j, enabling graph-based evidence traversal.
