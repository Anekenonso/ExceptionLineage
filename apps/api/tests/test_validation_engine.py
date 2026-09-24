"""Unit tests for the ValidationEngine execution and outcome determination."""

from decimal import Decimal
import pytest

from app.models.enums import InvestigationStatus, ValidationStatus
from app.models.validation import ValidationResult
from app.validation.context import InvestigationContext
from app.validation.engine import ValidationEngine
from app.validation.rules import BaseValidationRule


class MockRulePass(BaseValidationRule):
    @property
    def name(self) -> str:
        return "mock_pass"

    @property
    def description(self) -> str:
        return "Always passes"

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.PASS,
            message="Check passed",
            evidence_ids=["EV-100"],
        )


class MockRuleFail(BaseValidationRule):
    @property
    def name(self) -> str:
        return "mock_fail"

    @property
    def description(self) -> str:
        return "Always fails"

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message="Check failed",
            evidence_ids=["EV-200"],
        )


class MockRuleUnknown(BaseValidationRule):
    @property
    def name(self) -> str:
        return "mock_unknown"

    @property
    def description(self) -> str:
        return "Always returns unknown"

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.UNKNOWN,
            message="Missing data",
            evidence_ids=[],
        )


@pytest.fixture
def sample_context() -> InvestigationContext:
    return InvestigationContext(
        invoice={
            "id": "INV-1001",
            "customer_id": "CUS-001",
            "amount": "1000.00",
            "currency": "USD",
            "issued_at": "2026-01-01T00:00:00Z",
        },
        contract={"id": "CTR-001", "customer_id": "CUS-001", "status": "ACTIVE"},
    )


def test_engine_verified_when_all_pass(sample_context) -> None:
    engine = ValidationEngine(rules=[MockRulePass()])
    outcome = engine.validate(sample_context)

    assert outcome.status == InvestigationStatus.VERIFIED
    assert outcome.is_verified
    assert len(outcome.passed_checks) == 1
    assert len(outcome.failed_checks) == 0
    assert outcome.cited_evidence_ids == ["EV-100"]


def test_engine_not_verified_when_rule_fails(sample_context) -> None:
    engine = ValidationEngine(rules=[MockRulePass(), MockRuleFail()])
    outcome = engine.validate(sample_context)

    assert outcome.status == InvestigationStatus.NOT_VERIFIED
    assert not outcome.is_verified
    assert len(outcome.failed_checks) == 1
    assert outcome.failure_reason is not None
    assert "mock_fail: Check failed" in outcome.failure_reason
    assert outcome.cited_evidence_ids == ["EV-100", "EV-200"]


def test_engine_insufficient_evidence_when_unknown(sample_context) -> None:
    engine = ValidationEngine(rules=[MockRulePass(), MockRuleUnknown()])
    outcome = engine.validate(sample_context)

    assert outcome.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert not outcome.is_verified
    assert len(outcome.unknown_checks) == 1
    assert outcome.failure_reason is not None
    assert "mock_unknown: Missing data" in outcome.failure_reason


def test_engine_accepts_raw_dictionary() -> None:
    lineage_dict = {
        "invoice": {
            "id": "INV-9999",
            "customer_id": "CUS-999",
            "amount": "5000.00",
            "currency": "USD",
            "issued_at": "2026-01-01T00:00:00Z",
        },
        "customer": {"id": "CUS-999"},
        "contract": None,
    }
    engine = ValidationEngine(rules=[MockRulePass()])
    outcome = engine.validate(lineage_dict)
    assert outcome.status == InvestigationStatus.VERIFIED


def test_engine_rejects_invalid_input_type() -> None:
    engine = ValidationEngine()
    with pytest.raises(TypeError, match="Expected InvestigationContext or dict"):
        engine.validate("invalid string")  # type: ignore
