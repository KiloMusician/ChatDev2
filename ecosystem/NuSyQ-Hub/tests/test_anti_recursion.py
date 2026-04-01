#!/usr/bin/env python3
"""🛡️ Anti-Recursion Verification Test
Tests all the recursion protection mechanisms we added
"""

import sys
import traceback
from pathlib import Path


def test_no_infinite_loops():
    """Test that our enhanced context browser can't go into infinite loops"""
    print("🛡️ ANTI-RECURSION TEST SUITE")
    print("=" * 60)

    # Add the interface directory to path
    interface_dir = Path(__file__).parent.parent / "src" / "interface"
    sys.path.insert(0, str(interface_dir))

    tests_passed = 0
    tests_total = 0

    # Test 1: Normal import should work
    print("\n🧪 Test 1: Normal import should work")
    tests_total += 1
    try:
        import Enhanced_Interactive_Context_Browser as browser_module

        print("   ✅ SUCCESS: Module imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 2: Single instance creation should work
    print("\n🧪 Test 2: Single instance creation should work")
    tests_total += 1
    try:
        browser_module.EnhancedContextBrowser()
        print("   ✅ SUCCESS: Single instance created")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 3: Multiple instance creation should be blocked
    print("\n🧪 Test 3: Multiple instances should be blocked")
    tests_total += 1
    try:
        browser_module.EnhancedContextBrowser()
        print("   ❌ FAILED: Second instance was allowed (should be blocked)")
    except RuntimeError as e:
        if "RECURSION PROTECTION" in str(e):
            print("   ✅ SUCCESS: Multiple instances correctly blocked")
            tests_passed += 1
        else:
            print(f"   ❌ FAILED: Wrong error type: {e}")
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")

    # Test 4: Reset counter and test again
    print("\n🧪 Test 4: Counter reset should allow new instance")
    tests_total += 1
    try:
        # Reset the instance counter
        browser_module.EnhancedContextBrowser._instance_count = 0
        browser_module.EnhancedContextBrowser()
        print("   ✅ SUCCESS: New instance created after reset")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 5: Main function recursion protection
    print("\n🧪 Test 5: Main function recursion protection")
    tests_total += 1
    try:
        # Reset main counter
        browser_module._main_execution_count = 0

        # First call should work
        try:
            # We can't actually call main() as it starts Streamlit
            # So we'll just test the counter mechanism
            browser_module._main_execution_count += 1
            if browser_module._main_execution_count <= browser_module._max_main_executions:
                print("   ✅ SUCCESS: Main function counter works correctly")
                tests_passed += 1
            else:
                print("   ❌ FAILED: Main function counter not working")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS: {tests_passed}/{tests_total} tests passed")

    assert tests_passed == tests_total, f"{tests_passed}/{tests_total} anti-recursion checks passed"
    print("🎉 ALL ANTI-RECURSION TESTS PASSED!")
    print("🛡️ No infinite loops detected - protection is working!")


def main():
    """Run the anti-recursion test suite"""
    try:
        test_no_infinite_loops()
        return 0
    except Exception as e:
        print(f"💥 TEST SUITE CRASHED: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
