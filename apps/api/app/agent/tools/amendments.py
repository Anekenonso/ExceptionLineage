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

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        contract_id = arguments.get("contract_id")
        if not contract_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Argument 'contract_id' is required",
            )

        amendments = lineage_repo.get_amendments(contract_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"amendments": amendments},
        )
