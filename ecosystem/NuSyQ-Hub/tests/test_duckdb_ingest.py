import json
from pathlib import Path

import duckdb
from src.duckdb_integration import ingest


def make_sample_jsonl(path: Path):
    lines = [
        {
            "timestamp": "2025-12-30T23:11:30.305916+00:00",
            "event": "add_questline",
            "details": {
                "name": "TestLine",
                "description": "desc",
                "tags": [],
                "created_at": "2025-12-30T23:11:30.305916+00:00",
                "updated_at": "2025-12-30T23:11:30.305916+00:00",
            },
        },
        {
            "timestamp": "2025-12-30T23:11:30.409485+00:00",
            "event": "add_quest",
            "details": {
                "id": "abc-123",
                "title": "T1",
                "description": "d",
                "questline": "TestLine",
                "status": "pending",
                "created_at": "2025-12-30T23:11:30.409485+00:00",
                "updated_at": "2025-12-30T23:11:30.409485+00:00",
                "dependencies": [],
                "tags": [],
            },
        },
        {
            "timestamp": "2025-12-30T23:11:30.413054+00:00",
            "event": "update_quest_status",
            "details": {
                "id": "abc-123",
                "title": "T1",
                "description": "d",
                "questline": "TestLine",
                "status": "active",
                "created_at": "2025-12-30T23:11:30.409485+00:00",
                "updated_at": "2025-12-30T23:11:30.412043+00:00",
                "dependencies": [],
                "tags": [],
            },
        },
    ]
    path.write_text(
        "\n".join(json.dumps(line, ensure_ascii=False) for line in lines),
        encoding="utf-8",
    )


def test_ingest_basic(tmp_path: Path):
    jsonl = tmp_path / "sample.jsonl"
    make_sample_jsonl(jsonl)

    db = tmp_path / "state.duckdb"
    con = duckdb.connect(str(db))
    try:
        ingest.create_tables(con)
        ingest.ingest_file(con, jsonl, batch_size=2, dry_run=False)

        ev_count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        assert ev_count == 3

        q_count = con.execute("SELECT COUNT(*) FROM quests").fetchone()[0]
        # quest was added once; update replaces same id
        assert q_count == 1

        ql_count = con.execute("SELECT COUNT(*) FROM questlines").fetchone()[0]
        assert ql_count == 1
    finally:
        con.close()
