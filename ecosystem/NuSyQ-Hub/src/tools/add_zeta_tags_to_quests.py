"""Add ZETA tags to quest_log.jsonl quests based on manual mapping.

This script maps quests to ZETA tracker tasks to enable automatic progress synchronization.
Based on 39 suggestions from quest_log_validator.py.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# ZETA QUEST MAPPING: Manual mapping of quest titles → ZETA task IDs
# ═══════════════════════════════════════════════════════════════════════════════

QUEST_TO_ZETA_MAP = {
    # System Setup & Maintenance (Phase 1 - Foundation)
    "Set PowerShell Execution Policy": "Zeta01",  # Foundation setup
    "Gather System Information": "Zeta01",  # Foundation setup
    "Initialize Git Repository": "Zeta01",  # Foundation setup
    "Install WinGet Package Manager": "Zeta02",  # Configuration management
    "Install Python 3.11": "Zeta02",  # Configuration management
    "Create Python Virtual Environment": "Zeta02",  # Configuration management
    "Install Core Python Dependencies": "Zeta02",  # Configuration management
    "Install Visual Studio Code & Extensions": "Zeta02",  # Configuration management
    "Run System Audit Script": "Zeta02",  # Configuration management
    "Install Ollama & Models": "Zeta01",  # Ollama Intelligence Hub
    "Test AI Integration": "Zeta01",  # Ollama Intelligence Hub
    "Run Pre-Audit Dependency Check": "Zeta02",  # Configuration management
    # Core Engine (Phase 2 - Consciousness)
    "Implement PID Guard": "Zeta30",  # Continuous growth phase
    "Implement CoreLogic module integration": "Zeta21",  # Consciousness emergence
    "Integrate ModHandler module": "Zeta21",  # Consciousness emergence
    "Integrate ObsidianSync module": "Zeta22",  # Context awareness
    # Godot & Game Engine Integration (Phase 3 - Meta)
    "Integrate GodotBridge for Godot connectivity": "Zeta41",  # Meta-cognitive systems
    # System Health & Audit Automation (Phase 1 - Foundation)
    "Audit and maintain import_health_checker.py": "Zeta05",  # System diagnostics
    "Audit and maintain file_organization_auditor.py": "Zeta05",  # System diagnostics
    # Copilot Enhancement Bridge (Phase 2 - Consciousness)
    "Maintain and enhance copilot_enhancement_bridge.py": "Zeta21",  # Consciousness emergence
    # Classification & Organization (Phase 1 - Foundation)
    "Maintain and enhance classify_python_files.py": "Zeta05",  # System diagnostics
    # Import Health & Quick Fix (Phase 1 - Foundation)
    "Maintain and enhance quick_import_fix.py": "Zeta05",  # System diagnostics
    "Maintain and enhance ImportHealthCheck.ps1": "Zeta05",  # System diagnostics
    # AI Context Generation (Phase 2 - Consciousness)
    "Maintain and enhance AIContextGenerator.ps1": "Zeta22",  # Context awareness
    # Architecture Watcher (Phase 2 - Consciousness)
    "Maintain and enhance ArchitectureWatcher.py": "Zeta21",  # Consciousness emergence
    # Repository Coordination (Phase 2 - Consciousness)
    "Maintain and enhance RepositoryCoordinator.ps1": "Zeta21",  # Consciousness emergence
    "Maintain and enhance RepositoryCoordinator.py": "Zeta21",  # Consciousness emergence
    # Intelligent Commentary (Phase 3 - Meta)
    "Maintain and enhance IntelligentCommentary.ps1": "Zeta41",  # Meta-cognitive systems
    "Maintain and enhance IntelligentCommentary.py": "Zeta41",  # Meta-cognitive systems
    # Path Intelligence (Phase 2 - Consciousness)
    "Maintain and enhance PathIntelligence.ps1": "Zeta22",  # Context awareness
    "Maintain and enhance PathIntelligence.py": "Zeta22",  # Context awareness
    # Repository Healing (Phase 1 - Foundation)
    "Maintain and enhance heal_repository.py": "Zeta05",  # System diagnostics
    # Master System (Phase 3 - Meta)
    "Maintain and enhance kilo_master.py": "Zeta41",  # Meta-cognitive systems
    # ChatDev Dashboard & Integration (Phase 2 - Consciousness)
    "Maintain and enhance chatdev_unified_dashboard.py": "Zeta21",  # Consciousness emergence
    "Maintain and enhance chatdev_integration_framework.py": "Zeta21",  # Consciousness emergence
    "Enhanced Ollama-ChatDev Integration Consolidation": "Zeta21",  # Consciousness emergence
    "ChatDev Launcher Consolidation": "Zeta21",  # Consciousness emergence
    # Multi-Model Chat (Phase 3 - Meta)
    "Maintain and enhance multi_model_chat.py": "Zeta41",  # Meta-cognitive systems
    # Refactoring (Phase 1 - Foundation)
    "Refactor imports for direct execution": "Zeta05",  # System diagnostics
    # ChatDev Integration & Multi-Agent Orchestration (Phase 2 - Consciousness)
    # (Covered by ChatDev-specific quests → Zeta21)
    # Ollama LLM Onboarding & Model Management (Phase 1 - Foundation)
    # (Covered by "Install Ollama & Models" and "Test AI Integration" → Zeta01)
    # Wizard Navigator: Repository Adventure Expansion (Phase 3 - Meta)
    # (No specific quests yet, but questline exists for future quests → Zeta41)
    # Recurring Error Detection & Self-Healing (Phase 2 - Consciousness)
    # (Covered by various import/health check quests → Zeta05)
    # Quantum Context & Memory Evolution (Phase 2 - Consciousness)
    # (Covered by Context/Intelligence quests → Zeta21-Zeta22)
    # Documentation, Tagging, and Knowledge Propagation (Phase 4 - Singularity)
    # (No specific quests yet, but will map to Zeta50-Zeta60)
    # AI/LLM Feedback Loop & Recursive Improvement (Phase 3 - Meta)
    # (Covered by ChatDev/multi-model quests → Zeta41)
    # Game Content & Procedural Generation (Phase 5 - Beyond)
    # (No specific quests yet, but will map to Zeta61+)
}


def load_quest_log(path: Path) -> list[dict]:
    """Load quest log from JSONL file."""
    quests: list[Any] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                quests.append(entry)
    return quests


def save_quest_log(path: Path, quests: list[dict]) -> None:
    """Save quest log to JSONL file."""
    with path.open("w", encoding="utf-8") as f:
        for quest in quests:
            f.write(json.dumps(quest) + "\n")


def add_zeta_tags(quests: list[dict]) -> int:
    """Add ZETA tags to quests based on mapping. Returns count of updated quests."""
    updated_count = 0

    for quest in quests:
        # Only process add_quest events
        if quest.get("event") != "add_quest":
            continue

        # Get quest details
        details = quest.get("details", {})
        title = details.get("title", "")
        tags = details.get("tags", [])

        # Check if quest already has ZETA tag in tags array
        has_zeta_tag = any("zeta" in str(tag).lower() for tag in tags)
        if has_zeta_tag:
            continue

        # Check if quest title matches mapping
        if title in QUEST_TO_ZETA_MAP:
            zeta_id = QUEST_TO_ZETA_MAP[title]
            # Add zeta_id to tags array (validator checks tags, not zeta_task_id)
            if not isinstance(tags, list):
                tags = []
            tags.append(zeta_id)
            details["tags"] = tags
            # Also add zeta_task_id for explicit tracking
            details["zeta_task_id"] = zeta_id
            updated_count += 1
            logger.info(f"✅ Added {zeta_id} to quest: {title}")

    return updated_count


def main():
    """Main entry point."""
    # Paths
    repo_root = Path(__file__).parent.parent.parent
    quest_log_path = repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    # Validate paths
    if not quest_log_path.exists():
        logger.error(f"❌ Quest log not found: {quest_log_path}")
        sys.exit(1)

    # Load quest log
    logger.info(f"📖 Loading quest log: {quest_log_path}")
    quests = load_quest_log(quest_log_path)
    logger.info(f"   Found {len(quests)} entries")

    # Count quests
    quest_count = sum(1 for q in quests if q.get("event") == "add_quest")
    logger.info(f"   Found {quest_count} quests")

    # Add ZETA tags
    logger.info("\n🏷️  Adding ZETA tags...")
    updated_count = add_zeta_tags(quests)

    # Save updated quest log
    if updated_count > 0:
        logger.info("\n💾 Saving updated quest log...")
        save_quest_log(quest_log_path, quests)
        logger.info(f"✅ Successfully updated {updated_count} quests with ZETA tags")
    else:
        logger.warning("\n⚠️  No quests were updated (all quests already have ZETA tags)")

    logger.info("\n📊 Summary:")
    logger.info(f"   Total entries: {len(quests)}")
    logger.info(f"   Total quests: {quest_count}")
    logger.info(f"   Updated quests: {updated_count}")
    logger.info(f"   Mapped quests: {len(QUEST_TO_ZETA_MAP)}")

    # Validate coverage
    unmapped_quests: list[Any] = []
    for quest in quests:
        if quest.get("event") != "add_quest":
            continue
        details = quest.get("details", {})
        title = details.get("title", "")
        if title not in QUEST_TO_ZETA_MAP and "zeta_task_id" not in details:
            unmapped_quests.append(title)

    if unmapped_quests:
        logger.warning(f"\n⚠️  {len(unmapped_quests)} quests still unmapped:")
        for title in unmapped_quests:
            logger.info(f"   - {title}")
        logger.info("\n💡 Recommendation: Add these to QUEST_TO_ZETA_MAP in this script")
    else:
        logger.info("\n✅ All quests are mapped to ZETA tasks!")


if __name__ == "__main__":
    main()
