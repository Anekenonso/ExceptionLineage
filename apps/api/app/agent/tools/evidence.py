"""Tool for retrieving evidentiary records and document clauses."""

from __future__ import annotations

from typing import Any

from app.agent.models import ToolResult
from app.agent.tools.base import BaseTool
from app.graph.lineage import LineageRepository


class GetRelatedEvidenceTool(BaseTool):
    """Retrieves evidentiary records linked to specific entity identifiers."""

    name = "get_related_evidence"
    description = "Retrieve evidentiary citations, clauses, and document excerpts for a list of source_ids."

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        source_ids = arguments.get("source_ids")
        if not source_ids:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Argument 'source_ids' list is required",
            )

        if isinstance(source_ids, str):
            source_ids = [source_ids]

        evidence = lineage_repo.get_evidence(source_ids)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"evidence": evidence},
            evidence=evidence,
        )
