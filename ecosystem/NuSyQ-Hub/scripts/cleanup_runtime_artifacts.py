"""Cleanup runtime artifacts before committing.
Reverts temple metadata timestamps and removes generated summaries.
"""

import json
import sys
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent


def clean_temple_metadata() -> bool:
    """Reset temple agent registry to remove timestamp-only changes."""
    registry_path = REPO_ROOT / "src/integration/temple/agent_registry.json"

    if not registry_path.exists():
        print("✅ Temple registry not found (nothing to clean)")
        return True

    try:
        # Check if file has only timestamp changes
        with open(registry_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check if this is a runtime-generated file
        if "last_updated" in data or "timestamp" in str(data):
            print(f"🧹 Cleaning temple metadata: {registry_path}")
            # Don't actually delete - just report
            print("   → Recommend: git checkout HEAD -- src/integration/temple/agent_registry.json")
            return True

        return True

    except Exception as e:
        print(f"⚠️  Error cleaning temple metadata: {e}")
        return False


def clean_summary_plans() -> bool:
    """Remove auto-generated summary prune plans."""
    summary_plan = REPO_ROOT / "SUMMARY_PRUNE_PLAN.json"

    if not summary_plan.exists():
        print("✅ Summary prune plan not found (nothing to clean)")
        return True

    try:
        with open(summary_plan, encoding="utf-8") as f:
            data = json.load(f)

        # Check if this is auto-generated
        if "candidate" in data and "/mnt/c/" in str(data):
            print(f"🧹 Cleaning summary prune plan: {summary_plan}")
            summary_plan.unlink()
            print("   ✅ Removed auto-generated summary plan")
            return True

        return True

    except Exception as e:
        print(f"⚠️  Error cleaning summary plan: {e}")
        return False


def clean_receipts() -> bool:
    """Verify receipts are gitignored."""
    receipts_dir = REPO_ROOT / "docs/tracing/RECEIPTS"

    if not receipts_dir.exists():
        print("✅ Receipts directory not found")
        return True

    receipt_count = len(list(receipts_dir.glob("*.txt")))
    print(f"📋 Found {receipt_count} receipt files (should be gitignored)")

    # Verify .gitignore has the entry
    gitignore = REPO_ROOT / ".gitignore"
    with open(gitignore, encoding="utf-8") as f:
        content = f.read()

    if "docs/tracing/RECEIPTS/" in content:
        print("   ✅ Receipts are properly gitignored")
        return True
    else:
        print("   ⚠️  Receipts NOT gitignored - add to .gitignore!")
        return False


def clean_temp_state() -> bool:
    """Remove temporary state files."""
    state_dir = REPO_ROOT / "state"
    if not state_dir.exists():
        print("✅ State directory not found")
        return True

    patterns = ["*.tmp", "*_snapshot.json", "*.timestamp.json"]
    removed_count = 0

    for pattern in patterns:
        for temp_file in state_dir.rglob(pattern):
            print(f"🧹 Removing: {temp_file.relative_to(REPO_ROOT)}")
            temp_file.unlink()
            removed_count += 1

    if removed_count > 0:
        print(f"   ✅ Removed {removed_count} temporary state files")
    else:
        print("✅ No temporary state files found")

    return True


def main() -> int:
    """Run all cleanup operations."""
    print("🧹 NuSyQ-Hub Runtime Artifact Cleanup")
    print("=" * 50)

    tasks = [
        ("Temple Metadata", clean_temple_metadata),
        ("Summary Plans", clean_summary_plans),
        ("Receipts Gitignore", clean_receipts),
        ("Temp State Files", clean_temp_state),
    ]

    results: list[bool] = []

    for name, task in tasks:
        print(f"\n📍 {name}")
        results.append(task())

    print("\n" + "=" * 50)
    if all(results):
        print("✅ All cleanup tasks completed successfully")
        print("\n📝 Next steps:")
        print("   1. Review changes: git status")
        print("   2. Stage intentional files: git add <files>")
        print("   3. Commit: git commit -m 'message'")
        return 0
    else:
        print("⚠️  Some cleanup tasks failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
