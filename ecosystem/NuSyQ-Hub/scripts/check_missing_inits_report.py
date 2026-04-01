"""Scan for Python packages missing __init__.py and write a markdown report.

Usage:
  python scripts/check_missing_inits_report.py --roots src . --output reports/missing_init_report.md

This script is safe to run repeatedly and will create the `reports/` folder if missing.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def find_python_dirs(root: Path) -> list[Path]:
    dirs_with_py = set()
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                dirs_with_py.add(Path(dirpath))
                break
    return sorted(dirs_with_py)


def scan(roots: list[Path]) -> dict:
    missing = []
    anomalies = []

    for root in roots:
        if not root.exists():
            continue
        py_dirs = find_python_dirs(root)
        for d in py_dirs:
            init = d / "__init__.py"
            if not init.exists():
                # check for suspicious variants
                variants = [p.name for p in d.iterdir() if p.name.startswith("__init__")]
                if variants:
                    anomalies.append((str(d), variants))
                else:
                    missing.append(str(d))

    return {"missing": sorted(set(missing)), "anomalies": sorted(set(anomalies))}


def write_report(result: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("# Missing __init__.py Report\n\n")
        f.write(f"Generated: {Path.cwd()}\n\n")

        missing = result.get("missing", [])
        anomalies = result.get("anomalies", [])

        f.write("## Summary\n\n")
        f.write(f"- Directories scanned: {len(missing) + len(anomalies)} (reported missing or anomalous)\n\n")

        if missing:
            f.write("## Directories missing __init__.py\n\n")
            for d in missing:
                f.write(f"- {d}\n")
            f.write("\n")
        else:
            f.write("No directories missing a plain __init__.py were found.\n\n")

        if anomalies:
            f.write("## Suspicious anomalies (files starting with __init__)\n\n")
            for d, variants in anomalies:
                f.write(f"- {d}: {', '.join(variants)}\n")
            f.write("\n")

        f.write("## Recommended actions\n\n")
        f.write(
            "- For each directory listed under 'Directories missing __init__.py', create an empty `__init__.py` to make it a package (or add appropriate package metadata).\n"
        )
        f.write(
            "- For anomalies, inspect and rename any mistakenly named files such as `__init___.py` to `__init__.py`.\n\n"
        )
        f.write("### Example commands\n\n")
        f.write("PowerShell:\n\n")
        f.write("```powershell\nNew-Item -ItemType File -Path ./path/to/dir/__init__.py -Force\n```\n\n")
        f.write("POSIX / Git Bash / WSL:\n\n")
        f.write("```bash\nmkdir -p ./path/to/dir && touch ./path/to/dir/__init__.py\n```\n")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--roots", nargs="+", default=["src"], help="Root folders to scan (relative to repo root)")
    p.add_argument("--output", default="reports/missing_init_report.md", help="Output markdown report")
    return p.parse_args()


def main():
    args = parse_args()
    roots = [Path(r) for r in args.roots]
    result = scan(roots)
    write_report(result, Path(args.output))
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
