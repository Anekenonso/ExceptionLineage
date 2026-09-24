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
    parameters = {
        "source_ids": {
            "type": "array",
            "items_type": "string",
            "description": "List of entity identifiers (contract, amendment, SOW, approval, exception) to fetch supporting evidence clauses for",
            "required": True,
        }
    }

    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        is_valid, err = self.validate_arguments(arguments)
        if not is_valid:
            return ToolResult(tool_name=self.name, success=False, error=err)

        source_ids = arguments.get("source_ids")

        if isinstance(source_ids, str):
            source_ids = [source_ids]

        evidence = lineage_repo.get_evidence(source_ids)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"evidence": evidence},
            evidence=evidence,
        )
