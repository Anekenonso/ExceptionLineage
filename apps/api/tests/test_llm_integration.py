"""Live LLM integration test for Stage 17.5.

Disabled by default in normal offline CI/local development.
Enabled only when RUN_LLM_AGENT_TESTS=true and valid LLM credentials are configured.
"""

from __future__ import annotations

import os
import pytest

from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.tools import get_default_tool_registry
from app.graph.lineage import InMemoryLineageRepository
from app.investigations.repository import InMemoryInvestigationRepository
from app.investigations.service import InvestigationService
from app.models.enums import InvestigationStatus
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


@pytest.mark.skipif(
    os.getenv("RUN_LLM_AGENT_TESTS") != "true",
    reason="Live LLM tests are disabled by default. Set RUN_LLM_AGENT_TESTS=true and provide AGENT_LLM_API_KEY to run.",
)
def test_live_llm_agent_case_001_end_to_end():
    """Verify that a real live LLM can dynamically plan and execute tools for CASE-001.

    Requirements:
    1. Load CASE-001 / INV-1001.
    2. Run LLMDecisionModel dynamically against available tools.
    3. Verify at least one real tool is called.
    4. Verify agent requests validation (validate_investigation).
    5. Run deterministic validation engine over assembled context.
    6. Verify final terminal outcome is VERIFIED.
    """
    api_key = os.getenv("AGENT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("No AGENT_LLM_API_KEY or OPENAI_API_KEY configured for live LLM test")

    registry = get_default_tool_registry()
    llm_model = LLMDecisionModel(
        tool_registry=registry,
        provider=os.getenv("AGENT_LLM_PROVIDER", "openai"),
        model_name=os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("AGENT_LLM_BASE_URL"),
    )

    lineage_store = build_mock_seed_graph_lineage()
    lineage_repo = InMemoryLineageRepository(lineage_store)

    agent = InvestigationAgent(
        lineage_repo=lineage_repo,
        model=llm_model,
        tool_registry=registry,
        max_steps=10,
    )

    service = InvestigationService(
        repository=InMemoryInvestigationRepository(),
        lineage_repository=lineage_repo,
        agent=agent,
    )

    inv = service.run_investigation("INV-1001", exception_id="EX-001")

    # 1. Verify at least one tool was called
    assert inv.agent_metrics is not None
    assert inv.agent_metrics["tool_calls"] >= 1
    assert inv.agent_metrics["llm_calls"] >= 1

    # 2. Verify agent concluded and requested validation
    assert inv.agent_metrics["termination_reason"] == "VALIDATION_REQUESTED"

    # 3. Verify deterministic validation outcome
    assert inv.status == InvestigationStatus.VERIFIED
    assert "EV-001" in inv.cited_evidence_ids
