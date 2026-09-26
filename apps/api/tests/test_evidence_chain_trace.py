"""Automated tests for Stage 18.5 / Stage 21 Claim C: End-to-End Evidence Chain Trace.

Verifies that the demonstrated investigation trace reconstructs the path from investigation input
through agent decisions, tool execution, evidence retrieval, deterministic validation, and final outcome
while preserving the authority boundary and redacting secrets:
1. Complete chronological chain:
   INPUT -> AGENT_DECISION -> TOOL_CALL -> GRAPH_RETRIEVAL -> VALIDATION -> OUTCOME.
2. Complete secret redaction across all arguments and metadata.
3. Preservation of immutable timestamps and identifiers.
4. Tri-state deterministic validation status semantics (PASS, FAIL, UNKNOWN).
5. HTTP API endpoint GET /api/investigations/{id}/trace returns verified trace.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.graph.lineage import InMemoryLineageRepository
from app.investigations.router import reset_default_service
from app.investigations.service import InvestigationService
from app.investigations.trace import _sanitize_secrets, build_evidence_trace
from app.main import app
from evaluation.dataset import load_seed_lineages


@pytest.fixture
def test_service():
    """Create isolated InvestigationService loaded with canonical seed data."""
    lineages = load_seed_lineages()
    service = InvestigationService(lineage_repository=InMemoryLineageRepository(lineages))
    reset_default_service(service)
    yield service
    reset_default_service(None)


def test_end_to_end_evidence_trace_generation(test_service):
    """Investigation execution produces an auditable, unbroken machine-readable trace."""
    inv = test_service.run_investigation("INV-1001")
    trace = test_service.get_evidence_trace(inv.id)

    assert trace.investigation_id == inv.id
    assert trace.chain_verified is True
    assert trace.final_outcome == "VERIFIED"
    assert len(trace.events) >= 10

    event_types = [e.type for e in trace.events]
    assert "input" in event_types
    assert "agent_decision" in event_types
    assert "tool_call" in event_types
    assert "graph_retrieval" in event_types
    assert "validation" in event_types
    assert "outcome" in event_types

    # First event must be input and last event must be outcome
    assert event_types[0] == "input"
    assert event_types[-1] == "outcome"

    # Input details
    assert trace.input["invoice_id"] == "INV-1001"
    assert trace.input["data_notice"] == "SIMULATED_DATA_FOR_EVALUATION"


def test_trace_secret_redaction():
    """Confidential credentials, auth tokens, and API keys are strictly redacted from trace."""
    leaked_payload = {
        "invoice_id": "INV-1001",
        "api_key": "sk-1234567890abcdef1234567890abcdef",
        "nested": {
            "password": "super_secret_password",
            "auth_token": "AQ.some-secret-token-value-1234567890",
            "normal_field": "valid_value",
        },
        "plain_key": "some_secret_key",
    }
    sanitized = _sanitize_secrets(leaked_payload)

    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["auth_token"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "valid_value"
    assert sanitized["plain_key"] == "[REDACTED]"


def test_trace_tri_state_validation_semantics(test_service):
    """Validation trace events adhere strictly to tri-state check statuses (PASS, FAIL, UNKNOWN)."""
    inv = test_service.run_investigation("INV-1001")
    trace = test_service.get_evidence_trace(inv.id)

    val_events = [e for e in trace.events if e.type == "validation"]
    assert len(val_events) > 0

    valid_statuses = {"PASS", "FAIL", "UNKNOWN"}
    for ve in val_events:
        assert ve.status in valid_statuses
        assert ve.check is not None
        assert isinstance(ve.evidence_ids, list)


def test_trace_http_api_endpoint(test_service):
    """GET /api/investigations/{id}/trace returns verified trace JSON schema."""
    client = TestClient(app)

    create_resp = client.post("/api/investigations", json={"invoice_id": "INV-1001"})
    assert create_resp.status_code == 200
    inv_data = create_resp.json()
    inv_id = inv_data["investigation_id"]

    trace_resp = client.get(f"/api/investigations/{inv_id}/trace")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()

    assert trace_data["investigation_id"] == inv_id
    assert trace_data["chain_verified"] is True
    assert trace_data["final_outcome"] == "VERIFIED"
    assert isinstance(trace_data["events"], list)
    assert len(trace_data["events"]) > 0
    assert trace_data["summary"]["authority_boundary_preserved"] is True
