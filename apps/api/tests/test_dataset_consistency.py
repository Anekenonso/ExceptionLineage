from decimal import Decimal
import json
from pathlib import Path
import pytest

from app.models import (
    Amendment,
    Approval,
    Contract,
    Customer,
    Evidence,
    Exception as ExceptionModel,
    InvestigationStatus,
    Invoice,
    SOW,
)

# Resolve data directory relative to repository root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
CASES_DIR = DATA_DIR / "cases"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"


def load_json(filepath: Path) -> list[dict]:
    assert filepath.exists(), f"File {filepath} must exist"
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def customers_data():
    return load_json(SEED_DIR / "customers.json")


@pytest.fixture(scope="module")
def contracts_data():
    return load_json(SEED_DIR / "contracts.json")


@pytest.fixture(scope="module")
def amendments_data():
    return load_json(SEED_DIR / "amendments.json")


@pytest.fixture(scope="module")
def sows_data():
    return load_json(SEED_DIR / "sows.json")


@pytest.fixture(scope="module")
def exceptions_data():
    return load_json(SEED_DIR / "exceptions.json")


@pytest.fixture(scope="module")
def approvals_data():
    return load_json(SEED_DIR / "approvals.json")


@pytest.fixture(scope="module")
def invoices_data():
    return load_json(SEED_DIR / "invoices.json")


@pytest.fixture(scope="module")
def evidence_data():
    return load_json(SEED_DIR / "evidence.json")


@pytest.fixture(scope="module")
def cases_data():
    return load_json(CASES_DIR / "cases.json")


@pytest.fixture(scope="module")
def ground_truth_data():
    return load_json(GROUND_TRUTH_DIR / "ground_truth.json")


# ==============================================================================
# 1. Pydantic Model Validation for All Seed Data
# ==============================================================================


def test_customers_parse_into_pydantic(customers_data):
    assert len(customers_data) >= 3
    for record in customers_data:
        # Strip metadata key if present
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Customer.model_validate(data)
        assert model.id == record["id"]


def test_contracts_parse_into_pydantic(contracts_data):
    assert len(contracts_data) >= 2
    for record in contracts_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Contract.model_validate(data)
        assert model.id == record["id"]


def test_amendments_parse_into_pydantic(amendments_data):
    assert len(amendments_data) >= 7
    for record in amendments_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Amendment.model_validate(data)
        assert model.id == record["id"]


def test_sows_parse_into_pydantic(sows_data):
    assert len(sows_data) >= 2
    for record in sows_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = SOW.model_validate(data)
        assert model.id == record["id"]


def test_exceptions_parse_into_pydantic(exceptions_data):
    assert len(exceptions_data) >= 7
    for record in exceptions_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = ExceptionModel.model_validate(data)
        assert model.id == record["id"]
        assert isinstance(model.expected_amount, (Decimal, type(None)))
        assert isinstance(model.actual_amount, (Decimal, type(None)))


def test_approvals_parse_into_pydantic(approvals_data):
    assert len(approvals_data) >= 3
    for record in approvals_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Approval.model_validate(data)
        assert model.id == record["id"]


def test_invoices_parse_into_pydantic(invoices_data):
    assert len(invoices_data) >= 8
    for record in invoices_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Invoice.model_validate(data)
        assert model.id == record["id"]
        assert isinstance(model.amount, Decimal)


def test_evidence_parse_into_pydantic(evidence_data):
    assert len(evidence_data) >= 13
    for record in evidence_data:
        data = {k: v for k, v in record.items() if not k.startswith("_")}
        model = Evidence.model_validate(data)
        assert model.id == record["id"]
        if model.confidence is not None:
            assert 0.0 <= model.confidence <= 1.0


# ==============================================================================
# 2. Identifier Uniqueness Across Entity Types
# ==============================================================================


@pytest.mark.parametrize(
    "dataset_fixture, id_field",
    [
        ("customers_data", "id"),
        ("contracts_data", "id"),
        ("amendments_data", "id"),
        ("sows_data", "id"),
        ("exceptions_data", "id"),
        ("approvals_data", "id"),
        ("invoices_data", "id"),
        ("evidence_data", "id"),
        ("cases_data", "case_id"),
        ("ground_truth_data", "case_id"),
    ],
)
def test_unique_identifiers(request, dataset_fixture, id_field):
    data = request.getfixturevalue(dataset_fixture)
    ids = [item[id_field] for item in data]
    assert len(ids) == len(set(ids)), f"Duplicate IDs detected in {dataset_fixture}"


# ==============================================================================
# 3. Foreign Key & Entity Reference Integrity
# ==============================================================================


def test_contracts_point_to_valid_customers(contracts_data, customers_data):
    valid_customer_ids = {c["id"] for c in customers_data}
    for ctr in contracts_data:
        assert ctr["customer_id"] in valid_customer_ids


def test_amendments_point_to_valid_contracts(amendments_data, contracts_data):
    valid_contract_ids = {c["id"] for c in contracts_data}
    for amd in amendments_data:
        assert amd["contract_id"] in valid_contract_ids


def test_sows_point_to_valid_contracts(sows_data, contracts_data):
    valid_contract_ids = {c["id"] for c in contracts_data}
    for sow in sows_data:
        assert sow["contract_id"] in valid_contract_ids


def test_exceptions_point_to_valid_contracts(exceptions_data, contracts_data):
    valid_contract_ids = {c["id"] for c in contracts_data}
    for exc in exceptions_data:
        assert exc["contract_id"] in valid_contract_ids


def test_approvals_point_to_valid_exceptions(approvals_data, exceptions_data):
    valid_exception_ids = {e["id"] for e in exceptions_data}
    for appr in approvals_data:
        assert appr["exception_id"] in valid_exception_ids


def test_invoices_point_to_valid_entities(invoices_data, customers_data, contracts_data, exceptions_data):
    valid_customer_ids = {c["id"] for c in customers_data}
    valid_contract_ids = {c["id"] for c in contracts_data}
    valid_exception_ids = {e["id"] for e in exceptions_data}

    for inv in invoices_data:
        assert inv["customer_id"] in valid_customer_ids
        if inv.get("contract_id") is not None:
            assert inv["contract_id"] in valid_contract_ids
        if inv.get("exception_id") is not None:
            assert inv["exception_id"] in valid_exception_ids


# ==============================================================================
# 4. Ground Truth Integrity & Valid Investigation States
# ==============================================================================


def test_ground_truth_references_exist(
    ground_truth_data,
    invoices_data,
    contracts_data,
    amendments_data,
    sows_data,
    exceptions_data,
    approvals_data,
    evidence_data,
):
    invoice_ids = {i["id"] for i in invoices_data}
    contract_ids = {c["id"] for c in contracts_data}
    amendment_ids = {a["id"] for a in amendments_data}
    sow_ids = {s["id"] for s in sows_data}
    exception_ids = {e["id"] for e in exceptions_data}
    approval_ids = {a["id"] for a in approvals_data}
    evidence_ids = {e["id"] for e in evidence_data}

    valid_statuses = {s.value for s in InvestigationStatus}

    for gt in ground_truth_data:
        # Expected status must be a legal Stage 11 InvestigationStatus
        assert gt["expected_status"] in valid_statuses

        # Invoice ID must exist
        assert gt["invoice_id"] in invoice_ids

        # Governing contract must exist if specified
        if gt.get("governing_contract_id") is not None:
            assert gt["governing_contract_id"] in contract_ids

        # Applicable amendments must exist
        for amd_id in gt.get("applicable_amendment_ids", []):
            assert amd_id in amendment_ids

        # Applicable SOWs must exist
        for sow_id in gt.get("applicable_sow_ids", []):
            assert sow_id in sow_ids

        # Exception ID must exist if specified
        if gt.get("exception_id") is not None:
            assert gt["exception_id"] in exception_ids

        # Approval ID must exist if specified
        if gt.get("approval_id") is not None:
            assert gt["approval_id"] in approval_ids

        # Cited evidence IDs must exist
        for ev_id in gt.get("relevant_evidence_ids", []):
            assert ev_id in evidence_ids


def test_cases_and_ground_truth_1to1_mapping(cases_data, ground_truth_data):
    case_ids = [c["case_id"] for c in cases_data]
    gt_case_ids = [gt["case_id"] for gt in ground_truth_data]
    assert case_ids == gt_case_ids
    assert len(case_ids) == 8


def test_intentional_missing_evidence_is_documented(ground_truth_data):
    gt_map = {gt["case_id"]: gt for gt in ground_truth_data}

    # Case 2: Approval is intentionally missing
    assert gt_map["CASE-002"]["approval_id"] is None
    assert gt_map["CASE-002"]["expected_status"] == InvestigationStatus.INSUFFICIENT_EVIDENCE.value
    assert gt_map["CASE-002"]["known_failure_condition"] == "MISSING_APPROVAL"

    # Case 7: Governing contract is intentionally missing
    assert gt_map["CASE-007"]["governing_contract_id"] is None
    assert gt_map["CASE-007"]["expected_status"] == InvestigationStatus.INSUFFICIENT_EVIDENCE.value
    assert gt_map["CASE-007"]["known_failure_condition"] == "MISSING_CONTRACT"


def test_simulation_notice_in_all_datasets():
    datasets = [
        SEED_DIR / "customers.json",
        SEED_DIR / "contracts.json",
        SEED_DIR / "amendments.json",
        SEED_DIR / "sows.json",
        SEED_DIR / "exceptions.json",
        SEED_DIR / "approvals.json",
        SEED_DIR / "invoices.json",
        SEED_DIR / "evidence.json",
        CASES_DIR / "cases.json",
        GROUND_TRUTH_DIR / "ground_truth.json",
    ]
    for filepath in datasets:
        data = load_json(filepath)
        for item in data:
            assert "_simulation_notice" in item
            assert "SIMULATED" in item["_simulation_notice"]
