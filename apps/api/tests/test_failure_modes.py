"""Dedicated failure-mode tests for ExceptionLineage (Stage 18).

Verifies the 11 critical failure modes:
1. Unknown tool
2. Missing argument
3. Invalid argument
4. Malformed LLM output
5. LLM timeout
6. Bounded retry
7. Tool failure
8. Missing evidence (MUST NOT become NOT_VERIFIED -> INSUFFICIENT_EVIDENCE)
9. Conflicting amendments (MUST NOT become VERIFIED -> NEEDS_REVIEW)
10. Expired authority (deterministic NOT_VERIFIED)
11. Step-limit exhaustion (safe termination at MAX_AGENT_STEPS)
"""

from __future__ import annotations

import json
from typing import Any
import httpx
import pytest

from app.agent.base_model import ScriptedAgentModel
from app.agent.exceptions import AgentStepLimitExceededError, AgentToolExecutionError
from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.models import AgentAction, AgentState
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage
from tests.test_llm_model import create_mock_transport


@pytest.fixture
def lineage_store():
    return build_mock_seed_graph_lineage()


@pytest.fixture
def lineage_repo(lineage_store):
    return InMemoryLineageRepository(lineage_store)


@pytest.fixture
def tool_registry():
    return get_default_tool_registry()


# ==============================================================================
# Failure Mode 1: Unknown Tool
# ==============================================================================


def test_failure_mode_1_unknown_tool(lineage_repo, tool_registry):
    """When an agent model requests an unknown tool, it must not crash the service;

    it must increment unknown_tools/failed_tool_calls and allow the agent to recover.
    """
    actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="arbitrary_hacker_tool", arguments={"payload": "drop"}),
        AgentAction(action="validate_investigation", arguments={}),
    ]
    model = ScriptedAgentModel(actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry)

    ctx, metrics = agent.execute_investigation("INVG-FAIL-1", "INV-1001")
    assert metrics.unknown_tool_calls == 1
    assert metrics.failed_tool_calls == 1
    assert metrics.successful_tool_calls == 2
    assert ctx.invoice_id == "INV-1001"


# ==============================================================================
# Failure Mode 2: Missing Argument
# ==============================================================================


def test_failure_mode_2_missing_argument(lineage_repo, tool_registry):
    """When a tool call is missing a required argument, schema validation must reject it;

    the system must record invalid_arguments/failed_tool_calls and continue safely.
    """
    actions = [
        AgentAction(action="get_invoice", arguments={}),  # Missing required invoice_id
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="validate_investigation", arguments={}),
    ]
    model = ScriptedAgentModel(actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry)

    ctx, metrics = agent.execute_investigation("INVG-FAIL-2", "INV-1001")
    assert metrics.invalid_argument_calls == 1
    assert metrics.failed_tool_calls == 1
    assert metrics.successful_tool_calls == 2
    assert ctx.invoice_id == "INV-1001"


# ==============================================================================
# Failure Mode 3: Invalid Argument Type
# ==============================================================================


def test_failure_mode_3_invalid_argument_type(lineage_repo, tool_registry):
    """When a tool call provides an invalid argument type (e.g. integer instead of list of strings),

    schema validation rejects it and records failure without crashing.
    """
    actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="get_related_evidence", arguments={"source_ids": 99999}),  # Wrong type
        AgentAction(action="get_related_evidence", arguments={"source_ids": ["CTR-001"]}),
        AgentAction(action="validate_investigation", arguments={}),
    ]
    model = ScriptedAgentModel(actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry)

    ctx, metrics = agent.execute_investigation("INVG-FAIL-3", "INV-1001")
    assert metrics.invalid_argument_calls == 1
    assert metrics.failed_tool_calls == 1
    assert metrics.successful_tool_calls == 3


# ==============================================================================
# Failure Mode 4: Malformed LLM Output
# ==============================================================================


def test_failure_mode_4_malformed_llm_output(tool_registry):
    """When LLM returns non-JSON or malformed syntax, the adapter detects it and tracks malformed_actions."""
    mock_responses = [
        {"choices": [{"message": {"content": "I am not returning JSON, just conversational text."}}]},
        {"choices": [{"message": {"content": json.dumps({"action": "get_invoice", "arguments": {"invoice_id": "INV-1001"}})}}]},
    ]
    client = create_mock_transport(mock_responses)
    model = LLMDecisionModel(tool_registry=tool_registry, api_key="test-key", max_retries=1, http_client=client)

    state = AgentState(investigation_id="INVG-FAIL-4", invoice_id="INV-1001")
    action = model.decide_next_action(state, tool_registry.list_tools())

    assert action.action == "get_invoice"
    assert model.malformed_actions == 1
    assert model.llm_retries == 1


# ==============================================================================
# Failure Mode 5: LLM Timeout
# ==============================================================================


def test_failure_mode_5_llm_timeout(tool_registry, lineage_repo):
    """When an LLM call times out, it must be caught, recorded in metrics, and transition service to FAILED."""
    client = create_mock_transport([httpx.ReadTimeout("Socket read timed out after 30s")])
    model = LLMDecisionModel(tool_registry=tool_registry, api_key="test-key", timeout_seconds=1.0, http_client=client)

    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry)
    service = InvestigationService(
        repository=InMemoryInvestigationRepository(),
        lineage_repository=lineage_repo,
        agent=agent,
    )

    inv = service.run_investigation("INV-1001")
    assert inv.status == InvestigationStatus.FAILED
    assert "timed out" in (inv.failure_reason or "").lower()


# ==============================================================================
# Failure Mode 6: Bounded Retry
# ==============================================================================


def test_failure_mode_6_bounded_retry(tool_registry):
    """When LLM repeatedly produces invalid responses, it must not retry indefinitely."""
    # Persistently invalid output
    broken_resp = {"choices": [{"message": {"content": "{unparseable json..."}}]}
    client = create_mock_transport([broken_resp, broken_resp, broken_resp])

    model = LLMDecisionModel(tool_registry=tool_registry, api_key="test-key", max_retries=2, http_client=client)
    state = AgentState(investigation_id="INVG-FAIL-6", invoice_id="INV-1001")

    with pytest.raises(AgentToolExecutionError, match="failed to produce a valid tool action"):
        model.decide_next_action(state, tool_registry.list_tools())

    assert model.llm_calls == 3  # Initial + 2 retries
    assert model.llm_retries == 2
    assert model.malformed_actions == 3


# ==============================================================================
# Failure Mode 7: Tool Failure
# ==============================================================================


def test_failure_mode_7_tool_failure(lineage_repo, tool_registry):
    """When a tool encounters an infrastructure exception or returns failure, it is tracked."""
    actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="find_contract", arguments={"contract_id": "CTR-NON-EXISTENT"}),  # Will return success=False
        AgentAction(action="validate_investigation", arguments={}),
    ]
    model = ScriptedAgentModel(actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry)

    ctx, metrics = agent.execute_investigation("INVG-FAIL-7", "INV-1001")
    assert metrics.failed_tool_calls == 1
    assert metrics.tool_errors == 1
    assert metrics.successful_tool_calls == 2


# ==============================================================================
# Failure Mode 8: Missing Evidence (Must NOT become NOT_VERIFIED)
# ==============================================================================


def test_failure_mode_8_missing_evidence_is_insufficient_evidence(lineage_repo):
    """CRITICAL: Missing evidence must not automatically become NOT_VERIFIED.

    In CASE-002, the invoice rate increase requires executive signoff, but no approval exists.
    The system MUST classify this as INSUFFICIENT_EVIDENCE, not NOT_VERIFIED.
    """
    service = InvestigationService(lineage_repository=lineage_repo)
    inv = service.run_investigation("INV-1002", exception_id="EXC-1002")

    assert inv.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert inv.status != InvestigationStatus.NOT_VERIFIED
    assert any(
        r.check_name == "approval_authorization" and r.status.value == "UNKNOWN"
        for r in (inv.validation_results or [])
    )


def test_failure_mode_8_missing_contract_is_insufficient_evidence(lineage_repo):
    """CRITICAL: When governing contract is missing (CASE-007), status must be INSUFFICIENT_EVIDENCE."""
    service = InvestigationService(lineage_repository=lineage_repo)
    inv = service.run_investigation("INV-1007", exception_id="EXC-1007")

    assert inv.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert inv.status != InvestigationStatus.NOT_VERIFIED


# ==============================================================================
# Failure Mode 9: Conflicting Amendments (Must NOT become VERIFIED)
# ==============================================================================


def test_failure_mode_9_conflicting_amendments_is_needs_review(lineage_repo):
    """CRITICAL: Conflicting amendments must never automatically become VERIFIED.

    In CASE-005, two concurrent amendments specify conflicting rates ($11,000 vs $11,500).
    The system MUST classify this as NEEDS_REVIEW, never VERIFIED.
    """
    service = InvestigationService(lineage_repository=lineage_repo)
    inv = service.run_investigation("INV-1005", exception_id="EXC-1005")

    assert inv.status == InvestigationStatus.NEEDS_REVIEW
    assert inv.status != InvestigationStatus.VERIFIED
    assert any(
        r.check_name == "conflicting_authority" and r.status.value == "FAIL"
        for r in (inv.validation_results or [])
    )


# ==============================================================================
# Failure Mode 10: Expired Authority
# ==============================================================================


def test_failure_mode_10_expired_authority_is_not_verified(lineage_repo):
    """When an authorizing amendment has expired before invoice issuance (CASE-003),

    the deterministic engine must reject it as NOT_VERIFIED.
    """
    service = InvestigationService(lineage_repository=lineage_repo)
    inv = service.run_investigation("INV-1003", exception_id="EXC-1003")

    assert inv.status == InvestigationStatus.NOT_VERIFIED
    assert any(
        r.check_name == "amendment_effectiveness" and r.status.value == "FAIL"
        for r in (inv.validation_results or [])
    )


# ==============================================================================
# Failure Mode 11: Step-Limit Exhaustion
# ==============================================================================


def test_failure_mode_11_step_limit_exhaustion_bounds_execution(lineage_repo, tool_registry):
    """When an agent model enters an infinite tool loop without calling validate_investigation,

    the agent loop must terminate at max_steps and the investigation must fail safely.
    """
    infinite_loop_actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="find_contract", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="get_contract_amendments", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="get_sows", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="find_approvals", arguments={"exception_id": "EX-001"}),
        # 6th step triggers limit
        AgentAction(action="get_contract_amendments", arguments={"contract_id": "CTR-001"}),
    ]
    model = ScriptedAgentModel(infinite_loop_actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model, tool_registry=tool_registry, max_steps=5)

    service = InvestigationService(
        repository=InMemoryInvestigationRepository(),
        lineage_repository=lineage_repo,
        agent=agent,
    )

    inv = service.run_investigation("INV-1001")
    assert inv.status == InvestigationStatus.FAILED
    assert inv.failure_reason == "AGENT_STEP_LIMIT_EXCEEDED"
    assert inv.agent_metrics is not None
    assert inv.agent_metrics["total_agent_steps"] == 5
    assert inv.agent_metrics["termination_reason"] == "AGENT_STEP_LIMIT_EXCEEDED"
