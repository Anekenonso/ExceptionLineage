from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field, field_validator

from app.models.common import ensure_timezone_aware, utc_now, validate_non_empty
from app.models.enums import ApprovalStatus


class Exception(BaseModel):
    """Represents an operational / transaction exception.

    Note: The Exception model defines the contract only and does NOT evaluate
    whether the exception is valid. That belongs to deterministic validation.
    """

    id: str = Field(..., description="Unique exception identifier")
    contract_id: str = Field(
        ..., description="ID of the governing contract associated with the exception"
    )
    invoice_id: str | None = Field(
        default=None, description="Optional associated invoice ID"
    )
    exception_type: str = Field(
        ..., description="Operational exception type/code (e.g. RATE_MISMATCH, UNAPPROVED_EXPENSE)"
    )
    description: str = Field(..., description="Human-readable exception details")
    expected_amount: Decimal | None = Field(
        default=None, description="Expected monetary amount as an exact Decimal"
    )
    actual_amount: Decimal | None = Field(
        default=None, description="Actual monetary amount charged as an exact Decimal"
    )
    currency: str = Field(
        default="USD", description="Currency code for monetary amounts"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Timestamp when the exception was recorded (UTC)"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp (UTC)"
    )

    @field_validator("id", "contract_id", "exception_type", "description", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("created_at", "updated_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)


# Alias to avoid shadowing Python's built-in Exception in contexts where desired
TransactionException = Exception


class Approval(BaseModel):
    """Represents an authorization associated with an operational exception."""

    id: str = Field(..., description="Unique approval identifier")
    exception_id: str = Field(
        ..., description="ID of the exception this approval pertains to"
    )
    approver: str = Field(
        ..., description="Name, email, or identifier of the approving entity"
    )
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING, description="Status of the authorization"
    )
    approved_at: datetime | None = Field(
        default=None, description="Timestamp of when approval was granted (UTC)"
    )
    context: dict[str, Any] | str | None = Field(
        default=None, description="Optional scope, rationale, or structured context"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Timestamp of approval record creation (UTC)"
    )

    @field_validator("id", "exception_id", "approver", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("approved_at", "created_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)
