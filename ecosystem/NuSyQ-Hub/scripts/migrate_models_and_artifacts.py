"""Migrate model registry and artifact lists into SQL tables.

This script looks for `state/registry.json` and `state/artifacts.json` (if present)
and imports entries into `models` and `artifacts` tables.
"""

import json
from pathlib import Path

from src.task_runtime.db import Database


def migrate_models(db: Database, registry_path: Path) -> int:
    if not registry_path.exists():
        print("No registry.json at", registry_path)
        return 0
    with registry_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    inserted = 0
    for entry in data.get("models", []) if isinstance(data, dict) else data:
        provider = entry.get("provider") or entry.get("source") or "local"
        name = entry.get("name") or entry.get("id")
        local_path = entry.get("path") or entry.get("local_path")
        meta = json.dumps(entry)
        db.execute(
            "INSERT INTO models (provider, name, local_path, metadata) VALUES (?, ?, ?, ?)",
            (provider, name, local_path, meta),
        )
        inserted += 1
    print(f"Inserted {inserted} models")
    return inserted


def migrate_artifacts(db: Database, artifacts_path: Path) -> int:
    if not artifacts_path.exists():
        print("No artifacts.json at", artifacts_path)
        return 0
    with artifacts_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    inserted = 0
    for a in data:
        path = a.get("path") or a.get("file")
        type_ = a.get("type") or a.get("kind")
        project_id = a.get("project_id")
        db.execute(
            "INSERT INTO artifacts (project_id, path, type) VALUES (?, ?, ?)",
            (project_id, path, type_),
        )
        inserted += 1
    print(f"Inserted {inserted} artifacts")
    return inserted


def main():
    repo_root = Path(__file__).resolve().parents[1]
    db = Database()
    registry = repo_root / "state" / "registry.json"
    artifacts = repo_root / "state" / "artifacts.json"
    migrate_models(db, registry)
    migrate_artifacts(db, artifacts)


if __name__ == "__main__":
    main()
