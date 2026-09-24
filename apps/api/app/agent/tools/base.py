"""Base tool abstractions and registry for the investigation agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.agent.models import ToolResult
from app.graph.lineage import LineageRepository


class BaseTool(ABC):
    """Abstract base class for all deterministic investigation tools.

    Tools encapsulate discrete graph and repository queries. They never allow
    arbitrary Cypher or database mutation, and strictly return structured ToolResult objects.
    """

    name: str
    description: str

    @abstractmethod
    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        """Execute the tool deterministically against the provided repository."""
        ...


class ToolRegistry:
    """Registry maintaining available investigation tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_descriptions(self) -> dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}
