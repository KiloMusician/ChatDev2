#!/usr/bin/env python3
"""prune_tmpclaude.py

Scan workspace roots for leftover tmpclaude-* directories and remove them.
Usage: python scripts/prune_tmpclaude.py [--roots PATH [PATH ...]] [--dry-run] [--yes]
"""

import argparse
import fnmatch
import shutil
from pathlib import Path


def find_tmpclaude_dirs(root: Path):
    matches = []
    for p in root.rglob("*"):
        if p.is_dir():
            name = p.name
            if fnmatch.fnmatch(name, "tmpclaude*") or fnmatch.fnmatch(name, "tmpclaude-*"):
                matches.append(p)
    return matches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="*", help="Root paths to scan", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help="Delete without prompt")
    args = ap.parse_args()

    if args.roots:
        roots = [Path(p).expanduser().resolve() for p in args.roots]
    else:
        # sensible defaults: repo root and sibling repos if present
        cwd = Path.cwd()
        roots = [cwd]

    all_matches = []
    for r in roots:
        if not r.exists():
            continue
        found = find_tmpclaude_dirs(r)
        all_matches.extend(found)

    if not all_matches:
        print("No tmpclaude-* directories found.")
        return

    print("Found the following tmpclaude directories:")
    for d in all_matches:
        print(" -", d)

    if args.dry_run:
        print("\nDry-run: no deletions performed.")
        return

    if not args.yes:
        ans = input("\nDelete these directories? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return

    for d in all_matches:
        try:
            shutil.rmtree(d)
            print("Deleted", d)
        except Exception as e:
            print("Failed to delete", d, e)


if __name__ == "__main__":
    main()
