# Demo Scenarios — ExceptionLineage

This document catalogs the verified demonstration scenarios for ExceptionLineage, detailing the target transaction exception, underlying evidentiary records, deterministic validation results, and observed terminal outcomes.

---

## Flagship Scenario: INV-1001 (Contractually Verified & Approved)

- **Scenario Identifier**: `INV-1001` (Exception `EX-001`)
- **Customer**: Acme Global Enterprise Inc. (`CUS-001`)
- **Invoice Amount**: $10,200.00 USD
- **Expected Baseline Amount**: $10,000.00 USD (Variance: +$200.00 USD)
- **Governing Contract**: Master Services Agreement `CTR-001`
- **Amendment**: `AMD-001` (Rate Adjustment)
- **Operational Approval**: `APR-001` (VP Approval)
- **Observed Terminal Status**: `VERIFIED`
- **Deterministic Validation Outcome**: 8 of 8 Rules Passed (0 Failed, 0 Unknown)
- **Key Deterministic Checks Passed**:
  - `contract_active_check`: `CTR-001` active on issuance date `2026-03-15`.
  - `customer_entity_match_check`: Invoice customer `CUS-001` matches contract customer.
  - `pricing_schedule_match_check`: Base rate corresponds to agreed schedule in `CTR-001`.
  - `amendment_terms_check`: `AMD-001` effective `2026-02-01` authorizes revised tier pricing.
  - `approval_authorization_check`: Variance approved by authorized VP (`APR-001`).
  - `currency_consistency_check`: All contract and invoice amounts consistently use `USD`.
  - `date_sequence_check`: Issuance date `2026-03-15` occurs within valid contract window.
  - `lineage_provenance_check`: Complete directional lineage graph established.
- **Auditable Citations**: `EV-001` (Contract), `EV-002` (Amendment), `EV-003` (Approval).
- **Demonstration Purpose**: Proves the happy path where AI agent discovers the complete graph lineage across disparate contract, amendment, and approval artifacts, and deterministic code validates compliance.

---

## Contrasting Scenario 1: INV-1002 (Insufficient Evidentiary Lineage)

- **Scenario Identifier**: `INV-1002` (Exception `EX-002`)
- **Customer**: Acme Global Enterprise Inc. (`CUS-001`)
- **Invoice Amount**: $11,500.00 USD
- **Expected Baseline Amount**: $10,000.00 USD (Variance: +$1,500.00 USD surcharge)
- **Governing Contract**: `CTR-001`
- **Observed Terminal Status**: `INSUFFICIENT_EVIDENCE`
- **Deterministic Validation Outcome**: 7 Passed, 0 Failed, 1 Unknown
- **Failing / Indeterminate Check**:
  - `approval_authorization_check` -> `UNKNOWN` (Required operational approval or surcharge authorization document was not found in evidentiary records).
- **Summary**: Investigation is inconclusive because essential contractual or approval evidence is missing.
- **Demonstration Purpose**: Demonstrates that ExceptionLineage refuses to guess or hallucinate approval; when evidence is absent, it returns tri-state `UNKNOWN` and terminal `INSUFFICIENT_EVIDENCE`.

---

## Contrasting Scenario 2: INV-1003 (Contractual Non-Compliance Detected)

- **Scenario Identifier**: `INV-1003` (Exception `EX-003`)
- **Customer**: Acme Global Enterprise Inc. (`CUS-001`)
- **Invoice Amount**: $9,500.00 USD
- **Expected Baseline Amount**: $10,000.00 USD
- **Governing Contract**: `CTR-001`
- **Observed Terminal Status**: `NOT_VERIFIED`
- **Deterministic Validation Outcome**: 6 Passed, 1 Failed, 1 Unknown
- **Violated Check**:
  - `pricing_schedule_match_check` -> `FAIL` (Rate discrepancy exceeds allowed contract threshold without qualifying discount schedule).
- **Summary**: Invoice amount $9,500.00 could not be verified due to contractual rule failure.
- **Demonstration Purpose**: Demonstrates deterministic authority rejecting unauthorized fee deductions or threshold violations.

---

## Contrasting Scenario 3: INV-1005 (Conflicting Contractual Authority)

- **Scenario Identifier**: `INV-1005` (Exception `EX-005`)
- **Customer**: Acme Global Enterprise Inc. (`CUS-001`)
- **Invoice Amount**: $14,000.00 USD
- **Governing Contract**: `CTR-001`
- **Observed Terminal Status**: `NEEDS_REVIEW`
- **Deterministic Validation Outcome**: 6 Passed, 1 Failed, 1 Unknown
- **Unresolved Conflict**:
  - `conflicting_authority_check` -> `FAIL` (Multiple competing contractual documents or amendments apply overlapping pricing without precedence resolution).
- **Summary**: Investigation requires human review due to conflicting contractual authority.
- **Demonstration Purpose**: Demonstrates fail-safe routing to human domain experts when legal documents present irreconcilable contractual conflicts.

---

## Additional Verified Benchmark Scenarios

| Scenario | Invoice ID | Customer | Amount | Status | Validation Result | Core Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INV-1004** | `INV-1004` | Acme Global | $8,000.00 | `NOT_VERIFIED` | 5 PASS, 2 FAIL, 1 UNKNOWN | Expired amendment & unauthorized rate reduction |
| **INV-1006** | `INV-1006` | Acme Global | $15,000.00 | `NOT_VERIFIED` | 5 PASS, 2 FAIL, 1 UNKNOWN | Quantity modifier exceeds authorized SOW ceiling |
| **INV-1007** | `INV-1007` | Beta Logistics | $4,500.00 | `INSUFFICIENT_EVIDENCE` | 1 PASS, 0 FAIL, 7 UNKNOWN | Orphaned invoice missing governing master contract |
| **INV-1008** | `INV-1008` | Beta Logistics | $18,000.00 | `VERIFIED` | 8 PASS, 0 FAIL, 0 UNKNOWN | Multi-tier SOW with verified VP approval |
