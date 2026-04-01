#!/usr/bin/env python3
"""Test Quantum Error Bridge - Self-Healing Error Resolution.

Tests the complete workflow:
1. Trigger various errors
2. Quantum error bridge handles them
3. Auto-fix attempts
4. PU creation for unresolved errors
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.integration.quantum_error_bridge import get_quantum_error_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)


async def test_syntax_error():
    """Test handling of syntax error (high auto-fix probability)."""
    print("\n" + "=" * 60)
    print("TEST 1: Syntax Error (Should Auto-Fix)")
    print("=" * 60)

    bridge = get_quantum_error_bridge()

    # Simulate syntax error
    error = SyntaxError("invalid syntax (missing colon)")
    context = {
        "task": "test_syntax_error",
        "file": "test_file.py",
        "function": "test_function",
        "line": 42,
    }

    result = await bridge.handle_error(error, context, auto_fix=True)

    print("\n📊 Result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Quantum State: {result['quantum_state']}")
    print(f"  Resolution Attempted: {result['resolution_attempted']}")
    print(f"  Auto-Fixed: {result['auto_fixed']}")
    print(f"  PU Created: {result['pu_created']}")
    print(f"  Actions: {result['actions']}")

    return result


async def test_import_error():
    """Test handling of import error (moderate auto-fix probability)."""
    print("\n" + "=" * 60)
    print("TEST 2: Import Error (Moderate Auto-Fix)")
    print("=" * 60)

    bridge = get_quantum_error_bridge()

    # Simulate import error
    error = ImportError("No module named 'nonexistent_module'")
    context = {
        "task": "test_import_error",
        "file": "test_imports.py",
        "function": "load_module",
        "line": 10,
    }

    result = await bridge.handle_error(error, context, auto_fix=True)

    print("\n📊 Result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Quantum State: {result['quantum_state']}")
    print(f"  Resolution Attempted: {result['resolution_attempted']}")
    print(f"  Auto-Fixed: {result['auto_fixed']}")
    print(f"  PU Created: {result['pu_created']}")
    print(f"  Actions: {result['actions']}")

    return result


async def test_timeout_error():
    """Test handling of timeout error (low auto-fix probability)."""
    print("\n" + "=" * 60)
    print("TEST 3: Timeout Error (Should Escalate to PU)")
    print("=" * 60)

    bridge = get_quantum_error_bridge()

    # Simulate timeout error
    error = TimeoutError("Operation timed out after 60 seconds")
    context = {
        "task": "test_timeout_error",
        "file": "test_async.py",
        "function": "long_running_task",
        "timeout": 60,
    }

    result = await bridge.handle_error(error, context, auto_fix=True)

    print("\n📊 Result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Quantum State: {result['quantum_state']}")
    print(f"  Resolution Attempted: {result['resolution_attempted']}")
    print(f"  Auto-Fixed: {result['auto_fixed']}")
    print(f"  PU Created: {result['pu_created']}")
    print(f"  Actions: {result['actions']}")

    return result


async def test_no_auto_fix():
    """Test with auto-fix disabled (should always create PU)."""
    print("\n" + "=" * 60)
    print("TEST 4: Auto-Fix Disabled (Should Create PU)")
    print("=" * 60)

    bridge = get_quantum_error_bridge()

    # Simulate value error
    error = ValueError("Invalid value provided")
    context = {
        "task": "test_no_auto_fix",
        "file": "test_validation.py",
        "function": "validate_input",
        "value": "invalid",
    }

    result = await bridge.handle_error(error, context, auto_fix=False)

    print("\n📊 Result:")
    print(f"  Error Type: {result['error_type']}")
    print(f"  Quantum State: {result['quantum_state']}")
    print(f"  Resolution Attempted: {result['resolution_attempted']}")
    print(f"  Auto-Fixed: {result['auto_fixed']}")
    print(f"  PU Created: {result['pu_created']}")
    print(f"  Actions: {result['actions']}")

    return result


async def test_scan_and_heal():
    """Test workspace scanning and healing."""
    print("\n" + "=" * 60)
    print("TEST 5: Workspace Scan and Heal")
    print("=" * 60)

    bridge = get_quantum_error_bridge()

    summary = await bridge.scan_and_heal()

    print("\n📊 Healing Summary:")
    print(f"  Problems Found: {summary['problems_found']}")
    print(f"  Auto-Resolved: {summary['auto_resolved']}")
    print(f"  PUs Created: {summary['pus_created']}")
    print(f"  Failed: {summary['failed']}")

    return summary


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🌌 QUANTUM ERROR BRIDGE TESTING")
    print("=" * 60)

    results = {
        "syntax_error": await test_syntax_error(),
        "import_error": await test_import_error(),
        "timeout_error": await test_timeout_error(),
        "no_auto_fix": await test_no_auto_fix(),
        "scan_heal": await test_scan_and_heal(),
    }

    print("\n" + "=" * 60)
    print("📊 OVERALL TEST SUMMARY")
    print("=" * 60)

    auto_fixed_count = sum(
        1
        for r in [
            results["syntax_error"],
            results["import_error"],
            results["timeout_error"],
            results["no_auto_fix"],
        ]
        if r.get("auto_fixed", False)
    )

    pu_created_count = sum(
        1
        for r in [
            results["syntax_error"],
            results["import_error"],
            results["timeout_error"],
            results["no_auto_fix"],
        ]
        if r.get("pu_created", False)
    )

    print("\n  Total Tests: 5")
    print(f"  Auto-Fixed: {auto_fixed_count}/4 error handling tests")
    print(f"  PUs Created: {pu_created_count}/4 error handling tests")
    print(f"  Scan Results: {results['scan_heal']['problems_found']} problems found")

    print("\n✅ Quantum Error Bridge testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
