#!/usr/bin/env python3
"""nusyq_git_utils.py — Git and subprocess utilities

Extracted from scripts/start_nusyq.py (Phase 2 modularization)

Responsibilities:
- Subprocess execution with tracing support
- Git repository detection
- Environment setup for OTEL tracing
- Resource attribute management

This module provides reusable utilities for git operations and subprocess
execution across the NuSyQ ecosystem.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Ensure package imports work when executed as script
if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _append_resource_attributes(existing: str | None, extra_attrs: dict[str, str]) -> str:
    """Append OTEL resource attributes to existing attributes string.

    Handles merging new attributes into existing comma-separated key=value pairs.

    Args:
        existing: Existing OTEL_RESOURCE_ATTRIBUTES string (may be None)
        extra_attrs: Dictionary of new attributes to add

    Returns:
        Merged OTEL_RESOURCE_ATTRIBUTES string
    """
    if not extra_attrs:
        return existing or ""

    # Parse existing attributes
    attrs = {}
    if existing:
        for pair in existing.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                attrs[k.strip()] = v.strip()

    # Merge in new attributes
    attrs.update(extra_attrs)

    # Reconstruct as comma-separated string
    return ",".join(f"{k}={v}" for k, v in attrs.items())


def _build_env() -> dict[str, str]:
    """Build environment dict with OTEL tracing support.

    Sets up environment variables for OpenTelemetry tracing if configured.
    Preserves existing environment and ensures tracing attributes are initialized.

    Returns:
        Dictionary with environment variables including OTEL_RESOURCE_ATTRIBUTES
    """
    env = dict(os.environ)

    # Initialize OTEL resource attributes if not set
    if "OTEL_RESOURCE_ATTRIBUTES" not in env:
        env["OTEL_RESOURCE_ATTRIBUTES"] = "nusyq.module=core"

    # Ensure UTF-8 mode is enabled
    if "PYTHONUTF8" not in env:
        env["PYTHONUTF8"] = "1"

    return env


def run(cmd: list[str], cwd: Path | None = None, timeout_s: int = 10) -> tuple[int, str, str]:
    """Run a subprocess command safely and return (code, stdout, stderr).

    Executes commands with automatic UTF-8 encoding, timeout handling,
    and OTEL tracing support in the environment.

    Args:
        cmd: Command as list of strings
        cwd: Working directory for command execution
        timeout_s: Command timeout in seconds (default: 10)

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=_build_env(),
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"TimeoutExpired: command exceeded {timeout_s}s timeout"
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def is_git_repo(path: Path) -> bool:
    """Lightweight check: directory contains a .git folder.

    Non-destructive validation that a path is a git repository.

    Args:
        path: Path to check

    Returns:
        True if path exists and contains .git directory
    """
    try:
        return path.is_dir() and (path / ".git").exists()
    except Exception:
        return False


def git_branch(path: Path | None) -> str:
    """Get current git branch name.

    Args:
        path: Repository path

    Returns:
        Branch name or "unknown" if unable to determine
    """
    if not path:
        return "unknown"

    rc, out, _err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    return out if rc == 0 and out else "unknown"


def git_head(path: Path | None, short: bool = True) -> str:
    """Get current git HEAD commit hash.

    Args:
        path: Repository path
        short: If True, return first 12 characters

    Returns:
        Commit hash or "unknown" if unable to determine
    """
    if not path:
        return "unknown"

    rc, out, _err = run(["git", "rev-parse", "HEAD"], cwd=path)
    if rc == 0 and out:
        return out[:12] if short else out
    return "unknown"


def git_status(path: Path | None) -> str:
    """Get git working tree status.

    Args:
        path: Repository path

    Returns:
        "clean" if no changes, "DIRTY" if changes exist, "unknown" on error
    """
    if not path:
        return "unknown"

    rc, out, _err = run(["git", "status", "--porcelain"], cwd=path)
    if rc == 0:
        return "clean" if not out else "DIRTY"
    return "unknown"


def git_ahead_behind(path: Path | None) -> str:
    """Get commits ahead/behind upstream.

    Args:
        path: Repository path

    Returns:
        String like "0 0" for ahead/behind, or "n/a" if no upstream
    """
    if not path:
        return "n/a"

    rc, out, _err = run(["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"], cwd=path)
    if rc == 0 and out:
        return out.replace("\t", " ")
    return "n/a"


if __name__ == "__main__":
    # Demo: if executed directly, show git operations
    cwd = Path.cwd()

    print(f"Git Utilities Demo (path={cwd})")
    print(f"- Is git repo: {is_git_repo(cwd)}")
    print(f"- Branch: {git_branch(cwd)}")
    print(f"- HEAD: {git_head(cwd)}")
    print(f"- Status: {git_status(cwd)}")
    print(f"- Ahead/Behind: {git_ahead_behind(cwd)}")
