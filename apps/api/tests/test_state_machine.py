"""Unit and integration tests for the Investigation State Machine and InvestigationService."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any
import pytest
from pydantic import ValidationError

from app.investigations import (
    InMemoryInvestigationRepository,
    InvalidStateTransitionError,
    InvestigationNotFoundError,
    InvestigationRepository,
    InvestigationService,
    InvestigationStateMachine,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
)
from app.models.enums import InvestigationEventType, InvestigationStatus
from app.models.investigation import Investigation, InvestigationEvent
from app.validation.engine import ValidationEngine
from app.validation.models import ValidationOutcome


# ==============================================================================
# 1. Initial State Tests
# ==============================================================================


def test_create_investigation_initial_state_is_queued():
    service = InvestigationService()
    inv = service.create_investigation(invoice_id="INV-1001", exception_id="EXC-001")

    assert inv.status == InvestigationStatus.QUEUED
    assert inv.current_state == InvestigationStatus.QUEUED
    assert inv.invoice_id == "INV-1001"
    assert inv.exception_id == "EXC-001"
    assert inv.investigation_id == inv.id
    assert inv.created_at is not None
    assert inv.updated_at is None
    # No events prior to first transition
    events = service.get_events(inv.id)
    assert events == []


def test_investigation_model_alias_support():
    inv = Investigation(
        investigation_id="INVG-TEST-1",
        invoice_id="INV-999",
        current_state=InvestigationStatus.QUEUED,
    )
    assert inv.id == "INVG-TEST-1"
    assert inv.investigation_id == "INVG-TEST-1"
    assert inv.status == InvestigationStatus.QUEUED
    assert inv.current_state == InvestigationStatus.QUEUED


# ==============================================================================
# 2. Valid Transitions Tests
# ==============================================================================


@pytest.mark.parametrize(
    "from_state, to_state",
    [
        (InvestigationStatus.QUEUED, InvestigationStatus.INVESTIGATING),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.VALIDATING),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.FAILED),
        (InvestigationStatus.VALIDATING, InvestigationStatus.VERIFIED),
        (InvestigationStatus.VALIDATING, InvestigationStatus.NOT_VERIFIED),
        (InvestigationStatus.VALIDATING, InvestigationStatus.INSUFFICIENT_EVIDENCE),
        (InvestigationStatus.VALIDATING, InvestigationStatus.NEEDS_REVIEW),
        (InvestigationStatus.VALIDATING, InvestigationStatus.FAILED),
    ],
)
def test_valid_transitions_allowed_by_state_machine(from_state, to_state):
    sm = InvestigationStateMachine()
    assert sm.is_valid_transition(from_state, to_state) is True

    inv = Investigation(id="INVG-1", invoice_id="INV-1", status=from_state)
    event = sm.transition(inv, target_state=to_state, reason=f"Valid {from_state}->{to_state}")

    assert inv.status == to_state
    assert inv.updated_at is not None
    assert event.from_state == from_state
    assert event.to_state == to_state
    assert event.investigation_id == "INVG-1"


def test_every_valid_transition_in_map():
    """Verify that all expected transitions are present in the VALID_TRANSITIONS map."""
    expected_map = {
        InvestigationStatus.QUEUED: {InvestigationStatus.INVESTIGATING},
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
    assert VALID_TRANSITIONS == expected_map


# ==============================================================================
# 3. Invalid Transitions Tests
# ==============================================================================


@pytest.mark.parametrize(
    "current_state, requested_state",
    [
        (InvestigationStatus.QUEUED, InvestigationStatus.VALIDATING),
        (InvestigationStatus.QUEUED, InvestigationStatus.VERIFIED),
        (InvestigationStatus.QUEUED, InvestigationStatus.NOT_VERIFIED),
        (InvestigationStatus.QUEUED, InvestigationStatus.INSUFFICIENT_EVIDENCE),
        (InvestigationStatus.QUEUED, InvestigationStatus.NEEDS_REVIEW),
        (InvestigationStatus.QUEUED, InvestigationStatus.FAILED),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.VERIFIED),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.NOT_VERIFIED),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.INSUFFICIENT_EVIDENCE),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.NEEDS_REVIEW),
        (InvestigationStatus.INVESTIGATING, InvestigationStatus.QUEUED),
        (InvestigationStatus.VALIDATING, InvestigationStatus.INVESTIGATING),
        (InvestigationStatus.VALIDATING, InvestigationStatus.QUEUED),
    ],
)
def test_invalid_active_transitions_rejected(current_state, requested_state):
    sm = InvestigationStateMachine()
    assert sm.is_valid_transition(current_state, requested_state) is False

    inv = Investigation(id="INVG-ERR", invoice_id="INV-1", status=current_state)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        sm.transition(inv, target_state=requested_state)

    err = exc_info.value
    assert err.investigation_id == "INVG-ERR"
    assert err.current_state == current_state
    assert err.requested_state == requested_state
    assert "INVG-ERR" in str(err)
    assert current_state.value in str(err)
    assert requested_state.value in str(err)


# ==============================================================================
# 4. Terminal State Tests
# ==============================================================================


@pytest.mark.parametrize(
    "terminal_state",
    [
        InvestigationStatus.VERIFIED,
        InvestigationStatus.NOT_VERIFIED,
        InvestigationStatus.INSUFFICIENT_EVIDENCE,
        InvestigationStatus.NEEDS_REVIEW,
        InvestigationStatus.FAILED,
    ],
)
def test_terminal_states_reject_all_outgoing_transitions(terminal_state):
    sm = InvestigationStateMachine()
    assert sm.is_terminal(terminal_state) is True
    assert sm.get_valid_transitions(terminal_state) == set()

    for any_state in InvestigationStatus:
        assert sm.is_valid_transition(terminal_state, any_state) is False
        inv = Investigation(id="INVG-TERM", invoice_id="INV-1", status=terminal_state)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(inv, target_state=any_state)

        assert "terminal" in str(exc_info.value).lower()
        assert exc_info.value.current_state == terminal_state


# ==============================================================================
# 5. Event History & Immutability Tests
# ==============================================================================


def test_event_history_recording_order_and_immutability():
    service = InvestigationService()
    inv = service.create_investigation(invoice_id="INV-1001", investigation_id="INVG-AUDIT-1")

    # 1. QUEUED -> INVESTIGATING
    _, ev1 = service.start_investigation(inv.id, reason="Started review of rates")
    assert ev1.from_state == InvestigationStatus.QUEUED
    assert ev1.to_state == InvestigationStatus.INVESTIGATING
    assert ev1.reason == "Started review of rates"
    assert ev1.timestamp is not None
    assert ev1.event_id == ev1.id

    # 2. INVESTIGATING -> VALIDATING
    _, ev2 = service.move_to_validation(inv.id, reason="Lineage collected; validating")
    assert ev2.from_state == InvestigationStatus.INVESTIGATING
    assert ev2.to_state == InvestigationStatus.VALIDATING
    assert ev2.reason == "Lineage collected; validating"
    assert ev2.timestamp >= ev1.timestamp

    # 3. VALIDATING -> VERIFIED
    dummy_outcome = ValidationOutcome(
        status=InvestigationStatus.VERIFIED,
        summary="All contractual rules verified",
        results=[],
        cited_evidence_ids=["EVI-001"],
    )
    _, ev3 = service.apply_validation_outcome(inv.id, dummy_outcome)
    assert ev3.from_state == InvestigationStatus.VALIDATING
    assert ev3.to_state == InvestigationStatus.VERIFIED
    assert ev3.reason == "All contractual rules verified"
    assert ev3.timestamp >= ev2.timestamp

    # Check total history
    events = service.get_events(inv.id)
    assert len(events) == 3
    assert [e.id for e in events] == [ev1.id, ev2.id, ev3.id]
    assert [e.from_state for e in events] == [
        InvestigationStatus.QUEUED,
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.VALIDATING,
    ]
    assert [e.to_state for e in events] == [
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.VALIDATING,
        InvestigationStatus.VERIFIED,
    ]


def test_event_immutability():
    ev = InvestigationEvent(
        id="EVT-001",
        investigation_id="INVG-001",
        from_state=InvestigationStatus.QUEUED,
        to_state=InvestigationStatus.INVESTIGATING,
        reason="Test event",
    )
    # Attempting to reassign an attribute on frozen model must raise error
    with pytest.raises(ValidationError):
        ev.reason = "Mutated reason"  # type: ignore

    with pytest.raises(ValidationError):
        ev.to_state = InvestigationStatus.FAILED  # type: ignore


def test_repository_events_list_is_isolated_copy():
    repo = InMemoryInvestigationRepository()
    inv = Investigation(id="INVG-1", invoice_id="INV-1")
    repo.create(inv)

    ev1 = InvestigationEvent(
        id="EVT-1",
        investigation_id="INVG-1",
        from_state=InvestigationStatus.QUEUED,
        to_state=InvestigationStatus.INVESTIGATING,
        reason="R1",
    )
    repo.append_event(ev1)

    events = repo.get_events("INVG-1")
    assert len(events) == 1

    # Mutating returned list should not affect repository internal list
    events.clear()
    assert len(repo.get_events("INVG-1")) == 1


# ==============================================================================
# 6. Validation Outcome Mapping Tests
# ==============================================================================


@pytest.mark.parametrize(
    "validation_status",
    [
        InvestigationStatus.VERIFIED,
        InvestigationStatus.NOT_VERIFIED,
        InvestigationStatus.INSUFFICIENT_EVIDENCE,
        InvestigationStatus.NEEDS_REVIEW,
    ],
)
def test_validation_outcomes_map_directly_to_terminal_states(validation_status):
    service = InvestigationService()
    inv = service.create_investigation(invoice_id="INV-001")
    service.start_investigation(inv.id)
    service.move_to_validation(inv.id)

    outcome = ValidationOutcome(
        status=validation_status,
        summary=f"Validation outcome for {validation_status.value}",
        failure_reason="Reason detail" if validation_status != InvestigationStatus.VERIFIED else None,
        results=[],
        cited_evidence_ids=["EVI-1"],
    )

    updated_inv, event = service.apply_validation_outcome(inv.id, outcome)

    assert updated_inv.status == validation_status
    assert updated_inv.summary == outcome.summary
    assert updated_inv.failure_reason == outcome.failure_reason
    assert event.from_state == InvestigationStatus.VALIDATING
    assert event.to_state == validation_status


def test_technical_failure_maps_to_failed_state():
    service = InvestigationService()
    inv = service.create_investigation(invoice_id="INV-001")
    service.start_investigation(inv.id)

    # Technical failure during investigation (e.g. database disconnect)
    failed_inv, event = service.fail_investigation(
        inv.id, reason="Neo4j connection dropped: ServiceUnavailable"
    )

    assert failed_inv.status == InvestigationStatus.FAILED
    assert failed_inv.failure_reason == "Neo4j connection dropped: ServiceUnavailable"
    assert event.from_state == InvestigationStatus.INVESTIGATING
    assert event.to_state == InvestigationStatus.FAILED


def test_technical_failure_during_validation():
    service = InvestigationService()
    inv = service.create_investigation(invoice_id="INV-001")
    service.start_investigation(inv.id)
    service.move_to_validation(inv.id)

    failed_inv, event = service.fail_investigation(
        inv.id, reason="Out of memory during rule execution"
    )

    assert failed_inv.status == InvestigationStatus.FAILED
    assert event.from_state == InvestigationStatus.VALIDATING
    assert event.to_state == InvestigationStatus.FAILED


# ==============================================================================
# 7. End-to-End Investigation Service Workflow Tests
# ==============================================================================


def test_run_investigation_full_lifecycle_success():
    from tests.test_graph_ground_truth import build_mock_seed_graph_lineage

    service = InvestigationService()
    lineages = build_mock_seed_graph_lineage()
    mock_context = lineages["INV-1001"]

    inv = service.run_investigation(
        invoice_id="INV-1001",
        context_or_lineage=mock_context,
        investigation_id="INVG-RUN-001",
    )

    assert inv.status == InvestigationStatus.VERIFIED
    assert inv.summary is not None
    assert "authorized and verified" in inv.summary.lower()

    events = service.get_events("INVG-RUN-001")
    assert len(events) == 3
    assert events[0].from_state == InvestigationStatus.QUEUED
    assert events[0].to_state == InvestigationStatus.INVESTIGATING
    assert events[1].from_state == InvestigationStatus.INVESTIGATING
    assert events[1].to_state == InvestigationStatus.VALIDATING
    assert events[2].from_state == InvestigationStatus.VALIDATING
    assert events[2].to_state == InvestigationStatus.VERIFIED


def test_investigation_service_all_8_benchmark_cases():
    """Verify that InvestigationService runs all 8 benchmark cases through the full lifecycle to expected outcomes."""
    import json
    from app.graph.loader import find_data_dir
    from tests.test_graph_ground_truth import build_mock_seed_graph_lineage

    data_dir = find_data_dir()
    with open(data_dir / "ground_truth" / "ground_truth.json", "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    lineages = build_mock_seed_graph_lineage()
    service = InvestigationService()

    for gt in ground_truth:
        case_id = gt["case_id"]
        invoice_id = gt["invoice_id"]
        expected_status = gt["expected_status"]

        lineage = lineages[invoice_id]
        inv = service.run_investigation(
            invoice_id=invoice_id,
            context_or_lineage=lineage,
            investigation_id=f"INVG-{case_id}",
        )

        assert inv.status.value == expected_status, (
            f"Case {case_id} ({invoice_id}) lifecycle outcome mismatch: "
            f"expected {expected_status}, got {inv.status.value}"
        )

        # Verify event history for each case
        events = service.get_events(f"INVG-{case_id}")
        assert len(events) == 3
        assert events[0].from_state == InvestigationStatus.QUEUED
        assert events[0].to_state == InvestigationStatus.INVESTIGATING
        assert events[1].from_state == InvestigationStatus.INVESTIGATING
        assert events[1].to_state == InvestigationStatus.VALIDATING
        assert events[2].from_state == InvestigationStatus.VALIDATING
        assert events[2].to_state.value == expected_status


def test_run_investigation_technical_failure_handling():
    service = InvestigationService()

    # Pass an invalid object that causes validate() to raise TypeError
    inv = service.run_investigation(
        invoice_id="INV-BAD",
        context_or_lineage=12345,  # type: ignore
        investigation_id="INVG-FAIL-001",
    )

    assert inv.status == InvestigationStatus.FAILED
    assert "technical validation failure" in inv.failure_reason.lower()

    events = service.get_events("INVG-FAIL-001")
    assert len(events) == 3
    assert events[0].to_state == InvestigationStatus.INVESTIGATING
    assert events[1].to_state == InvestigationStatus.VALIDATING
    assert events[2].to_state == InvestigationStatus.FAILED


def test_get_nonexistent_investigation_raises():
    service = InvestigationService()
    with pytest.raises(InvestigationNotFoundError):
        service.get_investigation("NON-EXISTENT")


# ==============================================================================
# 8. No Ground-Truth Leakage in State Machine Code
# ==============================================================================


def test_state_machine_does_not_import_ground_truth():
    """Verify that app.investigations does not import ground-truth datasets, fixtures, or benchmarks."""
    investigations_dir = Path(__file__).parent.parent / "app" / "investigations"
    py_files = list(investigations_dir.glob("*.py"))
    assert len(py_files) > 0, "No python files found in app/investigations"

    forbidden_patterns = [
        r"data\.ground_truth",
        r"ground_truth",
        r"test_.*",
        r"data/cases",
        r"data/seed",
    ]

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(py_file))

        # Check imports via AST
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for pattern in forbidden_patterns:
                        assert not re.search(pattern, alias.name), (
                            f"Illegal import '{alias.name}' matching '{pattern}' in {py_file.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for pattern in forbidden_patterns:
                    assert not re.search(pattern, module), (
                        f"Illegal from-import '{module}' matching '{pattern}' in {py_file.name}"
                    )
