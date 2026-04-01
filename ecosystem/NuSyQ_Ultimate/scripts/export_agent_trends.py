#!/usr/bin/env python
"""Export per-agent performance trends to Reports/metrics.

Useful for ad-hoc snapshots or scheduled runs via a VS Code task.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Best-effort wire terminal logging for metrics export
try:
    from src.system.init_terminal import init_terminal_logging

    try:
        init_terminal_logging(channel="Export-Agent-Trends", level=logging.INFO)
    except (OSError, RuntimeError, ValueError, TypeError):
        pass
except (ImportError, OSError, RuntimeError):
    pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# pylint: disable=wrong-import-position
from mcp_server.performance_metrics import get_metrics  # noqa: E402


def main() -> int:
    """Export agent performance trends to Reports/metrics."""
    pm = get_metrics()
    path = pm.export_agent_trends()
    print(f"Exported agent trends to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
