"""Batch Type Hints Addition Script.

Automatically adds comprehensive type hints to Python modules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Priority modules to add type hints to
PRIORITY_MODULES = [
    "src/ai/ai_coordinator.py",
    "src/ai/ollama_integration.py",
    "src/context/context_manager.py",
    "src/core/config_manager.py",
    "src/integration/chatdev_integration.py",
    "src/orchestration/multi_ai_orchestrator.py",
    "src/system/feature_flags.py",
]


def add_type_hints_to_module(module_path: Path) -> bool:
    """Add type hints to a module using ruff's auto-fix capability.

    Args:
        module_path: Path to the module

    Returns:
        True if successful, False otherwise
    """
    print(f"\n📝 Adding type hints to {module_path.name}...")

    try:
        # Run ruff with annotation fixes
        result = subprocess.run(
            ["ruff", "check", "--select", "ANN", "--fix", str(module_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"   ✅ Successfully added type hints to {module_path.name}")
            return True
        else:
            print(f"   ⚠️  Some type hints could not be auto-fixed in {module_path.name}")
            if result.stdout:
                print(f"   Details: {result.stdout[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Error processing {module_path.name}: {e}")
        return False


def check_module_type_coverage(module_path: Path) -> tuple[int, int]:
    """Check type hint coverage for a module.

    Args:
        module_path: Path to the module

    Returns:
        Tuple of (total_functions, annotated_functions)
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "--select", "ANN", str(module_path), "--output-format=concise"],
            capture_output=True,
            text=True,
        )

        # Count missing annotations
        missing_annotations = result.stdout.count("ANN")

        # Rough estimate - each function typically has 2-3 annotation issues
        total_issues = missing_annotations

        return total_issues, 0 if total_issues > 0 else 1

    except (SyntaxError, OSError, UnicodeDecodeError):
        return 0, 0


def main() -> int:
    """Main execution function."""
    print("🚀 Batch Type Hints Addition")
    print("=" * 60)

    repo_root = Path(__file__).parent.parent

    successful = 0
    failed = 0

    for module_rel_path in PRIORITY_MODULES:
        module_path = repo_root / module_rel_path

        if not module_path.exists():
            print(f"⏭️  Skipping {module_path.name} (not found)")
            continue

        # Check current coverage
        issues_before, _ = check_module_type_coverage(module_path)

        # Add type hints
        if add_type_hints_to_module(module_path):
            successful += 1

            # Check coverage after
            issues_after, _ = check_module_type_coverage(module_path)

            if issues_after < issues_before:
                print(f"   📊 Reduced type annotation issues: {issues_before} → {issues_after}")
        else:
            failed += 1

    print("\n" + "=" * 60)
    print("✨ Batch Type Hints Complete!")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
