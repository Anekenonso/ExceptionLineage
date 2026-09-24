"""Lineage retrieval abstraction and implementations for ExceptionLineage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.graph.client import Neo4jClient
from app.graph.queries import get_invoice_lineage
from app.graph.schema import NodeLabel, RelationshipType


class LineageRepository(ABC):
    """Abstract interface for invoice evidence lineage retrieval.

    Decouples investigation orchestration from the physical Neo4j graph database,
    enabling deterministic test doubles without live database connections.
    """

    @abstractmethod
    def get_invoice_lineage(self, invoice_id: str) -> dict[str, Any] | None:
        """Traverse and return the complete lineage for a given invoice.

        Returns a dictionary containing the invoice, customer, governing contract,
        exception, approval, amendments, SOWs, and evidence citations, or None
        if the invoice does not exist in the graph.
        """
        ...

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        """Retrieve an invoice and its directly linked customer and exception."""
        lineage = self.get_invoice_lineage(invoice_id)
        if not lineage or not lineage.get("invoice"):
            return None
        return {
            "invoice": lineage.get("invoice"),
            "customer": lineage.get("customer"),
            "exception": lineage.get("exception"),
        }

    def get_contract(self, contract_id: str) -> dict[str, Any] | None:
        """Retrieve a contract and its associated customer."""
        return None

    def get_amendments(self, contract_id: str) -> list[dict[str, Any]]:
        """Retrieve amendments linked to a governing contract."""
        return []

    def get_sows(self, contract_id: str) -> list[dict[str, Any]]:
        """Retrieve Statements of Work (SOWs) linked to a governing contract."""
        return []

    def get_approvals(self, exception_id: str) -> list[dict[str, Any]]:
        """Retrieve approval records linked to a specific transaction exception."""
        return []

    def get_evidence(self, source_ids: list[str]) -> list[dict[str, Any]]:
        """Retrieve evidentiary citations linked to any of the specified source entity IDs."""
        return []


class Neo4jLineageRepository(LineageRepository):
    """Production implementation retrieving invoice lineage from Neo4j."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or Neo4jClient()

    def get_invoice_lineage(self, invoice_id: str) -> dict[str, Any] | None:
        """Execute deterministic Cypher traversal query against Neo4j."""
        return get_invoice_lineage(self.client, invoice_id)

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        query = f"""
        MATCH (i:{NodeLabel.INVOICE.value} {{id: $invoice_id}})
        OPTIONAL MATCH (i)-[:{RelationshipType.BILLED_TO.value}]->(c:{NodeLabel.CUSTOMER.value})
        OPTIONAL MATCH (i)-[:{RelationshipType.HAS_EXCEPTION.value}]->(e:{NodeLabel.EXCEPTION.value})
        RETURN properties(i) AS invoice, properties(c) AS customer, properties(e) AS exception
        """
        results = self.client.execute_query(query, {"invoice_id": invoice_id})
        if not results or not results[0].get("invoice"):
            return None
        return {
            "invoice": results[0].get("invoice"),
            "customer": results[0].get("customer"),
            "exception": results[0].get("exception"),
        }

    def get_contract(self, contract_id: str) -> dict[str, Any] | None:
        query = f"""
        MATCH (k:{NodeLabel.CONTRACT.value} {{id: $contract_id}})
        OPTIONAL MATCH (c:{NodeLabel.CUSTOMER.value})-[:{RelationshipType.HAS_CONTRACT.value}]->(k)
        RETURN properties(k) AS contract, properties(c) AS customer
        """
        results = self.client.execute_query(query, {"contract_id": contract_id})
        if not results or not results[0].get("contract"):
            return None
        return {
            "contract": results[0].get("contract"),
            "customer": results[0].get("customer"),
        }

    def get_amendments(self, contract_id: str) -> list[dict[str, Any]]:
        query = f"""
        MATCH (k:{NodeLabel.CONTRACT.value} {{id: $contract_id}})-[:{RelationshipType.HAS_AMENDMENT.value}]->(amd:{NodeLabel.AMENDMENT.value})
        RETURN properties(amd) AS amendment
        ORDER BY amd.id
        """
        results = self.client.execute_query(query, {"contract_id": contract_id})
        return [r["amendment"] for r in results if r.get("amendment")]

    def get_sows(self, contract_id: str) -> list[dict[str, Any]]:
        query = f"""
        MATCH (k:{NodeLabel.CONTRACT.value} {{id: $contract_id}})-[:{RelationshipType.HAS_SOW.value}]->(sow:{NodeLabel.SOW.value})
        RETURN properties(sow) AS sow
        ORDER BY sow.id
        """
        results = self.client.execute_query(query, {"contract_id": contract_id})
        return [r["sow"] for r in results if r.get("sow")]

    def get_approvals(self, exception_id: str) -> list[dict[str, Any]]:
        query = f"""
        MATCH (e:{NodeLabel.EXCEPTION.value} {{id: $exception_id}})-[:{RelationshipType.HAS_APPROVAL.value}]->(a:{NodeLabel.APPROVAL.value})
        RETURN properties(a) AS approval
        ORDER BY a.id
        """
        results = self.client.execute_query(query, {"exception_id": exception_id})
        return [r["approval"] for r in results if r.get("approval")]

    def get_evidence(self, source_ids: list[str]) -> list[dict[str, Any]]:
        query = f"""
        MATCH (ev:{NodeLabel.EVIDENCE.value})
        WHERE ev.source_id IN $source_ids
        RETURN properties(ev) AS evidence
        ORDER BY ev.id
        """
        results = self.client.execute_query(query, {"source_ids": source_ids})
        return [r["evidence"] for r in results if r.get("evidence")]


class InMemoryLineageRepository(LineageRepository):
    """In-memory lineage repository for deterministic testing and offline verification."""

    def __init__(self, lineages: dict[str, dict[str, Any]] | None = None) -> None:
        self._lineages: dict[str, dict[str, Any]] = dict(lineages or {})

    def add_lineage(self, invoice_id: str, lineage: dict[str, Any]) -> None:
        """Register or update an invoice lineage in the in-memory store."""
        self._lineages[invoice_id] = lineage

    def get_invoice_lineage(self, invoice_id: str) -> dict[str, Any] | None:
        """Retrieve lineage from the in-memory store."""
        return self._lineages.get(invoice_id)

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        lin = self._lineages.get(invoice_id)
        if not lin or not lin.get("invoice"):
            return None
        return {
            "invoice": lin.get("invoice"),
            "customer": lin.get("customer"),
            "exception": lin.get("exception"),
        }

    def get_contract(self, contract_id: str) -> dict[str, Any] | None:
        for lin in self._lineages.values():
            contract = lin.get("contract")
            if contract and contract.get("id") == contract_id:
                return {
                    "contract": contract,
                    "customer": lin.get("customer"),
                }
        return None

    def get_amendments(self, contract_id: str) -> list[dict[str, Any]]:
        for lin in self._lineages.values():
            contract = lin.get("contract")
            if contract and contract.get("id") == contract_id:
                return list(lin.get("amendments") or [])
        return []

    def get_sows(self, contract_id: str) -> list[dict[str, Any]]:
        for lin in self._lineages.values():
            contract = lin.get("contract")
            if contract and contract.get("id") == contract_id:
                return list(lin.get("sows") or [])
        return []

    def get_approvals(self, exception_id: str) -> list[dict[str, Any]]:
        for lin in self._lineages.values():
            exc = lin.get("exception")
            if exc and exc.get("id") == exception_id:
                apr = lin.get("approval")
                return [apr] if apr else []
        return []

    def get_evidence(self, source_ids: list[str]) -> list[dict[str, Any]]:
        source_set = set(source_ids)
        evidence_map: dict[str, dict[str, Any]] = {}
        for lin in self._lineages.values():
            for ev in lin.get("evidence") or []:
                if ev.get("source_id") in source_set:
                    evidence_map[ev["id"]] = ev
        return sorted(list(evidence_map.values()), key=lambda x: x["id"])
