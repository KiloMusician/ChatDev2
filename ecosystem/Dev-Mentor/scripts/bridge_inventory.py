#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.bridge_inventory import build_bridge_inventory, save_bridge_inventory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate bridge inventory for IDE and claw-family surfaces"
    )
    parser.add_argument(
        "--json", action="store_true", help="Print inventory JSON to stdout"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write state/bridge_inventory.json",
    )
    args = parser.parse_args()

    inventory = build_bridge_inventory()
    if not args.no_save:
        save_bridge_inventory(inventory)
    if args.json:
        print(json.dumps(inventory, indent=2))
    else:
        print(
            f"[bridge-inventory] {inventory['summary']['installed']}/{inventory['summary']['total']} surfaces installed"
        )
        print(
            f"[bridge-inventory] first-class: {', '.join(inventory['summary']['first_class']) or 'none'}"
        )


if __name__ == "__main__":
    main()
