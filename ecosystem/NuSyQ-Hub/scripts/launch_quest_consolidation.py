#!/usr/bin/env python3
"""Launch ChatDev Multi-Agent Team for Quest Bridge Consolidation.

Task: Consolidate 3 Quest modules into unified_quest_bridge.py
Target XP: 100
"""

import asyncio
import logging
import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.tools.agent_task_router import AgentTaskRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUEST_CONSOLIDATION_TASK = """
Create a unified Quest integration bridge by consolidating 3 existing Quest modules into a single, maintainable module.

PROJECT NAME: QuestBridgeConsolidation

REQUIREMENTS:
1. **Source Modules** (3 files to consolidate):
   - src/integration/error_quest_bridge.py (ErrorQuestBridge class, ~255 LOC, 8.8KB)
     * Auto-generates quests from critical errors via UnifiedErrorReporter
     * Filters by severity threshold (ERROR, WARNING, etc.)
     * Creates quests with error metadata

   - src/integration/quest_temple_bridge.py (QuestTempleBridge, QuestTempleProgressionBridge, ~591 LOC, 19.6KB)
     * Links quest completion to Temple consciousness progression
     * Calculates consciousness points from quest attributes
     * Provides async sync_progress() method
     * Has QuestTempleProgressionCalculator (base points, multipliers, bonuses)

   - src/integration/game_quest_bridge.py (GameQuestIntegrationBridge, HouseOfLeavesGameBridge, ~401 LOC, 12.9KB)
     * Converts game events to quest system updates
     * Maps GameEventType to quest updates
     * Provides GameQuestMapper with event-quest rules
     * Supports bidirectional game ↔ quest communication

2. **Target Module**:
   - Create: src/integration/unified_quest_bridge.py (estimated 1,400+ LOC)

3. **Architecture**:
   - Implement **UnifiedQuestBridge** class as main facade
   - Sub-components:
     * ErrorQuestBridge (error → quest generation)
     * QuestTempleProgressionBridge (quest → temple progression)
     * GameQuestIntegrationBridge (game events → quests)
   - Use dependency injection pattern
   - Async-first design (async methods for temple sync, game events)
   - Configuration precedence: explicit args → config file → environment → defaults
   - Comprehensive type hints (100% coverage)
   - Detailed docstrings with examples

4. **Backward Compatibility**:
   - Add deprecation warnings to old modules:
     ```python
     import warnings
     warnings.warn("Module deprecated, use unified_quest_bridge", DeprecationWarning, stacklevel=2)
     from src.integration.unified_quest_bridge import UnifiedQuestBridge as ErrorQuestBridge
     ```
   - Preserve all public APIs
   - Maintain existing function signatures
   - Keep async compatibility for sync_progress()

5. **Downstream Integration Updates** (estimate 5-7 files):
   - src/orchestration/ecosystem_activator.py (QuestTempleProgressionBridge, GameQuestIntegrationBridge)
   - src/Rosetta_Quest_System/quest_engine.py (potential integration)
   - tests/integration/* (test imports)
   Update imports:
   ```python
   # OLD: from src.integration.error_quest_bridge import ErrorQuestBridge
   # NEW: from src.integration.unified_quest_bridge import UnifiedQuestBridge
   # OR: from src.integration.unified_quest_bridge import ErrorQuestBridge  # deprecated compat
   ```

6. **Testing**:
   - Create test suite: tests/integration/test_unified_quest_bridge.py
   - Test cases:
     * Import compatibility (all old imports still work)
     * UnifiedQuestBridge initialization
     * Error → Quest generation workflow
     * Quest → Temple progression calculation
     * Game event → Quest update workflow
     * Async method compatibility (sync_progress)
   - All tests must pass (pytest)

7. **Code Quality**:
   - Zero ruff errors
   - Black formatted
   - 100% type hints
   - Docstrings for all public methods
   - Async/await best practices
   - No circular imports

8. **Documentation**:
   - Create migration guide: docs/migrations/QUEST_CONSOLIDATION_GUIDE.md
   - Document breaking changes (if any)
   - Provide example usage:
     * Error-driven quest generation
     * Temple progression tracking
     * Game event integration
   - API reference with code examples

CONSTRAINTS:
- Maintain all existing functionality (zero regression)
- Pass all existing tests
- Follow NuSyQ coding standards (type hints, docstrings, logging)
- Use Python 3.12+ features
- Keep complexity under control (max 15 per method)
- Preserve async patterns from original modules

DELIVERABLES:
1. src/integration/unified_quest_bridge.py (unified module)
2. Updated backward compatibility wrappers (3 deprecated modules)
3. Updated downstream imports (5-7 files)
4. Test suite (tests/integration/test_unified_quest_bridge.py)
5. Migration guide (docs/migrations/QUEST_CONSOLIDATION_GUIDE.md)
6. Commit message template:
   ```
   feat(integration): consolidate Quest modules via multi-agent collaboration

   - Unified 3 modules into UnifiedQuestBridge facade
   - Maintained backward compatibility with deprecation warnings
   - Updated downstream integrations
   - Added comprehensive test suite
   - Zero ruff errors, 100% type hints

   XP: +100 (CONSOLIDATION, ASYNC_DESIGN, QUEST_INTEGRATION)
   ```

SUCCESS CRITERIA:
- ✅ All 3 modules consolidated
- ✅ Zero import errors
- ✅ All tests passing
- ✅ Zero ruff/black errors
- ✅ Backward compatibility verified
- ✅ Async compatibility maintained
- ✅ Migration guide complete
"""


async def main() -> None:
    """Launch ChatDev quest consolidation task."""
    logger.info("=" * 80)
    logger.info("🚀 LAUNCHING CHATDEV QUEST BRIDGE CONSOLIDATION")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Task: Consolidate 3 Quest modules → unified_quest_bridge.py")
    logger.info("Modules: ErrorQuestBridge, QuestTempleProgressionBridge, GameQuestIntegrationBridge")
    logger.info("Target XP: +100 (CONSOLIDATION, ASYNC_DESIGN, QUEST_INTEGRATION)")
    logger.info("")
    logger.info("Waiting for ChatDev availability (after ChatDev consolidation completes)...")
    logger.info("")

    router = AgentTaskRouter()

    logger.info("🤖 Routing task to ChatDev multi-agent system...")

    result = await router.route_task(
        task_type="generate",
        description=QUEST_CONSOLIDATION_TASK,
        context={
            "project_name": "QuestBridgeConsolidation",
            "target_directory": "src/integration",
            "xp_target": 100,
            "tags": ["CONSOLIDATION", "ASYNC_DESIGN", "QUEST_INTEGRATION"],
        },
        target_system="chatdev",
        priority="HIGH",
    )

    logger.info("")
    logger.info("=" * 80)
    logger.info("📋 QUEST CONSOLIDATION ROUTING RESULT")
    logger.info("=" * 80)
    logger.info(f"Status: {result.get('status', 'unknown')}")
    logger.info(f"System: {result.get('system', 'unknown')}")

    if "task_id" in result:
        logger.info(f"Task ID: {result['task_id']}")

    if "error" in result:
        logger.error(f"❌ Error: {result['error']}")

    logger.info("")
    logger.info("After ChatDev completes:")
    logger.info("  1. Review unified_quest_bridge.py")
    logger.info("  2. Run: pytest tests/integration/test_unified_quest_bridge.py")
    logger.info("  3. Run quality checks (ruff, black)")
    logger.info("  4. Commit with quest-commit-bridge for +100 XP")
    logger.info("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Task routing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Task routing failed: {e}")
        sys.exit(1)
