#!/usr/bin/env python3
"""Bootstrap and activate the complete EOL (Epistemic-Operational Lattice) system.

This script:
1. Validates all Phase 1 modules are importable
2. Tests EOL facade access via nusyq.eol
3. Runs advanced workflows demo
4. Generates activation report

Run: python scripts/bootstrap_eol_system.py
"""

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Make src/ importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_phase1_modules() -> dict:
    """Verify all Phase 1 modules import correctly."""
    print("\n" + "=" * 70)
    print("PHASE 1: MODULE IMPORTS")
    print("=" * 70)

    modules = {
        "build_world_state": "src.core.build_world_state",
        "plan_from_world_state": "src.core.plan_from_world_state",
        "action_receipt_ledger": "src.core.action_receipt_ledger",
        "eol_integration": "src.core.eol_integration",
        "quest_receipt_linkage": "src.core.quest_receipt_linkage",
        "eol_facade": "src.core.eol_facade_integration",
        "orchestrate": "src.core.orchestrate",
        "eol_actions": "scripts.nusyq_actions.eol",
        "advanced_workflows": "src.advanced_workflows.orchestrator",
    }

    results = {}
    for name, module_path in modules.items():
        try:
            __import__(module_path)
            print(f"  ✓ {name:25} → {module_path}")
            results[name] = {"status": "ok", "module": module_path}
        except Exception as e:
            print(f"  ✗ {name:25} → {module_path}")
            print(f"    Error: {str(e)[:80]}")
            results[name] = {"status": "failed", "module": module_path, "error": str(e)}

    success = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)
    print(f"\nModules: {success}/{total} imported successfully")

    return results


def check_eol_facade() -> dict:
    """Verify EOL facade is accessible."""
    print("\n" + "=" * 70)
    print("PHASE 2: EOL FACADE ACCESS")
    print("=" * 70)

    results = {}

    try:
        from src.core.orchestrate import nusyq

        print("  ✓ nusyq facade imported")
        results["facade_import"] = {"status": "ok"}

        # Check eol property
        if hasattr(nusyq, "eol"):
            print("  ✓ nusyq.eol property exists")
            results["eol_property"] = {"status": "ok"}

            # List eol methods
            eol = nusyq.eol
            methods = [m for m in dir(eol) if not m.startswith("_")]
            print(f"  ✓ EOL methods available: {', '.join(methods[:5])}...")
            results["eol_methods"] = {"status": "ok", "count": len(methods), "methods": methods}
        else:
            print("  ✗ nusyq.eol property NOT found")
            results["eol_property"] = {"status": "failed", "error": "eol property missing"}

    except Exception as e:
        print(f"  ✗ Failed to access EOL facade: {str(e)[:100]}")
        results["facade_access"] = {"status": "failed", "error": str(e)}

    return results


def check_eol_commands() -> dict:
    """Verify EOL CLI commands are available."""
    print("\n" + "=" * 70)
    print("PHASE 3: EOL CLI COMMANDS")
    print("=" * 70)

    results = {}

    try:
        from scripts.nusyq_actions.eol import (
            handle_eol_command,
            handle_eol_debug,
            handle_eol_full_cycle,
            handle_eol_propose,
            handle_eol_sense,
            handle_eol_stats,
        )

        handlers = [
            ("handle_eol_command", handle_eol_command),
            ("handle_eol_sense", handle_eol_sense),
            ("handle_eol_propose", handle_eol_propose),
            ("handle_eol_full_cycle", handle_eol_full_cycle),
            ("handle_eol_stats", handle_eol_stats),
            ("handle_eol_debug", handle_eol_debug),
        ]

        for name, handler in handlers:
            if callable(handler):
                print(f"  ✓ {name} available")
                results[name] = {"status": "ok", "callable": True}
            else:
                print(f"  ✗ {name} not callable")
                results[name] = {"status": "failed", "callable": False}

    except Exception as e:
        print(f"  ✗ Failed to import EOL handlers: {str(e)[:100]}")
        results["handlers_import"] = {"status": "failed", "error": str(e)}

    return results


def check_advanced_workflows() -> dict:
    """Verify advanced workflows system."""
    print("\n" + "=" * 70)
    print("PHASE 4: ADVANCED WORKFLOWS SYSTEM")
    print("=" * 70)

    results = {}

    try:
        from src.advanced_workflows.orchestrator import (
            AdvancedWorkflowOrchestrator,
            CapabilityEscalator,
            ExploitChainer,
            OptimizationGoal,
            ParallelConsensus,
            ParallelRecognaissance,
        )

        components = [
            ("AdvancedWorkflowOrchestrator", AdvancedWorkflowOrchestrator),
            ("ParallelRecognaissance", ParallelRecognaissance),
            ("CapabilityEscalator", CapabilityEscalator),
            ("ExploitChainer", ExploitChainer),
            ("ParallelConsensus", ParallelConsensus),
            ("OptimizationGoal", OptimizationGoal),
        ]

        for name, component in components:
            if component:
                print(f"  ✓ {name} available")
                results[name] = {"status": "ok"}
            else:
                print(f"  ✗ {name} not found")
                results[name] = {"status": "failed"}

        # Try instantiating orchestrator
        try:
            _orchestrator = AdvancedWorkflowOrchestrator()  # Instantiation test only
            print("  ✓ AdvancedWorkflowOrchestrator instantiated")
            results["orchestrator_instantiation"] = {"status": "ok"}
        except Exception as e:
            print(f"  ⚠ Could not instantiate orchestrator: {str(e)[:80]}")
            results["orchestrator_instantiation"] = {"status": "warning", "error": str(e)}

    except Exception as e:
        print(f"  ✗ Failed to import advanced workflows: {str(e)[:100]}")
        results["imports"] = {"status": "failed", "error": str(e)}

    return results


def test_eol_sense() -> dict:
    """Test the EOL sense() method."""
    print("\n" + "=" * 70)
    print("PHASE 5: EOL SENSE TEST")
    print("=" * 70)

    results = {}

    try:
        from src.core.orchestrate import nusyq

        print("  Calling nusyq.eol.sense()...")
        result = nusyq.eol.sense()

        if result.ok:
            world_state = result.value
            print("  ✓ sense() succeeded")
            print(f"    - Epoch: {world_state.get('decision_epoch')}")
            print(f"    - Signals: {len(world_state.get('signals', {}).get('facts', []))}")
            print(f"    - Timestamp: {world_state.get('timestamp')}")
            results["sense_call"] = {"status": "ok", "epoch": world_state.get("decision_epoch")}
        else:
            print(f"  ✗ sense() failed: {result.error}")
            results["sense_call"] = {"status": "failed", "error": result.error}

    except Exception as e:
        print(f"  ✗ Exception during sense(): {str(e)[:100]}")
        results["sense_exception"] = {
            "status": "failed",
            "error": str(e),
            "trace": traceback.format_exc(),
        }

    return results


def generate_activation_report(checks: dict) -> None:
    """Generate and display activation report."""
    print("\n" + "=" * 70)
    print("ACTIVATION REPORT")
    print("=" * 70)

    timestamp = datetime.now().isoformat()

    all_ok = all(
        check.get("status") == "ok"
        for results in checks.values()
        for check in (results.values() if isinstance(results, dict) else [])
        if isinstance(check, dict) and "status" in check
    )

    status = "🟢 FULLY ACTIVATED" if all_ok else "🟡 PARTIALLY ACTIVATED"
    print(f"\nStatus: {status}")
    print(f"Timestamp: {timestamp}")

    # Summary table
    print("\nPhase Summary:")
    phase_names = {
        "phase1": "Module Imports",
        "phase2": "EOL Facade",
        "phase3": "CLI Commands",
        "phase4": "Advanced Workflows",
        "phase5": "EOL Sense Test",
    }

    for phase_key, phase_name in phase_names.items():
        if phase_key not in checks:
            continue

        phase_results = checks[phase_key]
        if isinstance(phase_results, dict):
            ok_count = sum(1 for r in phase_results.values() if isinstance(r, dict) and r.get("status") == "ok")
            total_count = sum(1 for r in phase_results.values() if isinstance(r, dict) and "status" in r)
            if total_count > 0:
                print(f"  {phase_name:30} {ok_count}/{total_count}")

    # Save report to file
    report_file = PROJECT_ROOT / "state" / "bootstrap_activation_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "timestamp": timestamp,
        "status": status,
        "checks": checks,
    }

    report_file.write_text(json.dumps(report_data, indent=2, default=str))
    print(f"\nReport saved to: {report_file}")


def main():
    """Run full bootstrap sequence."""
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  EOL (Epistemic-Operational Lattice) System Bootstrap".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    checks = {}

    # Run all checks
    checks["phase1"] = check_phase1_modules()
    checks["phase2"] = check_eol_facade()
    checks["phase3"] = check_eol_commands()
    checks["phase4"] = check_advanced_workflows()
    checks["phase5"] = test_eol_sense()

    # Generate report
    generate_activation_report(checks)

    # Final status
    all_critical_ok = (
        checks.get("phase1", {}).get("orchestrate", {}).get("status") == "ok"
        and checks.get("phase2", {}).get("eol_property", {}).get("status") == "ok"
        and checks.get("phase3", {}).get("handle_eol_command", {}).get("status") == "ok"
    )

    print("\n" + "=" * 70)
    if all_critical_ok:
        print("\n✅ BOOTSTRAP COMPLETE: System is ready for use")
        print("\nNext steps:")
        print("  1. python scripts/start_nusyq.py eol sense")
        print("  2. python scripts/start_nusyq.py eol propose 'Your objective'")
        print("  3. python -m src.advanced_workflows.orchestrator --demo")
        print("  4. pytest tests/integration/test_eol_e2e.py -v")
        return 0
    else:
        print("\n⚠️  BOOTSTRAP PARTIAL: Some components need attention")
        print("\nReview report at: state/bootstrap_activation_report.json")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
