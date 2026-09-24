"""Evaluation reporting library producing machine-readable JSON and human-readable Markdown (Stage 18)."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.schemas import EvaluationRun, EvaluationSuiteReport


def save_json_report(report: EvaluationSuiteReport | EvaluationRun, output_path: Path) -> None:
    """Save an evaluation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))


def generate_markdown_report(suite: EvaluationSuiteReport) -> str:
    """Generate a structured, human-readable Markdown evaluation report."""
    lines: list[str] = [
        f"# ExceptionLineage Quantitative Evaluation Report",
        f"",
        f"- **Suite ID:** `{suite.suite_id}`",
        f"- **Timestamp:** `{suite.timestamp}`",
        f"- **Git Commit:** `{suite.git_commit or 'unknown'}`",
        f"- **Dataset Version:** `{suite.dataset_version}`",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary & Baseline Comparison",
        f"",
        f"| Baseline / System | Model Provider | Model Name | Status | Accuracy | Mean Evidence Recall | Mean Steps | Total Tool Calls | Tool Errors | Mean Duration (ms) | Total Tokens |",
        f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for bname, run in suite.runs.items():
        agg = run.aggregate_metrics
        acc_pct = f"{agg.accuracy * 100:.1f}% ({agg.correct_cases}/{agg.total_cases})" if agg.total_cases > 0 else "N/A"
        rec_pct = f"{agg.mean_evidence_recall * 100:.1f}%"
        tokens_str = str(agg.total_tokens) if agg.total_tokens is not None else "N/A"
        lines.append(
            f"| **{bname}** | {run.model_provider} | {run.model_name} | `{run.status}` | {acc_pct} | {rec_pct} | {agg.mean_agent_steps} | {agg.total_tool_calls} | {agg.total_tool_errors} | {agg.mean_duration_ms} ms | {tokens_str} |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 2. Baseline Details & Per-Case Results",
        f"",
    ])

    for bname, run in suite.runs.items():
        agg = run.aggregate_metrics
        lines.extend([
            f"### Baseline: `{bname}` ({run.model_name})",
            f"",
            f"- **Provider:** {run.model_provider}",
            f"- **Status:** `{run.status}`",
            f"- **Accuracy:** {agg.accuracy * 100:.1f}% ({agg.correct_cases}/{agg.total_cases})",
            f"- **Mean Evidence Recall:** {agg.mean_evidence_recall * 100:.1f}%",
            f"- **Overall Evidence Recall:** {agg.overall_evidence_recall * 100:.1f}% ({agg.total_retrieved_required_evidence}/{agg.total_required_evidence})",
            f"- **Total Tool Calls:** {agg.total_tool_calls} (Successful: {agg.successful_tool_calls}, Failed: {agg.failed_tool_calls}, Duplicates: {agg.duplicate_tool_calls}, Validation: {agg.validation_calls})",
            f"- **Total Duration:** {agg.total_duration_ms} ms (Mean: {agg.mean_duration_ms} ms)",
            f"",
            f"#### Outcome Distribution",
            f"",
            f"| Status / Outcome | Count |",
            f"| :--- | :--- |",
        ])
        for term_status, count in agg.termination_counts.items():
            lines.append(f"| `{term_status}` | {count} |")

        lines.extend([
            f"",
            f"#### Failure Metrics",
            f"",
            f"- Malformed Actions: {agg.total_malformed_actions}",
            f"- Unknown Tools: {agg.total_unknown_tools}",
            f"- Invalid Arguments: {agg.total_invalid_arguments}",
            f"- Tool Errors: {agg.total_tool_errors}",
            f"- LLM Errors: {agg.total_llm_errors}",
            f"- Timeouts: {agg.total_timeouts}",
            f"- Retries: {agg.total_retries}",
            f"",
            f"#### Case-by-Case Breakdown",
            f"",
            f"| Case ID | Invoice ID | Expected Status | Actual Status | Match | Evidence Recall | Steps | Tool Calls | Duration (ms) | Termination Reason |",
            f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for c in run.case_results:
            match_icon = "PASS" if c.status_match else "FAIL"
            recall_str = f"{c.evidence_recall * 100:.0f}% ({c.retrieved_required_evidence_count}/{c.required_evidence_count})"
            lines.append(
                f"| `{c.case_id}` | `{c.invoice_id}` | `{c.expected_status}` | `{c.actual_status}` | **{match_icon}** | {recall_str} | {c.agent_steps} | {c.tool_calls} | {c.duration_ms} ms | {c.termination_reason or 'N/A'} |"
            )

        if run.notes:
            lines.extend([
                f"",
                f"> **Notes:** {run.notes}",
            ])

        lines.extend([f"", f"---", f""])

    lines.extend([
        f"## 3. Evaluation Methodology & Metric Formulas",
        f"",
        f"### Outcome Accuracy",
        f"- Formula: `accuracy = correct_cases / total_cases`",
        f"- Authoritative validation outcomes are computed by the deterministic `ValidationEngine`.",
        f"- Evaluated agents gather evidence and invoke `validate_investigation` to transfer authority.",
        f"",
        f"### Evidence Recall",
        f"- Formula: `recall = |retrieved_evidence ∩ required_evidence| / |required_evidence|`",
        f"- If `|required_evidence| == 0` (e.g. no contract on record), recall is defined as 1.0 (100%).",
        f"- Mean evidence recall is the arithmetic mean across all cases.",
        f"",
        f"### Tool Usage & Efficiency",
        f"- Recorded tool metrics include total steps, total calls, successful calls, failed calls, duplicate calls, and validation calls.",
        f"- Tool efficiency is evaluated transparently by observing tool call counts and duplicate ratios without arbitrary weighted formulas.",
        f"",
        f"### Reproducibility & Limitations",
        f"- **Deterministic Baselines:** Baseline A (ValidationEngine) and Baseline B (HeuristicAgentModel) are 100% deterministic and reproducible across runs without network dependencies.",
        f"- **Live LLM Evaluations:** LLM evaluations depend on external model APIs and nondeterministic sampling (temperature=0.0 reduces variance but does not guarantee bitwise determinism).",
        f"- **Mock LLM Mode:** Provided for offline testing and continuous integration without API credentials.",
        f"",
    ])

    return "\n".join(lines)


def save_markdown_report(markdown_content: str, output_path: Path) -> None:
    """Save markdown content to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
