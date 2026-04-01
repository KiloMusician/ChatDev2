#!/usr/bin/env python3
"""Rollback registry entries and remove created junctions/hard-links.

Usage:
  python scripts/rollback_registration.py --path <path> [--yes]
  python scripts/rollback_registration.py --name <model-name> [--yes]

This will attempt to remove the filesystem object (directory junction or file
hard-link) and then remove the entry from `state/registry.json` using the
ModelRegistry's underlying save routine.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.shared.model_registry import ModelRegistry


def find_entries_by_path(reg: ModelRegistry, path: str) -> list[dict]:
    return [i for i in reg._load() if i.get("path") == path]


def find_entries_by_name(reg: ModelRegistry, name: str) -> list[dict]:
    return [i for i in reg._load() if i.get("name") == name]


def remove_filesystem(path_str: str) -> bool:
    p = Path(path_str)
    if not p.exists() and not p.is_symlink():
        print(f"[warn] target does not exist: {path_str}")
        return False

    try:
        if p.is_dir():
            # directory junction or directory
            # os.rmdir will remove junctions on Windows
            os.rmdir(p)
            print(f"[ok] removed directory/junction: {path_str}")
            return True
        else:
            # file or hard-link
            p.unlink()
            print(f"[ok] removed file/hard-link: {path_str}")
            return True
    except Exception as exc:
        print(f"[error] failed to remove {path_str}: {exc}")
        return False


def remove_registry_entries(reg: ModelRegistry, entries: list[dict]) -> int:
    if not entries:
        return 0
    data = reg._load()
    paths = {e.get("path") for e in entries}
    new = [i for i in data if i.get("path") not in paths]
    reg._save_atomic(new)
    return len(entries)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Exact path to remove (file or directory)")
    parser.add_argument("--name", help="Model name to remove from registry")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive actions")
    args = parser.parse_args()

    if not args.path and not args.name:
        parser.error("one of --path or --name is required")

    reg = ModelRegistry()
    entries = []

    if args.path:
        entries = find_entries_by_path(reg, args.path)
    else:
        entries = find_entries_by_name(reg, args.name)

    if not entries:
        print("No matching registry entries found.")
        return

    print("Found entries:")
    for e in entries:
        print(f" - {e.get('name')} @ {e.get('path')}")

    if not args.yes:
        ans = input("Proceed with removal? (y/N): ").strip().lower()
        if ans != "y":
            print("Aborted by user.")
            return

    removed_fs = 0
    for e in entries:
        p = e.get("path")
        if p:
            if remove_filesystem(p):
                removed_fs += 1

    removed_entries = remove_registry_entries(reg, entries)
    print(f"Removed filesystem objects: {removed_fs}; registry entries removed: {removed_entries}")


if __name__ == "__main__":
    main()
