"""Benchmark comparison infrastructure for agent investigation models (Stage 17.5).

Enables quantitative side-by-side comparison between deterministic baselines
(HeuristicAgentModel) and LLM-driven models (LLMDecisionModel) across the 8 benchmark cases.
Captures:
- final_status
- total_agent_steps
- tool_calls
- successful_tool_calls
- failed_tool_calls
- duplicate_tool_calls
- evidence_items_collected
- investigation_duration_ms
- termination_reason
"""

from __future__ import annotations

import json
from typing import Any

from app.agent.base_model import AgentModel, HeuristicAgentModel
from app.agent.loop import InvestigationAgent
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


BENCHMARK_CASES = [
    {"case_id": "CASE-001", "invoice_id": "INV-1001", "exception_id": "EX-001", "expected_status": InvestigationStatus.VERIFIED},
    {"case_id": "CASE-002", "invoice_id": "INV-1002", "exception_id": "EX-002", "expected_status": InvestigationStatus.INSUFFICIENT_EVIDENCE},
    {"case_id": "CASE-003", "invoice_id": "INV-1003", "exception_id": "EX-003", "expected_status": InvestigationStatus.NOT_VERIFIED},
    {"case_id": "CASE-004", "invoice_id": "INV-1004", "exception_id": "EX-004", "expected_status": InvestigationStatus.NOT_VERIFIED},
    {"case_id": "CASE-005", "invoice_id": "INV-1005", "exception_id": "EX-005", "expected_status": InvestigationStatus.NEEDS_REVIEW},
    {"case_id": "CASE-006", "invoice_id": "INV-1006", "exception_id": "EX-006", "expected_status": InvestigationStatus.NOT_VERIFIED},
    {"case_id": "CASE-007", "invoice_id": "INV-1007", "exception_id": "EX-007", "expected_status": InvestigationStatus.INSUFFICIENT_EVIDENCE},
    {"case_id": "CASE-008", "invoice_id": "INV-1008", "exception_id": "EX-008", "expected_status": InvestigationStatus.VERIFIED},
]


def run_benchmark_for_model(
    model: AgentModel,
    model_label: str = "model",
) -> list[dict[str, Any]]:
    """Run all 8 benchmark cases using the given AgentModel and collect standard metrics."""
    lineage_store = build_mock_seed_graph_lineage()
    lineage_repo = InMemoryLineageRepository(lineage_store)
    registry = get_default_tool_registry()

    results: list[dict[str, Any]] = []

    for case in BENCHMARK_CASES:
        agent = InvestigationAgent(
            lineage_repo=lineage_repo,
            model=model,
            tool_registry=registry,
            max_steps=10,
        )
        service = InvestigationService(
            repository=InMemoryInvestigationRepository(),
            lineage_repository=lineage_repo,
            agent=agent,
        )

        inv = service.run_investigation(
            invoice_id=case["invoice_id"],
            exception_id=case["exception_id"],
        )

        metrics = inv.agent_metrics or {}
        record = {
            "model": model_label,
            "case_id": case["case_id"],
            "invoice_id": case["invoice_id"],
            "final_status": inv.status.value,
            "expected_status": case["expected_status"].value,
            "status_match": inv.status == case["expected_status"],
            "total_agent_steps": metrics.get("total_agent_steps", 0),
            "tool_calls": metrics.get("tool_calls", 0),
            "successful_tool_calls": metrics.get("successful_tool_calls", 0),
            "failed_tool_calls": metrics.get("failed_tool_calls", 0),
            "duplicate_tool_calls": metrics.get("duplicate_tool_calls", 0),
            "evidence_items_collected": metrics.get("evidence_items_collected", 0),
            "investigation_duration_ms": metrics.get("investigation_duration_ms", 0.0),
            "termination_reason": metrics.get("termination_reason"),
            "cited_evidence_count": len(inv.cited_evidence_ids or []),
        }
        results.append(record)

    return results


def test_heuristic_baseline_benchmark_metrics():
    """Verify that the baseline HeuristicAgentModel produces a complete, valid metrics profile across all 8 cases."""
    heuristic_model = HeuristicAgentModel()
    results = run_benchmark_for_model(heuristic_model, model_label="heuristic_baseline")

    assert len(results) == 8

    for record in results:
        # 1. 100% agreement with deterministic expected status
        assert record["status_match"] is True, f"Status mismatch for {record['case_id']}"
        # 2. Steps and tool calls bounded within limits
        assert 1 <= record["total_agent_steps"] <= 10
        assert record["tool_calls"] >= 1
        assert record["successful_tool_calls"] >= 1
        assert record["failed_tool_calls"] == 0
        assert record["duplicate_tool_calls"] == 0
        assert record["termination_reason"] == "VALIDATION_REQUESTED"
        assert record["investigation_duration_ms"] >= 0.0

    # Verify summary aggregations are calculable
    total_steps = sum(r["total_agent_steps"] for r in results)
    avg_steps = total_steps / len(results)
    assert avg_steps > 0
