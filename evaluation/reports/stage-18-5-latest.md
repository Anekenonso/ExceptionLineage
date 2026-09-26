# Architectural Evaluation Report (Stage 18.5 / Stage 21)

## Adaptive Investigation Value + Relationship-Aware Retrieval + End-to-End Evidence Chain

- **Suite ID:** `proof-18-5-b78065028f3b`
- **Timestamp:** `2026-09-26T15:39:43.643513+00:00`
- **Git Commit:** `1c19b1402e2368164d2b6cbe455c4bac0d219e62`
- **Dataset:** `adaptive-v1` (Branching) + `benchmark-v1` (Canonical)
- **Architectural Invariant:** *"AI handles ambiguity. Code handles authority."*

> **Scope of evidence:** These results are controlled experiments on synthetic investigation data. They demonstrate properties of this implementation and evaluation setup; they are not universal benchmarks of all agents, databases, or enterprise systems.

---

## Claims Summary Table

| Claim | Focus | Status | Primary Quantitative Evidence |
| :--- | :--- | :--- | :--- |
| **Claim A** | Adaptive Investigation Value | **DEMONSTRATED** | Adaptive Agent achieved **100.0% accuracy** (vs Heuristic 80.0%), eliminated **7 unnecessary tool calls**, and performed **3 dynamic early stops**. |
| **Claim B** | Relationship-Aware Retrieval | **DEMONSTRATED** | Flat retrieval dropped accuracy to **87.5%** (vs Graph 100.0%), returned **37 irrelevant records**, and degraded provenance to **20%**. |
| **Claim C** | End-to-End Evidence Chain | **VERIFIED** | Complete, unbroken **30-event audit trace** verified from input to outcome with secret redaction and tri-state check semantics. |

---

## Claim A: Adaptive Investigation Value Experiment

> In controlled branching scenarios, adaptive, state-dependent investigation improved investigation efficiency and recovery compared with the fixed heuristic baseline.

### Quantitative Comparison (Branching Dataset: 5 Cases)

| Metric | Heuristic (Fixed Sequence) | Adaptive Agent | Operational Advantage |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 80.0% | **100.0%** | +20.0% on branching scenarios |
| **Total Tool Calls** | 32 | **24** | **8 fewer calls** (25.0% reduction) |
| **Unnecessary Tool Calls** | 7 | **0** | **Zero wasted queries** |
| **Dynamic Early Stops** | 0 | **3** | Stops immediately when conclusive proof found |
| **Branching Path Recovery Rate** | 0.0% | **60%** | Successfully navigated branching paths in <= 5 steps (3/5 cases) |

> **Scope Note:** In controlled branching scenarios, adaptive, state-dependent investigation improved investigation efficiency and recovery compared with the fixed heuristic baseline. These results demonstrate behavior on the tested scenarios and do not establish a universal requirement for agentic AI or LLMs. (Live LLM evaluation was blocked by provider quota/availability).

### Architectural Rationale
- **Linear workflows** (`benchmark-v1`): A fixed heuristic achieves parity because every invoice strictly follows Invoice -> Contract -> Amendment -> SOW -> Approval.
- **Branching workflows** (`adaptive-v1`): Fixed sequences execute unnecessary queries (e.g. querying amendments for an unanchored transaction or querying SOWs when base rate matches). The adaptive agent terminates early or pivots paths dynamically.

---

## Claim B: Relationship-Aware Retrieval Experiment

> The controlled retrieval experiment showed measurable benefits from explicit relationship-aware traversal for this workload, including accuracy, relevance, and provenance differences.

### Quantitative Comparison (Benchmark Dataset: 8 Cases)

| Metric | Knowledge Graph Traversal | Flat Relational Mock | Impact of Graph Removal |
| :--- | :--- | :--- | :--- |
| **Validation Accuracy** | **100.0%** | 87.5% | Accuracy drops due to false amendment conflicts |
| **Irrelevant Records Retrieved** | **0** | 37 | High context contamination (37 extraneous items) |
| **Multi-Hop Provenance** | **100%** | 20% | -80% loss in end-to-end evidence lineage |
| **Retrieval Operations / Case** | **1.0** | 8.25 | 8x multiplication in discrete scan operations |

> **Limitation:** This controlled experiment demonstrates the value of explicit relationship-aware retrieval for the tested workload. It does not establish that Neo4j is universally superior to a well-designed relational implementation.

### Architectural Rationale
- In a flat lookup, querying amendments for customer `CUS-001` returns amendments belonging to *other contracts* of the same customer. Without directional relationship edges (`(Contract)-[:AMENDED_BY]->(Amendment)`), the validation engine encounters conflicting rates.
- Explicit relationship-aware traversal isolates the exact contract sub-graph, preventing cross-contract context contamination.

---

## Claim C: End-to-End Evidence Chain Verification

> The demonstrated investigation trace reconstructs the path from investigation input through agent decisions, tool execution, evidence retrieval, deterministic validation, and final outcome while preserving the authority boundary and redacting secrets.

- **Chain Integrity:** `VERIFIED`
- **Total Auditable Events:** 30
- **Secret Redaction:** `CONFIRMED` (All tokens, passwords, and API keys redacted)
- **Authority Boundary:** `PRESERVED` (*AI handles ambiguity. Code handles authority.*)
- **Event Types Present:** `input, agent_decision, tool_call, graph_retrieval, validation, outcome`

### Chronological Chain Schema
```
INPUT
  ↓
AGENT_DECISION  (probabilistic tool planning & rationale)
  ↓
TOOL_CALL       (controlled tool invocation)
  ↓
GRAPH_RETRIEVAL (knowledge graph Cypher traversal & citations)
  ↓
VALIDATION      (deterministic rule check: PASS | FAIL | UNKNOWN)
  ↓
OUTCOME         (authoritative final determination & state transition)
```

---

## Reproduction Instructions

To re-run the architectural proof harness and regenerate this report:
```powershell
.\apps\api\venv\Scripts\python.exe evaluation/runner.py --stage-18-5
```

To run the automated test suite for Claims A, B, and C:
```powershell
.\apps\api\venv\Scripts\python.exe -m pytest apps/api/tests/test_agent_necessity_experiment.py apps/api/tests/test_neo4j_removal_experiment.py apps/api/tests/test_evidence_chain_trace.py -v
```
