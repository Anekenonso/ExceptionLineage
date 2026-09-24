"""Agent package for ExceptionLineage controlled investigation loop."""

from app.agent.base_model import AgentModel, HeuristicAgentModel, ScriptedAgentModel
from app.agent.exceptions import (
    AgentStepLimitExceededError,
    AgentToolExecutionError,
)
from app.agent.factory import create_investigation_agent, get_configured_agent_model
from app.agent.llm_model import LLMDecisionModel
from app.agent.loop import InvestigationAgent
from app.agent.models import AgentAction, AgentMetrics, AgentState, ToolResult
from app.agent.tools import ToolRegistry, get_default_tool_registry

__all__ = [
    "AgentAction",
    "AgentMetrics",
    "AgentModel",
    "AgentState",
    "AgentStepLimitExceededError",
    "AgentToolExecutionError",
    "HeuristicAgentModel",
    "InvestigationAgent",
    "LLMDecisionModel",
    "ScriptedAgentModel",
    "ToolRegistry",
    "ToolResult",
    "create_investigation_agent",
    "get_configured_agent_model",
    "get_default_tool_registry",
]
