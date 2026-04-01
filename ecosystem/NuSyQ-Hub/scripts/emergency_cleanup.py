#!/usr/bin/env python3
"""Emergency workspace cleanup - removes bloat with safety checks
Run this when workspace exceeds size limits

Usage:
    python scripts/emergency_cleanup.py                  # Dry run (shows what would be deleted)
    python scripts/emergency_cleanup.py --execute        # Actually execute cleanup
    python scripts/emergency_cleanup.py --stats-only     # Just show statistics
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

# Config
WORKSPACE_ROOT = Path(__file__).parent.parent


def get_file_size_gb(path):
    """Get file size in GB"""
    try:
        return os.path.getsize(path) / (1024**3)
    except (OSError, FileNotFoundError):
        return 0


def get_file_size_mb(path):
    """Get file size in MB"""
    try:
        return os.path.getsize(path) / (1024**2)
    except (OSError, FileNotFoundError):
        return 0


def cleanup_maze_summaries(dry_run=True):
    """Keep only 3 most recent maze_summary files"""
    logs_dir = WORKSPACE_ROOT / "logs"
    if not logs_dir.exists():
        print("⚠️  logs/ directory not found")
        return 0

    files = sorted(logs_dir.glob("maze_summary_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(files) == 0:
        print("✅ No maze_summary files found")
        return 0

    to_keep = files[:3]
    to_delete = files[3:]

    print(f"\n{'=' * 70}")
    print("📊 MAZE SUMMARY CLEANUP")
    print(f"{'=' * 70}")
    print(f"Total files found: {len(files)}")
    print(f"Keeping (3 most recent): {len(to_keep)}")
    print(f"Deleting (old): {len(to_delete)}")

    if to_keep:
        print("\n✅ Files to KEEP:")
        for f in to_keep:
            size = get_file_size_gb(f)
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"   ✓ {f.name:50s} {size:6.2f} GB  ({mtime.strftime('%Y-%m-%d %H:%M')})")

    total_size_gb = sum(get_file_size_gb(f) for f in to_delete)

    if to_delete:
        print(f"\n🗑️  Files to DELETE (recover {total_size_gb:.2f} GB):")
        for f in to_delete:
            size = get_file_size_gb(f)
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if dry_run:
                print(f"   - {f.name:50s} {size:6.2f} GB  ({mtime.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"   🗑️  Deleting {f.name:50s} {size:6.2f} GB...")
                try:
                    f.unlink()
                    print("      ✅ Deleted successfully")
                except Exception as e:
                    print(f"      ❌ Error: {e}")

        if not dry_run:
            print(f"\n✅ Deleted {len(to_delete)} files, recovered {total_size_gb:.2f} GB")
    else:
        print(f"\n✅ No old files to delete (only {len(files)} total, keeping all)")

    return total_size_gb


def cleanup_large_artifacts(dry_run=True):
    """Remove large generated artifacts"""
    artifacts = [
        WORKSPACE_ROOT / "docs/dependency-analysis/dependency-analysis.json",
        WORKSPACE_ROOT / "function_registry_data.json",
    ]

    print(f"\n{'=' * 70}")
    print("📊 LARGE ARTIFACTS CLEANUP")
    print(f"{'=' * 70}")

    total_size_gb = 0
    found_any = False

    for path in artifacts:
        if path.exists():
            found_any = True
            size = get_file_size_gb(path)
            total_size_gb += size

            if dry_run:
                print(f"🗑️  Would delete: {path.name:50s} {size:6.2f} GB")
            else:
                print(f"🗑️  Deleting: {path.name:50s} {size:6.2f} GB...")
                try:
                    path.unlink()
                    print("   ✅ Deleted successfully")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

    if not found_any:
        print("✅ No large artifacts found")
    elif dry_run:
        print(f"\nTotal space to recover: {total_size_gb:.2f} GB")
    else:
        print(f"\n✅ Recovered {total_size_gb:.2f} GB from artifacts")

    return total_size_gb


def show_statistics():
    """Show workspace statistics without deleting anything"""
    print(f"\n{'=' * 70}")
    print("📊 WORKSPACE STATISTICS")
    print(f"{'=' * 70}")

    logs_dir = WORKSPACE_ROOT / "logs"

    # Count maze_summary files
    if logs_dir.exists():
        maze_files = list(logs_dir.glob("maze_summary_*.json"))
        if maze_files:
            total_maze_size = sum(get_file_size_gb(f) for f in maze_files)
            print("\nMaze Summary Files:")
            print(f"  Count: {len(maze_files)}")
            print(f"  Total size: {total_maze_size:.2f} GB")

            largest = max(maze_files, key=lambda f: f.stat().st_size)
            print(f"  Largest: {largest.name} ({get_file_size_gb(largest):.2f} GB)")

            oldest = min(maze_files, key=lambda f: f.stat().st_mtime)
            newest = max(maze_files, key=lambda f: f.stat().st_mtime)
            print(f"  Oldest: {datetime.fromtimestamp(oldest.stat().st_mtime).strftime('%Y-%m-%d')}")
            print(f"  Newest: {datetime.fromtimestamp(newest.stat().st_mtime).strftime('%Y-%m-%d')}")

    # Check large artifacts
    dep_analysis = WORKSPACE_ROOT / "docs/dependency-analysis/dependency-analysis.json"
    func_registry = WORKSPACE_ROOT / "function_registry_data.json"

    print("\nLarge Artifacts:")
    if dep_analysis.exists():
        print(f"  dependency-analysis.json: {get_file_size_mb(dep_analysis):.0f} MB")
    else:
        print("  dependency-analysis.json: Not found")

    if func_registry.exists():
        print(f"  function_registry_data.json: {get_file_size_mb(func_registry):.0f} MB")
    else:
        print("  function_registry_data.json: Not found")

    # Search indexes
    search_index_dir = WORKSPACE_ROOT / "State/search_index"
    if search_index_dir.exists():
        index_files = list(search_index_dir.glob("*.json"))
        if index_files:
            total_index_size = sum(get_file_size_mb(f) for f in index_files)
            print(f"\nSearch Indexes ({len(index_files)} files):")
            print(f"  Total size: {total_index_size:.0f} MB")
            for f in index_files:
                print(f"  - {f.name}: {get_file_size_mb(f):.0f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Emergency workspace cleanup script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/emergency_cleanup.py                  # Dry run
  python scripts/emergency_cleanup.py --execute        # Execute cleanup
  python scripts/emergency_cleanup.py --stats-only     # Show statistics
        """,
    )
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default is dry-run)")
    parser.add_argument("--stats-only", action="store_true", help="Just show statistics, don't show deletion plan")

    args = parser.parse_args()

    dry_run = not args.execute

    print("\n" + "=" * 70)
    print("🧹 EMERGENCY WORKSPACE CLEANUP")
    print("=" * 70)

    if args.stats_only:
        show_statistics()
        return

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print("   Use --execute flag to actually delete files")
    else:
        print("🚨 EXECUTION MODE - Files will be DELETED")
        print("   Backup recommended before proceeding")
        response = input("\n⚠️  Continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("❌ Cleanup cancelled")
            return

    # Run cleanup phases
    maze_size = cleanup_maze_summaries(dry_run)
    artifacts_size = cleanup_large_artifacts(dry_run)

    # Summary
    total_recovery = maze_size + artifacts_size

    print(f"\n{'=' * 70}")
    print("📊 SUMMARY")
    print(f"{'=' * 70}")
    print(f"Maze summaries: {maze_size:.2f} GB")
    print(f"Large artifacts: {artifacts_size:.2f} GB")
    print(f"{'─' * 70}")
    print(f"Total recovery: {total_recovery:.2f} GB")
    print(f"{'=' * 70}")

    if dry_run:
        print("\n✅ Dry run complete - no files were deleted")
        print("💡 To execute cleanup: python scripts/emergency_cleanup.py --execute")
    else:
        print("\n✅ Cleanup complete!")
        print(f"💾 Recovered {total_recovery:.2f} GB of disk space")


if __name__ == "__main__":
    main()
