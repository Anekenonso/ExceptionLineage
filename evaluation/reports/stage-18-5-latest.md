# Stage 18.5 Architectural Proof Report

## Agent Necessity + Neo4j Necessity + End-to-End Evidence Chain

- **Suite ID:** `proof-18-5-4230494cae25`
- **Timestamp:** `2026-09-26T01:58:30.322458+00:00`
- **Git Commit:** `cc8528e5e425e5be6be2fb569b7277d183ad2720`
- **Dataset:** `adaptive-v1` (Branching) + `benchmark-v1` (Canonical)
- **Architectural Boundary:** *"AI handles ambiguity. Code handles authority."*

---

## Claims Summary Table

| Claim | Focus | Status | Primary Quantitative Evidence |
| :--- | :--- | :--- | :--- |
| **Claim A** | Agent Necessity | **PROVEN** | Adaptive Agent achieved **100.0% accuracy** (vs Heuristic 80.0%), eliminated **7 unnecessary tool calls**, and performed **3 dynamic early stops**. |
| **Claim B** | Neo4j Necessity | **PROVEN** | Flat retrieval dropped accuracy to **87.5%** (vs Graph 100.0%), returned **37 irrelevant records**, and degraded provenance to **20%**. |
| **Claim C** | Evidence Chain Trace | **PROVEN** | Complete, unbroken **30-event audit trace** verified from input to outcome with secret redaction and tri-state check semantics. |

---

## Claim A: Agent Necessity Experiment

> **Hypothesis:** An adaptive agent loop dynamically stops, backtracks, and selects tools based on intermediate evidence, whereas a fixed deterministic sequence wastes operations and fails on non-linear lineage branches.

### Quantitative Comparison (Branching Dataset: 5 Cases)

| Metric | Heuristic (Fixed Sequence) | Adaptive Agent | Operational Advantage |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 80.0% | **100.0%** | +20.0% on branching scenarios |
| **Total Tool Calls** | 32 | **24** | **8 fewer calls** (25.0% reduction) |
| **Unnecessary Tool Calls** | 7 | **0** | **Zero wasted queries** |
| **Dynamic Early Stops** | 0 | **3** | Stops immediately when conclusive proof found |
| **Dead-End Recovery Rate** | 0.0% | **60%** | Recovers from dead-end SOW branches |

### Architectural Rationale
- **Linear workflows** (`benchmark-v1`): A fixed heuristic achieves parity because every invoice strictly follows Invoice -> Contract -> Amendment -> SOW -> Approval.
- **Branching workflows** (`adaptive-v1`): Fixed sequences execute unnecessary queries (e.g. querying amendments for a contract that was already terminated or querying SOWs when base rate matches). The adaptive agent terminates early or pivots paths dynamically.

---

## Claim B: Neo4j Removal Experiment

> **Hypothesis:** Removing Neo4j graph relationships and falling back to flat table/relational lookups leads to context contamination, false conflicts from unlinked amendments, and degraded evidence provenance.

### Quantitative Comparison (Benchmark Dataset: 8 Cases)

| Metric | Knowledge Graph (Neo4j) | Flat Relational Mock | Impact of Graph Removal |
| :--- | :--- | :--- | :--- |
| **Validation Accuracy** | **100.0%** | 87.5% | Accuracy drops due to false amendment conflicts |
| **Irrelevant Records Retrieved** | **0** | 37 | High context contamination (37 extraneous items) |
| **Multi-Hop Provenance** | **100%** | 20% | -80% loss in end-to-end evidence lineage |
| **Retrieval Operations / Case** | **1.0** | 8.25 | 8x multiplication in discrete scan operations |

### Architectural Rationale
- In a flat lookup, querying amendments for customer `CUS-001` returns amendments belonging to *other contracts* of the same customer. Without directional relationship edges (`(Contract)-[:AMENDED_BY]->(Amendment)`), the validation engine encounters conflicting rates.
- Graph traversal isolates the exact contract sub-graph, guaranteeing zero context pollution.

---

## Claim C: End-to-End Evidence Chain Verification

> **Hypothesis:** ExceptionLineage produces a verifiable, auditable machine-readable evidence trace connecting user input to authoritative validation outcome.

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

To re-run the complete Stage 18.5 proof harness and regenerate this report:
```powershell
.\apps\api\venv\Scripts\python.exe evaluation/runner.py --stage-18-5
```

To run the automated test suite for Claims A, B, and C:
```powershell
.\apps\api\venv\Scripts\python.exe -m pytest apps/api/tests/test_agent_necessity_experiment.py apps/api/tests/test_neo4j_removal_experiment.py apps/api/tests/test_evidence_chain_trace.py -v
```
