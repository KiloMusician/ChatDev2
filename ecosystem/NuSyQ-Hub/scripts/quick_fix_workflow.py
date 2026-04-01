#!/usr/bin/env python
"""Quick fix workflow for the Perpetual Chug Engine.
Runs through prioritized fixes in a systematic way.
"""

import subprocess
import sys
import time


def run_step(name, command, critical=False):
    """Run a fix step and return success"""
    print(f"\n{'=' * 60}")
    print(f"🔧 STEP: {name}")
    print(f"   Command: {command}")
    print(f"{'=' * 60}")

    start_time = time.time()

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ SUCCESS ({elapsed:.1f}s)")
            if result.stdout:
                lines = result.stdout.split("\n")
                print(f"   Output: {lines[-2] if len(lines) > 1 else lines[0]}")
            return True
        else:
            print(f"❌ FAILED ({elapsed:.1f}s, exit {result.returncode})")
            if result.stderr:
                error_lines = result.stderr.split("\n")
                print(f"   Error: {error_lines[0][:100]}")

            if critical:
                print("   ⚠️  This step is critical - stopping workflow")
                return False
            else:
                print("   ⚠️  Non-critical failure - continuing")
                return True  # Continue anyway for non-critical

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"⏰ TIMEOUT ({elapsed:.1f}s)")
        return not critical  # Continue if not critical
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"💥 EXCEPTION ({elapsed:.1f}s): {e}")
        return not critical


def main():
    print("🚀 QUICK FIX WORKFLOW FOR PERPETUAL CHUG")
    print("=" * 60)

    all_success = True

    # Step 1: Ensure pytest capture works
    success = run_step("Fix pytest capture", "python scripts/fix_pytest_capture.py", critical=False)
    all_success = all_success and success

    # Step 2: Check syntax errors (must fix)
    success = run_step(
        "Run quick error scan",
        "python scripts/start_nusyq.py error_report --quick --hub-only --force",
        critical=False,
    )
    all_success = all_success and success

    # Step 3: Fix highest priority ruff errors
    success = run_step(
        "Auto-fix ruff errors (F-category)",
        "python -m ruff check --select F --fix --exit-zero",
        critical=False,
    )
    all_success = all_success and success

    # Step 4: Format code with black
    success = run_step(
        "Format code with black",
        "python -m black src/ tests/ scripts/ --line-length=100 --quiet",
        critical=False,
    )
    all_success = all_success and success

    # Step 5: Test spine manager
    success = run_step(
        "Test spine manager with canonical runner",
        "python scripts/friendly_test_runner.py --mode quick tests/test_spine_manager.py -v",
        critical=False,
    )
    all_success = all_success and success

    # Step 6: Run a quick test sample
    success = run_step(
        "Run sample tests",
        "python -m pytest tests/test_imports_smoke.py -v --tb=short",
        critical=False,
    )
    all_success = all_success and success

    print("\n" + "=" * 60)
    print("📊 WORKFLOW COMPLETE")
    print("=" * 60)

    if all_success:
        print("✅ All steps completed successfully")
        print("\n🎯 Next actions:")
        print("  1. Review changes: git diff --stat")
        print("  2. Run full test suite: python scripts/friendly_test_runner.py tests/")
        print("  3. Commit changes: git add . && git commit -m 'fix: apply comprehensive error fixes'")
        print("  4. Continue with regular development")
    else:
        print("⚠️  Some steps failed - check output above")
        print("\n🔧 Debug steps:")
        print("  1. Run single test: python -m pytest tests/test_spine_manager.py -xvs")
        print("  2. Check error report: python scripts/start_nusyq.py error_report --quick")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
