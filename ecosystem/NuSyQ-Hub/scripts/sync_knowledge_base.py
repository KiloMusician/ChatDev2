#!/usr/bin/env python3
"""Auto-sync knowledge-base.yaml from NuSyQ to Hub for unified access."""

import shutil
from datetime import datetime
from pathlib import Path


def sync_knowledge_base() -> bool:
    """Sync knowledge base from NuSyQ to Hub."""
    source = Path("C:/Users/keath/NuSyQ/knowledge-base.yaml")
    dest = Path.cwd() / "state" / "knowledge" / "knowledge-base.yaml"

    dest.parent.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        print(f"❌ Source knowledge-base.yaml not found: {source}")
        return False

    try:
        shutil.copy2(source, dest)

        # Create timestamp marker
        timestamp_file = dest.parent / ".last_sync"
        with open(timestamp_file, "w") as f:
            f.write(datetime.now().isoformat())

        print("✓ Knowledge base synced from NuSyQ")
        print(f"  Source: {source}")
        print(f"  Dest: {dest}")
        print(f"  Size: {dest.stat().st_size} bytes")
        return True

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return False


if __name__ == "__main__":
    success = sync_knowledge_base()
    exit(0 if success else 1)
