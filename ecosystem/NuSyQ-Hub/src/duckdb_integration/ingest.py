"""Stream JSONL state files into DuckDB.

Usage (example):
  python -m src.duckdb_integration.ingest --db-path ./data/state.duckdb --input SimulatedVerse/state/shared_cultivation/quest_log.jsonl

Features:
- Creates `events`, `quests`, and `questlines` tables (idempotent)
- Streams JSONL in batches to avoid high memory use
- Simple upsert: deletes matching PKs in batch then inserts fresh rows

Requirements: duckdb, pandas
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Iterable
from pathlib import Path

import duckdb
import pandas as pd

LOG = logging.getLogger("duckdb_ingest")


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            timestamp TIMESTAMP,
            event VARCHAR,
            details VARCHAR
        )
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS quests (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            description VARCHAR,
            questline VARCHAR,
            status VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            dependencies VARCHAR,
            tags VARCHAR,
            history VARCHAR,
            priority VARCHAR
        )
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS questlines (
            name VARCHAR PRIMARY KEY,
            description VARCHAR,
            tags VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )


def parse_jsonl_lines(lines: Iterable[str]) -> Iterable[dict]:
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            LOG.exception("failed to parse line: %s", line[:200])


def batch(iterable, size: int):
    buf = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def ingest_file(
    con: duckdb.DuckDBPyConnection, path: Path, batch_size: int = 1000, dry_run: bool = False
) -> None:
    # DuckDB connection objects don't expose a `.database` attribute across
    # all versions; avoid relying on it for logging to prevent AttributeError
    LOG.info("ingesting %s (batch_size=%d) -> duckdb_connection", path, batch_size)
    with path.open("r", encoding="utf-8") as fh:
        parsed = parse_jsonl_lines(fh)
        for b in batch(parsed, batch_size):
            # events insert
            events_rows = []
            quests_rows = []
            questline_rows = []
            for obj in b:
                ts = obj.get("timestamp")
                ev = obj.get("event")
                details = obj.get("details") or {}
                events_rows.append(
                    {
                        "timestamp": ts,
                        "event": ev,
                        "details": json.dumps(details, ensure_ascii=False),
                    }
                )

                if ev in ("add_quest", "update_quest_status") and isinstance(details, dict):
                    quests_rows.append(
                        {
                            "id": details.get("id"),
                            "title": details.get("title"),
                            "description": details.get("description"),
                            "questline": details.get("questline"),
                            "status": details.get("status"),
                            "created_at": details.get("created_at"),
                            "updated_at": details.get("updated_at"),
                            "dependencies": json.dumps(
                                details.get("dependencies", []), ensure_ascii=False
                            ),
                            "tags": json.dumps(details.get("tags", []), ensure_ascii=False),
                            "history": json.dumps(details.get("history", []), ensure_ascii=False),
                            "priority": details.get("priority"),
                        }
                    )

                if ev == "add_questline" and isinstance(details, dict):
                    questline_rows.append(
                        {
                            "name": details.get("name"),
                            "description": details.get("description"),
                            "tags": json.dumps(details.get("tags", []), ensure_ascii=False),
                            "created_at": details.get("created_at"),
                            "updated_at": details.get("updated_at"),
                        }
                    )

            # insert events
            if events_rows:
                df_events = pd.DataFrame(events_rows)
                if not dry_run:
                    con.register("_events_df", df_events)
                    con.execute(
                        "INSERT INTO events (timestamp,event,details) SELECT timestamp,event,details FROM _events_df"
                    )

            # upsert quests: delete existing ids then insert
            if quests_rows:
                dfq = pd.DataFrame([r for r in quests_rows if r.get("id")])
                ids = dfq["id"].tolist() if not dfq.empty else []
                if ids and not dry_run:
                    # delete existing
                    # build param list safely by creating a temporary table
                    con.register("_del_ids", pd.DataFrame({"id": ids}))
                    con.execute("DELETE FROM quests WHERE id IN (SELECT id FROM _del_ids)")
                    con.register("_quests_df", dfq)
                    con.execute("INSERT INTO quests SELECT * FROM _quests_df")

            # upsert questlines
            if questline_rows:
                dfql = pd.DataFrame(questline_rows)
                # delete by name then insert
                names = dfql["name"].tolist() if not dfql.empty else []
                if names and not dry_run:
                    con.register("_del_qnames", pd.DataFrame({"name": names}))
                    con.execute(
                        "DELETE FROM questlines WHERE name IN (SELECT name FROM _del_qnames)"
                    )
                    con.register("_questlines_df", dfql)
                    con.execute("INSERT INTO questlines SELECT * FROM _questlines_df")


def main(argv=None):
    p = argparse.ArgumentParser(description="Stream JSONL state files into DuckDB")
    p.add_argument("--db-path", type=Path, default=Path("./state.duckdb"), help="DuckDB file path")
    p.add_argument("--input", type=Path, required=True, help="Input JSONL file path")
    p.add_argument("--batch-size", type=int, default=1000)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    db_path = args.db_path
    input_path = args.input

    con = duckdb.connect(str(db_path))
    create_tables(con)

    if input_path.is_file():
        ingest_file(con, input_path, batch_size=args.batch_size, dry_run=args.dry_run)
    else:
        # if given a directory, iterate *.jsonl
        for fp in sorted(input_path.rglob("*.jsonl")):
            ingest_file(con, fp, batch_size=args.batch_size, dry_run=args.dry_run)

    con.close()


if __name__ == "__main__":
    main()
