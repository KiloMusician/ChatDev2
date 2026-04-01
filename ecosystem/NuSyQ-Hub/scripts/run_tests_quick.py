"""Deprecated shim: delegates to `friendly_test_runner.py --mode quick`.

This keeps backward compatibility while the canonical runner lives in
`scripts/friendly_test_runner.py`.
"""

import subprocess
import sys
from pathlib import Path


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    runner = Path(__file__).resolve().parents[0] / "friendly_test_runner.py"
    cmd = [sys.executable, str(runner), "--mode", "quick", *list(argv)]
    print("Delegating to friendly_test_runner quick mode...")
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
