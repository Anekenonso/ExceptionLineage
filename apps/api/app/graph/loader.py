"""Deterministic seed data loader for populating Neo4j from Stage 12 simulated data."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.graph.client import Neo4jClient
from app.graph.schema import NodeLabel, RelationshipType
from app.models.contract import Amendment, Contract, SOW
from app.models.customer import Customer
from app.models.evidence import Evidence
from app.models.exception import Approval, TransactionException
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)


def find_data_dir() -> Path:
    """Find the data directory by traversing upwards until data/seed is found."""
    current = Path(__file__).resolve().parent
    for _ in range(6):
        if (current / "data" / "seed").exists():
            return current / "data"
        current = current.parent

    current = Path.cwd()
    for _ in range(6):
        if (current / "data" / "seed").exists():
            return current / "data"
        current = current.parent

    raise FileNotFoundError(f"Could not locate 'data/seed' from {Path(__file__)} or {Path.cwd()}")


@dataclass
class SeedLoadReport:
    """Summary of nodes and relationships created during seed data loading."""

    nodes_loaded: dict[str, int] = field(default_factory=dict)
    relationships_loaded: dict[str, int] = field(default_factory=dict)
    total_nodes: int = 0
    total_relationships: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return len(errors) == 0 if (errors := self.errors) else True


class SeedLoader:
    """Loads validated Stage 12 domain models into Neo4j with idempotent Cypher queries."""

    def __init__(self, client: Neo4jClient, data_dir: Path | None = None) -> None:
        self.client = client
        self.data_dir = data_dir or find_data_dir()

    def _read_json_file(self, filename: str) -> list[dict[str, Any]]:
        path = self.data_dir / "seed" / filename
        if not path.exists():
            raise FileNotFoundError(f"Seed file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------------------------------
    # Property Transformation Helpers (Exact Decimal & ISO Datetimes)
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_cents(amount: Decimal | None) -> int | None:
        """Convert Decimal currency to integer cents without floating-point drift."""
        if amount is None:
            return None
        return int((amount * 100).to_integral_value())

    @classmethod
    def transform_customer(cls, item: dict[str, Any]) -> dict[str, Any]:
        c = Customer.model_validate(item)
        return {
            "id": c.id,
            "name": c.name,
            "external_id": c.external_id or "",
            "created_at": c.created_at.isoformat(),
        }

    @classmethod
    def transform_contract(cls, item: dict[str, Any]) -> dict[str, Any]:
        c = Contract.model_validate(item)
        return {
            "id": c.id,
            "customer_id": c.customer_id,
            "title": c.title,
            "effective_from": c.effective_from.isoformat(),
            "effective_until": c.effective_until.isoformat() if c.effective_until else None,
            "status": c.status.value,
            "currency": c.currency,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }

    @classmethod
    def transform_amendment(cls, item: dict[str, Any]) -> dict[str, Any]:
        a = Amendment.model_validate(item)
        return {
            "id": a.id,
            "contract_id": a.contract_id,
            "amendment_number": a.amendment_number,
            "title": a.title,
            "description": a.description or "",
            "effective_from": a.effective_from.isoformat(),
            "effective_until": a.effective_until.isoformat() if a.effective_until else None,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }

    @classmethod
    def transform_sow(cls, item: dict[str, Any]) -> dict[str, Any]:
        s = SOW.model_validate(item)
        return {
            "id": s.id,
            "contract_id": s.contract_id,
            "reference": s.reference,
            "title": s.title,
            "scope": s.scope or "",
            "effective_from": s.effective_from.isoformat(),
            "effective_until": s.effective_until.isoformat() if s.effective_until else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }

    @classmethod
    def transform_exception(cls, item: dict[str, Any]) -> dict[str, Any]:
        e = TransactionException.model_validate(item)
        return {
            "id": e.id,
            "contract_id": e.contract_id,
            "invoice_id": e.invoice_id or "",
            "exception_type": e.exception_type,
            "description": e.description,
            "expected_amount": str(e.expected_amount) if e.expected_amount is not None else None,
            "expected_amount_cents": cls._to_cents(e.expected_amount),
            "actual_amount": str(e.actual_amount) if e.actual_amount is not None else None,
            "actual_amount_cents": cls._to_cents(e.actual_amount),
            "currency": e.currency,
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        }

    @classmethod
    def transform_approval(cls, item: dict[str, Any]) -> dict[str, Any]:
        a = Approval.model_validate(item)
        context_str = json.dumps(a.context) if a.context is not None else None
        return {
            "id": a.id,
            "exception_id": a.exception_id,
            "approver": a.approver,
            "status": a.status.value,
            "approved_at": a.approved_at.isoformat() if a.approved_at else None,
            "context_json": context_str,
            "created_at": a.created_at.isoformat(),
        }

    @classmethod
    def transform_invoice(cls, item: dict[str, Any]) -> dict[str, Any]:
        inv = Invoice.model_validate(item)
        return {
            "id": inv.id,
            "customer_id": inv.customer_id,
            "contract_id": inv.contract_id,
            "exception_id": inv.exception_id,
            "product_id": inv.product_id or "",
            "amount": str(inv.amount),
            "amount_cents": cls._to_cents(inv.amount),
            "currency": inv.currency,
            "issued_at": inv.issued_at.isoformat(),
            "due_at": inv.due_at.isoformat() if inv.due_at else None,
            "created_at": inv.created_at.isoformat(),
        }

    @classmethod
    def transform_evidence(cls, item: dict[str, Any]) -> dict[str, Any]:
        ev = Evidence.model_validate(item)
        return {
            "id": ev.id,
            "evidence_type": ev.evidence_type,
            "source": ev.source,
            "source_id": ev.source_id,
            "title": ev.title or "",
            "locator": ev.locator or "",
            "excerpt": ev.excerpt or "",
            "captured_at": ev.captured_at.isoformat(),
            "effective_from": ev.effective_from.isoformat() if ev.effective_from else None,
            "effective_until": ev.effective_until.isoformat() if ev.effective_until else None,
            "scope": ev.scope or "",
            "confidence": ev.confidence if ev.confidence is not None else 1.0,
        }

    # -------------------------------------------------------------------------
    # Batch Node Ingestion Methods
    # -------------------------------------------------------------------------

    def load_customers(self) -> int:
        data = self._read_json_file("customers.json")
        props = [self.transform_customer(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (c:{NodeLabel.CUSTOMER.value} {{id: props.id}})
        SET c += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_contracts(self) -> int:
        data = self._read_json_file("contracts.json")
        props = [self.transform_contract(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (c:{NodeLabel.CONTRACT.value} {{id: props.id}})
        SET c += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_amendments(self) -> int:
        data = self._read_json_file("amendments.json")
        props = [self.transform_amendment(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (a:{NodeLabel.AMENDMENT.value} {{id: props.id}})
        SET a += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_sows(self) -> int:
        data = self._read_json_file("sows.json")
        props = [self.transform_sow(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (s:{NodeLabel.SOW.value} {{id: props.id}})
        SET s += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_exceptions(self) -> int:
        data = self._read_json_file("exceptions.json")
        props = [self.transform_exception(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (e:{NodeLabel.EXCEPTION.value} {{id: props.id}})
        SET e += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_approvals(self) -> int:
        data = self._read_json_file("approvals.json")
        props = [self.transform_approval(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (a:{NodeLabel.APPROVAL.value} {{id: props.id}})
        SET a += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_invoices(self) -> int:
        data = self._read_json_file("invoices.json")
        props = [self.transform_invoice(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (i:{NodeLabel.INVOICE.value} {{id: props.id}})
        SET i += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    def load_evidence(self) -> int:
        data = self._read_json_file("evidence.json")
        props = [self.transform_evidence(item) for item in data]
        query = f"""
        UNWIND $batch AS props
        MERGE (e:{NodeLabel.EVIDENCE.value} {{id: props.id}})
        SET e += props
        """
        self.client.execute_query(query, {"batch": props})
        return len(props)

    # -------------------------------------------------------------------------
    # Relationship Creation Methods
    # -------------------------------------------------------------------------

    def create_relationships(self) -> dict[str, int]:
        """Create domain relationships deterministically using MERGE."""
        counts: dict[str, int] = {}

        # 1. Customer -> Contract
        q_cust_contract = f"""
        MATCH (c:{NodeLabel.CUSTOMER.value}), (k:{NodeLabel.CONTRACT.value})
        WHERE k.customer_id = c.id
        MERGE (c)-[r:{RelationshipType.HAS_CONTRACT.value}]->(k)
        RETURN count(r) AS cnt
        """
        res = self.client.execute_query(q_cust_contract)
        counts[RelationshipType.HAS_CONTRACT.value] = res[0]["cnt"] if res else 0

        # 2. Contract -> Amendment (and reverse AMENDS)
        q_contract_amendment = f"""
        MATCH (k:{NodeLabel.CONTRACT.value}), (a:{NodeLabel.AMENDMENT.value})
        WHERE a.contract_id = k.id
        MERGE (k)-[r1:{RelationshipType.HAS_AMENDMENT.value}]->(a)
        MERGE (a)-[r2:{RelationshipType.AMENDS.value}]->(k)
        RETURN count(r1) AS cnt
        """
        res = self.client.execute_query(q_contract_amendment)
        counts[RelationshipType.HAS_AMENDMENT.value] = res[0]["cnt"] if res else 0
        counts[RelationshipType.AMENDS.value] = res[0]["cnt"] if res else 0

        # 3. Contract -> SOW (and reverse UNDER_CONTRACT)
        q_contract_sow = f"""
        MATCH (k:{NodeLabel.CONTRACT.value}), (s:{NodeLabel.SOW.value})
        WHERE s.contract_id = k.id
        MERGE (k)-[r1:{RelationshipType.HAS_SOW.value}]->(s)
        MERGE (s)-[r2:{RelationshipType.UNDER_CONTRACT.value}]->(k)
        RETURN count(r1) AS cnt
        """
        res = self.client.execute_query(q_contract_sow)
        counts[RelationshipType.HAS_SOW.value] = res[0]["cnt"] if res else 0
        counts[RelationshipType.UNDER_CONTRACT.value] = res[0]["cnt"] if res else 0

        # 4. Contract -> Exception
        q_contract_exception = f"""
        MATCH (k:{NodeLabel.CONTRACT.value}), (e:{NodeLabel.EXCEPTION.value})
        WHERE e.contract_id = k.id
        MERGE (k)-[r:{RelationshipType.HAS_EXCEPTION.value}]->(e)
        RETURN count(r) AS cnt
        """
        res = self.client.execute_query(q_contract_exception)
        counts[f"Contract_{RelationshipType.HAS_EXCEPTION.value}"] = res[0]["cnt"] if res else 0

        # 5. Exception -> Approval (and reverse APPROVES)
        q_exception_approval = f"""
        MATCH (e:{NodeLabel.EXCEPTION.value}), (a:{NodeLabel.APPROVAL.value})
        WHERE a.exception_id = e.id
        MERGE (e)-[r1:{RelationshipType.HAS_APPROVAL.value}]->(a)
        MERGE (a)-[r2:{RelationshipType.APPROVES.value}]->(e)
        RETURN count(r1) AS cnt
        """
        res = self.client.execute_query(q_exception_approval)
        counts[RelationshipType.HAS_APPROVAL.value] = res[0]["cnt"] if res else 0
        counts[RelationshipType.APPROVES.value] = res[0]["cnt"] if res else 0

        # 6. Customer -> Invoice (HAS_INVOICE and reverse BILLED_TO)
        q_cust_invoice = f"""
        MATCH (c:{NodeLabel.CUSTOMER.value}), (i:{NodeLabel.INVOICE.value})
        WHERE i.customer_id = c.id
        MERGE (c)-[r1:{RelationshipType.HAS_INVOICE.value}]->(i)
        MERGE (i)-[r2:{RelationshipType.BILLED_TO.value}]->(c)
        RETURN count(r1) AS cnt
        """
        res = self.client.execute_query(q_cust_invoice)
        counts[RelationshipType.HAS_INVOICE.value] = res[0]["cnt"] if res else 0
        counts[RelationshipType.BILLED_TO.value] = res[0]["cnt"] if res else 0

        # 7. Invoice -> Contract (GOVERNED_BY, only when invoice.contract_id is not null)
        q_invoice_contract = f"""
        MATCH (i:{NodeLabel.INVOICE.value}), (k:{NodeLabel.CONTRACT.value})
        WHERE i.contract_id IS NOT NULL AND i.contract_id = k.id
        MERGE (i)-[r:{RelationshipType.GOVERNED_BY.value}]->(k)
        RETURN count(r) AS cnt
        """
        res = self.client.execute_query(q_invoice_contract)
        counts[RelationshipType.GOVERNED_BY.value] = res[0]["cnt"] if res else 0

        # 8. Invoice -> Exception (HAS_EXCEPTION, only when invoice.exception_id is not null)
        q_invoice_exception = f"""
        MATCH (i:{NodeLabel.INVOICE.value}), (e:{NodeLabel.EXCEPTION.value})
        WHERE i.exception_id IS NOT NULL AND i.exception_id = e.id
        MERGE (i)-[r:{RelationshipType.HAS_EXCEPTION.value}]->(e)
        RETURN count(r) AS cnt
        """
        res = self.client.execute_query(q_invoice_exception)
        counts[f"Invoice_{RelationshipType.HAS_EXCEPTION.value}"] = res[0]["cnt"] if res else 0

        # 9. Source Node -> Evidence (HAS_EVIDENCE and reverse EVIDENCE_FOR)
        # In Stage 12, evidence.source_id references Contract, Amendment, SOW, or Approval.
        q_evidence_links = f"""
        MATCH (e:{NodeLabel.EVIDENCE.value})
        MATCH (target)
        WHERE target.id = e.source_id
        MERGE (target)-[r1:{RelationshipType.HAS_EVIDENCE.value}]->(e)
        MERGE (e)-[r2:{RelationshipType.EVIDENCE_FOR.value}]->(target)
        RETURN count(r1) AS cnt
        """
        res = self.client.execute_query(q_evidence_links)
        counts[RelationshipType.HAS_EVIDENCE.value] = res[0]["cnt"] if res else 0
        counts[RelationshipType.EVIDENCE_FOR.value] = res[0]["cnt"] if res else 0

        return counts

    # -------------------------------------------------------------------------
    # Full Deterministic Seed Ingestion Pipeline
    # -------------------------------------------------------------------------

    def load_seed_data(self, init_schema: bool = True, clear_existing: bool = False) -> SeedLoadReport:
        """Run the complete deterministic seed load pipeline.

        Args:
            init_schema: Whether to ensure constraints and indexes exist.
            clear_existing: Whether to clear existing graph nodes before loading.
        """
        report = SeedLoadReport()
        try:
            if init_schema:
                logger.info("Initializing Neo4j graph schema constraints and indexes...")
                self.client.initialize_schema()

            if clear_existing:
                logger.info("Clearing existing graph data...")
                self.client.clear_database()

            # Load nodes
            logger.info("Loading domain nodes into Neo4j...")
            c_cnt = self.load_customers()
            k_cnt = self.load_contracts()
            a_cnt = self.load_amendments()
            s_cnt = self.load_sows()
            e_cnt = self.load_exceptions()
            ap_cnt = self.load_approvals()
            i_cnt = self.load_invoices()
            ev_cnt = self.load_evidence()

            report.nodes_loaded = {
                NodeLabel.CUSTOMER.value: c_cnt,
                NodeLabel.CONTRACT.value: k_cnt,
                NodeLabel.AMENDMENT.value: a_cnt,
                NodeLabel.SOW.value: s_cnt,
                NodeLabel.EXCEPTION.value: e_cnt,
                NodeLabel.APPROVAL.value: ap_cnt,
                NodeLabel.INVOICE.value: i_cnt,
                NodeLabel.EVIDENCE.value: ev_cnt,
            }
            report.total_nodes = sum(report.nodes_loaded.values())

            # Load relationships
            logger.info("Creating graph relationships...")
            report.relationships_loaded = self.create_relationships()
            report.total_relationships = sum(report.relationships_loaded.values())

            logger.info(
                "Successfully loaded %d nodes and %d relationships into Neo4j",
                report.total_nodes,
                report.total_relationships,
            )

        except Exception as exc:
            logger.exception("Error loading seed data into Neo4j: %s", exc)
            report.errors.append(str(exc))

        return report


def load_seed_lineages(data_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Build graph traversal lineage representations directly from seed records.
    
    Enables deterministic offline investigation and UI testing when live Neo4j
    is unavailable.
    """
    resolved_dir = data_dir or find_data_dir()
    seed_dir = resolved_dir / "seed"

    def read_seed(name: str) -> dict[str, dict[str, Any]]:
        path = seed_dir / name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
            return {item["id"]: item for item in items}

    customers = read_seed("customers.json")
    contracts = read_seed("contracts.json")
    amendments = read_seed("amendments.json")
    sows = read_seed("sows.json")
    exceptions = read_seed("exceptions.json")
    approvals = read_seed("approvals.json")
    invoices = read_seed("invoices.json")
    evidence = read_seed("evidence.json")

    lineages: dict[str, dict[str, Any]] = {}

    for inv_id, inv in invoices.items():
        cid = inv.get("customer_id")
        kid = inv.get("contract_id")
        eid = inv.get("exception_id")

        cust_node = customers.get(cid) if cid else None
        contract_node = contracts.get(kid) if kid else None
        exception_node = exceptions.get(eid) if eid else None

        approval_node = None
        if exception_node:
            for apr in approvals.values():
                if apr.get("exception_id") == exception_node["id"]:
                    approval_node = apr
                    break

        linked_amendments = []
        linked_sows = []
        if contract_node:
            linked_amendments = [
                a for a in amendments.values() if a.get("contract_id") == contract_node["id"]
            ]
            linked_sows = [
                s for s in sows.values() if s.get("contract_id") == contract_node["id"]
            ]

        active_ids = {
            x["id"]
            for x in [contract_node, exception_node, approval_node, *linked_amendments, *linked_sows]
            if x is not None
        }
        linked_evidence = [ev for ev in evidence.values() if ev.get("source_id") in active_ids]

        lineages[inv_id] = {
            "invoice": inv,
            "customer": cust_node,
            "contract": contract_node,
            "exception": exception_node,
            "approval": approval_node,
            "amendments": linked_amendments,
            "sows": linked_sows,
            "evidence": linked_evidence,
        }

    return lineages


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    client = Neo4jClient()
    if not client.verify_connectivity():
        print(f"ERROR: Cannot connect to Neo4j at {client.uri}. Is Neo4j running?", file=sys.stderr)
        sys.exit(1)

    loader = SeedLoader(client)
    res = loader.load_seed_data(init_schema=True, clear_existing=True)
    print("Seed Load Result:")
    print("  Nodes:", res.nodes_loaded)
    print("  Relationships:", res.relationships_loaded)
    if res.errors:
        print("  Errors:", res.errors, file=sys.stderr)
        sys.exit(1)
    print("SUCCESS: Stage 12 simulated dataset loaded into Neo4j.")
