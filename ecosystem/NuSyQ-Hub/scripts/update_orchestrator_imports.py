#!/usr/bin/env python3
"""Batch update orchestrator imports to use new unified orchestrators."""

import re
import sys
from pathlib import Path

# Files to update (excluding .docker_build_context and .sanitized_build_context)
TARGET_FILES = [
    "demo_ai_game_creation.py",
    "src/culture_ship_real_action.py",
    "tests/test_orchestrator_pruning.py",
    "tests/test_summary_retrieval.py",
    "src/utils/enhanced_directory_context_generator.py",
    "src/orchestration/sns_orchestrator_adapter.py",
    "src/evolution/consolidated_system.py",
    "src/diagnostics/kilo_infrastructure_validator.py",
    "src/diagnostics/integrated_health_orchestrator.py",
    "bootstrap_chatdev_pipeline.py",
    "scripts/orchestrate_coding_fixes.py",
    "scripts/fix_future_imports.py",
    "scripts/submit_orchestrator_test_task.py",
    "scripts/ecosystem_deep_dive_tour.py",
    "tests/test_orchestrator_sns.py",
    "final_health_check.py",
    "examples/sns_orchestrator_demo.py",
    "src/tools/kilo_dev_launcher.py",
    "scripts/generate_sns_tests.py",
    "scripts/run_post_optimization_qa.py",
    "scripts/test_chatdev_consensus.py",
]

# Import replacement patterns
REPLACEMENTS = [
    # multi_ai_orchestrator → unified_ai_orchestrator
    (
        r"from\s+src\.orchestration\.multi_ai_orchestrator\s+import",
        "from src.orchestration.unified_ai_orchestrator import",
    ),
    (
        r"from\s+\.\.orchestration\.multi_ai_orchestrator\s+import",
        "from ..orchestration.unified_ai_orchestrator import",
    ),
    (
        r"import\s+src\.orchestration\.multi_ai_orchestrator",
        "import src.orchestration.unified_ai_orchestrator",
    ),
    # Class name aliases
    (r"MultiAIOrchestrator\(", "UnifiedAIOrchestrator("),
    # comprehensive_workflow_orchestrator → unified_ai_orchestrator
    (
        r"from\s+src\.orchestration\.comprehensive_workflow_orchestrator\s+import",
        "from src.orchestration.unified_ai_orchestrator import",
    ),
    (r"ComprehensiveWorkflowOrchestrator\(", "UnifiedAIOrchestrator("),
    # system_testing_orchestrator → unified_ai_orchestrator
    (
        r"from\s+src\.orchestration\.system_testing_orchestrator\s+import",
        "from src.orchestration.unified_ai_orchestrator import",
    ),
    (r"SystemTestingOrchestrator\(", "UnifiedAIOrchestrator("),
    # kilo_ai_orchestration_master → unified_ai_orchestrator
    (
        r"from\s+src\.orchestration\.kilo_ai_orchestration_master\s+import",
        "from src.orchestration.unified_ai_orchestrator import",
    ),
    # chatdev orchestrators → chatdev_development_orchestrator
    (
        r"from\s+src\.automation\.chatdev_orchestration\s+import",
        "from src.orchestration.chatdev_development_orchestrator import",
    ),
    (
        r"from\s+src\.ai\.chatdev_phase_orchestrator\s+import",
        "from src.orchestration.chatdev_development_orchestrator import",
    ),
    (r"ChatDevOrchestrator\(", "ChatDevDevelopmentOrchestrator("),
    (r"ChatDevPhaseOrchestrator\(", "ChatDevDevelopmentOrchestrator("),
    # autonomous_orchestrator → autonomous_quest_orchestrator
    (
        r"from\s+src\.automation\.autonomous_orchestrator\s+import",
        "from src.orchestration.autonomous_quest_orchestrator import",
    ),
]


def update_file(file_path: Path) -> bool:
    """Update imports in a single file.

    Returns:
        True if file was modified, False otherwise
    """
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
    print("🔄 UPDATING ORCHESTRATOR IMPORTS")
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
    print("📊 IMPORT UPDATE SUMMARY")
    print("=" * 80)
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ⏭️  No Changes: {skipped_count}")
    print(f"  ❌ Errors/Not Found: {error_count}")
    print(f"  📁 Total Files: {len(TARGET_FILES)}")
    print("=" * 80 + "\n")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
