"""Database Client MCP Bridge for NuSyQ ecosystem.

Provides integration with Database Client MCP tools for SQL database operations:
queries, schema inspection, and database management.

MCP Tool Prefix: dbclient-
Total Tools: 3

Primary Use Case: Inspecting NuSyQ state database (state/nusyq_state.db)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Database connection information."""

    path: Path
    db_type: str = "sqlite"
    exists: bool = False
    size_bytes: int = 0
    table_count: int = 0


@dataclass
class DBClientBridgeStatus:
    """DBClient bridge availability status."""

    available: bool
    nusyq_state_db: DatabaseInfo | None = None
    sqlite_available: bool = True
    message: str = ""


# ── MCP Tool Catalog ──────────────────────────────────────────────────────────

DBCLIENT_MCP_TOOLS: dict[str, dict[str, Any]] = {
    "execute-query": {
        "category": "query",
        "description": "Execute SQL queries and return results as structured data",
        "parameters": ["sql", "database"],
        "usage": "Run SELECT, INSERT, UPDATE, DELETE or other SQL statements",
        "examples": [
            "SELECT * FROM tasks LIMIT 10",
            "SELECT COUNT(*) FROM events",
            "PRAGMA table_info(tasks)",
        ],
    },
    "get-databases": {
        "category": "schema",
        "description": "List all available database connections",
        "parameters": [],
        "usage": "Discover which databases are configured and accessible",
    },
    "get-tables": {
        "category": "schema",
        "description": "List tables in a database with schema information",
        "parameters": ["database"],
        "usage": "Explore database structure, columns, and relationships",
    },
}


# ── Known Databases ───────────────────────────────────────────────────────────

NUSYQ_DATABASES: dict[str, dict[str, Any]] = {
    "nusyq_state": {
        "path": "state/nusyq_state.db",
        "description": "Primary NuSyQ state database (tasks, events, config)",
        "tables": ["tasks", "events", "config", "quest_state"],
    },
}


class DBClientBridge:
    """Bridge to Database Client MCP tools.

    Provides unified access to:
    - SQL query execution
    - Database schema inspection
    - Table discovery

    Primary use case: Inspecting NuSyQ state without direct SQLite access.
    """

    MCP_PREFIX = "dbclient-"

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize DBClient bridge.

        Args:
            workspace_root: Root path for database discovery. Defaults to CWD.
        """
        self.workspace_root = workspace_root or Path.cwd()
        self._status: DBClientBridgeStatus | None = None

    def probe(self) -> DBClientBridgeStatus:
        """Probe DBClient availability.

        Returns:
            DBClientBridgeStatus with availability details.
        """
        # Check if sqlite3 is available (it's in stdlib, should always work)
        sqlite_available = True
        try:
            import sqlite3
        except ImportError:
            sqlite_available = False

        # Check if NuSyQ state database exists
        state_db_path = self.workspace_root / "state" / "nusyq_state.db"
        nusyq_state_db = None

        if state_db_path.exists():
            table_count = 0
            try:
                conn = sqlite3.connect(str(state_db_path))
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass

            nusyq_state_db = DatabaseInfo(
                path=state_db_path,
                db_type="sqlite",
                exists=True,
                size_bytes=state_db_path.stat().st_size,
                table_count=table_count,
            )

        message = "DBClient MCP ready"
        if nusyq_state_db:
            size_mb = nusyq_state_db.size_bytes / (1024 * 1024)
            message = f"DBClient ready (nusyq_state.db: {size_mb:.1f}MB, {nusyq_state_db.table_count} tables)"

        self._status = DBClientBridgeStatus(
            available=True,  # MCP tools always available via extension
            sqlite_available=sqlite_available,
            nusyq_state_db=nusyq_state_db,
            message=message,
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _db = f"tables={nusyq_state_db.table_count}" if nusyq_state_db else "no_db"
            _emit(
                "agents",
                f"DBClient probe: sqlite={sqlite_available} {_db}",
                level="INFO",
                source="dbclient_bridge",
            )
        except Exception:
            pass

        return self._status

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific MCP tool.

        Args:
            tool_name: Tool name without prefix (e.g., 'execute-query').

        Returns:
            Tool metadata dict or None if not found.
        """
        return DBCLIENT_MCP_TOOLS.get(tool_name)

    def get_mcp_tool_name(self, tool: str) -> str:
        """Get full MCP tool name with prefix.

        Args:
            tool: Short tool name (e.g., 'execute-query').

        Returns:
            Full MCP name (e.g., 'dbclient-execute-query').
        """
        return f"{self.MCP_PREFIX}{tool}"

    def get_common_queries(self) -> list[dict[str, str]]:
        """Get common useful queries for NuSyQ state database.

        Returns:
            List of query suggestions with descriptions.
        """
        return [
            {
                "query": "SELECT * FROM sqlite_master WHERE type='table'",
                "description": "List all tables in database",
            },
            {
                "query": "SELECT COUNT(*) FROM tasks",
                "description": "Count total tasks",
            },
            {
                "query": "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 20",
                "description": "Recent tasks",
            },
            {
                "query": "SELECT * FROM events ORDER BY timestamp DESC LIMIT 50",
                "description": "Recent events",
            },
            {
                "query": "PRAGMA table_info(tasks)",
                "description": "Tasks table schema",
            },
            {
                "query": "SELECT status, COUNT(*) as count FROM tasks GROUP BY status",
                "description": "Task status distribution",
            },
        ]


# ── Module-Level Functions ────────────────────────────────────────────────────

_bridge: DBClientBridge | None = None


def get_bridge(workspace_root: Path | None = None) -> DBClientBridge:
    """Get or create DBClient bridge singleton.

    Args:
        workspace_root: Optional workspace root path.

    Returns:
        DBClientBridge instance.
    """
    global _bridge
    if _bridge is None:
        _bridge = DBClientBridge(workspace_root)
    return _bridge


def probe_dbclient() -> dict[str, Any]:
    """Probe DBClient availability for agent registry.

    Returns:
        Dict with status and detail for agent registry.
    """
    bridge = get_bridge()
    status = bridge.probe()

    db_info = ""
    if status.nusyq_state_db:
        size_mb = status.nusyq_state_db.size_bytes / (1024 * 1024)
        db_info = f", nusyq_state.db: {size_mb:.1f}MB"

    return {
        "status": "online" if status.available else "offline",
        "detail": f"DBClient MCP: {len(DBCLIENT_MCP_TOOLS)} tools{db_info}",
    }


def quick_status() -> str:
    """Get quick one-line status for display.

    Returns:
        Status string.
    """
    bridge = get_bridge()
    status = bridge.probe()

    if status.nusyq_state_db:
        size_mb = status.nusyq_state_db.size_bytes / (1024 * 1024)
        return f"DBClient: ONLINE - {len(DBCLIENT_MCP_TOOLS)} tools (state DB: {size_mb:.1f}MB)"
    return f"DBClient: ONLINE - {len(DBCLIENT_MCP_TOOLS)} tools (no state DB)"


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("DBClient MCP Bridge - NuSyQ Integration")
    print("=" * 60)

    bridge = get_bridge()
    status = bridge.probe()

    print(f"\nStatus: {'ONLINE' if status.available else 'OFFLINE'}")
    print(f"SQLite Available: {status.sqlite_available}")

    if status.nusyq_state_db:
        db = status.nusyq_state_db
        size_mb = db.size_bytes / (1024 * 1024)
        print("\nNuSyQ State Database:")
        print(f"  Path: {db.path}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Tables: {db.table_count}")
    else:
        print("\nNo NuSyQ state database found")

    print(f"\nTotal MCP Tools: {len(DBCLIENT_MCP_TOOLS)}")
    print("\nAvailable Tools:")
    for name, info in DBCLIENT_MCP_TOOLS.items():
        print(f"  - {bridge.get_mcp_tool_name(name)}: {info['description']}")

    print("\nCommon Queries for NuSyQ:")
    for q in bridge.get_common_queries()[:3]:
        print(f"  {q['description']}:")
        print(f"    {q['query']}")

    print(f"\nQuick Status: {quick_status()}")
