"""Neo4j graph package for ExceptionLineage."""

from app.graph.client import Neo4jClient
from app.graph.lineage import (
    InMemoryLineageRepository,
    LineageRepository,
    Neo4jLineageRepository,
)
from app.graph.loader import SeedLoader, SeedLoadReport
from app.graph.queries import (
    find_orphaned_invoices,
    find_unapproved_exceptions,
    get_contract_hierarchy,
    get_evidence_for_entity,
    get_invoice_lineage,
)
from app.graph.schema import (
    CONSTRAINTS,
    INDEXES,
    NodeLabel,
    RelationshipType,
    get_schema_init_queries,
)
from app.graph.verifier import (
    CaseVerificationResult,
    GraphGroundTruthVerifier,
    GroundTruthVerificationReport,
)

__all__ = [
    # Schema
    "NodeLabel",
    "RelationshipType",
    "CONSTRAINTS",
    "INDEXES",
    "get_schema_init_queries",
    # Client
    "Neo4jClient",
    # Lineage Repository Abstraction
    "LineageRepository",
    "Neo4jLineageRepository",
    "InMemoryLineageRepository",
    # Loader
    "SeedLoader",
    "SeedLoadReport",
    # Traversal Queries
    "get_invoice_lineage",
    "get_contract_hierarchy",
    "get_evidence_for_entity",
    "find_orphaned_invoices",
    "find_unapproved_exceptions",
    # Verifier
    "GraphGroundTruthVerifier",
    "CaseVerificationResult",
    "GroundTruthVerificationReport",
]
