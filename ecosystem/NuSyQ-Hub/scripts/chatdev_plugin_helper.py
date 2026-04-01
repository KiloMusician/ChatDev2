#!/usr/bin/env python3
"""Utility to inspect and document ChatDev integration for NuSyQ."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from pathlib import Path


def discover_chatdev_roots() -> list[Path]:
    """Return candidate paths where ChatDev might live."""
    candidates: Iterable[Path] = (
        Path(os.environ["CHATDEV_ROOT"]) if "CHATDEV_ROOT" in os.environ else Path(),
        (Path(os.environ["SIMULATEDVERSE_ROOT"]) / "ChatDev" if "SIMULATEDVERSE_ROOT" in os.environ else Path()),
        Path.home() / "NuSyQ" / "ChatDev",
        Path.home() / "Desktop" / "NuSyQ" / "ChatDev",
    )

    roots = []
    for candidate in candidates:
        if not candidate or not candidate.exists():
            continue
        roots.append(candidate.resolve())

    return roots


def print_status(roots: list[Path], warehouse_projects: list[str]):
    if not roots:
        print("⚠️  No ChatDev installation detected.")
        print("  * Set CHATDEV_ROOT to your cloned ChatDev repo.")
        print("  * Or create a symlink from NuSyQ/ChatDev into your workspace.")
        print("See docs/ChatDev_Plugin_Layer.md for plugin guidance.")
        return

    for root in roots:
        print(f"✅ ChatDev root detected at {root}")
        warehouse = root / "WareHouse"
        if warehouse.exists():
            print(f"  Warehouse projects ({warehouse_projects or 'all'}) live under: {warehouse}")
        else:
            print(
                "  Warehouse directory not found; run `python scripts/chatdev_plugin_helper.py --print-instructions` for suggestions."
            )


def print_instructions():
    print("Plugin integration tips:")
    print('- Add ChatDev to PYTHONPATH only when you need it: `export PYTHONPATH="$CHATDEV_ROOT/src:$PYTHONPATH"`')
    print("- Use `python scripts/chatdev_plugin_helper.py --warehouse-projects pvz` to focus audits.")
    print("- If you want NuSyQ to import from ChatDev, set `CHATDEV_ROOT` before launching.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect ChatDev installations for NuSyQ plugin workflows.")
    parser.add_argument(
        "--warehouse-projects",
        nargs="*",
        default=[],
        help="Search for specific warehouse project folders when scanning.",
    )
    parser.add_argument(
        "--print-instructions",
        action="store_true",
        help="Print integration reminders and environment hints.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roots = discover_chatdev_roots()
    print_status(roots, args.warehouse_projects)
    if args.print_instructions:
        print()
        print_instructions()


if __name__ == "__main__":
    main()
