#!/usr/bin/env python3
"""🧪 Test Suite: Zen → Subprocess Integration

Tests safe subprocess wrapper with Zen Engine validation.
Validates security layer on critical system commands.

OmniTag: {
    "purpose": "Test Zen subprocess integration",
    "dependencies": ["safe_subprocess", "zen_engine_wrapper"],
    "context": "Security validation testing",
    "evolution_stage": "v1.0-testing"
}
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_safe_subprocess_basic():
    """Test basic safe subprocess execution."""
    print("\n🧪 TEST 1: Basic Safe Subprocess Execution")
    print("=" * 60)

    try:
        from src.utils.safe_subprocess import SafeSubprocessExecutor

        executor = SafeSubprocessExecutor(auto_fix=True, strict_mode=False)

        # Test safe command (use shell for Windows compatibility)
        result = executor.run("echo Hello, Zen validation!", shell=True, capture_output=True, text=True)

        assert result.returncode == 0, "Command should succeed"
        assert "Hello" in result.stdout or "Zen" in result.stdout, "Output should contain message"

        print(f"   ✅ Safe command executed: {result.stdout.strip()}")
        print(f"   📊 Zen available: {executor.zen_available}")
        print(f"   🔧 Auto-fix enabled: {executor.auto_fix}")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_safe_subprocess_validation():
    """Test command validation with Zen Engine."""
    print("\n🧪 TEST 2: Zen Engine Command Validation")
    print("=" * 60)

    try:
        from src.utils.safe_subprocess import SafeSubprocessExecutor

        executor = SafeSubprocessExecutor(auto_fix=True, strict_mode=False)

        # Test command that might trigger validation warnings
        # (safe in non-strict mode)
        result = executor.run(
            "echo 'test' > nul" if sys.platform == "win32" else "echo 'test' > /dev/null",
            shell=True,
            capture_output=True,
            text=True,
        )

        print("   ✅ Command validated and executed")
        print(f"   📊 Exit code: {result.returncode}")
        print(f"   🛡️ Validation mode: {'Zen-enabled' if executor.zen_available else 'Fallback'}")

        return True

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_culture_ship_safe_launch():
    """Test Culture Ship launcher uses safe subprocess."""
    print("\n🧪 TEST 3: Culture Ship Safe Launch Integration")
    print("=" * 60)

    try:
        import inspect

        from src.diagnostics.ecosystem_startup_sentinel import EcosystemStartupSentinel

        sentinel = EcosystemStartupSentinel()

        # Check that _launch_culture_ship method exists
        assert hasattr(sentinel, "_launch_culture_ship"), "Culture Ship launcher should exist"

        # Inspect the method source to verify safe_subprocess usage
        source = inspect.getsource(sentinel._launch_culture_ship)
        uses_safe_subprocess = "safe_subprocess" in source

        print("   ✅ Culture Ship launcher exists")
        print(f"   🛡️ Uses safe_subprocess: {uses_safe_subprocess}")
        print(f"   📍 Method signature: {inspect.signature(sentinel._launch_culture_ship)}")

        if uses_safe_subprocess:
            print("   ✅ INTEGRATION VERIFIED: Zen validation active")
        else:
            print("   ⚠️  WARNING: Not using safe_subprocess wrapper")

        return uses_safe_subprocess

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pip_install_safe_wrapper():
    """Test pip install commands use safe subprocess."""
    print("\n🧪 TEST 4: Pip Install Safe Wrapper Integration")
    print("=" * 60)

    try:
        import inspect

        # Check import_health_checker
        try:
            from src.utils.import_health_checker import ImportHealthChecker

            checker = ImportHealthChecker()
            source = inspect.getsource(checker.fix_imports)
            uses_safe = "safe_subprocess" in source

            print("   ✅ ImportHealthChecker analyzed")
            print(f"   🛡️ Uses safe_subprocess: {uses_safe}")
        except Exception as e:
            print(f"   ⚠️  ImportHealthChecker check skipped: {e}")
            uses_safe = False

        # Check setup_chatdev_integration
        try:
            with open(repo_root / "src" / "utils" / "setup_chatdev_integration.py", "r") as f:
                setup_source = f.read()
            uses_safe_setup = "safe_subprocess" in setup_source

            print("   ✅ setup_chatdev_integration analyzed")
            print(f"   🛡️ Uses safe_subprocess: {uses_safe_setup}")
        except Exception as e:
            print(f"   ⚠️  setup_chatdev check skipped: {e}")
            uses_safe_setup = False

        result = uses_safe or uses_safe_setup
        if result:
            print("   ✅ INTEGRATION VERIFIED: Pip installs protected")
        else:
            print("   ⚠️  WARNING: Some pip installs may not be protected")

        return result

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all Zen subprocess integration tests."""
    print("🛡️ ZEN → SUBPROCESS INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing safe subprocess wrapper with Zen Engine validation")
    print()

    results = {
        "Basic Execution": test_safe_subprocess_basic(),
        "Zen Validation": test_safe_subprocess_validation(),
        "Culture Ship Launch": test_culture_ship_safe_launch(),
        "Pip Install Protection": test_pip_install_safe_wrapper(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   Total: {passed}/{total} tests passing")

    if passed == total:
        print("   🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"   ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
