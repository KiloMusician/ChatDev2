#!/usr/bin/env python3
"""Scan for stray ``src`` directories across repositories.

This script helps catch misplaced ``src`` folders (e.g., inside backups or docs)
that can confuse tooling and import resolution. It supports an allowlist for
known, intentional nested ``src`` trees and can return a non-zero exit code
when unexpected locations are found.

Quality-of-life additions:
- Extra allowlist entries via CLI (``--allow``) or env ``CHECK_SRC_EXTRA_ALLOWLIST``
    (semicolon-separated relative paths applied to all roots)
- Broader default exclusions (e.g., .ruff_cache, __pycache__)
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TypedDict

EXCLUDE_PARTS: set[str] = {
    ".venv",
    ".venv.old",
    ".venv.bak",
    "node_modules",
    ".mypy_cache",
    ".docker_build_context",
    ".sanitized_build_context",
    ".git",
    "venv",
    ".ruff_cache",
    "__pycache__",
}


class ScanResult(TypedDict):
    root: str
    exists: bool
    root_src: bool
    found: list[str]
    unexpected: list[str]


def _default_root(env_key: str, fallback: Path) -> Path:
    env_value = os.getenv(env_key)
    return Path(env_value).expanduser().resolve() if env_value else fallback.resolve()


# Known, intentional src directories (relative to their repo root)
HUB_ROOT = _default_root(
    "NUSYQ_HUB_ROOT",
    Path.home() / "Desktop" / "Legacy" / "NuSyQ-Hub",
)
SIMVERSE_ROOT = _default_root(
    "SIMULATEDVERSE_ROOT",
    Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
)
NUSYQ_ROOT = _default_root("NUSYQ_ROOT", Path.home() / "NuSyQ")

ALLOWLIST: dict[Path, set[Path]] = {
    HUB_ROOT: {
        Path("src"),
        Path("src/game_development/src"),
        Path("Transcendent_Spine/kilo-foolish-transcendent-spine/src"),
        Path("vscode-extension/src"),
    },
    SIMVERSE_ROOT: {
        Path("src"),
        Path("application-services/engine/src"),
        Path("application-services/repopilot/src"),
        Path("application-services/storyteller/src"),
        Path("application-services/web/src"),
        Path("apps/web/src"),
        Path("client/src"),
        Path("packages/kpulse-atmo/src"),
        Path("PreviewUI/src"),
    },
    NUSYQ_ROOT: {
        Path("src"),
        Path("mcp_server/src"),
    },
}


def _iter_src_dirs(root: Path, exclude_parts: Iterable[str]) -> list[Path]:
    """Return all ``src`` directories under ``root`` excluding unwanted paths."""
    # On Windows paths are case-insensitive; rglob("src") is sufficient.
    dirs: list[Path] = []
    for candidate in root.rglob("src"):
        if not candidate.is_dir():
            continue
        parts = set(candidate.parts)
        if any(part in parts for part in exclude_parts):
            continue
        dirs.append(candidate)
    return dirs


def scan_root(root: Path, allowed: set[Path]) -> ScanResult:
    """Scan a single repository root for src directories.

    Returns a dictionary suitable for JSON output and testing.
    """
    result: ScanResult = {
        "root": str(root),
        "exists": root.exists(),
        "root_src": False,
        "found": [],
        "unexpected": [],
    }

    if not root.exists():
        return result

    found_dirs = _iter_src_dirs(root, EXCLUDE_PARTS)
    root_src = root / "src"
    result["root_src"] = root_src.exists()

    rel_paths = [d.relative_to(root) for d in found_dirs]
    result["found"] = [str(p) for p in sorted(rel_paths)]

    unexpected = [p for p in rel_paths if p not in allowed]
    result["unexpected"] = [str(p) for p in sorted(unexpected)]
    return result


def format_report(entry: ScanResult) -> str:
    lines = [f"\nRepository root: {entry['root']}"]
    if not entry.get("exists"):
        lines.append("  Not found")
        return "\n".join(lines)

    lines.append(f"  root/src exists: {entry.get('root_src')}")
    found = entry.get("found", [])
    lines.append(f"  total src directories found (excluding venv/node_modules): {len(found)}")
    for rel in found:
        depth = len(Path(rel).parts)
        lines.append(f"    depth {depth}: {rel}")

    unexpected = entry.get("unexpected", [])
    if unexpected:
        lines.append(f"  ⚠️  unexpected src directories: {len(unexpected)}")
        for rel in unexpected:
            lines.append(f"    - {rel}")
    return "\n".join(lines)


def _extra_allowlist_from_env() -> set[Path]:
    """Load extra allowlist entries from environment variable.

    The variable ``CHECK_SRC_EXTRA_ALLOWLIST`` may contain a semicolon-separated
    list of relative paths (e.g., ``src/custom;packages/app/src``). Entries are
    applied to **all** scanned roots and merged with the per-root allowlist.
    """
    import os

    raw = os.environ.get("CHECK_SRC_EXTRA_ALLOWLIST", "")
    if not raw.strip():
        return set()
    return {Path(piece.strip()) for piece in raw.split(";") if piece.strip()}


def parse_roots(raw_roots: Sequence[str] | None) -> list[Path]:
    if raw_roots:
        return [Path(r).resolve() for r in raw_roots]
    return list(ALLOWLIST.keys())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan for stray src directories")
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        help="Root path(s) to scan. Defaults to configured repos.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument(
        "--allow",
        dest="extra_allow",
        action="append",
        help="Extra relative src path to allow (applied to all roots). Can be given multiple times.",
    )
    parser.add_argument(
        "--fail-on-unexpected",
        action="store_true",
        help="Exit with code 1 if unexpected src directories are found",
    )
    args = parser.parse_args(argv)

    roots = parse_roots(args.roots)
    summaries = []
    unexpected_total = 0

    extra_allow = {Path(p) for p in args.extra_allow or []} | _extra_allowlist_from_env()

    for root in roots:
        allowed = ALLOWLIST.get(root, {Path("src")}) | extra_allow
        entry = scan_root(root, allowed)
        summaries.append(entry)
        unexpected_total += len(entry.get("unexpected", []))

    if args.json:
        print(json.dumps(summaries, indent=2))
    else:
        for entry in summaries:
            print(format_report(entry))

    if getattr(args, "fail_on_unexpected", False) and unexpected_total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
