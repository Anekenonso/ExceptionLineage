"""Tool for concluding evidence gathering and initiating deterministic validation."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class ValidateInvestigationTool(BaseTool):
    """Signals that evidence gathering is complete and deterministic validation should be invoked."""

    name = "validate_investigation"
    description = "Conclude evidence gathering and proceed to authoritative deterministic validation."

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"ready_for_validation": True},
        )
