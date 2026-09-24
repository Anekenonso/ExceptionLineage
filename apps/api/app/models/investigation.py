from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty
from app.models.enums import InvestigationEventType, InvestigationStatus
from app.models.validation import ValidationResult


class Investigation(BaseModel):
    """Represents an ExceptionLineage investigation.

    The model defines the contract and vocabulary for an investigation lifecycle.
    Authoritative state transitions are governed by the InvestigationStateMachine.
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
    validation_results: list[ValidationResult] | None = Field(
        default=None,
        description="Discrete individual rule evaluation results from deterministic validation",
    )
    cited_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidentiary citations supporting the validation outcome",
    )

    @property
    def investigation_id(self) -> str:
        """Alias for id conforming to investigation domain naming conventions."""
        return self.id

    @property
    def current_state(self) -> InvestigationStatus:
        """Alias for status representing the current lifecycle state."""
        return self.status

    @current_state.setter
    def current_state(self, new_state: InvestigationStatus) -> None:
        self.status = new_state

    @model_validator(mode="before")
    @classmethod
    def _remap_alias_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "investigation_id" in data and "id" not in data:
                data["id"] = data["investigation_id"]
            if "current_state" in data and "status" not in data:
                data["status"] = data["current_state"]
        return data

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

    Captures state transitions and operational actions in an immutable audit trail.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique audit event identifier")
    investigation_id: str = Field(
        ..., description="ID of the investigation this event belongs to"
    )
    from_state: InvestigationStatus | None = Field(
        default=None,
        description="Previous lifecycle state before transition",
    )
    to_state: InvestigationStatus | None = Field(
        default=None,
        description="New lifecycle state after transition",
    )
    reason: str | None = Field(
        default=None,
        description="Rationale or trigger for the transition",
    )
    event_type: InvestigationEventType | str = Field(
        default=InvestigationEventType.STATE_TRANSITION,
        description="Standardized event category or descriptive event key",
    )
    message: str = Field(
        default="",
        description="Human-readable description of what transpired",
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the event occurred (UTC)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured context (e.g. tool inputs/outputs, model outputs, raw diffs)",
    )

    @property
    def event_id(self) -> str:
        """Alias for id conforming to event domain naming conventions."""
        return self.id

    @model_validator(mode="before")
    @classmethod
    def _remap_event_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "event_id" in data and "id" not in data:
                data["id"] = data["event_id"]
            if not data.get("message"):
                from_s = data.get("from_state")
                to_s = data.get("to_state")
                reason = data.get("reason")
                if from_s is not None and to_s is not None:
                    msg = f"Transitioned from {from_s} to {to_s}"
                    if reason:
                        msg += f": {reason}"
                    data["message"] = msg
                elif reason:
                    data["message"] = str(reason)
                else:
                    data["message"] = "Investigation event"
        return data

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

