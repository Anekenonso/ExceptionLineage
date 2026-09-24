"""Tests for Stage 17 — Controlled Agentic Investigation Loop.

Verifies:
1. Tool contracts and registry isolation.
2. Controlled agent loop bounding (MAX_AGENT_STEPS).
3. Scripted and Heuristic agent models.
4. End-to-end investigation across all 8 benchmark cases (Tests A-H).
5. Audit trail reconstruction (INPUT -> DECISION -> TOOL CALL -> VALIDATION -> OUTCOME).
6. Agent metrics tracking and persistence.
7. Technical failure semantics vs genuine evidence insufficiency.
8. Anti-leakage AST validation for app/agent.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from app.agent.base_model import HeuristicAgentModel, ScriptedAgentModel
from app.agent.exceptions import AgentStepLimitExceededError, AgentToolExecutionError
from app.agent.loop import InvestigationAgent
from app.agent.models import AgentAction, AgentMetrics, AgentState, ToolResult
from app.agent.tools import create_default_tool_registry
from app.agent.tools.amendments import GetContractAmendmentsTool
from app.agent.tools.approvals import FindApprovalsTool
from app.agent.tools.contract import FindContractTool
from app.agent.tools.evidence import GetRelatedEvidenceTool
from app.agent.tools.invoice import GetInvoiceTool
from app.agent.tools.sows import GetSOWsTool
from app.agent.tools.validation import ValidateInvestigationTool
from app.graph.lineage import InMemoryLineageRepository, LineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationEventType, InvestigationStatus


# ==============================================================================
# Helper / Fixtures
# ==============================================================================


from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


def load_benchmark_lineage_repo() -> InMemoryLineageRepository:
    return InMemoryLineageRepository(build_mock_seed_graph_lineage())


# ==============================================================================
# 1. Tool Contract Tests
# ==============================================================================


def test_tool_registry_initialization():
    registry = create_default_tool_registry()
    tools = registry.list_tools()
    expected_tools = [
        "get_invoice",
        "find_contract",
        "get_contract_amendments",
        "get_sows",
        "find_approvals",
        "get_related_evidence",
        "validate_investigation",
    ]
    for t in expected_tools:
        assert t in tools
        tool = registry.get(t)
        assert tool is not None
        assert tool.name == t
        assert len(tool.description) > 0


def test_get_invoice_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = GetInvoiceTool()

    # Missing argument
    res = tool.execute({}, lineage_repo)
    assert not res.success
    assert "invoice_id" in res.error

    # Valid execution
    res = tool.execute({"invoice_id": "INV-1001"}, lineage_repo)
    assert res.success
    assert res.tool_name == "get_invoice"
    assert res.data["invoice"]["id"] == "INV-1001"
    assert res.data["customer"]["id"] == "CUS-001"

    # Missing from graph raises ValueError for clean pipeline failure
    with pytest.raises(ValueError, match="not found in knowledge graph"):
        tool.execute({"invoice_id": "NON-EXISTENT"}, lineage_repo)


def test_find_contract_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = FindContractTool()

    # Missing argument
    res = tool.execute({}, lineage_repo)
    assert not res.success
    assert "contract_id" in res.error

    # Valid execution
    res = tool.execute({"contract_id": "CTR-001"}, lineage_repo)
    assert res.success
    assert res.data["contract"]["id"] == "CTR-001"

    # Non-existent contract returns failure result (genuine missing evidence)
    res = tool.execute({"contract_id": "CTR-UNKNOWN"}, lineage_repo)
    assert not res.success
    assert "not found in knowledge graph" in res.error


def test_get_contract_amendments_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = GetContractAmendmentsTool()

    res = tool.execute({"contract_id": "CTR-001"}, lineage_repo)
    assert res.success
    assert "amendments" in res.data
    assert len(res.data["amendments"]) >= 1


def test_get_sows_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = GetSOWsTool()

    res = tool.execute({"contract_id": "CTR-001"}, lineage_repo)
    assert res.success
    assert "sows" in res.data
    assert len(res.data["sows"]) >= 1


def test_find_approvals_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = FindApprovalsTool()

    res = tool.execute({"exception_id": "EX-001"}, lineage_repo)
    assert res.success
    assert "approvals" in res.data
    assert len(res.data["approvals"]) == 1
    assert res.data["approvals"][0]["id"] == "APR-001"


def test_get_related_evidence_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = GetRelatedEvidenceTool()

    res = tool.execute({"source_ids": ["CTR-001", "AMD-001"]}, lineage_repo)
    assert res.success
    assert "evidence" in res.data
    assert len(res.evidence) >= 1


def test_validate_investigation_tool_contract():
    lineage_repo = load_benchmark_lineage_repo()
    tool = ValidateInvestigationTool()

    res = tool.execute({}, lineage_repo)
    assert res.success
    assert res.data["ready_for_validation"] is True


# ==============================================================================
# 2. Agent Loop Bounded Execution & Error Semantics
# ==============================================================================


def test_agent_loop_exhaustion_transitions_to_failed():
    """Verify that exceeding MAX_AGENT_STEPS transitions to FAILED with AGENT_STEP_LIMIT_EXCEEDED."""
    lineage_repo = load_benchmark_lineage_repo()

    # Scripted model that never calls validate_investigation
    infinite_loop_actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="find_contract", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="get_contract_amendments", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="get_sows", arguments={"contract_id": "CTR-001"}),
        AgentAction(action="find_approvals", arguments={"exception_id": "EX-001"}),
        # 6th action when max_steps=5
        AgentAction(action="get_contract_amendments", arguments={"contract_id": "CTR-001"}),
    ]
    scripted_model = ScriptedAgentModel(infinite_loop_actions)

    agent = InvestigationAgent(
        lineage_repo=lineage_repo,
        model=scripted_model,
        max_steps=5,
    )

    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=lineage_repo,
        agent=agent,
    )

    inv = service.run_investigation("INV-1001")
    assert inv.status == InvestigationStatus.FAILED
    assert inv.failure_reason == "AGENT_STEP_LIMIT_EXCEEDED"

    events = service.get_events(inv.id)
    assert len(events) == 2
    assert events[1].to_state == InvestigationStatus.FAILED


def test_agent_unknown_tool_handled_gracefully():
    """Verify that an unknown tool action does not crash the system, increments failed_tool_calls."""
    lineage_repo = load_benchmark_lineage_repo()

    actions = [
        AgentAction(action="get_invoice", arguments={"invoice_id": "INV-1001"}),
        AgentAction(action="non_existent_tool", arguments={}),
        AgentAction(action="validate_investigation", arguments={}),
    ]
    model = ScriptedAgentModel(actions)
    agent = InvestigationAgent(lineage_repo=lineage_repo, model=model)

    ctx, metrics = agent.execute_investigation("INVG-TEST", "INV-1001")
    assert ctx.invoice_id == "INV-1001"
    assert metrics.failed_tool_calls == 1
    assert metrics.successful_tool_calls == 2


# ==============================================================================
# 3. Test Scenarios: Tests A through H (All 8 Benchmark Cases)
# ==============================================================================


def test_scenario_a_case_001_verified():
    """Test A — CASE-001: Standard verified contract exception investigation."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1001", exception_id="EX-001")
    assert inv.status == InvestigationStatus.VERIFIED
    assert "EV-001" in inv.cited_evidence_ids
    assert inv.agent_metrics is not None
    assert inv.agent_metrics["total_agent_steps"] >= 4
    assert inv.agent_metrics["termination_reason"] == "VALIDATION_REQUESTED"


def test_scenario_b_case_002_missing_approval():
    """Test B — CASE-002: Missing approval evidence leads to INSUFFICIENT_EVIDENCE."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1002", exception_id="EXC-1002")
    assert inv.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert inv.agent_metrics is not None


def test_scenario_c_case_003_expired_amendment():
    """Test C — CASE-003: Expired amendment rejected deterministically -> NOT_VERIFIED."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1003", exception_id="EXC-1003")
    assert inv.status == InvestigationStatus.NOT_VERIFIED


def test_scenario_d_case_004_scope_mismatch():
    """Test D — CASE-004: Product scope mismatch rejected deterministically -> NOT_VERIFIED."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1004", exception_id="EXC-1004")
    assert inv.status == InvestigationStatus.NOT_VERIFIED


def test_scenario_e_case_005_conflicting_amendments():
    """Test E — CASE-005: Competing conflicting amendments -> NEEDS_REVIEW."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1005", exception_id="EXC-1005")
    assert inv.status == InvestigationStatus.NEEDS_REVIEW


def test_scenario_f_case_006_no_authorizing_amendment():
    """Test F — CASE-006: Unauthorized overage without amendment -> NOT_VERIFIED."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1006", exception_id="EXC-1006")
    assert inv.status == InvestigationStatus.NOT_VERIFIED


def test_scenario_g_case_007_no_governing_contract():
    """Test G — CASE-007: Missing governing contract -> INSUFFICIENT_EVIDENCE."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1007", exception_id="EXC-1007")
    assert inv.status == InvestigationStatus.INSUFFICIENT_EVIDENCE


def test_scenario_h_case_008_sow_adjusted_contract():
    """Test H — CASE-008: Valid SOW deliverable adjustment -> VERIFIED."""
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1008", exception_id="EXC-1008")
    assert inv.status == InvestigationStatus.VERIFIED


# ==============================================================================
# 4. Audit Trail Reconstruction
# ==============================================================================


def test_audit_trail_reconstruction_case_001():
    """Verify that an independent technical reviewer can reconstruct:

    INPUT
     ↓
    AGENT DECISION
     ↓
    TOOL CALL
     ↓
    TOOL RESULT / EVIDENCE
     ↓
    VALIDATION
     ↓
    OUTCOME
    """
    lineage_repo = load_benchmark_lineage_repo()
    service = InvestigationService(lineage_repository=lineage_repo)

    inv = service.run_investigation("INV-1001", exception_id="EXC-1001")

    # 1. State transition events (high-level lifecycle)
    lifecycle_events = service.get_events(inv.id, include_agent_events=False)
    assert len(lifecycle_events) == 3
    assert [e.to_state for e in lifecycle_events] == [
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.VALIDATING,
        InvestigationStatus.VERIFIED,
    ]

    # 2. Detailed agent execution audit events
    agent_events = service.get_agent_events(inv.id)
    assert len(agent_events) > 0

    # Ensure decisions and tool calls occurred in alternating/correlated pairs
    decisions = [e for e in agent_events if e.event_type == InvestigationEventType.AGENT_DECISION]
    tool_calls = [e for e in agent_events if e.event_type == InvestigationEventType.TOOL_CALL]

    assert len(decisions) >= 5
    assert len(tool_calls) >= 5

    # Check that tool call events contain structured arguments, success status, and metadata
    for tc in tool_calls:
        assert "tool" in tc.metadata or "action" in tc.metadata
        assert "step" in tc.metadata

    # Check complete combined history
    all_events = service.get_all_events(inv.id)
    assert len(all_events) == len(lifecycle_events) + len(agent_events)


# ==============================================================================
# 5. Anti-Leakage AST Check for app/agent
# ==============================================================================


def test_agent_does_not_import_ground_truth():
    """Verify app/agent AST has zero imports of test datasets or ground truth."""
    agent_dir = Path(__file__).parent.parent / "app" / "agent"
    assert agent_dir.exists(), "app/agent directory not found"

    forbidden_patterns = ["ground_truth", "tests", "data.datasets", "test_"]

    for py_file in agent_dir.rglob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for pattern in forbidden_patterns:
                        assert pattern not in alias.name, (
                            f"Prohibited import '{alias.name}' detected in {py_file}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for pattern in forbidden_patterns:
                    assert pattern not in module, (
                        f"Prohibited from-import '{module}' detected in {py_file}"
                    )
