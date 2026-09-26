# Project State

## Current Stage

**Stage 20.5** — COMPLETE — Product UX & Language Refinement

## What Works

- **End-to-End Application Workflow**:
  - Full coherent stack from Browser UI (`apps/web` on Next.js 16 / React 19) → FastAPI Backend (`apps/api` on Python 3.11) → Investigation Service → Investigation Agent Loop → Tool Execution → Lineage Graph → Evidentiary Records → Deterministic Validation Engine → Real-time UI Presentation.
  - 100% reproducible demo execution across all 8 controlled benchmark scenarios (`INV-1001` through `INV-1008`).

- **Flagship Demo Path (`INV-1001`)**:
  - Demonstrates full evidence-backed contractual verification under Master Services Agreement `CTR-001`, Amendment `AMD-001`, and Operational Approval `APR-001`.
  - 8/8 deterministic validation checks pass.
  - Interactive SVG lineage graph visualizes full directional chain `Customer → Contract → Amendment → Approval → Invoice → Evidence`.
  - Side-drawer inspection reveals verbatim contract/approval excerpts and validity timestamps.
  - Complete machine-readable audit trace exported in Markdown and JSON.

- **Contrasting Uncertainty & Failure Demonstrations**:
  - **`INV-1002` (Insufficient Evidence)**: Correctly flags missing approval documentation as `UNKNOWN` rather than guessing, yielding `INSUFFICIENT_EVIDENCE`.
  - **`INV-1003` (Contractual Non-Compliance)**: Correctly rejects unauthorized rate deduction exceeding contractual threshold, yielding `NOT_VERIFIED`.
  - **`INV-1005` (Conflicting Authority)**: Correctly identifies competing amendment terms without clear precedence, routing to human review via `NEEDS_REVIEW`.
  - **Failure Handling**: Technical or infrastructure errors (invalid IDs, graph timeouts) transition to `FAILED` with explicit UI notice: *"No determination was made."* No infrastructure failure is converted into a business conclusion.

- **Visual QA & Enterprise UI Polish**:
  - Refined enterprise SaaS styling with light backgrounds, crisp dark typography, restrained status badges, and zero decorative AI fluff.
  - Preserves tri-state deterministic logic (`UNKNOWN` is never coerced to `PASS` or `FAIL`).
  - Authority boundary callout: *"AI investigates. Deterministic logic verifies."*
  - Responsive, desktop-first layouts with smooth loading skeletons and zero layout shifts.

- **Deployment & Production Readiness**:
  - Frontend production build succeeds cleanly (`npm run build` / Next.js Turbopack).
  - TypeScript static type check passed (`tsc --noEmit` clean with 0 errors).
  - Backend API health endpoint (`GET /health`) active and responsive.
  - Safe offline graph fallback (`InMemoryLineageRepository` populated from `data/seed` when Neo4j is offline).
  - Complete test suite passes: 278 unit/integration tests passing (2 skipped conditional live tests).
  - Architectural evaluation verified: Claim A (Adaptive Investigation Value — DEMONSTRATED), Claim B (Relationship-Aware Retrieval — DEMONSTRATED), Claim C (End-to-End Evidence Chain — VERIFIED).

## Verified Benchmark Scenarios Matrix

| Scenario | Invoice ID | Customer | Amount | Status | Validation Result | Core Determination Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INV-1001** | `INV-1001` | Acme Global | $10,200.00 | `VERIFIED` | 8 PASS, 0 FAIL, 0 UNKNOWN | Rate adjustment verified under CTR-001, AMD-001, APR-001 |
| **INV-1002** | `INV-1002` | Acme Global | $11,500.00 | `INSUFFICIENT_EVIDENCE` | 7 PASS, 0 FAIL, 1 UNKNOWN | Surcharge variance with missing approval evidence |
| **INV-1003** | `INV-1003` | Acme Global | $9,500.00 | `NOT_VERIFIED` | 6 PASS, 1 FAIL, 1 UNKNOWN | Rate discrepancy exceeds allowed contract threshold |
| **INV-1004** | `INV-1004` | Acme Global | $8,000.00 | `NOT_VERIFIED` | 5 PASS, 2 FAIL, 1 UNKNOWN | Expired amendment & unauthorized rate reduction |
| **INV-1005** | `INV-1005` | Acme Global | $14,000.00 | `NEEDS_REVIEW` | 6 PASS, 1 FAIL, 1 UNKNOWN | Conflicting amendment & SOW terms |
| **INV-1006** | `INV-1006` | Acme Global | $15,000.00 | `NOT_VERIFIED` | 5 PASS, 2 FAIL, 1 UNKNOWN | Quantity modifier exceeds authorized SOW ceiling |
| **INV-1007** | `INV-1007` | Beta Logistics | $4,500.00 | `INSUFFICIENT_EVIDENCE` | 1 PASS, 0 FAIL, 7 UNKNOWN | Orphaned invoice missing governing master contract |
| **INV-1008** | `INV-1008` | Beta Logistics | $18,000.00 | `VERIFIED` | 8 PASS, 0 FAIL, 0 UNKNOWN | Multi-tier SOW with verified VP approval |

## Current Limitations & Remaining Deployment Steps

- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. Durable persistence (PostgreSQL) will be introduced in future persistence milestones.
- **Simulated Seed Dataset**: All evidence, contracts, invoices, and approvals are synthetic simulated records created for testing and evaluation. No live enterprise ERP connections exist.
- **Live LLM Reasoning Benchmark**: While evaluation infrastructure, schemas, adapters, and fail-closed handling are fully implemented and verified, live external LLM calls depend on active provider API quotas. `AGENT_MODEL=heuristic` provides deterministic, offline-reliable demo execution.
- **Remaining Production Cloud Deployment Steps**:
  1. Provision Docker container runtime (e.g. AWS ECS / Google Cloud Run) using `docker-compose.yml` or container manifests.
  2. Configure production domain SSL/TLS certificate and reverse proxy.
  3. Supply live production environment secrets (`NEO4J_URI`, `NEO4J_PASSWORD`, `AGENT_LLM_API_KEY`, `NEXT_PUBLIC_API_URL`).
  4. Run container health check against `GET /health`.

## What Does Not Exist Yet (Intentionally)

- Persistent PostgreSQL / Meterless H-MEM
- Multi-agent systems / Zetaris data integration
- Evidence ingestion pipelines
- User authentication and authorization
- Background Celery/Redis workers

## Stage 20.5 — Product UX & Language Refinement

Completed full product positioning, information hierarchy, and visual refinement to achieve "Simple Surface, Sophisticated Engine":

- **Product Language Refinement**:
  - Replaced internal engineering/evaluation jargon across the primary customer UX.
  - Positioned product as: *"Understand why a transaction was flagged. ExceptionLineage traces invoices through contracts, amendments, SOWs and approvals to explain what happened and whether the available records support the charge."*
  - Internal backend enums preserved while frontend translates:
    - `VERIFIED` → **Verified**
    - `NOT_VERIFIED` → **Not verified**
    - `INSUFFICIENT_EVIDENCE` → **Not enough evidence**
    - `NEEDS_REVIEW` → **Needs review**
    - `FAILED` → **Review couldn't be completed**
    - `QUEUED` → **Queued**
    - `INVESTIGATING` → **Investigating**
    - `VALIDATING` → **Verifying**
    - `PASS` → **Passed**, `FAIL` → **Failed**, `UNKNOWN` → **Not available**

- **Primary Navigation**:
  - Restructured to: **ExceptionLineage** (Brand), **Overview**, **Investigations**, **Evidence**, **Reports**.
  - Replaced engineering action buttons with **Review an invoice**.
  - Moved system/engine connectivity status to a secondary, non-intrusive status popover.
  - Removed internal stage development badges from navigation and primary views.

- **Information Hierarchy**:
  - Restructured investigation workspace into a clear operational hierarchy:
    1. **Invoice**: Clean business metadata (invoice number, customer, amount, currency, issuance date, flagged reason).
    2. **Finding**: Visual focal point with human-friendly determination statements.
    3. **Why**: Concise, evidence-backed explanations translating raw validation checks into plain business language.
    4. **Verification checks**: Renamed from "Validation Engine", showing human-readable checks with pass/fail/unavailable status and cited records.
    5. **Contract history**: Renamed from "Lineage Graph", highlighting how the invoice connects to the contract, amendments, SOWs, and approvals.
    6. **Supporting records**: Renamed from "Evidentiary Records", with clean clause excerpts, source references, and validity dates.
    7. **Investigation activity**: Human-readable execution timeline first (Invoice received → Contract identified → Amendment reviewed → Approval checked → Finding reached).
    8. **Technical trace**: Granular tool execution, agent decisions, graph retrievals, and raw JSON arguments moved behind a collapsible **View technical trace** secondary interaction.

- **Authority Boundary / How We Verify**:
  - Redesigned from a dominant banner into a concise, reassuring explanation: *"How we verify: AI helps investigate the available records. Verification is performed using deterministic checks against the evidence found."*

- **Visual Quality & Responsive UX**:
  - Stripe/Linear-inspired light neutral palette (`bg-slate-50`, `bg-white`, subtle borders, restrained badge colors).
  - Clean typography: sans-serif for UI copy, monospace strictly reserved for IDs, timestamps, code, and raw trace data.
  - Fully responsive on desktop, tablet, and mobile with zero horizontal overflow.

- **Verification Results**:
  - Backend tests: 278 passed, 2 skipped (100% passing across unit/integration tests).
  - TypeScript type check (`tsc --noEmit`): clean with 0 errors.
  - Frontend production build (`next build` / Turbopack): clean with 0 errors.
  - Zero backend changes, zero logic changes, zero API contract regressions.

## Next Steps

- **Post-Hackathon Roadmap**: Production data ingestion connectors and durable database backends.
