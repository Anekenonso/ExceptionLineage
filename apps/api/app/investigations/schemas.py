"""Pydantic request and response schemas for investigation API endpoints."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.agent.models import AgentMetrics
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
    agent_metrics: AgentMetrics | None = Field(
        default=None,
        description="Execution metrics from the investigation agent loop",
    )
    events: list[InvestigationEvent] | None = Field(
        default=None,
        description="Immutable chronological lifecycle audit events",
    )
    agent_events: list[InvestigationEvent] | None = Field(
        default=None,
        description="Detailed agent action and tool execution audit events",
    )
    customer_id: str | None = Field(
        default=None, description="Enterprise customer identifier if available"
    )
    customer_name: str | None = Field(
        default=None, description="Enterprise customer name if available"
    )
    amount: str | None = Field(
        default=None, description="Invoice amount if available"
    )
    currency: str | None = Field(
        default="USD", description="Currency code for monetary amounts"
    )
    duration_seconds: float | None = Field(
        default=None, description="Investigation execution duration in seconds"
    )
    lineage: dict[str, Any] | None = Field(
        default=None, description="Graph lineage data (customer, contract, amendments, sows, exception, approval, evidence)"
    )

    @classmethod
    def from_investigation(
        cls,
        inv: Investigation,
        events: list[InvestigationEvent] | None = None,
        agent_events: list[InvestigationEvent] | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> InvestigationResponse:
        """Construct an InvestigationResponse from domain Investigation, events, and lineage."""
        from typing import Any
        raw_metrics = inv.agent_metrics
        parsed_metrics = None
        if isinstance(raw_metrics, AgentMetrics):
            parsed_metrics = raw_metrics
        elif isinstance(raw_metrics, dict):
            parsed_metrics = AgentMetrics(**raw_metrics)

        # Extract contextual fields from lineage if available
        customer_id = None
        customer_name = None
        amount = None
        currency = "USD"
        if lineage:
            cust = lineage.get("customer") or {}
            customer_name = cust.get("name")
            customer_id = cust.get("id")
            inv_data = lineage.get("invoice") or {}
            if inv_data.get("amount") is not None:
                amount = str(inv_data.get("amount"))
            currency = inv_data.get("currency") or "USD"

        # Calculate duration
        duration_seconds = None
        if parsed_metrics and parsed_metrics.investigation_duration_ms > 0:
            duration_seconds = round(parsed_metrics.investigation_duration_ms / 1000.0, 3)
        elif inv.updated_at and inv.created_at:
            duration_seconds = round((inv.updated_at - inv.created_at).total_seconds(), 3)

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
            agent_metrics=parsed_metrics,
            events=events,
            agent_events=agent_events,
            customer_id=customer_id,
            customer_name=customer_name,
            amount=amount,
            currency=currency,
            duration_seconds=duration_seconds,
            lineage=lineage,
        )
