# ExceptionLineage Quantitative Evaluation Report

- **Suite ID:** `suite-dae3a8575b3a`
- **Timestamp:** `2026-09-24T18:26:14.519805+00:00`
- **Git Commit:** `61e976bc0ca176fc8899b1f98d4138e567d11bac`
- **Dataset Version:** `benchmark-v1`

---

## 1. Executive Summary & Baseline Comparison

| Baseline / System | Model Provider | Model Name | Status | Accuracy | Mean Evidence Recall | Mean Steps | Total Tool Calls | Tool Errors | Mean Duration (ms) | Total Tokens |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **deterministic_baseline** | deterministic | ValidationEngine | `COMPLETED` | 100.0% (8/8) | 100.0% | 0.0 | 0 | 0 | 0.37 ms | N/A |
| **heuristic_baseline** | heuristic | HeuristicAgentModel | `COMPLETED` | 100.0% (8/8) | 100.0% | 6.38 | 51 | 0 | 0.46 ms | N/A |
| **llm_decision_model** | unconfigured | none | `SKIPPED` | N/A | 0.0% | 0.0 | 0 | 0 | 0.0 ms | N/A |

---

## 2. Baseline Details & Per-Case Results

### Baseline: `deterministic_baseline` (ValidationEngine)

- **Provider:** deterministic
- **Status:** `COMPLETED`
- **Accuracy:** 100.0% (8/8)
- **Mean Evidence Recall:** 100.0%
- **Overall Evidence Recall:** 100.0% (18/18)
- **Total Tool Calls:** 0 (Successful: 0, Failed: 0, Duplicates: 0, Validation: 8)
- **Total Duration:** 2.94 ms (Mean: 0.37 ms)

#### Outcome Distribution

| Status / Outcome | Count |
| :--- | :--- |
| `VERIFIED` | 2 |
| `NOT_VERIFIED` | 3 |
| `INSUFFICIENT_EVIDENCE` | 2 |
| `NEEDS_REVIEW` | 1 |
| `FAILED` | 0 |
| `STEP_LIMIT_EXCEEDED` | 0 |

#### Failure Metrics

- Malformed Actions: 0
- Unknown Tools: 0
- Invalid Arguments: 0
- Tool Errors: 0
- LLM Errors: 0
- Timeouts: 0
- Retries: 0

#### Case-by-Case Breakdown

| Case ID | Invoice ID | Expected Status | Actual Status | Match | Evidence Recall | Steps | Tool Calls | Duration (ms) | Termination Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CASE-001` | `INV-1001` | `VERIFIED` | `VERIFIED` | **PASS** | 100% (3/3) | 0 | 0 | 1.26 ms | VALIDATION_APPLIED |
| `CASE-002` | `INV-1002` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | **PASS** | 100% (2/2) | 0 | 0 | 0.3 ms | VALIDATION_APPLIED |
| `CASE-003` | `INV-1003` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (2/2) | 0 | 0 | 0.27 ms | VALIDATION_APPLIED |
| `CASE-004` | `INV-1004` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (2/2) | 0 | 0 | 0.29 ms | VALIDATION_APPLIED |
| `CASE-005` | `INV-1005` | `NEEDS_REVIEW` | `NEEDS_REVIEW` | **PASS** | 100% (4/4) | 0 | 0 | 0.31 ms | VALIDATION_APPLIED |
| `CASE-006` | `INV-1006` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (1/1) | 0 | 0 | 0.25 ms | VALIDATION_APPLIED |
| `CASE-007` | `INV-1007` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | **PASS** | 100% (0/0) | 0 | 0 | 0.07 ms | VALIDATION_APPLIED |
| `CASE-008` | `INV-1008` | `VERIFIED` | `VERIFIED` | **PASS** | 100% (4/4) | 0 | 0 | 0.19 ms | VALIDATION_APPLIED |

---

### Baseline: `heuristic_baseline` (HeuristicAgentModel)

- **Provider:** heuristic
- **Status:** `COMPLETED`
- **Accuracy:** 100.0% (8/8)
- **Mean Evidence Recall:** 100.0%
- **Overall Evidence Recall:** 100.0% (18/18)
- **Total Tool Calls:** 51 (Successful: 51, Failed: 0, Duplicates: 0, Validation: 8)
- **Total Duration:** 3.65 ms (Mean: 0.46 ms)

#### Outcome Distribution

| Status / Outcome | Count |
| :--- | :--- |
| `VERIFIED` | 2 |
| `NOT_VERIFIED` | 3 |
| `INSUFFICIENT_EVIDENCE` | 2 |
| `NEEDS_REVIEW` | 1 |
| `FAILED` | 0 |
| `STEP_LIMIT_EXCEEDED` | 0 |

#### Failure Metrics

- Malformed Actions: 0
- Unknown Tools: 0
- Invalid Arguments: 0
- Tool Errors: 0
- LLM Errors: 0
- Timeouts: 0
- Retries: 0

#### Case-by-Case Breakdown

| Case ID | Invoice ID | Expected Status | Actual Status | Match | Evidence Recall | Steps | Tool Calls | Duration (ms) | Termination Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CASE-001` | `INV-1001` | `VERIFIED` | `VERIFIED` | **PASS** | 100% (3/3) | 7 | 7 | 0.71 ms | VALIDATION_REQUESTED |
| `CASE-002` | `INV-1002` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | **PASS** | 100% (2/2) | 7 | 7 | 0.51 ms | VALIDATION_REQUESTED |
| `CASE-003` | `INV-1003` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (2/2) | 7 | 7 | 0.47 ms | VALIDATION_REQUESTED |
| `CASE-004` | `INV-1004` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (2/2) | 7 | 7 | 0.46 ms | VALIDATION_REQUESTED |
| `CASE-005` | `INV-1005` | `NEEDS_REVIEW` | `NEEDS_REVIEW` | **PASS** | 100% (4/4) | 7 | 7 | 0.47 ms | VALIDATION_REQUESTED |
| `CASE-006` | `INV-1006` | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** | 100% (1/1) | 7 | 7 | 0.45 ms | VALIDATION_REQUESTED |
| `CASE-007` | `INV-1007` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | **PASS** | 100% (0/0) | 2 | 2 | 0.12 ms | VALIDATION_REQUESTED |
| `CASE-008` | `INV-1008` | `VERIFIED` | `VERIFIED` | **PASS** | 100% (4/4) | 7 | 7 | 0.46 ms | VALIDATION_REQUESTED |

---

### Baseline: `llm_decision_model` (none)

- **Provider:** unconfigured
- **Status:** `SKIPPED`
- **Accuracy:** 0.0% (0/0)
- **Mean Evidence Recall:** 0.0%
- **Overall Evidence Recall:** 0.0% (0/0)
- **Total Tool Calls:** 0 (Successful: 0, Failed: 0, Duplicates: 0, Validation: 0)
- **Total Duration:** 0.0 ms (Mean: 0.0 ms)

#### Outcome Distribution

| Status / Outcome | Count |
| :--- | :--- |
| `VERIFIED` | 0 |
| `NOT_VERIFIED` | 0 |
| `INSUFFICIENT_EVIDENCE` | 0 |
| `NEEDS_REVIEW` | 0 |
| `FAILED` | 0 |
| `STEP_LIMIT_EXCEEDED` | 0 |

#### Failure Metrics

- Malformed Actions: 0
- Unknown Tools: 0
- Invalid Arguments: 0
- Tool Errors: 0
- LLM Errors: 0
- Timeouts: 0
- Retries: 0

#### Case-by-Case Breakdown

| Case ID | Invoice ID | Expected Status | Actual Status | Match | Evidence Recall | Steps | Tool Calls | Duration (ms) | Termination Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

> **Notes:** Live LLM not evaluated in this run. Explicitly skipped to avoid external API dependency.

---

## 3. Evaluation Methodology & Metric Formulas

### Outcome Accuracy
- Formula: `accuracy = correct_cases / total_cases`
- Authoritative validation outcomes are computed by the deterministic `ValidationEngine`.
- Evaluated agents gather evidence and invoke `validate_investigation` to transfer authority.

### Evidence Recall
- Formula: `recall = |retrieved_evidence ∩ required_evidence| / |required_evidence|`
- If `|required_evidence| == 0` (e.g. no contract on record), recall is defined as 1.0 (100%).
- Mean evidence recall is the arithmetic mean across all cases.

### Tool Usage & Efficiency
- Recorded tool metrics include total steps, total calls, successful calls, failed calls, duplicate calls, and validation calls.
- Tool efficiency is evaluated transparently by observing tool call counts and duplicate ratios without arbitrary weighted formulas.

### Reproducibility & Limitations
- **Deterministic Baselines:** Baseline A (ValidationEngine) and Baseline B (HeuristicAgentModel) are 100% deterministic and reproducible across runs without network dependencies.
- **Live LLM Evaluations:** LLM evaluations depend on external model APIs and nondeterministic sampling (temperature=0.0 reduces variance but does not guarantee bitwise determinism).
- **Mock LLM Mode:** Provided for offline testing and continuous integration without API credentials.
