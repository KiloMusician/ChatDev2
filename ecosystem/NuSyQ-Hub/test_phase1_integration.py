#!/usr/bin/env python3
"""Quick test script to validate Phase 1 integration."""

import subprocess
import sys


def test_examples_command():
    """Test that examples command works via start_nusyq.py"""
    print("=" * 70)
    print("Testing: python scripts/start_nusyq.py examples --list")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "examples", "--list"],
        capture_output=True,
        text=True,
        timeout=15,
    )

    # Show just the last 50 lines of output (to avoid terminal history)
    output_lines = result.stdout.split("\n")
    relevant_output = "\n".join(output_lines[-50:])

    print(relevant_output)
    print("\n" + "=" * 70)
    print(f"Return code: {result.returncode}")
    print("=" * 70)

    return result.returncode


def test_menu_learn():
    """Test that menu learn command shows the new category."""
    print("\n" * 2)
    print("=" * 70)
    print("Testing: python scripts/start_nusyq.py menu learn")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, "scripts/start_nusyq.py", "menu", "learn"],
        capture_output=True,
        text=True,
        timeout=15,
    )

    # Show just the last 50 lines
    output_lines = result.stdout.split("\n")
    relevant_output = "\n".join(output_lines[-50:])

    print(relevant_output)
    print("\n" + "=" * 70)
    print(f"Return code: {result.returncode}")
    print("=" * 70)

    return result.returncode


if __name__ == "__main__":
    print("🧪 Phase 1 Integration Tests - Documentation Examples\n")

    test1 = test_examples_command()
    test2 = test_menu_learn()

    print("\n" + "=" * 70)
    print("📊 Test Summary:")
    print("=" * 70)
    print(f"  examples command: {'✅ PASS' if test1 == 0 else '❌ FAIL'}")
    print(f"  menu learn command: {'✅ PASS' if test2 == 0 else '❌ FAIL'}")
    print("=" * 70)

    sys.exit(0 if (test1 == 0 and test2 == 0) else 1)
