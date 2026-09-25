"""Automated tests for Stage 18.5 Claim A: Agent Necessity Experiment.

Proves that an adaptive agent layer provides meaningful operational advantages
over a fixed deterministic/heuristic sequence:
1. Dynamic early stopping when conclusive proof or early rejection is identified.
2. Backtracking and recovery from dead ends.
3. Avoiding unnecessary tool calls and context contamination.
4. Higher accuracy and resource efficiency on branching workflows.
"""

from __future__ import annotations

import pytest

from evaluation.adapters.adaptive import AdaptiveAgentAdapter
from evaluation.adapters.heuristic import HeuristicAgentAdapter
from evaluation.dataset import load_benchmark_cases, load_seed_lineages


@pytest.fixture
def branching_dataset():
    """Load branching dataset cases and seed lineages."""
    cases = load_benchmark_cases("adaptive")
    lineages = load_seed_lineages()
    return cases, lineages


def test_agent_necessity_accuracy_comparison(branching_dataset):
    """Adaptive agent achieves 100% accuracy on branching workflows while fixed heuristic fails."""
    cases, lineages = branching_dataset

    adaptive_adapter = AdaptiveAgentAdapter()
    adaptive_run = adaptive_adapter.run_suite(cases, lineages)

    heuristic_adapter = HeuristicAgentAdapter()
    heuristic_run = heuristic_adapter.run_suite(cases, lineages)

    # Adaptive agent correctly navigates all 5 branching scenarios
    assert adaptive_run.aggregate_metrics.accuracy == 1.0
    assert adaptive_run.aggregate_metrics.correct_cases == 5

    # Heuristic baseline fails on branching scenarios (e.g. dead ends / early stops)
    assert heuristic_run.aggregate_metrics.accuracy is not None
    assert heuristic_run.aggregate_metrics.accuracy < 1.0


def test_agent_necessity_tool_efficiency(branching_dataset):
    """Adaptive agent significantly reduces total tool calls and eliminates unnecessary calls."""
    cases, lineages = branching_dataset

    adaptive_adapter = AdaptiveAgentAdapter()
    adaptive_run = adaptive_adapter.run_suite(cases, lineages)

    heuristic_adapter = HeuristicAgentAdapter()
    heuristic_run = heuristic_adapter.run_suite(cases, lineages)

    # Adaptive makes zero unnecessary tool calls
    assert adaptive_run.aggregate_metrics.total_unnecessary_tool_calls == 0

    # Fixed heuristic makes unnecessary calls across cases
    assert heuristic_run.aggregate_metrics.total_unnecessary_tool_calls > 0

    # Total tool calls: adaptive is strictly more efficient
    assert adaptive_run.aggregate_metrics.total_tool_calls < heuristic_run.aggregate_metrics.total_tool_calls


def test_agent_necessity_early_termination(branching_dataset):
    """Adaptive agent dynamically terminates early when conclusive proof or rejection is found."""
    cases, lineages = branching_dataset

    adaptive_adapter = AdaptiveAgentAdapter()
    adaptive_run = adaptive_adapter.run_suite(cases, lineages)

    # Early terminations recorded for BRANCH-001, BRANCH-003, BRANCH-005
    assert adaptive_run.aggregate_metrics.early_terminations >= 2

    # Verify BRANCH-001 terminated early on matching base contract
    res_001 = next(r for r in adaptive_run.case_results if r.case_id == "BRANCH-001")
    assert res_001.status_match is True
    assert res_001.actual_status == "VERIFIED"
    assert res_001.unnecessary_tool_calls == 0

    heu_res_001 = next(
        r for r in HeuristicAgentAdapter().run_suite(cases, lineages).case_results
        if r.case_id == "BRANCH-001"
    )
    assert res_001.tool_calls < heu_res_001.tool_calls


def test_agent_necessity_dead_end_recovery(branching_dataset):
    """Adaptive agent successfully backtracks from dead-end branches (BRANCH-004)."""
    cases, lineages = branching_dataset

    adaptive_adapter = AdaptiveAgentAdapter()
    adaptive_run = adaptive_adapter.run_suite(cases, lineages)

    # Recovery rate across branching cases
    assert adaptive_run.aggregate_metrics.recovery_rate is not None
    assert adaptive_run.aggregate_metrics.recovery_rate >= 0.5

    res_004 = next(r for r in adaptive_run.case_results if r.case_id == "BRANCH-004")
    assert res_004.status_match is True
    assert res_004.actual_status == "NOT_VERIFIED"
    assert res_004.recovery_success is True
