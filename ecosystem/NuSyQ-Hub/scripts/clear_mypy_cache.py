#!/usr/bin/env python3
"""🧹 MyPy Cache Maintenance Script

Clears corrupted or oversized mypy cache to prevent timeout issues.
"""

import shutil
import sys
from pathlib import Path


def main() -> None:
    """Clear mypy cache and report results."""
    repo_root = Path(__file__).resolve().parents[1]
    cache_dir = repo_root / ".mypy_cache"

    print("🧹 MyPy Cache Maintenance")
    print("=" * 60)

    if not cache_dir.exists():
        print("✅ No mypy cache found - nothing to clear")
        return

    # Check cache size
    try:
        total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)

        print(f"📦 Current cache size: {size_mb:.1f} MB")

        if size_mb > 100:
            print("⚠️  Cache is large (>100MB) - clearing recommended")
        else:
            print("✅ Cache size is reasonable")

        # Clear cache
        print("🗑️  Removing cache directory...")
        shutil.rmtree(cache_dir)
        print("✅ MyPy cache cleared successfully")
        print()
        print("💡 Tip: Run mypy with --no-incremental to avoid cache issues")

    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
