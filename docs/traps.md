# Traps

Known traps to avoid during ExceptionLineage development.

## T-001: Premature AI Integration

**Trap:** Adding an LLM or AI agent before the data model and evidence pipeline are defined.

**Why it's dangerous:** Without a clear understanding of what evidence looks like and how investigations flow, an AI agent will produce hallucinated or unverifiable results. The system's value is in evidence-backed determinations, not AI-generated guesses.

**Avoidance:** Define the data model, evidence schema, and validation rules before introducing any AI component.

---

## T-002: Over-Engineering the Foundation

**Trap:** Building complex abstractions, plugin systems, or microservice architectures before any business logic exists.

**Why it's dangerous:** Abstractions without concrete use cases are usually wrong. They slow development and create refactoring debt.

**Avoidance:** Keep the foundation minimal. Add complexity only when driven by actual requirements.

---

## T-003: Fake Data as a Substitute for Design

**Trap:** Creating mock investigation data or fake API integrations to make the system "look complete."

**Why it's dangerous:** Fake data masks missing requirements and creates false confidence. Real investigation data will have structure and edge cases that mocks won't capture.

**Avoidance:** Design the data model from real enterprise transaction patterns, not from imagined examples.

---

## T-004: Ignoring the Evidence Chain

**Trap:** Treating investigation results as simple pass/fail without maintaining the chain of evidence that led to the determination.

**Why it's dangerous:** The entire value proposition of ExceptionLineage is evidence-backed determinations. Without the evidence chain, results are unverifiable.

**Avoidance:** Every determination must reference the specific documents, clauses, and relationships that support it.

---

## T-005: Building UI Before the API

**Trap:** Designing elaborate dashboard screens before the API endpoints and data models are stable.

**Why it's dangerous:** UI built against an unstable API creates constant rework. The frontend becomes a maintenance burden instead of a productivity tool.

**Avoidance:** Stabilise the API contract first, then build the UI to consume it.
