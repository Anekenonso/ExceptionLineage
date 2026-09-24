"""Lineage retrieval abstraction and implementations for ExceptionLineage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.graph.client import Neo4jClient
from app.graph.queries import get_invoice_lineage


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


class Neo4jLineageRepository(LineageRepository):
    """Production implementation retrieving invoice lineage from Neo4j."""

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or Neo4jClient()

    def get_invoice_lineage(self, invoice_id: str) -> dict[str, Any] | None:
        """Execute deterministic Cypher traversal query against Neo4j."""
        return get_invoice_lineage(self.client, invoice_id)


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
