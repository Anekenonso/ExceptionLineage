"""Deterministic validation rules for ExceptionLineage investigation evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from app.models.enums import ValidationStatus
from app.models.validation import ValidationResult
from app.validation.context import InvestigationContext


class BaseValidationRule(ABC):
    """Abstract base class for deterministic validation rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the validation check."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this rule verifies."""
        ...

    @property
    def is_required(self) -> bool:
        """Whether passing this check is mandatory for overall verification."""
        return True

    @abstractmethod
    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        """Deterministically evaluate this rule against the provided context.

        Must return a ValidationResult with status PASS, FAIL, or UNKNOWN.
        """
        ...


class CustomerGoverningContractRule(BaseValidationRule):
    """Verifies that the invoice belongs to the customer governed by the contract."""

    @property
    def name(self) -> str:
        return "customer_governing_contract"

    @property
    def description(self) -> str:
        return "Verifies that the invoice belongs to the customer governed by the master agreement."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; customer relationship cannot be verified.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        contract_id = ctx.contract_id or ""
        evidence_ids = [ev["id"] for ev in ctx.evidence_for(contract_id)]

        if ctx.contract_customer_id == ctx.invoice_customer_id:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message=f"Invoice customer '{ctx.invoice_customer_id}' matches governing contract '{contract_id}' customer.",
                evidence_ids=evidence_ids,
                is_required=self.is_required,
            )

        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message=(
                f"Invoice customer '{ctx.invoice_customer_id}' does not match governing contract '{contract_id}' "
                f"customer '{ctx.contract_customer_id}'."
            ),
            evidence_ids=evidence_ids,
            is_required=self.is_required,
        )


class ContractApplicabilityRule(BaseValidationRule):
    """Verifies that the governing contract was active and applicable on the invoice issue date."""

    @property
    def name(self) -> str:
        return "contract_applicability"

    @property
    def description(self) -> str:
        return "Verifies that the governing contract was ACTIVE and legally effective on invoice issue date."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; contract applicability cannot be evaluated.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        contract_id = ctx.contract_id or ""
        evidence_ids = [ev["id"] for ev in ctx.evidence_for(contract_id)]

        if ctx.contract_status != "ACTIVE":
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message=f"Governing contract '{contract_id}' status is '{ctx.contract_status}', expected ACTIVE.",
                evidence_ids=evidence_ids,
                is_required=self.is_required,
            )

        c_from = ctx.contract_effective_from
        c_until = ctx.contract_effective_until
        inv_date = ctx.invoice_issued_at

        if c_from and inv_date < c_from:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message=f"Invoice issue date {inv_date.date()} is prior to contract effective start date {c_from.date()}.",
                evidence_ids=evidence_ids,
                is_required=self.is_required,
            )

        if c_until and inv_date > c_until:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message=f"Invoice issue date {inv_date.date()} is after contract expiration date {c_until.date()}.",
                evidence_ids=evidence_ids,
                is_required=self.is_required,
            )

        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.PASS,
            message=f"Governing contract '{contract_id}' is ACTIVE and legally effective on invoice issue date {inv_date.date()}.",
            evidence_ids=evidence_ids,
            is_required=self.is_required,
        )


class ConflictingAuthorityRule(BaseValidationRule):
    """Verifies that there are no contradictory amendments or competing schedules."""

    @property
    def name(self) -> str:
        return "conflicting_authority"

    @property
    def description(self) -> str:
        return "Verifies that there are no contradictory amendments or unresolved conflicting authorities."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; conflicting authority cannot be evaluated.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        target_product = ctx.invoice_product_id

        # Check for multiple amendments for the same product with differing rates
        if len(ctx.amendments) >= 2 and target_product:
            relevant_amds: list[dict[str, Any]] = []
            for amd in ctx.amendments:
                amd_id = amd["id"]
                scope = ctx.get_amendment_scope(amd_id)
                if scope == target_product:
                    relevant_amds.append(amd)

            if len(relevant_amds) >= 2:
                rates = {ctx.get_amendment_rate(a["id"]) for a in relevant_amds}
                rates.discard(None)
                if len(rates) > 1:
                    conflicting_ids = [a["id"] for a in relevant_amds]
                    evidence_ids: list[str] = []
                    for aid in conflicting_ids:
                        evidence_ids.extend([ev["id"] for ev in ctx.evidence_for(aid)])
                    if ctx.approval:
                        evidence_ids.extend([ev["id"] for ev in ctx.evidence_for(ctx.approval["id"])])

                    return ValidationResult(
                        check_name=self.name,
                        status=ValidationStatus.FAIL,
                        message=(
                            f"Conflicting executed amendments detected: {conflicting_ids} specify contradictory "
                            f"rates ({sorted([str(r) for r in rates])}) for product '{target_product}'."
                        ),
                        evidence_ids=sorted(list(set(evidence_ids))),
                        is_required=self.is_required,
                    )

        # Check if approval context or evidence notes unresolved conflict
        if ctx.approval and ctx.approval.get("status") == "PENDING":
            ctx_json = str(ctx.approval.get("context_json") or ctx.approval.get("context") or "")
            if "conflict" in ctx_json.lower() or "escalated" in ctx_json.lower():
                ev_ids = [ev["id"] for ev in ctx.evidence_for(ctx.approval["id"])]
                return ValidationResult(
                    check_name=self.name,
                    status=ValidationStatus.FAIL,
                    message=f"Unresolved contractual conflict flagged in approval escalation '{ctx.approval['id']}'.",
                    evidence_ids=ev_ids,
                    is_required=self.is_required,
                )

        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.PASS,
            message="No conflicting contractual amendments or authorities detected.",
            evidence_ids=[],
            is_required=self.is_required,
        )


class ApplicableAmendmentRule(BaseValidationRule):
    """Verifies that an applicable amendment or SOW exists if the invoice varies from contract baseline."""

    @property
    def name(self) -> str:
        return "applicable_amendment"

    @property
    def description(self) -> str:
        return "Verifies that an applicable amendment or SOW exists when invoice amount differs from baseline."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; applicable amendments cannot be determined.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        baseline = ctx.contract_baseline_rate
        contract_ev = [ev["id"] for ev in ctx.evidence_for(ctx.contract_id or "")]

        # If invoice matches baseline and no exception exists, baseline applies
        if baseline is not None and ctx.invoice_amount == baseline and not ctx.exception:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message="Invoice amount matches contract baseline; no amendment required.",
                evidence_ids=contract_ev,
                is_required=self.is_required,
            )

        # Invoice varies from baseline or an exception exists
        # To be an applicable amendment, it must authorize the invoice amount/variance
        authorizing_amds = [
            a for a in ctx.amendments
            if ctx.get_amendment_rate(a["id"]) == ctx.invoice_amount
        ]

        # Or SOW covers product with an accompanying amendment
        sow_match = any(
            ctx.get_sow_scope(s["id"]) == ctx.invoice_product_id
            for s in ctx.sows
        )

        if not authorizing_amds and not (sow_match and ctx.amendments):
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message=(
                    f"Invoice amount ${ctx.invoice_amount} differs from contract baseline "
                    f"${baseline or 'unknown'}, but no authorizing amendment exists in the repository."
                ),
                evidence_ids=contract_ev,
                is_required=self.is_required,
            )

        found_amds = authorizing_amds or ctx.amendments
        evidence_ids: list[str] = list(contract_ev)
        for a in found_amds:
            evidence_ids.extend([ev["id"] for ev in ctx.evidence_for(a["id"])])
        for s in ctx.sows:
            evidence_ids.extend([ev["id"] for ev in ctx.evidence_for(s["id"])])

        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.PASS,
            message=f"Found applicable candidate amendment(s): {[a['id'] for a in found_amds]}.",
            evidence_ids=sorted(list(set(evidence_ids))),
            is_required=self.is_required,
        )


class AmendmentEffectivenessRule(BaseValidationRule):
    """Verifies that candidate amendments or SOWs were legally effective on the invoice issue date."""

    @property
    def name(self) -> str:
        return "amendment_effectiveness"

    @property
    def description(self) -> str:
        return "Verifies that the governing amendment or SOW was legally effective on invoice issue date."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; amendment effectiveness cannot be evaluated.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        baseline = ctx.contract_baseline_rate
        if baseline is not None and ctx.invoice_amount == baseline and not ctx.exception:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message="Standard contract baseline applies; no amendment required.",
                evidence_ids=[ev["id"] for ev in ctx.evidence_for(ctx.contract_id or "")],
                is_required=self.is_required,
            )

        candidates = ctx.get_candidate_amendments()
        if not candidates and not ctx.sows:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message="No amendment exists in the lineage to evaluate effective period.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        inv_date = ctx.invoice_issued_at

        # Check each candidate amendment
        active_candidates: list[dict[str, Any]] = []
        expired_candidates: list[tuple[dict[str, Any], str]] = []

        for amd in candidates:
            # Check dates on amendment node or linked evidence
            a_from_str = amd.get("effective_from")
            a_until_str = amd.get("effective_until")

            evidence_items = ctx.evidence_for(amd["id"])
            for ev in evidence_items:
                if ev.get("effective_from"):
                    a_from_str = ev["effective_from"]
                if ev.get("effective_until"):
                    a_until_str = ev["effective_until"]

            from app.validation.context import parse_datetime

            a_from = parse_datetime(a_from_str)
            a_until = parse_datetime(a_until_str)

            if a_from and inv_date < a_from:
                expired_candidates.append((amd, f"not yet effective (starts {a_from.date()})"))
            elif a_until and inv_date > a_until:
                expired_candidates.append((amd, f"expired on {a_until.date()}"))
            else:
                active_candidates.append(amd)

        if active_candidates:
            ev_ids = [ev["id"] for a in active_candidates for ev in ctx.evidence_for(a["id"])]
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message=(
                    f"Amendment '{active_candidates[0]['id']}' was legally effective on invoice issue "
                    f"date {inv_date.date()}."
                ),
                evidence_ids=sorted(list(set(ev_ids))),
                is_required=self.is_required,
            )

        # All candidates are expired or inapplicable on invoice date
        failed_amd, reason = expired_candidates[0]
        ev_ids = [ev["id"] for ev in ctx.evidence_for(failed_amd["id"])]
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message=(
                f"Candidate amendment '{failed_amd['id']}' was {reason} and was not effective on "
                f"invoice issue date {inv_date.date()}."
            ),
            evidence_ids=ev_ids,
            is_required=self.is_required,
        )


class AmendmentScopeRule(BaseValidationRule):
    """Verifies that the amendment or SOW scope covers the specific product billed on the invoice."""

    @property
    def name(self) -> str:
        return "amendment_scope_match"

    @property
    def description(self) -> str:
        return "Verifies that the amendment or SOW scope covers the specific billed product."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; amendment scope cannot be evaluated.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        baseline = ctx.contract_baseline_rate
        if baseline is not None and ctx.invoice_amount == baseline and not ctx.exception:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message="Standard contract baseline applies; no amendment scope restriction.",
                evidence_ids=[ev["id"] for ev in ctx.evidence_for(ctx.contract_id or "")],
                is_required=self.is_required,
            )

        target_product = ctx.invoice_product_id
        if not target_product:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Invoice does not specify a product_id; scope match cannot be verified.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        # 1. Check if SOW covers target product
        for sow in ctx.sows:
            sow_scope = ctx.get_sow_scope(sow["id"])
            if sow_scope == target_product:
                ev_ids = [ev["id"] for ev in ctx.evidence_for(sow["id"])]
                for amd in ctx.amendments:
                    ev_ids.extend([ev["id"] for ev in ctx.evidence_for(amd["id"])])
                return ValidationResult(
                    check_name=self.name,
                    status=ValidationStatus.PASS,
                    message=f"Statement of Work '{sow['id']}' scope covers billed product '{target_product}'.",
                    evidence_ids=sorted(list(set(ev_ids))),
                    is_required=self.is_required,
                )

        # 2. Check amendments covering target product
        matching_amds = [a for a in ctx.amendments if ctx.get_amendment_scope(a["id"]) == target_product]
        if matching_amds:
            ev_ids = [ev["id"] for a in matching_amds for ev in ctx.evidence_for(a["id"])]
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message=f"Amendment '{matching_amds[0]['id']}' scope matches billed product '{target_product}'.",
                evidence_ids=sorted(list(set(ev_ids))),
                is_required=self.is_required,
            )

        # 3. If an amendment exists with matching rate but different scope
        rate_matches = [a for a in ctx.amendments if ctx.get_amendment_rate(a["id"]) == ctx.invoice_amount]
        if rate_matches:
            target_amd = rate_matches[0]
            amd_scope = ctx.get_amendment_scope(target_amd["id"])
            ev_ids = [ev["id"] for ev in ctx.evidence_for(target_amd["id"])]
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.FAIL,
                message=(
                    f"Amendment '{target_amd['id']}' authorizes rate ${ctx.invoice_amount} strictly for scope "
                    f"'{amd_scope}', which does not apply to billed product '{target_product}'."
                ),
                evidence_ids=ev_ids,
                is_required=self.is_required,
            )

        # No amendment found
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message=f"No amendment in contract lineage authorizes scope for product '{target_product}'.",
            evidence_ids=[ev["id"] for ev in ctx.evidence_for(ctx.contract_id or "")],
            is_required=self.is_required,
        )


class ApprovalAuthorizationRule(BaseValidationRule):
    """Verifies that any required operational or executive approval is present and APPROVED."""

    @property
    def name(self) -> str:
        return "approval_authorization"

    @property
    def description(self) -> str:
        return "Verifies that required operational or executive approval is documented and approved."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        # Check if approval is required
        # Approval is required if:
        # 1. An exception exists
        # 2. An amendment terms clause conditions rate on approval
        # 3. Invoice varies from baseline
        requires_approval = False

        if ctx.exception is not None:
            requires_approval = True

        for ev in ctx.evidence:
            excerpt = ev.get("excerpt", "").lower()
            if "approval" in excerpt or "signoff" in excerpt or "contingent on" in excerpt:
                requires_approval = True
                break

        if not requires_approval:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message="No approval required for standard baseline billing.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        # Approval is required
        if ctx.approval is None:
            # Check which evidence notes approval requirement
            approval_requirement_ev = [
                ev["id"]
                for ev in ctx.evidence
                if "approval" in ev.get("excerpt", "").lower() or "approval" in ev.get("title", "").lower()
            ]
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Required approval record is missing from the approval repository.",
                evidence_ids=approval_requirement_ev,
                is_required=self.is_required,
            )

        approval_id = ctx.approval.get("id") or ""
        approval_status = ctx.approval.get("status")
        approver = ctx.approval.get("approver", "unknown approver")
        ev_ids = [ev["id"] for ev in ctx.evidence_for(approval_id)]

        if approval_status == "APPROVED":
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message=f"Required approval '{approval_id}' granted by {approver}.",
                evidence_ids=ev_ids,
                is_required=self.is_required,
            )

        if approval_status == "PENDING":
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message=f"Approval '{approval_id}' is PENDING signoff; review pending.",
                evidence_ids=ev_ids,
                is_required=self.is_required,
            )

        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message=f"Approval '{approval_id}' was REJECTED by {approver}.",
            evidence_ids=ev_ids,
            is_required=self.is_required,
        )


class AuthorizedAmountRule(BaseValidationRule):
    """Verifies that the invoiced amount matches the legally authorized rate."""

    @property
    def name(self) -> str:
        return "authorized_amount_match"

    @property
    def description(self) -> str:
        return "Verifies that the billed invoice amount matches the legally authorized contractual or amended rate."

    def evaluate(self, ctx: InvestigationContext) -> ValidationResult:
        if not ctx.has_contract:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.UNKNOWN,
                message="Governing contract is missing; authorized amount cannot be verified.",
                evidence_ids=[],
                is_required=self.is_required,
            )

        contract_ev = [ev["id"] for ev in ctx.evidence_for(ctx.contract_id or "")]
        target_product = ctx.invoice_product_id
        invoice_amount = ctx.invoice_amount
        baseline = ctx.contract_baseline_rate

        # 1. Check if SOW + Amendment authorizes this rate for product
        for sow in ctx.sows:
            if ctx.get_sow_scope(sow["id"]) == target_product:
                for amd in ctx.amendments:
                    amd_rate = ctx.get_amendment_rate(amd["id"])
                    if amd_rate == invoice_amount:
                        ev_ids = list(contract_ev)
                        ev_ids.extend([ev["id"] for ev in ctx.evidence_for(sow["id"])])
                        ev_ids.extend([ev["id"] for ev in ctx.evidence_for(amd["id"])])
                        return ValidationResult(
                            check_name=self.name,
                            status=ValidationStatus.PASS,
                            message=f"Invoice billed amount ${invoice_amount} matches rate authorized under {sow['id']} and {amd['id']}.",
                            evidence_ids=sorted(list(set(ev_ids))),
                            is_required=self.is_required,
                        )

        # 2. Check if an amendment matching product scope authorizes this rate
        for amd in ctx.amendments:
            if ctx.get_amendment_scope(amd["id"]) == target_product:
                amd_rate = ctx.get_amendment_rate(amd["id"])
                if amd_rate == invoice_amount:
                    ev_ids = list(contract_ev)
                    ev_ids.extend([ev["id"] for ev in ctx.evidence_for(amd["id"])])
                    return ValidationResult(
                        check_name=self.name,
                        status=ValidationStatus.PASS,
                        message=f"Invoice billed amount ${invoice_amount} matches rate authorized by amendment '{amd['id']}'.",
                        evidence_ids=sorted(list(set(ev_ids))),
                        is_required=self.is_required,
                    )

        # 3. Check if invoice matches baseline standard rate
        if baseline is not None and invoice_amount == baseline:
            return ValidationResult(
                check_name=self.name,
                status=ValidationStatus.PASS,
                message=f"Invoice billed amount ${invoice_amount} matches contract baseline rate ${baseline}.",
                evidence_ids=contract_ev,
                is_required=self.is_required,
            )

        # 4. Unauthorized amount
        return ValidationResult(
            check_name=self.name,
            status=ValidationStatus.FAIL,
            message=(
                f"Invoice billed amount ${invoice_amount} does not match any legally authorized contractual "
                f"or amended rate (baseline: ${baseline or 'unknown'})."
            ),
            evidence_ids=contract_ev,
            is_required=self.is_required,
        )


def get_default_validation_rules() -> list[BaseValidationRule]:
    """Return the ordered list of standard deterministic validation rules."""
    return [
        CustomerGoverningContractRule(),
        ContractApplicabilityRule(),
        ConflictingAuthorityRule(),
        ApplicableAmendmentRule(),
        AmendmentEffectivenessRule(),
        AmendmentScopeRule(),
        ApprovalAuthorizationRule(),
        AuthorizedAmountRule(),
    ]
