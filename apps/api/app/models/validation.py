from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty
from app.models.enums import ValidationStatus


class ValidationResult(BaseModel):
    """Represents the discrete outcome of a deterministic validation check.

    Core Principle:
    UNKNOWN is a legitimate result representing indeterminate or missing evidence.
    UNKNOWN must never be silently converted into PASS or FAIL.
    """

    check_name: str = Field(
        ..., description="Identifier or name of the deterministic validation check executed"
    )
    status: ValidationStatus = Field(
        ...,
        description="Outcome of the check: PASS (verified), FAIL (rule violated), or UNKNOWN (insufficient evidence)",
    )
    message: str | None = Field(
        default=None,
        description="Explanation, failure rationale, or description of missing data",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="IDs of evidence records that substantiate this validation check outcome",
    )
    timestamp: datetime = Field(
        default_factory=utc_now,
        description="Timestamp when the check was evaluated (UTC)",
    )
    is_required: bool = Field(
        default=True,
        description="Flag indicating if passing this check is mandatory for overall verification",
    )

    @field_validator("check_name", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("timestamp")
    @classmethod
    def check_tz_aware(cls, value: datetime) -> datetime:
        res = ensure_timezone_aware(value)
        assert res is not None
        return res
