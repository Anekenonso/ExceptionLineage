# Stage 18 Evaluation Report

- **Suite ID:** `suite-936cb688a67f`
- **Timestamp:** `2026-09-28T05:17:38.176487+00:00`
- **Git Commit:** `80df16b31fa605fce4725e8d0005e5c777f551c7`
- **Dataset Version:** `benchmark-v1`

---

## Evaluation Status

**Overall:** `COMPLETED`

## Executive Summary

Deterministic and heuristic baselines completed successfully. Live LLM evaluation was SKIPPED.

---

## Baseline Results

| Baseline | Model Provider | Model Name | Status | Accuracy | Mean Evidence Recall | Total Tool Calls | Tool Errors | Mean Duration (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **deterministic_baseline** | deterministic | ValidationEngine | `COMPLETED` | 100.0% (8/8) | 100.0% | 0 | 0 | 0.36 ms |
| **heuristic_baseline** | heuristic | HeuristicAgentModel | `COMPLETED` | 100.0% (8/8) | 100.0% | 51 | 0 | 0.86 ms |

---

## Live LLM Evaluation

- **Status:** `SKIPPED`
- **Provider:** unconfigured
- **Model:** none
- **Accuracy:** 0.0%
- **Mean Evidence Recall:** 0.0%
- **Tool Calls:** 0

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

---

## Limitations

> **Notice:** A successful live-provider run is still required before making claims about LLM reasoning accuracy, tool-selection accuracy, evidence retrieval, or token efficiency.

---

## Reproduction

To execute the benchmark with an active live LLM provider, run:
```powershell
.\apps\api\venv\Scripts\python.exe evaluation/runner.py --with-llm
```
