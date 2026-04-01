#!/usr/bin/env python3
"""Mirror the NuSyQ spine health snapshot into downstream repositories."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_repo_path(env_var: str, fallback: Path) -> Path | None:
    env_path = os.environ.get(env_var)
    if env_path:
        return Path(env_path).expanduser()
    if fallback and fallback.exists():
        return fallback
    return None


def _read_snapshot(snapshot_path: Path) -> dict:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Spine snapshot missing at {snapshot_path}")
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def _mirror_snapshot(snapshot: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    logger.info("Mirrored snapshot to %s", destination)


def get_default_targets(hub_root: Path) -> dict[str, Path]:
    result = {
        "hub_feed": hub_root / "state" / "feeds" / "nu_spine_health.json",
    }
    root_candidate = _resolve_repo_path("NUSYQ_ROOT_PATH", hub_root.parent / "NuSyQ")
    if root_candidate:
        result["nusyq_root"] = root_candidate / "state" / "feeds" / "nu_spine_health.json"
    sim_candidate = _resolve_repo_path("SIMULATEDVERSE_PATH", hub_root.parent / "SimulatedVerse" / "SimulatedVerse")
    if sim_candidate:
        result["simulatedverse"] = sim_candidate / "state" / "feeds" / "nu_spine_health.json"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror the NuSyQ spine health JSON into downstream repos.")
    parser.add_argument(
        "--hub-root",
        type=Path,
        help="Path to NuSyQ-Hub (defaults to repository root).",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        type=Path,
        help="Explicit target paths to write the snapshot.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only log via logging instead of printing summary.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    hub_root = args.hub_root or Path(__file__).resolve().parents[1]
    snapshot_path = hub_root / "state" / "reports" / "spine_health_snapshot.json"
    try:
        snapshot = _read_snapshot(snapshot_path)
    except Exception as exc:
        logger.error("Unable to read spine snapshot: %s", exc)
        return 1

    targets = args.targets or []
    if not targets:
        defaults = get_default_targets(hub_root)
        targets.extend(defaults.values())

    if not targets:
        logger.warning("No mirror targets configured; nothing to do.")
        return 0

    for target in targets:
        try:
            _mirror_snapshot(snapshot, target)
        except Exception as exc:
            logger.error("Failed to write snapshot to %s: %s", target, exc)
            return 1

    if not args.quiet:
        print(f"Mirrored spine snapshot to {len(targets)} location(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
