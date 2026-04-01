"""Reconciliation utilities to find and re-ingest events missing from DuckDB.

Strategy:
- Scan a JSONL stream and for each event check if a matching row exists in
  the `events` table by matching timestamp, event name, and details JSON text.
- For quest/questline events we also check the respective `quests`/`questlines`
  table to determine presence.
- Provide a replay function to insert missing rows idempotently using the
  existing `ingest.insert_single_event` helper.

This is a best-effort tool; it assumes the `events` table stores the raw
details JSON text (as produced by the ingester/dual-write helpers).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

import duckdb

LOG = logging.getLogger("duckdb_reconcile")


def iter_parsed_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                LOG.exception("failed to parse line: %s", line[:200])


def find_missing_events(con: duckdb.DuckDBPyConnection, jsonl_path: Path) -> list[dict]:
    """Return list of event objects present in JSONL but missing from DuckDB.

    Checks for existence by matching (timestamp,event,details) triple in the
    `events` table. For quest/questline events we also check the domain table
    (`quests`/`questlines`) for the key.
    """
    missing = []
    for obj in iter_parsed_jsonl(jsonl_path):
        ts = obj.get("timestamp")
        ev = obj.get("event")
        details = obj.get("details") or {}
        details_text = json.dumps(details, ensure_ascii=False)

        try:
            q = con.execute(
                "SELECT COUNT(*) FROM events WHERE timestamp = ? AND event = ? AND details = ?",
                [ts, ev, details_text],
            ).fetchone()[0]
        except Exception:
            # if events table doesn't exist or query fails, consider the row missing
            q = 0

        if q == 0:
            # additional checks for domain tables
            if ev in ("add_quest", "update_quest_status") and isinstance(details, dict):
                quest_id = details.get("id")
                if quest_id:
                    try:
                        cq = con.execute(
                            "SELECT COUNT(*) FROM quests WHERE id = ?", [quest_id]
                        ).fetchone()[0]
                    except Exception:
                        cq = 0
                    if cq > 0:
                        # quests table already has it (likely earlier insert), skip
                        continue
            if ev == "add_questline" and isinstance(details, dict):
                name = details.get("name")
                if name:
                    try:
                        cq = con.execute(
                            "SELECT COUNT(*) FROM questlines WHERE name = ?", [name]
                        ).fetchone()[0]
                    except Exception:
                        cq = 0
                    if cq > 0:
                        continue

            missing.append(obj)

    return missing


def replay_missing(jsonl_path: Path, db_path: Path, dry_run: bool = False) -> int:
    """Find missing events and insert them into DuckDB using existing helper.

    Returns the number of events inserted.
    """
    con = duckdb.connect(str(db_path))
    try:
        missing = find_missing_events(con, jsonl_path)
        LOG.info("found %d missing events", len(missing))
        if dry_run:
            return len(missing)

        from .dual_write import insert_single_event

        inserted = 0
        for obj in missing:
            try:
                insert_single_event(Path(db_path), obj)
                inserted += 1
            except Exception:
                LOG.exception("failed to insert missing event: %s", obj)

        return inserted
    finally:
        con.close()
