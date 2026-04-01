#!/usr/bin/env python3
r"""Cleanup Duplicate Evolution Files

Deletes the duplicate files created by mistake and keeps the proper integration.

Files to DELETE (duplicates of existing superior systems):
- src/evolution/ai_council.py → Use c:\Users\keath\NuSyQ\config\ai_council.py
- src/evolution/chatdev_integrator.py → Use src/culture_ship_real_action.py
- src/evolution/complete_evolution_orchestrator.py → Use src/orchestration/multi_ai_orchestrator.py
- src/evolution/README.md → References wrong systems

Files to KEEP:
- src/evolution/consolidated_system.py → Proper integration
- src/evolution/progress_tracker.py → Unique functionality
- src/evolution/system_evolution_auditor.py → Needs assessment first
- INTEGRATION_ANALYSIS.md → Documentation
- EVOLUTION_INTEGRATION_SUCCESS.md → Success report
"""

import shutil
from datetime import datetime
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent

# Backup directory
BACKUP_DIR = REPO_ROOT / "data" / "cleanup_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")

# Files to delete (duplicates)
DUPLICATES_TO_DELETE = [
    "src/evolution/ai_council.py",
    "src/evolution/chatdev_integrator.py",
    "src/evolution/complete_evolution_orchestrator.py",
    "src/evolution/README.md",
    "src/evolution/proper_integration.py",  # Incomplete - replaced by consolidated_system.py
]

# Files to keep
FILES_TO_KEEP = [
    "src/evolution/consolidated_system.py",
    "src/evolution/progress_tracker.py",
    "src/evolution/system_evolution_auditor.py",
    "INTEGRATION_ANALYSIS.md",
    "EVOLUTION_INTEGRATION_SUCCESS.md",
]


def backup_and_delete():
    """Backup duplicates before deleting"""
    print("\n" + "=" * 70)
    print(" CLEANUP DUPLICATE EVOLUTION FILES")
    print("=" * 70 + "\n")

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[BACKUP] Created: {BACKUP_DIR}\n")

    # Backup and delete each duplicate
    deleted_count = 0
    for filepath in DUPLICATES_TO_DELETE:
        full_path = REPO_ROOT / filepath

        if full_path.exists():
            # Backup
            backup_path = BACKUP_DIR / filepath
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_path, backup_path)
            print(f"[BACKUP] {filepath}")

            # Delete
            full_path.unlink()
            print(f"[DELETE] {filepath}\n")
            deleted_count += 1
        else:
            print(f"[SKIP] {filepath} (not found)\n")

    print("=" * 70)
    print(f" CLEANUP COMPLETE: {deleted_count} files deleted")
    print("=" * 70 + "\n")

    print(f"[BACKUP] All deleted files saved to: {BACKUP_DIR}\n")

    # List files that were kept
    print("Files KEPT (proper integration):")
    for filepath in FILES_TO_KEEP:
        full_path = REPO_ROOT / filepath
        if full_path.exists():
            print(f"  ✅ {filepath}")
        else:
            print(f"  ⚠️  {filepath} (not found)")

    print("\n" + "=" * 70)
    print(" Next Steps:")
    print("=" * 70)
    print("1. Use src/evolution/consolidated_system.py for all evolution tasks")
    print("2. Assess system_evolution_auditor.py vs. existing 10+ auditors")
    print("3. Fix Culture Ship import issues")
    print("4. Fix Multi-AI Orchestrator import issues")
    print("5. Test full autonomous evolution cycle")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    backup_and_delete()
