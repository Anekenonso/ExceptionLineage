"""Investigation lifecycle service orchestrating the non-agent investigation skeleton."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.investigations.exceptions import (
    InvestigationNotFoundError,
    InvalidStateTransitionError,
)
from app.investigations.repository import (
    InMemoryInvestigationRepository,
    InvestigationRepository,
)
from app.investigations.state_machine import InvestigationStateMachine
from app.models.common import utc_now
from app.models.enums import InvestigationStatus
from app.models.investigation import Investigation, InvestigationEvent
from app.validation.context import InvestigationContext
from app.validation.engine import ValidationEngine
from app.validation.models import ValidationOutcome

logger = logging.getLogger(__name__)


class InvestigationService:
    """Service representing the controlled investigation lifecycle.

    Lifecycle Progression:
        create investigation -> QUEUED
        start investigation  -> INVESTIGATING
        move to validation   -> VALIDATING
        apply outcome        -> VERIFIED | NOT_VERIFIED | INSUFFICIENT_EVIDENCE | NEEDS_REVIEW | FAILED

    Adheres strictly to the architectural boundary:
        AI handles ambiguity. Code handles authority.
    """

    def __init__(
        self,
        repository: InvestigationRepository | None = None,
        state_machine: InvestigationStateMachine | None = None,
        validation_engine: ValidationEngine | None = None,
    ) -> None:
        self.repository = (
            repository if repository is not None else InMemoryInvestigationRepository()
        )
        self.state_machine = (
            state_machine
            if state_machine is not None
            else InvestigationStateMachine(repository=self.repository)
        )
        # Ensure state machine persistence delegates to this service's repository
        if self.state_machine.repository is None:
            self.state_machine.repository = self.repository

        self.validation_engine = (
            validation_engine if validation_engine is not None else ValidationEngine()
        )

    def create_investigation(
        self,
        invoice_id: str,
        exception_id: str | None = None,
        investigation_id: str | None = None,
    ) -> Investigation:
        """Create a new investigation in the initial QUEUED lifecycle state."""
        inv_id = investigation_id or f"invg-{uuid.uuid4().hex[:12]}"
        inv = Investigation(
            id=inv_id,
            invoice_id=invoice_id,
            exception_id=exception_id,
            status=InvestigationStatus.QUEUED,
            created_at=utc_now(),
        )
        return self.repository.create(inv)

    def get_investigation(self, investigation_id: str) -> Investigation:
        """Retrieve an investigation by ID or raise InvestigationNotFoundError."""
        inv = self.repository.get(investigation_id)
        if inv is None:
            raise InvestigationNotFoundError(investigation_id)
        return inv

    def get_events(self, investigation_id: str) -> list[InvestigationEvent]:
        """Retrieve the immutable chronological audit event history for an investigation."""
        # Ensure investigation exists
        self.get_investigation(investigation_id)
        return self.repository.get_events(investigation_id)

    def start_investigation(
        self,
        investigation_id: str,
        reason: str = "Investigation started",
    ) -> tuple[Investigation, InvestigationEvent]:
        """Transition an investigation from QUEUED to INVESTIGATING."""
        inv = self.get_investigation(investigation_id)
        event = self.state_machine.transition(
            inv,
            target_state=InvestigationStatus.INVESTIGATING,
            reason=reason,
        )
        return inv, event

    def move_to_validation(
        self,
        investigation_id: str,
        reason: str = "Evidence gathered; proceeding to deterministic validation",
    ) -> tuple[Investigation, InvestigationEvent]:
        """Transition an investigation from INVESTIGATING to VALIDATING."""
        inv = self.get_investigation(investigation_id)
        event = self.state_machine.transition(
            inv,
            target_state=InvestigationStatus.VALIDATING,
            reason=reason,
        )
        return inv, event

    def apply_validation_outcome(
        self,
        investigation_id: str,
        outcome: ValidationOutcome,
    ) -> tuple[Investigation, InvestigationEvent]:
        """Apply a ValidationOutcome from the deterministic validation engine to reach a terminal outcome.

        Mapping from ValidationOutcome to InvestigationStatus:
            VERIFIED              -> VERIFIED
            NOT_VERIFIED          -> NOT_VERIFIED
            INSUFFICIENT_EVIDENCE -> INSUFFICIENT_EVIDENCE
            NEEDS_REVIEW          -> NEEDS_REVIEW
        """
        inv = self.get_investigation(investigation_id)
        target_state = outcome.status
        reason = outcome.failure_reason or outcome.summary

        event = self.state_machine.transition(
            inv,
            target_state=target_state,
            reason=reason,
            metadata={
                "summary": outcome.summary,
                "failure_reason": outcome.failure_reason,
                "cited_evidence_ids": outcome.cited_evidence_ids,
                "passed_checks_count": len(outcome.passed_checks),
                "failed_checks_count": len(outcome.failed_checks),
                "unknown_checks_count": len(outcome.unknown_checks),
            },
        )

        inv.summary = outcome.summary
        inv.failure_reason = outcome.failure_reason
        self.repository.update(inv)

        return inv, event

    def fail_investigation(
        self,
        investigation_id: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Investigation, InvestigationEvent]:
        """Transition an active investigation to FAILED due to technical or infrastructure failure."""
        inv = self.get_investigation(investigation_id)
        event = self.state_machine.transition(
            inv,
            target_state=InvestigationStatus.FAILED,
            reason=reason,
            metadata=metadata or {},
        )
        inv.failure_reason = reason
        self.repository.update(inv)
        return inv, event

    def run_investigation(
        self,
        invoice_id: str,
        context_or_lineage: InvestigationContext | dict[str, Any],
        exception_id: str | None = None,
        investigation_id: str | None = None,
    ) -> Investigation:
        """Execute a complete, non-agent deterministic investigation lifecycle.

        SKELETON:
            create investigation (QUEUED)
                ↓
            start investigation (INVESTIGATING)
                ↓
            move to validation (VALIDATING)
                ↓
            apply validation outcome (VERIFIED | NOT_VERIFIED | INSUFFICIENT_EVIDENCE | NEEDS_REVIEW)

        If a technical failure occurs during processing, the investigation is transitioned to FAILED.
        """
        inv = self.create_investigation(
            invoice_id=invoice_id,
            exception_id=exception_id,
            investigation_id=investigation_id,
        )

        # 1. Start investigation (QUEUED -> INVESTIGATING)
        self.start_investigation(inv.id, reason="Investigation initiated")

        # 2. Move to validation (INVESTIGATING -> VALIDATING)
        self.move_to_validation(
            inv.id, reason="Lineage context ready for deterministic validation"
        )

        # 3. Evaluate deterministic rules & apply outcome
        try:
            outcome = self.validation_engine.validate(context_or_lineage)
            self.apply_validation_outcome(inv.id, outcome)
        except Exception as exc:
            logger.exception("Technical failure during validation: %s", exc)
            self.fail_investigation(
                inv.id, reason=f"Technical validation failure: {exc}"
            )

        return self.get_investigation(inv.id)
