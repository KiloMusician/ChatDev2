#!/usr/bin/env python3
"""Automated Coding Fundamentals Fix Orchestrator.

Leverages the real Multi-AI Orchestrator instead of ad‑hoc/manual edits.
Refactors bare ``except:`` clauses and adds timeouts to risky network calls.
"""

# (Path / Any previously used in earlier revisions; remove unused imports to satisfy linters.)

# In normal execution the repository root is already on sys.path because this
# script lives in ``scripts/`` directly under the project root. Avoid mutating
# ``sys.path`` – linters flag mid‑module path manipulation. If an execution
# environment ever requires it, prefer a wrapper launcher instead.

from src.orchestration.unified_ai_orchestrator import (
    AISystemType,
    MultiAIOrchestrator,
    OrchestrationTask,
    TaskPriority,
)


def main():
    """Use the ACTUAL orchestration system to fix coding fundamentals"""
    print("🎯 Activating Multi-AI Orchestration System...")
    print("=" * 80)

    # Initialize orchestrator (limit exception scope – avoid blanket Exception)
    try:
        orchestrator = MultiAIOrchestrator()
        print("✅ Multi-AI Orchestrator initialized")
    except (RuntimeError, ImportError, ValueError, OSError) as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        print("\n💡 Falling back to manual ChatDev invocation...")
        use_chatdev_directly()
        return

    # Define the coding fundamentals fix task
    task_description = """
Fix 40 bare except: clauses in the NuSyQ-Hub codebase.

CRITICAL TASK: Replace all bare 'except:' statements with specific exception types.

Priority files (fix these first):
1. src/consciousness/the_oldest_house.py (3 instances)
2. src/core/performance_monitor.py (2 instances)
3. src/healing/repository_health_restorer.py (1 instance)
4. src/game_development/zeta21_game_pipeline.py (1 instance)

Pattern to fix:
    ❌ BAD:
    try:
        operation()
    except:
        pass

    ✅ GOOD:
    try:
        operation()
    except (SpecificError, AnotherError) as e:
        logger.error(f"Operation failed: {e}", exc_info=True)

Also add missing timeout parameters to 8 network requests:
- test_continue_integration.py (2 instances)
- scripts/codex_integration.py (1 instance)
- src/ai/ollama_chatdev_integrator.py (1 instance)
- src/ai/ollama_integration.py (1 instance)
- src/integration/ollama_integration.py (1 instance)

Generate a comprehensive fix with proper exception handling and timeouts.
    """

    print("\n📋 Task Description:")
    print(task_description)
    print("\n" + "=" * 80)

    # Submit task to orchestrator using the current Task API
    try:
        print("\n🚀 Submitting task to Multi-AI Orchestrator...")
        task = OrchestrationTask(
            task_id="",  # allow orchestrator to assign
            task_type="code_quality",
            content=task_description.strip(),
            priority=TaskPriority.CRITICAL,
            preferred_systems=[AISystemType.CHATDEV],
            context={"origin": "scripts/orchestrate_coding_fixes.py"},
        )
        task_id = orchestrator.submit_task(task)

        print(f"\n✅ Task submitted: {task_id}")
        print("\n📊 Orchestrator will:")
        print("   1. Analyze the codebase")
        print("   2. Generate fixes for all bare except clauses")
        print("   3. Add timeout parameters to network requests")
        print("   4. Create comprehensive test coverage")
        print("   5. Generate documentation")

    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
        print(f"\n❌ Orchestrator task submission failed: {e}")
        print("\n💡 Trying direct ChatDev invocation...")
        use_chatdev_directly()


def use_chatdev_directly():
    """Fallback: Use ChatDev directly if orchestrator unavailable"""
    print("\n" + "=" * 80)
    print("🤖 Using ChatDev Multi-Agent System Directly")
    print("=" * 80)

    try:
        from src.integration.chatdev_launcher import launch_chatdev_session

        task = {
            "name": "Fix Coding Fundamentals - Bare Except Clauses",
            "description": """
Fix all 40 bare 'except:' clauses across the codebase with specific exception handling.

REQUIREMENTS:
1. Replace bare except: with specific exception types
2. Add logging to all exception handlers
3. Add timeout parameters to all network requests
4. Maintain existing functionality
5. Add comprehensive error context

FILES TO FIX (priority order):
- src/consciousness/the_oldest_house.py
- src/core/performance_monitor.py
- src/healing/repository_health_restorer.py
- src/game_development/zeta21_game_pipeline.py
- test_continue_integration.py
- scripts/codex_integration.py
- src/ai/ollama_chatdev_integrator.py
- src/ai/ollama_integration.py
- src/integration/ollama_integration.py

DELIVERABLES:
1. Fixed Python files with proper exception handling
2. Test suite validating fixes
3. Documentation of changes
4. Verification script
            """,
            "agent_roles": ["Programmer", "Code Reviewer", "Tester"],
            "complexity": "high",
        }

        print(f"\n📋 ChatDev Task: {task['name']}")
        print(f"👥 Agents: {', '.join(task['agent_roles'])}")
        print("\n🚀 Launching ChatDev session...")

        result = launch_chatdev_session(task)
        print(f"\n✅ ChatDev session result: {result}")

    except ImportError as e:
        print(f"\n❌ ChatDev not available: {e}")
        print("\n💡 Manual fix instructions:")
        print("   1. Read Reports/coding_fundamentals_scan.txt")
        print("   2. Fix files in priority order")
        print("   3. Run: python scripts/fix_coding_fundamentals.py --verify")
    except (RuntimeError, ValueError) as e:
        print(f"\n❌ ChatDev execution error: {e}")
        print("\n📄 See docs/CODING_FUNDAMENTALS_AUDIT.md for manual fix patterns")


if __name__ == "__main__":
    main()
