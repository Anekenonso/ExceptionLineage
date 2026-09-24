"""Domain exceptions for ExceptionLineage investigation lifecycle and state machine."""

from __future__ import annotations

from app.models.enums import InvestigationStatus


class InvestigationError(Exception):
    """Base domain exception for investigation errors."""


class InvalidStateTransitionError(InvestigationError):
    """Raised when an illegal investigation lifecycle state transition is attempted."""

    def __init__(
        self,
        investigation_id: str,
        current_state: InvestigationStatus,
        requested_state: InvestigationStatus,
        details: str | None = None,
    ) -> None:
        self.investigation_id = investigation_id
        self.current_state = current_state
        self.requested_state = requested_state
        self.details = details

        msg = (
            f"Invalid state transition for investigation '{investigation_id}': "
            f"cannot transition from '{current_state.value}' to '{requested_state.value}'."
        )
        if details:
            msg += f" {details}"
        super().__init__(msg)


class InvestigationNotFoundError(InvestigationError):
    """Raised when an investigation record cannot be found in repository storage."""

    def __init__(self, investigation_id: str) -> None:
        self.investigation_id = investigation_id
        super().__init__(f"Investigation '{investigation_id}' not found.")


class GraphRetrievalError(InvestigationError):
    """Raised when graph lineage retrieval fails due to infrastructure or missing graph node."""

