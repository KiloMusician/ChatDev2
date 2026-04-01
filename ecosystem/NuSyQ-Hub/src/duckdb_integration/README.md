# DuckDB integration (NuSyQ-Hub)

This small module provides a streaming JSONL -> DuckDB ingestion tool focused on
the `state/` files (event streams such as `quest_log.jsonl`). It creates three
tables: `events`, `quests`, and `questlines` and supports batched ingestion to
avoid high memory usage.

Quick start

1. Create a Python virtualenv and install dependencies (see repository policy
   for how you manage deps). A minimal set:

```bash
# from project root
python -m venv .venv_duckdb
. .venv_duckdb/Scripts/activate
pip install duckdb pandas
```

2. Run the ingester against a file:

```bash
python -m src.duckdb_integration.ingest --db-path ./data/state.duckdb --input SimulatedVerse/state/shared_cultivation/quest_log.jsonl --batch-size 1000
```

Notes

- The script uses a simple delete-then-insert upsert strategy per batch for
  `quests` and `questlines` to keep the implementation dependency-light and to
  be idempotent in repeated runs.
- For very large archives, point `--input` to a folder and the script will
  iterate all `*.jsonl` files.

Next steps

- Add a small dual-write helper for producers to write both JSONL and DuckDB
  (atomic append + insert)
- Add integration tests and CI steps
