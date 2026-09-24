"""Baseline A: Deterministic Validation Engine Adapter (Stage 18).

Represents the baseline where the necessary evidence and lineage context are
already available, and the deterministic ValidationEngine validates contractual terms.
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

from app.validation.engine import ValidationEngine
from evaluation.adapters.base import BaseEvaluationAdapter
from evaluation.dataset import BenchmarkCase
from evaluation.metrics import compute_evidence_recall
from evaluation.schemas import CaseResult


class DeterministicValidationAdapter(BaseEvaluationAdapter):
    """Adapter for Baseline A: Direct deterministic ValidationEngine execution."""

    def __init__(self) -> None:
        super().__init__(
            baseline_name="deterministic_baseline",
            model_provider="deterministic",
            model_name="ValidationEngine",
            configuration={
                "description": "Authoritative deterministic rule validation engine",
                "rules_active": [
                    "customer_governing_contract",
                    "applicable_amendment",
                    "amendment_effectiveness",
                    "amendment_scope_match",
                    "approval_authorization",
                    "conflicting_authority",
                    "rate_authorization",
                ],
            },
        )
        self.engine = ValidationEngine()

    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        lineage = lineage_store.get(case.invoice_id)
        if lineage is None:
            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status="FAILED",
                status_match=False,
                error=f"Lineage for invoice '{case.invoice_id}' not found in mock store",
            )

        start_time = time.perf_counter()
        try:
            outcome = self.engine.validate(lineage)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            actual_status = outcome.status.value
            status_match = actual_status == case.expected_status

            all_lineage_evidence = [
                e["id"] for e in lineage.get("evidence", []) if isinstance(e, dict) and "id" in e
            ]
            cited_evidence = list(outcome.cited_evidence_ids or [])

            # For deterministic validation, evidence cited in the outcome is the retrieved evidence
            req_count, ret_count, recall = compute_evidence_recall(
                required_ids=case.relevant_evidence_ids,
                retrieved_ids=cited_evidence or all_lineage_evidence,
            )

            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status=actual_status,
                status_match=status_match,
                termination_reason="VALIDATION_APPLIED",
                summary=outcome.summary,
                failure_reason=outcome.failure_reason,
                required_evidence_ids=case.relevant_evidence_ids,
                retrieved_evidence_ids=all_lineage_evidence,
                cited_evidence_ids=cited_evidence,
                required_evidence_count=req_count,
                retrieved_required_evidence_count=ret_count,
                evidence_recall=recall,
                agent_steps=0,
                tool_calls=0,
                successful_tool_calls=0,
                failed_tool_calls=0,
                duplicate_tool_calls=0,
                validation_calls=1,
                malformed_actions=0,
                unknown_tools=0,
                invalid_arguments=0,
                tool_errors=0,
                llm_errors=0,
                timeouts=0,
                retries=0,
                duration_ms=duration_ms,
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
                error=f"ValidationEngine exception: {exc}",
                duration_ms=duration_ms,
            )
