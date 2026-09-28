# ExceptionLineage System Architecture

## 1. System Overview & Core Philosophy

ExceptionLineage is an enterprise investigation engine designed to resolve financial and contractual invoice exceptions by traversing multi-hop relationship lineages across contracts, amendments, Statements of Work (SOWs), and managerial approvals.

The architecture is governed by an inviolable foundational law:

> **"AI handles ambiguity. Code handles authority."**

- **AI's Role:** Goal-driven evidentiary exploration, natural language clause interpretation, dynamic query planning, and adapting to non-linear discovery paths.
- **Code's Role:** State machine lifecycle governance, strict deterministic rule evaluation, financial amount calculations, and binding business determinations (`VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`).

---

## 2. Layered Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │       Client Applications / HTTP Ingress      │
                    │         (POST /api/investigations)            │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │             InvestigationService              │
                    │   Orchestrates lifecycle & state machine      │
                    └───────┬───────────────────────────────┬───────┘
                            │                               │
       (Active: INVESTIGATING)                     (Active: VALIDATING)
                            ▼                               ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │      InvestigationAgent       │   │       ValidationEngine        │
       │   Bounded Tool Execution Loop │   │   Pure Deterministic Rules    │
       │   (Max steps: 10)             │   │   Tri-state: PASS/FAIL/UNKNOWN│
       └───────────────┬───────────────┘   └───────────────┬───────────────┘
                       │                                   │
                       ▼                                   ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │         ToolRegistry          │   │   InvestigationStateMachine   │
       │  Typed, schema-validated tools│   │  Enforces valid transitions   │
       └───────────────┬───────────────┘   └───────────────┬───────────────┘
                       │                                   │
                       ▼                                   ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │       LineageRepository       │   │    Immutable Event Audit Log  │
       │  (Neo4j / InMemoryLineage)    │   │  Trace & Timeline Persistence │
       └───────────────────────────────┘   └───────────────────────────────┘
```

### 2.1 HTTP Ingress & API Layer (`app/investigations/router.py`)
- Provides clean, versioned endpoints (`/api/investigations`, `/api/investigations/{id}`, `/api/investigations/{id}/events`, `/api/investigations/{id}/trace`).
- Decoupled from internal database representations via Pydantic response schemas (`InvestigationResponse`, `InvestigationEvidenceTrace`).

### 2.2 Lifecycle State Machine (`app/investigations/state_machine.py`)
- Enforces valid lifecycle transitions:
  - `QUEUED` $\rightarrow$ `INVESTIGATING`
  - `INVESTIGATING` $\rightarrow$ `VALIDATING` or `FAILED`
  - `VALIDATING` $\rightarrow$ `VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, or `FAILED`
- Terminal states are strictly immutable.
- Direct mutations by external callers or agents are rejected with `InvalidStateTransitionError`.

### 2.3 Controlled Agent Layer (`app/agent/`)
- **`InvestigationAgent`**: Executes a bounded reasoning loop (`MAX_AGENT_STEPS = 10`).
- **`ToolRegistry`**: Exposes typed evidentiary tools (`get_invoice`, `find_contract`, `get_contract_amendments`, `get_sows`, `find_approvals`, `get_related_evidence`, `validate_investigation`).
- **`AgentModel`**: Abstract strategy interface with polymorphic implementations:
  - `HeuristicAgentModel`: Deterministic, zero-credential baseline.
  - `LLMDecisionModel`: OpenAI-compatible structured JSON action model.
  - `AdaptiveAgentModel`: Adaptive evaluation model demonstrating dynamic early stopping and recovery.

### 2.4 Knowledge Graph Layer (`app/graph/`)
- Driven by Neo4j (`Neo4jLineageRepository`) with an in-memory test double (`InMemoryLineageRepository`).
- Node labels: `Customer`, `Contract`, `Amendment`, `SOW`, `Exception`, `Approval`, `Invoice`, `Evidence`.
- Explicit directed relationship semantics: `GOVERNED_BY`, `AMENDS`, `UNDER_CONTRACT`, `HAS_EXCEPTION`, `APPROVES`, `HAS_EVIDENCE`.
- Monetary values are stored as string literals (`"10200.00"`) and integer cents (`1020000`) to completely eliminate floating-point precision loss.

### 2.5 Deterministic Validation Engine (`app/validation/`)
- Evaluates discrete rules against the assembled `InvestigationContext`:
  1. `CustomerMatchCheck`: Validates invoice customer against contract.
  2. `ContractActiveCheck`: Validates contract active status and legal effective dates.
  3. `AmendmentConflictCheck`: Detects contradictory amendment clauses or competing rates.
  4. `AmendmentEffectiveCheck`: Validates amendment legal effective date.
  5. `ProductScopeCheck`: Validates billed product match.
  6. `ApprovalGrantedCheck`: Validates required executive approvals.
  7. `RateMatchCheck`: Verifies billed amounts match governing rates.
- Strict tri-state evaluation (`PASS`, `FAIL`, `UNKNOWN`).

---

## 3. Architectural Proof (Stage 18.5 & Stage 21)

### 3.1 Claim A: Adaptive Investigation Value — DEMONSTRATED
**Statement:** *In controlled branching scenarios, adaptive, state-dependent investigation improved investigation efficiency and recovery compared with the fixed heuristic baseline.*

- **Empirical Evidence:** On the controlled branching dataset (`adaptive-v1`), the adaptive agent achieved:
  - **100.0% Accuracy** (5/5 cases) vs **80.0%** for the fixed heuristic sequence.
  - **25.0% Tool Call Reduction** (24 calls vs 32 calls).
  - **Zero Unnecessary Tool Calls** (avoiding 7 wasted queries made by the fixed sequence).
  - **3 Dynamic Early Stops** upon discovering conclusive base rate matches, missing contracts, or explicit rejections.
  - **60.0% Branching Path Recovery Rate** successfully navigating branching paths in $\le$ 5 steps without redundant queries (3 of 5 cases).
- **Scope of Evidence:** These results demonstrate behavior on the tested scenarios and do not establish a universal requirement for agentic AI or LLMs. Live LLM evaluation was blocked by external provider quota/availability; the adaptive evaluation measures state-dependent tool selection logic.

### 3.2 Claim B: Relationship-Aware Retrieval — DEMONSTRATED
**Statement:** *The controlled retrieval experiment showed measurable benefits from explicit relationship-aware traversal for this workload, including accuracy, relevance, and provenance differences.*

- **Empirical Evidence:** Removing explicit graph relationship traversal and falling back to flat relational lookups (`FlatLineageRepository`) resulted in:
  - **Validation Accuracy:** 100.0% graph-aware vs **87.5%** flat retrieval (unlinked amendments triggered false rate conflicts).
  - **Irrelevant Records Retrieved:** 0 with graph traversal vs **37** across 8 benchmark cases under flat lookups.
  - **Provenance Completeness:** 100.0% multi-hop lineage vs **20.0%** (-80% loss in end-to-end evidence lineage).
  - **Retrieval Operations / Case:** 1.0 graph query vs **8.25 operations/case** under flat table scans.
- **Architectural Conclusion:** Explicit relationship-aware traversal isolates the exact contract sub-graph, preventing customer-wide records from crossing contract boundaries and contaminating the validation context.
- **Limitation:** *This controlled experiment demonstrates the value of explicit relationship-aware retrieval for the tested workload. It does not establish that Neo4j is universally superior to a well-designed relational implementation.*

### 3.3 Claim C: End-to-End Evidence Chain — VERIFIED
**Statement:** *The demonstrated investigation trace reconstructs the path from investigation input through agent decisions, tool execution, evidence retrieval, deterministic validation, and final outcome while preserving the authority boundary and redacting secrets.*

- **Empirical Evidence:** The system generates a complete, auditable, machine-readable evidence trace (`GET /api/investigations/{id}/trace`):
  ```
  INPUT
    ↓
  AGENT_DECISION   (probabilistic tool planning & rationale)
    ↓
  TOOL_CALL        (controlled tool invocation)
    ↓
  GRAPH_RETRIEVAL  (knowledge graph Cypher traversal & citations)
    ↓
  VALIDATION       (deterministic rule check: PASS | FAIL | UNKNOWN)
    ↓
  OUTCOME          (authoritative final determination & state transition)
  ```
- **Quantitative Trace Attributes:**
  - 30 total chronological events
  - 7 agent decisions, 7 tool calls, 6 graph retrievals, 8 validation checks, 3 cited evidence items
  - `secrets_redacted = true` (automated recursive sanitization of API keys, passwords, and tokens)
  - `authority_boundary_preserved = true` (*"AI investigates. Deterministic logic verifies."*)

> **Scope of evidence:** These results are controlled experiments on synthetic investigation data. They demonstrate properties of this implementation and evaluation setup; they are not universal benchmarks of all agents, databases, or enterprise systems.

---

## 4. Failure Modes & Defense-in-Depth

| Failure Mode | Threat / Risk | Architectural Defense |
| :--- | :--- | :--- |
| **Provider Quota / Outage** | External LLM throws HTTP 429/503 | Agent boundary fails closed safely (`FAILED`); zero arbitrary tools executed; report marks `UNMEASURABLE / BLOCKED_PROVIDER`. |
| **Agent Infinite Loop** | Agent cycles indefinitely | `MAX_AGENT_STEPS = 10` boundary forces termination with `AGENT_STEP_LIMIT_EXCEEDED`. |
| **Prompt Injection / Ground Truth Leak** | Agent reads test ground truth or mutates database | AST import isolation enforces zero `evaluation/` imports in `app/`; tool registry enforces typed read-only queries. |
| **Floating-Point Drift** | Dollar amounts drift during math evaluation | Exact `Decimal` and integer cents used throughout pipeline. |
| **Context Contamination** | Extraneous records pollute validation rules | Neo4j multi-hop directional traversals isolate contract sub-graphs. |

---

## 5. Secure Temporary Case Testing Architecture ("Test Your Own Case")

### 5.1 Architectural Principle: "Two Input Paths. One Investigation Engine."

The system provides a secure, sandboxed testing ingress that allows evaluators to upload an independent JSON case file and run it through the full investigation pipeline without altering any persistent storage or canonical benchmark datasets.

```
+-----------------------------------------------------------------------------------+
|                                 INGRESS LAYER                                     |
|                                                                                   |
|    Path A (Canonical Ingress)                      Path B (Ephemeral Sandbox)     |
|    POST /api/investigations                        POST /api/investigations/test-case
|    [invoice_id: "INV-1001"]                        [multipart/form-data: .json]   |
+------------------------+------------------------------------------+---------------+
                         |                                          |
                         v                                          v
+------------------------+------------------------------------------+---------------+
|    Neo4j / Persistent Lineage                     InMemoryLineageRepository       |
|    Persistent Graph Storage                       Request-Scoped Ephemeral Double |
+------------------------+------------------------------------------+---------------+
                         |                                          |
                         +--------------------+---------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------+
|                        SINGLE SHARED INVESTIGATION ENGINE                         |
|                                                                                   |
|    InvestigationService                                                           |
|      ├── InvestigationAgent (Tool loop: get_invoice, find_contract, etc.)         |
|      └── ValidationEngine   (Deterministic evaluation: PASS | FAIL | UNKNOWN)     |
|                                                                                   |
|    Output: InvestigationResponse (deterministic status, citations, audit trace)   |
+-----------------------------------------------------------------------------------+
```

### 5.2 Ephemeral Execution Pipeline

1. **Ingress & Format Enforcement:**
   - The file is received via `UploadFile` strictly checking for `.json` extension and `application/json` or `text/json` MIME type.
   - Bounded chunked streaming verification reads in 64 KB chunks up to `MAX_TEST_CASE_SIZE_BYTES = 1,048,576` (1 MB), aborting immediately with HTTP 413 if the threshold is exceeded.
2. **Schema & Semantic Parsing:**
   - The file payload is parsed through `TestCasePayload` Pydantic models with `strict=False` parsing for strings/numbers.
   - Validates existence of the mandatory `invoice` object.
   - Lineage anchors (`customer`, `contract`, `exception`) and supporting records (`amendments`, `sows`, `evidence`, `approval`) are intentionally optional: this enables evaluators to test missing contracts, unanchored invoices, or missing approvals to observe deterministic `UNKNOWN` $\rightarrow$ `INSUFFICIENT_EVIDENCE` determinations.
3. **Sandbox Population:**
   - A fresh, request-scoped `InMemoryLineageRepository` instance is allocated.
   - The normalized nodes and their explicit relationship pointers are populated in memory.
4. **Engine Traversal & Audit Trace:**
   - A dedicated `InvestigationService` is constructed with the ephemeral repository and executed.
   - Deterministic rule checks (`ValidationEngine`) evaluate legal applicability, scope, rates, and authority.
   - Complete audit events and an end-to-end `InvestigationEvidenceTrace` are generated.
5. **Zero-Persistence Completion & Dereferencing:**
   - The response is returned to the client marked with `is_temporary=True`.
   - The ephemeral repository instance is immediately released to Python garbage collection.
   - No records are written to Neo4j, SQLite, PostgreSQL, Redis, disk, uploads folder, or client browser storage (`localStorage`, `sessionStorage`, `cookies`, `IndexedDB`).

