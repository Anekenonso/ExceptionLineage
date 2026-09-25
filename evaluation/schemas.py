"""Pydantic schemas for ExceptionLineage evaluation harness and reporting (Stage 18).

Provides typed schemas for:
- CaseResult: Per-case evaluation outputs and detailed metrics.
- AggregateMetrics: Rollup metrics (accuracy, recall, tool usage, failures, tokens).
- EvaluationRun: Complete record of a single baseline evaluation run.
- EvaluationSuiteReport: Comparative report containing multiple baseline runs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    """Explicit lifecycle and outcome status for evaluation runs and suites."""

    COMPLETED = "COMPLETED"
    BLOCKED_PROVIDER = "BLOCKED_PROVIDER"
    PARTIAL = "PARTIAL"
    FAILED_SYSTEM = "FAILED_SYSTEM"
    SKIPPED = "SKIPPED"


class CaseResult(BaseModel):
    """Evaluation result for an individual benchmark case."""

    case_id: str = Field(..., description="Unique case identifier, e.g. CASE-001")
    invoice_id: str = Field(..., description="Target invoice identifier, e.g. INV-1001")
    scenario_type: str | None = Field(default=None, description="Scenario classification")
    expected_status: str = Field(..., description="Ground truth expected status")
    actual_status: str = Field(..., description="Outcome status produced by system")
    status_match: bool = Field(..., description="Whether actual status equals expected status")
    termination_reason: str | None = Field(default=None, description="Reason for termination")
    summary: str | None = Field(default=None, description="Investigation summary text")
    failure_reason: str | None = Field(default=None, description="Explanation of failure or rejection")

    # Provider and infrastructure failure tracking
    is_provider_failure: bool = Field(
        default=False,
        description="Whether this case failed due to external LLM provider/infrastructure error",
    )
    provider_failure_category: str | None = Field(
        default=None,
        description="Category of provider failure: provider_quota, provider_auth, provider_network, etc.",
    )
    provider_http_status: int | None = Field(
        default=None,
        description="HTTP status returned by provider if applicable",
    )

    # Evidence retrieval metrics
    required_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Ground truth required evidence IDs",
    )
    retrieved_evidence_ids: list[str] = Field(
        default_factory=list,
        description="All evidence IDs gathered during investigation",
    )
    cited_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence IDs specifically cited in authoritative validation outcome",
    )
    required_evidence_count: int = Field(default=0, description="Total ground truth evidence items")
    retrieved_required_evidence_count: int = Field(
        default=0,
        description="Ground truth evidence items actually retrieved",
    )
    evidence_recall: float | None = Field(
        default=None,
        description="Recall fraction: retrieved_required / required (null if unmeasurable due to provider failure)",
    )

    # Tool and agent metrics
    agent_steps: int = Field(default=0, description="Number of agent loop steps")
    tool_calls: int = Field(default=0, description="Total tool invocations attempted")
    successful_tool_calls: int = Field(default=0, description="Tool calls that succeeded")
    failed_tool_calls: int = Field(default=0, description="Tool calls that failed")
    duplicate_tool_calls: int = Field(default=0, description="Repeated identical tool calls")
    validation_calls: int = Field(default=0, description="Invocations of validation tool/engine")

    # Failure metrics
    malformed_actions: int = Field(default=0, description="Malformed agent actions")
    unknown_tools: int = Field(default=0, description="Calls to nonexistent tools")
    invalid_arguments: int = Field(default=0, description="Calls with invalid arguments")
    tool_errors: int = Field(default=0, description="Errors returned by tools")
    llm_errors: int = Field(default=0, description="LLM network or provider failures")
    timeouts: int = Field(default=0, description="Timeouts during execution")
    retries: int = Field(default=0, description="Retries performed")

    # Operational metrics
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    llm_calls: int = Field(default=0, description="Total LLM API calls")
    prompt_tokens: int | None = Field(default=None, description="Prompt tokens used (null if unavailable)")
    completion_tokens: int | None = Field(default=None, description="Completion tokens used (null if unavailable)")
    total_tokens: int | None = Field(default=None, description="Total tokens used (null if unavailable)")

    error: str | None = Field(default=None, description="Exception or error message if case crashed")


class AggregateMetrics(BaseModel):
    """Aggregated quantitative metrics rolled up across an evaluation run."""

    total_cases: int = Field(default=0, description="Total benchmark cases evaluated")
    correct_cases: int = Field(default=0, description="Cases matching expected outcome")
    accuracy: float | None = Field(
        default=0.0,
        description="correct_cases / total_cases (0.0 to 1.0, null if unmeasurable)",
    )

    # Model measurability & Provider breakdown
    is_measurable: bool = Field(
        default=True,
        description="Whether model reasoning was measurable (False if blocked by provider)",
    )
    unmeasurable_reason: str | None = Field(
        default=None,
        description="Explanation if model reasoning was unmeasurable",
    )
    cases_attempted: int = Field(default=0, description="Total benchmark cases attempted in this run")
    cases_completed: int = Field(default=0, description="Cases reaching model reasoning completion")
    provider_failures: int = Field(default=0, description="Count of cases failing due to provider errors")
    provider_failure_category: str | None = Field(
        default=None,
        description="Category of provider failure: provider_quota, provider_auth, etc.",
    )
    provider_http_status: int | None = Field(default=None, description="Provider HTTP status code")
    provider_error_code: str | None = Field(
        default=None,
        description="Provider error code e.g. credit_balance_exhausted / insufficient_quota",
    )

    # Evidence retrieval metrics
    mean_evidence_recall: float | None = Field(
        default=0.0,
        description="Mean of per-case evidence recall fractions (null if unmeasurable)",
    )
    total_required_evidence: int = Field(default=0, description="Sum of required evidence across cases")
    total_retrieved_required_evidence: int = Field(
        default=0,
        description="Sum of retrieved required evidence across cases",
    )
    overall_evidence_recall: float | None = Field(
        default=0.0,
        description="total_retrieved_required / total_required (null if unmeasurable)",
    )

    # Tool usage aggregates
    total_agent_steps: int = Field(default=0, description="Sum of agent steps")
    mean_agent_steps: float = Field(default=0.0, description="Average agent steps per case")
    total_tool_calls: int = Field(default=0, description="Sum of tool calls")
    mean_tool_calls: float = Field(default=0.0, description="Average tool calls per case")
    successful_tool_calls: int = Field(default=0, description="Sum of successful tool calls")
    failed_tool_calls: int = Field(default=0, description="Sum of failed tool calls")
    duplicate_tool_calls: int = Field(default=0, description="Sum of duplicate tool calls")
    validation_calls: int = Field(default=0, description="Sum of validation invocations")

    # Termination counts
    termination_counts: dict[str, int] = Field(
        default_factory=lambda: {
            "VERIFIED": 0,
            "NOT_VERIFIED": 0,
            "INSUFFICIENT_EVIDENCE": 0,
            "NEEDS_REVIEW": 0,
            "FAILED": 0,
            "STEP_LIMIT_EXCEEDED": 0,
        },
        description="Distribution of final terminal states and step-limit exhaustion",
    )

    # Failure metrics totals
    total_malformed_actions: int = Field(default=0, description="Sum of malformed model actions")
    total_unknown_tools: int = Field(default=0, description="Sum of calls to unknown tools")
    total_invalid_arguments: int = Field(default=0, description="Sum of invalid tool arguments")
    total_tool_errors: int = Field(default=0, description="Sum of tool execution errors")
    total_llm_errors: int = Field(default=0, description="Sum of LLM provider or network errors")
    total_timeouts: int = Field(default=0, description="Sum of network or read timeouts")
    total_retries: int = Field(default=0, description="Sum of model retries")

    # Operational aggregates
    total_duration_ms: float = Field(default=0.0, description="Total runtime across all cases in ms")
    mean_duration_ms: float = Field(default=0.0, description="Average case duration in ms")
    total_llm_calls: int = Field(default=0, description="Total LLM API invocations")
    total_prompt_tokens: int | None = Field(default=None, description="Sum of prompt tokens (null if unavailable)")
    total_completion_tokens: int | None = Field(default=None, description="Sum of completion tokens (null if unavailable)")
    total_tokens: int | None = Field(default=None, description="Sum of total tokens (null if unavailable)")


class EvaluationRun(BaseModel):
    """Complete evaluation run results for a single baseline or model."""

    run_id: str = Field(..., description="Unique run identifier (UUID)")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of execution")
    git_commit: str | None = Field(default=None, description="Git commit hash if available")
    dataset_version: str = Field(..., description="Dataset name and version tag")
    baseline_name: str = Field(..., description="Identifier of the evaluated baseline/model")
    model_provider: str | None = Field(default=None, description="Provider: e.g. deterministic, heuristic, openai")
    model_name: str | None = Field(default=None, description="Specific model: e.g. ValidationEngine, gpt-4o-mini")
    configuration: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized configuration settings (never secrets)",
    )
    status: EvaluationStatus = Field(
        default=EvaluationStatus.COMPLETED,
        description="Run status: COMPLETED, BLOCKED_PROVIDER, PARTIAL, FAILED_SYSTEM, or SKIPPED",
    )
    status_detail: str | None = Field(default=None, description="Explanation or diagnostics for run status")
    case_results: list[CaseResult] = Field(default_factory=list, description="Per-case evaluation results")
    aggregate_metrics: AggregateMetrics = Field(
        default_factory=AggregateMetrics,
        description="Aggregated metrics across all evaluated cases",
    )
    notes: str | None = Field(default=None, description="Operational notes, warnings, or limitations")


class EvaluationSuiteReport(BaseModel):
    """Comparative evaluation report combining multiple baseline runs."""

    suite_id: str = Field(..., description="Unique suite execution identifier")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    git_commit: str | None = Field(default=None, description="Git commit hash if available")
    dataset_version: str = Field(..., description="Dataset version evaluated")
    status: EvaluationStatus = Field(
        default=EvaluationStatus.COMPLETED,
        description="Overall suite evaluation status: COMPLETED, BLOCKED_PROVIDER, PARTIAL, FAILED_SYSTEM, or SKIPPED",
    )
    status_detail: str | None = Field(default=None, description="Overall suite status explanation")
    runs: dict[str, EvaluationRun] = Field(
        default_factory=dict,
        description="Evaluation runs indexed by baseline key",
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="High-level comparative metrics across baselines",
    )

