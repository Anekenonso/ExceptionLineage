"""Live Neo4j integration test (conditionally executed if Neo4j is running)."""

import pytest

from app.graph.client import Neo4jClient
from app.graph.loader import SeedLoader
from app.graph.queries import get_invoice_lineage
from app.graph.verifier import GraphGroundTruthVerifier


def is_live_neo4j_reachable() -> bool:
    try:
        client = Neo4jClient()
        return client.verify_connectivity()
    except Exception:
        return False


neo4j_live = pytest.mark.skipif(
    not is_live_neo4j_reachable(),
    reason="Live Neo4j instance is not reachable at configured URI",
)


@neo4j_live
def test_live_neo4j_seed_and_verify() -> None:
    """Full live integration test: initialises schema, loads seed data, and verifies ground truth."""
    client = Neo4jClient()

    # Load seed data
    loader = SeedLoader(client)
    report = loader.load_seed_data(init_schema=True, clear_existing=True)
    assert report.is_success
    assert report.total_nodes == 45

    # Test deterministic traversal query
    lineage = get_invoice_lineage(client, "INV-1001")
    assert lineage is not None
    assert lineage["invoice"]["id"] == "INV-1001"
    assert lineage["contract"]["id"] == "CTR-001"
    assert lineage["exception"]["id"] == "EX-001"
    assert lineage["approval"]["id"] == "APR-001"

    # Verify ground truth
    verifier = GraphGroundTruthVerifier(client)
    gt_report = verifier.verify_all()
    assert gt_report.is_all_passed
