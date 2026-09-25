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
from evaluation.schemas import AggregateMetrics, CaseResult, EvaluationStatus


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


def _detect_provider_failure(case: CaseResult) -> tuple[bool, str | None, int | None, str | None]:
    """Inspect a case result to determine if it failed due to external LLM provider blockage."""
    if case.is_provider_failure:
        return True, case.provider_failure_category or "provider_error", case.provider_http_status, None

    text_to_check = " ".join(
        str(x) for x in [case.failure_reason, case.termination_reason, case.error] if x
    ).lower()

    if not text_to_check:
        return False, None, None, None

    # Check for HTTP 429 / quota / credit / rate limit
    if "429" in text_to_check or "rate limit" in text_to_check or "quota" in text_to_check or "credit" in text_to_check:
        return True, "provider_quota", 429, "credit_balance_exhausted"

    # Check for HTTP 401 / 403 / auth error
    if "401" in text_to_check or "403" in text_to_check or "authentication failed" in text_to_check:
        return True, "provider_auth", 401 if "401" in text_to_check else 403, "auth_failure"

    # Check for timeout / network
    if "timed out" in text_to_check or "timeout" in text_to_check:
        return True, "provider_timeout", None, "timeout"
    if "network connectivity" in text_to_check or "connecterror" in text_to_check:
        return True, "provider_network", None, "connection_error"

    if "provider error" in text_to_check:
        return True, "provider_error", None, "provider_error"

    return False, None, None, None


def classify_run_status(
    case_results: list[CaseResult],
    aggregate: AggregateMetrics,
) -> tuple[EvaluationStatus, str | None]:
    """Determine the authoritative EvaluationStatus and explanatory detail."""
    total_cases = len(case_results)
    if total_cases == 0:
        return EvaluationStatus.COMPLETED, "No cases evaluated"

    provider_failures = aggregate.provider_failures

    # 1. Total provider blockage
    if provider_failures == total_cases:
        category = aggregate.provider_failure_category or "provider_error"
        status_str = f" (HTTP {aggregate.provider_http_status})" if aggregate.provider_http_status else ""
        return (
            EvaluationStatus.BLOCKED_PROVIDER,
            f"All {total_cases} cases blocked by external LLM provider{status_str}: {category}",
        )

    # 2. Partial execution
    if provider_failures > 0:
        return (
            EvaluationStatus.PARTIAL,
            f"{provider_failures}/{total_cases} cases failed due to provider errors; partial evaluation",
        )

    # 3. System crash
    system_errors = sum(1 for c in case_results if c.error and not c.is_provider_failure)
    if system_errors == total_cases:
        return EvaluationStatus.FAILED_SYSTEM, "All cases failed due to internal system exceptions"
    elif system_errors > 0:
        return EvaluationStatus.PARTIAL, f"{system_errors}/{total_cases} cases failed due to system exceptions"

    # 4. Completed normally
    return EvaluationStatus.COMPLETED, "All cases completed evaluation"


def compute_aggregate_metrics(case_results: list[CaseResult]) -> AggregateMetrics:
    """Aggregate per-case metrics into a comprehensive quantitative summary.

    Strictly adheres to evaluation integrity:
    - Distinguishes model-performance metrics from provider/infrastructure failure metrics.
    - If cases were blocked by external provider before model completion, model accuracy
      and recall are marked as unmeasurable (null/None) rather than reporting 0%.
    """
    total_cases = len(case_results)
    if total_cases == 0:
        return AggregateMetrics()

    # 1. Inspect and classify provider failures
    provider_fail_count = 0
    detected_cat: str | None = None
    detected_http: int | None = None
    detected_code: str | None = None

    for c in case_results:
        is_prov, cat, http_s, code = _detect_provider_failure(c)
        if is_prov:
            c.is_provider_failure = True
            c.provider_failure_category = cat
            c.provider_http_status = http_s
            # If the model never executed, evidence recall is unmeasurable (do not fabricate 1.0 for CASE-007)
            c.evidence_recall = None
            provider_fail_count += 1
            if not detected_cat:
                detected_cat = cat
            if not detected_http:
                detected_http = http_s
            if not detected_code:
                detected_code = code

    all_provider_blocked = (provider_fail_count == total_cases)
    any_provider_blocked = (provider_fail_count > 0)
    cases_completed = sum(1 for c in case_results if not c.is_provider_failure and c.actual_status != "FAILED")

    # 2. Outcome Accuracy & Measurability
    if all_provider_blocked:
        accuracy: float | None = None
        is_measurable = False
        unmeasurable_reason = "UNMEASURABLE — provider quota / rate limit failure (requests rejected prior to model completion)"
    elif any_provider_blocked:
        accuracy = None
        is_measurable = False
        unmeasurable_reason = f"PARTIAL — {provider_fail_count}/{total_cases} cases blocked by external provider"
    else:
        correct_cases = sum(1 for c in case_results if c.status_match)
        accuracy = round(correct_cases / total_cases, 4)
        is_measurable = True
        unmeasurable_reason = None

    correct_cases_count = sum(1 for c in case_results if c.status_match)

    # 3. Evidence recall
    if all_provider_blocked:
        mean_recall: float | None = None
        overall_recall: float | None = None
        total_retrieved_required = 0
    else:
        valid_recalls = [c.evidence_recall for c in case_results if c.evidence_recall is not None]
        mean_recall = round(sum(valid_recalls) / len(valid_recalls), 4) if valid_recalls else None
        total_required_sum = sum(c.required_evidence_count for c in case_results)
        total_retrieved_required = sum(c.retrieved_required_evidence_count for c in case_results)
        overall_recall = (
            round(total_retrieved_required / total_required_sum, 4)
            if total_required_sum > 0
            else 1.0
        )

    total_required = sum(c.required_evidence_count for c in case_results)

    # 4. Tool usage
    total_steps = sum(c.agent_steps for c in case_results)
    mean_steps = round(total_steps / total_cases, 2)
    total_calls = sum(c.tool_calls for c in case_results)
    mean_calls = round(total_calls / total_cases, 2)
    successful_calls = sum(c.successful_tool_calls for c in case_results)
    failed_calls = sum(c.failed_tool_calls for c in case_results)
    duplicate_calls = sum(c.duplicate_tool_calls for c in case_results)
    validation_calls = sum(c.validation_calls for c in case_results)

    # 5. Termination counts
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

    # 6. Failure metrics
    malformed = sum(c.malformed_actions for c in case_results)
    unknown_tools = sum(c.unknown_tools for c in case_results)
    invalid_args = sum(c.invalid_arguments for c in case_results)
    tool_errors = sum(c.tool_errors for c in case_results)
    llm_errors = sum(c.llm_errors for c in case_results)
    timeouts = sum(c.timeouts for c in case_results)
    retries = sum(c.retries for c in case_results)

    # 7. Operational metrics
    total_duration = round(sum(c.duration_ms for c in case_results), 2)
    mean_duration = round(total_duration / total_cases, 2)
    total_llm_calls = sum(c.llm_calls for c in case_results)

    # Token aggregates
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
        correct_cases=correct_cases_count,
        accuracy=accuracy,
        is_measurable=is_measurable,
        unmeasurable_reason=unmeasurable_reason,
        cases_attempted=total_cases,
        cases_completed=cases_completed,
        provider_failures=provider_fail_count,
        provider_failure_category=detected_cat,
        provider_http_status=detected_http,
        provider_error_code=detected_code,
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

