#!/usr/bin/env python
"""Validate the Agent Check/Patch/Wire Protocol implementation.

Phase 10 final validation checklist.
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_file_exists(path, description):
    """Check if a file exists."""
    p = Path(path)
    exists = p.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def check_import(module_path, class_name):
    """Check if an import works."""
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name, None)
        status = "✅" if cls else "❌"
        print(f"{status} {class_name}: {module_path}")
        return cls is not None
    except Exception as e:
        print(f"❌ {class_name}: {module_path} - {e}")
        return False


def check_cli_command(args, expected_markers, timeout=240):
    """Run an nq command and verify output markers."""
    repo_root = Path(__file__).parent
    nq_path = repo_root / "nq"
    command = [sys.executable, str(nq_path), *args]
    cmd_display = " ".join(["nq", *args])

    try:
        proc = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as e:
        print(f"❌ {cmd_display}: failed to execute - {e}")
        return False

    output = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 0:
        print(f"❌ {cmd_display}: exited with {proc.returncode}")
        return False

    missing = [marker for marker in expected_markers if marker not in output]
    if missing:
        print(f"❌ {cmd_display}: missing output markers {missing}")
        return False

    print(f"✅ {cmd_display}")
    return True


def main():
    """Run full validation."""
    print_header("PHASE 10: FINAL VALIDATION")

    all_passed = True

    # Check files were created
    print_header("File Creation Checks")
    files_to_check = [
        ("config/templates/flask_api.yaml", "Flask API template"),
        ("config/templates/fastapi_service.yaml", "FastAPI template"),
        ("src/connectors/__init__.py", "Connector package"),
        ("src/connectors/base.py", "Base connector"),
        ("src/connectors/registry.py", "Connector registry"),
        ("src/connectors/webhook.py", "Webhook connector"),
        ("src/workflow/__init__.py", "Workflow package"),
        ("src/workflow/nodes.py", "Workflow nodes"),
        ("src/workflow/engine.py", "Workflow engine"),
        ("src/automation/test_loop.py", "Test loop"),
        ("tests/test_protocol_integration.py", "Integration tests"),
        ("tests/test_nq_cli_protocol.py", "CLI protocol tests"),
    ]

    for path, desc in files_to_check:
        all_passed &= check_file_exists(path, desc)

    # Check imports
    print_header("Import Resolution Checks")
    imports_to_check = [
        ("src.core", "get_connector_registry"),
        ("src.core", "get_workflow_engine"),
        ("src.core", "get_test_loop"),
        ("src.connectors.base", "BaseConnector"),
        ("src.connectors.registry", "ConnectorRegistry"),
        ("src.connectors.webhook", "WebhookConnector"),
        ("src.workflow.nodes", "WorkflowNode"),
        ("src.workflow.nodes", "TriggerNode"),
        ("src.workflow.nodes", "ActionNode"),
        ("src.workflow.nodes", "OutputNode"),
        ("src.workflow.engine", "WorkflowEngine"),
        ("src.automation.test_loop", "TestLoop"),
    ]

    for module, cls in imports_to_check:
        all_passed &= check_import(module, cls)

    # Check CLI commands by executing real surfaces
    print_header("CLI Command Runtime Checks")
    cli_checks = [
        (["connector", "list"], ["Registered Connectors", "Total:"]),
        (["workflow", "list"], ["Workflows"]),
        (
            ["test-loop", "tests/test_protocol_integration.py", "-n", "1", "--no-ai", "--dry-run"],
            ["Dry run: test loop execution skipped"],
        ),
        (
            ["protocol", "status", "--quick"],
            ["Protocol Status", "Quick mode enabled", "Protocol status: healthy"],
        ),
    ]
    for args, markers in cli_checks:
        all_passed &= check_cli_command(args, markers)

    # Check SpineRegistry
    print_header("SpineRegistry Wiring Checks")
    try:
        from src.spine.registry import SpineRegistry

        spine = SpineRegistry()
        config = spine._config
        modules = config.get("modules", {})

        required_modules = ["connector.registry", "workflow.engine", "automation.test_loop"]

        for module_name in required_modules:
            exists = module_name in modules
            status = "✅" if exists else "❌"
            print(f"{status} {module_name} in SpineRegistry")
            all_passed &= exists
    except Exception as e:
        print(f"❌ SpineRegistry check failed: {e}")
        all_passed = False

    # Check Result type usage
    print_header("Result Type Compatibility")
    try:
        from src.core import Fail, Ok

        ok_result = Ok({"test": "data"})
        fail_result = Fail("test error", code="TEST")
        print(f"✅ Ok() type works: {ok_result.success}")
        print(f"✅ Fail() type works: {fail_result.success}")
    except Exception as e:
        print(f"❌ Result type check failed: {e}")
        all_passed = False

    # Summary
    print_header("VALIDATION SUMMARY")
    if all_passed:
        print("✅ ALL CHECKS PASSED - Protocol implementation complete!")
        print("\nYou can now use these commands:")
        print("  nq connector list       - List connectors")
        print("  nq workflow list        - List workflows")
        print("  nq test-loop <target>   - Run test loop")
        print("  nq protocol status      - Check protocol health")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - See above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
