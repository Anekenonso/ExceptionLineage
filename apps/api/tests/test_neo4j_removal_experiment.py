"""Automated tests for Stage 18.5 Claim B: Neo4j Removal Experiment.

Proves that Neo4j / Knowledge Graph traversal is load-bearing for ExceptionLineage:
1. Multi-hop lineage completeness.
2. Avoiding context contamination from irrelevant/conflicting records.
3. Maintaining provenance chains across invoice -> contract -> amendment.
4. Reducing retrieval operation overhead compared to unindexed flat scans.
"""

from __future__ import annotations

import pytest

from evaluation.adapters.deterministic import DeterministicValidationAdapter
from evaluation.adapters.flat import FlatRetrievalAdapter
from evaluation.dataset import load_benchmark_cases, load_seed_lineages


@pytest.fixture
def benchmark_dataset():
    """Load canonical benchmark dataset cases and seed lineages."""
    cases = load_benchmark_cases("benchmark")
    lineages = load_seed_lineages()
    return cases, lineages


def test_neo4j_removal_accuracy_impact(benchmark_dataset):
    """Removing graph relationships and using flat retrieval causes false amendment conflicts and reduces accuracy."""
    cases, lineages = benchmark_dataset

    # Authoritative graph-backed deterministic validation engine: 100% accuracy
    graph_adapter = DeterministicValidationAdapter()
    graph_run = graph_adapter.run_suite(cases, lineages)
    assert graph_run.aggregate_metrics.accuracy == 1.0

    # Flat relational retrieval without explicit edge semantics
    flat_adapter = FlatRetrievalAdapter()
    flat_run = flat_adapter.run_suite(cases, lineages)

    # Flat accuracy drops (e.g. 87.5% due to customer-wide amendment contamination)
    assert flat_run.aggregate_metrics.accuracy is not None
    assert flat_run.aggregate_metrics.accuracy < 1.0
    assert flat_run.aggregate_metrics.accuracy == 0.875


def test_neo4j_removal_irrelevant_retrieval_contamination(benchmark_dataset):
    """Flat retrieval floods validation context with extraneous records lacking relationship bounds."""
    cases, lineages = benchmark_dataset

    flat_adapter = FlatRetrievalAdapter()
    flat_run = flat_adapter.run_suite(cases, lineages)

    # Flat retrieval pulls extraneous entities (37 across 8 cases)
    assert flat_run.aggregate_metrics.total_irrelevant_retrievals > 0
    assert flat_run.aggregate_metrics.total_irrelevant_retrievals == 37


def test_neo4j_removal_provenance_degradation(benchmark_dataset):
    """Flat retrieval fails to establish unbroken multi-hop relationship provenance."""
    cases, lineages = benchmark_dataset

    flat_adapter = FlatRetrievalAdapter()
    flat_run = flat_adapter.run_suite(cases, lineages)

    # Provenance completeness is severely degraded without graph edges
    assert flat_run.aggregate_metrics.provenance_completeness is not None
    assert flat_run.aggregate_metrics.provenance_completeness < 0.50
    assert flat_run.aggregate_metrics.provenance_completeness == 0.20


def test_neo4j_removal_query_multiplication(benchmark_dataset):
    """Flat relational retrieval requires multiple separate queries and table scans per investigation."""
    cases, lineages = benchmark_dataset

    flat_adapter = FlatRetrievalAdapter()
    flat_run = flat_adapter.run_suite(cases, lineages)

    # Mean retrieval operations per case is significantly higher
    assert flat_run.aggregate_metrics.mean_retrieval_operations >= 8.0
