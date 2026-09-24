"""Executable evaluation runner for ExceptionLineage (Stage 18).

Usage:
    python evaluation/runner.py
    python evaluation/runner.py --baseline deterministic
    python evaluation/runner.py --baseline heuristic
    python evaluation/runner.py --mock-llm
    python evaluation/runner.py --with-llm
    python evaluation/runner.py --dataset extended

Produces:
    evaluation/reports/latest.json
    evaluation/reports/latest.md
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root and apps/api to sys.path so modules resolve anywhere
repo_root = Path(__file__).resolve().parent.parent
api_dir = repo_root / "apps" / "api"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from evaluation.adapters.deterministic import DeterministicValidationAdapter
from evaluation.adapters.heuristic import HeuristicAgentAdapter
from evaluation.adapters.llm import LLMDecisionAdapter
from evaluation.dataset import load_benchmark_cases, load_seed_lineages
from evaluation.reporter import generate_markdown_report, save_json_report, save_markdown_report
from evaluation.schemas import AggregateMetrics, EvaluationRun, EvaluationSuiteReport


def get_git_commit() -> str | None:
    """Safely obtain current git commit hash if available."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
        return out.decode("utf-8").strip()
    except Exception:
        return None


def run_evaluation(
    baseline: str = "all",
    dataset: str = "benchmark",
    with_llm: bool = False,
    mock_llm: bool = False,
    max_steps: int = 10,
    output_dir: Path | None = None,
) -> EvaluationSuiteReport:
    """Execute evaluation harness across selected baselines and write reports."""
    out_dir = output_dir or (repo_root / "evaluation" / "reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    git_commit = get_git_commit()
    suite_id = f"suite-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    dataset_version = f"{dataset}-v1"

    print("================================================================================")
    print(f"ExceptionLineage Stage 18 Quantitative Evaluation Harness")
    print(f"Suite ID: {suite_id}")
    print(f"Dataset:  {dataset_version}")
    print(f"Commit:   {git_commit or 'unknown'}")
    print("================================================================================\n")

    cases = load_benchmark_cases(dataset_name=dataset)
    lineages = load_seed_lineages()
    print(f"Loaded {len(cases)} benchmark cases from controlled dataset.\n")

    runs: dict[str, EvaluationRun] = {}

    # 1. Baseline A: Deterministic Validation Engine
    if baseline in ("all", "deterministic"):
        print("--> Running Baseline A: Deterministic Validation Engine...")
        det_adapter = DeterministicValidationAdapter()
        det_run = det_adapter.run_suite(
            cases=cases,
            lineage_store=lineages,
            dataset_version=dataset_version,
            git_commit=git_commit,
        )
        runs["deterministic_baseline"] = det_run
        acc = det_run.aggregate_metrics.accuracy * 100
        rec = det_run.aggregate_metrics.mean_evidence_recall * 100
        print(f"    Completed Baseline A: Accuracy {acc:.1f}%, Mean Recall {rec:.1f}%\n")

    # 2. Baseline B: HeuristicAgentModel
    if baseline in ("all", "heuristic"):
        print("--> Running Baseline B: HeuristicAgentModel...")
        heu_adapter = HeuristicAgentAdapter(max_steps=max_steps)
        heu_run = heu_adapter.run_suite(
            cases=cases,
            lineage_store=lineages,
            dataset_version=dataset_version,
            git_commit=git_commit,
        )
        runs["heuristic_baseline"] = heu_run
        acc = heu_run.aggregate_metrics.accuracy * 100
        rec = heu_run.aggregate_metrics.mean_evidence_recall * 100
        steps = heu_run.aggregate_metrics.mean_agent_steps
        calls = heu_run.aggregate_metrics.total_tool_calls
        print(f"    Completed Baseline B: Accuracy {acc:.1f}%, Mean Recall {rec:.1f}%, Mean Steps {steps}, Tool Calls {calls}\n")

    # 3. System Under Evaluation: LLMDecisionModel
    if baseline in ("all", "llm"):
        has_api_key = bool(os.getenv("AGENT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
        should_run_live = with_llm and has_api_key
        should_run_mock = mock_llm or (baseline == "llm" and not has_api_key and not with_llm)

        if should_run_live or mock_llm:
            mode_desc = "Live API" if should_run_live else "Controlled Mock"
            print(f"--> Running System Under Evaluation: LLMDecisionModel ({mode_desc})...")
            llm_adapter = LLMDecisionAdapter(
                max_steps=max_steps,
                is_mock=not should_run_live,
            )
            llm_run = llm_adapter.run_suite(
                cases=cases,
                lineage_store=lineages,
                dataset_version=dataset_version,
                git_commit=git_commit,
            )
            runs["llm_decision_model"] = llm_run
            acc = llm_run.aggregate_metrics.accuracy * 100
            rec = llm_run.aggregate_metrics.mean_evidence_recall * 100
            print(f"    Completed LLM Evaluation: Accuracy {acc:.1f}%, Mean Recall {rec:.1f}%\n")
        else:
            # Explicitly mark live LLM as skipped/unevaluated as required by specification
            print("--> System Under Evaluation: LLMDecisionModel [SKIPPED]")
            print("    Reason: Live LLM evaluation requires --with-llm flag and AGENT_LLM_API_KEY environment variable.")
            print("    (To run offline controlled LLM evaluation, use --mock-llm flag)\n")
            runs["llm_decision_model"] = EvaluationRun(
                run_id=f"eval-{uuid.uuid4().hex[:12]}",
                timestamp=now_iso,
                git_commit=git_commit,
                dataset_version=dataset_version,
                baseline_name="llm_decision_model",
                model_provider="unconfigured",
                model_name="none",
                status="SKIPPED",
                notes="Live LLM not evaluated in this run. Explicitly skipped to avoid external API dependency.",
                aggregate_metrics=AggregateMetrics(),
            )

    suite = EvaluationSuiteReport(
        suite_id=suite_id,
        timestamp=now_iso,
        git_commit=git_commit,
        dataset_version=dataset_version,
        runs=runs,
        summary={
            "total_baselines": len(runs),
            "completed_baselines": sum(1 for r in runs.values() if r.status == "COMPLETED"),
        },
    )

    # Save reports
    latest_json_path = out_dir / "latest.json"
    latest_md_path = out_dir / "latest.md"
    suite_json_path = out_dir / f"{suite_id}.json"

    save_json_report(suite, latest_json_path)
    save_json_report(suite, suite_json_path)

    md_content = generate_markdown_report(suite)
    save_markdown_report(md_content, latest_md_path)

    print("================================================================================")
    print("Evaluation Summary:")
    print("--------------------------------------------------------------------------------")
    print(f"Reports saved to:")
    print(f"  JSON:     {latest_json_path}")
    print(f"  Markdown: {latest_md_path}")
    print("================================================================================\n")

    return suite


def main() -> None:
    parser = argparse.ArgumentParser(description="ExceptionLineage Quantitative Evaluation Runner")
    parser.add_argument(
        "--baseline",
        choices=["all", "deterministic", "heuristic", "llm"],
        default="all",
        help="Which baseline to evaluate (default: all)",
    )
    parser.add_argument(
        "--dataset",
        choices=["benchmark", "extended"],
        default="benchmark",
        help="Dataset to evaluate (default: benchmark)",
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="Explicitly enable live LLM evaluation using AGENT_LLM_API_KEY",
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Evaluate LLMDecisionModel using deterministic mock client (no API key needed)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum agent steps per investigation (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save report files (default: evaluation/reports)",
    )

    args = parser.parse_args()

    run_evaluation(
        baseline=args.baseline,
        dataset=args.dataset,
        with_llm=args.with_llm,
        mock_llm=args.mock_llm,
        max_steps=args.max_steps,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
