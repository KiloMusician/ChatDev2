#!/usr/bin/env python3
"""NuSyQ Control Center entrypoint for packaging and local ops."""

from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("start-services")
    args = parser.parse_args()
    if args.cmd == "status":
        return run([sys.executable, "scripts/service_watch.py", "--json"])
    if args.cmd == "start-services":
        return run([sys.executable, "scripts/service_manager.py", "start_all"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
