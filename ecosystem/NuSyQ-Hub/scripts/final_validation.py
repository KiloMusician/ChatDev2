#!/usr/bin/env python3
"""Final Validation & Test Run
============================
Validates that all error fixes are in place and tests can run successfully.
"""

import subprocess
import sys
from pathlib import Path


def run_cmd(name: str, cmd: list, timeout: int = 60) -> tuple[bool, str, str]:
    """Run a command and return (success, stdout, stderr)."""
    print(f"\n{'=' * 70}")
    print(f"🧪 {name}")
    print(f"{'=' * 70}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=Path(__file__).parent.parent)
        success = result.returncode == 0
        status = "✅ PASS" if success else f"⚠️ EXIT {result.returncode}"
        print(f"{status} (output below)")
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT ({timeout}s)")
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, "", str(e)


def main():
    print(
        """
    🎯 FINAL VALIDATION & TEST RUN
    ===============================================
    Checking: errors fixed, tests working, cache valid
    """
    )

    validations = [
        (
            "Error count verification",
            [sys.executable, "scripts/start_nusyq.py", "error_report", "--quick", "--hub-only"],
        ),
        (
            "Spine manager tests (serial)",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_spine_manager.py",
                "-v",
                "--tb=short",
                "--override-ini=addopts=",
            ],
        ),
        ("Quick linting check", [sys.executable, "-m", "ruff", "check", "src/", "--statistics"]),
        ("conftest.py validation", [sys.executable, "-m", "py_compile", "tests/conftest.py"]),
    ]

    results = []
    for name, cmd in validations:
        success, stdout, stderr = run_cmd(name, cmd)
        results.append((name, success))

        # Print relevant output
        if "error_report" in name.lower() and stdout:
            # Show diagnostic summary
            lines = stdout.split("\n")
            for i, line in enumerate(lines):
                if "CANONICAL GROUND TRUTH" in line:
                    print("\n".join(lines[i : i + 10]))
                    break
        elif "spine" in name.lower() and stdout:
            # Show test results
            lines = stdout.split("\n")
            for line in lines:
                if "passed" in line.lower() or "failed" in line.lower():
                    print(line)

        if stderr and "warning" not in stderr.lower()[:50]:
            print(f"STDERR: {stderr[:200]}")

    # Summary
    print(f"\n{'=' * 70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅" if success else "⚠️"
        print(f"{status} {name}")

    print(f"\n{'✅ ALL VALIDATIONS PASSED' if passed == total else f'⚠️ {total - passed}/{total} FAILED'}")
    print("\n🚀 Ready for next phase: Address E402/E501 or run full test suite")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
