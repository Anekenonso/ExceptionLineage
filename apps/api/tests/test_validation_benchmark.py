"""Benchmark test verifying that the ValidationEngine deterministically determines outcomes

for all 8 benchmark cases from Stage 12 simulated data, matching ground truth determinations
without importing or referencing ground-truth files at runtime.
"""

import json
from pathlib import Path

from app.graph.loader import find_data_dir
from app.models.enums import InvestigationStatus
from app.validation.engine import ValidationEngine
from tests.test_graph_ground_truth import build_mock_seed_graph_lineage


def test_validation_engine_does_not_import_ground_truth() -> None:
    """Ensure the validation engine does not import or read ground truth at runtime."""
    val_dir = Path(__file__).resolve().parent.parent / "app" / "validation"
    for py_file in val_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "ground_truth.json" not in content, f"Found ground_truth reference in {py_file.name}"
        assert "CASE-" not in content, f"Found hardcoded case ID in {py_file.name}"


def test_validation_engine_all_8_benchmark_cases() -> None:
    """Execute the deterministic validation engine across all 8 benchmark cases."""
    data_dir = find_data_dir()
    with open(data_dir / "ground_truth" / "ground_truth.json", "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    lineages = build_mock_seed_graph_lineage()
    engine = ValidationEngine()

    for gt in ground_truth:
        case_id = gt["case_id"]
        invoice_id = gt["invoice_id"]
        expected_status = gt["expected_status"]

        lineage = lineages[invoice_id]
        outcome = engine.validate(lineage)

        # Assert status matches expected ground truth status
        assert outcome.status.value == expected_status, (
            f"Case {case_id} ({invoice_id}) outcome mismatch: "
            f"expected {expected_status}, got {outcome.status.value}. "
            f"Summary: {outcome.summary}. Failure reason: {outcome.failure_reason}. "
            f"Results: {[(r.check_name, r.status.value, r.message) for r in outcome.results]}"
        )

        # Case-specific validation checks
        if case_id == "CASE-001":
            assert outcome.status == InvestigationStatus.VERIFIED
            assert outcome.is_verified
            assert len(outcome.failed_checks) == 0
            assert len(outcome.unknown_checks) == 0
            assert "EV-001" in outcome.cited_evidence_ids
            assert "EV-002" in outcome.cited_evidence_ids
            assert "EV-003" in outcome.cited_evidence_ids

        elif case_id == "CASE-002":
            assert outcome.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
            assert any(r.check_name == "approval_authorization" and r.status.value == "UNKNOWN" for r in outcome.results)

        elif case_id == "CASE-003":
            assert outcome.status == InvestigationStatus.NOT_VERIFIED
            assert any(r.check_name == "amendment_effectiveness" and r.status.value == "FAIL" for r in outcome.results)

        elif case_id == "CASE-004":
            assert outcome.status == InvestigationStatus.NOT_VERIFIED
            assert any(r.check_name == "amendment_scope_match" and r.status.value == "FAIL" for r in outcome.results)

        elif case_id == "CASE-005":
            assert outcome.status == InvestigationStatus.NEEDS_REVIEW
            assert any(r.check_name == "conflicting_authority" and r.status.value == "FAIL" for r in outcome.results)

        elif case_id == "CASE-006":
            assert outcome.status == InvestigationStatus.NOT_VERIFIED
            assert any(r.check_name == "applicable_amendment" and r.status.value == "FAIL" for r in outcome.results)

        elif case_id == "CASE-007":
            assert outcome.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
            assert any(r.check_name == "customer_governing_contract" and r.status.value == "UNKNOWN" for r in outcome.results)

        elif case_id == "CASE-008":
            assert outcome.status == InvestigationStatus.VERIFIED
            assert outcome.is_verified
            assert len(outcome.failed_checks) == 0
            assert "EV-010" in outcome.cited_evidence_ids
            assert "EV-012" in outcome.cited_evidence_ids
            assert "EV-013" in outcome.cited_evidence_ids
