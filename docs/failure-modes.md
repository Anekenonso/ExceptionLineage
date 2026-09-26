# Failure Modes and Resiliency Semantics

Controlled failure modes, edge cases, and safety semantics for ExceptionLineage (Stage 18).

## Architectural Invariant
> **"AI handles ambiguity. Code handles authority."**

Under this invariant, the system must fail safely under corrupted, missing, adversarial, or malformed inputs:
1. **Missing evidence must NEVER automatically become `NOT_VERIFIED`.** It must be classified as `INSUFFICIENT_EVIDENCE`.
2. **Conflicting evidence must NEVER automatically become `VERIFIED`.** It must be classified as `NEEDS_REVIEW`.
3. **Agent loop exhaustion must NEVER enter an infinite loop.** It terminates strictly at `MAX_AGENT_STEPS` with `FAILED` (`AGENT_STEP_LIMIT_EXCEEDED`).
4. **The deterministic `ValidationEngine` remains the sole authority** for contractual compliance.

---

## Controlled Failure Modes Catalog

### FM-001: Unknown Tool Request
- **Scenario:** The agent model attempts to invoke a tool that does not exist in `ToolRegistry` (e.g., hallucinated tool name or arbitrary command).
- **Behavior:** The agent loop intercepts the action, records `unknown_tool_calls += 1` and `failed_tool_calls += 1`, appends an explanatory error to `state.observations`, and continues the loop without crashing.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_1_unknown_tool`

### FM-002: Missing Tool Arguments
- **Scenario:** The agent requests a valid tool but omits required parameters (e.g., invoking `get_invoice` without `invoice_id`).
- **Behavior:** `ToolRegistry.validate_action` validates arguments against tool schema, rejects execution, records `invalid_argument_calls += 1`, and prompts the agent to correct the argument on the subsequent step.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_2_missing_argument`

### FM-003: Invalid Argument Types
- **Scenario:** The agent supplies unexpected parameter types (e.g., passing an integer for `source_ids` where a `list[str]` is required) or extraneous unexpected keys.
- **Behavior:** Pydantic schema validation rejects the arguments, records `invalid_argument_calls += 1`, and prevents corrupted execution.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_3_invalid_argument_type`

### FM-004: Malformed LLM Output
- **Scenario:** The LLM returns non-JSON text, conversational explanations, or broken syntax.
- **Behavior:** `_parse_and_validate_action` catches `JSONDecodeError`, increments `malformed_actions += 1`, and initiates a bounded corrective retry prompt.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_4_malformed_llm_output`

### FM-005: LLM Network Timeout
- **Scenario:** The external LLM API exceeds `timeout_seconds` or fails socket read.
- **Behavior:** Caught cleanly as `httpx.TimeoutException`, increments `llm_timeouts += 1` and `llm_failures += 1`, and safely transitions the investigation state to `FAILED` with clear reason without crashing the API server.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_5_llm_timeout`

### FM-006: Bounded Retry Limit
- **Scenario:** The model persistently outputs unparseable text across all allowed attempts.
- **Behavior:** The retry loop is strictly bounded by `max_retries` (default: 1). Upon exhaustion, it raises `AgentToolExecutionError` and aborts rather than looping infinitely.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_6_bounded_retry`

### FM-007: Tool Execution Infrastructure Failure
- **Scenario:** A tool query to the underlying graph fails or returns an error.
- **Behavior:** The failure is isolated into `ToolResult.error`, `tool_errors += 1` is recorded, and the agent state logs the missing evidence.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_7_tool_failure`

### FM-008: Genuine Missing Evidence (Must NOT become `NOT_VERIFIED`)
- **Scenario:** 
  - An invoice rate revision requires executive signoff, but no approval record exists (CASE-002).
  - An invoice has no governing contract on record (CASE-007).
- **Critical Requirement:** Missing evidence must **NEVER** be conflated with contract violation. A missing record does not prove terms were breached; it indicates that sufficiency has not been established.
- **Behavior:** The system terminates with `INSUFFICIENT_EVIDENCE`.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_8_missing_evidence_is_insufficient_evidence` and `test_failure_mode_8_missing_contract_is_insufficient_evidence`

### FM-009: Conflicting Legal Authority (Must NOT become `VERIFIED`)
- **Scenario:** Two concurrent amendments authorize contradictory rates with equal legal precedence (CASE-005).
- **Critical Requirement:** An automated system must **NEVER** pick a winner between conflicting legal contracts.
- **Behavior:** The deterministic rule `conflicting_authority` triggers `FAIL`, forcing the investigation into `NEEDS_REVIEW`.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_9_conflicting_amendments_is_needs_review`

### FM-010: Expired Contractual Authority
- **Scenario:** An amendment authorized a pilot rate, but its effective period expired prior to invoice issuance (CASE-003).
- **Behavior:** Evaluated deterministically against invoice issuance date. The rule `amendment_effectiveness` fails, yielding `NOT_VERIFIED`.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_10_expired_authority_is_not_verified`

### FM-011: Step-Limit Exhaustion
- **Scenario:** An agent model enters an exploratory or repetitive loop without ever calling `validate_investigation`.
- **Behavior:** The agent loop is strictly capped at `MAX_AGENT_STEPS` (default: 10). When the step count reaches the limit, `AgentStepLimitExceededError` is raised, partial metrics are preserved, and the investigation transitions to `FAILED` with `AGENT_STEP_LIMIT_EXCEEDED`.
- **Tested by:** `tests/test_failure_modes.py::test_failure_mode_11_step_limit_exhaustion_bounds_execution`

### FM-012: Context Contamination from Flat Relational Lookups
- **Scenario:** Querying contractual amendments or SOWs using flat customer-level lookups without explicit relationship traversal boundaries.
- **Risk:** Amendments belonging to different contracts for the same customer are pulled into the validation context, triggering false rate conflicts and incorrect `NEEDS_REVIEW` or `NOT_VERIFIED` outcomes (accuracy drops to 87.5% in Flat mock).
- **Defense:** Explicit directional relationship traversal (`Contract -[:AMENDED_BY]-> Amendment`) isolates the exact contract lineage, preventing cross-contract context pollution.
- **Tested by:** `apps/api/tests/test_neo4j_removal_experiment.py::test_neo4j_removal_accuracy_impact` and `test_neo4j_removal_irrelevant_retrieval_contamination`

### FM-013: Redundant Tool Loops and Blind Query Execution
- **Scenario:** A fixed deterministic workflow executes a static sequence of tool calls regardless of intermediate discovery (e.g., continuing to query amendments and SOWs for an unanchored transaction or when base terms already match).
- **Risk:** Wasted database operations, latency, and inability to adapt to non-linear branching scenarios.
- **Defense:** An adaptive investigation loop evaluates intermediate evidence after each tool step, terminating early when conclusive proof or early rejection is identified, and navigating non-linear branching paths.
- **Tested by:** `apps/api/tests/test_agent_necessity_experiment.py::test_agent_necessity_tool_efficiency` and `test_agent_necessity_dead_end_recovery`

### FM-014: Credential and Secret Leakage in Evidence Audit Traces
- **Scenario:** Tool parameters, database connection metadata, or external API keys leak into public or auditable investigation traces.
- **Risk:** Sensitive enterprise credentials exposed in compliance reports or trace logs.
- **Defense:** Automated recursive sanitization (`_sanitize_secrets`) inspects all dictionary arguments, nested lists, and string payloads in `InvestigationEvidenceTrace`, redacting sensitive keys and known credential signatures to `[REDACTED]`.
- **Tested by:** `apps/api/tests/test_evidence_chain_trace.py::test_trace_secret_redaction`

