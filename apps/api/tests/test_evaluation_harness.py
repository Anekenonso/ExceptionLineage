"""Tests for the Stage 18 Evaluation Harness and Reporting Infrastructure.

Verifies:
1. DeterministicValidationAdapter evaluates Baseline A correctly across all benchmark cases.
2. HeuristicAgentAdapter evaluates Baseline B correctly across all benchmark cases.
3. LLMDecisionAdapter executes in mock mode and records valid operational and failure metrics.
4. Metric computations (accuracy, evidence recall, tool usage, termination, tokens).
5. JSON and Markdown report generation and schema compliance.
6. Evaluation runner CLI execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pytest

from evaluation.adapters.deterministic import DeterministicValidationAdapter
from evaluation.adapters.heuristic import HeuristicAgentAdapter
from evaluation.adapters.llm import LLMDecisionAdapter, create_deterministic_mock_llm_client
from evaluation.dataset import BenchmarkCase, load_benchmark_cases, load_seed_lineages
from evaluation.metrics import classify_run_status, compute_aggregate_metrics, compute_evidence_recall
from evaluation.reporter import generate_markdown_report, save_json_report, save_markdown_report
from evaluation.runner import run_evaluation
from evaluation.schemas import AggregateMetrics, CaseResult, EvaluationRun, EvaluationStatus, EvaluationSuiteReport


@pytest.fixture
def benchmark_data():
    cases = load_benchmark_cases("benchmark")
    lineages = load_seed_lineages()
    return cases, lineages


def test_compute_evidence_recall_edge_cases():
    """Verify evidence recall formula across regular, empty, and partial sets."""
    # 1. Zero required evidence items (e.g. CASE-007) -> recall is 1.0 (no required items missed)
    req_cnt, ret_cnt, recall = compute_evidence_recall(required_ids=[], retrieved_ids=["EV-001"])
    assert req_cnt == 0
    assert ret_cnt == 0
    assert recall == 1.0

    # 2. Complete retrieval
    req_cnt, ret_cnt, recall = compute_evidence_recall(
        required_ids=["EV-001", "EV-002"],
        retrieved_ids=["EV-001", "EV-002", "EV-003"],
    )
    assert req_cnt == 2
    assert ret_cnt == 2
    assert recall == 1.0

    # 3. Partial retrieval
    req_cnt, ret_cnt, recall = compute_evidence_recall(
        required_ids=["EV-001", "EV-002", "EV-003", "EV-004"],
        retrieved_ids=["EV-001", "EV-002"],
    )
    assert req_cnt == 4
    assert ret_cnt == 2
    assert recall == 0.5

    # 4. Zero retrieved
    req_cnt, ret_cnt, recall = compute_evidence_recall(
        required_ids=["EV-001"],
        retrieved_ids=[],
    )
    assert req_cnt == 1
    assert ret_cnt == 0
    assert recall == 0.0


def test_deterministic_validation_adapter(benchmark_data):
    """Verify Baseline A: Deterministic validation engine adapter."""
    cases, lineages = benchmark_data
    adapter = DeterministicValidationAdapter()
    run = adapter.run_suite(cases, lineages)

    assert run.baseline_name == "deterministic_baseline"
    assert run.status == EvaluationStatus.COMPLETED
    assert run.aggregate_metrics.total_cases == 8
    assert run.aggregate_metrics.correct_cases == 8
    assert run.aggregate_metrics.accuracy == 1.0
    assert run.aggregate_metrics.mean_evidence_recall == 1.0
    assert run.aggregate_metrics.total_agent_steps == 0
    assert run.aggregate_metrics.total_tool_calls == 0
    assert run.aggregate_metrics.validation_calls == 8

    # Verify termination breakdown
    term_counts = run.aggregate_metrics.termination_counts
    assert term_counts["VERIFIED"] == 2
    assert term_counts["NOT_VERIFIED"] == 3
    assert term_counts["INSUFFICIENT_EVIDENCE"] == 2
    assert term_counts["NEEDS_REVIEW"] == 1
    assert term_counts["FAILED"] == 0
    assert term_counts["STEP_LIMIT_EXCEEDED"] == 0


def test_heuristic_agent_adapter(benchmark_data):
    """Verify Baseline B: Heuristic agent model adapter."""
    cases, lineages = benchmark_data
    adapter = HeuristicAgentAdapter(max_steps=10)
    run = adapter.run_suite(cases, lineages)

    assert run.baseline_name == "heuristic_baseline"
    assert run.status == EvaluationStatus.COMPLETED
    assert run.aggregate_metrics.total_cases == 8
    assert run.aggregate_metrics.correct_cases == 8
    assert run.aggregate_metrics.accuracy == 1.0
    assert run.aggregate_metrics.mean_evidence_recall == 1.0
    assert run.aggregate_metrics.total_agent_steps > 0
    assert run.aggregate_metrics.total_tool_calls > 0
    assert run.aggregate_metrics.successful_tool_calls == run.aggregate_metrics.total_tool_calls
    assert run.aggregate_metrics.failed_tool_calls == 0
    assert run.aggregate_metrics.validation_calls == 8


def test_llm_decision_adapter_in_mock_mode(benchmark_data):
    """Verify System Under Evaluation: LLMDecisionModel in mock mode."""
    cases, lineages = benchmark_data
    adapter = LLMDecisionAdapter(is_mock=True, max_steps=10)
    assert adapter.is_configured()

    run = adapter.run_suite(cases, lineages)
    assert run.baseline_name == "llm_decision_model"
    assert run.status == EvaluationStatus.COMPLETED
    assert run.aggregate_metrics.total_cases == 8
    assert run.aggregate_metrics.total_tokens is not None
    assert run.aggregate_metrics.total_tokens > 0
    assert run.aggregate_metrics.total_llm_calls > 0


def test_report_generation(tmp_path, benchmark_data):
    """Verify JSON and Markdown report generation and schema persistence."""
    cases, lineages = benchmark_data

    det_adapter = DeterministicValidationAdapter()
    det_run = det_adapter.run_suite(cases, lineages)

    heu_adapter = HeuristicAgentAdapter()
    heu_run = heu_adapter.run_suite(cases, lineages)

    suite = EvaluationSuiteReport(
        suite_id="test-suite-001",
        timestamp="2026-09-24T18:00:00Z",
        git_commit="test-commit-sha",
        dataset_version="benchmark-v1",
        runs={
            "deterministic_baseline": det_run,
            "heuristic_baseline": heu_run,
        },
        summary={"total_baselines": 2, "completed_baselines": 2},
    )

    json_path = tmp_path / "test_report.json"
    save_json_report(suite, json_path)
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["suite_id"] == "test-suite-001"
    assert "deterministic_baseline" in loaded["runs"]
    assert "heuristic_baseline" in loaded["runs"]

    md_path = tmp_path / "test_report.md"
    md_content = generate_markdown_report(suite)
    save_markdown_report(md_content, md_path)
    assert md_path.exists()
    assert "# Stage 18 Evaluation Report" in md_content
    assert "deterministic_baseline" in md_content
    assert "heuristic_baseline" in md_content


def test_evaluation_runner_end_to_end(tmp_path):
    """Verify evaluation runner end-to-end execution without live LLM dependencies."""
    suite = run_evaluation(
        baseline="all",
        dataset="benchmark",
        with_llm=False,
        mock_llm=False,
        output_dir=tmp_path,
    )
    assert suite.suite_id.startswith("suite-")
    assert "deterministic_baseline" in suite.runs
    assert "heuristic_baseline" in suite.runs
    assert "llm_decision_model" in suite.runs

    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "latest.md").exists()
    assert suite.runs["llm_decision_model"].status == EvaluationStatus.SKIPPED


# ==============================================================================
# Stage 18 Closure: Evaluation Integrity & Reporting Semantics Tests (Task 7)
# ==============================================================================


def test_reporting_semantics_1_successful_evaluation_completed():
    """Requirement 1: A successful run across benchmark cases produces status COMPLETED."""
    cases = [
        CaseResult(
            case_id=f"CASE-00{i}",
            invoice_id=f"INV-100{i}",
            expected_status="VERIFIED",
            actual_status="VERIFIED",
            status_match=True,
            evidence_recall=1.0,
            required_evidence_count=2,
            retrieved_required_evidence_count=2,
        )
        for i in range(1, 9)
    ]
    agg = compute_aggregate_metrics(cases)
    status, detail = classify_run_status(cases, agg)

    assert status == EvaluationStatus.COMPLETED
    assert agg.is_measurable is True
    assert agg.accuracy == 1.0
    assert agg.mean_evidence_recall == 1.0


def test_reporting_semantics_2_provider_quota_failure_blocked_provider():
    """Requirement 2: Provider quota failure (HTTP 429) across all cases produces BLOCKED_PROVIDER."""
    cases = [
        CaseResult(
            case_id=f"CASE-00{i}",
            invoice_id=f"INV-100{i}",
            expected_status="VERIFIED",
            actual_status="FAILED",
            status_match=False,
            is_provider_failure=True,
            provider_failure_category="provider_quota",
            provider_http_status=429,
            failure_reason="Graph retrieval failed: LLM rate limit reached (HTTP 429): please retry after backoff",
        )
        for i in range(1, 9)
    ]
    agg = compute_aggregate_metrics(cases)
    status, detail = classify_run_status(cases, agg)

    assert status == EvaluationStatus.BLOCKED_PROVIDER
    assert agg.is_measurable is False
    assert agg.provider_failures == 8
    assert agg.provider_failure_category == "provider_quota"
    assert agg.provider_http_status == 429


def test_reporting_semantics_3_system_exception_failed_system():
    """Requirement 3: System crash / unhandled internal exception produces FAILED_SYSTEM."""
    cases = [
        CaseResult(
            case_id=f"CASE-00{i}",
            invoice_id=f"INV-100{i}",
            expected_status="VERIFIED",
            actual_status="FAILED",
            status_match=False,
            is_provider_failure=False,
            error="ConnectionRefusedError: Neo4j database unreachable at bolt://localhost:7687",
        )
        for i in range(1, 9)
    ]
    agg = compute_aggregate_metrics(cases)
    status, detail = classify_run_status(cases, agg)

    assert status == EvaluationStatus.FAILED_SYSTEM
    assert "system exceptions" in str(detail).lower()


def test_reporting_semantics_4_partial_evaluation_partial():
    """Requirement 4: Partial completion (some cases succeed, some hit provider errors) produces PARTIAL."""
    cases = [
        CaseResult(
            case_id="CASE-001",
            invoice_id="INV-1001",
            expected_status="VERIFIED",
            actual_status="VERIFIED",
            status_match=True,
            evidence_recall=1.0,
        ),
        CaseResult(
            case_id="CASE-002",
            invoice_id="INV-1002",
            expected_status="INSUFFICIENT_EVIDENCE",
            actual_status="FAILED",
            status_match=False,
            is_provider_failure=True,
            provider_failure_category="provider_quota",
            provider_http_status=429,
            failure_reason="LLM rate limit reached (HTTP 429)",
        ),
    ]
    agg = compute_aggregate_metrics(cases)
    status, detail = classify_run_status(cases, agg)

    assert status == EvaluationStatus.PARTIAL
    assert agg.is_measurable is False
    assert agg.provider_failures == 1
    assert agg.cases_completed == 1


def test_reporting_semantics_5_provider_blocked_does_not_calculate_accuracy():
    """Requirement 5: A provider-blocked run does NOT calculate model accuracy as 0.0, but sets it to None."""
    cases = [
        CaseResult(
            case_id=f"CASE-00{i}",
            invoice_id=f"INV-100{i}",
            expected_status="VERIFIED",
            actual_status="FAILED",
            status_match=False,
            failure_reason="LLM rate limit reached (HTTP 429): please retry after backoff or check provider limits",
        )
        for i in range(1, 9)
    ]
    agg = compute_aggregate_metrics(cases)

    # Must be None, NEVER 0.0 or 0%
    assert agg.accuracy is None
    assert agg.is_measurable is False
    assert "UNMEASURABLE" in (agg.unmeasurable_reason or "")


def test_reporting_semantics_6_provider_blocked_does_not_calculate_evidence_recall():
    """Requirement 6: A provider-blocked run does NOT calculate evidence recall, avoiding CASE-007 skew."""
    cases = [
        CaseResult(
            case_id="CASE-001",
            invoice_id="INV-1001",
            expected_status="VERIFIED",
            actual_status="FAILED",
            status_match=False,
            required_evidence_count=3,
            retrieved_required_evidence_count=0,
            failure_reason="LLM rate limit reached (HTTP 429)",
        ),
        # CASE-007 normally has 0 required items which yields 1.0 when executed;
        # on provider blockage it must NOT skew aggregate recall
        CaseResult(
            case_id="CASE-007",
            invoice_id="INV-1007",
            expected_status="INSUFFICIENT_EVIDENCE",
            actual_status="FAILED",
            status_match=False,
            required_evidence_count=0,
            retrieved_required_evidence_count=0,
            failure_reason="LLM rate limit reached (HTTP 429)",
        ),
    ]
    agg = compute_aggregate_metrics(cases)

    # Evidence recall must be None rather than 0.5 or 0.125
    assert agg.mean_evidence_recall is None
    assert agg.overall_evidence_recall is None
    assert cases[1].evidence_recall is None


def test_reporting_semantics_7_baseline_metrics_remain_measurable(benchmark_data):
    """Requirement 7: Deterministic and heuristic baseline metrics remain 100% measurable."""
    cases, lineages = benchmark_data

    det_adapter = DeterministicValidationAdapter()
    det_run = det_adapter.run_suite(cases, lineages)
    assert det_run.status == EvaluationStatus.COMPLETED
    assert det_run.aggregate_metrics.is_measurable is True
    assert det_run.aggregate_metrics.accuracy == 1.0
    assert det_run.aggregate_metrics.mean_evidence_recall == 1.0

    heu_adapter = HeuristicAgentAdapter(max_steps=10)
    heu_run = heu_adapter.run_suite(cases, lineages)
    assert heu_run.status == EvaluationStatus.COMPLETED
    assert heu_run.aggregate_metrics.is_measurable is True
    assert heu_run.aggregate_metrics.accuracy == 1.0
    assert heu_run.aggregate_metrics.mean_evidence_recall == 1.0
    assert heu_run.aggregate_metrics.total_tool_calls == 51


def test_reporting_semantics_8_ground_truth_isolated():
    """Requirement 8: Ground truth datasets and evaluation reporting remain isolated from production code."""
    from tests.test_ground_truth_isolation import (
        test_production_code_ast_imports_isolated,
        test_production_code_contains_no_hardcoded_benchmark_references,
    )
    test_production_code_ast_imports_isolated()
    test_production_code_contains_no_hardcoded_benchmark_references()
