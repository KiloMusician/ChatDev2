#!/usr/bin/env python
"""Post-commit hook: Automatic Quest-Commit Bridge + Smart Search Index Update

This hook automatically transforms every git commit into:
1. Quest completion receipt
2. XP award calculation
3. Knowledge base update
4. Evolution pattern extraction
5. Smart Search incremental index update (ZERO-TOKEN OPTIMIZATION)

OmniTag: [git, hook, automation, consciousness, evolution, smart_search]
MegaTag: [PERPETUAL_MOTION, FEEDBACK_LOOP, SELF_IMPROVEMENT, ZERO_TOKEN]
"""

import subprocess
import sys
from pathlib import Path

# Get project root (2 levels up from .githooks/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
bridge_script = PROJECT_ROOT / "scripts" / "quest_commit_bridge.py"
index_builder_script = PROJECT_ROOT / "src" / "search" / "index_builder.py"


def run_quest_bridge() -> None:
    """Execute quest-commit bridge."""
    if not bridge_script.exists():
        print(f"⚠️  Quest-commit bridge not found: {bridge_script}")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(bridge_script)],
            cwd=PROJECT_ROOT,
            capture_output=False,
            check=False,
        )

        if result.returncode != 0:
            print(f"⚠️  Quest-commit bridge exited with code {result.returncode}")

    except Exception as e:
        print(f"⚠️  Quest-commit bridge error: {e}")


def update_smart_search_index() -> None:
    """Update Smart Search index incrementally."""
    print("🔍 Updating Smart Search index...")

    if not index_builder_script.exists():
        print(f"⚠️  Index builder not found: {index_builder_script}")
        return

    try:
        # Run incremental update
        result = subprocess.run(
            [sys.executable, str(index_builder_script), "--incremental"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            # Parse stats if available
            import json

            try:
                stats = json.loads(result.stdout)
                files_updated = stats.get("files_updated", 0)
                files_removed = stats.get("files_removed", 0)
                elapsed = stats.get("elapsed_seconds", 0)

                if files_updated > 0 or files_removed > 0:
                    print(
                        f"   ✅ Index updated: +{files_updated} ~{files_removed} ({elapsed:.1f}s)"
                    )
                else:
                    print("   ✅ Index up-to-date")
            except (json.JSONDecodeError, ValueError):
                print("   ✅ Index update complete")
        else:
            print(f"   ⚠️  Index update failed: {result.stderr}")

    except Exception as e:
        print(f"⚠️  Index update error: {e}")


def main() -> int:
    """Execute post-commit automation tasks."""
    print("\n🌉 Post-Commit: Activating evolutionary feedback loop...")

    # Run quest-commit bridge
    run_quest_bridge()

    # Update Smart Search index (zero-token optimization)
    update_smart_search_index()

    print("✅ Post-commit automation complete\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
