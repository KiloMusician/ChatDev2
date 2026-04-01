#!/usr/bin/env python3
"""Strip markdown fences (```...```) from PowerShell watcher files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_watcher_root(raw_root: str | None) -> Path:
    """Resolve watcher directory from arg/env/repo defaults."""
    if raw_root:
        return Path(raw_root).expanduser().resolve()

    env_value = os.environ.get("NUSYQ_TERMINAL_WATCHERS") or os.environ.get("SIMULATEDVERSE_TERMINAL_WATCHERS")
    if env_value:
        return Path(env_value).expanduser().resolve()

    candidates = [
        REPO_ROOT / "data" / "terminal_watchers",
        REPO_ROOT.parent / "SimulatedVerse" / "SimulatedVerse" / "data" / "terminal_watchers",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def clean_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean markdown fences from watcher .ps1 scripts",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Watcher directory (default: auto-detect from NuSyQ/SimulatedVerse locations)",
    )
    args = parser.parse_args()

    root = resolve_watcher_root(args.root)
    if not root.exists():
        print(f"Watcher directory not found: {root}")
        return 1

    cleaned = []
    for p in sorted(root.glob("*.ps1")):
        clean_file(p)
        cleaned.append(p)
        print("cleaned:", p)
    print(f"Cleaned {len(cleaned)} files in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
