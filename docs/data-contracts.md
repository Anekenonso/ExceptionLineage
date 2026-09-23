# ExceptionLineage Data Contracts

This document specifies the core domain vocabulary, schemas, and contracts for ExceptionLineage (Stage 11).

## Principles

1. **Contracts, not workflows**: Models define the structure and legal vocabulary of entities, not state transition machines or validation execution.
2. **Explicit identifiers over nested graphs**: Relationships are maintained via stable string IDs (e.g. `customer_id`, `contract_id`) to avoid circular dependencies and permit flexible graph/database storage.
3. **Exact monetary values**: All monetary amounts are represented using `Decimal` to eliminate binary floating-point representation errors.
4. **Timezone-aware datetimes**: All timestamps are timezone-aware (UTC). Naive datetimes are strictly rejected.
5. **Legitimate UNKNOWN state**: In deterministic validation checks, `UNKNOWN` indicates indeterminate or missing evidence and is never coerced to `PASS` or `FAIL`.
6. **Bounded confidence**: Evidence confidence is bounded to $[0.0, 1.0]$ and serves as an informational attribute, not proof.

---

## Relationship Graph

```
Customer
  ↓ (customer_id)
Contract
  ├── Amendment (contract_id)
  ├── SOW (contract_id)
  └── Exception (contract_id)
        ↓ (exception_id)
      Approval

Invoice
  ├── Customer (customer_id)
  ├── Contract [optional] (contract_id)
  └── Exception [optional] (exception_id)

Investigation
  ├── Invoice (invoice_id)
  ├── Exception [optional] (exception_id)
  ├── Evidence [cited via evidence_ids]
  ├── InvestigationEvent (investigation_id)
  └── ValidationResult (evidence_ids)
```

---

## Domain Entities

### 1. Customer
Represents an enterprise customer.
- `id` (str, required, non-empty): Stable unique customer identifier.
- `name` (str, required, non-empty): Enterprise customer legal name.
- `external_id` (str, optional): Reference ID in external ERP/CRM.
- `created_at` (datetime, UTC): Timestamp of customer record creation.

### 2. Contract
Represents the governing master agreement.
- `id` (str, required, non-empty): Unique contract ID.
- `customer_id` (str, required, non-empty): Target customer reference.
- `title` (str, required, non-empty): Contract title.
- `effective_from` (datetime, UTC): Start of validity period.
- `effective_until` (datetime, UTC, optional): End of validity period (`effective_until >= effective_from`).
- `status` (`ContractStatus`): `DRAFT`, `ACTIVE`, `EXPIRED`, `TERMINATED`.
- `currency` (str, default `"USD"`): Governing currency code.
- `created_at` / `updated_at` (datetime, UTC).

### 3. Amendment
Represents a formal modification to an existing contract.
- `id` (str, required, non-empty): Unique amendment ID.
- `contract_id` (str, required, non-empty): Parent contract reference.
- `amendment_number` (str, required, non-empty): Sequence/reference number (e.g. `AMD-001`).
- `title` (str, required, non-empty): Amendment title.
- `description` (str, optional): Description of amended clauses or scope.
- `effective_from` (datetime, UTC): Effective start timestamp.
- `effective_until` (datetime, UTC, optional): Effective end timestamp (`effective_until >= effective_from`).
- `created_at` / `updated_at` (datetime, UTC).

### 4. SOW (Statement of Work)
Represents work authorization under a governing contract.
- `id` (str, required, non-empty): Unique SOW ID.
- `contract_id` (str, required, non-empty): Parent contract reference.
- `reference` (str, required, non-empty): Reference identifier (e.g. `SOW-2026-01`).
- `title` (str, required, non-empty): SOW title.
- `scope` (str, optional): Scope of work description or milestones.
- `effective_from` (datetime, UTC): SOW start timestamp.
- `effective_until` (datetime, UTC, optional): SOW end timestamp (`effective_until >= effective_from`).
- `created_at` / `updated_at` (datetime, UTC).

### 5. Exception (alias: `TransactionException`)
Represents an operational or financial transaction exception detected in enterprise processing.
- `id` (str, required, non-empty): Unique exception ID.
- `contract_id` (str, required, non-empty): Governing contract reference.
- `invoice_id` (str, optional): Associated invoice reference.
- `exception_type` (str, required, non-empty): Exception category code (e.g. `RATE_MISMATCH`, `UNAPPROVED_EXPENSE`).
- `description` (str, required, non-empty): Context and details.
- `expected_amount` (Decimal, optional): Expected monetary amount as an exact Decimal.
- `actual_amount` (Decimal, optional): Actual charged amount as an exact Decimal.
- `currency` (str, default `"USD"`): Monetary currency code.
- `created_at` / `updated_at` (datetime, UTC).

### 6. Approval
Represents an explicit authorization or exception waiver.
- `id` (str, required, non-empty): Unique approval ID.
- `exception_id` (str, required, non-empty): Exception being authorized.
- `approver` (str, required, non-empty): Approving authority name or email.
- `status` (`ApprovalStatus`): `PENDING`, `APPROVED`, `REJECTED`.
- `approved_at` (datetime, UTC, optional): Timestamp authorization was granted.
- `context` (dict | str, optional): Contextual metadata or justification.
- `created_at` (datetime, UTC).

### 7. Invoice
Represents the billed transaction under investigation.
- `id` (str, required, non-empty): Invoice identifier.
- `customer_id` (str, required, non-empty): Billed customer reference.
- `contract_id` (str, optional): Associated contract reference.
- `exception_id` (str, optional): Associated exception reference.
- `product_id` (str, optional): Associated product or SKU reference.
- `amount` (Decimal, required): Exact monetary amount as a Decimal.
- `currency` (str, required, non-empty): Currency code.
- `issued_at` (datetime, UTC, required): Timestamp when invoice was issued.
- `due_at` (datetime, UTC, optional): Due date (`due_at >= issued_at`).
- `created_at` (datetime, UTC).

### 8. Evidence
Represents an evidentiary artifact supporting or refuting investigation findings.
- `id` (str, required, non-empty): Unique evidence record ID.
- `evidence_type` (str, required, non-empty): E.g. `CONTRACT_CLAUSE`, `AMENDMENT_TERMS`, `APPROVAL_RECORD`.
- `source` (str, required, non-empty): Originating repository or system.
- `source_id` (str, required, non-empty): Primary key of the source document/record.
- `title` (str, optional): Brief descriptive title.
- `locator` (str, optional): Location pointer within source (e.g. `"Section 3.1, Line 12"`).
- `excerpt` (str, optional): Exact quoted excerpt or content reference.
- `captured_at` (datetime, UTC): Timestamp evidence was ingested.
- `effective_from` / `effective_until` (datetime, UTC, optional): Validity period (`effective_until >= effective_from`).
- `scope` (str, optional): Domain or jurisdictional scope.
- `confidence` (float, optional): Assessment confidence bounded to $[0.0, 1.0]$.

### 9. Investigation
Represents an evidence-driven investigation lifecycle.
- `id` (str, required, non-empty): Unique investigation ID.
- `invoice_id` (str, required, non-empty): Subject invoice reference.
- `exception_id` (str, optional): Subject exception reference.
- `status` (`InvestigationStatus`):
  - **Active states**: `QUEUED`, `INVESTIGATING`, `VALIDATING`
  - **Terminal states**: `VERIFIED`, `NOT_VERIFIED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_REVIEW`, `FAILED`
- `summary` (str, optional): Narrative conclusion.
- `failure_reason` (str, optional): Failure or escalation details.
- `created_at` / `updated_at` (datetime, UTC).

### 10. InvestigationEvent
Represents an auditable event in the timeline of an investigation.
- `id` (str, required, non-empty): Unique event ID.
- `investigation_id` (str, required, non-empty): Parent investigation reference.
- `event_type` (`InvestigationEventType` | str): `INPUT`, `EVIDENCE_FOUND`, `AGENT_DECISION`, `TOOL_CALL`, `VALIDATION`, `ACTION_RESULT`.
- `message` (str, required, non-empty): Event narrative.
- `timestamp` (datetime, UTC): Timestamp of occurrence.
- `metadata` (dict, default `{}`): Arbitrary structured payloads (tool outputs, diffs, metrics).

### 11. ValidationResult
Represents the atomic result of a deterministic validation rule check.
- `check_name` (str, required, non-empty): Name of the check executed (e.g. `"approval_authorization_check"`).
- `status` (`ValidationStatus`):
  - `PASS`: Requirement definitively verified by evidence.
  - `FAIL`: Requirement violated.
  - `UNKNOWN`: Evidence is missing, inconclusive, or indeterminate.
- `message` (str, optional): Detail or rationale.
- `evidence_ids` (list[str], default `[]`): Explicit IDs of supporting `Evidence` records.
- `timestamp` (datetime, UTC): Timestamp check was performed.
- `is_required` (bool, default `True`): Whether this check is mandatory for overall verification.
