"""Factory for creating configured agent models and investigation agents."""

from __future__ import annotations

import logging
import os

from app.agent.base_model import AgentModel, HeuristicAgentModel
from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.tools import ToolRegistry, get_default_tool_registry
from app.graph.lineage import LineageRepository

logger = logging.getLogger(__name__)


def get_configured_agent_model(
    tool_registry: ToolRegistry | None = None,
) -> AgentModel:
    """Return configured AgentModel based on AGENT_MODEL environment variable.

    Supported values:
        - 'heuristic' (default): deterministic rule-based investigation planner
        - 'llm': dynamic LLM decision layer via LLMDecisionModel

    If 'llm' is specified but no API key is found and no local endpoint is set,
    it falls back to HeuristicAgentModel with a descriptive warning to ensure
    safe default development and CI behavior.
    """
    model_choice = os.getenv("AGENT_MODEL", "heuristic").strip().lower()
    registry = tool_registry or get_default_tool_registry()

    if model_choice == "llm":
        api_key = os.getenv("AGENT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("AGENT_LLM_BASE_URL")

        # Allow localhost / Ollama without api_key, but for cloud providers require key
        if not api_key and (not base_url or "localhost" not in base_url):
            logger.warning(
                "AGENT_MODEL is set to 'llm' but neither AGENT_LLM_API_KEY nor a local AGENT_LLM_BASE_URL "
                "was found. Falling back to HeuristicAgentModel for safe offline operation."
            )
            return HeuristicAgentModel()

        logger.info("Initializing LLMDecisionModel for investigation agent")
        return LLMDecisionModel(tool_registry=registry)

    return HeuristicAgentModel()


def create_investigation_agent(
    lineage_repo: LineageRepository,
    model: AgentModel | None = None,
    tool_registry: ToolRegistry | None = None,
    max_steps: int = 10,
) -> InvestigationAgent:
    """Build an InvestigationAgent with the default or configured model."""
    registry = tool_registry or get_default_tool_registry()
    agent_model = model or get_configured_agent_model(registry)
    return InvestigationAgent(
        lineage_repo=lineage_repo,
        model=agent_model,
        tool_registry=registry,
        max_steps=max_steps,
    )
