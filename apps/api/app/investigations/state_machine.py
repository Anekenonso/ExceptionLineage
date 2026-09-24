"""Controlled investigation lifecycle state machine for ExceptionLineage.

Architectural Principle:
    AI handles ambiguity. Code handles authority.

The InvestigationStateMachine acts as the authoritative lifecycle boundary.
External agents, heuristics, or LLM components may propose findings, request evidence,
or interpret narrative ambiguity, but CANNOT directly mutate authoritative investigation
lifecycle states. State transitions are strictly validated and recorded as immutable events.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.investigations.exceptions import InvalidStateTransitionError
from app.investigations.repository import InvestigationRepository
from app.models.common import utc_now
from app.models.enums import InvestigationEventType, InvestigationStatus
from app.models.investigation import Investigation, InvestigationEvent

logger = logging.getLogger(__name__)

# Explicit transition map defining authoritative progression
VALID_TRANSITIONS: dict[InvestigationStatus, set[InvestigationStatus]] = {
    InvestigationStatus.QUEUED: {
        InvestigationStatus.INVESTIGATING,
    },
    InvestigationStatus.INVESTIGATING: {
        InvestigationStatus.VALIDATING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.VALIDATING: {
        InvestigationStatus.VERIFIED,
        InvestigationStatus.NOT_VERIFIED,
        InvestigationStatus.INSUFFICIENT_EVIDENCE,
        InvestigationStatus.NEEDS_REVIEW,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.VERIFIED: set(),
    InvestigationStatus.NOT_VERIFIED: set(),
    InvestigationStatus.INSUFFICIENT_EVIDENCE: set(),
    InvestigationStatus.NEEDS_REVIEW: set(),
    InvestigationStatus.FAILED: set(),
}

# Immutable set of terminal outcome states
TERMINAL_STATES: frozenset[InvestigationStatus] = frozenset({
    InvestigationStatus.VERIFIED,
    InvestigationStatus.NOT_VERIFIED,
    InvestigationStatus.INSUFFICIENT_EVIDENCE,
    InvestigationStatus.NEEDS_REVIEW,
    InvestigationStatus.FAILED,
})


class InvestigationStateMachine:
    """Deterministic domain state machine managing investigation lifecycle transitions."""

    def __init__(self, repository: InvestigationRepository | None = None) -> None:
        self.repository = repository

    @staticmethod
    def is_valid_transition(
        from_state: InvestigationStatus,
        to_state: InvestigationStatus,
    ) -> bool:
        """Check whether a transition between two states is legal according to the transition map."""
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @staticmethod
    def is_terminal(state: InvestigationStatus) -> bool:
        """Check whether a state is a terminal outcome that forbids further transitions."""
        return state in TERMINAL_STATES

    @staticmethod
    def get_valid_transitions(current_state: InvestigationStatus) -> set[InvestigationStatus]:
        """Return the set of valid next states from the specified current state."""
        return set(VALID_TRANSITIONS.get(current_state, set()))

    def validate_transition(
        self,
        investigation_id: str,
        current_state: InvestigationStatus,
        requested_state: InvestigationStatus,
    ) -> None:
        """Validate a proposed transition.

        Raises:
            InvalidStateTransitionError: If the proposed transition violates lifecycle rules.
        """
        if not self.is_valid_transition(current_state, requested_state):
            if self.is_terminal(current_state):
                details = f"State '{current_state.value}' is terminal and cannot transition to any state."
            else:
                allowed_names = sorted([s.value for s in self.get_valid_transitions(current_state)])
                details = f"Allowed transitions from '{current_state.value}': {allowed_names or 'None'}."

            raise InvalidStateTransitionError(
                investigation_id=investigation_id,
                current_state=current_state,
                requested_state=requested_state,
                details=details,
            )

    def transition(
        self,
        investigation: Investigation,
        target_state: InvestigationStatus,
        reason: str | None = None,
        event_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> InvestigationEvent:
        """Execute a validated transition on an investigation.

        Responsibilities:
        1. Determine whether transition is valid; reject invalid transitions explicitly.
        2. Apply valid transition to update investigation state and updated_at timestamp.
        3. Record an immutable InvestigationEvent capturing the transition and reason.
        4. Persist to repository if configured.

        Returns:
            The newly created immutable InvestigationEvent.
        """
        from_state = investigation.status
        self.validate_transition(investigation.id, from_state, target_state)

        now = utc_now()
        event_reason = reason or f"Transitioned from {from_state.value} to {target_state.value}"

        event = InvestigationEvent(
            id=event_id or f"evt-{uuid.uuid4().hex[:12]}",
            investigation_id=investigation.id,
            from_state=from_state,
            to_state=target_state,
            reason=event_reason,
            event_type=InvestigationEventType.STATE_TRANSITION,
            timestamp=now,
            metadata=metadata or {},
        )

        # Mutate investigation model state
        investigation.status = target_state
        investigation.updated_at = now
        if target_state == InvestigationStatus.FAILED and reason:
            investigation.failure_reason = reason

        # Persist through repository if wired
        if self.repository is not None:
            self.repository.update(investigation)
            self.repository.append_event(event)

        logger.info(
            "Investigation '%s' transitioned: %s -> %s (reason: %s)",
            investigation.id,
            from_state.value,
            target_state.value,
            event_reason,
        )
        return event
