"""Exceptions for the agentic investigation loop in ExceptionLineage."""

from __future__ import annotations


from typing import Any


class AgentError(Exception):
    """Base exception for all agent-related failures."""


class AgentStepLimitExceededError(AgentError):
    """Raised when the agent exceeds the maximum allowable iterations."""

    def __init__(self, message: str, metrics: Any = None) -> None:
        super().__init__(message)
        self.metrics = metrics


class AgentToolExecutionError(AgentError):
    """Raised when an unrecoverable tool or infrastructure failure occurs."""
