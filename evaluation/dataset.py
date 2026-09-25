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
    unnecessary_tool_names: list[str] = field(default_factory=list)
    branching_type: str | None = None


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
        dataset_name: 'benchmark' for standard 8 cases, 'extended' for edge-case scenarios,
                      'adaptive' for branching scenarios, or 'all' for full combination.
    """
    if dataset_name == "adaptive":
        return _get_adaptive_scenarios()

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

    if dataset_name in ("extended", "all"):
        # Add controlled harder scenarios (CASE-009 through CASE-010)
        extended_cases = _get_extended_scenarios()
        cases.extend(extended_cases)

    if dataset_name == "all":
        cases.extend(_get_adaptive_scenarios())

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


def _get_adaptive_scenarios() -> list[BenchmarkCase]:
    """Controlled branching investigation scenarios designed to evaluate adaptive vs fixed workflows (Stage 18.5)."""
    return [
        BenchmarkCase(
            case_id="BRANCH-001",
            invoice_id="INV-2001",
            expected_status="VERIFIED",
            scenario_type="BASE_CONTRACT_MATCH_EARLY_STOP",
            title="Direct Base Contract Rate Match",
            description="Invoice amount matches base contract standard rate exactly ($10,000); no exception exists.",
            core_question="Does the agent terminate early upon discovering the invoice matches the base contract without querying unnecessary amendments or SOWs?",
            governing_contract_id="CTR-001",
            applicable_amendment_ids=[],
            applicable_sow_ids=[],
            exception_id=None,
            approval_id=None,
            relevant_evidence_ids=["EV-001"],
            explanation="Billed amount matches base contract standard rate; no variance exception requires investigation.",
            unnecessary_tool_names=["get_contract_amendments", "get_sows", "find_approvals"],
            branching_type="EARLY_STOP_BASE_MATCH",
        ),
        BenchmarkCase(
            case_id="BRANCH-002",
            invoice_id="INV-2002",
            expected_status="INSUFFICIENT_EVIDENCE",
            scenario_type="SEVERED_CONTRACT_EARLY_STOP",
            title="Severed Governing Contract Lineage",
            description="Invoice cites contract CTR-NONEXISTENT which does not exist in graph; lineage is severed.",
            core_question="Does the agent abort further discovery when governing contract is missing, avoiding redundant approval or evidence queries?",
            governing_contract_id=None,
            applicable_amendment_ids=[],
            applicable_sow_ids=[],
            exception_id="EX-2002",
            approval_id=None,
            relevant_evidence_ids=[],
            explanation="Governing contract is absent in the graph, rendering the transaction unanchored.",
            known_failure_condition="MISSING_CONTRACT",
            unnecessary_tool_names=["get_contract_amendments", "get_sows", "get_related_evidence"],
            branching_type="EARLY_STOP_MISSING_CONTRACT",
        ),
        BenchmarkCase(
            case_id="BRANCH-003",
            invoice_id="INV-2003",
            expected_status="VERIFIED",
            scenario_type="AMENDMENT_VARIANCE_AVOID_SOWS",
            title="Software Support Rate Variance Disregarding SOWs",
            description="Invoice billed under executed amendment AMD-001 with executive approval APR-001 on file. Querying SOWs is unnecessary.",
            core_question="Does the agent recognize that an authorizing amendment and approval fully govern the variance, avoiding unnecessary SOW searches?",
            governing_contract_id="CTR-001",
            applicable_amendment_ids=["AMD-001"],
            applicable_sow_ids=[],
            exception_id="EX-001",
            approval_id="APR-001",
            relevant_evidence_ids=["EV-001", "EV-002", "EV-003"],
            explanation="Tier-1 support discount authorized by AMD-001 and approved under APR-001.",
            unnecessary_tool_names=["get_sows"],
            branching_type="AVOID_IRRELEVANT_SOWS",
        ),
        BenchmarkCase(
            case_id="BRANCH-004",
            invoice_id="INV-2004",
            expected_status="NOT_VERIFIED",
            scenario_type="EXPLICIT_REJECTION_EARLY_STOP",
            title="Explicit Executive Rejection on File",
            description="Invoice exception EX-2004 has an approval record that is explicitly REJECTED by VP of Finance.",
            core_question="Does the agent recognize that formal approval rejection invalidates variance and halt further amendment/SOW queries?",
            governing_contract_id="CTR-001",
            applicable_amendment_ids=[],
            applicable_sow_ids=[],
            exception_id="EX-2004",
            approval_id="APR-2004",
            relevant_evidence_ids=["EV-2004"],
            explanation="Formal rejection on file directly invalidates the exception variance.",
            known_failure_condition="REJECTED_APPROVAL",
            unnecessary_tool_names=["get_contract_amendments", "get_sows"],
            branching_type="EARLY_STOP_ON_REJECTION",
        ),
        BenchmarkCase(
            case_id="BRANCH-005",
            invoice_id="INV-2005",
            expected_status="NEEDS_REVIEW",
            scenario_type="CONFLICTING_AMENDMENTS_EARLY_VALIDATE",
            title="Conflicting Concurrent Rate Amendments",
            description="Contract has two concurrent active amendments (AMD-005 and AMD-006) authorizing contradictory rates.",
            core_question="Does the agent detect irreconcilable amendment conflict and proceed directly to validation for review without querying SOWs or approvals?",
            governing_contract_id="CTR-001",
            applicable_amendment_ids=["AMD-005", "AMD-006"],
            applicable_sow_ids=[],
            exception_id="EX-005",
            approval_id=None,
            relevant_evidence_ids=["EV-005", "EV-006"],
            explanation="Concurrent conflicting rate amendments require legal review.",
            known_failure_condition="CONFLICTING_AMENDMENTS",
            unnecessary_tool_names=["get_sows"],
            branching_type="EARLY_ESCALATE_ON_CONFLICT",
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
    # Add simulated lineages for branching scenarios (BRANCH-001 through BRANCH-005)
    lineages["INV-2001"] = {
        "invoice": {
            "id": "INV-2001",
            "invoice_number": "INV-2001",
            "amount": "12000.00",
            "currency": "USD",
            "customer_id": "CUS-001",
            "contract_id": "CTR-001",
            "product_id": "PROD-CLOUD-SUP",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z",
            "exception_id": None,
        },
        "customer": customers.get("CUS-001"),
        "contract": contracts.get("CTR-001"),
        "exception": None,
        "approval": None,
        "amendments": [a for a in amendments.values() if a.get("contract_id") == "CTR-001"],
        "sows": [s for s in sows.values() if s.get("contract_id") == "CTR-001"],
        "evidence": [ev for ev in evidence.values() if ev.get("source_id") == "CTR-001"],
    }
    lineages["INV-2002"] = {
        "invoice": {
            "id": "INV-2002",
            "invoice_number": "INV-2002",
            "amount": "12500.00",
            "currency": "USD",
            "customer_id": "CUS-002",
            "contract_id": "CTR-NONEXISTENT",
            "product_id": "PROD-CLOUD-SUP",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z",
            "exception_id": "EX-2002",
        },
        "customer": customers.get("CUS-002"),
        "contract": None,
        "exception": {"id": "EX-2002", "invoice_id": "INV-2002", "type": "MISSING_CONTRACT", "description": "Unanchored transaction"},
        "approval": None,
        "amendments": [],
        "sows": [],
        "evidence": [],
    }
    lineages["INV-2003"] = {
        "invoice": {
            "id": "INV-2003",
            "invoice_number": "INV-2003",
            "amount": "10200.00",
            "currency": "USD",
            "customer_id": "CUS-001",
            "contract_id": "CTR-001",
            "product_id": "PROD-CLOUD-SUP",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z",
            "exception_id": "EX-001",
        },
        "customer": customers.get("CUS-001"),
        "contract": contracts.get("CTR-001"),
        "exception": exceptions.get("EX-001"),
        "approval": approvals.get("APR-001"),
        "amendments": [a for a in amendments.values() if a.get("id") == "AMD-001" or a.get("contract_id") == "CTR-001"],
        "sows": [s for s in sows.values() if s.get("contract_id") == "CTR-001"],
        "evidence": [ev for ev in evidence.values() if ev.get("source_id") in ("CTR-001", "AMD-001", "APR-001")],
    }
    lineages["INV-2004"] = {
        "invoice": {
            "id": "INV-2004",
            "invoice_number": "INV-2004",
            "amount": "14000.00",
            "currency": "USD",
            "customer_id": "CUS-001",
            "contract_id": "CTR-001",
            "product_id": "PROD-CLOUD-SUP",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z",
            "exception_id": "EX-2004",
        },
        "customer": customers.get("CUS-001"),
        "contract": contracts.get("CTR-001"),
        "exception": {"id": "EX-2004", "invoice_id": "INV-2004", "type": "RATE_OVERAGE", "description": "Overtime rate revision rejected"},
        "approval": {
            "id": "APR-2004",
            "exception_id": "EX-2004",
            "status": "REJECTED",
            "approver_role": "VP_FINANCE",
            "approver_name": "Executive Rejection",
            "notes": "Budget freeze rejection",
        },
        "amendments": [a for a in amendments.values() if a.get("contract_id") == "CTR-001"],
        "sows": [],
        "evidence": [{"id": "EV-2004", "source_id": "APR-2004", "type": "REJECTION_MEMO", "text": "Formal executive rejection of variance."}],
    }
    lineages["INV-2005"] = {
        "invoice": {
            "id": "INV-2005",
            "invoice_number": "INV-2005",
            "amount": "11250.00",
            "currency": "USD",
            "customer_id": "CUS-001",
            "contract_id": "CTR-001",
            "product_id": "PROD-CLOUD-SUP",
            "issued_at": "2026-03-15T00:00:00Z",
            "due_at": "2026-04-15T00:00:00Z",
            "exception_id": "EX-005",
        },
        "customer": customers.get("CUS-001"),
        "contract": contracts.get("CTR-001"),
        "exception": exceptions.get("EX-005"),
        "approval": None,
        "amendments": [
            a for a in amendments.values()
            if a.get("id") in ("AMD-005", "AMD-006") or a.get("contract_id") == "CTR-001"
        ],
        "sows": [s for s in sows.values() if s.get("contract_id") == "CTR-001"],
        "evidence": [ev for ev in evidence.values() if ev.get("source_id") in ("AMD-005", "AMD-006")],
    }

    return lineages
