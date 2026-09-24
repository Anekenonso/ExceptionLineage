"""Automated AST and ground-truth isolation test (Stage 18).

Verifies that production packages:
- app/agent/
- app/graph/
- app/investigations/
- app/api/
- app/validation/
- app/models/

strictly contain NO imports or dependencies on evaluation ground truth,
test suites, or benchmark dataset files.
"""

from __future__ import annotations

import ast
from pathlib import Path


def get_production_dirs() -> list[Path]:
    """Return all production code package directories."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    assert app_dir.exists(), f"app directory not found at {app_dir}"

    subdirs = [
        app_dir / "agent",
        app_dir / "graph",
        app_dir / "investigations",
        app_dir / "api",
        app_dir / "validation",
        app_dir / "models",
    ]
    return [d for d in subdirs if d.exists()]


def test_production_code_ast_imports_isolated():
    """Verify that AST walks of all production code find zero imports of ground truth or test modules."""
    prod_dirs = get_production_dirs()
    assert len(prod_dirs) >= 4, "Expected at least 4 production directories"

    forbidden_import_substrings = [
        "ground_truth",
        "tests",
        "test_",
        "evaluation",
        "data.cases",
        "data.ground_truth",
    ]

    checked_files_count = 0
    for prod_dir in prod_dirs:
        for py_file in prod_dir.rglob("*.py"):
            checked_files_count += 1
            code = py_file.read_text(encoding="utf-8")
            tree = ast.parse(code, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_import_substrings:
                            assert forbidden not in alias.name, (
                                f"Ground-truth leakage: prohibited import '{alias.name}' "
                                f"found in production file: {py_file}"
                            )
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for forbidden in forbidden_import_substrings:
                        assert forbidden not in mod, (
                            f"Ground-truth leakage: prohibited from-import '{mod}' "
                            f"found in production file: {py_file}"
                        )

    assert checked_files_count >= 15, f"Expected to check at least 15 production files, checked {checked_files_count}"


def test_production_code_contains_no_hardcoded_benchmark_references():
    """Verify production code does not reference ground_truth.json or hardcoded CASE- identifiers."""
    prod_dirs = get_production_dirs()

    for prod_dir in prod_dirs:
        for py_file in prod_dir.rglob("*.py"):
            if py_file.name == "verifier.py":
                continue  # GraphGroundTruthVerifier is a Stage 12 DB state verification helper
            content = py_file.read_text(encoding="utf-8")
            assert "ground_truth.json" not in content, (
                f"Prohibited reference to 'ground_truth.json' found in production file: {py_file}"
            )
            assert "CASE-" not in content, (
                f"Prohibited reference to benchmark case ID 'CASE-' found in production file: {py_file}"
            )
