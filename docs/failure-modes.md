# Failure Modes

Anticipated failure modes for the ExceptionLineage investigation system.

## FM-001: Incomplete Evidence

**Description:** An investigation reaches a determination but is missing critical evidence (e.g., an amendment that modifies contract terms).

**Impact:** Incorrect determination that could lead to wrong exception handling.

**Mitigation:** The system must track evidence completeness and flag investigations where expected document types are missing.

---

## FM-002: Contradictory Evidence

**Description:** Multiple documents provide conflicting information (e.g., two amendments with different effective dates for the same clause).

**Impact:** The system cannot produce a reliable determination.

**Mitigation:** Surface contradictions explicitly rather than silently choosing one version. Require human review for contradictory evidence.

---

## FM-003: Stale Data

**Description:** The system operates on outdated document versions because source data hasn't been refreshed.

**Impact:** Determinations based on superseded contracts or expired approvals.

**Mitigation:** Track document versions and timestamps. Flag evidence that may be stale relative to the investigation date.

---

## FM-004: Graph Relationship Errors

**Description:** Incorrect relationships in the knowledge graph (e.g., an invoice linked to the wrong contract).

**Impact:** Investigation follows wrong evidence chains, producing incorrect determinations.

**Mitigation:** Validate graph relationships against source document references. Implement relationship confidence scoring.

---

## FM-005: Agent Hallucination

**Description:** An AI agent fabricates evidence or relationships that don't exist in the source documents.

**Impact:** False determinations that appear legitimate because they include fabricated evidence.

**Mitigation:** Every agent-generated claim must be traceable to a specific source document and location. Implement verification steps that check claims against source material.

---

## FM-006: Silent Failures

**Description:** A component fails without the system reporting the failure, leading to partial or missing results being treated as complete.

**Impact:** Users act on incomplete investigations without knowing they're incomplete.

**Mitigation:** Health checks, progress tracking, and explicit failure reporting at every stage of the investigation pipeline.
