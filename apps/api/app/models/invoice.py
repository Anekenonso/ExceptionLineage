from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.common import (
    ensure_timezone_aware,
    utc_now,
    validate_date_range,
    validate_non_empty,
)


class Invoice(BaseModel):
    """Represents an enterprise transaction / invoice being investigated.

    Money values MUST use Decimal rather than floating-point numbers to preserve
    exact monetary precision without rounding distortion.
    """

    id: str = Field(..., description="Unique invoice identifier / number")
    customer_id: str = Field(..., description="ID of the billed enterprise customer")
    contract_id: str | None = Field(
        default=None, description="Optional governing contract ID"
    )
    exception_id: str | None = Field(
        default=None, description="Optional associated exception ID"
    )
    product_id: str | None = Field(
        default=None, description="Optional product or service identifier"
    )
    amount: Decimal = Field(
        ..., description="Exact monetary total for the invoice as a Decimal"
    )
    currency: str = Field(
        default="USD", description="Currency code (e.g. USD, EUR, GBP)"
    )
    issued_at: datetime = Field(..., description="Timestamp when invoice was issued (UTC)")
    due_at: datetime | None = Field(
        default=None, description="Timestamp when invoice payment is due (UTC)"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Invoice record creation timestamp (UTC)"
    )

    @field_validator("id", "customer_id", "currency", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("issued_at", "due_at", "created_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)

    @model_validator(mode="after")
    def check_dates(self) -> "Invoice":
        validate_date_range(self.issued_at, self.due_at)
        return self
