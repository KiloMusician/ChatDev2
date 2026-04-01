#!/usr/bin/env python
"""Deprecated shim: delegates to canonical friendly_test_runner.py.

This legacy safe test runner has been consolidated into
`scripts/friendly_test_runner.py --mode quick`.

For backwards compatibility, this shim maintains the old interface while
delegating to the modern canonical runner.

Legacy usage (deprecated):
    python scripts/run_tests_safely.py tests/

Modern usage (recommended):
    python scripts/friendly_test_runner.py --mode quick tests/
"""

import subprocess
import sys
from pathlib import Path


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    runner = Path(__file__).resolve().parents[0] / "friendly_test_runner.py"
    cmd = [sys.executable, str(runner), "--mode", "quick", *list(argv)]

    print("⚠️  run_tests_safely.py is deprecated.")
    print("Delegating to friendly_test_runner quick mode...")
    print()

    proc = subprocess.run(cmd, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
