#!/usr/bin/env python3
"""Launch ChatDev Multi-Agent Team for ChatDev Module Consolidation.

This script delegates the complex consolidation task to ChatDev's collaborative
multi-agent system (CEO → CTO → Programmer → Tester).

Task: Consolidate 6 ChatDev modules into unified_chatdev_bridge.py
Target XP: 200
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add repo root to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.tools.agent_task_router import AgentTaskRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Task description for ChatDev multi-agent team
CONSOLIDATION_TASK = """
Create a unified ChatDev integration bridge by consolidating 6 existing modules into a single, maintainable module.

PROJECT NAME: ChatDevConsolidation

REQUIREMENTS:
1. **Source Modules** (6 files to consolidate):
   - src/integration/chatdev_integration.py (ChatDevIntegration class, ~400 LOC)
   - src/integration/chatdev_launcher.py (ChatDevLauncher class, ~524 LOC)
   - src/integration/chatdev_service.py (ChatDevService class, ~350 LOC)
   - src/ai/chatdev_llm_adapter.py (ChatDevLLMAdapter class, ~280 LOC)
   - src/integration/copilot_chatdev_bridge.py (CopilotChatDevBridge class, ~420 LOC)
   - src/orchestration/advanced_chatdev_copilot_integration.py (AdvancedIntegration class, ~1,350 LOC)

2. **Target Module**:
   - Create: src/integration/unified_chatdev_bridge.py (estimated 2,000+ LOC)

3. **Architecture**:
   - Implement **ChatDevOrchestrator** class as main facade
   - Sub-components:
     * ChatDevLauncher (project launching)
     * ChatDevService (API service wrapper)
     * ChatDevAdapter (LLM model adaptation)
     * ChatDevBridge (Copilot integration)
   - Use dependency injection pattern
   - Configuration precedence: explicit args → config file → environment → defaults
   - Comprehensive type hints (100% coverage)
   - Detailed docstrings with examples

4. **Backward Compatibility**:
   - Add deprecation warnings to old modules:
     ```python
     import warnings
     warnings.warn("Module deprecated, use unified_chatdev_bridge", DeprecationWarning)
     from src.integration.unified_chatdev_bridge import ChatDevOrchestrator as ChatDevIntegration
     ```
   - Preserve all public APIs
   - Maintain existing function signatures

5. **Downstream Integration Updates** (4 files):
   - src/integration/autonomous_integration_engine.py
   - scripts/ingest_maze_summary.py
   - src/integration/unified_orchestration_bridge.py
   - src/orchestration/chatdev_development_orchestrator.py
   Update imports:
   ```python
   # OLD: from src.integration.chatdev_launcher import ChatDevLauncher
   # NEW: from src.integration.unified_chatdev_bridge import ChatDevOrchestrator
   ```

6. **Testing**:
   - Create test suite: tests/integration/test_unified_chatdev_bridge.py
   - Test cases:
     * Import compatibility (all old imports still work)
     * Orchestrator initialization
     * Project launching workflow
     * Service API calls
     * LLM adapter model selection
     * Copilot bridge integration
   - All tests must pass (pytest)

7. **Code Quality**:
   - Zero ruff errors
   - Black formatted
   - 100% type hints
   - Docstrings for all public methods
   - No circular imports

8. **Documentation**:
   - Create migration guide: docs/migrations/CHATDEV_CONSOLIDATION_GUIDE.md
   - Document breaking changes (if any)
   - Provide example usage for all major workflows
   - API reference with code examples

CONSTRAINTS:
- Maintain all existing functionality (zero regression)
- Pass all existing tests
- Follow NuSyQ coding standards (type hints, docstrings, logging)
- Use Python 3.12+ features
- Keep complexity under control (max 15 per method)

DELIVERABLES:
1. src/integration/unified_chatdev_bridge.py (unified module)
2. Updated backward compatibility wrappers (6 deprecated modules)
3. Updated downstream imports (4 files)
4. Test suite (tests/integration/test_unified_chatdev_bridge.py)
5. Migration guide (docs/migrations/CHATDEV_CONSOLIDATION_GUIDE.md)
6. Commit message template:
   ```
   feat(integration): consolidate ChatDev modules via multi-agent collaboration

   - Unified 6 modules into ChatDevOrchestrator facade
   - Maintained backward compatibility with deprecation warnings
   - Updated 4 downstream integrations
   - Added comprehensive test suite
   - Zero ruff errors, 100% type hints

   XP: +200 (CONSOLIDATION, ARCHITECTURE, BACKWARD_COMPAT)
   ```

SUCCESS CRITERIA:
- ✅ All 6 modules consolidated
- ✅ Zero import errors
- ✅ All tests passing
- ✅ Zero ruff/black errors
- ✅ Backward compatibility verified
- ✅ Migration guide complete
"""


async def main() -> None:
    """Launch ChatDev consolidation task."""
    logger.info("=" * 80)
    logger.info("🚀 LAUNCHING CHATDEV MULTI-AGENT CONSOLIDATION")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Task: Consolidate 6 ChatDev modules → unified_chatdev_bridge.py")
    logger.info("Agents: CEO → CTO → Programmer → Tester → Reviewer")
    logger.info("Target XP: +200 (CONSOLIDATION, ARCHITECTURE, BACKWARD_COMPAT)")
    logger.info("")
    logger.info("This will take 2-3 hours for ChatDev multi-agent collaboration...")
    logger.info("")

    # Initialize router
    router = AgentTaskRouter()

    # Route to ChatDev
    logger.info("🤖 Routing task to ChatDev multi-agent system...")

    result = await router.route_task(
        task_type="generate",
        description=CONSOLIDATION_TASK,
        context={
            "project_name": "ChatDevConsolidation",
            "target_directory": "src/integration",
            "xp_target": 200,
            "tags": ["CONSOLIDATION", "ARCHITECTURE", "BACKWARD_COMPAT"],
        },
        target_system="chatdev",
        priority="HIGH",
    )

    logger.info("")
    logger.info("=" * 80)
    logger.info("📋 CHATDEV TASK ROUTING RESULT")
    logger.info("=" * 80)
    logger.info(f"Status: {result.get('status', 'unknown')}")
    logger.info(f"System: {result.get('system', 'unknown')}")

    if "task_id" in result:
        logger.info(f"Task ID: {result['task_id']}")

    if "output_directory" in result:
        logger.info(f"Output: {result['output_directory']}")

    if "error" in result:
        logger.error(f"❌ Error: {result['error']}")
        if "suggestion" in result:
            logger.info(f"💡 Suggestion: {result['suggestion']}")

    logger.info("")
    logger.info("ChatDev Multi-Agent Workflow:")
    logger.info("  👔 CEO: Parse requirements → Create project plan")
    logger.info("  👨‍💼 CTO: Design facade architecture → Plan backward compatibility")
    logger.info("  👨‍💻 Programmer: Implement unified_chatdev_bridge.py")
    logger.info("  🧪 Tester: Create test suite → Validate backward compatibility")
    logger.info("  📝 Reviewer: Code review → Documentation")
    logger.info("")
    logger.info("Monitor ChatDev in NuSyQ/ChatDev/WareHouse/ChatDevConsolidation_*/")
    logger.info("")
    logger.info("After ChatDev completes:")
    logger.info("  1. Review generated code")
    logger.info("  2. Run: pytest tests/integration/test_unified_chatdev_bridge.py")
    logger.info("  3. Run: python -m ruff check src/integration/unified_chatdev_bridge.py")
    logger.info("  4. Run: python -m black src/integration/unified_chatdev_bridge.py --check")
    logger.info("  5. Commit with quest-commit-bridge for +200 XP")
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
