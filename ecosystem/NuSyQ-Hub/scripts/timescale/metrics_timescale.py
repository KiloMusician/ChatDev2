"""Lightweight TimescaleDB writer for quest/events metrics.

Features:
- Dual-write helper: keep JSONL as-is and optionally emit rows into quest_events.
- Safe-by-default: if Timescale is unreachable or psycopg2 is missing, we no-op with a warning.
- CLI utilities:
    * write-event          : emit a single quest event row
    * sync-quest-log       : backfill from quest_log.jsonl into quest_events

Environment (defaults shown):
    TS_HOST=127.0.0.1
    TS_PORT=5432
    TS_DB=consciousness
    TS_USER=nusyq
    TS_PASS=nusyq
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import Json
except Exception:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def get_conn():
    """Return a psycopg2 connection or None if unavailable."""
    if psycopg2 is None:
        return None
    try:
        return psycopg2.connect(
            host=_env("TS_HOST", "127.0.0.1"),
            port=int(_env("TS_PORT", "5432")),
            dbname=_env("TS_DB", "consciousness"),
            user=_env("TS_USER", "nusyq"),
            password=_env("TS_PASS", "nusyq"),
            connect_timeout=3,
        )
    except Exception:
        return None


def write_event(
    *,
    time: datetime,
    event_type: str,
    quest_id: str | None = None,
    questline: str | None = None,
    status: str | None = None,
    details: dict[str, Any] | None = None,
) -> bool:
    """Insert a single quest event row. Returns True on success, False on any failure/no-op."""
    conn = get_conn()
    if conn is None:
        return False
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO quest_events (time, event_type, quest_id, questline, status, details)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    time,
                    event_type,
                    quest_id,
                    questline,
                    status,
                    Json(details or {}),
                ),
            )
        return True
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def parse_quest_jsonl(path: Path) -> Iterable[tuple[datetime, dict[str, Any]]]:
    """Yield (timestamp, record) from a quest_log.jsonl file.
    Expects each line to be JSON with at least a timestamp field or falls back to now().
    """
    now = datetime.utcnow()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                continue
        except Exception:
            continue
        ts_raw = obj.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_raw) if ts_raw else now
        except Exception:
            ts = now
        yield ts, obj


def sync_quest_log(jsonl_path: Path) -> dict[str, Any]:
    """Backfill quest_log.jsonl into quest_events. Returns a summary dict."""
    if not jsonl_path.exists():
        return {"ok": False, "reason": f"Missing file: {jsonl_path}"}
    conn = get_conn()
    if conn is None:
        return {"ok": False, "reason": "Timescale not reachable or psycopg2 missing"}

    inserted = 0
    skipped = 0
    try:
        with conn, conn.cursor() as cur:
            for ts, obj in parse_quest_jsonl(jsonl_path):
                cur.execute(
                    """
                    INSERT INTO quest_events (time, event_type, quest_id, questline, status, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        ts,
                        obj.get("task_type") or obj.get("event_type") or "quest",
                        str(obj.get("id") or obj.get("quest_id") or obj.get("quest") or ""),
                        obj.get("questline") or obj.get("category"),
                        obj.get("status") or obj.get("state"),
                        Json(obj),
                    ),
                )
                inserted += 1
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"Insert failed: {exc}",
            "inserted": inserted,
            "skipped": skipped,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {"ok": True, "inserted": inserted, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Timescale quest/metrics writer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("write-event", help="Write a single quest event row")
    ev.add_argument("--event-type", required=True)
    ev.add_argument("--quest-id")
    ev.add_argument("--questline")
    ev.add_argument("--status")
    ev.add_argument("--details", help="JSON string for details", default="{}")
    ev.add_argument("--time", help="ISO8601 time (defaults to now)")

    sync = sub.add_parser("sync-quest-log", help="Backfill quest_log.jsonl into quest_events")
    sync.add_argument("--quest-log", type=Path, default=Path("src/Rosetta_Quest_System/quest_log.jsonl"))

    args = parser.parse_args()

    if args.cmd == "write-event":
        try:
            details = json.loads(args.details) if args.details else {}
        except Exception:
            details = {"raw_details": args.details}
        ts = datetime.fromisoformat(args.time) if getattr(args, "time", None) else datetime.utcnow()
        ok = write_event(
            time=ts,
            event_type=args.event_type,
            quest_id=args.quest_id,
            questline=args.questline,
            status=args.status,
            details=details,
        )
        if ok:
            print("Inserted")
        else:
            print("No-op (Timescale unreachable or error)")
    elif args.cmd == "sync-quest-log":
        summary = sync_quest_log(args.quest_log)
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
