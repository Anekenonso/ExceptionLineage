from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.common import (
    ensure_timezone_aware,
    utc_now,
    validate_date_range,
    validate_non_empty,
)


class Evidence(BaseModel):
    """Represents an item of evidence linking investigation claims to source records.

    Evidence is not automatically authoritative merely because it exists.
    Confidence, if present, is strictly constrained to [0.0, 1.0] and does not constitute proof.
    """

    id: str = Field(..., description="Unique evidence record identifier")
    evidence_type: str = Field(
        ...,
        description="Type of evidence (e.g. CONTRACT_CLAUSE, AMENDMENT_TERMS, APPROVAL_RECORD, RATE_TABLE)",
    )
    source: str = Field(
        ...,
        description="Originating system or artifact source (e.g. contracts, erp, email, approval_system)",
    )
    source_id: str = Field(
        ...,
        description="Identifier of the specific source record this evidence cites",
    )
    title: str | None = Field(
        default=None, description="Optional brief descriptive title"
    )
    locator: str | None = Field(
        default=None,
        description="Specific location within the source (e.g. 'Section 4.2', 'Page 12, Line 5')",
    )
    excerpt: str | None = Field(
        default=None,
        description="Direct textual excerpt, snippet, or content reference from the source",
    )
    captured_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when this evidence was ingested or captured (UTC)",
    )
    effective_from: datetime | None = Field(
        default=None,
        description="Date/time from which the underlying evidence was legally effective (UTC)",
    )
    effective_until: datetime | None = Field(
        default=None,
        description="Date/time until which the underlying evidence was legally effective (UTC)",
    )
    scope: str | None = Field(
        default=None,
        description="Applicable scope, jurisdiction, product line, or domain context",
    )
    confidence: float | None = Field(
        default=None,
        description="Optional assessment confidence bounded between 0.0 and 1.0",
    )

    @field_validator("id", "evidence_type", "source", "source_id", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("captured_at", "effective_from", "effective_until")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)

    @field_validator("confidence")
    @classmethod
    def check_confidence_range(cls, value: float | None) -> float | None:
        if value is not None and not (0.0 <= value <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0; received {value}")
        return value

    @model_validator(mode="after")
    def check_dates(self) -> "Evidence":
        validate_date_range(self.effective_from, self.effective_until)
        return self
