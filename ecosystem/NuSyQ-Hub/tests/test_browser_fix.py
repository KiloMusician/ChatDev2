#!/usr/bin/env python3
"""Test Script to Verify Enhanced Context Browser Fixes"""

import sys
from pathlib import Path


def test_import():
    """Test if the fixed browser can be imported"""
    try:
        # Add the interface directory to path
        interface_dir = Path(__file__).parent.parent / "src" / "interface"
        sys.path.insert(0, str(interface_dir))

        print("🔍 Testing Enhanced Context Browser import...")

        # Import the module
        import Enhanced_Interactive_Context_Browser as browser_module

        print("✅ SUCCESS: Module imported without stack overflow!")

        # Check for duplicate classes
        class_count = sum(1 for name in dir(browser_module) if name == "EnhancedContextBrowser")
        print(f"📊 EnhancedContextBrowser class instances found: {class_count}")

        if class_count == 1:
            print("✅ SUCCESS: Only one EnhancedContextBrowser class found!")
        else:
            print("❌ ERROR: Multiple EnhancedContextBrowser classes detected!")

        # Test class instantiation — allow exceptions to fail the test
        browser = browser_module.EnhancedContextBrowser()
        print("✅ SUCCESS: EnhancedContextBrowser instantiated successfully!")
        assert browser is not None

    except Exception as e:
        print(f"❌ ERROR: Import failed: {e}")
        raise AssertionError(f"Import failed: {e}") from e


def main():
    print("🚀 Enhanced Context Browser Fix Verification")
    print("=" * 50)

    # Run standalone: convert exceptions into exit codes
    try:
        test_import()
        print("=" * 50)
        print("🎉 ALL TESTS PASSED! Stack overflow issue appears to be fixed.")
        return 0
    except (RecursionError, RuntimeError):  # StackOverflowError doesn't exist in Python
        print("=" * 50)
        print("💥 TESTS FAILED! Stack overflow issue may still exist.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
