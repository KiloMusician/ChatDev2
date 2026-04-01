#!/usr/bin/env python3
"""Consume and mirror the NuSyQ spine health snapshot for downstream orchestrators."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _find_hub_path(cli_root: Path | None = None) -> Path:
    if cli_root:
        return cli_root

    env_root = os.environ.get("NUSYQ_HUB_PATH")
    if env_root:
        return Path(env_root).expanduser()

    # Fallback search: neighbor directory
    default = Path(__file__).resolve().parents[1]
    neighbor = default.parent / "NuSyQ-Hub"
    if neighbor.exists():
        return neighbor
    return default


def load_snapshot(hub_root: Path) -> dict[str, Any]:
    snapshot_path = hub_root / "state" / "reports" / "spine_health_snapshot.json"
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Spine snapshot not found at {snapshot_path}")

    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to read snapshot: {exc}") from exc

    return data


def summarize_snapshot(snapshot: dict[str, Any]) -> str:
    status = snapshot.get("status", "unknown")
    timestamp = snapshot.get("timestamp", "unknown")
    signals = snapshot.get("signals", {})
    lines = snapshot.get("current_state_excerpt", [])
    lifecycle = snapshot.get("lifecycle_entries", [])

    parts = [
        f"Spine Status: {status}",
        f"Captured: {timestamp}",
        f"Current state lines: {signals.get('current_state_lines', 0)}",
        f"Lifecycle entries: {signals.get('lifecycle_entries', 0)}",
        f"Latest line: {lines[0] if lines else 'N/A'}",
        f"Lifecycle sample: {lifecycle[0] if lifecycle else 'N/A'}",
    ]
    return "\n".join(parts)


def mirror_snapshot(snapshot: dict[str, Any], export_path: Path | None) -> Path | None:
    if not export_path:
        return None

    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return export_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read the hub spine health snapshot and optionally mirror it elsewhere."
    )
    parser.add_argument(
        "--hub-root",
        type=Path,
        help="Path to NuSyQ-Hub checkout (uses NUSYQ_HUB_PATH or ../NuSyQ-Hub by default)",
    )
    parser.add_argument(
        "--mirror",
        type=Path,
        help="Destination path for copying the spine snapshot (e.g., NuSyQ Root state/feeds/)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only log summary via INFO/DEBUG; suppress stdout extra text.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    hub_root = _find_hub_path(args.hub_root)
    try:
        snapshot = load_snapshot(hub_root)
    except Exception as exc:
        logger.error("Unable to read spine snapshot: %s", exc)
        return 1

    summary = summarize_snapshot(snapshot)
    if not args.quiet:
        print(summary)
    else:
        logger.info(summary)

    if args.mirror:
        mirror_path = mirror_snapshot(snapshot, args.mirror)
        if mirror_path:
            logger.info("Mirrored spine snapshot to %s", mirror_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
