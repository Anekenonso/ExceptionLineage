import json
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.investigations.schemas import (
    InvestigationCreateRequest,
    InvestigationResponse,
    TestCasePayload,
)
from app.investigations.service import InvestigationService
from app.investigations.trace import InvestigationEvidenceTrace
from app.models.investigation import InvestigationEvent

router = APIRouter()

# Module-level shared service for application lifetime in-memory persistence
_default_service: InvestigationService | None = None


CANONICAL_DEMO_CASES = [
    ("INV-1001", "EX-001"),
    ("INV-1002", "EX-002"),
    ("INV-1003", "EX-003"),
    ("INV-1004", "EX-004"),
    ("INV-1005", "EX-005"),
    ("INV-1006", "EX-006"),
    ("INV-1007", "EX-007"),
    ("INV-1008", "EX-008"),
]


def seed_canonical_demo_data(service: InvestigationService) -> None:
    """Deterministically seed the 8 canonical benchmark cases for clean demo readiness."""
    for inv_id, exc_id in CANONICAL_DEMO_CASES:
        try:
            service.run_investigation(invoice_id=inv_id, exception_id=exc_id)
        except Exception:
            pass


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
        seed_canonical_demo_data(_default_service)
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
    """Retrieve all investigations ordered chronologically (newest first), deduplicated by invoice."""
    investigations = service.repository.list_all()
    sorted_invs = sorted(investigations, key=lambda x: x.created_at, reverse=True)

    # Deduplicate by invoice_id so multiple development/demo executions do not display duplicate ledger rows
    seen_invoices: set[str] = set()
    deduped_invs = []
    for inv in sorted_invs:
        if inv.invoice_id not in seen_invoices:
            seen_invoices.add(inv.invoice_id)
            deduped_invs.append(inv)

    results: list[InvestigationResponse] = []
    for inv in deduped_invs:
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


MAX_TEST_CASE_SIZE_BYTES = 1024 * 1024  # 1 MB maximum allowed file size


@router.get(
    "/test-case/template",
    response_model=dict,
    summary="Get sample test case template",
    description="Returns a clean, complete JSON template showing the expected structure for Test Your Own Case.",
)
def get_test_case_template() -> dict:
    """Return a working sample test case JSON structure."""
    return {
        "case_meta": {
            "title": "Sample External Cloud Support Rate Variance Case",
            "description": "Demonstrates an independently defined test case with governing contract, amendment, approval, and documentary evidence."
        },
        "invoice": {
            "id": "INV-EXT-001",
            "customer_id": "CUS-EXT-001",
            "contract_id": "CTR-EXT-001",
            "exception_id": "EX-EXT-001",
            "product_id": "PROD-CLOUD-SUP",
            "amount": "10200.00",
            "currency": "USD",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z"
        },
        "customer": {
            "id": "CUS-EXT-001",
            "name": "Global Test Enterprise Corp",
            "external_id": "ERP-CUS-991"
        },
        "contract": {
            "id": "CTR-EXT-001",
            "customer_id": "CUS-EXT-001",
            "title": "Master Cloud Infrastructure Agreement",
            "effective_from": "2026-01-01T00:00:00Z",
            "effective_until": "2026-12-31T23:59:59Z",
            "status": "ACTIVE",
            "currency": "USD"
        },
        "exception": {
            "id": "EX-EXT-001",
            "contract_id": "CTR-EXT-001",
            "invoice_id": "INV-EXT-001",
            "exception_type": "RATE_VARIANCE",
            "description": "Invoice amount $10,200.00 differs from standard contract fee $12,000.00.",
            "expected_amount": "12000.00",
            "actual_amount": "10200.00",
            "currency": "USD"
        },
        "approval": {
            "id": "APR-EXT-001",
            "exception_id": "EX-EXT-001",
            "approver": "sarah.chen@acmeglobal.com",
            "status": "APPROVED",
            "approved_at": "2026-02-01T14:30:00Z",
            "context": {
                "role": "VP Commercial Finance",
                "authorization_ref": "AUTH-EXT-01"
            }
        },
        "amendments": [
            {
                "id": "AMD-EXT-001",
                "contract_id": "CTR-EXT-001",
                "amendment_number": "AMD-2026-01",
                "title": "Cloud Support Volume Discount Amendment",
                "description": "Adjusts monthly rate from $12,000.00 to $10,200.00 for PROD-CLOUD-SUP.",
                "effective_from": "2026-01-15T00:00:00Z",
                "effective_until": "2026-09-30T23:59:59Z"
            }
        ],
        "sows": [],
        "evidence": [
            {
                "id": "EV-EXT-001",
                "evidence_type": "CONTRACT_CLAUSE",
                "source": "contracts_repository",
                "source_id": "CTR-EXT-001",
                "title": "Base Support Rate Clause",
                "locator": "Schedule B, Section 1.1",
                "excerpt": "Standard enterprise cloud support services shall be invoiced at the baseline rate of $12,000.00 USD monthly.",
                "captured_at": "2026-01-02T10:00:00Z",
                "effective_from": "2026-01-01T00:00:00Z",
                "effective_until": "2026-12-31T23:59:59Z",
                "scope": "enterprise_cloud_support",
                "confidence": 1.0
            },
            {
                "id": "EV-EXT-002",
                "evidence_type": "AMENDMENT_TERMS",
                "source": "contracts_repository",
                "source_id": "AMD-EXT-001",
                "title": "Tier-1 Volume Rate Reduction",
                "locator": "Section 2.1",
                "excerpt": "The monthly fee for PROD-CLOUD-SUP is amended to $10,200.00 USD effective January 15, 2026 through September 30, 2026.",
                "captured_at": "2026-01-16T09:00:00Z",
                "effective_from": "2026-01-15T00:00:00Z",
                "effective_until": "2026-09-30T23:59:59Z",
                "scope": "PROD-CLOUD-SUP",
                "confidence": 0.98
            },
            {
                "id": "EV-EXT-003",
                "evidence_type": "APPROVAL_RECORD",
                "source": "approval_system",
                "source_id": "APR-EXT-001",
                "title": "VP Commercial Finance Signoff",
                "locator": "Workflow Audit #88412",
                "excerpt": "Executive authorization granted by Sarah Chen (VP Commercial Finance) for Tier-1 Support rate variance $10,200.00.",
                "captured_at": "2026-02-01T15:00:00Z",
                "effective_from": "2026-02-01T14:30:00Z",
                "effective_until": None,
                "scope": "commercial_pricing_waiver",
                "confidence": 0.99
            }
        ]
    }


@router.post(
    "/test-case",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Test Your Own Case (Secure Temporary In-Memory Testing)",
    description=(
        "Upload ONE structured JSON case to execute through the existing ExceptionLineage "
        "investigation pipeline. The case is processed in temporary isolated memory and is "
        "never persisted to database, filesystem, or application caches."
    ),
)
async def test_your_own_case(
    file: UploadFile = File(..., description="Structured .json test case file"),
) -> InvestigationResponse:
    """Execute an independently supplied JSON case in an isolated, temporary in-memory environment."""
    # 1. Format verification: JSON only
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .json files are accepted for external case testing.",
        )

    # 2. Read in-memory buffer with size bounding
    contents = await file.read()
    if len(contents) > MAX_TEST_CASE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 1MB ({MAX_TEST_CASE_SIZE_BYTES} bytes).",
        )
    if not contents.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSON file is empty.",
        )

    # 3. JSON parsing
    try:
        raw_data = json.loads(contents.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON syntax: {exc}",
        )

    if not isinstance(raw_data, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JSON root must be an object representing an enterprise transaction case.",
        )

    # 4. Schema validation
    try:
        payload = TestCasePayload.model_validate(raw_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Test case schema validation failed: {exc}",
        )

    # 5. In-memory normalization to lineage representation
    lineage_dict = payload.to_lineage_dict()

    # 6. Create temporary, completely isolated repository & engine context
    from app.agent.factory import create_investigation_agent
    from app.graph.lineage import InMemoryLineageRepository
    from app.investigations.repository import InMemoryInvestigationRepository
    from app.investigations.state_machine import InvestigationStateMachine
    from app.validation.engine import ValidationEngine

    isolated_lineage_repo = InMemoryLineageRepository()
    isolated_lineage_repo.add_lineage(invoice_id=payload.invoice.id, lineage=lineage_dict)

    isolated_inv_repo = InMemoryInvestigationRepository()
    isolated_state_machine = InvestigationStateMachine(repository=isolated_inv_repo)

    agent = create_investigation_agent(lineage_repo=isolated_lineage_repo)

    isolated_service = InvestigationService(
        repository=isolated_inv_repo,
        state_machine=isolated_state_machine,
        validation_engine=ValidationEngine(),
        lineage_repository=isolated_lineage_repo,
        agent=agent,
    )

    # 7. Execute through existing investigation pipeline
    inv = isolated_service.run_investigation(
        invoice_id=payload.invoice.id,
        exception_id=payload.invoice.exception_id or (payload.exception.id if payload.exception else None),
    )

    # 8. Retrieve events and trace from isolated service
    events = isolated_service.get_events(inv.id, include_agent_events=False)
    agent_events = isolated_service.get_agent_events(inv.id)
    lineage_data = isolated_lineage_repo.get_invoice_lineage(inv.invoice_id)
    trace = isolated_service.get_evidence_trace(inv.id)

    # 9. Return structured response marked as temporary
    return InvestigationResponse.from_investigation(
        inv,
        events=events,
        agent_events=agent_events,
        lineage=lineage_data,
        is_temporary=True,
        trace=trace,
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

