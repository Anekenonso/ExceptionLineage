# ExceptionLineage Synthetic Dataset & Ground Truth

> [!IMPORTANT]
> **SIMULATION NOTICE**: All data contained in this directory is strictly **SIMULATED** for development, automated testing, and evaluation purposes. None of this data originates from real enterprises, real customers, or real legal contracts. Do not use this data for production purposes or cite it as real-world evidence.

---

## Purpose

ExceptionLineage investigates operational variances between enterprise transaction invoices and their governing legal contracts.

This dataset provides a controlled, relationally dense, and machine-verifiable benchmark to:
1. Exercise deterministic validation checks without flaky external dependencies.
2. Evaluate future investigation agents against known ground-truth outcomes.
3. Validate future graph schemas (e.g. Neo4j) and data connectors (e.g. Zetaris).
4. Prove that non-verified and indeterminate cases (`INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, `NOT_VERIFIED`) are preserved rather than hallucinated into success.

---

## Directory Structure

```
data/
├── README.md                          # This specification
├── seed/                              # Core domain records (Pydantic-validated)
│   ├── customers.json                 # Enterprise customers (CUS-001, CUS-002, CUS-003)
│   ├── contracts.json                 # Master agreements (CTR-001, CTR-002)
│   ├── amendments.json                # Amendments modifying rates and scopes (AMD-001 to AMD-007)
│   ├── sows.json                      # Statements of Work (SOW-001, SOW-002)
│   ├── exceptions.json                # Transaction exceptions (EX-001 to EX-008)
│   ├── approvals.json                 # Waivers and authorizations (APR-001, APR-005, APR-008)
│   ├── invoices.json                  # Invoices under investigation (INV-1001 to INV-1008)
│   └── evidence.json                  # Evidentiary citations with locators and excerpts (EV-001 to EV-013)
├── cases/
│   └── cases.json                     # 8 investigation case descriptions
└── ground_truth/
    └── ground_truth.json              # Machine-checkable ground truth outcomes for each case
```

---

## Core Investigation Model

The primary investigation question is:
> *Why does this invoice differ from the amount established by the governing contract?*

The dataset models the evidence chain:
$$\text{Invoice} \rightarrow \text{Customer} \rightarrow \text{Contract} \rightarrow \text{Amendment} \rightarrow \text{SOW} \rightarrow \text{Exception} \rightarrow \text{Approval}$$

---

## Investigation Cases Summary

| Case ID | Invoice ID | Scenario | Expected Status | Known Failure / Condition |
|---|---|---|---|---|
| `CASE-001` | `INV-1001` | Baseline $12,000 modified to $10,200 by valid AMD-001, within dates, approved by APR-001 | `VERIFIED` | `null` |
| `CASE-002` | `INV-1002` | Baseline $12,000 modified by AMD-002 to $10,500, but required approval is missing | `INSUFFICIENT_EVIDENCE` | `MISSING_APPROVAL` |
| `CASE-003` | `INV-1003` | Invoice issued in 2026, but AMD-003 was only effective during calendar year 2025 | `NOT_VERIFIED` | `INVALID_EFFECTIVE_PERIOD` |
| `CASE-004` | `INV-1004` | AMD-004 discounts `PROD-SEC`, but invoice is billed for infrastructure `PROD-INFRA` | `NOT_VERIFIED` | `WRONG_PRODUCT_SCOPE` |
| `CASE-005` | `INV-1005` | Overlapping amendments AMD-005 ($11,000) and AMD-006 ($11,500) conflict without clear precedence | `NEEDS_REVIEW` | `CONFLICTING_AMENDMENTS` |
| `CASE-006` | `INV-1006` | Invoice $15,000 exceeds baseline $12,000; no amendment or approval exists | `NOT_VERIFIED` | `NO_APPLICABLE_AMENDMENT` |
| `CASE-007` | `INV-1007` | Invoice exists for CUS-003, but no governing contract is established in repository | `INSUFFICIENT_EVIDENCE` | `MISSING_CONTRACT` |
| `CASE-008` | `INV-1008` | SOW-002 under CTR-002 with authorized exception EX-008 and approval APR-008 | `VERIFIED` | `null` |

---

## Ground Truth Semantics

- **`VERIFIED`**: All required conditions (governing contract, applicable amendment/SOW, effective date period, product scope, and required approval) are substantiated by evidence.
- **`NOT_VERIFIED`**: Evidence proves the claimed exception is legally or contractually invalid (e.g. wrong product, expired effective date, unauthorized overage).
- **`INSUFFICIENT_EVIDENCE`**: Critical evidence is missing from the record (e.g. missing approval record, unresolvable governing contract).
- **`NEEDS_REVIEW`**: Evidence is contradictory or creates legal ambiguity that cannot be resolved deterministically without human review.

---

## Automated Validation

To run the consistency tests across the entire dataset:
```bash
cd apps/api
venv\Scripts\python.exe -m pytest tests/test_dataset_consistency.py -v
```

This verifies:
1. Every record parses cleanly into its respective Stage 11 Pydantic domain model.
2. All entity identifiers are unique within their collection.
3. Referential foreign-key integrity between contracts, amendments, SOWs, exceptions, approvals, and invoices.
4. Ground truth referential integrity (all cited evidence, amendments, and invoices exist).
5. All intentional missing evidence is documented and matches expected failure conditions.
6. All date ranges and Decimal monetary representations are mathematically valid.
