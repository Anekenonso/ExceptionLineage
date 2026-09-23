from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.common import (
    ensure_timezone_aware,
    utc_now,
    validate_date_range,
    validate_non_empty,
)
from app.models.enums import ContractStatus


class Contract(BaseModel):
    """Represents the governing master contract for an enterprise customer."""

    id: str = Field(..., description="Unique contract identifier")
    customer_id: str = Field(..., description="ID of the customer this contract belongs to")
    title: str = Field(..., description="Contract title / descriptive name")
    effective_from: datetime = Field(..., description="Effective start date/time (UTC)")
    effective_until: datetime | None = Field(
        default=None, description="Effective end date/time (UTC), if specified"
    )
    status: ContractStatus = Field(
        default=ContractStatus.ACTIVE, description="Lifecycle status of the contract"
    )
    currency: str = Field(
        default="USD", description="Governing currency code (e.g. USD, EUR, GBP)"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Contract record creation timestamp (UTC)"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp (UTC)"
    )

    @field_validator("id", "customer_id", "title", "currency", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("effective_from", "effective_until", "created_at", "updated_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)

    @model_validator(mode="after")
    def check_dates(self) -> "Contract":
        validate_date_range(self.effective_from, self.effective_until)
        return self


class Amendment(BaseModel):
    """Represents an amendment modifying an existing contract."""

    id: str = Field(..., description="Unique amendment identifier")
    contract_id: str = Field(..., description="ID of the contract this amendment modifies")
    amendment_number: str = Field(
        ..., description="Amendment reference / sequence number (e.g. AMD-001)"
    )
    title: str = Field(..., description="Amendment title")
    description: str | None = Field(
        default=None, description="Description of changes or altered scope"
    )
    effective_from: datetime = Field(..., description="Effective start date/time (UTC)")
    effective_until: datetime | None = Field(
        default=None, description="Effective end date/time (UTC), if specified"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Amendment record creation timestamp (UTC)"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp (UTC)"
    )

    @field_validator("id", "contract_id", "amendment_number", "title", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("effective_from", "effective_until", "created_at", "updated_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)

    @model_validator(mode="after")
    def check_dates(self) -> "Amendment":
        validate_date_range(self.effective_from, self.effective_until)
        return self


class SOW(BaseModel):
    """Represents a Statement of Work associated with a governing contract."""

    id: str = Field(..., description="Unique SOW identifier")
    contract_id: str = Field(..., description="ID of the governing contract")
    reference: str = Field(..., description="SOW reference number or code (e.g. SOW-2026-01)")
    title: str = Field(..., description="SOW title")
    scope: str | None = Field(
        default=None, description="Description or structured text of the scope of work"
    )
    effective_from: datetime = Field(..., description="Effective start date/time (UTC)")
    effective_until: datetime | None = Field(
        default=None, description="Effective end date/time (UTC), if specified"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="SOW record creation timestamp (UTC)"
    )
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp (UTC)"
    )

    @field_validator("id", "contract_id", "reference", "title", mode="before")
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        return validate_non_empty(value, info.field_name or "field")

    @field_validator("effective_from", "effective_until", "created_at", "updated_at")
    @classmethod
    def check_tz_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_timezone_aware(value)

    @model_validator(mode="after")
    def check_dates(self) -> "SOW":
        validate_date_range(self.effective_from, self.effective_until)
        return self
