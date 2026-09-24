"""Tests for Neo4j schema definitions, constraints, indexes, and relationship types."""

from app.graph.schema import (
    CONSTRAINTS,
    INDEXES,
    NodeLabel,
    RelationshipType,
    get_schema_init_queries,
)


def test_node_labels_defined() -> None:
    expected_labels = {
        "Customer",
        "Contract",
        "Amendment",
        "SOW",
        "Exception",
        "Approval",
        "Invoice",
        "Evidence",
    }
    actual_labels = {label.value for label in NodeLabel}
    assert actual_labels == expected_labels


def test_relationship_types_defined() -> None:
    expected_rels = {
        "HAS_CONTRACT",
        "HAS_AMENDMENT",
        "AMENDS",
        "HAS_SOW",
        "UNDER_CONTRACT",
        "HAS_EXCEPTION",
        "HAS_APPROVAL",
        "APPROVES",
        "BILLED_TO",
        "HAS_INVOICE",
        "GOVERNED_BY",
        "HAS_EVIDENCE",
        "EVIDENCE_FOR",
    }
    actual_rels = {rel.value for rel in RelationshipType}
    assert expected_rels.issubset(actual_rels)


def test_constraints_cover_all_node_labels() -> None:
    # 8 constraints for 8 node labels
    assert len(CONSTRAINTS) == 8
    for label in NodeLabel:
        matching = [c for c in CONSTRAINTS if f":{label.value}" in c and "REQUIRE" in c and ".id IS UNIQUE" in c]
        assert len(matching) == 1, f"Constraint missing or malformed for label {label.value}"


def test_indexes_defined() -> None:
    assert len(INDEXES) >= 8
    # Confirm key lookup indexes exist
    combined = " ".join(INDEXES)
    assert "contract_customer_id_idx" in combined
    assert "amendment_contract_id_idx" in combined
    assert "sow_contract_id_idx" in combined
    assert "exception_contract_id_idx" in combined
    assert "approval_exception_id_idx" in combined
    assert "invoice_customer_id_idx" in combined
    assert "evidence_source_id_idx" in combined


def test_get_schema_init_queries_order() -> None:
    queries = get_schema_init_queries()
    assert len(queries) == len(CONSTRAINTS) + len(INDEXES)
    # Constraints should precede indexes
    assert queries[: len(CONSTRAINTS)] == CONSTRAINTS
    assert queries[len(CONSTRAINTS) :] == INDEXES
