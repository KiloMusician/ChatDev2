"""Unified AI Context Manager for cross-system context sharing.

This module provides centralized context management across all AI systems:
- GitHub Copilot
- Ollama (local LLMs)
- ChatDev
- Claude Code
- Custom consciousness systems

OmniTag: {
    "purpose": "Unified context management across all AI systems",
    "dependencies": ["agent_context_manager", "ecosystem_integrator", "quest_engine"],
    "context": "Enable consistent context across Copilot, Ollama, ChatDev, Claude",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Represents a single context entry."""

    id: str
    content: str
    context_type: str  # code, conversation, error, quest, knowledge
    source_system: str  # copilot, ollama, chatdev, claude, consciousness
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 1.0
    tags: list[str] = field(default_factory=list)


@dataclass
class AISystemContext:
    """Context specific to an AI system."""

    system_name: str
    status: str  # active, idle, error
    current_task: str | None = None
    recent_outputs: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    last_updated: str = ""


class UnifiedAIContextManager:
    """Unified context manager for all AI systems."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize unified context manager.

        Args:
            db_path: Path to SQLite database for context storage

        """
        self.db_path = db_path or Path("data/unified_ai_context.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connection pooling for better performance
        self._conn_pool: list[sqlite3.Connection] = []
        self._max_pool_size = 5
        self._pool_lock = threading.Lock()

        # Initialize database
        self._init_database()

        # In-memory cache for fast access
        self.context_cache: dict[str, ContextEntry] = {}
        self.system_contexts: dict[str, AISystemContext] = {}

        # Initialize system contexts
        self._init_system_contexts()

        logger.info("Unified AI Context Manager initialized with DB: %s", self.db_path)

    def _init_database(self) -> None:
        """Initialize SQLite database for context storage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create contexts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contexts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                context_type TEXT NOT NULL,
                source_system TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                relevance_score REAL DEFAULT 1.0,
                tags TEXT
            )
        """,
        )

        # Create system_status table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_status (
                system_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_task TEXT,
                recent_outputs TEXT,
                capabilities TEXT,
                last_updated TEXT NOT NULL
            )
        """,
        )

        # Create context_links table for relationships
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS context_links (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relationship_type)
            )
        """,
        )

        # Performance indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_type ON contexts(context_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_system ON contexts(source_system)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON contexts(timestamp DESC)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_context_links_source ON context_links(source_id)",
        )

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool or create a new one."""
        with self._pool_lock:
            if self._conn_pool:
                return self._conn_pool.pop()
        # Create new connection if pool is empty
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool."""
        with self._pool_lock:
            if len(self._conn_pool) < self._max_pool_size:
                self._conn_pool.append(conn)
            else:
                conn.close()

    def close_all_connections(self) -> None:
        """Close all pooled connections. Call on shutdown."""
        with self._pool_lock:
            for conn in self._conn_pool:
                conn.close()
            self._conn_pool.clear()

    def _init_system_contexts(self) -> None:
        """Initialize default AI system contexts."""
        systems = [
            AISystemContext(
                system_name="copilot",
                status="idle",
                capabilities=[
                    "code_completion",
                    "code_generation",
                    "documentation",
                    "refactoring",
                ],
                last_updated=datetime.now().isoformat(),
            ),
            AISystemContext(
                system_name="ollama",
                status="idle",
                capabilities=[
                    "code_generation",
                    "code_analysis",
                    "architecture_planning",
                    "debugging",
                ],
                last_updated=datetime.now().isoformat(),
            ),
            AISystemContext(
                system_name="chatdev",
                status="idle",
                capabilities=[
                    "multi_agent_development",
                    "consensus_building",
                    "code_review",
                    "testing",
                ],
                last_updated=datetime.now().isoformat(),
            ),
            AISystemContext(
                system_name="claude",
                status="idle",
                capabilities=[
                    "comprehensive_analysis",
                    "long_context_processing",
                    "architectural_design",
                    "documentation",
                ],
                last_updated=datetime.now().isoformat(),
            ),
            AISystemContext(
                system_name="consciousness",
                status="idle",
                capabilities=[
                    "error_memory",
                    "pattern_recognition",
                    "semantic_healing",
                    "knowledge_synthesis",
                ],
                last_updated=datetime.now().isoformat(),
            ),
        ]

        for system in systems:
            self.system_contexts[system.system_name] = system
            self._save_system_context(system)

    def add_context(
        self,
        content: str,
        context_type: str,
        source_system: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Add new context entry.

        Args:
            content: Context content
            context_type: Type of context (code, conversation, error, quest, knowledge)
            source_system: Source AI system
            metadata: Additional metadata
            tags: Context tags

        Returns:
            Context entry ID

        """
        context_id = f"{source_system}_{int(datetime.now().timestamp() * 1000)}"

        entry = ContextEntry(
            id=context_id,
            content=content,
            context_type=context_type,
            source_system=source_system,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            tags=tags or [],
        )

        # Save to database
        self._save_context_entry(entry)

        # Update cache
        self.context_cache[context_id] = entry

        logger.info(
            "Added context: %s from %s (type: %s)",
            context_id,
            source_system,
            context_type,
        )

        return context_id

    def get_context(self, context_id: str, use_cache: bool = True) -> ContextEntry | None:
        """Retrieve context by ID.

        Args:
            context_id: Context identifier
            use_cache: Use in-memory cache

        Returns:
            ContextEntry if found, None otherwise

        """
        # Try cache first
        if use_cache and context_id in self.context_cache:
            return self.context_cache[context_id]

        # Query database using connection pool
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contexts WHERE id = ?", (context_id,))
            row = cursor.fetchone()

            if not row:
                return None

            entry = ContextEntry(
                id=row[0],
                content=row[1],
                context_type=row[2],
                source_system=row[3],
                timestamp=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                relevance_score=row[6],
                tags=json.loads(row[7]) if row[7] else [],
            )

            # Update cache
            self.context_cache[context_id] = entry

            return entry
        finally:
            self._return_connection(conn)

    def get_contexts_by_type(self, context_type: str, limit: int = 100) -> list[ContextEntry]:
        """Get all contexts of a specific type.

        Args:
            context_type: Type to filter by
            limit: Maximum number of results

        Returns:
            list of ContextEntry objects

        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM contexts WHERE context_type = ? ORDER BY timestamp DESC LIMIT ?",
                (context_type, limit),
            )
            rows = cursor.fetchall()

            contexts: list[Any] = []
            for row in rows:
                entry = ContextEntry(
                    id=row[0],
                    content=row[1],
                    context_type=row[2],
                    source_system=row[3],
                    timestamp=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    relevance_score=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                )
                contexts.append(entry)

            return contexts
        finally:
            self._return_connection(conn)

    def get_contexts_by_system(self, system_name: str, limit: int = 100) -> list[ContextEntry]:
        """Get all contexts from a specific system.

        Args:
            system_name: System to filter by
            limit: Maximum number of results

        Returns:
            list of ContextEntry objects

        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM contexts WHERE source_system = ? ORDER BY timestamp DESC LIMIT ?",
                (system_name, limit),
            )
            rows = cursor.fetchall()

            contexts: list[Any] = []
            for row in rows:
                entry = ContextEntry(
                    id=row[0],
                    content=row[1],
                    context_type=row[2],
                    source_system=row[3],
                    timestamp=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    relevance_score=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                )
                contexts.append(entry)

            return contexts
        finally:
            self._return_connection(conn)

    def update_system_status(
        self,
        system_name: str,
        status: str,
        current_task: str | None = None,
        recent_output: str | None = None,
    ) -> None:
        """Update AI system status.

        Args:
            system_name: Name of AI system
            status: System status (active, idle, error)
            current_task: Current task description
            recent_output: Recent output to add

        """
        if system_name not in self.system_contexts:
            # Create new system context
            self.system_contexts[system_name] = AISystemContext(
                system_name=system_name,
                status=status,
                current_task=current_task,
                last_updated=datetime.now().isoformat(),
            )

        system = self.system_contexts[system_name]
        system.status = status
        system.last_updated = datetime.now().isoformat()

        if current_task:
            system.current_task = current_task

        if recent_output:
            system.recent_outputs.append(recent_output)
            # Keep only last 10 outputs
            if len(system.recent_outputs) > 10:
                system.recent_outputs = system.recent_outputs[-10:]

        # Save to database
        self._save_system_context(system)

        logger.info("Updated %s status: %s", system_name, status)
        try:
            from src.system.agent_awareness import emit as _emit

            _task = f" task={current_task[:50]!r}" if current_task else ""
            _emit(
                "agents",
                f"AIContextManager: {system_name} → {status}{_task}",
                level="INFO",
                source="unified_ai_context_manager",
            )
        except Exception:
            pass

    def get_system_status(self, system_name: str) -> AISystemContext | None:
        """Get status of an AI system.

        Args:
            system_name: Name of system

        Returns:
            AISystemContext if found

        """
        return self.system_contexts.get(system_name)

    def get_all_system_statuses(self) -> dict[str, AISystemContext]:
        """Get status of all AI systems.

        Returns:
            Dictionary of system name to AISystemContext

        """
        return self.system_contexts.copy()

    def create_context_link(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        strength: float = 1.0,
    ) -> None:
        """Create relationship between two contexts.

        Args:
            source_id: Source context ID
            target_id: Target context ID
            relationship_type: Type of relationship (related, caused_by, solution_for, etc.)
            strength: Relationship strength (0.0-1.0)

        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO context_links
                (source_id, target_id, relationship_type, strength)
                VALUES (?, ?, ?, ?)
            """,
                (source_id, target_id, relationship_type, strength),
            )
            conn.commit()
            logger.info("Created link: %s -> %s (%s)", source_id, target_id, relationship_type)
        finally:
            self._return_connection(conn)

    def get_related_contexts(
        self,
        context_id: str,
        relationship_type: str | None = None,
    ) -> list[ContextEntry]:
        """Get contexts related to a given context.

        Args:
            context_id: Context to find relationships for
            relationship_type: Optional filter by relationship type

        Returns:
            list of related ContextEntry objects

        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if relationship_type:
                cursor.execute(
                    """
                    SELECT c.* FROM contexts c
                    JOIN context_links l ON c.id = l.target_id
                    WHERE l.source_id = ? AND l.relationship_type = ?
                """,
                    (context_id, relationship_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT c.* FROM contexts c
                    JOIN context_links l ON c.id = l.target_id
                    WHERE l.source_id = ?
                """,
                    (context_id,),
                )

            rows = cursor.fetchall()

            contexts: list[Any] = []
            for row in rows:
                entry = ContextEntry(
                    id=row[0],
                    content=row[1],
                    context_type=row[2],
                    source_system=row[3],
                    timestamp=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    relevance_score=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                )
                contexts.append(entry)

            return contexts
        finally:
            self._return_connection(conn)

    def export_context_for_system(
        self,
        system_name: str,
        context_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Export relevant context for a specific AI system.

        Args:
            system_name: Target AI system
            context_types: Optional filter by context types

        Returns:
            Dictionary with formatted context

        """
        contexts = self.get_contexts_by_system(system_name, limit=50)

        # Filter by type if specified
        if context_types:
            contexts = [c for c in contexts if c.context_type in context_types]

        # Get system status
        system_status = self.get_system_status(system_name)

        ctx = {
            "system": system_name,
            "timestamp": datetime.now().isoformat(),
            "system_status": asdict(system_status) if system_status else None,
            "context_count": len(contexts),
            "contexts": [asdict(c) for c in contexts],
        }
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "system",
                f"AI context exported for {system_name}: {len(contexts)} entries",
                level="DEBUG",
                source="unified_ai_context_manager",
            )
        except Exception:
            pass
        return ctx

    def _save_context_entry(self, entry: ContextEntry) -> None:
        """Save context entry to database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO contexts
                (id, content, context_type, source_system, timestamp, metadata, relevance_score, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.id,
                    entry.content,
                    entry.context_type,
                    entry.source_system,
                    entry.timestamp,
                    json.dumps(entry.metadata),
                    entry.relevance_score,
                    json.dumps(entry.tags),
                ),
            )
            conn.commit()
        finally:
            self._return_connection(conn)

    def _save_system_context(self, system: AISystemContext) -> None:
        """Save system context to database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO system_status
                (system_name, status, current_task, recent_outputs, capabilities, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    system.system_name,
                    system.status,
                    system.current_task,
                    json.dumps(system.recent_outputs),
                    json.dumps(system.capabilities),
                    system.last_updated,
                ),
            )
            conn.commit()
        finally:
            self._return_connection(conn)


# Global instance for easy access
_global_context_manager: UnifiedAIContextManager | None = None


def get_unified_context_manager() -> UnifiedAIContextManager:
    """Get or create global unified context manager.

    Returns:
        Global UnifiedAIContextManager instance

    """
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = UnifiedAIContextManager()
    return _global_context_manager
