"""VSCode Diagnostics Reader - Single Source of Truth for All Agents.

This module provides a simple API for all agents in the ecosystem to
access consistent error counts from VSCode diagnostics.

All agents (Claude Code, Copilot, Ollama, ChatDev, etc.) should use
this module instead of running their own linters to ensure consistent
error signals.

Usage:
    from src.diagnostics.vscode_diagnostics_reader import get_error_count, get_diagnostics

    # Get just the error count
    errors = get_error_count()
    print(f"Current errors: {errors}")

    # Get full diagnostics
    diag = get_diagnostics()
    print(f"Errors: {diag['errors']}, Warnings: {diag['warnings']}")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DiagnosticsNotAvailableError(Exception):
    """Raised when diagnostics file is not available."""


def get_diagnostics_path() -> Path:
    """Get path to VSCode diagnostics file."""
    # Assume we're in src/diagnostics, go up to repo root
    repo_root = Path(__file__).parent.parent.parent
    return repo_root / "state" / "vscode_diagnostics.json"


def get_unified_errors_path() -> Path:
    """Get path to unified errors file."""
    repo_root = Path(__file__).parent.parent.parent
    return repo_root / "state" / "unified_errors.json"


def get_diagnostics(fresh: bool = False, timeout: int = 180) -> dict:
    """Get current VSCode diagnostics.

    Args:
        fresh: If True, run diagnostics bridge to get fresh data
        timeout: Timeout for running diagnostics bridge (seconds)

    Returns:
        Dictionary with diagnostics data:
        {
            "timestamp": "2025-12-25T13:15:00",
            "errors": 623,
            "warnings": 43,
            "infos": 0,
            "hints": 0,
            "total": 666,
            "by_source": {...},
            "by_file": {...}
        }

    Raises:
        DiagnosticsNotAvailableError: If diagnostics file doesn't exist and fresh=False
    """
    diagnostics_path = get_diagnostics_path()

    if fresh:
        # Run diagnostics bridge to get fresh data
        import subprocess

        try:
            subprocess.run(
                ["python", "scripts/vscode_diagnostics_bridge.py", "--quiet"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except Exception as e:
            raise DiagnosticsNotAvailableError(f"Failed to run diagnostics bridge: {e}") from e

    if not diagnostics_path.exists():
        raise DiagnosticsNotAvailableError(
            f"Diagnostics file not found: {diagnostics_path}. Run: python scripts/vscode_diagnostics_bridge.py"
        )

    with open(diagnostics_path, encoding="utf-8") as f:
        result: dict[Any, Any] = json.load(f)
        return result


def get_error_count(fresh: bool = False) -> int:
    """Get current error count from VSCode diagnostics.

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        Number of errors (0 if diagnostics not available)
    """
    try:
        diagnostics = get_diagnostics(fresh=fresh)
        result: int = diagnostics.get("errors", 0)
        return result
    except DiagnosticsNotAvailableError:
        return 0


def get_warning_count(fresh: bool = False) -> int:
    """Get current warning count from VSCode diagnostics.

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        Number of warnings (0 if diagnostics not available)
    """
    try:
        diagnostics = get_diagnostics(fresh=fresh)
        result: int = diagnostics.get("warnings", 0)
        return result
    except DiagnosticsNotAvailableError:
        return 0


def get_total_issues(fresh: bool = False) -> int:
    """Get total issue count (errors + warnings + infos + hints).

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        Total number of issues (0 if diagnostics not available)
    """
    try:
        diagnostics = get_diagnostics(fresh=fresh)
        result: int = diagnostics.get("total", 0)
        return result
    except DiagnosticsNotAvailableError:
        return 0


def get_diagnostics_summary(fresh: bool = False) -> str:
    """Get human-readable diagnostics summary.

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        Summary string like "623 errors, 43 warnings, 0 infos (666 total)"
    """
    try:
        diagnostics = get_diagnostics(fresh=fresh)
        return (
            f"{diagnostics['errors']} errors, "
            f"{diagnostics['warnings']} warnings, "
            f"{diagnostics['infos']} infos "
            f"({diagnostics['total']} total)"
        )
    except DiagnosticsNotAvailableError:
        return "Diagnostics not available"


def is_diagnostics_stale(max_age_minutes: int = 30) -> bool:
    """Check if diagnostics are stale.

    Args:
        max_age_minutes: Maximum age in minutes before considering stale

    Returns:
        True if diagnostics are older than max_age_minutes or don't exist
    """
    try:
        diagnostics = get_diagnostics(fresh=False)
        timestamp_str = diagnostics.get("timestamp")
        if not timestamp_str:
            return True

        timestamp = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - timestamp
        return age.total_seconds() > (max_age_minutes * 60)
    except DiagnosticsNotAvailableError:
        return True


def get_unified_errors() -> dict | None:
    """Get unified errors from all linters (command-line tools).

    This provides error counts from flake8, mypy, ruff, tsc, eslint across
    all three repositories. Use get_diagnostics() for VSCode parity.

    Returns:
        Dictionary with unified errors or None if not available
    """
    unified_path = get_unified_errors_path()
    if not unified_path.exists():
        return None

    with open(unified_path, encoding="utf-8") as f:
        result: dict[Any, Any] = json.load(f)
        return result


def compare_vscode_vs_linters() -> dict:
    """Compare VSCode diagnostics against command-line linters.

    Returns:
        Dictionary with comparison:
        {
            "vscode": {...},
            "linters": {...},
            "delta": {...}
        }
    """
    vscode = get_diagnostics(fresh=False)
    unified = get_unified_errors()

    if not unified:
        return {"vscode": vscode, "linters": None, "delta": None}

    linter_totals = unified.get("totals", {})

    return {
        "vscode": {
            "errors": vscode["errors"],
            "warnings": vscode["warnings"],
            "total": vscode["total"],
        },
        "linters": linter_totals,
        "delta": {
            "errors": vscode["errors"] - linter_totals.get("errors", 0),
            "warnings": vscode["warnings"] - linter_totals.get("warnings", 0),
            "total": vscode["total"] - linter_totals.get("total", 0),
        },
    }


# Convenience constants for quick checks
def has_errors(fresh: bool = False) -> bool:
    """Check if there are any errors.

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        True if there are errors
    """
    return get_error_count(fresh=fresh) > 0


def is_clean(fresh: bool = False) -> bool:
    """Check if codebase is clean (no errors).

    Args:
        fresh: If True, run diagnostics bridge to get fresh data

    Returns:
        True if there are no errors
    """
    return get_error_count(fresh=fresh) == 0


# Example usage
if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("VSCODE DIAGNOSTICS READER - EXAMPLE USAGE")
    logger.info("=" * 70)

    try:
        # Get diagnostics
        diag = get_diagnostics()
        logger.info("\n✅ Diagnostics loaded:")
        logger.info(f"   {get_diagnostics_summary()}")

        # Check if stale
        if is_diagnostics_stale():
            logger.warning("\n⚠️  Diagnostics are stale (>30 min old)")
            logger.info("   Run: python scripts/vscode_diagnostics_bridge.py")

        # Check error status
        if is_clean():
            logger.error("\n🎉 Codebase is clean! No errors.")
        else:
            logger.error(f"\n❌ Codebase has {get_error_count()} errors")

        # Compare with linters
        comparison = compare_vscode_vs_linters()
        if comparison["delta"]:
            logger.info("\n📊 VSCode vs Linters Comparison:")
            logger.error(f"   VSCode:  {comparison['vscode']['errors']} errors")
            logger.error(f"   Linters: {comparison['linters']['errors']} errors")
            logger.error(f"   Delta:   {comparison['delta']['errors']:+d}")

    except DiagnosticsNotAvailableError as e:
        logger.error(f"\n❌ {e}")
        logger.info("   Run: python scripts/vscode_diagnostics_bridge.py")
