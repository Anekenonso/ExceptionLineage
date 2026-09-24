"""Tool for retrieving governing contract details."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class FindContractTool(BaseTool):
    """Finds and retrieves governing contract metadata."""

    name = "find_contract"
    description = "Retrieve contract terms, validity period, and customer link given contract_id."

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        contract_id = arguments.get("contract_id")
        if not contract_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Argument 'contract_id' is required",
            )

        data = lineage_repo.get_contract(contract_id)
        if not data or not data.get("contract"):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Contract '{contract_id}' not found in knowledge graph",
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
        )
