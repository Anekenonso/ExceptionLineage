"""Deterministic validation engine for ExceptionLineage investigation evaluation."""

from __future__ import annotations

import logging
from typing import Any

from app.models.enums import InvestigationStatus, ValidationStatus
from app.models.validation import ValidationResult
from app.validation.context import InvestigationContext
from app.validation.models import ValidationOutcome
from app.validation.rules import BaseValidationRule, get_default_validation_rules

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Evaluates explicit deterministic rules against retrieved investigation context.

    Core Principles:
    - Completely deterministic (no LLM, no probabilistic reasoning, no hardcoded shortcuts).
    - Tri-state rule evaluation (PASS, FAIL, UNKNOWN are never collapsed).
    - Clear separation between retrieval and evaluation.
    """

    def __init__(self, rules: list[BaseValidationRule] | None = None) -> None:
        self.rules = rules if rules is not None else get_default_validation_rules()

    def validate(self, context_or_lineage: InvestigationContext | dict[str, Any]) -> ValidationOutcome:
        """Run deterministic validation checks on the supplied investigation context.

        Args:
            context_or_lineage: Either an InvestigationContext instance or a raw dictionary
                                returned by get_invoice_lineage.

        Returns:
            A ValidationOutcome containing individual ValidationResult checks and the overall
            investigation status.
        """
        if isinstance(context_or_lineage, dict):
            ctx = InvestigationContext.from_lineage(context_or_lineage)
        elif isinstance(context_or_lineage, InvestigationContext):
            ctx = context_or_lineage
        else:
            raise TypeError(
                f"Expected InvestigationContext or dict, got {type(context_or_lineage).__name__}"
            )

        # 1. Evaluate all rules
        results: list[ValidationResult] = []
        for rule in self.rules:
            try:
                res = rule.evaluate(ctx)
                results.append(res)
            except Exception as exc:
                logger.exception("Error evaluating rule '%s': %s", rule.name, exc)
                results.append(
                    ValidationResult(
                        check_name=rule.name,
                        status=ValidationStatus.UNKNOWN,
                        message=f"Rule evaluation error: {exc}",
                        evidence_ids=[],
                        is_required=rule.is_required,
                    )
                )

        # 2. Gather cited evidence IDs
        cited_evidence: set[str] = set()
        for r in results:
            for eid in r.evidence_ids:
                cited_evidence.add(eid)

        # 3. Determine overall status and summary
        outcome_status, summary, failure_reason = self._determine_outcome(ctx, results)

        return ValidationOutcome(
            status=outcome_status,
            summary=summary,
            results=results,
            cited_evidence_ids=sorted(list(cited_evidence)),
            failure_reason=failure_reason,
        )

    def _determine_outcome(
        self,
        ctx: InvestigationContext,
        results: list[ValidationResult],
    ) -> tuple[InvestigationStatus, str, str | None]:
        """Aggregate discrete rule results into an overall investigation outcome."""
        failed_results = [r for r in results if r.status == ValidationStatus.FAIL and r.is_required]
        unknown_results = [r for r in results if r.status == ValidationStatus.UNKNOWN and r.is_required]

        # 1. Check for conflicting authority or escalated review
        conflict_check = next((r for r in results if r.check_name == "conflicting_authority"), None)
        has_conflict = conflict_check is not None and conflict_check.status == ValidationStatus.FAIL
        has_pending_escalation = (
            ctx.approval is not None and ctx.approval.get("status") == "PENDING"
        )

        if has_conflict or (has_pending_escalation and not failed_results):
            reason = conflict_check.message if conflict_check and conflict_check.message else (
                "Unresolved approval escalation or conflicting contractual terms detected."
            )
            summary = (
                f"Investigation for invoice '{ctx.invoice_id}' requires human review: "
                f"conflicting contractual authority or pending approvals detected."
            )
            return InvestigationStatus.NEEDS_REVIEW, summary, reason

        # 2. Check for explicit rule failures
        if failed_results:
            failure_messages = [f"{r.check_name}: {r.message}" for r in failed_results if r.message]
            primary_reason = failure_messages[0] if failure_messages else "One or more contractual validation checks failed."
            summary = (
                f"Invoice '{ctx.invoice_id}' amount ${ctx.invoice_amount} could not be verified: "
                f"{len(failed_results)} contractual check(s) failed."
            )
            return InvestigationStatus.NOT_VERIFIED, summary, primary_reason

        # 3. Check for missing required evidence (UNKNOWN state)
        if unknown_results:
            unknown_messages = [f"{r.check_name}: {r.message}" for r in unknown_results if r.message]
            primary_reason = unknown_messages[0] if unknown_messages else "Essential evidence missing from repository."
            summary = (
                f"Investigation for invoice '{ctx.invoice_id}' is inconclusive: "
                f"essential contractual or approval evidence is missing."
            )
            return InvestigationStatus.INSUFFICIENT_EVIDENCE, summary, primary_reason

        # 4. All required checks passed
        summary = (
            f"Invoice '{ctx.invoice_id}' amount ${ctx.invoice_amount} is authorized and verified "
            f"under governing contract '{ctx.contract_id}'."
        )
        return InvestigationStatus.VERIFIED, summary, None
