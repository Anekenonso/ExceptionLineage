"""Investigation agent tools package."""

from app.agent.tools.amendments import GetContractAmendmentsTool
from app.agent.tools.approvals import FindApprovalsTool
from app.agent.tools.base import BaseTool, ToolRegistry
from app.agent.tools.contract import FindContractTool
from app.agent.tools.evidence import GetRelatedEvidenceTool
from app.agent.tools.invoice import GetInvoiceTool
from app.agent.tools.sows import GetSOWsTool
from app.agent.tools.validation import ValidateInvestigationTool


def get_default_tool_registry() -> ToolRegistry:
    """Build and populate the standard registry of investigation tools."""
    registry = ToolRegistry()
    registry.register(GetInvoiceTool())
    registry.register(FindContractTool())
    registry.register(GetContractAmendmentsTool())
    registry.register(GetSOWsTool())
    registry.register(FindApprovalsTool())
    registry.register(GetRelatedEvidenceTool())
    registry.register(ValidateInvestigationTool())
    return registry


create_default_tool_registry = get_default_tool_registry


__all__ = [
    "BaseTool",
    "ToolRegistry",
    "GetInvoiceTool",
    "FindContractTool",
    "GetContractAmendmentsTool",
    "GetSOWsTool",
    "FindApprovalsTool",
    "GetRelatedEvidenceTool",
    "ValidateInvestigationTool",
    "get_default_tool_registry",
]
