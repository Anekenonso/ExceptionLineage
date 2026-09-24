"""Base tool abstractions and registry for the investigation agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.agent.models import ToolResult
from app.graph.lineage import LineageRepository


class BaseTool(ABC):
    """Abstract base class for all deterministic investigation tools.

    Tools encapsulate discrete graph and repository queries. They never allow
    arbitrary Cypher or database mutation, and strictly return structured ToolResult objects.
    """

    name: str
    description: str
    parameters: dict[str, dict[str, Any]] = {}

    def validate_arguments(self, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate argument names, required fields, and types against tool schema.

        Returns (True, None) if valid, or (False, error_message) if invalid.
        """
        # 1. Check for unexpected arguments
        allowed_keys = set(self.parameters.keys())
        provided_keys = set(arguments.keys())
        unexpected = provided_keys - allowed_keys
        if unexpected:
            return False, f"Unexpected argument(s) for tool '{self.name}': {sorted(unexpected)}. Allowed: {sorted(allowed_keys)}"

        # 2. Check for missing required arguments
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", True):
                if param_name not in arguments or arguments[param_name] is None:
                    return False, f"Missing required argument '{param_name}' for tool '{self.name}'"
                val = arguments[param_name]
                if param_spec.get("type") == "string" and isinstance(val, str) and not val.strip():
                    return False, f"Argument '{param_name}' cannot be empty or whitespace"

        # 3. Check argument types
        for param_name, val in arguments.items():
            param_spec = self.parameters.get(param_name, {})
            expected_type = param_spec.get("type")
            if expected_type == "string" and not isinstance(val, str):
                return False, f"Argument '{param_name}' must be a string, got {type(val).__name__}"
            elif expected_type == "array":
                if not isinstance(val, list):
                    return False, f"Argument '{param_name}' must be a list, got {type(val).__name__}"
                item_type = param_spec.get("items_type")
                if item_type == "string":
                    for item in val:
                        if not isinstance(item, str):
                            return False, f"Item in '{param_name}' list must be a string, got {type(item).__name__}"

        return True, None

    @abstractmethod
    def execute(self, arguments: dict[str, Any], lineage_repo: LineageRepository) -> ToolResult:
        """Execute the tool deterministically against the provided repository."""
        ...


class ToolRegistry:
    """Registry maintaining available investigation tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_descriptions(self) -> dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return machine-readable JSON schema descriptions for all registered tools."""
        definitions = []
        for name, tool in self._tools.items():
            properties: dict[str, Any] = {}
            required: list[str] = []
            for p_name, p_spec in tool.parameters.items():
                p_dict: dict[str, Any] = {
                    "type": p_spec.get("type", "string"),
                    "description": p_spec.get("description", ""),
                }
                if p_spec.get("type") == "array" and p_spec.get("items_type"):
                    p_dict["items"] = {"type": p_spec["items_type"]}
                properties[p_name] = p_dict
                if p_spec.get("required", True):
                    required.append(p_name)

            definitions.append({
                "name": name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
            })
        return definitions

    def validate_action(self, action_name: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        """Confirm tool exists and validate requested arguments against its schema."""
        tool = self.get(action_name)
        if not tool:
            allowed = self.list_tools()
            return False, f"Unknown tool '{action_name}'. Available tools: {allowed}"
        return tool.validate_arguments(arguments)
