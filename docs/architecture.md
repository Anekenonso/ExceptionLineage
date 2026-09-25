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

## 3. Proof of Core Architectural Claims (Stage 18.5)

### 3.1 Claim A: Agent Necessity
**Statement:** *The agentic investigation layer provides meaningful value beyond a fixed deterministic workflow.*

- **Empirical Evidence:** On the controlled branching dataset (`adaptive-v1`), the adaptive agent achieved:
  - **100.0% Accuracy** (5/5 cases) vs **80.0%** for the fixed heuristic sequence.
  - **25.0% Tool Call Reduction** (24 calls vs 32 calls).
  - **Zero Unnecessary Tool Calls** (avoiding 7 wasted queries made by the fixed sequence).
  - **3 Dynamic Early Stops** upon discovering conclusive proof or contract termination.
  - **60% Dead-End Recovery Rate** backtracking from dead-end SOW paths to valid amendment paths.
- **Architectural Conclusion:** On linear paths, a fixed sequence suffices. On non-linear enterprise exception paths, the agentic loop is necessary to prevent wasted API/database calls, avoid context contamination, and recover from false leads.

### 3.2 Claim B: Neo4j Load-Bearing Role
**Statement:** *Neo4j provides meaningful value for multi-hop relationship traversal and prevents context contamination.*

- **Empirical Evidence:** Removing graph relationship traversal and falling back to flat relational lookups (`FlatLineageRepository`) resulted in:
  - **Accuracy dropped to 87.5%** due to false amendment conflicts.
  - **37 Irrelevant Records Retrieved** across 8 benchmark cases.
  - **80% Loss in Provenance Completeness** (degraded from 100% to 20%).
  - **8.25 Retrieval Operations/Case** (vs 1.0 graph query).
- **Architectural Conclusion:** Directional graph relationships (`Contract -[:AMENDED_BY]-> Amendment`) establish hard entity boundaries. Flat relational queries pull customer-wide records that cross contract boundaries, polluting the validation context with competing rates and invalidating audit determinations.

### 3.3 Claim C: End-to-End Evidence Chain
**Statement:** *The system produces a complete, auditable end-to-end evidence trace connecting input to outcome.*

- **Empirical Evidence:** The system generates a complete, machine-readable evidence trace (`GET /api/investigations/{id}/trace`):
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
- **Integrity Guarantees:**
  - Automated secret redaction (API keys, passwords, bearer tokens).
  - Strict preservation of UTC ISO timestamps and immutable IDs.
  - Absolute preservation of the authority boundary.

---

## 4. Failure Modes & Defense-in-Depth

| Failure Mode | Threat / Risk | Architectural Defense |
| :--- | :--- | :--- |
| **Provider Quota / Outage** | External LLM throws HTTP 429/503 | Agent boundary fails closed safely (`FAILED`); zero arbitrary tools executed; report marks `UNMEASURABLE / BLOCKED_PROVIDER`. |
| **Agent Infinite Loop** | Agent cycles indefinitely | `MAX_AGENT_STEPS = 10` boundary forces termination with `AGENT_STEP_LIMIT_EXCEEDED`. |
| **Prompt Injection / Ground Truth Leak** | Agent reads test ground truth or mutates database | AST import isolation enforces zero `evaluation/` imports in `app/`; tool registry enforces typed read-only queries. |
| **Floating-Point Drift** | Dollar amounts drift during math evaluation | Exact `Decimal` and integer cents used throughout pipeline. |
| **Context Contamination** | Extraneous records pollute validation rules | Neo4j multi-hop directional traversals isolate contract sub-graphs. |
