"""Return the most recent bounded smoke receipt from the sandbox receipt directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _find_latest_receipt(receipt_dir: Path) -> Path | None:
    if not receipt_dir.exists():
        return None
    latest_pointer = receipt_dir / "latest.json"
    if latest_pointer.exists() and latest_pointer.is_file():
        return latest_pointer
    candidates = [path for path in receipt_dir.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_receipt(receipt_path: Path) -> dict[str, Any]:
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Return the latest bounded smoke receipt.")
    parser.add_argument(
        "--receipt-dir",
        default=r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke\WareHouse\_smoke_receipts",
        help="Directory containing smoke receipt JSON files",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit only a compact summary instead of the full receipt payload",
    )
    args = parser.parse_args()

    receipt_dir = Path(args.receipt_dir).expanduser().resolve()
    latest = _find_latest_receipt(receipt_dir)
    if latest is None:
        print(
            json.dumps(
                {
                    "status": "missing",
                    "receipt_dir": str(receipt_dir),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1

    payload = _load_receipt(latest)
    if args.summary:
        payload = {
            "receipt_path": str(latest),
            "session_name": payload.get("session_name"),
            "status": payload.get("status"),
            "bounded_stop_reason": payload.get("bounded_stop_reason"),
            "first_artifact_path": payload.get("first_artifact_path"),
            "runtime_python": payload.get("runtime_python"),
            "elapsed_seconds": payload.get("elapsed_seconds"),
        }
    else:
        payload = {
            "receipt_path": str(latest),
            **payload,
        }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
