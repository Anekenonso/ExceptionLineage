"""System Under Evaluation: LLM Decision Model Adapter (Stage 18).

Evaluates the real LLM decision layer (LLMDecisionModel) within the controlled
agent loop, testing autonomous tool selection, evidence gathering, and safe handoff
to deterministic validation.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure apps/api is in sys.path
api_dir = Path(__file__).resolve().parent.parent.parent / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

import httpx

from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationEventType
from evaluation.adapters.base import BaseEvaluationAdapter
from evaluation.dataset import BenchmarkCase
from evaluation.metrics import compute_evidence_recall
from evaluation.schemas import CaseResult, EvaluationRun


def create_deterministic_mock_llm_client() -> httpx.Client:
    """Create a mock httpx.Client that dynamically simulates an intelligent LLM.

    Inspects the prompt state and returns rational tool actions for benchmark evaluation
    without requiring external network or API keys.
    """
    def handle_request(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        messages = body.get("messages", [])
        user_msg = messages[-1]["content"] if messages else ""

        # Parse state from prompt
        action_name = "validate_investigation"
        args: dict[str, Any] = {}
        reason = "Validation handoff"

        if "CURRENT INVESTIGATION STATE:" in user_msg:
            try:
                state_json_str = user_msg.split("CURRENT INVESTIGATION STATE:\n", 1)[1].split("\n\nChoose", 1)[0]
                state_dict = json.loads(state_json_str)
                invoice_id = state_dict.get("invoice_id")
                prior_calls = state_dict.get("prior_tool_calls", [])
                discovered = state_dict.get("discovered_entities", {})

                if "get_invoice" not in prior_calls:
                    action_name = "get_invoice"
                    args = {"invoice_id": invoice_id}
                    reason = "Inspect invoice details and identify governing contract"
                elif invoice_id == "INV-1007":
                    # Case 007: No contract exists
                    action_name = "validate_investigation"
                    args = {}
                    reason = "No governing contract on record; proceed to deterministic validation"
                elif "find_contract" not in prior_calls:
                    contract_id = "CTR-002" if invoice_id == "INV-1008" else "CTR-001"
                    action_name = "find_contract"
                    args = {"contract_id": contract_id}
                    reason = "Retrieve governing contract terms"
                elif "get_contract_amendments" not in prior_calls:
                    contract_id = "CTR-002" if invoice_id == "INV-1008" else "CTR-001"
                    action_name = "get_contract_amendments"
                    args = {"contract_id": contract_id}
                    reason = "Discover executed contract amendments"
                elif "get_sows" not in prior_calls:
                    contract_id = "CTR-002" if invoice_id == "INV-1008" else "CTR-001"
                    action_name = "get_sows"
                    args = {"contract_id": contract_id}
                    reason = "Discover Statements of Work"
                elif "find_approvals" not in prior_calls:
                    exc_id = state_dict.get("exception_id") or "EX-001"
                    action_name = "find_approvals"
                    args = {"exception_id": exc_id}
                    reason = "Check for operational approvals on file"
                elif "get_related_evidence" not in prior_calls:
                    contract_id = "CTR-002" if invoice_id == "INV-1008" else "CTR-001"
                    action_name = "get_related_evidence"
                    args = {"source_ids": [contract_id]}
                    reason = "Retrieve contractual evidence clauses"
                else:
                    action_name = "validate_investigation"
                    args = {}
                    reason = "Sufficient evidence discovered; proceed to deterministic validation"
            except Exception:
                action_name = "validate_investigation"
                args = {}
                reason = "Fallback validation request"

        resp_content = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "action": action_name,
                            "arguments": args,
                            "reason": reason,
                        })
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 180,
                "completion_tokens": 35,
                "total_tokens": 215,
            },
        })
        return httpx.Response(status_code=200, content=resp_content.encode("utf-8"), request=request)

    transport = httpx.MockTransport(handle_request)
    return httpx.Client(transport=transport)


class LLMDecisionAdapter(BaseEvaluationAdapter):
    """Adapter for evaluating LLMDecisionModel against the benchmark suite."""

    def __init__(
        self,
        provider: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_steps: int = 10,
        max_retries: int = 1,
        timeout_seconds: float = 30.0,
        mock_client: httpx.Client | None = None,
        is_mock: bool = False,
    ) -> None:
        eff_provider = provider or os.getenv("AGENT_LLM_PROVIDER") or ("mock" if is_mock else "gemini")
        if is_mock:
            default_model = "mock-llm-planner"
        elif eff_provider in ("gemini", "google"):
            default_model = "gemini-2.5-flash"
        else:
            default_model = "gpt-4o-mini"
        eff_model = model_name or os.getenv("AGENT_LLM_MODEL") or default_model
        eff_key = (
            api_key
            or os.getenv("AGENT_LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        super().__init__(
            baseline_name="llm_decision_model",
            model_provider=eff_provider,
            model_name=eff_model,
            configuration={
                "provider": eff_provider,
                "model_name": eff_model,
                "max_steps": max_steps,
                "max_retries": max_retries,
                "timeout_seconds": timeout_seconds,
                "is_mock": is_mock or (mock_client is not None),
            },
        )
        self.api_key = eff_key
        self.base_url = base_url
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.is_mock = is_mock
        self.mock_client = mock_client

    def is_configured(self) -> bool:
        """Return True if model has credentials or is operating in mock mode."""
        return bool(self.api_key or self.is_mock or self.mock_client)

    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        if not self.is_configured():
            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status="UNCONFIGURED",
                status_match=False,
                error="LLM credentials not configured (set AGENT_LLM_API_KEY or use --mock-llm)",
            )

        client = self.mock_client
        if client is None and self.is_mock:
            client = create_deterministic_mock_llm_client()

        lineage_repo = InMemoryLineageRepository(lineage_store)
        tool_registry = get_default_tool_registry()

        model = LLMDecisionModel(
            tool_registry=tool_registry,
            provider=self.model_provider,
            model_name=self.model_name,
            api_key=self.api_key or "mock-key",
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            http_client=client,
        )

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

            termination_reason = (
                metrics.get("termination_reason")
                or inv.failure_reason
                or "VALIDATION_COMPLETED"
            )

            # Check if this case was blocked by an external provider error
            is_prov = False
            prov_cat = None
            prov_http = None
            fail_text = str(inv.failure_reason or "").lower()
            if "429" in fail_text or "rate limit" in fail_text or "quota" in fail_text or "credit" in fail_text:
                is_prov = True
                prov_cat = "provider_quota"
                prov_http = 429
            elif "401" in fail_text or "403" in fail_text or "authentication failed" in fail_text:
                is_prov = True
                prov_cat = "provider_auth"
                prov_http = 401 if "401" in fail_text else 403

            eff_recall = None if is_prov else recall

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
                is_provider_failure=is_prov,
                provider_failure_category=prov_cat,
                provider_http_status=prov_http,
                required_evidence_ids=case.relevant_evidence_ids,
                retrieved_evidence_ids=retrieved_ids,
                cited_evidence_ids=cited_ids,
                required_evidence_count=req_count,
                retrieved_required_evidence_count=ret_count,
                evidence_recall=eff_recall,
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
                llm_errors=metrics.get("llm_failures", 0),
                timeouts=metrics.get("llm_timeouts", 0),
                retries=metrics.get("llm_retries", 0),
                duration_ms=metrics.get("investigation_duration_ms", duration_ms),
                llm_calls=metrics.get("llm_calls", 0),
                prompt_tokens=metrics.get("prompt_tokens"),
                completion_tokens=metrics.get("completion_tokens"),
                total_tokens=metrics.get("total_tokens"),
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            exc_str = str(exc).lower()
            is_prov = False
            prov_cat = None
            prov_http = None
            if "429" in exc_str or "rate limit" in exc_str or "quota" in exc_str or "credit" in exc_str:
                is_prov = True
                prov_cat = "provider_quota"
                prov_http = 429
            elif "401" in exc_str or "403" in exc_str or "auth" in exc_str:
                is_prov = True
                prov_cat = "provider_auth"
                prov_http = 401 if "401" in exc_str else 403

            return CaseResult(
                case_id=case.case_id,
                invoice_id=case.invoice_id,
                scenario_type=case.scenario_type,
                expected_status=case.expected_status,
                actual_status="FAILED",
                status_match=False,
                is_provider_failure=is_prov,
                provider_failure_category=prov_cat,
                provider_http_status=prov_http,
                evidence_recall=None if is_prov else 0.0,
                error=f"LLMDecisionAdapter execution failed: {exc}",
                duration_ms=duration_ms,
            )
