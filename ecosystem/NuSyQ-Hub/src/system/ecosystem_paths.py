#!/usr/bin/env python3
"""🗺️ Unified Ecosystem Path Resolution.

Provides intelligent path resolution for the NuSyQ tripartite ecosystem.
Works seamlessly in both host and container environments.

Ecosystem Structure:
    - NuSyQ-Hub: Main hub with scripts, git hooks, and core infrastructure
    - NuSyQ: MCP server, orchestrator, and core services
    - SimulatedVerse: Frontend visualization and interaction layer

Priority Order:
    1. Environment variables (NUSYQ_HUB_ROOT, NUSYQ_ROOT, SIMULATEDVERSE_ROOT)
    2. Git root detection (for current repo)
    3. Fallback defaults (home-based conventional paths)

Usage:
    from src.system.ecosystem_paths import get_repo_roots, get_ecosystem_root

    # Get all three repo paths
    roots = get_repo_roots()
    print(roots['hub'])      # Path to NuSyQ-Hub
    print(roots['nusyq'])    # Path to NuSyQ
    print(roots['simverse']) # Path to SimulatedVerse

    # Get current executing repo
    current = get_ecosystem_root()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)


class RepoRoots(TypedDict):
    """Type definition for repository roots."""

    hub: Path
    nusyq: Path
    simverse: Path


def get_ecosystem_root() -> Path:
    """Get current executing repository root.

    Determines which of the three repos (NuSyQ-Hub, NuSyQ, SimulatedVerse)
    is currently being executed from.

    Returns:
        Path to the git root of the current repository

    Priority:
        1. ECOSYSTEM_ROOT environment variable
        2. Git root detection (traverse up to find .git/)
        3. Current working directory

    """
    # Check environment variable first (container priority)
    if env_root := os.getenv("ECOSYSTEM_ROOT"):
        return Path(env_root).resolve()

    # Find git root by traversing upward
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Fallback to current directory
    return Path.cwd().resolve()


def get_repo_roots() -> RepoRoots:
    """Get all three repository roots with intelligent fallback.

    Returns:
        Dictionary with keys 'hub', 'nusyq', 'simverse' mapping to Path objects

    Fallback Strategy:
        1. Environment variables (highest priority - container-friendly)
        2. repo_path_resolver.py (if available and configured)
        3. Conventional defaults (home-based paths)

    """
    # Start with environment variables (container-aware)
    hub_root = os.getenv("NUSYQ_HUB_ROOT")
    nusyq_root = os.getenv("NUSYQ_ROOT")
    simverse_root = os.getenv("SIMULATEDVERSE_ROOT")

    # Detect if we're in a container
    in_container = os.getenv("IN_DEVCONTAINER") == "true"

    if in_container:
        # Container paths (fixed locations)
        roots: RepoRoots = {
            "hub": Path(hub_root or "/workspaces/NuSyQ-Hub"),
            "nusyq": Path(nusyq_root or "/workspaces/NuSyQ"),
            "simverse": Path(simverse_root or "/workspaces/SimulatedVerse"),
        }
    else:
        # Host paths - use fallback detection
        roots = {
            "hub": Path(hub_root or Path.home() / "Desktop" / "Legacy" / "NuSyQ-Hub"),
            "nusyq": Path(nusyq_root or Path.home() / "NuSyQ"),
            "simverse": Path(
                simverse_root or Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
            ),
        }

    # Attempt to use repo_path_resolver as fallback (if module exists)
    try:
        from src.utils.repo_path_resolver import get_repo_path

        # Only override if path doesn't exist and resolver can provide better one
        if not roots["hub"].exists():
            try:
                resolved = get_repo_path("NUSYQ_HUB_ROOT")
                if resolved.exists():
                    roots["hub"] = resolved
            except KeyError:
                logger.debug("Suppressed KeyError", exc_info=True)

        if not roots["nusyq"].exists():
            try:
                resolved = get_repo_path("NUSYQ_ROOT")
                if resolved.exists():
                    roots["nusyq"] = resolved
            except KeyError:
                logger.debug("Suppressed KeyError", exc_info=True)

        if not roots["simverse"].exists():
            try:
                resolved = get_repo_path("SIMULATEDVERSE_ROOT")
                if resolved.exists():
                    roots["simverse"] = resolved
            except KeyError:
                logger.debug("Suppressed KeyError", exc_info=True)
    except ImportError:
        pass  # repo_path_resolver not available - stick with defaults

    # Resolve all paths (make absolute, follow symlinks)
    result: RepoRoots = {
        "hub": roots["hub"].resolve(),
        "nusyq": roots["nusyq"].resolve(),
        "simverse": roots["simverse"].resolve(),
    }
    return result


def validate_ecosystem() -> dict[str, bool]:
    """Validate that all ecosystem repositories exist.

    Returns:
        Dictionary mapping repo name to existence status

    """
    roots = get_repo_roots()
    result = {}
    for name in ("hub", "nusyq", "simverse"):
        result[name] = roots[name].exists()
    return result


def print_ecosystem_status() -> None:
    """Print ecosystem status with visual indicators."""
    roots = get_repo_roots()
    validation = validate_ecosystem()

    logger.info("🗺️  NuSyQ Ecosystem Path Status\n")

    for name, path in roots.items():
        exists = "✅" if validation[name] else "❌"
        repo_names = {"hub": "NuSyQ-Hub", "nusyq": "NuSyQ-Root", "simverse": "SimulatedVerse"}
        logger.info(f"{exists} {repo_names[name]}: {path}")

    # Environment context
    in_container = os.getenv("IN_DEVCONTAINER") == "true"
    logger.info(f"\n🌍 Environment: {'Container' if in_container else 'Host'}")

    # Validation summary
    valid_count = sum(validation.values())
    total_count = len(validation)
    logger.info(f"📊 Valid: {valid_count}/{total_count} repositories")


if __name__ == "__main__":
    # CLI usage for diagnostics
    print_ecosystem_status()
