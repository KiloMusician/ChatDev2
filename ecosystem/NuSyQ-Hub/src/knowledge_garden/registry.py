#!/usr/bin/env python3
"""State Registry - Foundation of Living Knowledge Ecosystem.

Single source of truth for ALL system artifacts (quests, PUs, proofs, changelogs, logs, ideas).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Types
Status = Literal["queued", "active", "paused", "archived", "revived", "completed"]
ArtifactType = Literal["quest", "pu", "proof", "changelog", "log", "idea", "error"]


@dataclass
class LifecycleEvent:
    """Single event in artifact lifecycle."""

    timestamp: str
    event: str  # 'created', 'queued', 'started', 'paused', 'completed', 'revived'
    actor: str  # Who/what triggered
    reason: str | None = None


@dataclass
class Lineage:
    """Provenance and relationships."""

    parent: str | None = None  # Forked from
    children: list[str] = field(default_factory=list)  # Forked into
    siblings: list[str] = field(default_factory=list)  # Related work


@dataclass
class Artifact:
    """Core artifact model."""

    id: str
    type: ArtifactType
    title: str
    summary: str
    status: Status

    # Temporal
    created_at: str
    updated_at: str
    completed_at: str | None = None
    last_accessed: str | None = None

    # Semantic
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Provenance
    references: list[str] = field(default_factory=list)
    lineage: Lineage | None = None

    # Content
    content: Any = None
    version: int = 1

    # Lifecycle
    lifecycle_events: list[LifecycleEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        return data


class StateRegistry:
    """State Registry - manages all artifacts."""

    def __init__(self, db_path: str | Path = "state/knowledge_garden.db"):
        """Initialize registry with SQLite database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return dicts

        self._create_tables()

    def _create_tables(self):
        """Create database schema."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                last_accessed TEXT,
                tags TEXT,  -- JSON array
                metadata TEXT,  -- JSON object
                artifact_references TEXT,  -- JSON array
                lineage TEXT,  -- JSON object
                content TEXT,  -- JSON
                version INTEGER DEFAULT 1,
                lifecycle_events TEXT  -- JSON array
            )
        """
        )

        # Indexes for fast queries
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON artifacts(type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON artifacts(status)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON artifacts(created_at DESC)")

        self.conn.commit()

    def create(self, artifact: Artifact) -> Artifact:
        """Create new artifact."""
        # Ensure ID
        if not artifact.id:
            artifact.id = str(uuid.uuid4())

        # Ensure timestamps
        now = datetime.now().isoformat()
        if not artifact.created_at:
            artifact.created_at = now
        artifact.updated_at = now

        # Add creation event
        artifact.lifecycle_events.append(
            LifecycleEvent(timestamp=now, event="created", actor="system")
        )

        # Insert
        self.conn.execute(
            """
            INSERT INTO artifacts (
                id, type, title, summary, status,
                created_at, updated_at, completed_at, last_accessed,
                tags, metadata, artifact_references, lineage, content, version, lifecycle_events
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                artifact.id,
                artifact.type,
                artifact.title,
                artifact.summary,
                artifact.status,
                artifact.created_at,
                artifact.updated_at,
                artifact.completed_at,
                artifact.last_accessed,
                json.dumps(artifact.tags),
                json.dumps(artifact.metadata),
                json.dumps(artifact.references),
                json.dumps(asdict(artifact.lineage)) if artifact.lineage else None,
                json.dumps(artifact.content),
                artifact.version,
                json.dumps([asdict(e) for e in artifact.lifecycle_events]),
            ),
        )

        self.conn.commit()
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        """Get artifact by ID."""
        cursor = self.conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_artifact(row)

    def update(self, artifact_id: str, updates: dict[str, Any]) -> Artifact | None:
        """Update artifact."""
        artifact = self.get(artifact_id)
        if not artifact:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(artifact, key):
                setattr(artifact, key, value)

        # Update timestamp
        artifact.updated_at = datetime.now().isoformat()

        # Save
        self.conn.execute(
            """
            UPDATE artifacts SET
                type = ?, title = ?, summary = ?, status = ?,
                updated_at = ?, completed_at = ?, last_accessed = ?,
                tags = ?, metadata = ?, artifact_references = ?, lineage = ?,
                content = ?, version = ?, lifecycle_events = ?
            WHERE id = ?
        """,
            (
                artifact.type,
                artifact.title,
                artifact.summary,
                artifact.status,
                artifact.updated_at,
                artifact.completed_at,
                artifact.last_accessed,
                json.dumps(artifact.tags),
                json.dumps(artifact.metadata),
                json.dumps(artifact.references),
                json.dumps(asdict(artifact.lineage)) if artifact.lineage else None,
                json.dumps(artifact.content),
                artifact.version,
                json.dumps([asdict(e) for e in artifact.lifecycle_events]),
                artifact_id,
            ),
        )

        self.conn.commit()
        return artifact

    def query(
        self,
        type_: ArtifactType | None = None,
        status: Status | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Artifact]:
        """Query artifacts with filters."""
        conditions: list[str] = []
        params: list[str | int] = []

        if type_:
            conditions.append("type = ?")
            params.append(type_)

        if status:
            conditions.append("status = ?")
            params.append(status)

        base_query = "SELECT * FROM artifacts"
        if conditions:
            where_clause = " AND ".join(conditions)
            query = f"{base_query} WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
        else:
            query = f"{base_query} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        artifacts = [self._row_to_artifact(row) for row in rows]

        # Filter by tags if provided
        if tags:
            artifacts = [a for a in artifacts if any(tag in a.tags for tag in tags)]

        return artifacts

    def count(self, type_: ArtifactType | None = None, status: Status | None = None) -> int:
        """Count artifacts with filters."""
        conditions: list[str] = []
        params: list[str] = []

        if type_:
            conditions.append("type = ?")
            params.append(type_)

        if status:
            conditions.append("status = ?")
            params.append(status)

        base_query = "SELECT COUNT(*) as count FROM artifacts"
        if conditions:
            where_clause = " AND ".join(conditions)
            query = f"{base_query} WHERE {where_clause}"
        else:
            query = base_query

        cursor = self.conn.execute(query, params)

        result = cursor.fetchone()
        return int(result["count"]) if result else 0

    def delete(self, artifact_id: str, soft: bool = True) -> bool:
        """Delete artifact (soft delete to 'archived' by default)."""
        if soft:
            # Soft delete - just archive
            artifact = self.get(artifact_id)
            if artifact:
                new_status: Status = "archived"
                artifact.status = new_status
                artifact.lifecycle_events.append(
                    LifecycleEvent(
                        timestamp=datetime.now().isoformat(),
                        event="archived",
                        actor="system",
                        reason="Soft delete",
                    )
                )
                self.update(artifact_id, {"status": new_status})
                return True
        else:
            # Hard delete
            self.conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
            self.conn.commit()
            return True

        return False

    def _row_to_artifact(self, row: sqlite3.Row) -> Artifact:
        """Convert database row to Artifact object."""
        lineage_data = json.loads(row["lineage"]) if row["lineage"] else None

        return Artifact(
            id=row["id"],
            type=row["type"],
            title=row["title"],
            summary=row["summary"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            last_accessed=row["last_accessed"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            references=json.loads(row["artifact_references"]) if row["artifact_references"] else [],
            lineage=Lineage(**lineage_data) if lineage_data else None,
            content=json.loads(row["content"]) if row["content"] else None,
            version=row["version"],
            lifecycle_events=(
                [LifecycleEvent(**e) for e in json.loads(row["lifecycle_events"])]
                if row["lifecycle_events"]
                else []
            ),
        )

    def close(self):
        """Close database connection."""
        self.conn.close()


# Global registry instance
_registry: StateRegistry | None = None


def get_registry() -> StateRegistry:
    """Get global registry instance."""
    global _registry
    if _registry is None:
        _registry = StateRegistry()
    return _registry


if __name__ == "__main__":
    # Test the registry
    registry = StateRegistry("state/knowledge_garden_test.db")

    # Create test artifact
    artifact = Artifact(
        id="test-001",
        type="quest",
        title="Test Quest",
        summary="This is a test quest",
        status="queued",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        tags=["test", "demo"],
        metadata={"cost": 5},
    )

    registry.create(artifact)
    logger.info(f"✅ Created artifact: {artifact.id}")

    # Query
    results = registry.query(type_="quest", status="queued")
    logger.info(f"✅ Found {len(results)} queued quests")

    # Update
    registry.update("test-001", {"status": "completed"})
    logger.info("✅ Updated artifact status")

    # Get
    updated = registry.get("test-001")
    if updated:
        logger.info(f"✅ Retrieved artifact, status: {updated.status}")
    else:
        logger.error("❌ Failed to retrieve artifact")

    registry.close()
