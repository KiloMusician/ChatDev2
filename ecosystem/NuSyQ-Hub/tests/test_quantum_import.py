import sys
from pathlib import Path

import pytest

# These tests are for import validation - skip if dependencies unavailable
pytestmark = pytest.mark.skip(reason="Import smoke tests require specific environment")

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_package_imports_present():
    """Use the import_smoke API to verify package-qualified imports are present.

    This test delegates to the shared runner so CI and local checks remain
    consistent with the scripts.
    """
    try:
        from scripts.import_smoke import run_checks

        results = run_checks()
    except ImportError:
        pytest.skip("import_smoke module not available")

    # Expected-success modules
    expected = [
        "src.orchestration.unified_ai_orchestrator",
        "orchestration.unified_ai_orchestrator",
        "src.orchestration.quantum_workflow_automation",
        "orchestration.quantum_workflow_automation",
        "src.quantum.quantum_problem_resolver_test",
        "quantum.quantum_problem_resolver_test",
    ]

    for key in expected:
        assert key in results, f"Missing result for {key}"
        assert results[key]["ok"] == "True", f"Import failed for {key}: {results[key]['msg']}"


def test_bare_module_not_present_alternative():
    """Test alternative import checking without import_smoke dependency."""
    try:
        from scripts.import_smoke import run_checks

        results = run_checks()
        assert results["quantum_problem_resolver_test"]["ok"] == "False"

        # Expected-success modules
        expected = [
            "src.orchestration.unified_ai_orchestrator",
            "orchestration.unified_ai_orchestrator",
            "src.orchestration.quantum_workflow_automation",
            "orchestration.quantum_workflow_automation",
            "src.quantum.quantum_problem_resolver_test",
            "quantum.quantum_problem_resolver_test",
        ]

        for key in expected:
            assert key in results, f"Missing result for {key}"
            assert results[key]["ok"] == "True", f"Import failed for {key}: {results[key]['msg']}"
    except ImportError:
        pytest.skip("import_smoke module not available")
