"""Repository abstraction and in-memory storage for investigation lifecycles and event audit trails."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.investigations.exceptions import InvestigationNotFoundError
from app.models.investigation import Investigation, InvestigationEvent


@runtime_checkable
class InvestigationRepository(Protocol):
    """Storage contract for investigation lifecycle management and audit event history."""

    def create(self, investigation: Investigation) -> Investigation:
        """Persist a newly initiated investigation record."""
        ...

    def get(self, investigation_id: str) -> Investigation | None:
        """Retrieve an investigation by its identifier, or None if not found."""
        ...

    def update(self, investigation: Investigation) -> Investigation:
        """Update an existing investigation record."""
        ...

    def append_event(self, event: InvestigationEvent) -> InvestigationEvent:
        """Append an immutable event to the investigation audit timeline."""
        ...

    def get_events(self, investigation_id: str) -> list[InvestigationEvent]:
        """Retrieve all audit events for an investigation, ordered chronologically."""
        ...

    def list_all(self) -> list[Investigation]:
        """List all investigations in repository storage."""
        ...


class InMemoryInvestigationRepository:
    """In-memory implementation of InvestigationRepository.

    LIMITATION:
    Data stored in this repository is held purely in volatile application memory.
    It does NOT persist across process restarts, crashes, or multi-instance deployments.
    This implementation is intentionally minimal and suited solely for Stage 15 lifecycle
    validation, test suites, and development. Production durable persistence (e.g., PostgreSQL
    or Neo4j) will be established in later stages when persistence architecture is formally added.
    """

    def __init__(self) -> None:
        self._investigations: dict[str, Investigation] = {}
        self._events: dict[str, list[InvestigationEvent]] = {}

    def create(self, investigation: Investigation) -> Investigation:
        """Store a new investigation record."""
        self._investigations[investigation.id] = investigation
        if investigation.id not in self._events:
            self._events[investigation.id] = []
        return investigation

    def get(self, investigation_id: str) -> Investigation | None:
        """Fetch investigation by ID."""
        return self._investigations.get(investigation_id)

    def update(self, investigation: Investigation) -> Investigation:
        """Update existing investigation record. Raises InvestigationNotFoundError if missing."""
        if investigation.id not in self._investigations:
            raise InvestigationNotFoundError(investigation.id)
        self._investigations[investigation.id] = investigation
        return investigation

    def append_event(self, event: InvestigationEvent) -> InvestigationEvent:
        """Append an immutable event record to the investigation history."""
        if event.investigation_id not in self._events:
            self._events[event.investigation_id] = []
        self._events[event.investigation_id].append(event)
        return event

    def get_events(self, investigation_id: str) -> list[InvestigationEvent]:
        """Return a chronological shallow copy of the event history list for this investigation."""
        return list(self._events.get(investigation_id, []))

    def list_all(self) -> list[Investigation]:
        """List all stored investigations."""
        return list(self._investigations.values())
