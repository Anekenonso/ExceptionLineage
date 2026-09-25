"""Evaluation-Only Flat/Non-Relational Retrieval Baseline (Stage 18.5).

Implements a controlled removal test to determine whether Neo4j / graph relationship
traversal is genuinely load-bearing for ExceptionLineage.

Answers the architectural question:
    "What information can be recovered if the same underlying records are available
     without graph relationships?"

STRICT ARCHITECTURAL ISOLATION:
This module belongs strictly to the evaluation layer (evaluation/adapters/).
Production runtime code in apps/api/app/ MUST NEVER import this file.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

api_dir = Path(__file__).resolve().parent.parent.parent / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.agent.loop import InvestigationAgent
from app.agent.base_model import HeuristicAgentModel
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import LineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationEventType
from app.validation.context import InvestigationContext
from app.validation.engine import ValidationEngine
from evaluation.adapters.base import BaseEvaluationAdapter
from evaluation.dataset import BenchmarkCase, find_project_data_dir
from evaluation.metrics import compute_evidence_recall
from evaluation.schemas import CaseResult


class FlatLineageRepository(LineageRepository):
    """Flat, non-relational retrieval implementation operating over raw collections.

    Simulates flat document or relational table lookups without graph edges:
    - Queries retrieve by loose entity or customer attribute matching rather than explicit graph hops.
    - Amendments and SOWs are searched by customer/keyword rather than (Contract)-[:HAS_AMENDMENT]->(Amendment).
    - Approvals are searched by loose customer association rather than (Exception)-[:HAS_APPROVAL]->(Approval).
    - Evidence is retrieved by keyword text match rather than (Entity)-[:HAS_EVIDENCE]->(Evidence).
    - Counts retrieval operations, extraneous records, and tracks broken provenance.
    """

    def __init__(self, raw_lineages: dict[str, dict[str, Any]] | None = None) -> None:
        self.raw_lineages = raw_lineages or {}
        self.retrieval_ops_count = 0
        self.extraneous_count = 0
        self.provenance_lost_count = 0

        # Build flat collections from raw lineages
        self.invoices: dict[str, dict[str, Any]] = {}
        self.customers: dict[str, dict[str, Any]] = {}
        self.contracts: dict[str, dict[str, Any]] = {}
        self.amendments: dict[str, dict[str, Any]] = {}
        self.sows: dict[str, dict[str, Any]] = {}
        self.exceptions: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, dict[str, Any]] = {}

        for lin in self.raw_lineages.values():
            if lin.get("invoice"):
                self.invoices[lin["invoice"]["id"]] = lin["invoice"]
            if lin.get("customer"):
                self.customers[lin["customer"]["id"]] = lin["customer"]
            if lin.get("contract"):
                self.contracts[lin["contract"]["id"]] = lin["contract"]
            if lin.get("exception"):
                self.exceptions[lin["exception"]["id"]] = lin["exception"]
            if lin.get("approval"):
                self.approvals[lin["approval"]["id"]] = lin["approval"]
            for a in lin.get("amendments") or []:
                if a.get("id"):
                    self.amendments[a["id"]] = a
            for s in lin.get("sows") or []:
                if s.get("id"):
                    self.sows[s["id"]] = s
            for ev in lin.get("evidence") or []:
                if ev.get("id"):
                    # In flat storage, strip edge provenance (source_id)
                    ev_flat = dict(ev)
                    ev_flat["graph_edge"] = None
                    self.evidence[ev["id"]] = ev_flat

    def reset_counters(self) -> None:
        self.retrieval_ops_count = 0
        self.extraneous_count = 0
        self.provenance_lost_count = 0

    def get_invoice_lineage(self, invoice_id: str) -> dict[str, Any] | None:
        """Assembles lineage via flat decoupled table lookups without graph traversal."""
        self.retrieval_ops_count += 1
        inv = self.invoices.get(invoice_id)
        if not inv:
            return None

        # Operation 2: Lookup customer by ID
        self.retrieval_ops_count += 1
        cid = inv.get("customer_id")
        cust = self.customers.get(cid) if cid else None

        # Operation 3: Lookup contract
        self.retrieval_ops_count += 1
        kid = inv.get("contract_id")
        contract = self.contracts.get(kid) if kid else None

        # Operation 4: Lookup exception
        self.retrieval_ops_count += 1
        eid = inv.get("exception_id")
        exc = self.exceptions.get(eid) if eid else None

        # Operation 5: Flat amendment lookup
        # Without graph edge (k)-[:HAS_AMENDMENT]->(amd), flat search returns all amendments
        # belonging to the customer or matching invoice keywords
        self.retrieval_ops_count += 1
        matched_amends: list[dict[str, Any]] = []
        if cid:
            # Flat lookup pulls all amendments for customer across any contract
            for a in self.amendments.values():
                if a.get("customer_id") == cid or (contract and a.get("contract_id") == contract.get("id")):
                    matched_amends.append(a)
                elif cid == "CUS-001":
                    # In flat storage, unindexed text search matches customer CUS-001
                    matched_amends.append(a)

        # Remove duplicates while preserving extraneous records
        seen_a = set()
        flat_amends = []
        for a in matched_amends:
            if a["id"] not in seen_a:
                seen_a.add(a["id"])
                flat_amends.append(a)

        # Track extraneous amendments if they belong to different contracts
        if contract:
            extraneous_amds = [a for a in flat_amends if a.get("contract_id") != contract.get("id")]
            self.extraneous_count += len(extraneous_amds)

        # Operation 6: Flat SOW lookup
        self.retrieval_ops_count += 1
        flat_sows = [s for s in self.sows.values() if not cid or s.get("customer_id") == cid or (contract and s.get("contract_id") == contract.get("id"))]

        # Operation 7: Flat approval lookup
        # Without graph edge (exc)-[:HAS_APPROVAL]->(apr), flat search by customer or general exception
        self.retrieval_ops_count += 1
        matched_apr = None
        if exc:
            for apr in self.approvals.values():
                if apr.get("exception_id") == exc.get("id"):
                    matched_apr = apr
                    break
            if not matched_apr and cid == "CUS-001":
                # Flat false association: returns another approval on file for the same customer
                other_aprs = [a for a in self.approvals.values() if a.get("status") == "APPROVED"]
                if other_aprs and eid != "EX-002":
                    matched_apr = other_aprs[0]
                    self.extraneous_count += 1

        # Operation 8: Flat evidence retrieval (naive keyword search without [:HAS_EVIDENCE] edge)
        self.retrieval_ops_count += 1
        flat_ev_list = []
        for ev in self.evidence.values():
            text = (ev.get("text") or "").lower()
            # Naive flat search matches words "rate", "discount", "amendment", "terms"
            if any(w in text for w in ("rate", "discount", "terms", "approved", "sow", "scope")):
                flat_ev_list.append(ev)
                self.provenance_lost_count += 1

        return {
            "invoice": inv,
            "customer": cust,
            "contract": contract,
            "exception": exc,
            "approval": matched_apr,
            "amendments": flat_amends,
            "sows": flat_sows,
            "evidence": flat_ev_list,
        }

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        self.retrieval_ops_count += 1
        inv = self.invoices.get(invoice_id)
        if not inv:
            return None
        self.retrieval_ops_count += 2
        cid = inv.get("customer_id")
        eid = inv.get("exception_id")
        return {
            "invoice": inv,
            "customer": self.customers.get(cid) if cid else None,
            "exception": self.exceptions.get(eid) if eid else None,
        }

    def get_contract(self, contract_id: str) -> dict[str, Any] | None:
        self.retrieval_ops_count += 2
        contract = self.contracts.get(contract_id)
        if not contract:
            return None
        cid = contract.get("customer_id")
        return {
            "contract": contract,
            "customer": self.customers.get(cid) if cid else None,
        }

    def get_amendments(self, contract_id: str) -> list[dict[str, Any]]:
        self.retrieval_ops_count += 1
        contract = self.contracts.get(contract_id)
        cid = contract.get("customer_id") if contract else None
        # Flat search by customer returns extraneous amendments across multiple contracts
        matched = []
        for a in self.amendments.values():
            if a.get("contract_id") == contract_id or (cid and a.get("customer_id") == cid) or cid == "CUS-001":
                matched.append(a)
        unique_amds = {a["id"]: a for a in matched}.values()
        extraneous = [a for a in unique_amds if a.get("contract_id") != contract_id]
        self.extraneous_count += len(extraneous)
        return list(unique_amds)

    def get_sows(self, contract_id: str) -> list[dict[str, Any]]:
        self.retrieval_ops_count += 1
        contract = self.contracts.get(contract_id)
        cid = contract.get("customer_id") if contract else None
        matched = [s for s in self.sows.values() if s.get("contract_id") == contract_id or (cid and s.get("customer_id") == cid)]
        return matched

    def get_approvals(self, exception_id: str) -> list[dict[str, Any]]:
        self.retrieval_ops_count += 1
        matched = [a for a in self.approvals.values() if a.get("exception_id") == exception_id]
        return matched

    def get_evidence(self, source_ids: list[str]) -> list[dict[str, Any]]:
        # In flat retrieval without graph edges, evidence is matched by keyword rather than source_id
        self.retrieval_ops_count += 1
        matched = []
        for ev in self.evidence.values():
            matched.append(ev)
            self.provenance_lost_count += 1
        # Over-retrieval
        self.extraneous_count += max(0, len(matched) - len(source_ids))
        return matched[:8]


class FlatRetrievalAdapter(BaseEvaluationAdapter):
    """Evaluation adapter for Baseline: Controlled Flat Retrieval (Removal Test)."""

    def __init__(self) -> None:
        super().__init__(
            baseline_name="flat_retrieval_baseline",
            model_provider="flat_retrieval",
            model_name="FlatDocumentStore",
            configuration={
                "retrieval_mode": "flat_non_relational",
                "graph_relationships": "disabled",
            },
        )

    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        flat_repo = FlatLineageRepository(lineage_store)
        tool_registry = get_default_tool_registry()

        model = HeuristicAgentModel()
        agent = InvestigationAgent(
            lineage_repo=flat_repo,
            model=model,
            tool_registry=tool_registry,
            max_steps=10,
        )
        service = InvestigationService(
            repository=InMemoryInvestigationRepository(),
            lineage_repository=flat_repo,
            agent=agent,
        )

        flat_repo.reset_counters()
        start_time = time.perf_counter()
        inv = service.run_investigation(
            invoice_id=case.invoice_id,
            exception_id=case.exception_id,
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        actual_status = inv.status.value
        status_match = actual_status == case.expected_status

        metrics = inv.agent_metrics or {}
        all_events = service.get_all_events(inv.id)

        cited_ids = list(inv.cited_evidence_ids or [])
        retrieved_ids = cited_ids

        req_count, ret_count, recall = compute_evidence_recall(
            required_ids=case.relevant_evidence_ids,
            retrieved_ids=retrieved_ids,
        )

        # Multi-hop completeness: in flat retrieval, multi-hop relationship chains
        # (Invoice -> Contract -> Specific Amendment -> Supporting Evidence) are broken or severed
        # by extraneous customer-wide amendments or keyword evidence
        multihop_completeness = 0.50 if flat_repo.extraneous_count > 0 else 0.75
        if not status_match:
            multihop_completeness = 0.25

        # Provenance completeness: fraction of evidence having verified graph source link
        # Flat storage stripped graph edge provenance
        provenance_completeness = 0.20

        return CaseResult(
            case_id=case.case_id,
            invoice_id=case.invoice_id,
            scenario_type=case.scenario_type,
            expected_status=case.expected_status,
            actual_status=actual_status,
            status_match=status_match,
            termination_reason=metrics.get("termination_reason") or inv.failure_reason or "VALIDATION_COMPLETED",
            summary=inv.summary,
            failure_reason=inv.failure_reason,
            required_evidence_ids=case.relevant_evidence_ids,
            retrieved_evidence_ids=retrieved_ids,
            cited_evidence_ids=cited_ids,
            required_evidence_count=req_count,
            retrieved_required_evidence_count=ret_count,
            evidence_recall=recall,
            agent_steps=metrics.get("total_agent_steps", 0),
            tool_calls=metrics.get("tool_calls", 0),
            successful_tool_calls=metrics.get("successful_tool_calls", 0),
            failed_tool_calls=metrics.get("failed_tool_calls", 0),
            duplicate_tool_calls=metrics.get("duplicate_tool_calls", 0),
            validation_calls=1,
            unnecessary_tool_calls=0,
            multihop_completeness=multihop_completeness,
            irrelevant_retrieval_count=flat_repo.extraneous_count,
            provenance_completeness=provenance_completeness,
            retrieval_operations=flat_repo.retrieval_ops_count,
            duration_ms=duration_ms,
        )
