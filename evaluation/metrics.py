"""Metric computation library for ExceptionLineage evaluation harness (Stage 18).

Provides explicit, transparent, and non-misleading calculations for:
1. Outcome Accuracy:
   - accuracy = correct_cases / total_cases
2. Evidence Retrieval:
   - evidence_recall = |retrieved_evidence ∩ required_evidence| / |required_evidence|
   - If required_evidence is empty, recall is defined as 1.0 (no required evidence missed).
   - overall_evidence_recall = total_retrieved_required / total_required
3. Tool Usage:
   - total agent steps, mean agent steps
   - total tool calls, mean tool calls
   - successful, failed, duplicate, and validation tool calls
4. Termination Breakdown:
   - counts of VERIFIED, NOT_VERIFIED, INSUFFICIENT_EVIDENCE, NEEDS_REVIEW, FAILED, STEP_LIMIT_EXCEEDED
5. Failure Metrics:
   - malformed actions, unknown tools, invalid arguments, tool errors, LLM errors, timeouts, retries
6. Operational Metrics:
   - duration_ms, LLM calls, token usage (null when unavailable)
"""

from __future__ import annotations

from typing import Iterable
from evaluation.schemas import AggregateMetrics, CaseResult


def compute_evidence_recall(
    required_ids: Iterable[str],
    retrieved_ids: Iterable[str],
) -> tuple[int, int, float]:
    """Calculate required count, retrieved required count, and recall fraction.

    Returns:
        (required_count, retrieved_required_count, recall_fraction)
    """
    req_set = set(required_ids)
    ret_set = set(retrieved_ids)

    req_count = len(req_set)
    if req_count == 0:
        return 0, 0, 1.0

    ret_req_count = len(req_set.intersection(ret_set))
    recall = round(ret_req_count / req_count, 4)
    return req_count, ret_req_count, recall


def compute_aggregate_metrics(case_results: list[CaseResult]) -> AggregateMetrics:
    """Aggregate per-case metrics into a comprehensive quantitative summary."""
    total_cases = len(case_results)
    if total_cases == 0:
        return AggregateMetrics()

    correct_cases = sum(1 for c in case_results if c.status_match)
    accuracy = round(correct_cases / total_cases, 4)

    # Evidence recall
    mean_recall = round(sum(c.evidence_recall for c in case_results) / total_cases, 4)
    total_required = sum(c.required_evidence_count for c in case_results)
    total_retrieved_required = sum(c.retrieved_required_evidence_count for c in case_results)
    overall_recall = (
        round(total_retrieved_required / total_required, 4) if total_required > 0 else 1.0
    )

    # Tool usage
    total_steps = sum(c.agent_steps for c in case_results)
    mean_steps = round(total_steps / total_cases, 2)
    total_calls = sum(c.tool_calls for c in case_results)
    mean_calls = round(total_calls / total_cases, 2)
    successful_calls = sum(c.successful_tool_calls for c in case_results)
    failed_calls = sum(c.failed_tool_calls for c in case_results)
    duplicate_calls = sum(c.duplicate_tool_calls for c in case_results)
    validation_calls = sum(c.validation_calls for c in case_results)

    # Termination counts
    term_counts: dict[str, int] = {
        "VERIFIED": 0,
        "NOT_VERIFIED": 0,
        "INSUFFICIENT_EVIDENCE": 0,
        "NEEDS_REVIEW": 0,
        "FAILED": 0,
        "STEP_LIMIT_EXCEEDED": 0,
    }
    for c in case_results:
        if c.termination_reason == "AGENT_STEP_LIMIT_EXCEEDED":
            term_counts["STEP_LIMIT_EXCEEDED"] += 1
        elif c.actual_status in term_counts:
            term_counts[c.actual_status] += 1
        else:
            term_counts[c.actual_status] = term_counts.get(c.actual_status, 0) + 1

    # Failure metrics
    malformed = sum(c.malformed_actions for c in case_results)
    unknown_tools = sum(c.unknown_tools for c in case_results)
    invalid_args = sum(c.invalid_arguments for c in case_results)
    tool_errors = sum(c.tool_errors for c in case_results)
    llm_errors = sum(c.llm_errors for c in case_results)
    timeouts = sum(c.timeouts for c in case_results)
    retries = sum(c.retries for c in case_results)

    # Operational metrics
    total_duration = round(sum(c.duration_ms for c in case_results), 2)
    mean_duration = round(total_duration / total_cases, 2)
    total_llm_calls = sum(c.llm_calls for c in case_results)

    # Token aggregates: Only sum if token metrics were reported, otherwise None
    has_tokens = any(c.total_tokens is not None for c in case_results)
    total_prompt_tokens = (
        sum(c.prompt_tokens for c in case_results if c.prompt_tokens is not None)
        if has_tokens
        else None
    )
    total_completion_tokens = (
        sum(c.completion_tokens for c in case_results if c.completion_tokens is not None)
        if has_tokens
        else None
    )
    total_tokens = (
        sum(c.total_tokens for c in case_results if c.total_tokens is not None)
        if has_tokens
        else None
    )

    return AggregateMetrics(
        total_cases=total_cases,
        correct_cases=correct_cases,
        accuracy=accuracy,
        mean_evidence_recall=mean_recall,
        total_required_evidence=total_required,
        total_retrieved_required_evidence=total_retrieved_required,
        overall_evidence_recall=overall_recall,
        total_agent_steps=total_steps,
        mean_agent_steps=mean_steps,
        total_tool_calls=total_calls,
        mean_tool_calls=mean_calls,
        successful_tool_calls=successful_calls,
        failed_tool_calls=failed_calls,
        duplicate_tool_calls=duplicate_calls,
        validation_calls=validation_calls,
        termination_counts=term_counts,
        total_malformed_actions=malformed,
        total_unknown_tools=unknown_tools,
        total_invalid_arguments=invalid_args,
        total_tool_errors=tool_errors,
        total_llm_errors=llm_errors,
        total_timeouts=timeouts,
        total_retries=retries,
        total_duration_ms=total_duration,
        mean_duration_ms=mean_duration,
        total_llm_calls=total_llm_calls,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_tokens=total_tokens,
    )
