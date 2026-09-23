from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty
from app.models.enums import InvestigationEventType, InvestigationStatus


class Investigation(BaseModel):
    """Represents an ExceptionLineage investigation.

    The model only defines the contract and vocabulary; state-transition logic
    belongs to the future investigation pipeline.
    """

    id: str = Field(..., description="Unique investigation identifier")
    invoice_id: str = Field(
        ..., description="Identifier of the target invoice being investigated"
    )
    exception_id: str | None = Field(
        default=None,
        description="Optional identifier of the specific transaction exception triggered",
    )
    status: InvestigationStatus = Field(
        default=InvestigationStatus.QUEUED,
        description="Current lifecycle status of the investigation",
    )
    summary: str | None = Field(
        default=None, description="Optional high-level executive summary of findings"
    )
    failure_reason: str | None = Field(
        default=None,
        description="Reason for failure if status is FAILED, or review context if NEEDS_REVIEW",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the investigation was initiated (UTC)",
    )
    updated_at: datetime | None = Field(
        default=None, description="Timestamp of latest investigation update (UTC)"
    )

    @field_validator("id", "invoice_id", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("created_at", "updated_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)


class InvestigationEvent(BaseModel):
    """Represents an auditable event in the timeline of an investigation.

    Supports the structured audit trail (e.g. INPUT -> EVIDENCE_FOUND ->
    AGENT_DECISION -> TOOL_CALL -> VALIDATION -> ACTION_RESULT).
    """

    id: str = Field(..., description="Unique audit event identifier")
    investigation_id: str = Field(
        ..., description="ID of the investigation this event belongs to"
    )
    event_type: InvestigationEventType | str = Field(
        ..., description="Standardized event category or descriptive event key"
    )
    message: str = Field(..., description="Human-readable description of what transpired")
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the event occurred (UTC)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured context (e.g. tool inputs/outputs, model outputs, raw diffs)",
    )

    @field_validator("id", "investigation_id", "message", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("timestamp")
    @classmethod
    def check_tz_aware(cls, value: datetime) -> datetime:
        res = ensure_timezone_aware(value)
        assert res is not None
        return res
