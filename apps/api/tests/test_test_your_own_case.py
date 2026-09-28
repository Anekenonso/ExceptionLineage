"""Unit and integration tests for the 'Test Your Own Case' feature in ExceptionLineage.

Verifies:
1. Correct schema parsing and validation.
2. File format enforcement (strictly .json only).
3. Payload size bounding (max 1MB).
4. Ephemeral in-memory execution through existing investigation engine.
5. Deterministic outcomes: VERIFIED, INSUFFICIENT_EVIDENCE, NOT_VERIFIED, NEEDS_REVIEW.
6. Absolute non-persistence and isolation from canonical benchmark cases and global ledger.
"""

from __future__ import annotations

import io
import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.investigations.router import (
    get_investigation_service,
    reset_default_service,
    seed_canonical_demo_data,
    MAX_TEST_CASE_SIZE_BYTES,
)
from app.investigations.schemas import TestCasePayload
from app.models.enums import InvestigationStatus, ValidationStatus


@pytest.fixture(autouse=True)
def clean_service_env():
    """Ensure clean service state for each test."""
    reset_default_service(None)
    yield
    reset_default_service(None)


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


def build_test_case_payload(
    invoice_amount: str = "10200.00",
    invoice_date: str = "2026-03-15T00:00:00Z",
    contract_start: str = "2026-01-01T00:00:00Z",
    contract_end: str = "2026-12-31T23:59:59Z",
    amendment_start: str = "2026-01-15T00:00:00Z",
    amendment_end: str = "2026-09-30T23:59:59Z",
    approval_status: str = "APPROVED",
    include_approval: bool = True,
    second_amendment: dict | None = None,
) -> dict:
    """Helper to generate well-formed test case dictionaries."""
    data = {
        "case_meta": {
            "title": "Custom Test Case Scenario",
            "description": "Independently supplied transaction-exception test case"
        },
        "invoice": {
            "id": "INV-TEST-9001",
            "customer_id": "CUS-TEST-9001",
            "contract_id": "CTR-TEST-9001",
            "exception_id": "EX-TEST-9001",
            "product_id": "PROD-CLOUD-SUP",
            "amount": invoice_amount,
            "currency": "USD",
            "issued_at": invoice_date,
            "due_at": "2026-04-15T00:00:00Z"
        },
        "customer": {
            "id": "CUS-TEST-9001",
            "name": "Acme Horizon Technologies",
            "external_id": "ERP-9001"
        },
        "contract": {
            "id": "CTR-TEST-9001",
            "customer_id": "CUS-TEST-9001",
            "title": "Enterprise Cloud Services Master Agreement",
            "effective_from": contract_start,
            "effective_until": contract_end,
            "status": "ACTIVE",
            "currency": "USD"
        },
        "exception": {
            "id": "EX-TEST-9001",
            "contract_id": "CTR-TEST-9001",
            "invoice_id": "INV-TEST-9001",
            "exception_type": "RATE_VARIANCE",
            "description": f"Invoice amount ${invoice_amount} differs from base contract fee $12,000.00.",
            "expected_amount": "12000.00",
            "actual_amount": invoice_amount,
            "currency": "USD"
        },
        "amendments": [
            {
                "id": "AMD-TEST-9001",
                "contract_id": "CTR-TEST-9001",
                "amendment_number": "AMD-2026-01",
                "title": "Cloud Support Rate Adjustment Amendment",
                "description": f"Adjusts standard monthly service fee from $12,000.00 to ${invoice_amount} for PROD-CLOUD-SUP.",
                "effective_from": amendment_start,
                "effective_until": amendment_end
            }
        ],
        "sows": [],
        "evidence": [
            {
                "id": "EV-TEST-9001",
                "evidence_type": "CONTRACT_CLAUSE",
                "source": "contracts_repository",
                "source_id": "CTR-TEST-9001",
                "title": "Baseline Cloud Support Clause",
                "locator": "Schedule A, Section 1",
                "excerpt": "Standard enterprise cloud support services shall be invoiced at the baseline rate of $12,000.00 USD monthly.",
                "captured_at": "2026-01-02T10:00:00Z",
                "effective_from": contract_start,
                "effective_until": contract_end,
                "scope": "enterprise_cloud_support",
                "confidence": 1.0
            },
            {
                "id": "EV-TEST-9002",
                "evidence_type": "AMENDMENT_TERMS",
                "source": "contracts_repository",
                "source_id": "AMD-TEST-9001",
                "title": "Volume Discount Terms",
                "locator": "Section 2.1",
                "excerpt": f"The monthly service fee for PROD-CLOUD-SUP is amended to ${invoice_amount} USD effective January 15, 2026 through September 30, 2026.",
                "captured_at": "2026-01-16T09:00:00Z",
                "effective_from": amendment_start,
                "effective_until": amendment_end,
                "scope": "PROD-CLOUD-SUP",
                "confidence": 0.98
            }
        ]
    }

    if include_approval:
        data["approval"] = {
            "id": "APR-TEST-9001",
            "exception_id": "EX-TEST-9001",
            "approver": "sarah.chen@acmeglobal.com",
            "status": approval_status,
            "approved_at": "2026-02-01T14:30:00Z" if approval_status == "APPROVED" else None,
            "context": {
                "role": "VP Commercial Finance",
                "authorization_ref": "AUTH-TEST-9001"
            }
        }
        data["evidence"].append({
            "id": "EV-TEST-9003",
            "evidence_type": "APPROVAL_RECORD",
            "source": "approval_system",
            "source_id": "APR-TEST-9001",
            "title": "Executive Pricing Signoff",
            "locator": "Workflow Audit #99101",
            "excerpt": f"Executive signoff granted by Sarah Chen for rate adjustment ${invoice_amount} under AMD-TEST-9001.",
            "captured_at": "2026-02-01T15:00:00Z",
            "effective_from": "2026-02-01T14:30:00Z",
            "effective_until": None,
            "scope": "commercial_pricing_waiver",
            "confidence": 0.99
        })

    if second_amendment:
        data["amendments"].append(second_amendment)
        data["evidence"].append({
            "id": "EV-TEST-9004",
            "evidence_type": "AMENDMENT_TERMS",
            "source": "contracts_repository",
            "source_id": second_amendment["id"],
            "title": "Conflicting Rate Schedule",
            "locator": "Schedule B",
            "excerpt": f"Rates for regional infrastructure set at ${second_amendment.get('rate', '11500.00')}.",
            "captured_at": "2026-01-16T09:00:00Z",
            "effective_from": second_amendment["effective_from"],
            "effective_until": second_amendment["effective_until"],
            "scope": "regional_infrastructure",
            "confidence": 0.95
        })

    return data


# =============================================================================
# 1. Template Endpoint Tests
# =============================================================================

def test_get_template_endpoint(client: TestClient):
    """GET /api/investigations/test-case/template returns valid structured test case schema."""
    resp = client.get("/api/investigations/test-case/template")
    assert resp.status_code == 200
    data = resp.json()
    assert "invoice" in data
    assert "customer" in data
    assert "contract" in data
    assert "exception" in data
    assert "approval" in data
    assert isinstance(data["amendments"], list)
    assert isinstance(data["evidence"], list)

    # Validate against Pydantic schema
    payload = TestCasePayload.model_validate(data)
    assert payload.invoice.id == "INV-EXT-001"
    lineage = payload.to_lineage_dict()
    assert lineage["invoice"]["id"] == "INV-EXT-001"


# =============================================================================
# 2. File Format & Input Validation Tests
# =============================================================================

def test_reject_non_json_extensions(client: TestClient):
    """Rejects non-JSON formats (.csv, .txt, .pdf, .yaml) with HTTP 400."""
    invalid_files = [
        ("test.csv", b"id,customer,amount\n1,2,3", "text/csv"),
        ("test.txt", b"invoice INV-1001 amount 1000", "text/plain"),
        ("test.pdf", b"%PDF-1.4...", "application/pdf"),
        ("test.yaml", b"invoice:\n  id: INV-1", "application/x-yaml"),
    ]

    for filename, content, mime in invalid_files:
        resp = client.post(
            "/api/investigations/test-case",
            files={"file": (filename, io.BytesIO(content), mime)},
        )
        assert resp.status_code == 400, f"Expected 400 for {filename}, got {resp.status_code}"
        assert "Only .json files are accepted" in resp.json()["detail"]


def test_reject_empty_json_file(client: TestClient):
    """Rejects empty JSON file with HTTP 400."""
    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("case.json", io.BytesIO(b"   "), "application/json")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_reject_malformed_json_syntax(client: TestClient):
    """Rejects invalid JSON syntax with HTTP 400."""
    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("case.json", io.BytesIO(b"{ invalid json : 123 "), "application/json")},
    )
    assert resp.status_code == 400
    assert "Invalid JSON syntax" in resp.json()["detail"]


def test_reject_oversized_file(client: TestClient):
    """Rejects JSON file exceeding 1MB maximum size with HTTP 413."""
    large_content = b'{"data": "' + (b"X" * (MAX_TEST_CASE_SIZE_BYTES + 100)) + b'"}'
    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("large_case.json", io.BytesIO(large_content), "application/json")},
    )
    assert resp.status_code == 413
    assert "maximum allowed size" in resp.json()["detail"].lower()


def test_reject_schema_missing_required_invoice(client: TestClient):
    """Rejects case missing mandatory invoice block with HTTP 422."""
    data = {"customer": {"id": "CUS-1", "name": "Acme Corp"}}
    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("case.json", io.BytesIO(json.dumps(data).encode("utf-8")), "application/json")},
    )
    assert resp.status_code == 422
    assert "validation failed" in resp.json()["detail"].lower()


# =============================================================================
# 3. Deterministic Pipeline Execution Tests
# =============================================================================

def test_upload_valid_case_verified(client: TestClient):
    """Independently defined case with valid amendment & approval achieves VERIFIED."""
    payload = build_test_case_payload(
        invoice_amount="10200.00",
        approval_status="APPROVED",
    )
    file_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("verified_case.json", io.BytesIO(file_bytes), "application/json")},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "VERIFIED"
    assert data["is_temporary"] is True
    assert data["invoice_id"] == "INV-TEST-9001"
    assert data["customer_id"] == "CUS-TEST-9001"
    assert data["amount"] == "10200.00"

    # Deterministic checks
    checks = {c["check_name"]: c["status"] for c in data["validation_results"]}
    assert checks["customer_governing_contract"] == "PASS"
    assert checks["contract_applicability"] == "PASS"
    assert checks["applicable_amendment"] == "PASS"
    assert checks["amendment_effectiveness"] == "PASS"
    assert checks["amendment_scope_match"] == "PASS"
    assert checks["approval_authorization"] == "PASS"
    assert checks["authorized_amount_match"] == "PASS"

    # Evidence citations
    assert len(data["cited_evidence_ids"]) >= 2
    assert "EV-TEST-9001" in data["cited_evidence_ids"]

    # Trace generated
    assert data["trace"] is not None
    assert data["trace"]["investigation_id"] == data["investigation_id"]
    assert len(data["trace"]["events"]) > 0


def test_upload_missing_approval_insufficient_evidence(client: TestClient):
    """Case with rate variance lacking required executive signoff achieves INSUFFICIENT_EVIDENCE."""
    payload = build_test_case_payload(
        invoice_amount="10500.00",
        include_approval=False,
    )
    file_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("missing_approval_case.json", io.BytesIO(file_bytes), "application/json")},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert data["is_temporary"] is True
    checks = {c["check_name"]: c["status"] for c in data["validation_results"]}
    assert checks["approval_authorization"] == "UNKNOWN"


def test_upload_expired_amendment_not_verified(client: TestClient):
    """Case where amendment expired prior to invoice issuance achieves NOT_VERIFIED."""
    payload = build_test_case_payload(
        invoice_amount="9500.00",
        invoice_date="2026-04-15T00:00:00Z",
        amendment_start="2025-01-01T00:00:00Z",
        amendment_end="2025-12-31T23:59:59Z",  # Expired in CY2025
    )
    file_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("expired_amendment_case.json", io.BytesIO(file_bytes), "application/json")},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "NOT_VERIFIED"
    assert data["is_temporary"] is True
    checks = {c["check_name"]: c["status"] for c in data["validation_results"]}
    assert checks["amendment_effectiveness"] == "FAIL"


def test_upload_conflicting_authority_needs_review(client: TestClient):
    """Case with pending approval escalation or conflicting terms achieves NEEDS_REVIEW."""
    payload = build_test_case_payload(
        invoice_amount="11000.00",
        approval_status="PENDING",
    )
    file_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("conflicting_case.json", io.BytesIO(file_bytes), "application/json")},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "NEEDS_REVIEW"
    assert data["is_temporary"] is True


# =============================================================================
# 4. Strict Isolation & Zero Persistence Invariants
# =============================================================================

def test_strict_isolation_and_zero_persistence(client: TestClient):
    """Verify that uploaded cases leave zero trace in persistent stores or canonical ledger."""
    # 1. Capture baseline investigations list
    init_resp = client.get("/api/investigations")
    assert init_resp.status_code == 200
    init_cases = init_resp.json()
    init_invoices = {c["invoice_id"] for c in init_cases}

    # 2. Upload and execute test case
    payload = build_test_case_payload(invoice_amount="10200.00")
    file_bytes = json.dumps(payload).encode("utf-8")

    upload_resp = client.post(
        "/api/investigations/test-case",
        files={"file": ("isolated_test.json", io.BytesIO(file_bytes), "application/json")},
    )
    assert upload_resp.status_code == 200
    temp_inv_id = upload_resp.json()["investigation_id"]

    # 3. Verify ledger is 100% UNCHANGED
    post_resp = client.get("/api/investigations")
    assert post_resp.status_code == 200
    post_cases = post_resp.json()
    post_invoices = {c["invoice_id"] for c in post_cases}

    assert post_invoices == init_invoices
    assert "INV-TEST-9001" not in post_invoices

    # 4. Verify querying by temporary ID returns 404 (not persisted)
    get_resp = client.get(f"/api/investigations/{temp_inv_id}")
    assert get_resp.status_code == 404

    # 5. Verify the 8 canonical benchmark cases remain intact
    for c_id in ["INV-1001", "INV-1002", "INV-1003", "INV-1004", "INV-1005", "INV-1006", "INV-1007", "INV-1008"]:
        assert c_id in post_invoices
