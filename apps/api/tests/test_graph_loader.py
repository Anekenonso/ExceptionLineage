"""Tests for the deterministic Neo4j seed loader and property transformations."""

from unittest.mock import MagicMock

from app.graph.client import Neo4jClient
from app.graph.loader import SeedLoader, find_data_dir


def test_find_data_dir() -> None:
    data_dir = find_data_dir()
    assert (data_dir / "seed" / "customers.json").exists()
    assert (data_dir / "seed" / "invoices.json").exists()


def test_transform_customer_properties() -> None:
    raw = {
        "id": "CUS-001",
        "name": "Acme Global Enterprise Inc.",
        "external_id": "EXT-CRM-001",
        "created_at": "2026-01-01T00:00:00Z",
    }
    props = SeedLoader.transform_customer(raw)
    assert props["id"] == "CUS-001"
    assert props["name"] == "Acme Global Enterprise Inc."
    assert props["external_id"] == "EXT-CRM-001"
    assert props["created_at"] == "2026-01-01T00:00:00+00:00"


def test_transform_contract_properties() -> None:
    raw = {
        "id": "CTR-001",
        "customer_id": "CUS-001",
        "title": "Master Cloud Agreement",
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_until": "2026-12-31T23:59:59Z",
        "status": "ACTIVE",
        "currency": "USD",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": None,
    }
    props = SeedLoader.transform_contract(raw)
    assert props["id"] == "CTR-001"
    assert props["customer_id"] == "CUS-001"
    assert props["status"] == "ACTIVE"
    assert props["effective_until"] == "2026-12-31T23:59:59+00:00"


def test_transform_exception_preserves_exact_decimal_and_cents() -> None:
    raw = {
        "id": "EX-001",
        "contract_id": "CTR-001",
        "invoice_id": "INV-1001",
        "exception_type": "RATE_VARIANCE",
        "description": "Rate discount",
        "expected_amount": "12000.00",
        "actual_amount": "10200.00",
        "currency": "USD",
        "created_at": "2026-03-15T00:00:00Z",
        "updated_at": None,
    }
    props = SeedLoader.transform_exception(raw)
    assert props["expected_amount"] == "12000.00"
    assert props["expected_amount_cents"] == 1200000
    assert props["actual_amount"] == "10200.00"
    assert props["actual_amount_cents"] == 1020000


def test_transform_invoice_preserves_exact_money_and_handles_null_links() -> None:
    # Test invoice with null contract and exception (INV-1007)
    raw = {
        "id": "INV-1007",
        "customer_id": "CUS-003",
        "contract_id": None,
        "exception_id": None,
        "product_id": "PROD-LOGISTICS-API",
        "amount": "8000.00",
        "currency": "USD",
        "issued_at": "2026-06-01T00:00:00Z",
        "due_at": "2026-07-01T00:00:00Z",
        "created_at": "2026-06-01T00:00:00Z",
    }
    props = SeedLoader.transform_invoice(raw)
    assert props["id"] == "INV-1007"
    assert props["amount"] == "8000.00"
    assert props["amount_cents"] == 800000
    assert props["contract_id"] is None
    assert props["exception_id"] is None


def test_transform_approval_serializes_context() -> None:
    raw = {
        "id": "APR-001",
        "exception_id": "EX-001",
        "approver": "sarah.chen@acmeglobal.com",
        "status": "APPROVED",
        "approved_at": "2026-02-01T14:30:00Z",
        "context": {"role": "VP Commercial Finance", "ref": "AUTH-1"},
        "created_at": "2026-01-20T09:00:00Z",
    }
    props = SeedLoader.transform_approval(raw)
    assert props["id"] == "APR-001"
    assert props["status"] == "APPROVED"
    assert "VP Commercial Finance" in props["context_json"]


def test_seed_loader_executes_complete_pipeline_with_mock_client() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    # Return count 1 for relationship queries
    mock_client.execute_query.return_value = [{"cnt": 1}]

    loader = SeedLoader(mock_client)
    report = loader.load_seed_data(init_schema=True, clear_existing=True)

    assert report.is_success
    assert mock_client.initialize_schema.called
    assert mock_client.clear_database.called

    # Verify counts of loaded nodes match the Stage 12 dataset
    assert report.nodes_loaded["Customer"] == 3
    assert report.nodes_loaded["Contract"] == 2
    assert report.nodes_loaded["Amendment"] == 7
    assert report.nodes_loaded["SOW"] == 2
    assert report.nodes_loaded["Exception"] == 7
    assert report.nodes_loaded["Approval"] == 3
    assert report.nodes_loaded["Invoice"] == 8
    assert report.nodes_loaded["Evidence"] == 13
    assert report.total_nodes == 45

    # Verify relationships were registered in report
    assert "HAS_CONTRACT" in report.relationships_loaded
    assert "HAS_AMENDMENT" in report.relationships_loaded
    assert "HAS_SOW" in report.relationships_loaded
    assert "HAS_APPROVAL" in report.relationships_loaded
    assert "BILLED_TO" in report.relationships_loaded
    assert "GOVERNED_BY" in report.relationships_loaded
    assert "HAS_EVIDENCE" in report.relationships_loaded
