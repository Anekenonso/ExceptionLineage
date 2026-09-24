"""Baseline B: Heuristic Agent Model Adapter (Stage 18).

Evaluates the rule-based, deterministic HeuristicAgentModel within the controlled
agent loop and investigation service.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

# Ensure apps/api is in sys.path
api_dir = Path(__file__).resolve().parent.parent.parent / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.agent.base_model import HeuristicAgentModel
from app.agent.loop import InvestigationAgent
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationEventType
from evaluation.adapters.base import BaseEvaluationAdapter
from evaluation.dataset import BenchmarkCase
from evaluation.metrics import compute_evidence_recall
from evaluation.schemas import CaseResult


class HeuristicAgentAdapter(BaseEvaluationAdapter):
    """Adapter for Baseline B: HeuristicAgentModel investigation."""

    def __init__(self, max_steps: int = 10) -> None:
        super().__init__(
            baseline_name="heuristic_baseline",
            model_provider="heuristic",
            model_name="HeuristicAgentModel",
            configuration={
                "description": "Deterministic rational investigation model",
                "max_steps": max_steps,
                "tool_registry": [
                    "get_invoice",
                    "find_contract",
                    "get_contract_amendments",
                    "get_sows",
                    "find_approvals",
                    "get_related_evidence",
                    "validate_investigation",
                ],
            },
        )
        self.max_steps = max_steps

    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        lineage_repo = InMemoryLineageRepository(lineage_store)
        tool_registry = get_default_tool_registry()

        model = HeuristicAgentModel()
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
        try:
            inv = service.run_investigation(
                invoice_id=case.invoice_id,
                exception_id=case.exception_id,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            actual_status = inv.status.value
            status_match = actual_status == case.expected_status

            metrics = inv.agent_metrics or {}
            all_events = service.get_all_events(inv.id)

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

            # Extract evidence gathered
            cited_ids = list(inv.cited_evidence_ids or [])
            # Also extract any evidence retrieved during tool execution from event metadata
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

            termination_reason = (
                metrics.get("termination_reason")
                or inv.failure_reason
                or "VALIDATION_COMPLETED"
            )

            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status=actual_status,
                status_match=status_match,
                termination_reason=termination_reason,
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
                malformed_actions=metrics.get("malformed_actions", 0),
                unknown_tools=metrics.get("unknown_tool_calls", 0),
                invalid_arguments=metrics.get("invalid_argument_calls", 0),
                tool_errors=metrics.get("tool_errors", 0),
                llm_errors=0,
                timeouts=0,
                retries=0,
                duration_ms=metrics.get("investigation_duration_ms", duration_ms),
                llm_calls=0,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status="FAILED",
                status_match=False,
                error=f"HeuristicAgentAdapter execution failed: {exc}",
                duration_ms=duration_ms,
            )
