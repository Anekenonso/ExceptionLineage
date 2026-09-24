"""Tool for finding approvals linked to transaction exceptions."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class FindApprovalsTool(BaseTool):
    """Finds approval sign-off records for an operational exception."""

    name = "find_approvals"
    description = "Retrieve executive or managerial approval records given exception_id."

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        exception_id = arguments.get("exception_id")
        if not exception_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Argument 'exception_id' is required",
            )

        approvals = lineage_repo.get_approvals(exception_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"approvals": approvals},
        )
