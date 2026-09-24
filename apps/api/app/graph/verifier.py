"""Graph ground truth verifier for validating Neo4j graph state against Stage 12 ground truth."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.graph.client import Neo4jClient
from app.graph.loader import find_data_dir
from app.graph.queries import get_invoice_lineage

logger = logging.getLogger(__name__)


@dataclass
class CaseVerificationResult:
    """Verification results for a single ground truth case against the graph."""

    case_id: str
    invoice_id: str
    expected_status: str
    passed: bool
    governing_contract_match: bool
    exception_match: bool
    approval_match: bool
    evidence_reachable: bool
    failure_condition_verified: bool
    details: list[str] = field(default_factory=list)


@dataclass
class GroundTruthVerificationReport:
    """Overall report summarizing verification of all ground truth cases."""

    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    case_results: list[CaseVerificationResult] = field(default_factory=list)

    @property
    def is_all_passed(self) -> bool:
        return self.passed_cases == self.total_cases and self.total_cases > 0


class GraphGroundTruthVerifier:
    """Verifies that the Neo4j graph reproduces all structural relationships in Stage 12 ground truth."""

    def __init__(self, client: Neo4jClient, data_dir: Path | None = None) -> None:
        self.client = client
        self.data_dir = data_dir or find_data_dir()

    def load_ground_truth(self) -> list[dict[str, Any]]:
        path = self.data_dir / "ground_truth" / "ground_truth.json"
        if not path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def verify_case(self, gt: dict[str, Any]) -> CaseVerificationResult:
        case_id = gt["case_id"]
        invoice_id = gt["invoice_id"]
        expected_status = gt["expected_status"]
        expected_contract_id = gt.get("governing_contract_id")
        expected_exception_id = gt.get("exception_id")
        expected_approval_id = gt.get("approval_id")
        expected_evidence_ids = set(gt.get("relevant_evidence_ids", []))
        known_failure = gt.get("known_failure_condition")

        details: list[str] = []

        lineage = get_invoice_lineage(self.client, invoice_id)
        if not lineage:
            return CaseVerificationResult(
                case_id=case_id,
                invoice_id=invoice_id,
                expected_status=expected_status,
                passed=False,
                governing_contract_match=False,
                exception_match=False,
                approval_match=False,
                evidence_reachable=False,
                failure_condition_verified=False,
                details=[f"Invoice '{invoice_id}' not found in graph"],
            )

        # 1. Governing contract check
        contract_node = lineage.get("contract")
        actual_contract_id = contract_node.get("id") if contract_node else None
        contract_match = actual_contract_id == expected_contract_id
        if not contract_match:
            details.append(f"Contract mismatch: expected {expected_contract_id}, found {actual_contract_id}")

        # 2. Exception check
        exception_node = lineage.get("exception")
        actual_exception_id = exception_node.get("id") if exception_node else None
        exception_match = actual_exception_id == expected_exception_id
        if not exception_match:
            details.append(f"Exception mismatch: expected {expected_exception_id}, found {actual_exception_id}")

        # 3. Approval check
        approval_node = lineage.get("approval")
        actual_approval_id = approval_node.get("id") if approval_node else None
        approval_match = actual_approval_id == expected_approval_id
        if not approval_match:
            details.append(f"Approval mismatch: expected {expected_approval_id}, found {actual_approval_id}")

        # 4. Relevant evidence reachable in lineage
        lineage_evidence_ids = {ev["id"] for ev in lineage.get("evidence", [])}
        missing_evidence = expected_evidence_ids - lineage_evidence_ids
        evidence_reachable = len(missing_evidence) == 0
        if not evidence_reachable:
            details.append(f"Missing expected evidence citations in lineage: {missing_evidence}")

        # 5. Failure condition check against graph structure
        failure_verified = True
        if known_failure == "MISSING_CONTRACT":
            failure_verified = actual_contract_id is None
            if not failure_verified:
                details.append("Expected MISSING_CONTRACT but governing contract was found")
        elif known_failure == "MISSING_APPROVAL":
            failure_verified = actual_approval_id is None
            if not failure_verified:
                details.append("Expected MISSING_APPROVAL but approval was found")
        elif known_failure == "CONFLICTING_AMENDMENTS":
            # CASE-005 has both AMD-005 and AMD-006
            amendments = {a["id"] for a in lineage.get("amendments", [])}
            failure_verified = "AMD-005" in amendments and "AMD-006" in amendments
            if not failure_verified:
                details.append("Expected CONFLICTING_AMENDMENTS (AMD-005, AMD-006) in lineage")

        passed = (
            contract_match
            and exception_match
            and approval_match
            and evidence_reachable
            and failure_verified
        )

        return CaseVerificationResult(
            case_id=case_id,
            invoice_id=invoice_id,
            expected_status=expected_status,
            passed=passed,
            governing_contract_match=contract_match,
            exception_match=exception_match,
            approval_match=approval_match,
            evidence_reachable=evidence_reachable,
            failure_condition_verified=failure_verified,
            details=details,
        )

    def verify_all(self) -> GroundTruthVerificationReport:
        """Verify all ground truth cases against the Neo4j graph."""
        cases = self.load_ground_truth()
        results = [self.verify_case(gt) for gt in cases]
        passed_cnt = sum(1 for r in results if r.passed)
        failed_cnt = len(results) - passed_cnt

        return GroundTruthVerificationReport(
            total_cases=len(results),
            passed_cases=passed_cnt,
            failed_cases=failed_cnt,
            case_results=results,
        )
