#!/usr/bin/env python3
"""Deprecated shim: delegates to canonical friendly_test_runner.py in CI mode.

This legacy comprehensive test runner has been consolidated into
`scripts/friendly_test_runner.py --mode ci`.

For backwards compatibility, this shim maintains the old interface while
delegating to the modern canonical runner.

Legacy usage (deprecated):
    python src/diagnostics/comprehensive_test_runner.py

Modern usage (recommended):
    python scripts/friendly_test_runner.py --mode ci
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    runner_path = Path(__file__).resolve().parents[2] / "scripts" / "friendly_test_runner.py"

    if not runner_path.exists():
        logger.error(f"Error: canonical runner not found at {runner_path}")
        return 1

    logger.warning("⚠️  comprehensive_test_runner.py is deprecated.")
    logger.info(f"Delegating to {runner_path} --mode ci")
    logger.info()

    cmd = [sys.executable, str(runner_path), "--mode", "ci"]
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
