"""Tool for retrieving invoice details and initial relationships."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class GetInvoiceTool(BaseTool):
    """Retrieves target invoice details, customer metadata, and linked exception."""

    name = "get_invoice"
    description = "Retrieve invoice details, billed customer, and exception link given invoice_id."

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        invoice_id = arguments.get("invoice_id")
        if not invoice_id:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Argument 'invoice_id' is required",
            )

        data = lineage_repo.get_invoice(invoice_id)
        if not data or not data.get("invoice"):
            raise ValueError(f"invoice '{invoice_id}' not found in knowledge graph")

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
        )
