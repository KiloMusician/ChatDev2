#!/usr/bin/env python
"""Export a simple event index (counts per tag/component) to Reports/events."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# pylint: disable=wrong-import-position
from src.telemetry.omnitag import export_event_index  # noqa: E402


def main() -> int:
    """Export event index with tag/component counts to Reports/events."""
    path = export_event_index()
    print(f"Exported event index to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
