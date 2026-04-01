#!/usr/bin/env python3
"""Find .gguf files across specified roots (safe dry-run discovery).

By default this script runs in dry-run mode and prints a JSON lines report to stdout
and to `state/reports/model_discovery_<timestamp>.ndjson` (if `state/reports` exists).

Usage examples:
  python scripts/find_ggufs.py --roots "C:\\Users\\keath" "D:\\" --limit 500 --dry-run
  python scripts/find_ggufs.py --auto-drives --limit 1000 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

EXCLUDE_DIRS = {
    "\\\\$Recycle.Bin",
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "node_modules",
    "AppData",
    "$RECYCLE.BIN",
}


def iter_drives() -> list[Path]:
    drives = []
    # common Windows drive letters
    for letter in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        p = Path(f"{letter}:/")
        if p.exists():
            drives.append(p)
    return drives


def should_skip_dir(path: Path) -> bool:
    name = path.name
    if name in EXCLUDE_DIRS:
        return True
    # skip hidden/system-ish dirs
    if name.startswith("."):
        return True
    return False


def find_ggufs(roots: Iterable[Path], limit: int = 1000):
    found = []
    for root in roots:
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                # mutate dirnames in place to skip excluded directories
                dirnames[:] = [d for d in dirnames if not should_skip_dir(Path(d))]
                for fn in filenames:
                    if fn.lower().endswith(".gguf"):
                        full = Path(dirpath) / fn
                        stat = None
                        try:
                            stat = full.stat()
                        except Exception:
                            pass
                        found.append(
                            {
                                "path": str(full),
                                "size": stat.st_size if stat else None,
                                "mtime": stat.st_mtime if stat else None,
                            }
                        )
                        if len(found) >= limit:
                            return found
        except PermissionError:
            continue
        except Exception:
            continue
    return found


def write_report(items, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"model_discovery_{ts}.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--roots", nargs="*", help="Roots to scan (paths)")
    p.add_argument("--auto-drives", action="store_true", help="Scan all mounted drives (may be slow)")
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--dry-run", action="store_true", default=True)
    args = p.parse_args()

    roots = []
    if args.auto_drives:
        roots = iter_drives()
    else:
        if not args.roots:
            # default safe roots
            home = Path.home()
            candidates = [home, Path("C:/Users"), Path("C:/")]
            roots = [p for p in candidates if p.exists()]
        else:
            roots = [Path(r) for r in args.roots if Path(r).exists()]

    print(f"Scanning roots: {[str(r) for r in roots]} (limit={args.limit})")
    items = find_ggufs(roots, limit=args.limit)
    print(f"Found {len(items)} .gguf files (reporting up to {args.limit})")
    # print sample
    for it in items[:200]:
        print(it["path"])

    # write report if state/reports exists or create it
    out_dir = Path("state") / "reports"
    if not out_dir.exists():
        print(f"Report directory {out_dir} does not exist; creating it.")
    try:
        out_path = write_report(items, out_dir)
        print(f"Wrote discovery report to {out_path}")
    except Exception as e:
        print(f"Failed to write report: {e}")

    if args.dry_run:
        print("Dry-run complete — no changes performed.")


if __name__ == "__main__":
    main()
