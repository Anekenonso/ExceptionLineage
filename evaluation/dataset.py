"""Evaluation dataset loader and scenario definition (Stage 18).

Loads controlled benchmark cases and ground truth data strictly for the evaluation
and testing layer. Production application code MUST NOT import this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkCase:
    """Controlled benchmark case containing input identifiers and ground truth expectations."""

    case_id: str
    invoice_id: str
    expected_status: str
    scenario_type: str | None = None
    title: str | None = None
    description: str | None = None
    core_question: str | None = None
    governing_contract_id: str | None = None
    applicable_amendment_ids: list[str] = field(default_factory=list)
    applicable_sow_ids: list[str] = field(default_factory=list)
    exception_id: str | None = None
    approval_id: str | None = None
    relevant_evidence_ids: list[str] = field(default_factory=list)
    explanation: str | None = None
    known_failure_condition: str | None = None


def find_project_data_dir() -> Path:
    """Resolve the repository data directory from current file location."""
    current = Path(__file__).resolve().parent
    for candidate in [current.parent / "data", current / "data", Path("data").resolve()]:
        if candidate.exists() and (candidate / "ground_truth").exists():
            return candidate
    # Fallback to root search
    for parent in current.parents:
        cand = parent / "data"
        if cand.exists() and (cand / "ground_truth").exists():
            return cand
    raise FileNotFoundError("Could not locate project data directory containing ground_truth/")


def load_benchmark_cases(dataset_name: str = "benchmark") -> list[BenchmarkCase]:
    """Load benchmark cases joining cases.json and ground_truth.json.

    Args:
        dataset_name: 'benchmark' for standard 8 cases, or 'extended' for edge-case scenarios.
    """
    data_dir = find_project_data_dir()
    gt_file = data_dir / "ground_truth" / "ground_truth.json"
    cases_file = data_dir / "cases" / "cases.json"

    with open(gt_file, "r", encoding="utf-8") as f:
        ground_truth_list = json.load(f)

    cases_metadata: dict[str, dict[str, Any]] = {}
    if cases_file.exists():
        with open(cases_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                cases_metadata[item["case_id"]] = item

    cases: list[BenchmarkCase] = []
    for gt in ground_truth_list:
        case_id = gt["case_id"]
        meta = cases_metadata.get(case_id, {})

        case = BenchmarkCase(
            case_id=case_id,
            invoice_id=gt["invoice_id"],
            expected_status=gt["expected_status"],
            scenario_type=meta.get("scenario_type"),
            title=meta.get("title"),
            description=meta.get("description"),
            core_question=meta.get("core_question"),
            governing_contract_id=gt.get("governing_contract_id"),
            applicable_amendment_ids=gt.get("applicable_amendment_ids") or [],
            applicable_sow_ids=gt.get("applicable_sow_ids") or [],
            exception_id=gt.get("exception_id"),
            approval_id=gt.get("approval_id"),
            relevant_evidence_ids=gt.get("relevant_evidence_ids") or [],
            explanation=gt.get("explanation"),
            known_failure_condition=gt.get("known_failure_condition"),
        )
        cases.append(case)

    if dataset_name == "extended":
        # Add controlled harder scenarios (CASE-009 through CASE-011)
        extended_cases = _get_extended_scenarios()
        cases.extend(extended_cases)

    return cases


def _get_extended_scenarios() -> list[BenchmarkCase]:
    """Return additional controlled edge scenarios exposing specific failure modes."""
    return [
        BenchmarkCase(
            case_id="CASE-009",
            invoice_id="INV-9001",
            expected_status="INSUFFICIENT_EVIDENCE",
            scenario_type="INCOMPLETE_LINEAGE_MISSING_CUSTOMER",
            title="Incomplete Lineage Missing Customer Master",
            description="Invoice references customer that does not exist in graph; lineage cannot be resolved.",
            core_question="How does the system terminate when customer master lineage is completely severed?",
            governing_contract_id=None,
            applicable_amendment_ids=[],
            applicable_sow_ids=[],
            exception_id="EX-9001",
            approval_id=None,
            relevant_evidence_ids=[],
            explanation="Customer record is absent, leaving the contract unanchored.",
            known_failure_condition="SEVERED_LINEAGE",
        ),
        BenchmarkCase(
            case_id="CASE-010",
            invoice_id="INV-9002",
            expected_status="NOT_VERIFIED",
            scenario_type="IRRELEVANT_AMENDMENT_SCOPE",
            title="Irrelevant Amendment Scope Applied to Support",
            description="Amendment authorizes discounted rate for hardware maintenance, billed for professional services.",
            core_question="Does the system prevent unauthorized rate application from an irrelevant scope amendment?",
            governing_contract_id="CTR-001",
            applicable_amendment_ids=[],
            applicable_sow_ids=[],
            exception_id="EX-9002",
            approval_id=None,
            relevant_evidence_ids=["EV-001"],
            explanation="Amendment scope does not cover billed line items.",
            known_failure_condition="IRRELEVANT_AMENDMENT_SCOPE",
        ),
    ]


def load_seed_lineages() -> dict[str, dict[str, Any]]:
    """Build simulated graph traversal lineage outputs directly from the Stage 12 seed records.

    Used by evaluation adapters to run against local controlled data without requiring Neo4j.
    """
    data_dir = find_project_data_dir()
    seed_dir = data_dir / "seed"

    def read_seed(name: str) -> dict[str, dict[str, Any]]:
        file_path = seed_dir / name
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return {item["id"]: item for item in json.load(f)}

    customers = read_seed("customers.json")
    contracts = read_seed("contracts.json")
    amendments = read_seed("amendments.json")
    sows = read_seed("sows.json")
    exceptions = read_seed("exceptions.json")
    approvals = read_seed("approvals.json")
    invoices = read_seed("invoices.json")
    evidence = read_seed("evidence.json")

    lineages: dict[str, dict[str, Any]] = {}

    for inv_id, inv in invoices.items():
        cid = inv.get("customer_id")
        kid = inv.get("contract_id")
        eid = inv.get("exception_id")

        cust_node = customers.get(cid) if cid else None
        contract_node = contracts.get(kid) if kid else None
        exception_node = exceptions.get(eid) if eid else None

        approval_node = None
        if exception_node:
            for apr in approvals.values():
                if apr.get("exception_id") == exception_node["id"]:
                    approval_node = apr
                    break

        linked_amendments: list[dict[str, Any]] = []
        linked_sows: list[dict[str, Any]] = []
        if contract_node:
            linked_amendments = [
                a for a in amendments.values() if a.get("contract_id") == contract_node["id"]
            ]
            linked_sows = [
                s for s in sows.values() if s.get("contract_id") == contract_node["id"]
            ]

        active_ids = {
            x["id"]
            for x in [contract_node, exception_node, approval_node, *linked_amendments, *linked_sows]
            if x is not None
        }
        linked_evidence = [ev for ev in evidence.values() if ev.get("source_id") in active_ids]

        lineages[inv_id] = {
            "invoice": inv,
            "customer": cust_node,
            "contract": contract_node,
            "exception": exception_node,
            "approval": approval_node,
            "amendments": linked_amendments,
            "sows": linked_sows,
            "evidence": linked_evidence,
        }

    # Add simulated lineages for extended test cases
    lineages["INV-9001"] = {
        "invoice": {"id": "INV-9001", "amount": 10000.0, "customer_id": "CUS-NONEXISTENT", "contract_id": None},
        "customer": None,
        "contract": None,
        "exception": {"id": "EX-9001", "type": "MISSING_CUSTOMER"},
        "approval": None,
        "amendments": [],
        "sows": [],
        "evidence": [],
    }
    lineages["INV-9002"] = {
        "invoice": {"id": "INV-9002", "amount": 14000.0, "customer_id": "CUS-001", "contract_id": "CTR-001", "product_code": "PROD-CONSULTING"},
        "customer": customers.get("CUS-001"),
        "contract": contracts.get("CTR-001"),
        "exception": {"id": "EX-9002", "type": "RATE_OVERAGE"},
        "approval": None,
        "amendments": [],
        "sows": [],
        "evidence": [ev for ev in evidence.values() if ev.get("source_id") == "CTR-001"],
    }

    return lineages
