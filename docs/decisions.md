# Architectural Decisions

## ADR-001: Monorepo Structure

**Date:** 2026-09-23

**Decision:** Use a monorepo with `apps/web` (frontend) and `apps/api` (backend) under a single repository.

**Rationale:** ExceptionLineage is a tightly-coupled system where frontend and backend evolve together. A monorepo simplifies versioning, cross-cutting changes, and development workflow.

---

## ADR-002: Next.js + TypeScript + Tailwind CSS for Frontend

**Date:** 2026-09-23

**Decision:** Use Next.js with TypeScript and Tailwind CSS.

**Rationale:** Next.js provides server-side rendering and API routes if needed later. TypeScript enforces type safety. Tailwind CSS enables rapid, consistent styling.

---

## ADR-003: FastAPI + Pydantic for Backend

**Date:** 2026-09-23

**Decision:** Use FastAPI with Pydantic models.

**Rationale:** FastAPI provides automatic OpenAPI documentation, async support, and strong typing via Pydantic. This aligns with the need for structured evidence and validation in the investigation system.

---

## ADR-004: Placeholder Module Directories

**Date:** 2026-09-23

**Decision:** Create empty placeholder directories for future modules (agent, investigations, evidence, validation, graph, data) without implementing any logic.

**Rationale:** Establishes the intended architecture without premature implementation. Each module can be built when its requirements are clear.

---

## ADR-005: Minimal Environment Variables

**Date:** 2026-09-23

**Decision:** Only include environment variables that are actively used by the current foundation (`API_PORT`, `NEXT_PUBLIC_API_URL`).

**Rationale:** Avoids cargo-culting environment variables for systems that don't exist yet. Variables for Neo4j, Zetaris, and LLM providers will be added when those integrations are built.

---

## ADR-006: Domain Models and Data Contracts Design

**Date:** 2026-09-23

**Decision:** Define domain models in `app.models` using Pydantic v2 with explicit relationship identifiers, Decimal monetary amounts, timezone-aware UTC datetimes, explicit status enums, and a strict tri-state validation contract (`PASS`, `FAIL`, `UNKNOWN`). Avoid premature ORM or database coupling.

**Rationale:**
1. **Pydantic Models over ORM**: ExceptionLineage is an investigation engine that ingests evidence from heterogeneous systems (contracts, ERP invoices, email/approvals, graph nodes). Defining pure Pydantic data contracts keeps domain entities decoupled from specific persistence layers (e.g. Neo4j, relational DBs, or in-memory pipelines).
2. **Explicit Identifier References**: Deeply nested object graphs create circular reference challenges and enforce rigid loading lifecycles. Stable identifier fields (e.g. `customer_id`, `contract_id`, `invoice_id`, `exception_id`) mirror graph node/edge boundaries and allow modular construction.
3. **Exact Decimal Representation for Money**: Floating-point representations (e.g. IEEE 754 `float`) introduce rounding errors that can corrupt audit determinations. `Decimal` preserves exact financial amounts (e.g. `10200.00`).
4. **Explicit Status Enums**: Open-ended strings invite typographical inconsistencies. `ValidationStatus` (`PASS`, `FAIL`, `UNKNOWN`) and `InvestigationStatus` (3 active + 5 terminal states) constrain states to known legal vocabularies.
5. **Legitimate UNKNOWN State**: Missing or inconclusive evidence is an authentic condition in investigation workflows. `UNKNOWN` must never be coerced into `PASS` or `FAIL`.
6. **No Premature Complexity**: No database engine, ORM, LLM SDK, or agent loop was introduced. The models serve as the foundational contract for subsequent stages.
