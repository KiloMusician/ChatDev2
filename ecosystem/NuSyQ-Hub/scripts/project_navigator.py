#!/usr/bin/env python3
"""NuSyQ-Hub Project Navigator

Quickly explore, search, and summarize the project directory, modules, and documentation.
"""

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()


def list_dirs(path=ROOT, depth=2):
    for root, _dirs, files in os.walk(path):
        level = root.replace(str(path), "").count(os.sep)
        if level > depth:
            continue
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")


def main():
    parser = argparse.ArgumentParser(description="NuSyQ-Hub Project Navigator")
    parser.add_argument("--list", action="store_true", help="List project directories/files")
    parser.add_argument("--depth", type=int, default=2, help="Directory depth to display")
    args = parser.parse_args()

    if args.list:
        list_dirs(depth=args.depth)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
