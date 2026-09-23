from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.models import (
    Amendment,
    Approval,
    ApprovalStatus,
    Contract,
    ContractStatus,
    Customer,
    Evidence,
    Exception as ExceptionModel,
    Investigation,
    InvestigationEvent,
    InvestigationEventType,
    InvestigationStatus,
    Invoice,
    SOW,
    TransactionException,
    ValidationResult,
    ValidationStatus,
)


# Helper fixtures
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ==============================================================================
# 1. Valid Construction Tests
# ==============================================================================


def test_customer_valid_construction():
    customer = Customer(
        id="cust-001",
        name="Acme Corporation",
        external_id="EXT-ACM-99",
    )
    assert customer.id == "cust-001"
    assert customer.name == "Acme Corporation"
    assert customer.external_id == "EXT-ACM-99"
    assert customer.created_at.tzinfo is not None


def test_contract_valid_construction():
    t_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t_end = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    contract = Contract(
        id="ctr-001",
        customer_id="cust-001",
        title="Master Services Agreement",
        effective_from=t_start,
        effective_until=t_end,
        status=ContractStatus.ACTIVE,
        currency="USD",
    )
    assert contract.id == "ctr-001"
    assert contract.customer_id == "cust-001"
    assert contract.status == ContractStatus.ACTIVE
    assert contract.currency == "USD"


def test_amendment_valid_construction():
    t_start = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    amd = Amendment(
        id="amd-001",
        contract_id="ctr-001",
        amendment_number="AMD-1",
        title="Rate Adjustment 2026",
        description="Increased consulting day rate by 5%",
        effective_from=t_start,
    )
    assert amd.id == "amd-001"
    assert amd.contract_id == "ctr-001"
    assert amd.amendment_number == "AMD-1"
    assert amd.effective_until is None


def test_sow_valid_construction():
    t_start = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    sow = SOW(
        id="sow-001",
        contract_id="ctr-001",
        reference="SOW-Q1-2026",
        title="Cloud Architecture Assessment",
        scope="Architecture review and risk analysis",
        effective_from=t_start,
    )
    assert sow.id == "sow-001"
    assert sow.contract_id == "ctr-001"
    assert sow.reference == "SOW-Q1-2026"


def test_exception_valid_construction():
    # Verify both Exception and TransactionException alias
    exc = ExceptionModel(
        id="exc-001",
        contract_id="ctr-001",
        invoice_id="inv-001",
        exception_type="RATE_DISCREPANCY",
        description="Billed rate exceeds agreed maximum",
        expected_amount=Decimal("10000.00"),
        actual_amount=Decimal("10200.00"),
        currency="USD",
    )
    assert exc.id == "exc-001"
    assert exc.contract_id == "ctr-001"
    assert exc.invoice_id == "inv-001"
    assert exc.expected_amount == Decimal("10000.00")
    assert exc.actual_amount == Decimal("10200.00")
    assert TransactionException is ExceptionModel


def test_approval_valid_construction():
    appr = Approval(
        id="appr-001",
        exception_id="exc-001",
        approver="vp_finance@acme.com",
        status=ApprovalStatus.APPROVED,
        approved_at=now_utc(),
        context={"threshold": 5000, "override_reason": "Executive signoff"},
    )
    assert appr.id == "appr-001"
    assert appr.exception_id == "exc-001"
    assert appr.status == ApprovalStatus.APPROVED


def test_invoice_valid_construction():
    t_issued = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    t_due = datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
    inv = Invoice(
        id="inv-001",
        customer_id="cust-001",
        contract_id="ctr-001",
        exception_id="exc-001",
        product_id="prod-cloud-sec",
        amount=Decimal("10200.00"),
        currency="USD",
        issued_at=t_issued,
        due_at=t_due,
    )
    assert inv.id == "inv-001"
    assert inv.customer_id == "cust-001"
    assert inv.amount == Decimal("10200.00")


def test_evidence_valid_construction():
    t_eff = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    ev = Evidence(
        id="ev-001",
        evidence_type="CONTRACT_CLAUSE",
        source="contracts_repository",
        source_id="ctr-001",
        title="Overtime Fee Clause",
        locator="Section 4.3, paragraph 2",
        excerpt="Overtime hours must be pre-approved by the VP of Engineering.",
        effective_from=t_eff,
        scope="engineering_services",
        confidence=0.95,
    )
    assert ev.id == "ev-001"
    assert ev.confidence == 0.95
    assert ev.source == "contracts_repository"


def test_investigation_valid_construction():
    invg = Investigation(
        id="invg-001",
        invoice_id="inv-001",
        exception_id="exc-001",
        status=InvestigationStatus.INVESTIGATING,
        summary="Investigating $200 rate variance against master agreement",
    )
    assert invg.id == "invg-001"
    assert invg.invoice_id == "inv-001"
    assert invg.status == InvestigationStatus.INVESTIGATING


def test_investigation_event_valid_construction():
    ev = InvestigationEvent(
        id="ev-evt-001",
        investigation_id="invg-001",
        event_type=InvestigationEventType.EVIDENCE_FOUND,
        message="Located amendment AMD-1 modifying rate card",
        metadata={"amendment_id": "amd-001", "confidence": 0.98},
    )
    assert ev.id == "ev-evt-001"
    assert ev.investigation_id == "invg-001"
    assert ev.event_type == InvestigationEventType.EVIDENCE_FOUND


def test_validation_result_valid_construction():
    vr = ValidationResult(
        check_name="approval_authorization_check",
        status=ValidationStatus.PASS,
        message="Valid VP Finance approval record identified",
        evidence_ids=["ev-001"],
        is_required=True,
    )
    assert vr.check_name == "approval_authorization_check"
    assert vr.status == ValidationStatus.PASS
    assert vr.evidence_ids == ["ev-001"]
    assert vr.is_required is True


# ==============================================================================
# 2. Relationship Identifier Validation Tests
# ==============================================================================


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_contract_rejects_empty_customer_id(invalid_id):
    with pytest.raises(ValidationError):
        Contract(
            id="ctr-001",
            customer_id=invalid_id,
            title="Title",
            effective_from=now_utc(),
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_amendment_rejects_empty_contract_id(invalid_id):
    with pytest.raises(ValidationError):
        Amendment(
            id="amd-001",
            contract_id=invalid_id,
            amendment_number="AMD-1",
            title="Title",
            effective_from=now_utc(),
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_sow_rejects_empty_contract_id(invalid_id):
    with pytest.raises(ValidationError):
        SOW(
            id="sow-001",
            contract_id=invalid_id,
            reference="REF-1",
            title="Title",
            effective_from=now_utc(),
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_exception_rejects_empty_contract_id(invalid_id):
    with pytest.raises(ValidationError):
        ExceptionModel(
            id="exc-001",
            contract_id=invalid_id,
            exception_type="TYPE",
            description="Desc",
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_approval_rejects_empty_exception_id(invalid_id):
    with pytest.raises(ValidationError):
        Approval(
            id="appr-001",
            exception_id=invalid_id,
            approver="alice@acme.com",
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_invoice_rejects_empty_customer_id(invalid_id):
    with pytest.raises(ValidationError):
        Invoice(
            id="inv-001",
            customer_id=invalid_id,
            amount=Decimal("100.00"),
            currency="USD",
            issued_at=now_utc(),
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_investigation_rejects_empty_invoice_id(invalid_id):
    with pytest.raises(ValidationError):
        Investigation(
            id="invg-001",
            invoice_id=invalid_id,
        )


@pytest.mark.parametrize(
    "invalid_id",
    ["", "   "],
)
def test_investigation_event_rejects_empty_investigation_id(invalid_id):
    with pytest.raises(ValidationError):
        InvestigationEvent(
            id="evt-001",
            investigation_id=invalid_id,
            event_type="TYPE",
            message="Msg",
        )


# ==============================================================================
# 3. Money Precision Tests (Exact Decimal Representation)
# ==============================================================================


def test_money_preserves_exact_decimal_representation():
    exact_amount = Decimal("10200.00")
    inv = Invoice(
        id="inv-001",
        customer_id="cust-001",
        amount=exact_amount,
        currency="USD",
        issued_at=now_utc(),
    )
    assert inv.amount == Decimal("10200.00")
    assert str(inv.amount) == "10200.00"
    # Ensure float coercion did not happen
    assert isinstance(inv.amount, Decimal)


def test_exception_amounts_preserve_exact_decimals():
    exc = ExceptionModel(
        id="exc-001",
        contract_id="ctr-001",
        exception_type="RATE_CHECK",
        description="Amount discrepancy",
        expected_amount=Decimal("10000.00"),
        actual_amount=Decimal("10200.00"),
    )
    assert exc.expected_amount == Decimal("10000.00")
    assert exc.actual_amount == Decimal("10200.00")
    assert isinstance(exc.expected_amount, Decimal)
    assert isinstance(exc.actual_amount, Decimal)


# ==============================================================================
# 4. Date Range Validation Tests
# ==============================================================================


def test_contract_date_range_validation():
    t_early = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Valid: effective_until >= effective_from
    c_valid = Contract(
        id="ctr-001",
        customer_id="cust-001",
        title="Title",
        effective_from=t_early,
        effective_until=t_late,
    )
    assert c_valid.effective_until == t_late

    # Valid: effective_until == effective_from (same instant)
    c_same = Contract(
        id="ctr-002",
        customer_id="cust-001",
        title="Title",
        effective_from=t_early,
        effective_until=t_early,
    )
    assert c_same.effective_until == t_early

    # Invalid: effective_from > effective_until
    with pytest.raises(ValidationError) as exc_info:
        Contract(
            id="ctr-003",
            customer_id="cust-001",
            title="Title",
            effective_from=t_late,
            effective_until=t_early,
        )
    assert "effective_until" in str(exc_info.value)


def test_amendment_date_range_validation():
    t_early = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        Amendment(
            id="amd-001",
            contract_id="ctr-001",
            amendment_number="AMD-1",
            title="Title",
            effective_from=t_late,
            effective_until=t_early,
        )


def test_sow_date_range_validation():
    t_early = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        SOW(
            id="sow-001",
            contract_id="ctr-001",
            reference="REF-1",
            title="Title",
            effective_from=t_late,
            effective_until=t_early,
        )


def test_evidence_date_range_validation():
    t_early = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        Evidence(
            id="ev-001",
            evidence_type="CLAUSE",
            source="src",
            source_id="src-001",
            effective_from=t_late,
            effective_until=t_early,
        )


def test_invoice_due_date_validation():
    t_issued = datetime(2026, 5, 15, 0, 0, 0, tzinfo=timezone.utc)
    t_due_prior = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        Invoice(
            id="inv-001",
            customer_id="cust-001",
            amount=Decimal("500.00"),
            currency="USD",
            issued_at=t_issued,
            due_at=t_due_prior,
        )


# ==============================================================================
# 5. Confidence Bounds Validation Tests
# ==============================================================================


@pytest.mark.parametrize("valid_conf", [0.0, 0.5, 1.0, None])
def test_evidence_confidence_valid(valid_conf):
    ev = Evidence(
        id="ev-001",
        evidence_type="CLAUSE",
        source="src",
        source_id="src-001",
        confidence=valid_conf,
    )
    assert ev.confidence == valid_conf


@pytest.mark.parametrize("invalid_conf", [-0.01, -1.0, 1.01, 2.0, 100.0])
def test_evidence_confidence_invalid(invalid_conf):
    with pytest.raises(ValidationError) as exc_info:
        Evidence(
            id="ev-001",
            evidence_type="CLAUSE",
            source="src",
            source_id="src-001",
            confidence=invalid_conf,
        )
    assert "Confidence must be between 0.0 and 1.0" in str(exc_info.value)


# ==============================================================================
# 6. Timezone Awareness Tests
# ==============================================================================


def test_naive_datetime_is_rejected():
    naive_dt = datetime(2026, 1, 1, 12, 0, 0)  # No tzinfo
    with pytest.raises(ValidationError) as exc_info:
        Customer(id="c-1", name="Acme", created_at=naive_dt)
    assert "timezone-aware" in str(exc_info.value)


# ==============================================================================
# 7. Validation Status & UNKNOWN Semantics Tests
# ==============================================================================


def test_validation_status_distinct_and_valid():
    # Verify all 3 statuses can be instantiated
    v_pass = ValidationResult(
        check_name="c1", status=ValidationStatus.PASS, message="ok"
    )
    v_fail = ValidationResult(
        check_name="c2", status=ValidationStatus.FAIL, message="failed"
    )
    v_unknown = ValidationResult(
        check_name="c3", status=ValidationStatus.UNKNOWN, message="unknown data"
    )

    assert v_pass.status == ValidationStatus.PASS
    assert v_fail.status == ValidationStatus.FAIL
    assert v_unknown.status == ValidationStatus.UNKNOWN

    # Values must be distinct
    assert v_unknown.status != v_pass.status
    assert v_unknown.status != v_fail.status
    assert v_pass.status != v_fail.status


def test_unknown_semantics_not_coerced():
    # UNKNOWN must remain UNKNOWN through JSON serialization/deserialization
    res = ValidationResult(
        check_name="amount_rate_check",
        status=ValidationStatus.UNKNOWN,
        message="Invoice amount requires amendment terms which are unavailable",
        evidence_ids=[],
    )
    serialized = res.model_dump()
    assert serialized["status"] == "UNKNOWN"
    assert serialized["status"] != "PASS"
    assert serialized["status"] != "FAIL"

    reconstructed = ValidationResult.model_validate(serialized)
    assert reconstructed.status == ValidationStatus.UNKNOWN
    assert reconstructed.status is not ValidationStatus.PASS
    assert reconstructed.status is not ValidationStatus.FAIL


# ==============================================================================
# 8. Investigation Status Lifecycle Coverage Tests
# ==============================================================================


@pytest.mark.parametrize(
    "status",
    [
        # Active states
        InvestigationStatus.QUEUED,
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.VALIDATING,
        # Terminal states
        InvestigationStatus.VERIFIED,
        InvestigationStatus.NOT_VERIFIED,
        InvestigationStatus.INSUFFICIENT_EVIDENCE,
        InvestigationStatus.NEEDS_REVIEW,
        InvestigationStatus.FAILED,
    ],
)
def test_all_investigation_statuses_accepted(status):
    invg = Investigation(
        id="invg-status-test",
        invoice_id="inv-001",
        status=status,
    )
    assert invg.status == status
    assert invg.status.value == status.value
