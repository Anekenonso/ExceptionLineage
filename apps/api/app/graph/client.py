"""Neo4j client wrapper using the official Neo4j Python driver."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import Driver, GraphDatabase, Query, Session
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.config import settings
from app.graph.schema import get_schema_init_queries

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Manages the Neo4j driver connection, session execution, and schema lifecycle."""

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        driver: Driver | None = None,
    ) -> None:
        self.uri = uri or settings.neo4j_uri
        self.username = username or settings.neo4j_username
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database
        self._driver: Driver | None = driver

    @property
    def driver(self) -> Driver:
        """Return the active driver, instantiating if necessary."""
        if self._driver is None:
            self.connect()
        assert self._driver is not None
        return self._driver

    def connect(self) -> None:
        """Establish the Neo4j driver connection."""
        if self._driver is None:
            logger.info("Connecting to Neo4j at %s (db: %s)", self.uri, self.database)
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> Neo4jClient:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def verify_connectivity(self) -> bool:
        """Verify that the Neo4j database is reachable and credentials are valid."""
        try:
            self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, Neo4jError, OSError) as exc:
            logger.warning("Neo4j connectivity check failed: %s", exc)
            return False

    def execute_query(
        self,
        query: str | Query,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return the records as a list of dictionaries."""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str | Query,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a write transaction using session.execute_write."""
        def _work(tx: Any) -> list[dict[str, Any]]:
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        with self.driver.session(database=self.database) as session:
            return session.execute_write(_work)

    def initialize_schema(self) -> list[str]:
        """Execute all constraint and index creation queries. Returns the list of executed queries."""
        executed = []
        queries = get_schema_init_queries()
        with self.driver.session(database=self.database) as session:
            for q in queries:
                try:
                    session.run(q)
                    executed.append(q)
                except Neo4jError as exc:
                    logger.error("Failed to execute schema query '%s': %s", q, exc)
                    raise
        logger.info("Initialized Neo4j schema (%d constraints and indexes created/verified)", len(executed))
        return executed

    def clear_database(self) -> None:
        """Remove all nodes and relationships from the database (use for clean seed reset)."""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Cleared all nodes and relationships from Neo4j database '%s'", self.database)

    def get_counts(self) -> dict[str, Any]:
        """Return counts of each node label and relationship type in the database."""
        node_counts_query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) AS cnt', {}) YIELD value
        RETURN label, value.cnt AS count
        """
        # Fallback simple node counts if APOC is not available:
        labels = [
            "Customer",
            "Contract",
            "Amendment",
            "SOW",
            "Exception",
            "Approval",
            "Invoice",
            "Evidence",
        ]
        node_counts: dict[str, int] = {}
        with self.driver.session(database=self.database) as session:
            for lbl in labels:
                res = session.run(f"MATCH (n:{lbl}) RETURN count(n) AS count").single()
                node_counts[lbl] = res["count"] if res else 0

            rel_res = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count")
            rel_counts = {rec["type"]: rec["count"] for rec in rel_res}

        return {
            "nodes": node_counts,
            "relationships": rel_counts,
            "total_nodes": sum(node_counts.values()),
            "total_relationships": sum(rel_counts.values()),
        }
