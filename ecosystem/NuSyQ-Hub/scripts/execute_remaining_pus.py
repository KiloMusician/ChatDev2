"""Execute Remaining PUs (PU-TODO-001, PU-CONFIG-001, PU-IMPL-001)."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from src.integration.simulatedverse_unified_bridge import (
        SimulatedVerseUnifiedBridge as SimulatedVerseBridge,
    )
except ImportError:
    SimulatedVerseBridge = None

DEFAULT_TIMEOUT = 30


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for PU execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="output_json", help="Emit raw PU results as JSON")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Per-agent timeout in seconds")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be >= 1")
    return args


def execute_pu_todo_001(timeout: int = DEFAULT_TIMEOUT):
    """PU-TODO-001: Convert TODOs to GitHub issues."""
    if not SimulatedVerseBridge:
        return {"error": "Bridge not available"}

    bridge = SimulatedVerseBridge()
    results = {}

    pu_data = {
        "id": "PU-TODO-001",
        "type": "DocPU",
        "title": "Convert 560 TODO comments to tracked GitHub issues",
        "todo_count": 560,
        "repository": "NuSyQ-Hub",
    }

    # Librarian: Extract and document TODOs
    task_id = bridge.submit_task(
        "librarian",
        "Extract TODO comments and create documentation",
        {"pu": pu_data, "action": "document_todos"},
    )
    results["librarian"] = bridge.check_result(task_id, timeout=timeout)

    # Party: Orchestrate TODO conversion workflow
    task_id = bridge.submit_task(
        "party",
        "Orchestrate TODO to GitHub issue conversion",
        {"pu": pu_data, "action": "coordinate_conversion"},
    )
    results["party"] = bridge.check_result(task_id, timeout=timeout)

    # Council: Vote on TODO prioritization
    task_id = bridge.submit_task(
        "council",
        "Vote on TODO priority for issue creation",
        {"pu": pu_data, "action": "prioritize_todos"},
    )
    results["council"] = bridge.check_result(task_id, timeout=timeout)

    return results


def execute_pu_config_001(timeout: int = DEFAULT_TIMEOUT):
    """PU-CONFIG-001: Create missing pytest.ini."""
    if not SimulatedVerseBridge:
        return {"error": "Bridge not available"}

    bridge = SimulatedVerseBridge()
    results = {}

    pu_data = {
        "id": "PU-CONFIG-001",
        "type": "SetupPU",
        "title": "Create missing configuration file: pytest.ini",
        "missing_files": ["pytest.ini"],
        "repository": "NuSyQ-Hub",
    }

    # Artificer: Create configuration artifact
    task_id = bridge.submit_task(
        "artificer",
        "Create pytest.ini configuration template",
        {"pu": pu_data, "action": "create_config"},
    )
    results["artificer"] = bridge.check_result(task_id, timeout=timeout)

    # Librarian: Document configuration
    task_id = bridge.submit_task(
        "librarian",
        "Document pytest.ini configuration options",
        {"pu": pu_data, "action": "document_config"},
    )
    results["librarian"] = bridge.check_result(task_id, timeout=timeout)

    # Zod: Validate configuration schema
    task_id = bridge.submit_task(
        "zod",
        "Validate pytest.ini configuration structure",
        {"pu": pu_data, "action": "validate_config"},
    )
    results["zod"] = bridge.check_result(task_id, timeout=timeout)

    return results


def execute_pu_impl_001(timeout: int = DEFAULT_TIMEOUT):
    """PU-IMPL-001: Complete incomplete modules."""
    if not SimulatedVerseBridge:
        return {"error": "Bridge not available"}

    bridge = SimulatedVerseBridge()
    results = {}

    pu_data = {
        "id": "PU-IMPL-001",
        "type": "ImplementationPU",
        "title": "Complete 5 partially implemented modules",
        "incomplete_count": 5,
        "repository": "NuSyQ-Hub",
    }

    # Alchemist: Transform incomplete code
    task_id = bridge.submit_task(
        "alchemist",
        "Transform incomplete code to full implementations",
        {"pu": pu_data, "action": "complete_implementations"},
    )
    results["alchemist"] = bridge.check_result(task_id, timeout=timeout)

    # Zod: Validate implementations
    task_id = bridge.submit_task(
        "zod",
        "Validate implementation completeness and types",
        {"pu": pu_data, "action": "validate_implementations"},
    )
    results["zod"] = bridge.check_result(task_id, timeout=timeout)

    # Redstone: Analyze logic
    task_id = bridge.submit_task(
        "redstone",
        "Analyze logic patterns in implementations",
        {"pu": pu_data, "action": "analyze_logic"},
    )
    results["redstone"] = bridge.check_result(task_id, timeout=timeout)

    # Librarian: Document implementations
    task_id = bridge.submit_task(
        "librarian",
        "Create documentation for completed modules",
        {"pu": pu_data, "action": "document_implementations"},
    )
    results["librarian"] = bridge.check_result(task_id, timeout=timeout)

    return results


def _summarize_results(all_results: dict[str, dict]) -> tuple[list[str], bool]:
    """Build human-readable summary lines and success signal."""
    lines: list[str] = ["", "=== PU Execution Summary ==="]
    has_errors = False

    for pu_id, results in all_results.items():
        if "error" in results:
            lines.append(f"{pu_id}: ❌ {results['error']}")
            has_errors = True
            continue

        success_count = sum(1 for result in results.values() if result is not None)
        total_count = len(results)
        lines.append(f"{pu_id}: {success_count}/{total_count} agents returned responses")
        for agent, result in results.items():
            status = "✅" if result is not None else "⏱️"
            if result is None:
                has_errors = True
            lines.append(f"  {status} {agent}")

    return lines, not has_errors


def main(argv: Sequence[str] | None = None) -> int:
    """Execute all remaining PUs and print a terminal summary."""
    args = _parse_args(argv)

    all_results: dict[str, dict] = {}

    # Execute each PU
    all_results["PU-TODO-001"] = execute_pu_todo_001(timeout=args.timeout)
    all_results["PU-CONFIG-001"] = execute_pu_config_001(timeout=args.timeout)
    all_results["PU-IMPL-001"] = execute_pu_impl_001(timeout=args.timeout)

    summary_lines, success = _summarize_results(all_results)
    print("\n".join(summary_lines))

    if args.output_json:
        print(json.dumps(all_results, indent=2, default=str))

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
