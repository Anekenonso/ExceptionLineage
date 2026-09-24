"""Agent model interface and deterministic decision models for ExceptionLineage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.agent.models import AgentAction, AgentState


class AgentModel(ABC):
    """Abstract interface for agent intelligence / action selection.

    Allows plugging in either autonomous LLM reasoning or deterministic heuristic models
    without changing the investigation tool orchestration or authority boundaries.
    """

    @abstractmethod
    def decide_next_action(
        self,
        state: AgentState,
        available_tools: list[str],
    ) -> AgentAction:
        """Evaluate current investigation state and select the next tool action."""
        ...


class HeuristicAgentModel(AgentModel):
    """Deterministic, rational investigation model.

    Gathers evidence systematically:
        1. Fetch invoice to discover amount, customer, governing contract, and exception.
        2. Fetch governing contract if referenced.
        3. Fetch associated amendments and SOWs if contract exists.
        4. Fetch approvals if an exception was identified.
        5. Fetch evidence citations for all active contractual entities.
        6. Proceed to deterministic validation.
    """

    def decide_next_action(
        self,
        state: AgentState,
        available_tools: list[str],
    ) -> AgentAction:
        # 1. Invoice
        if state.invoice is None:
            return AgentAction(
                action="get_invoice",
                arguments={"invoice_id": state.invoice_id},
                reason="Retrieve invoice details to identify billed amount, customer, and governing contract link",
            )

        # 2. Contract
        contract_id = state.invoice.get("contract_id")
        if contract_id and state.contract is None and "find_contract" not in state.tool_calls:
            return AgentAction(
                action="find_contract",
                arguments={"contract_id": contract_id},
                reason=f"Retrieve terms and validity for governing contract '{contract_id}'",
            )

        # 3. Amendments & SOWs (if contract exists)
        if state.contract is not None:
            cid = state.contract["id"]
            if "get_contract_amendments" not in state.tool_calls:
                return AgentAction(
                    action="get_contract_amendments",
                    arguments={"contract_id": cid},
                    reason=f"Discover executed amendments for contract '{cid}' to verify authorized rates",
                )
            if "get_sows" not in state.tool_calls:
                return AgentAction(
                    action="get_sows",
                    arguments={"contract_id": cid},
                    reason=f"Discover Statements of Work (SOWs) for contract '{cid}' to verify deliverable scope",
                )

        # 4. Approvals (if exception exists)
        exception_id = (
            state.exception.get("id")
            if state.exception
            else state.invoice.get("exception_id") or state.exception_id
        )
        if exception_id and "find_approvals" not in state.tool_calls:
            return AgentAction(
                action="find_approvals",
                arguments={"exception_id": exception_id},
                reason=f"Check for executive or managerial approval on file for exception '{exception_id}'",
            )

        # 5. Evidentiary records
        if "get_related_evidence" not in state.tool_calls:
            source_ids: list[str] = []
            if state.contract:
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
                    reason=f"Retrieve supporting document clauses and citations for sources: {source_ids}",
                )

        # 6. Conclude evidence gathering -> Validate
        return AgentAction(
            action="validate_investigation",
            arguments={},
            reason="All relevant contractual evidence gathered; invoke authoritative deterministic validation engine",
        )


class ScriptedAgentModel(AgentModel):
    """Test model executing an explicit sequence of actions."""

    def __init__(self, actions: list[AgentAction]) -> None:
        self.actions = list(actions)
        self.step_index = 0

    def decide_next_action(
        self,
        state: AgentState,
        available_tools: list[str],
    ) -> AgentAction:
        if self.step_index < len(self.actions):
            action = self.actions[self.step_index]
            self.step_index += 1
            return action
        return AgentAction(
            action="validate_investigation",
            reason="Prescribed test script complete",
        )
