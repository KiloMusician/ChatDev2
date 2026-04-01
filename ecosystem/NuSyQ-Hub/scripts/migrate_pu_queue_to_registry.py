#!/usr/bin/env python3
"""Migrate pu_queue.theater.backup to Living Knowledge Registry

Extracts 21,274 tasks from backup file and imports into State Registry.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledge_garden.registry import Artifact, StateRegistry


def rename_references_recursive(obj):
    """Recursively rename all 'references' keys to 'pu_references' in dicts/lists."""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            new_key = "pu_references" if k == "references" else k
            new_obj[new_key] = rename_references_recursive(v)
        return new_obj
    if isinstance(obj, list):
        return [rename_references_recursive(i) for i in obj]
    return obj


def parse_pu_queue_line(line: str) -> dict | None:
    """Parse single line from pu_queue backup."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def convert_pu_to_artifact(pu: dict) -> Artifact:
    """Convert PU task to Artifact."""
    # Recursively rename 'references' keys
    pu = rename_references_recursive(pu)

    # Map PU fields to Artifact
    artifact = Artifact(
        id=pu.get("id", ""),
        type="pu",
        title=pu.get("summary", "Untitled PU"),
        summary=pu.get("summary", ""),
        status=pu.get("status", "queued"),
        created_at=datetime.fromtimestamp(pu.get("createdAt", 0) / 1000).isoformat(),
        updated_at=datetime.now().isoformat(),
        completed_at=None,
        tags=[pu.get("kind", "unknown").lower()],
        metadata={
            "kind": pu.get("kind"),
            "cost": pu.get("cost", 0),
            "payload": pu.get("payload", {}),
            "msg": pu.get("msg"),
            "proof": pu.get("proof"),
        },
        content=pu,  # Store original PU data
    )

    # Add completed timestamp if done
    if pu.get("status") == "done" and "proof" in pu:
        proof = pu["proof"]
        if "verification_timestamp" in proof:
            artifact.completed_at = datetime.fromtimestamp(proof["verification_timestamp"] / 1000).isoformat()

    return artifact


def migrate_pu_queue(backup_path: Path, registry: StateRegistry):
    """Migrate all PUs from backup to registry."""
    print(f"🔄 Migrating PUs from: {backup_path}")

    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return

    stats = {"total": 0, "queued": 0, "unverified": 0, "done": 0, "errors": 0}

    with open(backup_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 1000 == 0:
                print(f"   Processing line {line_num}...", end="\r")

            pu = parse_pu_queue_line(line)
            if not pu:
                stats["errors"] += 1
                continue

            artifact = convert_pu_to_artifact(pu)
            try:
                registry.create(artifact)
            except Exception as e:
                if "UNIQUE constraint failed: artifacts.id" in str(e):
                    import uuid

                    artifact.id = str(uuid.uuid4())
                    try:
                        registry.create(artifact)
                    except Exception as e2:
                        print(f"\n⚠️  Error on line {line_num} (after new ID): {e2}")
                        stats["errors"] += 1
                        continue
                else:
                    print(f"\n⚠️  Error on line {line_num}: {e}")
                    stats["errors"] += 1
                    continue

            stats["total"] += 1
            stats[pu.get("status", "unknown")] = stats.get(pu.get("status", "unknown"), 0) + 1

    print("\n\n✅ Migration complete!")
    print("\n📊 Statistics:")
    print(f"   Total migrated: {stats['total']}")
    print(f"   Queued (unstarted): {stats.get('queued', 0)}")
    print(f"   Unverified (completed but not proven): {stats.get('unverified', 0)}")
    print(f"   Done (completed & verified): {stats.get('done', 0)}")
    print(f"   Errors: {stats['errors']}")

    return stats


def main():
    """Main migration script."""
    print("🌱 PU Queue → Living Knowledge Registry Migration")
    print("=" * 60)

    # Accept backup file path as argument
    backup_paths = []
    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1])
        backup_paths.append(arg_path)
    # Default search locations
    backup_paths.extend(
        [
            Path("/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/data/pu_queue.theater.backup"),
            Path("../SimulatedVerse/SimulatedVerse/data/pu_queue.theater.backup"),
            Path("data/pu_queue.theater.backup"),
        ]
    )

    backup_path = None
    for path in backup_paths:
        if path.exists():
            backup_path = path
            break

    if not backup_path:
        print("❌ Could not find pu_queue.theater.backup")
        print("   Searched:")
        for path in backup_paths:
            print(f"   - {path}")
        sys.exit(1)

    # Initialize registry
    registry = StateRegistry()

    # Check if already migrated
    existing_pus = registry.count(type="pu")
    if existing_pus > 0:
        print(f"⚠️  Registry already contains {existing_pus} PUs")
        response = input("   Continue and add more? (y/n): ")
        if response.lower() != "y":
            print("Migration cancelled")
            sys.exit(0)

    # Migrate
    migrate_pu_queue(backup_path, registry)

    # Query examples
    print("\n🔍 Query Examples:")

    queued = registry.query(type="pu", status="queued", limit=5)
    print("\n   📋 Top 5 Queued PUs:")
    for pu in queued:
        cost = pu.metadata.get("cost", 0)
        kind = pu.metadata.get("kind", "unknown")
        print(f"      [{kind}] {pu.title} (cost: {cost})")

    # 'unverified' is not a valid status, so skip or adjust this query if needed
    # unverified = registry.query(type="pu", status="unverified", limit=5)
    # print("\n   ⚠️  Top 5 Unverified PUs:")
    # for pu in unverified:
    #     kind = pu.metadata.get("kind", "unknown")
    #     print(f"      [{kind}] {pu.title}")

    # High-value queued work
    all_queued = registry.query(type="pu", status="queued", limit=1000)
    high_value = sorted(all_queued, key=lambda p: p.metadata.get("cost", 0), reverse=True)[:10]

    print("\n   🏆 Top 10 High-Value Queued Work:")
    for pu in high_value:
        cost = pu.metadata.get("cost", 0)
        kind = pu.metadata.get("kind", "unknown")
        print(f"      [{kind}] {pu.title} (cost: {cost})")

    registry.close()

    print("\n✨ Registry is now live at: state/knowledge_garden.db")
    print("   Access via: from knowledge_garden.registry import get_registry")


if __name__ == "__main__":
    main()
