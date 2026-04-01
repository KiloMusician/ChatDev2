#!/usr/bin/env python3
"""Run contract/subprocess tests without coverage gates."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    args = sys.argv[1:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        "no_cov",
        "-p",
        "no:cov",
        "-o",
        "addopts=",
    ]
    cmd.extend(args)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
