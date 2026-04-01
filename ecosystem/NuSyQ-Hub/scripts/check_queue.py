#!/usr/bin/env python3
"""Check queue status and code gen tasks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator as BTO

bg = BTO()
stats = bg.get_queue_stats()
print("📊 Queue Status:")
print(f"   Queued: {stats['queued']}")
print(f"   Completed: {stats['completed']}")
print(f"   Failed: {stats['failed']}")
print(f"   Total: {stats['queued'] + stats['completed'] + stats['failed']}")
print()

# Find code generation tasks
queued = [t for t in bg.tasks.values() if t.status.name == "QUEUED"]
codegen = [t for t in queued if t.metadata and t.metadata.get("category") == "code_generation"]
print(f"📋 Code Gen Tasks: {len(codegen)} waiting")
if codegen:
    for t in codegen[:3]:
        print(f"   - {t.prompt[:65]}...")
    if len(codegen) > 3:
        print(f"   ... and {len(codegen) - 3} more")
