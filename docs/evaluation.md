# Quantitative Evaluation Framework (Stage 18 — ENGINEERING COMPLETE — LIVE LLM PERFORMANCE PENDING ACTIVE PROVIDER RUN)

Comprehensive evaluation and benchmarking system for ExceptionLineage.

## 1. Architectural Philosophy

ExceptionLineage operates under a foundational architectural law:
> **"AI handles ambiguity. Code handles authority."**

The objective of the quantitative evaluation harness is to verify whether:
1. The investigation agent retrieves all necessary documentary evidence from the knowledge graph.
2. The agent navigates tool interactions safely without infinite loops or unhandled exceptions.
3. The deterministic `ValidationEngine` maintains final authority over contractual determinations.
4. The system fails gracefully and safely when evidence is missing, conflicting, or corrupted.

Ground truth expectations and benchmark datasets are strictly isolated from production code.

---

## 2. Evaluation Dataset

The evaluation suite utilizes the 8 controlled benchmark cases defined in `data/ground_truth/ground_truth.json` and `data/cases/cases.json`:

| Case ID | Target Invoice | Governing Contract | Authorizing Document | Exception / Condition | Expected Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CASE-001** | `INV-1001` | `CTR-001` | `AMD-001` (Cloud support discount) | `APR-001` (Executive approval on file) | `VERIFIED` |
| **CASE-002** | `INV-1002` | `CTR-001` | `AMD-002` (Monitoring rate revision) | `MISSING_APPROVAL` (Approval required but absent) | `INSUFFICIENT_EVIDENCE` |
| **CASE-003** | `INV-1003` | `CTR-001` | `AMD-003` (Pilot rate expired 2025-12-31) | `INVALID_EFFECTIVE_PERIOD` (Invoice issued in 2026) | `NOT_VERIFIED` |
| **CASE-004** | `INV-1004` | `CTR-001` | `AMD-004` (Cybersecurity PROD-SEC only) | `WRONG_PRODUCT_SCOPE` (Billed for general infra) | `NOT_VERIFIED` |
| **CASE-005** | `INV-1005` | `CTR-001` | `AMD-005` ($11k) vs `AMD-006` ($11.5k) | `CONFLICTING_AMENDMENTS` (Competing rate clauses) | `NEEDS_REVIEW` |
| **CASE-006** | `INV-1006` | `CTR-001` | None ($15k exceeds $12k standard) | `NO_APPLICABLE_AMENDMENT` (Unauthorized rate hike) | `NOT_VERIFIED` |
| **CASE-007** | `INV-1007` | None | None (Customer CUS-003 has no contract) | `MISSING_CONTRACT` (No baseline terms on record) | `INSUFFICIENT_EVIDENCE` |
| **CASE-008** | `INV-1008` | `CTR-002` | `AMD-007` + `SOW-002` (Milestone deliverables) | `APR-008` (Procurement approval on file) | `VERIFIED` |

### Extended Scenarios
The evaluation runner additionally supports extended controlled edge cases via `--dataset extended`:
- **CASE-009**: Incomplete Lineage (severed customer master lineage $\rightarrow$ `INSUFFICIENT_EVIDENCE`).
- **CASE-010**: Irrelevant Amendment Scope applied across distinct services ($\rightarrow$ `NOT_VERIFIED`).

---

## 3. Evaluated Baselines

The harness compares three evaluation tiers:

### Baseline A: Deterministic Validation Baseline (`deterministic_baseline`)
- **Model / System:** Direct `ValidationEngine` execution.
- **Description:** Represents the system when complete lineage and evidence context are already assembled. Evaluates pure contractual rule evaluation without agent traversal.

### Baseline B: Heuristic Agent Baseline (`heuristic_baseline`)
- **Model / System:** `InvestigationService` + `InvestigationAgent` driven by `HeuristicAgentModel`.
- **Description:** A deterministic, rational state-machine agent that systematically queries the graph via tools (`get_invoice` $\rightarrow$ `find_contract` $\rightarrow$ `get_contract_amendments` $\rightarrow$ `get_sows` $\rightarrow$ `find_approvals` $\rightarrow$ `get_related_evidence` $\rightarrow$ `validate_investigation`). Serves as the reproducible offline benchmark.

### System Under Evaluation: LLM Decision Model (`llm_decision_model`)
- **Model / System:** `InvestigationService` + `InvestigationAgent` driven by `LLMDecisionModel`.
- **Description:** Autonomous LLM-driven planning layer that selects tools based on observed state. Supports live execution against OpenAI-compatible APIs or deterministic mock execution for offline testing and CI.
- **Note:** Live LLM evaluation only executes when explicitly enabled via `--with-llm` and supplied with `AGENT_LLM_API_KEY`. When unconfigured, it is reported as `SKIPPED` to ensure reproducibility and zero external CI dependencies.

---

## 4. Quantitative Metrics and Formulas

### Outcome Accuracy
- **Formula:**
  $$\text{Accuracy} = \frac{\text{Correct Cases}}{\text{Total Cases}}$$
- A case is considered correct if and only if the authoritative status produced by the deterministic `ValidationEngine` strictly matches the ground truth `expected_status`.

### Evidence Retrieval
- **Per-Case Evidence Recall:**
  $$\text{Evidence Recall} = \begin{cases} 1.0 & \text{if } |\text{Required Evidence}| = 0 \\ \frac{|\text{Retrieved Evidence} \cap \text{Required Evidence}|}{|\text{Required Evidence}|} & \text{if } |\text{Required Evidence}| > 0 \end{cases}$$
  *Rationale:* When a case has no governing contract or required evidence (e.g. CASE-007), 0 required items were missed, yielding a recall of 1.0.
- **Mean Evidence Recall:** Arithmetic mean of per-case recall scores across the suite.
- **Overall Evidence Recall:** Total retrieved required evidence divided by total required evidence across all cases.

### Tool Usage & Operational Efficiency
- **Tracked Metrics:**
  - `total_agent_steps`: Sum of agent planning loop iterations.
  - `total_tool_calls`: Sum of tool execution attempts.
  - `successful_tool_calls`: Tool executions returning `success=True`.
  - `failed_tool_calls`: Tool executions returning `success=False` or schema errors.
  - `duplicate_tool_calls`: Repeated invocations with identical tool name and arguments.
  - `validation_calls`: Number of explicit transfers of authority to `validate_investigation`.
- **Formula Transparency:** No composite "black-box" efficiency score is fabricated. Tool counts, step ratios, and duplicate frequencies are reported directly.

### Termination Breakdown
Tracks the exact frequency of each final outcome state:
- `VERIFIED`: Validated authorized variances.
- `NOT_VERIFIED`: Deterministically rejected variances.
- `INSUFFICIENT_EVIDENCE`: Genuinely missing contracts, approvals, or evidence.
- `NEEDS_REVIEW`: Unresolved conflicting authority requiring legal review.
- `FAILED`: Infrastructure or technical failures.
- `STEP_LIMIT_EXCEEDED`: Agent loop exhausted `MAX_AGENT_STEPS` without concluding.

### Failure Metrics
Measures robust error isolation:
- `malformed_actions`: Unparseable model outputs.
- `unknown_tools`: Requests for nonexistent tools.
- `invalid_arguments`: Tool argument schema violations.
- `tool_errors`: Runtime exceptions or errors returned by tools.
- `llm_errors`: Network, HTTP 401/429/500 provider errors.
- `timeouts`: Network or read timeouts.
- `retries`: Model retries triggered by schema validation.

### Operational Metrics
- `duration_ms`: Wall-clock execution time per case in milliseconds.
- `llm_calls`: Total chat completion API calls.
- `prompt_tokens`, `completion_tokens`, `total_tokens`: Actual tokens consumed as reported by the provider (reported as `null` when unavailable; never fabricated).

### Evaluation Status Semantics
The evaluation framework distinguishes external execution and infrastructure realities from model reasoning results using an explicit status taxonomy:
- `COMPLETED`: All cases attempted and reached model completion / deterministic termination. Metrics are fully measurable.
- `BLOCKED_PROVIDER`: Evaluation halted or all cases failed due to external provider constraints (HTTP 429 quota exhaustion, rate limits, HTTP 401 authentication errors, network connection drops). Model performance metrics (`accuracy`, `evidence_recall`) are classified as **UNMEASURABLE** (reported as `null`).
- `PARTIAL`: Some cases completed successfully while others encountered provider, infrastructure, or timeout errors. Metrics are computed strictly across completed cases with failure counters transparently reported.
- `FAILED_SYSTEM`: Internal software crashes, unhandled harness exceptions, or environment configuration failures occurred.
- `SKIPPED`: The baseline was intentionally omitted (e.g. `--with-llm` flag not provided).

---

## 5. Reproducibility & Ground-Truth Isolation

### Ground-Truth Isolation Law
Production packages (`app/agent/`, `app/graph/`, `app/investigations/`, `app/api/`, `app/validation/`, `app/models/`) are verified by automated AST tests (`tests/test_ground_truth_isolation.py`) to ensure:
1. Zero imports of ground truth datasets, test modules, or evaluation runners.
2. Zero hardcoded case expectations or `CASE-` identifiers.

### Reproducibility
- **Deterministic Baselines:** Baseline A and Baseline B are 100% deterministic and achieve identical results across any platform without external API dependencies.
- **Live LLM Evaluations:** Explicitly documented as subject to model stochasticity and external API provider changes.
- **Mock Mode:** `--mock-llm` provides a deterministic mock client allowing offline CI verification of the full LLM evaluation harness.

---

## 6. How to Run the Evaluation Harness

### Run Default Evaluation (Deterministic & Heuristic Baselines)
```bash
python evaluation/runner.py
```
Outputs:
- Machine-readable JSON: `evaluation/reports/latest.json`
- Human-readable Markdown: `evaluation/reports/latest.md`

### Run with Deterministic Mock LLM
```bash
python evaluation/runner.py --mock-llm
```

### Run with Live LLM
```bash
export AGENT_LLM_API_KEY="your-api-key"
export AGENT_LLM_MODEL="gpt-4o-mini"
python evaluation/runner.py --with-llm
```

### Run a Specific Baseline
```bash
python evaluation/runner.py --baseline deterministic
python evaluation/runner.py --baseline heuristic
```

### Run Extended Edge-Case Dataset
```bash
python evaluation/runner.py --dataset extended
```

---

## 7. Actual Benchmark Results (Latest Run)

Results from execution of `evaluation/runner.py`:

| Baseline / System | Provider | Model | Status | Accuracy | Mean Recall | Mean Steps | Tool Calls | Duration (mean) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A** (ValidationEngine) | deterministic | ValidationEngine | `COMPLETED` | **100.0%** (8/8) | 100.0% | 0.0 | 0 (8 val) | 0.30 ms |
| **Baseline B** (HeuristicAgent) | heuristic | HeuristicAgentModel | `COMPLETED` | **100.0%** (8/8) | 100.0% | 6.38 | 51 (8 val) | 0.57 ms |
| **LLM Decision Model (Mock)** | mock | mock-llm-planner | `COMPLETED` | **62.5%** (5/8) | 54.2% | 6.38 | 51 (8 val) | 8.90 ms |
| **LLM Decision Model (Live gpt-4o-mini)** | openai | gpt-4o-mini | `BLOCKED_PROVIDER` | **UNMEASURABLE** | **UNMEASURABLE** | 0.0 | 0 (0 val) | 1432 ms |

### Live LLM Evaluation Findings (Suite `suite-b16fb5f27789`):
- **Provider Status:** 8/8 cases attempted; 0/8 reached model completion due to OpenAI HTTP 429 (`insufficient_quota` / `credit_balance_exhausted`).
- **Measurability:** Live LLM reasoning performance was **UNMEASURABLE**. Model accuracy, evidence recall, and token counts are recorded as `null` rather than 0% to prevent misrepresenting external provider quota exhaustion as reasoning failure.
- **Fail-Closed Verification:** 100% of cases terminated safely with state `FAILED` and zero tool executions, zero hallucinations, and zero fabricated business determinations.
- **Pending Live Run:** A live run with active provider credits is required before making claims regarding LLM reasoning accuracy, tool selection, or token efficiency.

---

## 8. Architectural Proof (Stage 18.5 & Stage 21)

> **Scope of evidence:** These results are controlled experiments on synthetic investigation data. They demonstrate properties of this implementation and evaluation setup; they are not universal benchmarks of all agents, databases, or enterprise systems.

### 8.1 Claim A: Adaptive Investigation Value Experiment — DEMONSTRATED

**Core Finding:** In controlled branching scenarios, adaptive, state-dependent investigation improved investigation efficiency and recovery compared with the fixed heuristic baseline.

**Dataset (`adaptive-v1`):** 5 controlled branching scenarios (`BRANCH-001` through `BRANCH-005`):
- `BRANCH-001`: Matching base contract terms allow immediate early termination without querying amendments or SOWs.
- `BRANCH-002`: Missing governing contract halts discovery immediately, avoiding redundant approval or evidence queries.
- `BRANCH-003`: Executed amendment and approved variance satisfy exception; agent skips irrelevant SOW queries.
- `BRANCH-004`: Explicit executive rejection on file invalidates exception; agent halts before redundant amendment/SOW lookups.
- `BRANCH-005`: Conflicting concurrent amendments detected; agent escalates directly to validation for review without querying SOWs.

**Results Table:**
| Metric | Heuristic Baseline (Fixed Sequence) | Adaptive Agent | Operational Advantage |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 80.0% (4/5) | **100.0%** (5/5) | +20.0% on branching workflows |
| **Total Tool Calls** | 32 | **24** | **8 fewer calls** (25.0% reduction) |
| **Unnecessary Tool Calls** | 7 | **0** | **Zero wasted queries** |
| **Dynamic Early Stops** | 0 | **3** | Stops immediately when conclusive proof found |
| **Branching Path Recovery Rate** | 0.0% | **60.0%** | Reaches expected outcome in $\le$ 5 steps without wasted calls (3/5 cases) |

*Recovery Definition:* In the evaluation harness, "recovery" measures whether the agent successfully navigated a branching path to the correct validation outcome within 5 steps while avoiding all unnecessary tool calls (achieved in 3 of 5 cases, or 60.0%, with the remaining 2 cases completing correctly in 6 steps).

*Scope Note:* The experiment demonstrates behavior on the tested scenarios and does not establish a universal requirement for agentic AI or LLMs. Live LLM evaluation was blocked by external provider quota/availability; this experiment evaluates adaptive state-dependent tool selection logic.

### 8.2 Claim B: Relationship-Aware Retrieval Experiment — DEMONSTRATED

**Core Finding:** The controlled retrieval experiment showed measurable benefits from explicit relationship-aware traversal for this workload, including accuracy, relevance, and provenance differences.

**Harness (`FlatRetrievalAdapter` vs `DeterministicValidationAdapter` on `benchmark-v1`):**
A flat relational repository was created that stores the exact same nodes as tables and resolves queries using foreign key lookups without graph edge constraints.

**Results Table:**
| Metric | Knowledge Graph Traversal | Flat Relational Mock | Impact of Graph Removal |
| :--- | :--- | :--- | :--- |
| **Validation Accuracy** | **100.0%** (8/8) | 87.5% (7/8) | False amendment conflicts cause incorrect rejections |
| **Irrelevant Records Retrieved** | **0** | **37** | Extreme context pollution across customer records |
| **Multi-Hop Provenance** | **100.0%** | **20.0%** | -80% loss in end-to-end evidence lineage |
| **Mean Retrieval Operations / Case** | **1.0** | **8.25** | 8x multiplication in discrete scan queries |

**Architectural Takeaway:** Directional graph relationships (`Contract -[:AMENDED_BY]-> Amendment`) establish clear contractual boundaries. In flat lookups, querying amendments by customer ID retrieves amendments from unrelated contracts, triggering false rate conflicts in validation.

> **Limitation:** *This controlled experiment demonstrates the value of explicit relationship-aware retrieval for the tested workload. It does not establish that Neo4j is universally superior to a well-designed relational implementation.*

### 8.3 Claim C: End-to-End Evidence Chain Verification — VERIFIED

**Core Finding:** The demonstrated investigation trace reconstructs the path from investigation input through agent decisions, tool execution, evidence retrieval, deterministic validation, and final outcome while preserving the authority boundary and redacting secrets.

**Verification Results:**
- **Endpoint:** `GET /api/investigations/{id}/trace` $\rightarrow$ `InvestigationEvidenceTrace`
- **Chain Integrity:** `VERIFIED` (unbroken 30-event chronological chain)
- **Chain Flow:**
  $$\text{INPUT} \rightarrow \text{AGENT\_DECISION} \rightarrow \text{TOOL\_CALL} \rightarrow \text{GRAPH\_RETRIEVAL} \rightarrow \text{VALIDATION} \rightarrow \text{OUTCOME}$$
- **Secret Redaction:** Fully verified; API keys, tokens, and credentials sanitized to `[REDACTED]`.
- **Validation Semantics:** Discrete rule check events preserve strict tri-state statuses (`PASS`, `FAIL`, `UNKNOWN`).
- **Authority Preservation:** Agent decisions remain strictly evidentiary; business outcomes are emitted solely by the deterministic validation engine.

### 8.4 Reproduction Commands
```powershell
# Run the architectural proof harness
.\apps\api\venv\Scripts\python.exe evaluation/runner.py --stage-18-5

# Run the automated test suite for Claims A, B, and C
.\apps\api\venv\Scripts\python.exe -m pytest apps/api/tests/test_agent_necessity_experiment.py apps/api/tests/test_neo4j_removal_experiment.py apps/api/tests/test_evidence_chain_trace.py -v
```



