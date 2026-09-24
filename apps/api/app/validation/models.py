"""Data models for deterministic validation engine outcomes in ExceptionLineage."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty
from app.models.enums import InvestigationStatus, ValidationStatus
from app.models.validation import ValidationResult


class ValidationOutcome(BaseModel):
    """Represents the complete outcome of executing the deterministic validation engine.

    Includes the overall investigation determination (VERIFIED, NOT_VERIFIED,
    INSUFFICIENT_EVIDENCE, or NEEDS_REVIEW), an auditable summary narrative,
    individual discrete check results, and cited evidence IDs.
    """

    status: InvestigationStatus = Field(
        ...,
        description="Overall investigation determination outcome",
    )
    summary: str = Field(
        ...,
        description="Deterministic executive narrative summarizing the validation findings",
    )
    results: list[ValidationResult] = Field(
        default_factory=list,
        description="Discrete individual rule evaluation results",
    )
    cited_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Unique evidentiary citations supporting all evaluated checks",
    )
    failure_reason: str | None = Field(
        default=None,
        description="Failure rationale if NOT_VERIFIED, missing data description if INSUFFICIENT_EVIDENCE, or escalation context if NEEDS_REVIEW",
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when validation was completed (UTC)",
    )

    @field_validator("summary", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("timestamp")
    @classmethod
    def check_tz_aware(cls, value: datetime) -> datetime:
        res = ensure_timezone_aware(value)
        assert res is not None
        return res

    @property
    def is_verified(self) -> bool:
        return self.status == InvestigationStatus.VERIFIED

    @property
    def passed_checks(self) -> list[ValidationResult]:
        return [r for r in self.results if r.status == ValidationStatus.PASS]

    @property
    def failed_checks(self) -> list[ValidationResult]:
        return [r for r in self.results if r.status == ValidationStatus.FAIL]

    @property
    def unknown_checks(self) -> list[ValidationResult]:
        return [r for r in self.results if r.status == ValidationStatus.UNKNOWN]


# Type alias for downstream investigation workflows
InvestigationOutcome = ValidationOutcome
