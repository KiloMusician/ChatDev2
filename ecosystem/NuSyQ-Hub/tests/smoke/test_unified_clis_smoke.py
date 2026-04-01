"""Smoke tests for unified CLIs (type, error, logging).

These tests verify that each unified CLI responds to --list-modes successfully,
which guards the entry points, argparse wiring, and basic execution path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run_cli(args: list[str]) -> str:
    """Run a CLI command from the repo root and return combined output."""
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert (
        proc.returncode == 0
    ), f"Command failed (rc={proc.returncode}): {' '.join(args)}\nOutput:\n{output}"
    return output


def test_unified_type_fixer_lists_modes():
    output = _run_cli(["scripts/unified_type_fixer.py", "--list-modes"])
    assert "add-annotations" in output
    assert "fix-mypy" in output


def test_unified_error_healer_lists_modes():
    output = _run_cli(["scripts/unified_error_healer.py", "--list-modes"])
    assert "surgical" in output
    assert "systematic" in output


def test_unified_logging_fixer_lists_modes():
    output = _run_cli(["scripts/unified_logging_fixer.py", "--list-modes"])
    assert "calls" in output
    assert "fstrings" in output
