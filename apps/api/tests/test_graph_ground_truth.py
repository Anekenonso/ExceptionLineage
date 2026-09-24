"""Tests validating the graph state against Stage 12 ground truth determinations."""

import json
from unittest.mock import MagicMock

from app.graph.client import Neo4jClient
from app.graph.loader import find_data_dir
from app.graph.verifier import GraphGroundTruthVerifier


def build_mock_seed_graph_lineage() -> dict[str, dict]:
    """Build simulated graph traversal lineage outputs directly from the Stage 12 seed records."""
    data_dir = find_data_dir()
    seed_dir = data_dir / "seed"

    def read_seed(name: str):
        with open(seed_dir / name, "r", encoding="utf-8") as f:
            return {item["id"]: item for item in json.load(f)}

    customers = read_seed("customers.json")
    contracts = read_seed("contracts.json")
    amendments = read_seed("amendments.json")
    sows = read_seed("sows.json")
    exceptions = read_seed("exceptions.json")
    approvals = read_seed("approvals.json")
    invoices = read_seed("invoices.json")
    evidence = read_seed("evidence.json")

    lineages: dict[str, dict] = {}

    for inv_id, inv in invoices.items():
        cid = inv.get("customer_id")
        kid = inv.get("contract_id")
        eid = inv.get("exception_id")

        cust_node = customers.get(cid) if cid else None
        contract_node = contracts.get(kid) if kid else None
        exception_node = exceptions.get(eid) if eid else None

        # Approval linked to exception
        approval_node = None
        if exception_node:
            for apr in approvals.values():
                if apr.get("exception_id") == exception_node["id"]:
                    approval_node = apr
                    break

        # Amendments and SOWs linked to contract
        linked_amendments = []
        linked_sows = []
        if contract_node:
            linked_amendments = [a for a in amendments.values() if a.get("contract_id") == contract_node["id"]]
            linked_sows = [s for s in sows.values() if s.get("contract_id") == contract_node["id"]]

        # Evidence linked to any of these entities
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

    return lineages


def test_ground_truth_verifier_all_8_cases_pass() -> None:
    lineages = build_mock_seed_graph_lineage()

    mock_client = MagicMock(spec=Neo4jClient)

    def mock_execute_query(query: str, parameters: dict | None = None):
        if parameters and "invoice_id" in parameters:
            inv_id = parameters["invoice_id"]
            if inv_id in lineages:
                lin = lineages[inv_id]
                return [lin]
        return []

    mock_client.execute_query.side_effect = mock_execute_query

    verifier = GraphGroundTruthVerifier(mock_client)
    report = verifier.verify_all()

    assert report.total_cases == 8
    assert report.passed_cases == 8
    assert report.failed_cases == 0
    assert report.is_all_passed

    # Verify per-case checks
    results_by_case = {r.case_id: r for r in report.case_results}

    # CASE-001 (VERIFIED): Contract CTR-001, EX-001, APR-001, EV-001, EV-002, EV-003
    c1 = results_by_case["CASE-001"]
    assert c1.passed
    assert c1.governing_contract_match
    assert c1.exception_match
    assert c1.approval_match
    assert c1.evidence_reachable

    # CASE-002 (INSUFFICIENT_EVIDENCE): Missing approval
    c2 = results_by_case["CASE-002"]
    assert c2.passed
    assert c2.approval_match  # None == None
    assert c2.failure_condition_verified

    # CASE-005 (NEEDS_REVIEW): Conflicting amendments
    c5 = results_by_case["CASE-005"]
    assert c5.passed
    assert c5.failure_condition_verified

    # CASE-007 (INSUFFICIENT_EVIDENCE): Missing contract
    c7 = results_by_case["CASE-007"]
    assert c7.passed
    assert c7.governing_contract_match  # None == None
    assert c7.failure_condition_verified


def test_ground_truth_verifier_detects_contract_mismatch() -> None:
    mock_client = MagicMock(spec=Neo4jClient)
    # Return wrong contract for INV-1001
    mock_client.execute_query.return_value = [
        {
            "invoice": {"id": "INV-1001"},
            "contract": {"id": "WRONG-CONTRACT"},
            "exception": {"id": "EX-001"},
            "approval": {"id": "APR-001"},
            "amendments": [],
            "sows": [],
            "evidence": [{"id": "EV-001"}, {"id": "EV-002"}, {"id": "EV-003"}],
        }
    ]

    verifier = GraphGroundTruthVerifier(mock_client)
    case_def = {
        "case_id": "CASE-001",
        "invoice_id": "INV-1001",
        "expected_status": "VERIFIED",
        "governing_contract_id": "CTR-001",
        "exception_id": "EX-001",
        "approval_id": "APR-001",
        "relevant_evidence_ids": ["EV-001", "EV-002", "EV-003"],
        "known_failure_condition": None,
    }

    result = verifier.verify_case(case_def)
    assert not result.passed
    assert not result.governing_contract_match
    assert any("Contract mismatch" in d for d in result.details)
