"""FastAPI router for investigation endpoints in ExceptionLineage."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.investigations.schemas import (
    InvestigationCreateRequest,
    InvestigationResponse,
)
from app.investigations.service import InvestigationService
from app.investigations.trace import InvestigationEvidenceTrace
from app.models.investigation import InvestigationEvent

router = APIRouter()

# Module-level shared service for application lifetime in-memory persistence
_default_service: InvestigationService | None = None


def get_investigation_service() -> InvestigationService:
    """Dependency provider for InvestigationService with offline fallback."""
    global _default_service
    if _default_service is None:
        from app.graph.client import Neo4jClient
        from app.graph.lineage import InMemoryLineageRepository, Neo4jLineageRepository
        from app.graph.loader import load_seed_lineages

        client = Neo4jClient()
        if client.verify_connectivity():
            lineage_repo = Neo4jLineageRepository(client=client)
        else:
            lineage_repo = InMemoryLineageRepository(load_seed_lineages())

        _default_service = InvestigationService(lineage_repository=lineage_repo)
    return _default_service


def reset_default_service(service: InvestigationService | None = None) -> None:
    """Helper to reset or inject service instance for testing."""
    global _default_service
    _default_service = service


def _safe_get_lineage(service: InvestigationService, invoice_id: str) -> dict | None:
    """Safely fetch lineage without propagating graph connection or retrieval failures."""
    try:
        return service.lineage_repository.get_invoice_lineage(invoice_id)
    except Exception:
        return None


@router.get(
    "",
    response_model=list[InvestigationResponse],
    summary="List all investigations",
    description="Retrieves all investigations currently stored in repository storage.",
)
def list_investigations(
    service: InvestigationService = Depends(get_investigation_service),
) -> list[InvestigationResponse]:
    """Retrieve all investigations ordered chronologically (newest first)."""
    investigations = service.repository.list_all()
    sorted_invs = sorted(investigations, key=lambda x: x.created_at, reverse=True)
    results: list[InvestigationResponse] = []
    for inv in sorted_invs:
        events = service.get_events(inv.id, include_agent_events=False)
        agent_events = service.get_agent_events(inv.id)
        lineage = _safe_get_lineage(service, inv.invoice_id)
        results.append(
            InvestigationResponse.from_investigation(
                inv, events=events, agent_events=agent_events, lineage=lineage
            )
        )
    return results


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Create and run investigation",
    description="Initiates an end-to-end investigation pipeline: retrieves graph lineage, evaluates deterministic rules, and applies state machine transitions.",
)
def create_investigation(
    payload: InvestigationCreateRequest,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    """Create and execute an investigation for a target invoice."""
    inv = service.run_investigation(
        invoice_id=payload.invoice_id,
        exception_id=payload.exception_id,
    )
    events = service.get_events(inv.id, include_agent_events=False)
    agent_events = service.get_agent_events(inv.id)
    lineage = _safe_get_lineage(service, inv.invoice_id)
    return InvestigationResponse.from_investigation(
        inv, events=events, agent_events=agent_events, lineage=lineage
    )


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    summary="Get investigation state",
    description="Retrieves the current lifecycle state and findings for an investigation.",
)
def get_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationResponse:
    """Retrieve an investigation by its identifier."""
    inv = service.get_investigation(investigation_id)
    events = service.get_events(investigation_id, include_agent_events=False)
    agent_events = service.get_agent_events(investigation_id)
    lineage = _safe_get_lineage(service, inv.invoice_id)
    return InvestigationResponse.from_investigation(
        inv, events=events, agent_events=agent_events, lineage=lineage
    )


@router.get(
    "/{investigation_id}/lineage",
    response_model=dict,
    summary="Get investigation lineage graph",
    description="Retrieves the graph lineage (customer, contract, amendments, sows, exception, approval, evidence) for the investigated invoice.",
)
def get_investigation_lineage(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> dict:
    """Retrieve the graph lineage for an investigation."""
    inv = service.get_investigation(investigation_id)
    lineage = _safe_get_lineage(service, inv.invoice_id)
    return lineage or {}


@router.get(
    "/{investigation_id}/events",
    response_model=list[InvestigationEvent],
    summary="Get investigation event timeline",
    description="Retrieves the chronological audit event timeline for an investigation.",
)
def get_investigation_events(
    investigation_id: str,
    include_agent_events: bool = False,
    service: InvestigationService = Depends(get_investigation_service),
) -> list[InvestigationEvent]:
    """Retrieve the chronological event log for an investigation."""
    return service.get_events(investigation_id, include_agent_events=include_agent_events)


@router.get(
    "/{investigation_id}/trace",
    response_model=InvestigationEvidenceTrace,
    summary="Get auditable machine-readable evidence trace",
    description="Retrieves the complete end-to-end evidence trace connecting input, agent decisions, tool calls, graph retrieval, validation checks, and final outcome.",
)
def get_investigation_evidence_trace(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> InvestigationEvidenceTrace:
    """Retrieve the machine-readable evidence chain trace for an investigation."""
    return service.get_evidence_trace(investigation_id)

