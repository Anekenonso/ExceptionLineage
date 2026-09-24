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
from evaluation.metrics import compute_aggregate_metrics, compute_evidence_recall
from evaluation.reporter import generate_markdown_report, save_json_report, save_markdown_report
from evaluation.runner import run_evaluation
from evaluation.schemas import AggregateMetrics, CaseResult, EvaluationRun, EvaluationSuiteReport


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
    assert run.status == "COMPLETED"
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
    assert run.status == "COMPLETED"
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
    assert run.status == "COMPLETED"
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
    assert "# ExceptionLineage Quantitative Evaluation Report" in md_content
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
    assert suite.runs["llm_decision_model"].status == "SKIPPED"
