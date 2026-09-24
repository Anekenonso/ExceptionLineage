"""Unit and orchestration tests for InvestigationService and LineageRepository abstraction."""

import pytest

from app.graph.lineage import InMemoryLineageRepository, LineageRepository, Neo4jLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


class FailingLineageRepository(LineageRepository):
    """Test double that simulates Neo4j connectivity drop."""

    def get_invoice_lineage(self, invoice_id: str) -> dict | None:
        raise ConnectionResetError("Neo4j socket closed unexpectedly")


def test_in_memory_lineage_repository_operations():
    """Verify InMemoryLineageRepository add and get behavior."""
    repo = InMemoryLineageRepository()
    assert repo.get_invoice_lineage("INV-999") is None

    repo.add_lineage("INV-999", {"invoice": {"id": "INV-999"}})
    lineage = repo.get_invoice_lineage("INV-999")
    assert lineage is not None
    assert lineage["invoice"]["id"] == "INV-999"


def test_service_orchestrates_lineage_retrieval_and_validation():
    """Verify that InvestigationService retrieves lineage via LineageRepository and completes validation."""
    lineages = build_mock_seed_graph_lineage()
    lineage_repo = InMemoryLineageRepository(lineages)
    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=lineage_repo,
    )

    inv = service.run_investigation(
        invoice_id="INV-1001",
        investigation_id="INVG-SVC-001",
    )

    assert inv.status == InvestigationStatus.VERIFIED
    assert inv.summary is not None
    assert "authorized and verified" in inv.summary.lower()
    assert inv.validation_results is not None
    assert len(inv.validation_results) == 8
    assert "EV-001" in inv.cited_evidence_ids

    events = service.get_events("INVG-SVC-001")
    assert len(events) == 3
    assert events[0].from_state == InvestigationStatus.QUEUED
    assert events[0].to_state == InvestigationStatus.INVESTIGATING
    assert events[1].from_state == InvestigationStatus.INVESTIGATING
    assert events[1].to_state == InvestigationStatus.VALIDATING
    assert events[2].from_state == InvestigationStatus.VALIDATING
    assert events[2].to_state == InvestigationStatus.VERIFIED


def test_service_graph_failure_transitions_to_failed():
    """Verify that graph retrieval exception transitions INVESTIGATING -> FAILED with 2 events."""
    failing_repo = FailingLineageRepository()
    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=failing_repo,
    )

    inv = service.run_investigation(
        invoice_id="INV-1001",
        investigation_id="INVG-SVC-FAIL",
    )

    assert inv.status == InvestigationStatus.FAILED
    assert "Graph retrieval failed" in inv.failure_reason
    assert "socket closed unexpectedly" in inv.failure_reason
    assert inv.validation_results is None
    assert inv.cited_evidence_ids == []

    events = service.get_events("INVG-SVC-FAIL")
    assert len(events) == 2
    assert events[0].from_state == InvestigationStatus.QUEUED
    assert events[0].to_state == InvestigationStatus.INVESTIGATING
    assert events[1].from_state == InvestigationStatus.INVESTIGATING
    assert events[1].to_state == InvestigationStatus.FAILED


def test_service_invoice_missing_from_graph_transitions_to_failed():
    """Verify that missing invoice in graph transitions INVESTIGATING -> FAILED."""
    empty_repo = InMemoryLineageRepository({})
    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=empty_repo,
    )

    inv = service.run_investigation(
        invoice_id="INV-ABSENT",
        investigation_id="INVG-SVC-ABSENT",
    )

    assert inv.status == InvestigationStatus.FAILED
    assert "not found in knowledge graph" in inv.failure_reason

    events = service.get_events("INVG-SVC-ABSENT")
    assert len(events) == 2
    assert events[1].to_state == InvestigationStatus.FAILED
