"""Real LLM decision layer adapter implementing AgentModel for ExceptionLineage.

Provides LLM-driven tool selection and evidence gathering planning while
strictly adhering to the foundational architectural law:
    AI handles ambiguity. Code handles authority.

The model is isolated behind AgentModel:
- Evaluates current AgentState against available tools.
- Returns a strictly typed and validated AgentAction.
- Does not determine contractual authority or final validation outcomes.
- Does not have direct database, Cypher, or code execution privileges.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable

import httpx

from app.agent.base_model import AgentModel
from app.agent.exceptions import AgentToolExecutionError
from app.agent.models import AgentAction, AgentState
from app.agent.tools.base import ToolRegistry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are an autonomous investigation planning agent for ExceptionLineage, an evidence-backed enterprise contract exception investigation system.

FOUNDATIONAL ARCHITECTURAL LAW:
    AI handles ambiguity. Code handles authority.

YOUR RESPONSIBILITIES:
1. You are investigating a transaction exception for a specific invoice.
2. Your sole objective is to discover and retrieve sufficient documentary evidence from the knowledge graph through the provided tools.
3. You have access ONLY to the listed investigation tools. You must use these tools to discover evidence.
4. You must NEVER invent, fabricate, or hallucinate entities, clauses, rates, or citations.
5. You must NEVER claim a record exists unless an investigation tool returned it.
6. You do NOT determine contractual authority or legal correctness yourself.
7. You must NEVER declare an invoice "VERIFIED" or "NOT_VERIFIED". That authority belongs solely to the downstream deterministic validation engine.
8. When you have gathered the necessary evidence (or confirmed that evidence is genuinely absent), you MUST call the "validate_investigation" tool with empty arguments to hand off to deterministic validation.
9. If an entity or record is missing, do NOT loop indefinitely. Acknowledge missing evidence and proceed to validate_investigation so the deterministic engine can evaluate compliance.
10. Do not repeatedly call the exact same tool with identical arguments unless there is a clear new operational reason.
11. Keep the investigation strictly bounded, efficient, and evidence-driven.

AVAILABLE INVESTIGATION TOOLS:
{tool_definitions}

RESPONSE FORMAT:
You MUST respond with a single, valid JSON object containing exactly these fields:
{{
    "action": "<tool_name_from_available_tools>",
    "arguments": {{
        "<argument_name>": <argument_value>
    }},
    "reason": "<concise explanation of why this evidence is being sought or why validation is ready>"
}}
"""


class LLMDecisionModel(AgentModel):
    """Concrete AgentModel utilizing an LLM for dynamic tool selection.

    Interfaces with OpenAI-compatible chat completion APIs (OpenAI, Anthropic via proxy,
    Google Gemini OpenAI endpoint, Ollama, vLLM, etc.) via httpx.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        provider: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.provider = (
            provider
            or os.getenv("AGENT_LLM_PROVIDER")
            or "openai"
        ).lower()
        self.model_name = (
            model_name
            or os.getenv("AGENT_LLM_MODEL")
            or ("gpt-4o-mini" if self.provider in ("openai", "openai-compatible") else "gemini-1.5-flash")
        )
        self.api_key = api_key or os.getenv("AGENT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("AGENT_LLM_BASE_URL")
            or ("https://api.openai.com/v1" if self.provider == "openai" else "http://localhost:11434/v1")
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._external_client = http_client

        # Operational metrics tracking
        self.llm_calls = 0
        self.llm_failures = 0
        self.llm_retries = 0
        self.malformed_actions = 0
        self.prompt_tokens: int | None = None
        self.completion_tokens: int | None = None
        self.total_tokens: int | None = None

    def decide_next_action(
        self,
        state: AgentState,
        available_tools: list[str],
    ) -> AgentAction:
        """Call LLM with structured prompt and return a validated AgentAction."""
        system_prompt = self._build_system_prompt()
        state_prompt = self._format_state(state, available_tools)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state_prompt},
        ]

        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1
            raw_content, usage = self._execute_llm_request(messages)

            # Record token usage if available
            if usage:
                self.prompt_tokens = usage.get("prompt_tokens")
                self.completion_tokens = usage.get("completion_tokens")
                self.total_tokens = usage.get("total_tokens")

            # Parse and validate response
            action, error_msg = self._parse_and_validate_action(raw_content)
            if action is not None:
                return action

            # Malformed output handling
            self.malformed_actions += 1
            logger.warning(
                "LLM produced malformed action on step %d (attempt %d/%d): %s",
                state.steps,
                attempt,
                self.max_retries + 1,
                error_msg,
            )

            if attempt <= self.max_retries:
                self.llm_retries += 1
                messages.append({"role": "assistant", "content": raw_content})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous response was rejected with error: {error_msg}.\n"
                        "Please correct the output and return a strictly valid JSON object matching "
                        "one of the available tools and their required arguments."
                    ),
                })
            else:
                raise AgentToolExecutionError(
                    f"LLM failed to produce a valid tool action after {self.max_retries + 1} attempts: {error_msg}"
                )

        raise AgentToolExecutionError("LLM action selection exhausted retry limit")

    def _build_system_prompt(self) -> str:
        tool_defs = json.dumps(self.tool_registry.get_tool_definitions(), indent=2)
        return SYSTEM_PROMPT_TEMPLATE.format(tool_definitions=tool_defs)

    def _format_state(self, state: AgentState, available_tools: list[str]) -> str:
        """Serialize current agent state into a structured prompt without leaking raw secrets."""
        # Summary of discovered entities
        discovered: dict[str, Any] = {}
        if state.invoice:
            discovered["invoice"] = {
                "id": state.invoice.get("id"),
                "amount": state.invoice.get("amount"),
                "customer_id": state.invoice.get("customer_id"),
                "contract_id": state.invoice.get("contract_id"),
                "product_id": state.invoice.get("product_id"),
                "issued_at": state.invoice.get("issued_at"),
            }
        if state.customer:
            discovered["customer"] = {"id": state.customer.get("id"), "name": state.customer.get("name")}
        if state.contract:
            discovered["contract"] = {
                "id": state.contract.get("id"),
                "status": state.contract.get("status"),
                "effective_from": state.contract.get("effective_from"),
                "effective_until": state.contract.get("effective_until"),
            }
        if state.amendments:
            discovered["amendments"] = [
                {
                    "id": a.get("id"),
                    "effective_from": a.get("effective_from"),
                    "effective_until": a.get("effective_until"),
                    "authorized_rate": a.get("authorized_rate"),
                }
                for a in state.amendments
            ]
        if state.sows:
            discovered["sows"] = [
                {"id": s.get("id"), "scope": s.get("scope"), "effective_from": s.get("effective_from")}
                for s in state.sows
            ]
        if state.approval:
            discovered["approval"] = {
                "id": state.approval.get("id"),
                "status": state.approval.get("status"),
                "approved_by": state.approval.get("approved_by"),
            }
        discovered["evidence_count"] = len(state.evidence)

        context_obj = {
            "investigation_id": state.investigation_id,
            "invoice_id": state.invoice_id,
            "exception_id": state.exception_id,
            "current_step": state.steps,
            "prior_tool_calls": state.tool_calls,
            "recent_observations": state.observations[-8:] if state.observations else [],
            "missing_evidence_noted": state.missing_evidence,
            "discovered_entities": discovered,
            "available_tools": available_tools,
        }
        return (
            "CURRENT INVESTIGATION STATE:\n"
            + json.dumps(context_obj, indent=2)
            + "\n\nChoose the single best next action."
        )

    def _execute_llm_request(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, dict[str, Any] | None]:
        """Execute HTTP request against OpenAI-compatible chat completion endpoint."""
        self.llm_calls += 1
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        try:
            if self._external_client is not None:
                resp = self._external_client.post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(url, json=payload, headers=headers)

            if resp.status_code == 401 or resp.status_code == 403:
                self.llm_failures += 1
                raise AgentToolExecutionError(
                    f"LLM authentication failed (HTTP {resp.status_code}): please check AGENT_LLM_API_KEY"
                )
            if resp.status_code == 429:
                self.llm_failures += 1
                raise AgentToolExecutionError(
                    "LLM rate limit reached (HTTP 429): please retry after backoff or check provider limits"
                )
            if resp.status_code >= 400:
                self.llm_failures += 1
                raise AgentToolExecutionError(
                    f"LLM provider error (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                self.llm_failures += 1
                raise AgentToolExecutionError("LLM response contained no choices")

            content = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage")
            return content, usage

        except (httpx.TimeoutException, httpx.ConnectTimeout) as exc:
            self.llm_failures += 1
            raise AgentToolExecutionError(f"LLM request timed out after {self.timeout_seconds}s: {exc}") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            self.llm_failures += 1
            raise AgentToolExecutionError(f"LLM network connectivity failure: {exc}") from exc
        except AgentToolExecutionError:
            raise
        except Exception as exc:
            self.llm_failures += 1
            raise AgentToolExecutionError(f"Unexpected error communicating with LLM provider: {exc}") from exc

    def _parse_and_validate_action(self, raw_content: str) -> tuple[AgentAction | None, str | None]:
        """Parse structured JSON from model and validate action name and argument schema."""
        if not raw_content or not raw_content.strip():
            return None, "Empty response received from LLM"

        # 1. Parse JSON
        try:
            # Handle potential markdown code fences ```json ... ```
            cleaned = raw_content.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return None, f"Invalid JSON format: {exc}"

        if not isinstance(parsed, dict):
            return None, f"Expected JSON object, got {type(parsed).__name__}"

        action_name = parsed.get("action")
        if not action_name or not isinstance(action_name, str):
            return None, "Missing or non-string 'action' field in model response"

        arguments = parsed.get("arguments", {})
        if not isinstance(arguments, dict):
            return None, "Field 'arguments' must be a JSON object (dictionary)"

        reason = parsed.get("reason")
        if reason is not None and not isinstance(reason, str):
            reason = str(reason)

        # 2. Validate against ToolRegistry schema
        is_valid, validation_err = self.tool_registry.validate_action(action_name, arguments)
        if not is_valid:
            return None, validation_err

        action = AgentAction(
            action=action_name,
            arguments=arguments,
            reason=reason or "LLM planned action",
        )
        return action, None
