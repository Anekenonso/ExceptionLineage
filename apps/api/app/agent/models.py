"""Data models for the controlled investigation agent in ExceptionLineage."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.models.common import utc_now


class ToolResult(BaseModel):
    """Structured result returned by an investigation tool execution."""

    tool_name: str = Field(..., description="Identifier of the executed tool")
    success: bool = Field(..., description="Whether the tool executed without error")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured entity data returned by the tool",
    )
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Evidentiary records retrieved by the tool with provenance",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the tool execution failed",
    )


class AgentAction(BaseModel):
    """Structured decision returned by the agent model."""

    action: str = Field(..., description="Tool name to execute, or 'validate_investigation'")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Typed arguments to pass to the tool",
    )
    reason: str | None = Field(
        default=None,
        description="Rationale for selecting this action",
    )


class AgentMetrics(BaseModel):
    """Instrumentation metrics capturing investigation agent performance and behavior."""

    total_agent_steps: int = Field(default=0, description="Total steps/iterations taken by agent")
    tool_calls: int = Field(default=0, description="Total tool invocations attempted")
    successful_tool_calls: int = Field(default=0, description="Tool invocations that succeeded")
    failed_tool_calls: int = Field(default=0, description="Tool invocations that failed")
    investigation_duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    evidence_items_collected: int = Field(default=0, description="Total evidence records collected")
    duplicate_tool_calls: int = Field(default=0, description="Repeated identical tool calls")
    termination_reason: str | None = Field(default=None, description="Reason why the agent loop ended")

    # LLM operational metrics
    llm_calls: int = Field(default=0, description="Total calls made to the LLM model adapter")
    llm_failures: int = Field(default=0, description="Total network, timeout, or auth failures with LLM")
    llm_retries: int = Field(default=0, description="Retries performed due to malformed structured output")
    malformed_actions: int = Field(default=0, description="Total malformed actions returned by the model")
    unknown_tool_calls: int = Field(default=0, description="Total invocations of nonexistent tools")
    invalid_argument_calls: int = Field(default=0, description="Total invocations with invalid arguments")
    tool_errors: int = Field(default=0, description="Total tool execution errors returned by tools")
    llm_timeouts: int = Field(default=0, description="Total LLM network or read timeouts")
    prompt_tokens: int | None = Field(default=None, description="Reported prompt tokens if available")
    completion_tokens: int | None = Field(default=None, description="Reported completion tokens if available")
    total_tokens: int | None = Field(default=None, description="Total tokens used if available")


class AgentState(BaseModel):
    """State of an ongoing investigation agent session."""

    investigation_id: str
    invoice_id: str
    exception_id: str | None = None
    current_question: str = Field(
        default="Investigate invoice exception and determine contractual compliance"
    )
    observations: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)

    # Accumulated lineage items discovered by tools
    invoice: dict[str, Any] | None = None
    customer: dict[str, Any] | None = None
    contract: dict[str, Any] | None = None
    exception: dict[str, Any] | None = None
    approval: dict[str, Any] | None = None
    amendments: list[dict[str, Any]] = Field(default_factory=list)
    sows: list[dict[str, Any]] = Field(default_factory=list)

    tool_calls: list[str] = Field(default_factory=list)
    steps: int = 0
    missing_evidence: list[str] = Field(default_factory=list)
    investigation_complete: bool = False
    failure_reason: str | None = None
