#!/usr/bin/env python3
"""Quick Check Test Suite for NuSyQ-Hub.

Fast automated tests for critical paths. Designed to run in under 5 seconds.
Run with: python tests/quick_check.py

Tests:
- Core imports (Result, safe_import, nusyq facade)
- Result type operations
- safe_import functionality
- NuSyQ orchestrator facade
"""

import sys
import time
import unittest
from pathlib import Path

# Ensure the project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestCoreImports(unittest.TestCase):
    """Test that core module imports work correctly."""

    def test_result_imports(self):
        """Result, Ok, Fail should import from src.core."""
        from src.core import Fail, Ok, Result

        self.assertIsNotNone(Result)
        self.assertIsNotNone(Ok)
        self.assertIsNotNone(Fail)

    def test_import_utilities(self):
        """safe_import, lazy_import, import_status should import."""
        from src.core import import_status, lazy_import, safe_import

        self.assertIsNotNone(safe_import)
        self.assertIsNotNone(lazy_import)
        self.assertIsNotNone(import_status)

    def test_nusyq_facade_import(self):
        """Nusyq orchestrator facade should import."""
        from src.core import NuSyQOrchestrator, nusyq

        self.assertIsNotNone(nusyq)
        self.assertIsNotNone(NuSyQOrchestrator)
        self.assertIsInstance(nusyq, NuSyQOrchestrator)

    def test_bootstrap_imports(self):
        """Bootstrap utilities should import."""
        from src.core import SystemBootstrap, get_bootstrap, quick_boot

        self.assertIsNotNone(SystemBootstrap)
        self.assertIsNotNone(quick_boot)
        self.assertIsNotNone(get_bootstrap)

    def test_all_exports_present(self):
        """All __all__ exports should be accessible."""
        import src.core as core

        expected = [
            "Result",
            "Ok",
            "Fail",
            "safe_import",
            "lazy_import",
            "import_status",
            "get_smart_search",
            "get_quest_engine",
            "get_ai_council",
            "get_background_orchestrator",
            "get_ai_intermediary",
            "get_chatdev_router",
            "SystemBootstrap",
            "quick_boot",
            "get_bootstrap",
            "nusyq",
            "NuSyQOrchestrator",
        ]
        for name in expected:
            self.assertTrue(hasattr(core, name), f"Missing export: {name}")


class TestResultType(unittest.TestCase):
    """Test the Result type functionality."""

    def test_result_ok_creation(self):
        """Result.ok should create a successful result."""
        from src.core import Result

        result = Result.ok(data={"key": "value"}, message="Success")
        self.assertTrue(result.success)
        self.assertEqual(result.data, {"key": "value"})
        self.assertEqual(result.message, "Success")
        self.assertIsNone(result.error)

    def test_result_fail_creation(self):
        """Result.fail should create a failed result."""
        from src.core import Result

        result = Result.fail("Something went wrong", code="ERR_001")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Something went wrong")
        self.assertEqual(result.code, "ERR_001")

    def test_ok_alias(self):
        """Ok() should be an alias for Result.ok()."""
        from src.core import Ok

        result = Ok(data="test data")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "test data")

    def test_fail_alias(self):
        """Fail() should be an alias for Result.fail()."""
        from src.core import Fail

        result = Fail("Error message", code="TEST")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Error message")

    def test_result_bool_context(self):
        """Result should work in boolean context."""
        from src.core import Fail, Ok

        self.assertTrue(bool(Ok(data="success")))
        self.assertFalse(bool(Fail("error")))

    def test_result_unwrap_success(self):
        """unwrap() should return data on success."""
        from src.core import Ok

        result = Ok(data=42)
        self.assertEqual(result.unwrap(), 42)

    def test_result_unwrap_failure(self):
        """unwrap() should raise on failure."""
        from src.core import Fail

        result = Fail("error")
        with self.assertRaises(ValueError):
            result.unwrap()

    def test_result_unwrap_or(self):
        """unwrap_or() should return default on failure."""
        from src.core import Fail, Ok

        self.assertEqual(Ok(data=10).unwrap_or(0), 10)
        self.assertEqual(Fail("error").unwrap_or(0), 0)

    def test_result_to_dict(self):
        """to_dict() should serialize the result."""
        from src.core import Ok

        result = Ok(data={"test": True}, message="Done")
        d = result.to_dict()

        self.assertIn("success", d)
        self.assertIn("timestamp", d)
        self.assertTrue(d["success"])
        self.assertEqual(d["data"], {"test": True})

    def test_result_meta(self):
        """Result should support additional metadata."""
        from src.core import Ok

        result = Ok(data="test", extra="info", count=5)
        self.assertEqual(result.meta["extra"], "info")
        self.assertEqual(result.meta["count"], 5)


class TestSafeImport(unittest.TestCase):
    """Test the safe_import functionality."""

    def test_safe_import_existing_module(self):
        """safe_import should load existing modules."""
        from src.core import safe_import

        # Import something from stdlib that definitely exists
        Path = safe_import("pathlib", "Path")
        self.assertIsNotNone(Path)
        self.assertEqual(Path.__name__, "Path")

    def test_safe_import_nonexistent_returns_none(self):
        """safe_import should return None for missing modules."""
        from src.core import safe_import

        result = safe_import("nonexistent_module_xyz", "SomeClass")
        self.assertIsNone(result)

    def test_safe_import_with_fallback(self):
        """safe_import should use fallback when module not found."""
        from src.core import safe_import

        class MockClass:
            pass

        result = safe_import("nonexistent_module", "Thing", fallback=MockClass)
        self.assertIs(result, MockClass)

    def test_safe_import_alternatives(self):
        """safe_import should try alternative paths."""
        from src.core import safe_import

        # Try a nonexistent first, then a real one
        Path = safe_import("nonexistent.pathlib", "Path", alternatives=["pathlib"])
        self.assertIsNotNone(Path)

    def test_safe_import_required_raises(self):
        """safe_import with required=True should raise on failure."""
        from src.core import safe_import

        with self.assertRaises(ImportError):
            safe_import("nonexistent_xyz", "Thing", required=True)

    def test_import_status(self):
        """import_status should return tracking info."""
        from src.core import import_status

        status = import_status()
        self.assertIn("total_attempts", status)
        self.assertIn("successful", status)
        self.assertIn("failed", status)
        self.assertIn("details", status)


class TestLazyImport(unittest.TestCase):
    """Test lazy_import functionality."""

    def test_lazy_import_returns_callable(self):
        """lazy_import should return a callable."""
        from src.core import lazy_import

        get_path = lazy_import("pathlib", "Path")
        self.assertTrue(callable(get_path))

    def test_lazy_import_loads_on_call(self):
        """lazy_import callable should load the module when called."""
        from src.core import lazy_import

        get_path = lazy_import("pathlib", "Path")
        Path = get_path()
        self.assertIsNotNone(Path)
        self.assertEqual(Path.__name__, "Path")

    def test_lazy_import_caches_result(self):
        """lazy_import should cache the loaded module."""
        from src.core import lazy_import

        get_path = lazy_import("pathlib", "Path")
        first_call = get_path()
        second_call = get_path()
        self.assertIs(first_call, second_call)


class TestNuSyQFacade(unittest.TestCase):
    """Test the nusyq orchestrator facade."""

    def test_nusyq_singleton(self):
        """Nusyq should be a singleton instance."""
        from src.core import NuSyQOrchestrator, nusyq
        from src.core.orchestrate import nusyq as nusyq2

        self.assertIs(nusyq, nusyq2)
        self.assertIsInstance(nusyq, NuSyQOrchestrator)

    def test_nusyq_has_facades(self):
        """Nusyq should have search, quest, council, background facades."""
        from src.core import nusyq

        self.assertTrue(hasattr(nusyq, "search"))
        self.assertTrue(hasattr(nusyq, "quest"))
        self.assertTrue(hasattr(nusyq, "council"))
        self.assertTrue(hasattr(nusyq, "background"))

    def test_nusyq_facades_lazy_load(self):
        """Facades should be lazily initialized."""
        from src.core.orchestrate import NuSyQOrchestrator

        # Create fresh instance
        orch = NuSyQOrchestrator()

        # Private attributes should be None before access
        self.assertIsNone(orch._search)
        self.assertIsNone(orch._quest)

        # Access should initialize
        _ = orch.search
        self.assertIsNotNone(orch._search)

    def test_nusyq_status_returns_result(self):
        """nusyq.status() should return a Result."""
        from src.core import Result, nusyq

        status = nusyq.status()
        self.assertIsInstance(status, Result)

    def test_search_facade_find_returns_result(self):
        """search.find() should return a Result type."""
        from src.core import Result, nusyq

        result = nusyq.search.find("test query")
        self.assertIsInstance(result, Result)


class TestBootstrap(unittest.TestCase):
    """Test the bootstrap system."""

    def test_system_bootstrap_creation(self):
        """SystemBootstrap should be instantiable."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap(name="TestSystem")
        self.assertEqual(bootstrap.name, "TestSystem")
        self.assertEqual(len(bootstrap.components), 0)

    def test_register_component(self):
        """Components should be registerable."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap()
        bootstrap.register("TestComp", lambda: "initialized")

        self.assertIn("TestComp", bootstrap.components)
        self.assertEqual(bootstrap.components["TestComp"].status, "pending")

    def test_register_chaining(self):
        """register() should support chaining."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap()
        result = bootstrap.register("A", lambda: 1).register("B", lambda: 2)

        self.assertIs(result, bootstrap)
        self.assertIn("A", bootstrap.components)
        self.assertIn("B", bootstrap.components)

    def test_boot_initializes_components(self):
        """boot() should initialize all enabled components."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap()
        bootstrap.register("Simple", lambda: {"ready": True})

        result = bootstrap.boot()

        self.assertTrue(result.success)
        self.assertEqual(result.systems_ready, 1)
        self.assertEqual(bootstrap.components["Simple"].status, "ready")

    def test_boot_handles_failures(self):
        """boot() should handle component failures gracefully."""
        from src.core import SystemBootstrap

        def fail_init():
            raise RuntimeError("Intentional failure")

        bootstrap = SystemBootstrap()
        bootstrap.register("Failing", fail_init)

        result = bootstrap.boot()

        self.assertTrue(result.success)  # Non-required failure doesn't fail boot
        self.assertEqual(result.systems_failed, 1)
        self.assertIn("Intentional failure", result.errors[0])

    def test_required_component_failure(self):
        """Required component failure should fail the boot."""
        from src.core import SystemBootstrap

        def fail_init():
            raise RuntimeError("Required failure")

        bootstrap = SystemBootstrap()
        bootstrap.register("Required", fail_init, required=True)

        result = bootstrap.boot()

        self.assertFalse(result.success)

    def test_disabled_components_skipped(self):
        """Disabled components should not be initialized."""
        from src.core import SystemBootstrap

        call_count = [0]

        def track_init():
            call_count[0] += 1
            return "init"

        bootstrap = SystemBootstrap()
        bootstrap.register("Disabled", track_init, enabled=False)

        result = bootstrap.boot()

        self.assertEqual(call_count[0], 0)
        self.assertEqual(result.systems_disabled, 1)

    def test_get_component(self):
        """get() should return initialized components."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap()
        bootstrap.register("Test", lambda: {"value": 42})
        bootstrap.boot()

        instance = bootstrap.get("Test")
        self.assertEqual(instance["value"], 42)

    def test_is_ready(self):
        """is_ready() should check component status."""
        from src.core import SystemBootstrap

        bootstrap = SystemBootstrap()
        bootstrap.register("Ready", lambda: True)
        bootstrap.register("Disabled", lambda: True, enabled=False)
        bootstrap.boot()

        self.assertTrue(bootstrap.is_ready("Ready"))
        self.assertFalse(bootstrap.is_ready("Disabled"))
        self.assertFalse(bootstrap.is_ready("NonExistent"))


def run_tests():
    """Run all tests and report results."""
    start_time = time.perf_counter()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestCoreImports,
        TestResultType,
        TestSafeImport,
        TestLazyImport,
        TestNuSyQFacade,
        TestBootstrap,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed = time.perf_counter() - start_time

    # Summary
    print("\n" + "=" * 60)
    print(f"Quick Check Complete: {elapsed:.2f}s")
    print(f"Tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if elapsed > 5.0:
        print(f"WARNING: Tests took {elapsed:.2f}s (target: <5s)")

    if result.wasSuccessful():
        print("STATUS: ALL TESTS PASSED")
        return 0
    else:
        print("STATUS: SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
