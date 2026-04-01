"""Modular import-smoke runner for NuSyQ-Hub.

Provides a programmatic API and small CLI for verifying importability of
candidate modules under common PYTHONPATH layouts. Designed to be reusable by
tests and CI.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

DEFAULT_CANDIDATES: list[tuple[str, str | None]] = [
    ("src.orchestration.unified_ai_orchestrator", "UnifiedAIOrchestrator"),
    ("orchestration.unified_ai_orchestrator", "UnifiedAIOrchestrator"),
    ("src.orchestration.quantum_workflow_automation", "QuantumWorkflowAutomator"),
    ("orchestration.quantum_workflow_automation", "QuantumWorkflowAutomator"),
    ("src.quantum.quantum_problem_resolver_test", "QuantumState"),
    ("quantum.quantum_problem_resolver_test", "QuantumState"),
]


def ensure_paths(repo_root: Path | None = None, add_src: bool = True) -> None:
    """Ensure repo_root and optional src path are on sys.path.

    Args:
        repo_root: path to repo root; defaults to two levels up from this file.
        add_src: whether to add repo_root/src to sys.path as well.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    src_path = str(repo_root / "src")
    nested_src = repo_root / "src" / "src"
    # Insert paths at front to mirror typical behavior
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    if add_src and src_path not in sys.path:
        # Avoid shadowing the top-level src package with a nested src/src path.
        if nested_src.exists():
            return
        sys.path.insert(0, src_path)


def try_import(modname: str, symbol: str | None = None) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(modname)
    except Exception as e:
        return False, f"Import {modname} failed: {e}"
    if symbol and not hasattr(mod, symbol):
        return False, f"Module {modname} imported but missing symbol {symbol}"
    return True, "OK"


def run_checks(
    candidates: list[tuple[str, str | None]] | None = None,
    repo_root: Path | None = None,
    add_src: bool = True,
) -> dict[str, dict[str, str]]:
    """Run import checks and return structured results.

    Returns a dictionary mapping module name -> {"ok": "True|False", "msg": str}
    """
    ensure_paths(repo_root=repo_root, add_src=add_src)
    if candidates is None:
        candidates = DEFAULT_CANDIDATES

    results: dict[str, dict[str, str]] = {}
    for modname, symbol in candidates:
        ok, msg = try_import(modname, symbol)
        results[modname] = {"ok": str(ok), "msg": msg}

    # Document the legacy bare module behavior
    try:
        importlib.import_module("quantum_problem_resolver_test")
        results["quantum_problem_resolver_test"] = {
            "ok": "True",
            "msg": "bare module importable (unexpected)",
        }
    except ModuleNotFoundError:
        results["quantum_problem_resolver_test"] = {
            "ok": "False",
            "msg": "NotFound (expected)",
        }

    return results


def main() -> int:
    """Small CLI entrypoint. Prints results and returns exit code.

    Exit codes: 0 success, 2 failure
    """
    results = run_checks()
    all_ok = True
    # Consider only the canonical candidate entries (DEFAULT_CANDIDATES) as
    # required for the smoke check. Legacy bare-module behavior is documented
    # but does not cause a failure.
    required_modules = [m for m, _ in DEFAULT_CANDIDATES if m.startswith("src.")]
    for mod, info in results.items():
        status = info["msg"]
        print(f"{mod:<60} -> {status}")
        if mod in required_modules and info["ok"] != "True":
            all_ok = False

    if all_ok:
        print("\nSMOKE CHECK: PASS")
        return 0
    print("\nSMOKE CHECK: FAIL")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
