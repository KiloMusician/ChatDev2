#!/usr/bin/env python3
"""Batch update SimulatedVerse bridge imports to use unified bridge."""

import re
import sys
from pathlib import Path

# Files to update (excluding build contexts)
TARGET_FILES = [
    "src/evolution/consolidated_system.py",
    "src/orchestration/chatdev_development_orchestrator.py",
    "tests/integration/test_simulatedverse_bridge_real.py",
    "src/automation/auto_theater_audit.py",
    "src/automation/autonomous_monitor.py",
    "src/automation/unified_pu_queue.py",
    "src/automation/ollama_validation_pipeline.py",
    "src/orchestration/autonomous_quest_orchestrator.py",
    "scripts/autonomous_modernization_execution.py",
    "scripts/comprehensive_modernization_audit.py",
    "scripts/execute_remaining_pus.py",
    "scripts/test_culture_ship_integration.py",
]

# Import replacement patterns
REPLACEMENTS = [
    # simulatedverse_async_bridge → simulatedverse_unified_bridge
    (
        r"from\s+(?:src\.)?integration\.simulatedverse_async_bridge\s+import\s+SimulatedVerseBridge",
        "from src.integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge as SimulatedVerseBridge",
    ),
    (
        r"from\s+\.\.integration\.simulatedverse_async_bridge\s+import\s+SimulatedVerseBridge",
        "from ..integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge as SimulatedVerseBridge",
    ),
    # simulatedverse_bridge → simulatedverse_unified_bridge
    (
        r"from\s+(?:src\.)?integration\.simulatedverse_bridge\s+import\s+SimulatedVerseBridge",
        "from src.integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge as SimulatedVerseBridge",
    ),
    (
        r"from\s+\.\.integration\.simulatedverse_bridge\s+import\s+SimulatedVerseBridge",
        "from ..integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge as SimulatedVerseBridge",
    ),
    # simulatedverse_enhanced_bridge → simulatedverse_unified_bridge
    (
        r"from\s+(?:src\.)?integration\.simulatedverse_enhanced_bridge\s+import\s+SimulatedVerseEnhancedBridge",
        "from src.integration.simulatedverse_unified_bridge import SimulatedVerseUnifiedBridge",
    ),
]


def update_file(file_path: Path) -> bool:
    """Update imports in a single file."""
    if not file_path.exists():
        print(f"⚠️  Skipping (not found): {file_path}")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        # Check if file was modified
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    """Update all target files."""
    hub_root = Path(__file__).parent.parent

    print("=" * 80)
    print("🔄 UPDATING SIMULATEDVERSE BRIDGE IMPORTS")
    print("=" * 80)
    print(f"Hub Root: {hub_root}")
    print(f"Target Files: {len(TARGET_FILES)}")
    print("=" * 80 + "\n")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for file_path_str in TARGET_FILES:
        file_path = hub_root / file_path_str

        if update_file(file_path):
            updated_count += 1
        elif file_path.exists():
            skipped_count += 1
        else:
            error_count += 1

    print("\n" + "=" * 80)
    print("📊 BRIDGE IMPORT UPDATE SUMMARY")
    print("=" * 80)
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ⏭️  No Changes: {skipped_count}")
    print(f"  ❌ Errors/Not Found: {error_count}")
    print(f"  📁 Total Files: {len(TARGET_FILES)}")
    print("=" * 80 + "\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
