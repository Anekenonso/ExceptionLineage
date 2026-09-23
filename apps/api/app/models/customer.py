from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty


class Customer(BaseModel):
    """Represents an enterprise customer with a stable identifier."""

    id: str = Field(..., description="Stable unique identifier for the customer")
    name: str = Field(..., description="Enterprise customer name")
    external_id: str | None = Field(
        default=None, description="Optional external/reference identifier"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Timestamp of customer record creation (UTC)"
    )

    @field_validator("id", "name", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("created_at")
    @classmethod
    def check_tz_aware(cls, value: datetime) -> datetime:
        res = ensure_timezone_aware(value)
        assert res is not None
        return res
