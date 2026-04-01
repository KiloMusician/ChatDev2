#!/usr/bin/env python
"""Comprehensive current state analyzer for NuSyQ-Hub."""

import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Run a command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        return result.stdout + result.stderr, result.returncode
    except (subprocess.SubprocessError, TimeoutError, OSError) as e:
        return f"Error: {e}", 1


def main():
    """Analyze current project state."""
    print("=" * 80)
    print("NUSYQ-HUB CURRENT STATE ANALYSIS")
    print("=" * 80)

    # 1. Ruff linting errors
    print("\n📋 RUFF LINTING ERRORS:")
    print("-" * 80)
    output, _ = run_command(["python", "-m", "ruff", "check", "src/", "tests/"])

    # Count errors by extracting the summary line
    lines = output.split("\n")
    for line in lines[-10:]:  # Check last 10 lines for summary
        if "Found" in line or "error" in line.lower():
            print(f"  {line.strip()}")

    # Get statistics
    print("\n📊 ERROR STATISTICS:")
    print("-" * 80)
    stat_output, _ = run_command(["python", "-m", "ruff", "check", "src/", "tests/", "--statistics"])
    stat_lines = [line for line in stat_output.split("\n") if line.strip() and not line.startswith("warning")]
    for line in stat_lines[:20]:  # Top 20 error types
        if line.strip():
            print(f"  {line}")

    # 2. Test suite status
    print("\n🧪 TEST SUITE STATUS:")
    print("-" * 80)
    test_output, _ = run_command(["python", "-m", "pytest", "tests/", "-q", "--tb=no", "-x"])

    # Extract summary
    for line in test_output.split("\n")[-5:]:
        if line.strip():
            print(f"  {line.strip()}")

    # 3. File counts
    print("\n📁 FILE COUNTS:")
    print("-" * 80)
    src_files = len(list(Path("src").rglob("*.py")))
    test_files = len(list(Path("tests").rglob("*.py")))
    print(f"  Source files: {src_files}")
    print(f"  Test files: {test_files}")

    # 4. Top error files
    print("\n🔥 TOP ERROR FILES:")
    print("-" * 80)
    error_files = {}
    for line in output.split("\n"):
        if line.strip() and (":" in line) and (".py:" in line):
            try:
                filepath = line.split(":")[0].strip()
                if filepath not in error_files:
                    error_files[filepath] = 0
                error_files[filepath] += 1
            except (ValueError, IndexError, KeyError):
                pass

    sorted_files = sorted(error_files.items(), key=lambda x: x[1], reverse=True)
    for filepath, count in sorted_files[:15]:
        filename = Path(filepath).name
        print(f"  {count:3d} errors - {filename}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
