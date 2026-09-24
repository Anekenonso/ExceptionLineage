"""Exceptions for the agentic investigation loop in ExceptionLineage."""

from __future__ import annotations


class AgentError(Exception):
    """Base exception for all agent-related failures."""


class AgentStepLimitExceededError(AgentError):
    """Raised when the agent exceeds the maximum allowable iterations."""


class AgentToolExecutionError(AgentError):
    """Raised when an unrecoverable tool or infrastructure failure occurs."""
