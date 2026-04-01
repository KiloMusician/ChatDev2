"""Realtime Status Queries via DuckDB.

Provides fast SQL queries for realtime system status instead of generating
thousands of unused report files.
"""

from pathlib import Path
from typing import Any

import duckdb


class RealtimeStatus:
    """Query realtime system status from DuckDB."""

    def __init__(self, db_path: str | Path = "data/state.duckdb"):
        """Initialize RealtimeStatus with db_path."""
        self.db_path = Path(db_path)

    def _conn(self) -> duckdb.DuckDBPyConnection:
        """Get database connection."""
        return duckdb.connect(str(self.db_path))

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent system events."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT timestamp, event, details FROM events ORDER BY timestamp DESC LIMIT ?",
            [limit],
        ).fetchall()
        return [{"timestamp": r[0], "event": r[1], "details": r[2]} for r in rows]

    def get_active_quests(self) -> list[dict[str, Any]]:
        """Get all active quests."""
        conn = self._conn()
        rows = conn.execute(
            """
            SELECT id, title, status, priority, created_at, updated_at
            FROM quests
            WHERE status IN ('OPEN', 'IN_PROGRESS')
            ORDER BY priority DESC, created_at DESC
            """
        ).fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "status": r[2],
                "priority": r[3],
                "created_at": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ]

    def get_quest_stats(self) -> dict[str, int]:
        """Get quest statistics."""
        conn = self._conn()
        result = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'DONE' THEN 1 ELSE 0 END) as done,
                SUM(CASE WHEN status = 'ABANDONED' THEN 1 ELSE 0 END) as abandoned
            FROM quests
            """
        ).fetchone()
        return {
            "total": result[0] or 0,
            "open": result[1] or 0,
            "in_progress": result[2] or 0,
            "done": result[3] or 0,
            "abandoned": result[4] or 0,
        }

    def get_event_counts_by_type(self, hours: int = 24) -> dict[str, int]:
        """Get event counts by type in the last N hours."""
        conn = self._conn()
        rows = conn.execute(
            f"""
            SELECT event, COUNT(*) as count
            FROM events
            WHERE timestamp >= current_timestamp - INTERVAL {hours} HOUR
            GROUP BY event
            ORDER BY count DESC
            """
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def query_custom(self, sql: str, params: list | None = None) -> list[tuple]:
        """Execute custom SQL query."""
        conn = self._conn()
        if params:
            return conn.execute(sql, params).fetchall()
        return conn.execute(sql).fetchall()


# Singleton instance
_status: RealtimeStatus | None = None


def get_realtime_status() -> RealtimeStatus:
    """Get or create singleton RealtimeStatus instance."""
    global _status
    if _status is None:
        _status = RealtimeStatus()
    return _status
