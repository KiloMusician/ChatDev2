#!/usr/bin/env python
"""Count all errors from all linting/checking tools."""

import subprocess


def count_errors(tool_cmd: list[str], pattern: str) -> int:
    """Run a tool and count error lines."""
    try:
        result = subprocess.run(
            tool_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            check=False,
        )
        output = result.stdout + result.stderr

        # Count lines matching pattern
        count = sum(1 for line in output.split("\n") if pattern in line.lower())

        # Also try to extract summary
        for line in output.split("\n")[-20:]:
            if "found" in line.lower() and "error" in line.lower():
                print(f"  Summary: {line.strip()}")

        return count
    except Exception as e:
        print(f"  Error running {tool_cmd[0]}: {e}")
        return 0


print("=" * 80)
print("COMPREHENSIVE ERROR COUNT")
print("=" * 80)

# Ruff errors
print("\n1. RUFF (linting):")
ruff_count = count_errors(["python", "-m", "ruff", "check", "src/", "tests/"], "error")
print(f"   Error lines: {ruff_count}")

# Mypy errors
print("\n2. MYPY (type checking):")
mypy_count = count_errors(["python", "-m", "mypy", "src/", "tests/", "--show-error-codes"], "error:")
print(f"   Error lines: {mypy_count}")

# Pylint errors
print("\n3. PYLINT (optional):")
try:
    pylint_count = count_errors(["python", "-m", "pylint", "src/", "--errors-only"], "error")
    print(f"   Error lines: {pylint_count}")
except (subprocess.SubprocessError, OSError):
    print("   Not installed or failed")

print("\n" + "=" * 80)
print(f"TOTAL APPROXIMATE ERRORS: {ruff_count + mypy_count}")
print("=" * 80)
