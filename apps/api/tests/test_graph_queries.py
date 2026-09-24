"""Tests for deterministic investigation traversal queries."""

from unittest.mock import MagicMock

from app.graph.client import Neo4jClient
from app.graph.queries import (
    find_orphaned_invoices,
    find_unapproved_exceptions,
    get_contract_hierarchy,
    get_evidence_for_entity,
    get_invoice_lineage,
)


def test_get_invoice_lineage_returns_mapped_dict() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = [
        {
            "invoice": {"id": "INV-1001", "amount": "10200.00"},
            "customer": {"id": "CUS-001", "name": "Acme Global"},
            "contract": {"id": "CTR-001", "title": "Master Agreement"},
            "exception": {"id": "EX-001", "exception_type": "RATE_VARIANCE"},
            "approval": {"id": "APR-001", "status": "APPROVED"},
            "amendments": [{"id": "AMD-001", "title": "Volume Discount"}],
            "sows": [],
            "evidence": [
                {"id": "EV-001", "source_id": "CTR-001"},
                {"id": "EV-002", "source_id": "AMD-001"},
                {"id": "EV-003", "source_id": "APR-001"},
            ],
        }
    ]

    result = get_invoice_lineage(mock_client, "INV-1001")
    assert result is not None
    assert result["invoice"]["id"] == "INV-1001"
    assert result["contract"]["id"] == "CTR-001"
    assert result["exception"]["id"] == "EX-001"
    assert result["approval"]["id"] == "APR-001"
    assert len(result["amendments"]) == 1
    assert result["amendments"][0]["id"] == "AMD-001"
    assert len(result["evidence"]) == 3


def test_get_invoice_lineage_returns_none_if_not_found() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = []

    result = get_invoice_lineage(mock_client, "NON-EXISTENT")
    assert result is None


def test_get_contract_hierarchy() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = [
        {
            "contract": {"id": "CTR-001", "title": "Master Agreement"},
            "customer": {"id": "CUS-001"},
            "amendments": [{"id": "AMD-001"}, {"id": "AMD-002"}],
            "sows": [{"id": "SOW-001"}],
            "exceptions": [{"id": "EX-001"}],
            "approvals": [{"id": "APR-001"}],
            "evidence": [{"id": "EV-001"}],
        }
    ]

    result = get_contract_hierarchy(mock_client, "CTR-001")
    assert result is not None
    assert result["contract"]["id"] == "CTR-001"
    assert len(result["amendments"]) == 2
    assert len(result["sows"]) == 1


def test_get_evidence_for_entity() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = [
        {"evidence": {"id": "EV-001", "source_id": "CTR-001"}},
    ]

    result = get_evidence_for_entity(mock_client, "CTR-001")
    assert len(result) == 1
    assert result[0]["id"] == "EV-001"
    mock_client.execute_query.assert_called_once()


def test_find_orphaned_invoices() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = [
        {
            "invoice": {"id": "INV-1007", "customer_id": "CUS-003", "amount": "8000.00"},
            "customer": {"id": "CUS-003", "name": "Vertex Freight"},
        }
    ]

    result = find_orphaned_invoices(mock_client)
    assert len(result) == 1
    assert result[0]["invoice"]["id"] == "INV-1007"


def test_find_unapproved_exceptions() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    mock_client.execute_query.return_value = [
        {"exception": {"id": "EX-002"}, "approval": None, "contract": {"id": "CTR-001"}},
        {"exception": {"id": "EX-005"}, "approval": {"id": "APR-005", "status": "PENDING"}, "contract": {"id": "CTR-001"}},
    ]

    result = find_unapproved_exceptions(mock_client)
    assert len(result) == 2
    assert result[0]["exception"]["id"] == "EX-002"
    assert result[0]["approval"] is None
    assert result[1]["approval"]["status"] == "PENDING"
