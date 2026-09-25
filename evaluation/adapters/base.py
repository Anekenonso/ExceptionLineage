"""Base interface for evaluation adapters (Stage 18)."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from evaluation.dataset import BenchmarkCase
from evaluation.metrics import classify_run_status, compute_aggregate_metrics, compute_evidence_recall
from evaluation.schemas import CaseResult, EvaluationRun


class BaseEvaluationAdapter(ABC):
    """Abstract evaluation adapter for running benchmark cases and reporting results."""

    def __init__(
        self,
        baseline_name: str,
        model_provider: str = "internal",
        model_name: str = "default",
        configuration: dict[str, Any] | None = None,
    ) -> None:
        self.baseline_name = baseline_name
        self.model_provider = model_provider
        self.model_name = model_name
        self.configuration = configuration or {}

    @abstractmethod
    def evaluate_case(
        self,
        case: BenchmarkCase,
        lineage_store: dict[str, dict[str, Any]],
    ) -> CaseResult:
        """Execute a single benchmark case and return structured CaseResult."""
        ...

    def run_suite(
        self,
        cases: list[BenchmarkCase],
        lineage_store: dict[str, dict[str, Any]],
        dataset_version: str = "benchmark-v1",
        git_commit: str | None = None,
    ) -> EvaluationRun:
        """Run all cases in the suite and compile an EvaluationRun."""
        run_id = f"eval-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        case_results: list[CaseResult] = []
        for case in cases:
            res = self.evaluate_case(case, lineage_store)
            case_results.append(res)

        aggregate = compute_aggregate_metrics(case_results)
        run_status, status_detail = classify_run_status(case_results, aggregate)

        return EvaluationRun(
            run_id=run_id,
            timestamp=timestamp,
            git_commit=git_commit,
            dataset_version=dataset_version,
            baseline_name=self.baseline_name,
            model_provider=self.model_provider,
            model_name=self.model_name,
            configuration=self.configuration,
            status=run_status,
            status_detail=status_detail,
            case_results=case_results,
            aggregate_metrics=aggregate,
        )
