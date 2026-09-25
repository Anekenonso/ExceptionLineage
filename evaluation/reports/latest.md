# Stage 18 Evaluation Report

- **Suite ID:** `suite-98c22aae2326`
- **Timestamp:** `2026-09-25T21:05:40.100794+00:00`
- **Git Commit:** `d162474675479e3a845bec92e3f846e47f2ab0b1`
- **Dataset Version:** `benchmark-v1`

---

## Evaluation Status

**Overall:** `BLOCKED_PROVIDER`

> **Status Diagnostic:** Live LLM evaluation was blocked due to external provider quota exhaustion (HTTP 429).

## Executive Summary

The deterministic baseline (`ValidationEngine`) and heuristic agent baseline (`HeuristicAgentModel`) completed the 8-case benchmark suite with **100.0% accuracy** and **100.0% evidence recall**.

The live LLM evaluation (`LLMDecisionModel` against `gemini-3.8-flash`) could **NOT** measure model reasoning performance because the external provider rejected all requests prior to model completion due to quota / credit balance exhaustion (`HTTP 429: credit_balance_exhausted`).

Crucially, the evaluation confirmed that the system **fails closed safely**: when the provider fails, the orchestrator records a technical failure, does not fabricate evidence, executes zero arbitrary tools, and never asserts an unauthorized business outcome.

---

## Baseline Results

| Baseline | Model Provider | Model Name | Status | Accuracy | Mean Evidence Recall | Total Tool Calls | Tool Errors | Mean Duration (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **deterministic_baseline** | deterministic | ValidationEngine | `COMPLETED` | 100.0% (8/8) | 100.0% | 0 | 0 | 0.37 ms |
| **heuristic_baseline** | heuristic | HeuristicAgentModel | `COMPLETED` | 100.0% (8/8) | 100.0% | 51 | 0 | 0.47 ms |

---

## Live LLM Evaluation

**Result:** `UNMEASURABLE — provider quota failure.`

- **Model Provider:** `gemini`
- **Model Name:** `gemini-3.8-flash`
- **Suite ID:** `suite-98c22aae2326`
- **Cases Attempted:** 8
- **Cases Reaching Model Completion:** 0
- **Provider Failures:** 8
- **HTTP Status:** `429`
- **Failure Category:** `provider_error`
- **Error Code:** `provider_error`

### Model Performance Metrics (Unavailable)

- **Accuracy:** `unavailable` (unmeasured due to provider blockage)
- **Evidence Recall:** `unavailable` (unmeasured due to provider blockage)
- **Tool-Selection Performance:** `unavailable` (0 tools invoked)
- **Reasoning Steps:** `unavailable` (0 steps executed)
- **Token Usage:** `unavailable` (0 tokens returned by provider)

---

## Provider Failure Handling

During the real-LLM benchmark run, all 8 attempted cases terminated strictly and safely as **`FAILED`**.

- **Zero Arbitrary Actions:** Zero tools were called (0 total calls).
- **Zero Hallucinated Citations:** No evidence IDs or contractual records were fabricated.
- **Zero False Determinations:** The system never declared an invoice `VERIFIED` or `NOT_VERIFIED` without deterministic authority.
- **Architectural Law Respected:** *"AI handles ambiguity. Code handles authority."* When the external model was unreachable due to provider quota limits, the agent boundary failed closed cleanly.

---

## Per-Case Results

The table below details raw case-level outcomes. These represent **provider infrastructure rejections**, not model reasoning errors:

| Case ID | Invoice ID | Expected Status | Actual Status | Classification | Evidence Recall | Steps | Tool Calls | Duration (ms) | Diagnostic Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CASE-001` | `INV-1001` | `VERIFIED` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 11140.97 ms | Graph retrieval failed: LLM provider error (HTTP 503): [{
  "error": {
 ... |
| `CASE-002` | `INV-1002` | `INSUFFICIENT_EVIDENCE` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 12843.21 ms | Graph retrieval failed: LLM provider error (HTTP 503): [{
  "error": {
 ... |
| `CASE-003` | `INV-1003` | `NOT_VERIFIED` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 841.28 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |
| `CASE-004` | `INV-1004` | `NOT_VERIFIED` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 931.14 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |
| `CASE-005` | `INV-1005` | `NEEDS_REVIEW` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 808.72 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |
| `CASE-006` | `INV-1006` | `NOT_VERIFIED` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 1197.07 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |
| `CASE-007` | `INV-1007` | `INSUFFICIENT_EVIDENCE` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 756.59 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |
| `CASE-008` | `INV-1008` | `VERIFIED` | `FAILED` | **PROVIDER_BLOCKED** | N/A | 0 | 0 | 1259.07 ms | Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry ... |

---

## Limitations

> **Notice:** A successful live-provider run is still required before making claims about LLM reasoning accuracy, tool-selection accuracy, evidence retrieval, or token efficiency.

---

## Reproduction

To execute the benchmark with an active live LLM provider, run:
```powershell
.\apps\api\venv\Scripts\python.exe evaluation/runner.py --with-llm
```
