"""Unit tests for discrete deterministic validation rules."""

from decimal import Decimal
import pytest

from app.models.enums import ValidationStatus
from app.validation.context import InvestigationContext
from app.validation.rules import (
    AmendmentEffectivenessRule,
    AmendmentScopeRule,
    ApplicableAmendmentRule,
    ApprovalAuthorizationRule,
    AuthorizedAmountRule,
    ConflictingAuthorityRule,
    ContractApplicabilityRule,
    CustomerGoverningContractRule,
)


@pytest.fixture
def base_invoice() -> dict:
    return {
        "id": "INV-1001",
        "customer_id": "CUS-001",
        "contract_id": "CTR-001",
        "product_id": "PROD-CLOUD-SUP",
        "amount": "10200.00",
        "currency": "USD",
        "issued_at": "2026-03-15T00:00:00Z",
    }


@pytest.fixture
def base_contract() -> dict:
    return {
        "id": "CTR-001",
        "customer_id": "CUS-001",
        "status": "ACTIVE",
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_until": "2026-12-31T23:59:59Z",
    }


# -----------------------------------------------------------------------------
# 1. CustomerGoverningContractRule
# -----------------------------------------------------------------------------

def test_customer_governing_contract_pass(base_invoice, base_contract) -> None:
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract)
    rule = CustomerGoverningContractRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS
    assert "matches" in res.message


def test_customer_governing_contract_fail_mismatch(base_invoice, base_contract) -> None:
    base_contract["customer_id"] = "CUS-DIFFERENT"
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract)
    rule = CustomerGoverningContractRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "does not match" in res.message


def test_customer_governing_contract_unknown_when_missing_contract(base_invoice) -> None:
    ctx = InvestigationContext(invoice=base_invoice, contract=None)
    rule = CustomerGoverningContractRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.UNKNOWN


# -----------------------------------------------------------------------------
# 2. ContractApplicabilityRule
# -----------------------------------------------------------------------------

def test_contract_applicability_pass(base_invoice, base_contract) -> None:
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract)
    rule = ContractApplicabilityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_contract_applicability_fail_status(base_invoice, base_contract) -> None:
    base_contract["status"] = "EXPIRED"
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract)
    rule = ContractApplicabilityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "expected ACTIVE" in res.message


def test_contract_applicability_fail_issued_outside_window(base_invoice, base_contract) -> None:
    base_invoice["issued_at"] = "2027-05-01T00:00:00Z"
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract)
    rule = ContractApplicabilityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "after contract expiration" in res.message


def test_contract_applicability_unknown_when_missing(base_invoice) -> None:
    ctx = InvestigationContext(invoice=base_invoice, contract=None)
    rule = ContractApplicabilityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.UNKNOWN


# -----------------------------------------------------------------------------
# 3. ConflictingAuthorityRule
# -----------------------------------------------------------------------------

def test_conflicting_authority_pass_when_no_conflicts(base_invoice, base_contract) -> None:
    amendments = [
        {"id": "AMD-001", "description": "Rate $10,200.00"},
    ]
    evidence = [
        {"id": "EV-002", "source_id": "AMD-001", "scope": "PROD-CLOUD-SUP", "excerpt": "$10,200.00 USD"},
    ]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = ConflictingAuthorityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_conflicting_authority_fail_when_competing_schedules(base_invoice, base_contract) -> None:
    base_invoice["product_id"] = "PROD-INFRA-REG"
    amendments = [
        {"id": "AMD-005", "description": "Rate $11,000.00"},
        {"id": "AMD-006", "description": "Rate $11,500.00"},
    ]
    evidence = [
        {"id": "EV-007", "source_id": "AMD-005", "scope": "PROD-INFRA-REG", "excerpt": "rate is fixed at $11,000.00 USD"},
        {"id": "EV-008", "source_id": "AMD-006", "scope": "PROD-INFRA-REG", "excerpt": "rate is established at $11,500.00 USD"},
    ]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = ConflictingAuthorityRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "Conflicting executed amendments" in res.message
    assert "EV-007" in res.evidence_ids
    assert "EV-008" in res.evidence_ids


# -----------------------------------------------------------------------------
# 4. ApplicableAmendmentRule
# -----------------------------------------------------------------------------

def test_applicable_amendment_pass_baseline_conformance(base_invoice, base_contract) -> None:
    base_invoice["amount"] = "12000.00"
    evidence = [{"id": "EV-001", "source_id": "CTR-001", "excerpt": "baseline rate of $12,000.00 USD"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, evidence=evidence)
    rule = ApplicableAmendmentRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS
    assert "matches contract baseline" in res.message


def test_applicable_amendment_fail_overage_without_amendment(base_invoice, base_contract) -> None:
    base_invoice["amount"] = "15000.00"
    evidence = [{"id": "EV-001", "source_id": "CTR-001", "excerpt": "baseline rate of $12,000.00 USD"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, evidence=evidence, amendments=[])
    rule = ApplicableAmendmentRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "no authorizing amendment exists" in res.message


# -----------------------------------------------------------------------------
# 5. AmendmentEffectivenessRule
# -----------------------------------------------------------------------------

def test_amendment_effectiveness_pass(base_invoice, base_contract) -> None:
    amendments = [
        {"id": "AMD-001", "effective_from": "2026-01-15T00:00:00Z", "effective_until": "2026-09-30T23:59:59Z"}
    ]
    evidence = [{"id": "EV-002", "source_id": "AMD-001", "scope": "PROD-CLOUD-SUP", "excerpt": "$10,200.00"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = AmendmentEffectivenessRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_amendment_effectiveness_fail_expired(base_invoice, base_contract) -> None:
    base_invoice["issued_at"] = "2026-04-15T00:00:00Z"
    amendments = [
        {"id": "AMD-003", "effective_from": "2025-01-01T00:00:00Z", "effective_until": "2025-12-31T23:59:59Z"}
    ]
    evidence = [{"id": "EV-005", "source_id": "AMD-003", "scope": "PROD-CLOUD-SUP", "excerpt": "$10,200.00"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = AmendmentEffectivenessRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "expired" in res.message


# -----------------------------------------------------------------------------
# 6. AmendmentScopeRule
# -----------------------------------------------------------------------------

def test_amendment_scope_pass_when_matching(base_invoice, base_contract) -> None:
    amendments = [{"id": "AMD-001"}]
    evidence = [{"id": "EV-002", "source_id": "AMD-001", "scope": "PROD-CLOUD-SUP"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = AmendmentScopeRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_amendment_scope_fail_when_mismatched(base_invoice, base_contract) -> None:
    base_invoice["product_id"] = "PROD-INFRA"
    base_invoice["amount"] = "8000.00"
    amendments = [{"id": "AMD-004", "description": "Rate $8,000.00 strictly for PROD-SEC"}]
    evidence = [{"id": "EV-006", "source_id": "AMD-004", "scope": "PROD-SEC", "excerpt": "$8,000.00 USD for PROD-SEC"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = AmendmentScopeRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "does not apply to billed product 'PROD-INFRA'" in res.message


# -----------------------------------------------------------------------------
# 7. ApprovalAuthorizationRule
# -----------------------------------------------------------------------------

def test_approval_authorization_pass_when_approved(base_invoice, base_contract) -> None:
    approval = {"id": "APR-001", "status": "APPROVED", "approver": "sarah.chen@acmeglobal.com"}
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, approval=approval, exception={"id": "EX-001"})
    rule = ApprovalAuthorizationRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_approval_authorization_unknown_when_missing(base_invoice, base_contract) -> None:
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, approval=None, exception={"id": "EX-002"})
    rule = ApprovalAuthorizationRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.UNKNOWN
    assert "missing" in res.message


def test_approval_authorization_unknown_when_pending(base_invoice, base_contract) -> None:
    approval = {"id": "APR-005", "status": "PENDING", "approver": "marcus.vance@acmeglobal.com"}
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, approval=approval, exception={"id": "EX-005"})
    rule = ApprovalAuthorizationRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.UNKNOWN
    assert "PENDING" in res.message


def test_approval_authorization_fail_when_rejected(base_invoice, base_contract) -> None:
    approval = {"id": "APR-999", "status": "REJECTED", "approver": "audit@acmeglobal.com"}
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, approval=approval, exception={"id": "EX-001"})
    rule = ApprovalAuthorizationRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "REJECTED" in res.message


# -----------------------------------------------------------------------------
# 8. AuthorizedAmountRule
# -----------------------------------------------------------------------------

def test_authorized_amount_pass_matching_amendment(base_invoice, base_contract) -> None:
    amendments = [{"id": "AMD-001"}]
    evidence = [
        {"id": "EV-001", "source_id": "CTR-001", "excerpt": "baseline $12,000.00"},
        {"id": "EV-002", "source_id": "AMD-001", "scope": "PROD-CLOUD-SUP", "excerpt": "rate is amended to $10,200.00"},
    ]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, amendments=amendments, evidence=evidence)
    rule = AuthorizedAmountRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.PASS


def test_authorized_amount_fail_unauthorized_overage(base_invoice, base_contract) -> None:
    base_invoice["amount"] = "15000.00"
    evidence = [{"id": "EV-001", "source_id": "CTR-001", "excerpt": "baseline rate $12,000.00"}]
    ctx = InvestigationContext(invoice=base_invoice, contract=base_contract, evidence=evidence)
    rule = AuthorizedAmountRule()
    res = rule.evaluate(ctx)
    assert res.status == ValidationStatus.FAIL
    assert "does not match any legally authorized contractual or amended rate" in res.message
