"""Tool for retrieving Statements of Work (SOWs)."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class GetSOWsTool(BaseTool):
    """Retrieves all Statements of Work linked to a governing contract."""

    name = "get_sows"
    description = "Retrieve list of Statements of Work (SOWs), deliverable scope, and baseline fees for contract_id."
    parameters = {
        "contract_id": {
            "type": "string",
            "description": "Governing contract identifier whose Statements of Work to retrieve",
            "required": True,
        }
    }

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        is_valid, err = self.validate_arguments(arguments)
        if not is_valid:
            return ToolResult(tool_name=self.name, success=False, error=err)

        contract_id = arguments.get("contract_id")

        sows = lineage_repo.get_sows(contract_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"sows": sows},
        )
