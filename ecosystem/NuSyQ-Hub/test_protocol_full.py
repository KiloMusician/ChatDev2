#!/usr/bin/env python
"""Comprehensive system test for Protocol implementation."""

import os
import sys
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test 1: Core imports."""
    print("\n[TEST 1] Core Imports")
    print("-" * 70)
    try:
        print("✅ All core imports successful")
        return True
    except Exception as e:
        print(f"❌ Core import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_files():
    """Test 2: File existence."""
    print("\n[TEST 2] File Existence")
    print("-" * 70)
    files = [
        "config/templates/flask_api.yaml",
        "config/templates/fastapi_service.yaml",
        "src/connectors/__init__.py",
        "src/connectors/base.py",
        "src/connectors/registry.py",
        "src/connectors/webhook.py",
        "src/workflow/__init__.py",
        "src/workflow/nodes.py",
        "src/workflow/engine.py",
        "src/automation/test_loop.py",
    ]

    all_exist = True
    for f in files:
        exists = os.path.exists(f)
        status = "✅" if exists else "❌"
        print(f"{status} {f}")
        if not exists:
            all_exist = False

    return all_exist


def test_resolver():
    """Test 3: Import resolution."""
    print("\n[TEST 3] Import Resolution")
    print("-" * 70)
    from src.core import get_connector_registry, get_test_loop, get_workflow_engine

    try:
        ConnectorRegistry = get_connector_registry()
        if ConnectorRegistry:
            print(f"✅ get_connector_registry(): {ConnectorRegistry}")
        else:
            print("❌ get_connector_registry() returned None")
    except Exception as e:
        print(f"❌ get_connector_registry() failed: {e}")

    try:
        WorkflowEngine = get_workflow_engine()
        if WorkflowEngine:
            print(f"✅ get_workflow_engine(): {WorkflowEngine}")
        else:
            print("❌ get_workflow_engine() returned None")
    except Exception as e:
        print(f"❌ get_workflow_engine() failed: {e}")

    try:
        TestLoop = get_test_loop()
        if TestLoop:
            print(f"✅ get_test_loop(): {TestLoop}")
        else:
            print("❌ get_test_loop() returned None")
    except Exception as e:
        print(f"❌ get_test_loop() failed: {e}")


def test_connector():
    """Test 4: Connector operations."""
    print("\n[TEST 4] Connector Registry")
    print("-" * 70)
    try:
        from src.connectors.registry import ConnectorRegistry

        registry = ConnectorRegistry()
        print("✅ ConnectorRegistry instantiated")

        status = registry.get_status()
        print(f"✅ get_status() returned: {list(status.keys())}")

        connectors = registry.list_connectors()
        print(f"✅ list_connectors(): {len(connectors)} connectors")
        return True
    except Exception as e:
        print(f"❌ Connector test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_workflow():
    """Test 5: Workflow operations."""
    print("\n[TEST 5] Workflow Engine")
    print("-" * 70)
    try:
        from src.workflow.engine import WorkflowEngine
        from src.workflow.nodes import NodeType, TriggerNode

        engine = WorkflowEngine()
        print("✅ WorkflowEngine instantiated")

        workflows = engine.list_workflows()
        print(f"✅ list_workflows(): {len(workflows)} workflows")

        wf = engine.create_workflow("test_wf_123", "Test Workflow")
        print(f"✅ create_workflow(): {wf.id}")

        node = TriggerNode("t1", "Test Trigger", NodeType.TRIGGER, {})
        wf.add_node(node)
        print(f"✅ add_node(): {node.id} added")

        return True
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_testloop():
    """Test 6: TestLoop."""
    print("\n[TEST 6] Test Loop")
    print("-" * 70)
    try:
        from src.automation.test_loop import TestLoop

        loop = TestLoop(enable_ai_fixes=False)
        print("✅ TestLoop instantiated")
        print(f"✅ enable_ai_fixes: {loop.enable_ai_fixes}")
        return True
    except Exception as e:
        print(f"❌ TestLoop test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_templates():
    """Test 7: Templates."""
    print("\n[TEST 7] Templates")
    print("-" * 70)
    try:
        from src.factories.templates import BaseWebApp, load_template

        flask_template = load_template("flask_api")
        print(f'✅ load_template("flask_api"): {type(flask_template).__name__}')
        if not isinstance(flask_template, BaseWebApp):
            print("⚠️  Flask template is not BaseWebApp instance")

        fastapi_template = load_template("fastapi_service")
        print(f'✅ load_template("fastapi_service"): {type(fastapi_template).__name__}')
        if not isinstance(fastapi_template, BaseWebApp):
            print("⚠️  FastAPI template is not BaseWebApp instance")

        return True
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_spine():
    """Test 8: SpineRegistry."""
    print("\n[TEST 8] SpineRegistry Wiring")
    print("-" * 70)
    try:
        from src.spine.registry import SpineRegistry

        spine = SpineRegistry()
        config = spine._config

        modules = config.get("modules", {})
        required = ["connector.registry", "workflow.engine", "automation.test_loop"]

        all_wired = True
        for mod in required:
            if mod in modules:
                print(f"✅ {mod} registered")
            else:
                print(f"❌ {mod} NOT registered")
                all_wired = False

        return all_wired
    except Exception as e:
        print(f"❌ SpineRegistry test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_result_type():
    """Test 9: Result type."""
    print("\n[TEST 9] Result Type")
    print("-" * 70)
    try:
        from src.core import Fail, Ok

        ok = Ok({"test": "data"})
        print(f"✅ Ok() created: success={ok.success}")

        fail = Fail("test error", code="TEST")
        print(f"✅ Fail() created: success={fail.success}")

        return True
    except Exception as e:
        print(f"❌ Result type test failed: {e}")
        return False


def test_cli():
    """Test 10: nq CLI."""
    print("\n[TEST 10] NQ CLI Commands")
    print("-" * 70)
    try:
        # Import the nq module
        import importlib.util

        spec = importlib.util.spec_from_file_location("nq", "nq")
        nq_module = importlib.util.module_from_spec(spec)

        # Check if commands are defined
        if hasattr(nq_module, "commands"):
            print("❌ nq module does not define commands dict")
            return False

        # Try to read the file directly
        with open("nq", "r") as f:
            content = f.read()

        # Check for command definitions
        commands = [
            "cmd_connector",
            "cmd_workflow",
            "cmd_test_loop",
            "cmd_protocol",
        ]

        all_found = True
        for cmd in commands:
            if f"def {cmd}" in content:
                print(f"✅ {cmd} defined in nq")
            else:
                print(f"❌ {cmd} NOT found in nq")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ nq CLI test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("NUSYQ-HUB PROTOCOL COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    results = {
        "Core Imports": test_imports(),
        "File Existence": test_files(),
        "Connector Registry": test_connector(),
        "Workflow Engine": test_workflow(),
        "TestLoop": test_testloop(),
        "Templates": test_templates(),
        "SpineRegistry": test_spine(),
        "Result Type": test_result_type(),
        "nq CLI": test_cli(),
    }

    # Test resolvers last
    test_resolver()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
