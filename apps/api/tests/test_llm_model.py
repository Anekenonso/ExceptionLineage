"""Unit tests for LLMDecisionModel adapter and tool schema validation.

Verifies:
1. Successful structured action parsing and execution.
2. Tool schema and argument validation (unexpected args, missing required, wrong types).
3. Bounded retry on malformed JSON / schema violations.
4. Error handling: timeout, auth failure (401), rate limit (429), provider errors.
5. Metrics synchronization with AgentMetrics.
6. End-to-end investigation with mocked LLM decision model.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from app.agent.exceptions import AgentStepLimitExceededError, AgentToolExecutionError
from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.models import AgentAction, AgentState
from app.agent.tools import get_default_tool_registry
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage
from app.graph.lineage import InMemoryLineageRepository


def create_mock_transport(responses: list[dict[str, Any] | Exception]) -> httpx.Client:
    """Create an httpx.Client with a custom transport returning prescribed mock responses."""
    resp_iter = iter(responses)

    def handle_request(request: httpx.Request) -> httpx.Response:
        try:
            item = next(resp_iter)
        except StopIteration:
            item = {"choices": [{"message": {"content": json.dumps({"action": "validate_investigation", "arguments": {}})}}]}

        if isinstance(item, Exception):
            raise item

        status_code = item.get("_status_code", 200)
        body = {k: v for k, v in item.items() if k != "_status_code"}
        return httpx.Response(
            status_code=status_code,
            json=body,
            request=request,
        )

    transport = httpx.MockTransport(handle_request)
    return httpx.Client(transport=transport)


# ==============================================================================
# 1. Structured Action Parsing & Validation
# ==============================================================================


def test_llm_model_valid_structured_action():
    registry = get_default_tool_registry()
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "action": "get_invoice",
                        "arguments": {"invoice_id": "INV-1001"},
                        "reason": "Need to inspect invoice details and customer reference",
                    })
                }
            }
        ],
        "usage": {"prompt_tokens": 150, "completion_tokens": 30, "total_tokens": 180},
    }
    client = create_mock_transport([mock_response])

    model = LLMDecisionModel(
        tool_registry=registry,
        api_key="test-key",
        http_client=client,
    )
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "get_invoice"
    assert action.arguments == {"invoice_id": "INV-1001"}
    assert "Need to inspect" in (action.reason or "")
    assert model.llm_calls == 1
    assert model.prompt_tokens == 150
    assert model.completion_tokens == 30
    assert model.total_tokens == 180


def test_llm_model_valid_action_with_markdown_fences():
    """Verify that model responses wrapped in ```json ... ``` are cleanly extracted."""
    registry = get_default_tool_registry()
    fenced_content = "```json\n" + json.dumps({
        "action": "find_contract",
        "arguments": {"contract_id": "CTR-001"},
        "reason": "Retrieve governing contract terms",
    }) + "\n```"
    mock_response = {
        "choices": [{"message": {"content": fenced_content}}],
    }
    client = create_mock_transport([mock_response])

    model = LLMDecisionModel(
        tool_registry=registry,
        api_key="test-key",
        http_client=client,
    )
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "find_contract"
    assert action.arguments == {"contract_id": "CTR-001"}


def test_llm_model_validate_investigation_action():
    registry = get_default_tool_registry()
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "action": "validate_investigation",
                        "arguments": {},
                        "reason": "All evidence collected",
                    })
                }
            }
        ]
    }
    client = create_mock_transport([mock_response])

    model = LLMDecisionModel(
        tool_registry=registry,
        api_key="test-key",
        http_client=client,
    )
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "validate_investigation"
    assert action.arguments == {}


# ==============================================================================
# 2. Schema Violations & Rejection
# ==============================================================================


def test_llm_model_rejects_unknown_tool():
    registry = get_default_tool_registry()
    # First response: unknown tool
    # Retry response: valid tool
    resp1 = {
        "choices": [{"message": {"content": json.dumps({"action": "drop_database", "arguments": {}})}}]
    }
    resp2 = {
        "choices": [{"message": {"content": json.dumps({"action": "get_invoice", "arguments": {"invoice_id": "INV-1001"}})}}]
    }
    client = create_mock_transport([resp1, resp2])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", max_retries=1, http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "get_invoice"
    assert model.malformed_actions == 1
    assert model.llm_retries == 1
    assert model.llm_calls == 2


def test_llm_model_rejects_missing_required_argument():
    registry = get_default_tool_registry()
    # Missing required 'invoice_id' for get_invoice
    resp1 = {
        "choices": [{"message": {"content": json.dumps({"action": "get_invoice", "arguments": {}})}}]
    }
    resp2 = {
        "choices": [{"message": {"content": json.dumps({"action": "get_invoice", "arguments": {"invoice_id": "INV-1001"}})}}]
    }
    client = create_mock_transport([resp1, resp2])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", max_retries=1, http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "get_invoice"
    assert action.arguments["invoice_id"] == "INV-1001"
    assert model.llm_retries == 1


def test_llm_model_rejects_unexpected_argument():
    registry = get_default_tool_registry()
    # Unexpected argument 'hacked_param'
    resp1 = {
        "choices": [{"message": {"content": json.dumps({
            "action": "get_invoice",
            "arguments": {"invoice_id": "INV-1001", "unexpected_param": "malicious_value"}
        })}}]
    }
    resp2 = {
        "choices": [{"message": {"content": json.dumps({
            "action": "get_invoice",
            "arguments": {"invoice_id": "INV-1001"}
        })}}]
    }
    client = create_mock_transport([resp1, resp2])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", max_retries=1, http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "get_invoice"
    assert "unexpected_param" not in action.arguments
    assert model.llm_retries == 1


def test_llm_model_rejects_wrong_argument_type():
    registry = get_default_tool_registry()
    # source_ids must be a list of strings, not a single integer
    resp1 = {
        "choices": [{"message": {"content": json.dumps({
            "action": "get_related_evidence",
            "arguments": {"source_ids": 12345}
        })}}]
    }
    resp2 = {
        "choices": [{"message": {"content": json.dumps({
            "action": "get_related_evidence",
            "arguments": {"source_ids": ["CTR-001"]}
        })}}]
    }
    client = create_mock_transport([resp1, resp2])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", max_retries=1, http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")
    action = model.decide_next_action(state, registry.list_tools())

    assert action.action == "get_related_evidence"
    assert action.arguments["source_ids"] == ["CTR-001"]


# ==============================================================================
# 3. Bounded Retry & Unrecoverable Failures
# ==============================================================================


def test_llm_model_exhausts_retries_on_persistent_malformed_json():
    registry = get_default_tool_registry()
    # Completely broken JSON across both attempts
    resp1 = {"choices": [{"message": {"content": "I think we should look at the invoice."}}]}
    resp2 = {"choices": [{"message": {"content": "Still not valid JSON: {"}}]}
    client = create_mock_transport([resp1, resp2])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", max_retries=1, http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")

    with pytest.raises(AgentToolExecutionError, match="failed to produce a valid tool action"):
        model.decide_next_action(state, registry.list_tools())

    assert model.malformed_actions == 2
    assert model.llm_calls == 2


def test_llm_model_authentication_failure():
    registry = get_default_tool_registry()
    mock_error_resp = {
        "_status_code": 401,
        "error": {"message": "Invalid API key provided", "type": "invalid_request_error"},
    }
    client = create_mock_transport([mock_error_resp])

    model = LLMDecisionModel(tool_registry=registry, api_key="bad-key", http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")

    with pytest.raises(AgentToolExecutionError, match="authentication failed"):
        model.decide_next_action(state, registry.list_tools())

    assert model.llm_failures == 1


def test_llm_model_rate_limit_failure():
    registry = get_default_tool_registry()
    mock_error_resp = {
        "_status_code": 429,
        "error": {"message": "Rate limit reached", "type": "rate_limit_error"},
    }
    client = create_mock_transport([mock_error_resp])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")

    with pytest.raises(AgentToolExecutionError, match="rate limit reached"):
        model.decide_next_action(state, registry.list_tools())

    assert model.llm_failures == 1


def test_llm_model_timeout_failure():
    registry = get_default_tool_registry()
    client = create_mock_transport([httpx.ReadTimeout("Read operation timed out")])

    model = LLMDecisionModel(tool_registry=registry, api_key="test-key", http_client=client)
    state = AgentState(investigation_id="INVG-1", invoice_id="INV-1001")

    with pytest.raises(AgentToolExecutionError, match="timed out"):
        model.decide_next_action(state, registry.list_tools())

    assert model.llm_failures == 1


# ==============================================================================
# 4. End-to-End Investigation with Mocked LLM Decision Model
# ==============================================================================


def test_end_to_end_investigation_with_mocked_llm():
    """Verify that an investigation agent driven by LLMDecisionModel executes tools,

    updates state, invokes validation, and maps to terminal VERIFIED status.
    """
    lineage_store = build_mock_seed_graph_lineage()
    lineage_repo = InMemoryLineageRepository(lineage_store)
    registry = get_default_tool_registry()

    # Prescribed sequence of LLM responses simulating real reasoning
    llm_responses = [
        {"choices": [{"message": {"content": json.dumps({
            "action": "get_invoice",
            "arguments": {"invoice_id": "INV-1001"},
            "reason": "Identify invoice amount, customer, and governing contract link",
        })}}]},
        {"choices": [{"message": {"content": json.dumps({
            "action": "find_contract",
            "arguments": {"contract_id": "CTR-001"},
            "reason": "Verify governing contract status and validity window",
        })}}]},
        {"choices": [{"message": {"content": json.dumps({
            "action": "get_contract_amendments",
            "arguments": {"contract_id": "CTR-001"},
            "reason": "Check for rate adjustments authorizing the overage",
        })}}]},
        {"choices": [{"message": {"content": json.dumps({
            "action": "find_approvals",
            "arguments": {"exception_id": "EX-001"},
            "reason": "Verify operational approval sign-off for the exception",
        })}}]},
        {"choices": [{"message": {"content": json.dumps({
            "action": "get_related_evidence",
            "arguments": {"source_ids": ["CTR-001", "AMD-001"]},
            "reason": "Retrieve documentary evidence clauses",
        })}}]},
        {"choices": [{"message": {"content": json.dumps({
            "action": "validate_investigation",
            "arguments": {},
            "reason": "Sufficient evidence discovered; proceed to deterministic validation",
        })}}]},
    ]
    client = create_mock_transport(llm_responses)
    llm_model = LLMDecisionModel(
        tool_registry=registry,
        model_name="gpt-4o-mini",
        api_key="mock-key",
        http_client=client,
    )

    agent = InvestigationAgent(
        lineage_repo=lineage_repo,
        model=llm_model,
        tool_registry=registry,
        max_steps=10,
    )

    inv_repo = InMemoryInvestigationRepository()
    service = InvestigationService(
        repository=inv_repo,
        lineage_repository=lineage_repo,
        agent=agent,
    )

    inv = service.run_investigation("INV-1001", exception_id="EX-001")

    assert inv.status == InvestigationStatus.VERIFIED
    assert "EV-001" in inv.cited_evidence_ids
    assert inv.agent_metrics is not None
    assert inv.agent_metrics["llm_calls"] == 6
    assert inv.agent_metrics["llm_failures"] == 0
    assert inv.agent_metrics["total_agent_steps"] == 6

    # Verify audit event history records model provider and name
    agent_events = service.get_agent_events(inv.id)
    decisions = [e for e in agent_events if e.event_type.value == "AGENT_DECISION"]
    assert len(decisions) == 6
    for d in decisions:
        assert d.metadata.get("model_name") == "gpt-4o-mini"
        assert d.metadata.get("model_provider") == "openai"
