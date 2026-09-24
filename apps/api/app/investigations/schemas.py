"""Pydantic request and response schemas for investigation API endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.enums import InvestigationStatus
from app.models.investigation import Investigation, InvestigationEvent
from app.models.validation import ValidationResult


class InvestigationCreateRequest(BaseModel):
    """Payload to initiate a new deterministic investigation."""

    invoice_id: str = Field(..., description="Target invoice identifier to investigate")
    exception_id: str | None = Field(
        default=None, description="Optional transaction exception identifier"
    )

    @field_validator("invoice_id")
    @classmethod
    def validate_invoice_id(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("invoice_id cannot be empty or whitespace")
        return v.strip()


class InvestigationResponse(BaseModel):
    """Structured response model representing an investigation and its outcome."""

    investigation_id: str = Field(..., description="Unique investigation identifier")
    invoice_id: str = Field(..., description="Target invoice identifier investigated")
    exception_id: str | None = Field(
        default=None, description="Associated transaction exception identifier"
    )
    status: InvestigationStatus = Field(
        ..., description="Current or terminal lifecycle status of the investigation"
    )
    summary: str | None = Field(
        default=None, description="Executive narrative summarizing findings"
    )
    failure_reason: str | None = Field(
        default=None,
        description="Reason for failure if FAILED, or review context if NEEDS_REVIEW",
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the investigation was initiated (UTC)"
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
    events: list[InvestigationEvent] | None = Field(
        default=None,
        description="Immutable chronological lifecycle audit events",
    )

    @classmethod
    def from_investigation(
        cls,
        inv: Investigation,
        events: list[InvestigationEvent] | None = None,
    ) -> InvestigationResponse:
        """Construct an InvestigationResponse from domain Investigation and events."""
        return cls(
            investigation_id=inv.id,
            invoice_id=inv.invoice_id,
            exception_id=inv.exception_id,
            status=inv.status,
            summary=inv.summary,
            failure_reason=inv.failure_reason,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            validation_results=inv.validation_results,
            cited_evidence_ids=inv.cited_evidence_ids or [],
            events=events,
        )
