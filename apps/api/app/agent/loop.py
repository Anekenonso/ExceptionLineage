"""Bounded agentic investigation loop for ExceptionLineage."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.agent.base_model import AgentModel, HeuristicAgentModel
from app.agent.models import AgentAction, AgentMetrics, AgentState, ToolResult
from app.agent.tools import ToolRegistry, get_default_tool_registry
from app.agent.exceptions import AgentStepLimitExceededError, AgentToolExecutionError
from app.graph.lineage import LineageRepository
from app.models.enums import InvestigationEventType
from app.validation.context import InvestigationContext

logger = logging.getLogger(__name__)


class InvestigationAgent:
    """Controlled, bounded investigation agent orchestrating evidence discovery.

    Adheres strictly to the architectural law:
        AI handles ambiguity. Code handles authority.

    The agent decides what evidence to collect next through explicit tools, but
    never directly determines contractual correctness or modifies authoritative state.
    """

    def __init__(
        self,
        lineage_repo: LineageRepository,
        model: AgentModel | None = None,
        max_steps: int = 10,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.lineage_repo = lineage_repo
        self.model = model if model is not None else HeuristicAgentModel()
        self.max_steps = max_steps
        self.tool_registry = (
            tool_registry if tool_registry is not None else get_default_tool_registry()
        )

    def execute_investigation(
        self,
        investigation_id: str,
        invoice_id: str,
        exception_id: str | None = None,
        event_recorder: Callable[[InvestigationEventType, str, dict[str, Any] | None], None] | None = None,
    ) -> tuple[InvestigationContext, AgentMetrics]:
        """Run the bounded investigation loop to discover evidence and assemble context."""
        state = AgentState(
            investigation_id=investigation_id,
            invoice_id=invoice_id,
            exception_id=exception_id,
        )
        metrics = AgentMetrics()
        start_time = time.perf_counter()

        seen_calls: set[str] = set()

        while state.steps < self.max_steps and not state.investigation_complete:
            state.steps += 1
            metrics.total_agent_steps = state.steps

            # 1. Decide next action
            available_tools = self.tool_registry.list_tools()
            action: AgentAction = self.model.decide_next_action(state, available_tools)

            call_signature = f"{action.action}:{sorted(action.arguments.items())}"
            if call_signature in seen_calls:
                metrics.duplicate_tool_calls += 1
            seen_calls.add(call_signature)

            # Record agent decision event
            if event_recorder:
                event_recorder(
                    InvestigationEventType.AGENT_DECISION,
                    f"Agent decided action: {action.action}" + (f" ({action.reason})" if action.reason else ""),
                    {
                        "step": state.steps,
                        "action": action.action,
                        "arguments": action.arguments,
                        "reason": action.reason,
                        "model_name": getattr(self.model, "model_name", self.model.__class__.__name__),
                        "model_provider": getattr(self.model, "provider", "heuristic"),
                    },
                )

            # 2. Validate action and tool existence
            tool = self.tool_registry.get(action.action)
            if not tool:
                metrics.failed_tool_calls += 1
                metrics.unknown_tool_calls += 1
                state.observations.append(f"Error: Unknown tool '{action.action}' requested")
                continue

            # Validate tool arguments against schema
            is_valid, validation_err = self.tool_registry.validate_action(action.action, action.arguments)
            if not is_valid:
                metrics.failed_tool_calls += 1
                metrics.invalid_argument_calls += 1
                state.observations.append(f"Error: Invalid arguments for '{action.action}': {validation_err}")
                continue

            # 3. Handle validation completion
            if action.action == "validate_investigation":
                metrics.tool_calls += 1
                metrics.successful_tool_calls += 1
                state.tool_calls.append(action.action)
                state.investigation_complete = True
                if event_recorder:
                    event_recorder(
                        InvestigationEventType.TOOL_CALL,
                        "Concluded evidence discovery and initiated validation",
                        {"step": state.steps, "action": action.action},
                    )
                break

            # 4. Execute tool
            metrics.tool_calls += 1
            try:
                result: ToolResult = tool.execute(action.arguments, self.lineage_repo)
            except Exception as exc:
                metrics.failed_tool_calls += 1
                metrics.tool_errors += 1
                logger.exception("Infrastructure failure during tool execution '%s': %s", action.action, exc)
                raise AgentToolExecutionError(f"Tool '{action.action}' failed: {exc}") from exc

            state.tool_calls.append(action.action)

            # 5. Process tool result
            if result.success:
                metrics.successful_tool_calls += 1
                self._update_state_from_result(state, action.action, result)
            else:
                metrics.failed_tool_calls += 1
                metrics.tool_errors += 1
                state.observations.append(f"Tool '{action.action}' returned error: {result.error}")
                if "not found" in (result.error or "").lower():
                    state.missing_evidence.append(result.error or action.action)

            # Record tool call event in audit trail
            if event_recorder:
                event_recorder(
                    InvestigationEventType.TOOL_CALL,
                    f"Executed tool '{action.action}' - Success: {result.success}",
                    {
                        "step": state.steps,
                        "tool": action.action,
                        "arguments": action.arguments,
                        "success": result.success,
                        "error": result.error,
                        "evidence_count": len(result.evidence),
                    },
                )
                if result.success:
                    rel_map = {
                        "get_invoice": ["[:BILLED_TO]", "[:HAS_EXCEPTION]"],
                        "find_contract": ["[:GOVERNED_BY]"],
                        "get_contract_amendments": ["[:HAS_AMENDMENT]"],
                        "get_sows": ["[:HAS_SOW]"],
                        "find_approvals": ["[:HAS_APPROVAL]"],
                        "get_related_evidence": ["[:HAS_EVIDENCE]"],
                    }
                    ev_ids = [
                        e["id"] for e in (result.evidence or [])
                        if isinstance(e, dict) and "id" in e
                    ]
                    event_recorder(
                        InvestigationEventType.EVIDENCE_FOUND,
                        f"Graph retrieval for '{action.action}' completed: {len(ev_ids)} evidence item(s)",
                        {
                            "step": state.steps,
                            "tool": action.action,
                            "source": "knowledge_graph",
                            "relationships": rel_map.get(action.action, []),
                            "evidence_ids": ev_ids,
                            "record_keys": list(result.data.keys()) if isinstance(result.data, dict) else [],
                        },
                    )

        duration_ms = (time.perf_counter() - start_time) * 1000
        metrics.investigation_duration_ms = round(duration_ms, 2)
        metrics.evidence_items_collected = len(state.evidence)

        # Sync operational LLM metrics if model tracks them
        metrics.llm_calls = getattr(self.model, "llm_calls", 0)
        metrics.llm_failures = getattr(self.model, "llm_failures", 0)
        metrics.llm_retries = getattr(self.model, "llm_retries", 0)
        metrics.malformed_actions = getattr(self.model, "malformed_actions", 0)
        metrics.llm_timeouts = getattr(self.model, "llm_timeouts", 0)
        metrics.prompt_tokens = getattr(self.model, "prompt_tokens", None)
        metrics.completion_tokens = getattr(self.model, "completion_tokens", None)
        metrics.total_tokens = getattr(self.model, "total_tokens", None)

        # Loop exhaustion check
        if not state.investigation_complete and state.steps >= self.max_steps:
            metrics.termination_reason = "AGENT_STEP_LIMIT_EXCEEDED"
            raise AgentStepLimitExceededError(
                f"Agent exceeded maximum allowable steps ({self.max_steps}) without concluding",
                metrics=metrics,
            )

        metrics.termination_reason = "VALIDATION_REQUESTED"

        # Assemble investigation context
        context = self._assemble_context(state)
        return context, metrics

    def _update_state_from_result(self, state: AgentState, tool_name: str, result: ToolResult) -> None:
        """Update accumulated state based on tool data."""
        data = result.data

        if tool_name == "get_invoice":
            state.invoice = data.get("invoice")
            if data.get("customer"):
                state.customer = data.get("customer")
            if data.get("exception"):
                state.exception = data.get("exception")
            state.observations.append(
                f"Invoice {state.invoice_id} retrieved: amount ${state.invoice.get('amount') if state.invoice else 'unknown'}, "
                f"customer {state.invoice.get('customer_id') if state.invoice else 'unknown'}"
            )

        elif tool_name == "find_contract":
            state.contract = data.get("contract")
            if data.get("customer") and not state.customer:
                state.customer = data.get("customer")
            state.observations.append(
                f"Governing contract retrieved: {state.contract.get('id') if state.contract else 'None'}"
            )

        elif tool_name == "get_contract_amendments":
            amendments = data.get("amendments") or []
            state.amendments.extend(amendments)
            state.observations.append(f"Discovered {len(amendments)} contract amendment(s)")

        elif tool_name == "get_sows":
            sows = data.get("sows") or []
            state.sows.extend(sows)
            state.observations.append(f"Discovered {len(sows)} Statement(s) of Work")

        elif tool_name == "find_approvals":
            approvals = data.get("approvals") or []
            if approvals:
                state.approval = approvals[0]
                state.observations.append(f"Located approval {state.approval.get('id')} ({state.approval.get('status')})")
            else:
                state.observations.append("No approval record found on file")

        elif tool_name == "get_related_evidence":
            evidence_items = result.evidence or data.get("evidence") or []
            # Merge unique evidence records by ID
            existing_ids = {e["id"] for e in state.evidence}
            for ev in evidence_items:
                if ev.get("id") and ev["id"] not in existing_ids:
                    state.evidence.append(ev)
                    existing_ids.add(ev["id"])
            state.observations.append(f"Retrieved {len(evidence_items)} supporting evidence records")

    def _assemble_context(self, state: AgentState) -> InvestigationContext:
        """Construct a validated InvestigationContext from gathered agent state."""
        if not state.invoice:
            raise ValueError(f"Investigation context cannot be formed without target invoice '{state.invoice_id}'")

        return InvestigationContext(
            invoice=state.invoice,
            customer=state.customer,
            contract=state.contract,
            exception=state.exception,
            approval=state.approval,
            amendments=state.amendments,
            sows=state.sows,
            evidence=state.evidence,
        )
