#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from agents.serena import SerenaAgent
from agents.serena.drift import DriftDetector

STATUS_PATH = BASE / "state" / "serena_status.json"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a Serena walk/drift/align cycle and persist status."
    )
    parser.add_argument("--mode", choices=["full", "scoped"], default="scoped")
    parser.add_argument("--scope", default="app/game_engine")
    args = parser.parse_args()

    serena = SerenaAgent(repo_root=BASE)
    walk_summary = serena.walk("full") if args.mode == "full" else serena.fast_walk()

    detector = DriftDetector(
        repo_root=BASE, db_path=BASE / "state" / "serena_memory.db"
    )
    signals = detector.detect_all(scope=args.scope, fast=True)
    align = detector.align_check()

    payload = {
        "ts": now_iso(),
        "mode": args.mode,
        "scope": args.scope,
        "walk": walk_summary,
        "align": align,
        "drift": {
            "critical": sum(1 for s in signals if s.severity == "critical"),
            "warn": sum(1 for s in signals if s.severity == "warn"),
            "info": sum(1 for s in signals if s.severity == "info"),
            "signals": [
                {
                    "category": s.category,
                    "severity": s.severity,
                    "path": s.path,
                    "message": s.message,
                    "auto_fix": s.auto_fix,
                }
                for s in signals[:50]
            ],
        },
        "agent_status": serena.get_status(),
    }

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
