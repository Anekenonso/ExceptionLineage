# Project State

## Current Stage

**Stage 19** — COMPLETE — ExceptionLineage Investigation Workspace

## What Works

- **Production-Quality Investigation Workspace Frontend (`apps/web`)**:
  - Built with Next.js 16 (App Router), React 19, and Tailwind CSS.
  - Adheres to approved enterprise SaaS direction: light background, dark typography, subtle borders, restrained status badges, desktop-first responsive layout.
  - Communicates *"Follow the evidence"* rather than decorative AI branding.
  - **Investigations Dashboard (`/investigations`)**:
    - Displays Investigation ID, Invoice ID, Customer, Amount, Status, Created Date, and Execution Duration.
    - Interactive search across IDs, invoices, and customer names.
    - Filter chips by status (`ALL`, `VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, `FAILED`).
    - "New Investigation" modal with quick preset selection for benchmark scenarios (`INV-1001` through `INV-1008`).
    - One-click benchmark case runner.
    - Seamless navigation to detail workspaces (`/investigations/[id]`).
  - **Main Investigation Workspace (`/investigations/[id]`)**:
    - Follows the required structural hierarchy:
      `HEADER ↓ INVOICE EXCEPTION + DETERMINATION ↓ LINEAGE GRAPH ↓ VALIDATION + EVIDENCE + ACTIVITY`
    - **Header**: Exposes Investigation ID, Invoice ID, Customer, Investigation Type, Current Status, Started, Completed, Duration, "Export Report" action, and "Back to Investigations" link.
    - **Invoice Exception Card**: Displays Invoice ID, Billed amount, Expected amount, Variance, Product, Invoice date, Customer, and Contract. Fields unavailable in backend data are represented as `Unavailable` / `—` rather than fabricated.
    - **Determination Card**: Prominent status card with strict adherence to domain rules:
      - `VERIFIED`: Displays backend-provided explanation and citation count.
      - `NOT_VERIFIED`: Highlights specific failed deterministic checks and violated rules.
      - `INSUFFICIENT_EVIDENCE`: Highlights missing evidence and indeterminate checks.
      - `NEEDS_REVIEW`: Highlights conflicting or unresolved contractual authority.
      - `FAILED`: Explicitly displays *"No determination was made."* without converting technical failures into business conclusions.
    - **Lineage Graph (Central Visual Element)**:
      - Interactive SVG graph rendering directional relationships: `Customer → Contract → Amendment → SOW → Approval → Invoice → Evidence`.
      - Only renders relationships returned by the backend without inventing edges.
      - Clickable nodes with status badges and an interactive Entity Inspector drawer showing full properties and raw data.
      - Zoom and reset controls with responsive DAG layout.
    - **Deterministic Validation Section**:
      - Displays check name, status (`PASS`, `FAIL`, `UNKNOWN`), cited evidence links, and explanation messages.
      - Obvious authority boundary callout: *"AI handles ambiguity. Code handles authority."*
      - Preserves tri-state semantics (`UNKNOWN` is never coerced to `PASS` or `FAIL`).
    - **Evidentiary Records Section & Drawer**:
      - Tabular display of evidence items with ID, type, source, related entity, locator/scope, and validity dates.
      - Slide-over Evidence Drawer displaying textual excerpts, legal validity dates, and confidence metrics.
    - **Investigation Activity Trace**:
      - Interactive timeline powered by `GET /api/investigations/{id}/trace`.
      - Visually differentiates: `INPUT → AGENT DECISION → TOOL CALL → GRAPH RETRIEVAL → VALIDATION → RESULT`.
      - Filterable by event type with sanitized tool arguments and redaction verification.
    - **Report Export (`ExportReportModal`)**:
      - Exports complete compliance investigation reports in both Markdown and raw JSON formats.
    - **State Handlers**:
      - Robust handling for Loading (skeletons), Empty (call-to-actions), Successful data, Insufficient evidence, Needs review, Failed investigation, and API error (with offline fixture toggle).
    - **Isolated UI Development Fixtures (`apps/web/src/fixtures/investigations.ts`)**:
      - Cleanly isolated mock dataset matching real API response contracts for offline testing across all 5 terminal states.
  - **Landing Hub (`apps/web/src/app/page.tsx`)**:
    - Direct launchpad to the Investigation Workspace.
    - Architectural overview highlighting the 3 proven claims from Stage 18.5.
    - Live system status and API health monitoring.
- **FastAPI Backend Integration (`apps/api`)**:
  - `GET /api/investigations`: Lists stored investigations with contextual customer, amount, and duration data.
  - `GET /api/investigations/{id}`: Retrieves full investigation state, findings, metrics, and lineage.
  - `GET /api/investigations/{id}/lineage`: Dedicated endpoint returning full graph lineage for the invoice.
  - `GET /api/investigations/{id}/events`: Immutable audit event timeline.
  - `GET /api/investigations/{id}/trace`: Machine-readable evidence trace for audit and verification.
  - `POST /api/investigations`: End-to-end investigation execution through agentic tool selection, deterministic validation, and state machine transition.
  - Safe offline graph fallback (`InMemoryLineageRepository` populated from `data/seed` when Neo4j is offline).
- **Backend Test Suite with 280 tests (278 passing, 2 conditional live tests)**.
- **Ground-Truth Isolation Law**:
  - AST verification confirms zero imports of `ground_truth`, `tests`, or benchmark datasets in `app/`.
  - Zero hardcoded `CASE-` identifiers in production request-serving code.

## Current Limitations

- **In-Memory Persistence Only**: The current `InMemoryInvestigationRepository` holds lifecycle state in volatile application memory. Durable persistence (PostgreSQL/Neo4j) will be introduced in future persistence milestones.
- **Simulated Seed Dataset**: All evidence, contracts, invoices, and approvals are synthetic simulated records created for testing and evaluation. No live enterprise connections exist.
- **Live LLM Reasoning Benchmark Pending Active Provider Run**: While evaluation infrastructure, schemas, adapters, and fail-closed handling are fully implemented and verified, live LLM reasoning accuracy, tool-selection accuracy, evidence recall, and token efficiency remain unmeasured due to provider quota exhaustion (HTTP 429).
- **Heuristic Baseline Default**: `AGENT_MODEL=heuristic` is active by default so CI and tests remain 100% deterministic and offline. External LLM requires explicit configuration or test flags.

## What Does Not Exist Yet (Intentionally)

- Persistent PostgreSQL / Meterless H-MEM
- Multi-agent systems / Zetaris data integration
- Evidence ingestion pipelines
- User authentication and authorization
- Background Celery/Redis workers

## Next Steps

**Stage 20**: Durable Persistence & External Connectors — PostgreSQL storage for investigations/events and external enterprise connectors.

