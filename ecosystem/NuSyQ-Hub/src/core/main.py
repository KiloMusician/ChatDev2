#!/usr/bin/env python3
"""Legacy redirect for NuSyQ-Hub main entry point.

Canonical implementation:
    src/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import NuSyQHubMain
from src.spine import initialize_spine

logger = logging.getLogger(__name__)


def main() -> int:
    """Entry point wrapper for legacy CLI usage."""
    try:
        initialize_spine(repo_root=Path(__file__).resolve().parents[1])
    except Exception as exc:
        logger.warning("Spine init failed in core entry: %s", exc)
    app = NuSyQHubMain()
    return app.main()


if __name__ == "__main__":
    raise SystemExit(main())
