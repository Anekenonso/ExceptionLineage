"""Tool for retrieving contract amendments."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class GetContractAmendmentsTool(BaseTool):
    """Retrieves all amendments associated with a governing contract."""

    name = "get_contract_amendments"
    description = "Retrieve list of executed amendments, effective dates, and rate adjustments for contract_id."
    parameters = {
        "contract_id": {
            "type": "string",
            "description": "Governing contract identifier whose amendments to retrieve",
            "required": True,
        }
    }

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        is_valid, err = self.validate_arguments(arguments)
        if not is_valid:
            return ToolResult(tool_name=self.name, success=False, error=err)

        contract_id = arguments.get("contract_id")

        amendments = lineage_repo.get_amendments(contract_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"amendments": amendments},
        )
