"""Run a lightweight import-only smoke check for key dormant systems.

This script is intentionally minimal and avoids test frameworks so it can run
in environments that lack pytest or coverage plugins.
"""

import importlib
import sys
from pathlib import Path


def ensure_paths():
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    # Insert src first, then repo root
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def try_import(modname, symbol=None):
    try:
        mod = importlib.import_module(modname)
    except Exception as e:
        return False, f"Import {modname} failed: {e}"
    if symbol and not hasattr(mod, symbol):
        return False, f"Module {modname} imported but missing symbol {symbol}"
    return True, "OK"


def main():
    ensure_paths()

    checks = [
        ("src.orchestration.multi_ai_orchestrator", "MultiAIOrchestrator"),
        ("orchestration.multi_ai_orchestrator", "MultiAIOrchestrator"),
        ("src.orchestration.quantum_workflow_automation", "QuantumWorkflowAutomator"),
        ("orchestration.quantum_workflow_automation", "QuantumWorkflowAutomator"),
        ("src.quantum.quantum_problem_resolver_test", "QuantumState"),
        ("quantum.quantum_problem_resolver_test", "QuantumState"),
    ]

    all_ok = True
    for modname, symbol in checks:
        ok, msg = try_import(modname, symbol)
        print(f"{modname:<60} -> {msg}")
        if not ok:
            all_ok = False

    # Confirm bare legacy import does not silently exist (document current behavior)
    try:
        importlib.import_module("quantum_problem_resolver_test")
        print("quantum_problem_resolver_test (bare) -> unexpectedly importable")
        all_ok = False
    except ModuleNotFoundError:
        print("quantum_problem_resolver_test (bare) -> NotFound (expected)")

    if all_ok:
        print("\nSMOKE CHECK: PASS")
        return 0
    print("\nSMOKE CHECK: FAIL")
    return 2


if __name__ == "__main__":
    sys.exit(main())
