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

---

## ADR-007: Controlled Synthetic Dataset and Ground Truth

**Date:** 2026-09-24

**Decision:** Create a compact, controlled, relationally dense synthetic dataset (8 investigation cases) with machine-verifiable ground truth determinations across `VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, and `NEEDS_REVIEW`. Mark all data clearly as `SIMULATED` and enforce automated data consistency via pytest.

**Rationale:**
1. **Objective Evaluation over Subjective Assessment**: AI-driven and graph-driven investigation engines cannot be reliably evaluated without definitive ground truth. Having structured ground-truth records ensures that future pipeline accuracy can be computed objectively and deterministically.
2. **Controlled Adversarial Scenarios**: Real-world exceptions fail for diverse reasons (missing approvals, expired effective dates, scope/product mismatches, conflicting amendments, missing contracts). Creating intentionally flawed cases guarantees the system will not default to superficial pass-through verification.
3. **Relationally Dense, Small Footprint**: Rather than generating hundreds of disconnected rows, 8 well-crafted cases sharing 3 customers and 2 master agreements test deep multi-hop evidence traversal ($\text{Invoice} \rightarrow \text{Customer} \rightarrow \text{Contract} \rightarrow \text{Amendment} \rightarrow \text{SOW} \rightarrow \text{Exception} \rightarrow \text{Approval}$) without unmanageable dataset bloat.
4. **Automated Schema & Consistency Checking**: All seed data is asserted against Stage 11 Pydantic models in the test suite. Foreign keys, date logic, Decimal values, and ground truth references are validated continuously to prevent drift.
5. **No Production Data or Fake Citations**: All records are explicitly identified as simulated data to avoid compliance risks or confusion with real-world enterprise contracts.

---

## ADR-008: Neo4j Graph Schema, Deterministic Identifiers, and Precision Representation

**Date:** 2026-09-24

**Decision:** Integrate Neo4j using the official Python driver (`neo4j>=5.26.0,<6.0.0`) to model domain entities as uniquely constrained nodes (`Customer`, `Contract`, `Amendment`, `SOW`, `Exception`, `Approval`, `Invoice`, `Evidence`) and explicit, typed relationships (`HAS_CONTRACT`, `HAS_AMENDMENT`, `AMENDS`, `HAS_SOW`, `UNDER_CONTRACT`, `HAS_EXCEPTION`, `HAS_APPROVAL`, `APPROVES`, `BILLED_TO`, `HAS_INVOICE`, `GOVERNED_BY`, `HAS_EVIDENCE`, `EVIDENCE_FOR`). Store exact monetary values as formatted strings (e.g. `"10200.00"`) alongside integer cents (e.g. `1020000`) to completely eliminate floating-point precision drift.

**Rationale:**
1. **Direct Official Driver without Layer Bloat**: Avoid third-party OGM layers, GraphRAG frameworks, or LLM agent wrappers. The official driver provides direct Cypher execution, low overhead, and straightforward connection lifecycle management.
2. **Deterministic Domain Identifiers**: Avoid Neo4j internal element IDs. Every node is identified by its stable domain key (`id`, e.g. `CUS-001`, `CTR-001`, `INV-1001`) with explicit unique constraints (`REQUIRE n.id IS UNIQUE`).
3. **Exact Monetary Precision in Graph Properties**: Neo4j does not have a native arbitrary-precision Decimal type. Converting financial decimals to 64-bit IEEE floats risks precision drift (e.g. `10200.000000000002`). By storing exact string amounts (`"10200.00"`) and integer cents (`1020000`), we preserve absolute financial precision while retaining integer range-filtering capabilities.
4. **Bi-directional Navigation for Investigation Traversal**: Traversals must navigate top-down (`Contract -> Amendment -> SOW`) and bottom-up (`Invoice -> Governed Contract`, `Approval -> Approves Exception`, `Evidence -> Evidence For`). Dual directed relationships provide intuitive, performant paths for deterministic audit queries.
5. **Idempotent Seed Loading**: Using Cypher `MERGE` across nodes and relationships ensures that seed data ingestion can be rerun deterministically without duplicating nodes or corrupting relationship cardinality.
6. **Docker & Non-Docker Testability**: While a standard Neo4j 5 community container is added to `docker-compose.yml`, the codebase provides 100% testability via mocked driver sessions and transformation tests without requiring a running Docker daemon.

---

## ADR-009: Deterministic Validation Engine and Tri-State Authority Evaluation

**Date:** 2026-09-24

**Decision:** Implement a pure, deterministic validation engine (`app.validation`) that evaluates explicit, auditable rules against normalized graph traversal context (`InvestigationContext`) without LLMs, probabilistic reasoning, or runtime ground-truth shortcuts. Maintain strict tri-state check semantics (`PASS`, `FAIL`, `UNKNOWN`) and aggregate checks into explicit investigation determinations (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`).

**Rationale:**
1. **Code Handles Authority**: In accordance with the foundational architecture (*AI handles ambiguity. Code handles authority*), legal and contractual compliance cannot depend on probabilistic model generation. Rule evaluation must be deterministic, reproducible, and explainable in legal audits.
2. **Strict Tri-State Evaluation**: Collapsing `UNKNOWN` into `PASS` or `FAIL` destroys evidentiary nuance. A missing approval record or an absent governing contract represents incomplete evidence (`UNKNOWN` $\rightarrow$ `INSUFFICIENT_EVIDENCE`), not an explicit contract breach (`FAIL` $\rightarrow$ `NOT_VERIFIED`).
3. **Decoupled Input Contract**: By separating graph traversal (`get_invoice_lineage`) from evaluation (`ValidationEngine.validate`), the engine receives a pure data structure (`InvestigationContext` or raw lineage dict) without binding to Neo4j network calls or sessions. This makes validation tests fast and isolated.
4. **No Ground Truth as Runtime Input**: Ground truth definitions in `data/ground_truth/` exist solely for evaluation and regression benchmarking. Production validation logic derives all determinations purely from the supplied evidentiary lineage.
5. **Conflict-Aware Aggregation**: Contradictory amendments (competing rate schedules) and pending legal escalations automatically map to `NEEDS_REVIEW` rather than premature automated failure or false pass-through.

---

## ADR-010: Controlled Investigation State Machine

**Date:** 2026-09-24

**Decision:** Implement a deterministic, controlled investigation state machine (`app.investigations`) that governs the authoritative lifecycle of an ExceptionLineage investigation (`QUEUED` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `VALIDATING` $\rightarrow$ terminal outcome). Prohibit autonomous agents, LLMs, and external callers from directly mutating authoritative investigation status. Enforce explicit valid transitions, immutable audit events, explicit rejection of illegal transitions, and strict separation between business outcomes and technical failures. Use an in-memory repository for Stage 15 lifecycle testing.

**Rationale:**
1. **Code Handles Authority**: In high-stakes enterprise compliance investigations, an AI agent must never be the authority that declares an invoice "VERIFIED" or mutates investigation lifecycle states directly. AI handles ambiguity (locating evidence, interpreting natural language clauses, querying graph paths), but deterministic code handles authority (state transitions, validation rules, compliance gates).
2. **Explicit Transition Map**: State progression follows a controlled progression:
   - `QUEUED` $\rightarrow$ `INVESTIGATING`
   - `INVESTIGATING` $\rightarrow$ `VALIDATING` or `FAILED`
   - `VALIDATING` $\rightarrow$ `VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, or `FAILED`
   Any attempt to transition to an unauthorized state (e.g. `QUEUED` $\rightarrow$ `VERIFIED`, `INVESTIGATING` $\rightarrow$ `VERIFIED`, or `VALIDATING` $\rightarrow$ `INVESTIGATING`) is explicitly rejected with `InvalidStateTransitionError` identifying the investigation ID, current state, and requested state.
3. **Terminal State Inviolability**: Terminal states (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, `FAILED`) have an empty transition set. Once an investigation reaches a terminal outcome, it cannot transition further.
4. **Immutable Audit Event Timeline**: Every state transition generates exactly one immutable `InvestigationEvent` recording `from_state`, `to_state`, `reason`, `timestamp`, and relevant metadata. Event history cannot be mutated retrospectively.
5. **Strict Failure Semantics**: There is a critical architectural distinction between business evidence outcomes and infrastructure failures:
   - Absence of evidence (e.g. missing approval or unlinked contract) evaluates via the validation engine to `INSUFFICIENT_EVIDENCE` or `NOT_VERIFIED`.
   - Infrastructure or technical errors (e.g. Neo4j connectivity drop, database timeout, out-of-memory crash) transition the investigation to `FAILED`. Infrastructure failure is never confused with lack of evidence.
6. **Intentionally Minimal Persistence for Stage 15**: Introducing an external relational database (e.g., PostgreSQL + migrations + ORM) at this stage would violate the incremental design principles (ADR-006, Trap T-002). The `InMemoryInvestigationRepository` satisfies all Stage 15 lifecycle, event audit, and unit/benchmark testing requirements while establishing the repository interface boundary for future database integration.

---

## ADR-011: First End-to-End Investigation Vertical Slice

**Date:** 2026-09-24

**Decision:** Build the first real end-to-end vertical slice through the application boundary: HTTP request $\rightarrow$ FastAPI router $\rightarrow$ `InvestigationService` $\rightarrow$ `LineageRepository` (graph abstraction) $\rightarrow$ `InvestigationContext` $\rightarrow$ `ValidationEngine` $\rightarrow$ `InvestigationStateMachine` $\rightarrow$ Terminal state $\rightarrow$ Structured API response (`InvestigationResponse`). Intentionally omit LLMs, prompt chains, autonomous agent loops, and heavy UI dashboards from this slice.

**Rationale:**
1. **Vertical Pipeline Proof Before Intelligence**: Integrating an LLM into an unverified or disjointed pipeline produces unverifiable results and fragile debugging loops (Trap T-001). Proving the deterministic backbone end-to-end first—from HTTP ingress through graph traversal, validation, and state machine transition—guarantees that when agents are introduced, they operate over an authoritative, fully functional, and testable foundation.
2. **Intentional Absence of LLM**: In accordance with the foundational architectural law (*AI handles ambiguity. Code handles authority*), business authority (determining whether an invoice is verified) is completely deterministic and code-governed. AI will later assist in natural language interpretation and graph exploration, but the vertical backbone must function autonomously and deterministically without AI.
3. **Graph Abstraction and Test Double Strategy**: Requiring a live Neo4j daemon for everyday CI and unit tests creates environment friction and flakiness. Introducing `LineageRepository` as an explicit abstraction with `Neo4jLineageRepository` (production) and `InMemoryLineageRepository` (test double) enables fast, deterministic, non-Dockerized test execution across all benchmark cases without substituting fake logic into production.
4. **Strict Infrastructure Failure Semantics**: Infrastructure outages (e.g. Neo4j connection refused or query timeout) must transition the investigation from `INVESTIGATING` to `FAILED` with an explicit failure reason and exactly two audit events (`QUEUED` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `FAILED`). Infrastructure failure must never be coerced into `INSUFFICIENT_EVIDENCE` or disguised as a successful HTTP 200 response with a misleading verified outcome.
5. **API-First over Premature UI Dashboard**: Following Trap T-005 (*Building UI Before the API*), building elaborate frontend dashboards before API contracts stabilize produces massive rework. Stage 16 establishes the immutable HTTP contract (`POST /api/investigations`, `GET /api/investigations/{id}`, `GET /api/investigations/{id}/events`) with explicit Pydantic response models, preserving the lightweight status frontend for subsequent UI expansion.

---

## ADR-012: Controlled Agentic Investigation Loop

**Date:** 2026-09-24

**Decision:** Introduce a controlled, bounded investigation agent (`InvestigationAgent`) into the active `INVESTIGATING` phase. The agent dynamically decides what evidence to retrieve next via an explicit, typed tool registry (`get_invoice`, `find_contract`, `get_contract_amendments`, `get_sows`, `find_approvals`, `get_related_evidence`, `validate_investigation`) to assemble an `InvestigationContext`. Authoritative validation outcomes and lifecycle state transitions remain strictly governed by the deterministic `ValidationEngine` and `InvestigationStateMachine`.

**Rationale:**
1. **Why the Agent Exists**: In contract and invoice exception investigation, the path to discovery is non-trivial and variable: different exceptions require exploring different contractual entities (amendments vs SOWs vs managerial approvals vs specific clauses). The agent provides intelligent, goal-driven discovery—planning the next evidentiary query based on observed context—without hardcoding rigid query sequences.
2. **Constrained Tool Access**: The agent operates through explicit, typed, deterministic tools interacting with the `LineageRepository` interface. It never receives direct database, SQL, or Cypher access, arbitrary code execution privileges, or mutation authority over contracts, invoices, or graph nodes.
3. **Deterministic Validation Remains Authoritative**: In strict compliance with *"AI handles ambiguity. Code handles authority"*, the agent is explicitly prohibited from declaring invoices valid, calculating authorized financial rates, or deciding contractual compliance. When the agent concludes evidence discovery, it transitions the investigation to `VALIDATING`, where the deterministic `ValidationEngine` evaluates rule logic over the gathered `InvestigationContext`.
4. **Bounded Agent Loop**: The agent execution loop is strictly bounded by `MAX_AGENT_STEPS` (default: 10). If the agent exhausts allowable steps without requesting validation, the investigation transitions from `INVESTIGATING` to `FAILED` with `AGENT_STEP_LIMIT_EXCEEDED`. Infinite loops or unbounded tool chains are architecturally impossible.
5. **Full Action Auditability**: Every step taken by the agent emits an immutable audit event (`AGENT_DECISION`, `TOOL_CALL`) with step numbers, tool arguments, success/failure status, and rationale. An independent reviewer can reconstruct the exact lineage from:
   $$\text{INPUT} \rightarrow \text{AGENT DECISION} \rightarrow \text{TOOL CALL} \rightarrow \text{TOOL RESULT} \rightarrow \text{VALIDATION} \rightarrow \text{OUTCOME}$$
6. **Infrastructure Failure vs. Evidence Insufficiency**:
   - If a tool fails due to an infrastructure outage (e.g. database connection refused), the investigation transitions to `FAILED`.
   - If a tool successfully discovers that an approval or contract is absent in the graph, that genuine evidence absence is passed to deterministic validation, resulting in `INSUFFICIENT_EVIDENCE` or `NOT_VERIFIED`. Infrastructure failure is never conflated with evidence absence.
7. **Real vs. Simulated Boundaries**:
   - Real: FastAPI endpoints, InvestigationService, InvestigationStateMachine, ValidationEngine, LineageRepository interface, tool registry, bounded agent loop, audit event logging, and execution metrics.
   - Simulated / Test Doubles: `HeuristicAgentModel` and `ScriptedAgentModel` serve as deterministic models for offline and CI verification without requiring live external LLM API keys. Live LLM adapter endpoints plug into the same `AgentModel` interface in subsequent stages.



