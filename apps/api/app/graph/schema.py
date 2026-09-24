"""Neo4j graph schema definitions, constraints, indexes, and relationship types."""

from enum import Enum


class NodeLabel(str, Enum):
    """Labels for Neo4j graph nodes corresponding to Stage 11 domain models."""

    CUSTOMER = "Customer"
    CONTRACT = "Contract"
    AMENDMENT = "Amendment"
    SOW = "SOW"
    EXCEPTION = "Exception"
    APPROVAL = "Approval"
    INVOICE = "Invoice"
    EVIDENCE = "Evidence"


class RelationshipType(str, Enum):
    """Relationship types connecting domain entities in the Neo4j knowledge graph."""

    # Customer -> Contract
    HAS_CONTRACT = "HAS_CONTRACT"

    # Contract -> Amendment / SOW / Exception
    HAS_AMENDMENT = "HAS_AMENDMENT"
    AMENDS = "AMENDS"
    HAS_SOW = "HAS_SOW"
    UNDER_CONTRACT = "UNDER_CONTRACT"
    HAS_EXCEPTION = "HAS_EXCEPTION"

    # Exception -> Approval
    HAS_APPROVAL = "HAS_APPROVAL"
    APPROVES = "APPROVES"

    # Invoice relationships
    BILLED_TO = "BILLED_TO"
    HAS_INVOICE = "HAS_INVOICE"
    GOVERNED_BY = "GOVERNED_BY"

    # Evidence citations
    HAS_EVIDENCE = "HAS_EVIDENCE"
    EVIDENCE_FOR = "EVIDENCE_FOR"


# Unique constraints ensuring deterministic, non-duplicate domain identifiers
CONSTRAINTS: list[str] = [
    "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT contract_id_unique IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT amendment_id_unique IF NOT EXISTS FOR (a:Amendment) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT sow_id_unique IF NOT EXISTS FOR (s:SOW) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT exception_id_unique IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT approval_id_unique IF NOT EXISTS FOR (a:Approval) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT invoice_id_unique IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",
]

# Indexes supporting multi-hop traversal and query acceleration
INDEXES: list[str] = [
    "CREATE INDEX contract_customer_id_idx IF NOT EXISTS FOR (c:Contract) ON (c.customer_id)",
    "CREATE INDEX amendment_contract_id_idx IF NOT EXISTS FOR (a:Amendment) ON (a.contract_id)",
    "CREATE INDEX sow_contract_id_idx IF NOT EXISTS FOR (s:SOW) ON (s.contract_id)",
    "CREATE INDEX exception_contract_id_idx IF NOT EXISTS FOR (e:Exception) ON (e.contract_id)",
    "CREATE INDEX exception_invoice_id_idx IF NOT EXISTS FOR (e:Exception) ON (e.invoice_id)",
    "CREATE INDEX approval_exception_id_idx IF NOT EXISTS FOR (a:Approval) ON (a.exception_id)",
    "CREATE INDEX invoice_customer_id_idx IF NOT EXISTS FOR (i:Invoice) ON (i.customer_id)",
    "CREATE INDEX invoice_contract_id_idx IF NOT EXISTS FOR (i:Invoice) ON (i.contract_id)",
    "CREATE INDEX evidence_source_id_idx IF NOT EXISTS FOR (e:Evidence) ON (e.source_id)",
]


def get_schema_init_queries() -> list[str]:
    """Return all schema initialization queries in correct execution order."""
    return [*CONSTRAINTS, *INDEXES]
