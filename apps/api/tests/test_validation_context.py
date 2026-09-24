"""Tests for InvestigationContext normalization and helper accessors."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.validation.context import (
    InvestigationContext,
    extract_dollar_amounts,
    parse_datetime,
    parse_decimal,
)


def test_parse_decimal_variants() -> None:
    assert parse_decimal("10200.00") == Decimal("10200.00")
    assert parse_decimal("$10,200.00") == Decimal("10200.00")
    assert parse_decimal(10200) == Decimal("10200")
    assert parse_decimal(10200.5) == Decimal("10200.5")
    assert parse_decimal(None) is None
    assert parse_decimal("") is None


def test_parse_datetime_variants() -> None:
    dt1 = parse_datetime("2026-03-15T00:00:00Z")
    assert dt1 is not None
    assert dt1.tzinfo == timezone.utc
    assert dt1.year == 2026
    assert dt1.month == 3
    assert dt1.day == 15

    dt2 = parse_datetime(datetime(2026, 3, 15, tzinfo=timezone.utc))
    assert dt2 == dt1

    # Naive gets converted to UTC
    dt3 = parse_datetime(datetime(2026, 3, 15))
    assert dt3 is not None
    assert dt3.tzinfo == timezone.utc

    assert parse_datetime(None) is None
    assert parse_datetime("") is None


def test_extract_dollar_amounts() -> None:
    text = "The monthly fee is adjusted from $12,000.00 to $10,200.00 USD."
    amounts = extract_dollar_amounts(text)
    assert amounts == [Decimal("12000.00"), Decimal("10200.00")]

    assert extract_dollar_amounts(None) == []
    assert extract_dollar_amounts("No money mentioned here.") == []


def test_investigation_context_from_lineage() -> None:
    lineage = {
        "invoice": {
            "id": "INV-1001",
            "customer_id": "CUS-001",
            "contract_id": "CTR-001",
            "product_id": "PROD-CLOUD-SUP",
            "amount": "10200.00",
            "currency": "USD",
            "issued_at": "2026-03-15T00:00:00Z",
        },
        "customer": {"id": "CUS-001", "name": "Acme Global"},
        "contract": {
            "id": "CTR-001",
            "customer_id": "CUS-001",
            "status": "ACTIVE",
            "effective_from": "2026-01-01T00:00:00Z",
            "effective_until": "2026-12-31T23:59:59Z",
        },
        "exception": {
            "id": "EX-001",
            "expected_amount": "12000.00",
            "actual_amount": "10200.00",
        },
        "approval": {
            "id": "APR-001",
            "status": "APPROVED",
            "approver": "sarah.chen@acmeglobal.com",
        },
        "amendments": [
            {
                "id": "AMD-001",
                "title": "Tier-1 Volume Discount",
                "description": "Adjusts fee from $12,000.00 to $10,200.00 for Tier-1 support.",
                "effective_from": "2026-01-15T00:00:00Z",
                "effective_until": "2026-09-30T23:59:59Z",
            }
        ],
        "sows": [],
        "evidence": [
            {
                "id": "EV-001",
                "source_id": "CTR-001",
                "excerpt": "Standard enterprise cloud support services shall be invoiced at the baseline rate of $12,000.00 USD monthly.",
            },
            {
                "id": "EV-002",
                "source_id": "AMD-001",
                "scope": "PROD-CLOUD-SUP",
                "excerpt": "The monthly service fee for Tier-1 Cloud Support is amended to $10,200.00 USD.",
            },
        ],
    }

    ctx = InvestigationContext.from_lineage(lineage)
    assert ctx.invoice_id == "INV-1001"
    assert ctx.invoice_amount == Decimal("10200.00")
    assert ctx.has_contract
    assert ctx.contract_id == "CTR-001"
    assert ctx.contract_baseline_rate == Decimal("12000.00")
    assert ctx.get_amendment_rate("AMD-001") == Decimal("10200.00")
    assert ctx.get_amendment_scope("AMD-001") == "PROD-CLOUD-SUP"
    assert len(ctx.get_candidate_amendments()) == 1
    assert ctx.get_candidate_amendments()[0]["id"] == "AMD-001"


def test_investigation_context_missing_invoice_raises() -> None:
    with pytest.raises(ValueError, match="Lineage must contain an 'invoice' node"):
        InvestigationContext.from_lineage({})
