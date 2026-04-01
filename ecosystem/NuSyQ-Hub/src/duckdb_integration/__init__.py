"""DuckDB integration package for NuSyQ-Hub.

Provides streaming JSONL → DuckDB ingestion for NuSyQ state files
(events.jsonl, guild_events.jsonl, etc.). Supports dual-write to both
JSONL and DuckDB for query-friendly analytics, with optional TimescaleDB
real-time streaming.

OmniTag: {
    "purpose": "duckdb_integration",
    "tags": ["DuckDB", "JSONL", "Ingestion", "Analytics", "Streaming"],
    "category": "data_infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "append_to_jsonl",
    "dual_write",
    "ingest_file",
]


def __getattr__(name: str):
    if name in ("ingest_file",):
        from src.duckdb_integration.ingest import ingest_file

        return ingest_file
    if name in ("dual_write", "append_to_jsonl"):
        from src.duckdb_integration.dual_write import (append_to_jsonl,
                                                       dual_write)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
