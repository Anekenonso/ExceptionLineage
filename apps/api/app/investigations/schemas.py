from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from app.agent.models import AgentMetrics
from app.investigations.trace import InvestigationEvidenceTrace
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
    is_temporary: bool = Field(
        default=False, description="Flag indicating if investigation was run in isolated temporary mode"
    )
    trace: InvestigationEvidenceTrace | None = Field(
        default=None, description="Auditable machine-readable evidence trace"
    )

    @classmethod
    def from_investigation(
        cls,
        inv: Investigation,
        events: list[InvestigationEvent] | None = None,
        agent_events: list[InvestigationEvent] | None = None,
        lineage: dict[str, Any] | None = None,
        is_temporary: bool = False,
        trace: InvestigationEvidenceTrace | None = None,
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
            is_temporary=is_temporary,
            trace=trace,
        )


# =============================================================================
# Test Your Own Case (Temporary Isolated JSON Case Testing) Schemas
# =============================================================================

class TestCaseMeta(BaseModel):
    """Metadata describing the external test case."""
    __test__ = False
    title: str | None = Field(default=None, description="Optional title for test scenario")
    description: str | None = Field(default=None, description="Optional scenario description")


class TestCaseInvoice(BaseModel):
    """Core transaction invoice under test."""
    __test__ = False
    id: str = Field(..., description="Unique invoice identifier (e.g. INV-EXT-001)")
    customer_id: str = Field(..., description="Billed customer identifier")
    contract_id: str | None = Field(default=None, description="Governing contract identifier")
    exception_id: str | None = Field(default=None, description="Associated transaction exception identifier")
    product_id: str | None = Field(default=None, description="Product / service SKU identifier")
    amount: str = Field(..., description="Invoice amount as decimal string, e.g. '10200.00'")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, GBP, etc.)")
    issued_at: str = Field(..., description="ISO 8601 issuance timestamp")
    due_at: str | None = Field(default=None, description="ISO 8601 due timestamp")

    @field_validator("id", "customer_id", "amount", "issued_at")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class TestCaseCustomer(BaseModel):
    """Customer entity representation."""
    __test__ = False
    id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer enterprise legal name")
    external_id: str | None = Field(default="", description="ERP / external customer reference")


class TestCaseContract(BaseModel):
    """Governing master contract representation."""
    __test__ = False
    id: str = Field(..., description="Contract ID")
    customer_id: str | None = Field(default=None, description="Associated customer ID")
    title: str = Field(..., description="Contract title")
    effective_from: str = Field(..., description="ISO 8601 start timestamp")
    effective_until: str | None = Field(default=None, description="ISO 8601 end timestamp")
    status: str = Field(default="ACTIVE", description="Contract status (ACTIVE, DRAFT, EXPIRED)")
    currency: str = Field(default="USD", description="Currency code")


class TestCaseException(BaseModel):
    """Transaction exception or rate variance record."""
    __test__ = False
    id: str = Field(..., description="Exception ID")
    contract_id: str | None = Field(default=None, description="Governing contract ID")
    invoice_id: str | None = Field(default=None, description="Subject invoice ID")
    exception_type: str = Field(default="RATE_VARIANCE", description="Exception category code")
    description: str = Field(default="", description="Detailed discrepancy explanation")
    expected_amount: str | None = Field(default=None, description="Expected baseline monetary amount")
    actual_amount: str | None = Field(default=None, description="Actual billed monetary amount")
    currency: str = Field(default="USD", description="Currency code")


class TestCaseApproval(BaseModel):
    """Approval or sign-off waiver record."""
    __test__ = False
    id: str = Field(..., description="Approval record ID")
    exception_id: str | None = Field(default=None, description="Subject exception ID")
    approver: str = Field(..., description="Approving authority name or email")
    status: str = Field(default="APPROVED", description="Approval status (APPROVED, PENDING, REJECTED)")
    approved_at: str | None = Field(default=None, description="ISO 8601 approval timestamp")
    context: dict[str, Any] | str | None = Field(default=None, description="Audit notes or role info")


class TestCaseAmendment(BaseModel):
    """Contract amendment modifying rates, terms, or scope."""
    __test__ = False
    id: str = Field(..., description="Amendment ID")
    contract_id: str | None = Field(default=None, description="Governing contract ID")
    amendment_number: str = Field(default="", description="Amendment sequence / tracking number")
    title: str = Field(..., description="Amendment title")
    description: str | None = Field(default="", description="Amended terms or rates description")
    effective_from: str = Field(..., description="ISO 8601 start timestamp")
    effective_until: str | None = Field(default=None, description="ISO 8601 end timestamp")


class TestCaseSOW(BaseModel):
    """Statement of Work authorized under a governing contract."""
    __test__ = False
    id: str = Field(..., description="SOW ID")
    contract_id: str | None = Field(default=None, description="Governing contract ID")
    reference: str = Field(default="", description="SOW reference number")
    title: str = Field(..., description="SOW title")
    scope: str | None = Field(default="", description="Deliverable scope description")
    effective_from: str = Field(..., description="ISO 8601 start timestamp")
    effective_until: str | None = Field(default=None, description="ISO 8601 end timestamp")


class TestCaseEvidence(BaseModel):
    """Documentary evidence citation supporting investigation determinations."""
    __test__ = False
    id: str = Field(..., description="Evidence ID (e.g. EV-EXT-001)")
    evidence_type: str = Field(..., description="Evidence type code (e.g. CONTRACT_CLAUSE, AMENDMENT_TERMS)")
    source: str = Field(..., description="Originating system or repository")
    source_id: str = Field(..., description="ID of source document or entity")
    title: str | None = Field(default="", description="Descriptive clause or record title")
    locator: str | None = Field(default="", description="Document locator pointer (e.g. 'Section 2.1')")
    excerpt: str | None = Field(default="", description="Verbatim cited text")
    captured_at: str | None = Field(default=None, description="Capture timestamp")
    effective_from: str | None = Field(default=None, description="Effective from timestamp")
    effective_until: str | None = Field(default=None, description="Effective until timestamp")
    scope: str | None = Field(default=None, description="Product or domain scope")
    confidence: float | None = Field(default=1.0, description="Confidence score bounded to [0.0, 1.0]")


class TestCasePayload(BaseModel):
    """Complete root payload for an independently supplied external test case."""
    __test__ = False
    case_meta: TestCaseMeta | None = Field(default=None, description="Optional case metadata")
    invoice: TestCaseInvoice = Field(..., description="Subject invoice transaction under test")
    customer: TestCaseCustomer | None = Field(default=None, description="Customer entity details")
    contract: TestCaseContract | None = Field(default=None, description="Governing master contract details")
    exception: TestCaseException | None = Field(default=None, description="Flagged transaction exception details")
    approval: TestCaseApproval | None = Field(default=None, description="Associated approval record")
    amendments: list[TestCaseAmendment] = Field(default_factory=list, description="Contract amendments")
    sows: list[TestCaseSOW] = Field(default_factory=list, description="Statements of work")
    evidence: list[TestCaseEvidence] = Field(default_factory=list, description="Evidentiary citations")

    def to_lineage_dict(self) -> dict[str, Any]:
        """Convert validated test case payload into standard LineageRepository dictionary."""
        inv_dict = self.invoice.model_dump()

        # Link foreign keys if omitted in sub-objects
        cust_dict = self.customer.model_dump() if self.customer else None
        contract_dict = self.contract.model_dump() if self.contract else None
        if contract_dict and not contract_dict.get("customer_id"):
            contract_dict["customer_id"] = self.invoice.customer_id
        if not inv_dict.get("contract_id") and contract_dict:
            inv_dict["contract_id"] = contract_dict["id"]

        exc_dict = self.exception.model_dump() if self.exception else None
        if exc_dict:
            if not exc_dict.get("invoice_id"):
                exc_dict["invoice_id"] = self.invoice.id
            if not exc_dict.get("contract_id") and contract_dict:
                exc_dict["contract_id"] = contract_dict["id"]
            if not inv_dict.get("exception_id"):
                inv_dict["exception_id"] = exc_dict["id"]

        app_dict = self.approval.model_dump() if self.approval else None
        if app_dict and exc_dict and not app_dict.get("exception_id"):
            app_dict["exception_id"] = exc_dict["id"]

        amd_list = []
        for a in self.amendments:
            ad = a.model_dump()
            if contract_dict and not ad.get("contract_id"):
                ad["contract_id"] = contract_dict["id"]
            amd_list.append(ad)

        sow_list = []
        for s in self.sows:
            sd = s.model_dump()
            if contract_dict and not sd.get("contract_id"):
                sd["contract_id"] = contract_dict["id"]
            sow_list.append(sd)

        ev_list = [e.model_dump() for e in self.evidence]

        return {
            "invoice": inv_dict,
            "customer": cust_dict,
            "contract": contract_dict,
            "exception": exc_dict,
            "approval": app_dict,
            "amendments": amd_list,
            "sows": sow_list,
            "evidence": ev_list,
        }

