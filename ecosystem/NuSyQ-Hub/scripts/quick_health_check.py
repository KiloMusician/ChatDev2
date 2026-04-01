#!/usr/bin/env python3
"""Quick Health Check - Fast pre-commit validation

Runs:
1. Smoke tests (~23s)
2. Ruff linting
3. Black formatting check

Total time: <30s
Perfect for pre-commit hooks and rapid feedback.
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_check(name: str, cmd: list[str]) -> tuple[bool, float]:
    """Run a check and return success + duration."""
    print(f"\n🔍 {name}...")
    start = time.time()

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    duration = time.time() - start
    success = result.returncode == 0

    if success:
        print(f"  ✅ Passed ({duration:.1f}s)")
    else:
        print(f"  ❌ Failed ({duration:.1f}s)")
        if result.stdout:
            print(f"\n{result.stdout}")
        if result.stderr:
            print(f"\n{result.stderr}")

    return success, duration


def main() -> int:
    """Run quick health checks."""
    print("=" * 60)
    print("🏥 QUICK HEALTH CHECK")
    print("=" * 60)

    total_start = time.time()
    checks = []

    # 1. Smoke tests (disable coverage for speed)
    success, duration = run_check(
        "Smoke Tests",
        [sys.executable, "-m", "pytest", "-m", "smoke", "-v", "--tb=line", "-q", "--no-cov"],
    )
    checks.append(("Smoke Tests", success, duration))

    # 2. Ruff linting
    success, duration = run_check("Ruff Linting", [sys.executable, "-m", "ruff", "check", "src/"])
    checks.append(("Ruff", success, duration))

    # 3. Black formatting
    success, duration = run_check("Black Formatting", [sys.executable, "-m", "black", "src/", "--check"])
    checks.append(("Black", success, duration))

    # Summary
    total_duration = time.time() - total_start
    all_passed = all(s for _, s, _ in checks)

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    for name, success, duration in checks:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name:20s} ({duration:5.1f}s)")

    print(f"\n{'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    print(f"Total time: {total_duration:.1f}s")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
