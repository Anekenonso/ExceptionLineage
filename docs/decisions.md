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
