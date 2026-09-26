"""Comprehensive API tests for Stage 16 - First Real Vertical Slice.

Verifies end-to-end investigation execution through the FastAPI boundary:
    HTTP request
        ↓
    FastAPI endpoint (/api/investigations)
        ↓
    InvestigationService
        ↓
    QUEUED
        ↓
    INVESTIGATING
        ↓
    Graph lineage retrieval (LineageRepository abstraction)
        ↓
    InvestigationContext
        ↓
    VALIDATING
        ↓
    Deterministic ValidationEngine
        ↓
    ValidationOutcome
        ↓
    State Machine
        ↓
    Terminal InvestigationStatus
        ↓
    Structured API response
"""

import ast
import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.graph.lineage import (
    InMemoryLineageRepository,
    LineageRepository,
    Neo4jLineageRepository,
)
from app.graph.loader import find_data_dir
from app.investigations.exceptions import GraphRetrievalError
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.router import get_investigation_service
from app.investigations.service import InvestigationService
from app.main import app
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


@pytest.fixture
def mock_lineages() -> dict[str, dict]:
    """Load simulated graph traversal lineages for all seed invoices."""
    return build_mock_seed_graph_lineage()


@pytest.fixture
def test_service(mock_lineages) -> InvestigationService:
    """Provide an isolated InvestigationService using InMemoryLineageRepository."""
    repo = InMemoryInvestigationRepository()
    lineage_repo = InMemoryLineageRepository(mock_lineages)
    return InvestigationService(repository=repo, lineage_repository=lineage_repo)


@pytest.fixture
def client(test_service) -> TestClient:
    """Provide a FastAPI TestClient with the test service dependency injected."""
    app.dependency_overrides[get_investigation_service] = lambda: test_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. First Vertical-Slice Proof Case (CASE-001 / INV-1001)
# ==============================================================================


def test_post_investigations_case_001_verified(client):
    """POST /api/investigations with INV-1001 executes end-to-end to VERIFIED."""
    payload = {
        "invoice_id": "INV-1001",
        "exception_id": "EX-001",
    }
    response = client.post("/api/investigations", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Core attributes
    assert data["investigation_id"].startswith("invg-")
    assert data["invoice_id"] == "INV-1001"
    assert data["exception_id"] == "EX-001"
    assert data["status"] == "VERIFIED"
    assert data["failure_reason"] is None

    # Summary
    assert data["summary"] is not None
    assert "authorized and verified" in data["summary"].lower()

    # Evidence citations
    assert "EV-001" in data["cited_evidence_ids"]
    assert "EV-002" in data["cited_evidence_ids"]
    assert "EV-003" in data["cited_evidence_ids"]

    # Discrete validation results
    assert data["validation_results"] is not None
    assert len(data["validation_results"]) == 8
    assert all(r["status"] == "PASS" for r in data["validation_results"])

    # Lifecycle audit event trail
    events = data["events"]
    assert events is not None
    assert len(events) == 3
    assert events[0]["from_state"] == "QUEUED"
    assert events[0]["to_state"] == "INVESTIGATING"
    assert events[1]["from_state"] == "INVESTIGATING"
    assert events[1]["to_state"] == "VALIDATING"
    assert events[2]["from_state"] == "VALIDATING"
    assert events[2]["to_state"] == "VERIFIED"


# ==============================================================================
# 2. GET Endpoints (Investigation State and Audit Events)
# ==============================================================================


def test_get_investigation_by_id(client):
    """GET /api/investigations/{id} retrieves current investigation state."""
    # Create investigation
    post_res = client.post("/api/investigations", json={"invoice_id": "INV-1001"})
    assert post_res.status_code == 200
    invg_id = post_res.json()["investigation_id"]

    # Retrieve investigation
    get_res = client.get(f"/api/investigations/{invg_id}")
    assert get_res.status_code == 200
    data = get_res.json()

    assert data["investigation_id"] == invg_id
    assert data["invoice_id"] == "INV-1001"
    assert data["status"] == "VERIFIED"
    assert data["created_at"] is not None
    assert len(data["events"]) == 3


def test_get_investigation_events_sequence(client):
    """GET /api/investigations/{id}/events returns the chronological transition sequence."""
    post_res = client.post("/api/investigations", json={"invoice_id": "INV-1001"})
    invg_id = post_res.json()["investigation_id"]

    events_res = client.get(f"/api/investigations/{invg_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()

    assert len(events) == 3
    # Step 1: QUEUED -> INVESTIGATING
    assert events[0]["from_state"] == "QUEUED"
    assert events[0]["to_state"] == "INVESTIGATING"
    # Step 2: INVESTIGATING -> VALIDATING
    assert events[1]["from_state"] == "INVESTIGATING"
    assert events[1]["to_state"] == "VALIDATING"
    # Step 3: VALIDATING -> VERIFIED
    assert events[2]["from_state"] == "VALIDATING"
    assert events[2]["to_state"] == "VERIFIED"


# ==============================================================================
# 3. Input Validation (Section 15)
# ==============================================================================


def test_post_investigations_missing_invoice_id(client):
    """Missing invoice_id returns HTTP 422 Unprocessable Entity."""
    response = client.post("/api/investigations", json={"exception_id": "EX-001"})
    assert response.status_code == 422


def test_post_investigations_empty_invoice_id(client):
    """Empty invoice_id returns HTTP 422 Unprocessable Entity."""
    response = client.post("/api/investigations", json={"invoice_id": ""})
    assert response.status_code == 422


def test_post_investigations_whitespace_invoice_id(client):
    """Whitespace-only invoice_id returns HTTP 422 Unprocessable Entity."""
    response = client.post("/api/investigations", json={"invoice_id": "   "})
    assert response.status_code == 422


def test_post_investigations_malformed_body(client):
    """Malformed non-JSON body returns HTTP 422 Unprocessable Entity."""
    response = client.post(
        "/api/investigations",
        content="not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


# ==============================================================================
# 4. Not-Found Behavior (Section 16)
# ==============================================================================


def test_get_nonexistent_investigation_returns_404(client):
    """GET /api/investigations/non-existent-id returns HTTP 404 with structured error."""
    response = client.get("/api/investigations/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "non-existent-id" in data["detail"]


def test_get_nonexistent_investigation_events_returns_404(client):
    """GET /api/investigations/non-existent-id/events returns HTTP 404 with structured error."""
    response = client.get("/api/investigations/non-existent-id/events")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "non-existent-id" in data["detail"]


# ==============================================================================
# 5. Graph / Infrastructure Failure Path (Sections 12 & 17)
# ==============================================================================


class FailingLineageRepository(LineageRepository):
    """Test double that simulates a database connectivity or query failure."""

    def __init__(self, exception_to_raise: Exception | None = None) -> None:
        self.exception_to_raise = (
            exception_to_raise
            if exception_to_raise is not None
            else ConnectionError("Neo4j database connection refused at bolt://localhost:7687")
        )

    def get_invoice_lineage(self, invoice_id: str) -> dict | None:
        raise self.exception_to_raise


def test_graph_infrastructure_failure_transitions_to_failed():
    """Verify that a Neo4j/graph failure cleanly transitions QUEUED -> INVESTIGATING -> FAILED.

    Crucially:
    - Status must be FAILED, NOT INSUFFICIENT_EVIDENCE.
    - No validation outcome is fabricated.
    - Failure reason is populated.
    - Event history contains exactly 2 transitions.
    """
    failing_lineage_repo = FailingLineageRepository()
    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=failing_lineage_repo,
    )

    app.dependency_overrides[get_investigation_service] = lambda: service
    client = TestClient(app)

    try:
        response = client.post("/api/investigations", json={"invoice_id": "INV-1001"})
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "FAILED"
        assert data["failure_reason"] is not None
        assert "Graph retrieval failed" in data["failure_reason"]
        assert "connection refused" in data["failure_reason"]

        # No validation outcome or citations fabricated
        assert data["validation_results"] is None
        assert data["cited_evidence_ids"] == []

        # Event audit history
        events = data["events"]
        assert len(events) == 2
        assert events[0]["from_state"] == "QUEUED"
        assert events[0]["to_state"] == "INVESTIGATING"
        assert events[1]["from_state"] == "INVESTIGATING"
        assert events[1]["to_state"] == "FAILED"
    finally:
        app.dependency_overrides.clear()


def test_invoice_not_found_in_graph_transitions_to_failed():
    """Verify that requesting an invoice that does not exist in the graph transitions to FAILED."""
    empty_lineage_repo = InMemoryLineageRepository({})
    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=empty_lineage_repo,
    )

    app.dependency_overrides[get_investigation_service] = lambda: service
    client = TestClient(app)

    try:
        response = client.post("/api/investigations", json={"invoice_id": "INV-UNKNOWN-9999"})
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "FAILED"
        assert "not found in knowledge graph" in data["failure_reason"]
        assert len(data["events"]) == 2
        assert data["events"][1]["to_state"] == "FAILED"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 6. All 8 Controlled Cases via HTTP API (Section 13)
# ==============================================================================


def test_api_all_8_benchmark_cases_end_to_end(client):
    """Run all 8 controlled investigation cases through POST /api/investigations.

    Asserts that the full pipeline (API -> Service -> Lineage -> Validation -> State Machine)
    achieves 100% agreement with expected benchmark determinations.
    """
    data_dir = find_data_dir()
    with open(data_dir / "ground_truth" / "ground_truth.json", "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    for gt in ground_truth:
        case_id = gt["case_id"]
        invoice_id = gt["invoice_id"]
        expected_status = gt["expected_status"]
        exception_id = gt.get("exception_id")

        payload = {"invoice_id": invoice_id}
        if exception_id:
            payload["exception_id"] = exception_id

        response = client.post("/api/investigations", json=payload)
        assert response.status_code == 200, f"Case {case_id} failed with HTTP {response.status_code}"
        data = response.json()

        # Check outcome status
        actual_status = data["status"]
        assert actual_status == expected_status, (
            f"Case {case_id} ({invoice_id}) outcome mismatch: "
            f"expected '{expected_status}', got '{actual_status}'"
        )

        # Check events sequence
        events = data["events"]
        assert len(events) == 3
        assert events[0]["from_state"] == "QUEUED"
        assert events[0]["to_state"] == "INVESTIGATING"
        assert events[1]["from_state"] == "INVESTIGATING"
        assert events[1]["to_state"] == "VALIDATING"
        assert events[2]["from_state"] == "VALIDATING"
        assert events[2]["to_state"] == expected_status

        # If verified, verify citations
        if expected_status == "VERIFIED":
            for expected_ev in gt["relevant_evidence_ids"]:
                assert expected_ev in data["cited_evidence_ids"]


# ==============================================================================
# 6b. Investigation List and Lineage Endpoints (Stage 19)
# ==============================================================================


def test_list_investigations_and_lineage_endpoint(client):
    """Verify GET /api/investigations and GET /api/investigations/{id}/lineage."""
    # 1. Initially empty or lists existing
    res_initial = client.get("/api/investigations")
    assert res_initial.status_code == 200
    initial_list = res_initial.json()
    assert isinstance(initial_list, list)

    # 2. Run investigation
    res_post = client.post("/api/investigations", json={"invoice_id": "INV-1001", "exception_id": "EX-001"})
    assert res_post.status_code == 200
    inv_data = res_post.json()
    inv_id = inv_data["investigation_id"]

    # 3. GET /api/investigations lists it
    res_list = client.get("/api/investigations")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) >= 1
    found = next((x for x in items if x["investigation_id"] == inv_id), None)
    assert found is not None
    assert found["invoice_id"] == "INV-1001"
    assert found["customer_name"] == "Acme Global Enterprise Inc."
    assert found["amount"] == "10200.00"

    # 4. GET /api/investigations/{id}/lineage
    res_lineage = client.get(f"/api/investigations/{inv_id}/lineage")
    assert res_lineage.status_code == 200
    lin = res_lineage.json()
    assert "invoice" in lin
    assert "customer" in lin
    assert "contract" in lin
    assert "evidence" in lin


# ==============================================================================
# 7. No Ground-Truth Leakage in API and Service Layer (Section 18)
# ==============================================================================


def test_api_and_service_do_not_import_ground_truth():
    """Verify that app/investigations and app/main do not import ground-truth or test datasets."""
    api_dir = Path(__file__).parent.parent / "app"
    targets = [
        api_dir / "main.py",
        *(api_dir / "investigations").glob("*.py"),
        *(api_dir / "graph").glob("*.py"),
    ]

    forbidden_patterns = [
        r"data\.ground_truth",
        r"ground_truth",
        r"test_.*",
        r"data/cases",
        r"data/seed",
    ]

    for py_file in targets:
        # Exclude verifier.py which is the designated benchmark verifier module
        if py_file.name == "verifier.py":
            continue

        content = py_file.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(py_file))

        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for pattern in forbidden_patterns:
                        assert not re.search(pattern, alias.name), (
                            f"Illegal import '{alias.name}' matching '{pattern}' in {py_file.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for pattern in forbidden_patterns:
                    assert not re.search(pattern, module), (
                        f"Illegal from-import '{module}' matching '{pattern}' in {py_file.name}"
                    )
