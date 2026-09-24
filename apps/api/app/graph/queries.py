"""Deterministic graph queries for investigation traversal in ExceptionLineage."""

from __future__ import annotations

from typing import Any

from app.graph.client import Neo4jClient
from app.graph.schema import NodeLabel, RelationshipType


def get_invoice_lineage(client: Neo4jClient, invoice_id: str) -> dict[str, Any] | None:
    """Traverse the complete evidence and relationship lineage for a given invoice.

    Returns the invoice, customer, governing contract, direct exception, approval,
    associated amendments, SOWs, and all evidentiary citations in the lineage chain.
    """
    query = f"""
    MATCH (i:{NodeLabel.INVOICE.value} {{id: $invoice_id}})
    OPTIONAL MATCH (i)-[:{RelationshipType.BILLED_TO.value}]->(c:{NodeLabel.CUSTOMER.value})
    OPTIONAL MATCH (i)-[:{RelationshipType.GOVERNED_BY.value}]->(k:{NodeLabel.CONTRACT.value})
    OPTIONAL MATCH (i)-[:{RelationshipType.HAS_EXCEPTION.value}]->(e:{NodeLabel.EXCEPTION.value})
    OPTIONAL MATCH (e)-[:{RelationshipType.HAS_APPROVAL.value}]->(a:{NodeLabel.APPROVAL.value})
    OPTIONAL MATCH (k)-[:{RelationshipType.HAS_AMENDMENT.value}]->(amd:{NodeLabel.AMENDMENT.value})
    OPTIONAL MATCH (k)-[:{RelationshipType.HAS_SOW.value}]->(sow:{NodeLabel.SOW.value})
    
    // Collect all evidence linked to contract, amendments, sows, or approvals in this lineage
    OPTIONAL MATCH (ev:{NodeLabel.EVIDENCE.value})
    WHERE (k IS NOT NULL AND ev.source_id = k.id)
       OR (amd IS NOT NULL AND ev.source_id = amd.id)
       OR (sow IS NOT NULL AND ev.source_id = sow.id)
       OR (a IS NOT NULL AND ev.source_id = a.id)
       OR (e IS NOT NULL AND ev.source_id = e.id)

    RETURN 
        properties(i) AS invoice,
        properties(c) AS customer,
        properties(k) AS contract,
        properties(e) AS exception,
        properties(a) AS approval,
        collect(DISTINCT properties(amd)) AS amendments,
        collect(DISTINCT properties(sow)) AS sows,
        collect(DISTINCT properties(ev)) AS evidence
    """
    results = client.execute_query(query, {"invoice_id": invoice_id})
    if not results or not results[0].get("invoice"):
        return None

    row = results[0]
    # Filter out empty dictionaries from collect(DISTINCT properties(null))
    amendments = [a for a in row.get("amendments", []) if a and a.get("id")]
    sows = [s for s in row.get("sows", []) if s and s.get("id")]
    evidence = [ev for ev in row.get("evidence", []) if ev and ev.get("id")]

    return {
        "invoice": row.get("invoice"),
        "customer": row.get("customer"),
        "contract": row.get("contract"),
        "exception": row.get("exception"),
        "approval": row.get("approval"),
        "amendments": amendments,
        "sows": sows,
        "evidence": evidence,
    }


def get_contract_hierarchy(client: Neo4jClient, contract_id: str) -> dict[str, Any] | None:
    """Retrieve a contract and its full child hierarchy: customer, amendments, SOWs, exceptions, and evidence."""
    query = f"""
    MATCH (k:{NodeLabel.CONTRACT.value} {{id: $contract_id}})
    OPTIONAL MATCH (c:{NodeLabel.CUSTOMER.value})-[:{RelationshipType.HAS_CONTRACT.value}]->(k)
    OPTIONAL MATCH (k)-[:{RelationshipType.HAS_AMENDMENT.value}]->(amd:{NodeLabel.AMENDMENT.value})
    OPTIONAL MATCH (k)-[:{RelationshipType.HAS_SOW.value}]->(sow:{NodeLabel.SOW.value})
    OPTIONAL MATCH (k)-[:{RelationshipType.HAS_EXCEPTION.value}]->(e:{NodeLabel.EXCEPTION.value})
    OPTIONAL MATCH (e)-[:{RelationshipType.HAS_APPROVAL.value}]->(a:{NodeLabel.APPROVAL.value})
    
    OPTIONAL MATCH (target)-[:{RelationshipType.HAS_EVIDENCE.value}]->(ev:{NodeLabel.EVIDENCE.value})
    WHERE target.id IN [k.id, amd.id, sow.id, a.id, e.id]

    RETURN
        properties(k) AS contract,
        properties(c) AS customer,
        collect(DISTINCT properties(amd)) AS amendments,
        collect(DISTINCT properties(sow)) AS sows,
        collect(DISTINCT properties(e)) AS exceptions,
        collect(DISTINCT properties(a)) AS approvals,
        collect(DISTINCT properties(ev)) AS evidence
    """
    results = client.execute_query(query, {"contract_id": contract_id})
    if not results or not results[0].get("contract"):
        return None

    row = results[0]
    return {
        "contract": row.get("contract"),
        "customer": row.get("customer"),
        "amendments": [x for x in row.get("amendments", []) if x and x.get("id")],
        "sows": [x for x in row.get("sows", []) if x and x.get("id")],
        "exceptions": [x for x in row.get("exceptions", []) if x and x.get("id")],
        "approvals": [x for x in row.get("approvals", []) if x and x.get("id")],
        "evidence": [x for x in row.get("evidence", []) if x and x.get("id")],
    }


def get_evidence_for_entity(client: Neo4jClient, entity_id: str) -> list[dict[str, Any]]:
    """Fetch all evidence citations linked to a specific entity identifier."""
    query = f"""
    MATCH (n {{id: $entity_id}})-[:{RelationshipType.HAS_EVIDENCE.value}]->(e:{NodeLabel.EVIDENCE.value})
    RETURN properties(e) AS evidence
    ORDER BY e.id
    """
    results = client.execute_query(query, {"entity_id": entity_id})
    return [r["evidence"] for r in results if r.get("evidence")]


def find_orphaned_invoices(client: Neo4jClient) -> list[dict[str, Any]]:
    """Find all invoices that do not have a governing contract linked in the graph."""
    query = f"""
    MATCH (i:{NodeLabel.INVOICE.value})
    WHERE NOT (i)-[:{RelationshipType.GOVERNED_BY.value}]->(:{NodeLabel.CONTRACT.value})
    OPTIONAL MATCH (i)-[:{RelationshipType.BILLED_TO.value}]->(c:{NodeLabel.CUSTOMER.value})
    RETURN properties(i) AS invoice, properties(c) AS customer
    ORDER BY i.id
    """
    results = client.execute_query(query)
    return results


def find_unapproved_exceptions(client: Neo4jClient) -> list[dict[str, Any]]:
    """Find all exceptions that either lack an approval or whose approval is not APPROVED."""
    query = f"""
    MATCH (e:{NodeLabel.EXCEPTION.value})
    OPTIONAL MATCH (e)-[:{RelationshipType.HAS_APPROVAL.value}]->(a:{NodeLabel.APPROVAL.value})
    WHERE a IS NULL OR a.status <> 'APPROVED'
    OPTIONAL MATCH (k:{NodeLabel.CONTRACT.value})-[:{RelationshipType.HAS_EXCEPTION.value}]->(e)
    RETURN 
        properties(e) AS exception,
        properties(a) AS approval,
        properties(k) AS contract
    ORDER BY e.id
    """
    results = client.execute_query(query)
    return results
