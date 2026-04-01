#!/usr/bin/env python3
"""Culture Ship / Rosetta Stone summary (Phase 8 prelude)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.system.knowledge import load_patterns


def main() -> None:
    report_path = Path("state/reports/culture_ship_summary.json")
    data = {
        "patterns": load_patterns(),
        "notes": "Culture Ship / Rosetta Stone placeholder summary",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
