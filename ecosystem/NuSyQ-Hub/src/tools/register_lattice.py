"""Register a lattice JSON into docs/Vault/lattices_index.json.

This makes it easy to discover generated lattices for agents or manual
inspection. The script appends/updates an entry keyed by lattice name.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Register a lattice JSON into docs/Vault")
    parser.add_argument("lattice", help="Path to lattice JSON")
    args = parser.parse_args(argv)

    p = Path(args.lattice)
    if not p.exists():
        return 2

    data = json.loads(p.read_text(encoding="utf-8"))
    name = data.get("lattice") or p.stem

    idx_path = Path("docs/Vault/lattices_index.json")
    idx: dict[str, Any] = {}
    if idx_path.exists():
        try:
            idx = json.loads(idx_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            idx = {}

    idx[name] = {
        "path": str(p),
        "rev": data.get("rev"),
        "registered_at": datetime.now(UTC).isoformat(),
        "nodes_count": len(data.get("nodes", [])),
        "edges_count": len(data.get("edges", [])),
    }

    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
