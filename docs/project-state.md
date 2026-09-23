# Project State

## Current Stage

**Stage 11** — Domain Models + Data Contracts established.

## What Works

- FastAPI backend with `GET /health` endpoint
- Next.js frontend with system status page
- Backend test suite with 57 passing tests (pytest)
- Core domain models and contracts in `app.models`:
  - `Customer`
  - `Contract`, `Amendment`, `SOW`
  - `Exception` (aliased as `TransactionException`), `Approval`
  - `Invoice` (exact Decimal money representation)
  - `Evidence` (source tracking, locator, confidence bounded $[0.0, 1.0]$, effective date ranges)
  - `Investigation` (8 lifecycle statuses), `InvestigationEvent` (audit trail)
  - `ValidationResult` (tri-state: `PASS`, `FAIL`, `UNKNOWN`)
- Data contract documentation (`docs/data-contracts.md`) and architectural decision records (`docs/decisions.md`)

## What Does Not Exist Yet (Intentionally)

- Investigation agent engine
- LLM integrations / prompts
- Neo4j graph database integration / queries
- Zetaris data integration
- Deterministic validation engine logic
- Evidence ingestion and retrieval pipelines
- Production seed dataset / fake evaluation results
- User authentication and authorization

## Next Steps

**Stage 12**: Graph schema definition & initial repository/graph representation (or deterministic validation rules) to connect contracts, invoices, and evidence relationships.
