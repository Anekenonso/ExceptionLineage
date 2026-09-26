# Live Demo Script — ExceptionLineage

This script provides a concise, step-by-step walkthrough for presenting ExceptionLineage during hackathon judging and technical evaluations.

---

## 1. Introduction (30 seconds)

- **Problem**: When enterprise billing systems flag an invoice exception (e.g. rate variance or surcharge), human analysts spend hours hunting across contracts, amendments, SOWs, and emails to verify if the variance was authorized.
- **Solution**: ExceptionLineage executes autonomous evidence discovery across enterprise graph lineage, and enforces deterministic contractual validation.
- **Core Principle**: *"AI handles ambiguity. Code handles authority."*

---

## 2. Launchpad & Architecture (30 seconds)

1. Open `http://localhost:3000` in the browser.
2. Note the system status indicator: API and Graph services are active and healthy.
3. Review the three proven architectural pillars:
   - **Agent Necessity**: Eliminates 100% of redundant queries via dynamic early-stopping.
   - **Graph Traversal**: Prevents false contractual conflicts with 100% provenance retention.
   - **Deterministic Authority**: Code (not LLM hallucinations) makes the legal determination.
4. Click **"Launch Workspace"** or navigate to `/investigations`.

---

## 3. Flagship Demonstration: INV-1001 (1 minute 30 seconds)

1. On `/investigations`, click **"New Investigation"**.
2. Select **`INV-1001` (Flagship: Rate Adjustment with Approved Variance)**.
3. Click **"Run Investigation"** (or select the existing row if already loaded).
4. Walk through the investigation workspace hierarchy:
   - **Header**: Shows Investigation ID, Invoice `INV-1001`, Acme Global Enterprise, and `VERIFIED` status badge.
   - **Invoice Exception Card**: Billed $10,200 vs. Expected $10,000 (+$200 variance).
   - **Determination Card**: Shows **"Contractually Verified & Approved"** with 3 substantiated evidentiary citations.
   - **Lineage Graph**: Point out the directional knowledge graph:
     `Customer (CUS-001) → Contract (CTR-001) → Amendment (AMD-001) → Approval (APR-001) → Invoice (INV-1001)`
     Click any node to inspect its structured properties in the Entity Inspector.
   - **Deterministic Validation**: Show 8/8 `PASS` checks. Highlight the architectural boundary callout.
   - **Evidentiary Records**: Click `EV-003` to open the slide-over Evidence Drawer showing the VP approval excerpt and validity window.
   - **Investigation Activity Trace**: Show the step-by-step audit trail (`INPUT → AGENT DECISION → TOOL CALL → GRAPH RETRIEVAL → VALIDATION → RESULT`).
   - **Export Report**: Click **"Export Report"** to show instant Markdown and raw JSON compliance export.

---

## 4. Contrasting Failure & Uncertainty Scenarios (1 minute)

Return to `/investigations` to show how the system handles uncertainty, non-compliance, and conflict without guessing:

1. **`INV-1002` — Missing Evidence (`INSUFFICIENT_EVIDENCE`)**:
   - Variance of +$1,500.
   - Agent discovers contract but no approval record exists.
   - Deterministic engine flags `approval_authorization_check` as `UNKNOWN`.
   - Result: Inconclusive. Zero fabricated claims.

2. **`INV-1003` — Contractual Non-Compliance (`NOT_VERIFIED`)**:
   - Unauthorized fee discount violating pricing schedule threshold.
   - Engine flags `pricing_schedule_match_check` as `FAIL`.
   - Result: Clear contractual violation recorded.

3. **`INV-1005` — Conflicting Authority (`NEEDS_REVIEW`)**:
   - Overlapping amendments present irreconcilable rate schedules.
   - Engine flags `conflicting_authority_check` as `FAIL`.
   - Result: Flagged for human legal review with exact conflict highlighted.

---

## 5. Technical Rigor & Edge Cases (30 seconds)

- Demonstrate failure handling: If an invalid invoice ID is submitted or infrastructure fails, the system transitions to `FAILED` and explicitly renders:
  > **"No determination was made."**
- Reiterate: Infrastructure failure is never converted into a business conclusion.

---

## 6. Summary Conclusion (15 seconds)

- ExceptionLineage turns enterprise billing uncertainty into auditable, reproducible, evidence-backed certainty.
