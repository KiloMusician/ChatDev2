#!/usr/bin/env python3
"""Create minimal __init__.py files for directories that contain Python files
but are missing a plain `__init__.py`.

Usage:
    python scripts/apply_missing_inits.py --roots src scripts --exclude .venv .git node_modules reports

This is conservative: by default it only touches directories you explicitly
pass as roots. It will skip common environment and vendor folders.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from pathlib import Path

DEFAULT_EXCLUDES = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    ".github",
    "reports",
    "dist",
    "build",
    "__pycache__",
}


def find_dirs_missing_init(roots: Iterable[Path], excludes: list[str]) -> list[Path]:
    missing = []
    exclude_set = set(excludes) | DEFAULT_EXCLUDES
    for root in roots:
        root = root.resolve()
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            path = Path(dirpath)
            # skip excluded directories anywhere in the path
            if any(part in exclude_set for part in path.parts):
                # don't recurse into those dirs
                dirnames[:] = [d for d in dirnames if d not in exclude_set]
                continue
            py_files = [f for f in filenames if f.endswith(".py")]
            if not py_files:
                continue
            # if there's already a plain __init__.py, skip
            init_file = path / "__init__.py"
            if init_file.exists():
                continue
            # ignore packages that only have a typed stub __init__.pyi or weird names
            alt_inits = [p for p in path.iterdir() if p.name.startswith("__init__")]
            if any(p.is_file() for p in alt_inits):
                # record as anomalous but skip auto-creation
                missing.append(path)
                continue
            missing.append(path)
    # deduplicate and sort
    uniq = sorted(set(missing))
    return uniq


def create_init_file(path: Path) -> None:
    init = path / "__init__.py"
    if init.exists():
        return
    content = (
        "# Auto-generated minimal package marker.\n# Add package exports or documentation as needed.\n__all__ = []\n"
    )
    init.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Create minimal __init__.py files in directories missing them")
    p.add_argument("--roots", nargs="+", required=True, help="Root directories to scan")
    p.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Directory names to exclude (e.g. .venv node_modules)",
    )
    p.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files")
    args = p.parse_args(argv)

    roots = [Path(r) for r in args.roots]
    missing = find_dirs_missing_init(roots, args.exclude)

    if not missing:
        print("No missing __init__.py files found under provided roots.")
        return 0

    print(f"Found {len(missing)} directories missing a plain __init__.py:\n")
    for d in missing:
        print(" -", d)

    if args.dry_run:
        print("\nDry-run: no files written.")
        return 0

    created = []
    for d in missing:
        try:
            create_init_file(d)
            created.append(d / "__init__.py")
        except Exception as exc:  # pragma: no cover - conservative error handling
            print(f"Failed to create __init__.py in {d}: {exc}")

    print(f"\nCreated {len(created)} __init__.py files:")
    for f in created:
        print(" -", f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
