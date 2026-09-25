"""Evaluation-Only Adaptive Agent Model and Adapter (Stage 18.5).

Implements an adaptive agent (AdaptiveAgentModel) that dynamically inspects
investigation state observations to:
- decide what information is missing
- select the next relevant tool
- stop early when variance is explained, rejected, or unanchored
- avoid tools that are no longer necessary (e.g. SOWs when only rate amendments apply, or amendments when SOW milestone governs)
- recover from branching, missing, and conflicting evidence paths

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

from app.agent.base_model import AgentModel
from app.agent.loop import InvestigationAgent
from app.agent.models import AgentAction, AgentState
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationEventType
from evaluation.adapters.base import BaseEvaluationAdapter
from evaluation.dataset import BenchmarkCase
from evaluation.metrics import compute_evidence_recall
from evaluation.schemas import CaseResult


class AdaptiveAgentModel(AgentModel):
    """Dynamic, state-adaptive agent decision model for Stage 18.5 evaluation.

    Inspects accumulated observations to decide the next evidentiary query,
    skipping irrelevant branches and stopping early when sufficient or decisive
    evidence (e.g. base match, missing contract, formal rejection, conflicting amendments)
    has been discovered.
    """

    def __init__(self) -> None:
        self.model_name = "AdaptiveAgentModel"
        self.provider = "adaptive_evaluation"

    def decide_next_action(
        self,
        state: AgentState,
        available_tools: list[str],
    ) -> AgentAction:
        prior_calls = set(state.tool_calls)

        # 1. Invoice Discovery
        if state.invoice is None:
            return AgentAction(
                action="get_invoice",
                arguments={"invoice_id": state.invoice_id},
                reason="Inspect invoice details to identify billed amount, customer, and contract reference",
            )

        inv = state.invoice
        amount = float(inv.get("amount", 0.0))
        contract_id = inv.get("contract_id")
        product_code = str(inv.get("product_code", "")).upper()
        has_exception = bool(
            state.exception
            or inv.get("exception_id")
            or state.exception_id
        )
        exception_id = (
            state.exception.get("id")
            if state.exception
            else inv.get("exception_id") or state.exception_id
        )

        # 2. Governing Contract Discovery
        if contract_id and state.contract is None and "find_contract" not in prior_calls:
            return AgentAction(
                action="find_contract",
                arguments={"contract_id": contract_id},
                reason=f"Retrieve terms and validity for governing contract '{contract_id}'",
            )

        # 3. Adaptive Branch: Missing Governing Contract -> Early Exit
        # If contract was queried but returned None, the transaction is unanchored.
        if "find_contract" in prior_calls and state.contract is None:
            return AgentAction(
                action="validate_investigation",
                arguments={},
                reason="Governing contract is absent in the graph; transaction cannot be validated under contractual terms",
            )

        # 4. Adaptive Branch: Direct Standard Rate Match -> Early Exit
        # If no exception exists on the invoice:
        if state.contract is not None and not has_exception:
            if "get_related_evidence" not in prior_calls:
                return AgentAction(
                    action="get_related_evidence",
                    arguments={"source_ids": [state.contract["id"]]},
                    reason=f"Retrieve base contract terms for '{state.contract['id']}' to verify standard rate",
                )
            return AgentAction(
                action="validate_investigation",
                arguments={},
                reason="Billed amount matches base contract standard rate; no variance exception requires investigation",
            )

        # 5. Prioritize Checking Approvals for Exceptions
        if exception_id and "find_approvals" not in prior_calls:
            return AgentAction(
                action="find_approvals",
                arguments={"exception_id": exception_id},
                reason=f"Check approval authority on file for exception '{exception_id}'",
            )

        # 6. Adaptive Branch: Formal Executive Rejection -> Early Exit
        # If approval is explicitly REJECTED, the variance is unauthorized regardless of amendments.
        if state.approval and state.approval.get("status") == "REJECTED":
            if "get_related_evidence" not in prior_calls:
                return AgentAction(
                    action="get_related_evidence",
                    arguments={"source_ids": [state.approval["id"]]},
                    reason=f"Retrieve rejection memo evidence for '{state.approval['id']}'",
                )
            return AgentAction(
                action="validate_investigation",
                arguments={},
                reason="Operational approval is explicitly REJECTED on file; variance cannot be authorized",
            )

        # 7. Governing Amendments & SOW Discovery
        if state.contract is not None:
            cid = state.contract["id"]

            if "get_contract_amendments" not in prior_calls:
                return AgentAction(
                    action="get_contract_amendments",
                    arguments={"contract_id": cid},
                    reason=f"Discover executed amendments for contract '{cid}' to verify authorized rates",
                )

            # 8. Adaptive Branch: Conflicting Concurrent Amendments -> Early Escalation
            # If competing active amendments are detected, conflict is irreconcilable; skip SOWs.
            if len(state.amendments) >= 2:
                active_amds = [a for a in state.amendments if a.get("status", "ACTIVE") == "ACTIVE"]
                if len(active_amds) >= 2:
                    if "get_related_evidence" not in prior_calls:
                        src_ids = [state.contract["id"]] + [a["id"] for a in active_amds if a.get("id")]
                        return AgentAction(
                            action="get_related_evidence",
                            arguments={"source_ids": src_ids},
                            reason="Retrieve evidentiary clauses for concurrent conflicting amendments",
                        )
                    return AgentAction(
                        action="validate_investigation",
                        arguments={},
                        reason="Concurrent contradictory amendments detected; escalate directly to deterministic validation for human review",
                    )

            # 9. Adaptive Branch: Amendment + Approval Fully Satisfy Variance -> Skip SOWs
            # If an amendment is present and an approval is active for general support, SOWs are unnecessary
            # However, if deliverable/milestone/platform scope is referenced, query SOWs
            requires_sows = (
                "AI" in product_code
                or "CONSULTING" in product_code
                or "DELIVERABLE" in str(state.exception or {}).upper()
            )
            has_satisfied_amendment = (
                state.approval is not None
                and state.approval.get("status") == "APPROVED"
                and len(state.amendments) >= 1
                and not requires_sows
            )
            if not has_satisfied_amendment and "get_sows" not in prior_calls:
                return AgentAction(
                    action="get_sows",
                    arguments={"contract_id": cid},
                    reason=f"Check for Statements of Work (SOWs) under contract '{cid}'",
                )

        # 9. Evidence Retrieval for Active Entities
        if "get_related_evidence" not in prior_calls:
            source_ids: list[str] = []
            if state.contract and state.contract.get("id"):
                source_ids.append(state.contract["id"])
            for amd in state.amendments:
                if amd.get("id"):
                    source_ids.append(amd["id"])
            for sow in state.sows:
                if sow.get("id"):
                    source_ids.append(sow["id"])
            if state.approval and state.approval.get("id"):
                source_ids.append(state.approval["id"])
            if state.exception and state.exception.get("id"):
                source_ids.append(state.exception["id"])

            if source_ids:
                return AgentAction(
                    action="get_related_evidence",
                    arguments={"source_ids": source_ids},
                    reason=f"Retrieve supporting evidence clauses for discovered entities: {source_ids}",
                )

        # 10. Conclude and Validate
        return AgentAction(
            action="validate_investigation",
            arguments={},
            reason="Investigation context gathered; hand off to authoritative deterministic validation engine",
        )


class AdaptiveAgentAdapter(BaseEvaluationAdapter):
    """Adapter for evaluating AdaptiveAgentModel against benchmark and branching suites."""

    def __init__(self, max_steps: int = 10) -> None:
        super().__init__(
            baseline_name="adaptive_baseline",
            model_provider="evaluation_adaptive",
            model_name="AdaptiveAgentModel",
            configuration={"max_steps": max_steps, "adaptive": True},
        )
        self.max_steps = max_steps

    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        lineage_repo = InMemoryLineageRepository(lineage_store)
        tool_registry = get_default_tool_registry()

        model = AdaptiveAgentModel()
        agent = InvestigationAgent(
            lineage_repo=lineage_repo,
            model=model,
            tool_registry=tool_registry,
            max_steps=self.max_steps,
        )
        service = InvestigationService(
            repository=InMemoryInvestigationRepository(),
            lineage_repository=lineage_repo,
            agent=agent,
        )

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

        # Count validation calls
        validation_calls = sum(
            1 for e in all_events
            if e.event_type == InvestigationEventType.TOOL_CALL
            and (
                (e.metadata and e.metadata.get("tool") == "validate_investigation")
                or (e.metadata and e.metadata.get("action") == "validate_investigation")
            )
        )
        if validation_calls == 0 and actual_status not in ("FAILED", "QUEUED", "INVESTIGATING"):
            validation_calls = 1

        # Collect retrieved evidence IDs
        cited_ids = list(inv.cited_evidence_ids or [])
        retrieved_ids_set = set(cited_ids)
        for e in all_events:
            if e.metadata and "evidence" in e.metadata:
                ev_items = e.metadata["evidence"]
                if isinstance(ev_items, list):
                    for item in ev_items:
                        if isinstance(item, dict) and "id" in item:
                            retrieved_ids_set.add(item["id"])
        retrieved_ids = list(retrieved_ids_set)

        req_count, ret_count, recall = compute_evidence_recall(
            required_ids=case.relevant_evidence_ids,
            retrieved_ids=retrieved_ids or cited_ids,
        )

        # Count executed tools
        executed_tool_names = [
            e.metadata.get("tool") or e.metadata.get("action")
            for e in all_events
            if e.event_type == InvestigationEventType.TOOL_CALL and e.metadata
        ]

        # Calculate unnecessary tool calls based on case definition
        unnecessary_called = sum(
            1 for t in executed_tool_names
            if t in getattr(case, "unnecessary_tool_names", [])
        )

        # Recovery metric: did it branch and terminate with correct outcome in <= 5 steps without unnecessary calls?
        is_branching = getattr(case, "branching_type", None) is not None
        recovery_success = None
        if is_branching:
            recovery_success = status_match and (unnecessary_called == 0) and (metrics.get("total_agent_steps", 0) <= 5)

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
            validation_calls=validation_calls,
            unnecessary_tool_calls=unnecessary_called,
            recovery_success=recovery_success,
            duration_ms=metrics.get("investigation_duration_ms", duration_ms),
        )
