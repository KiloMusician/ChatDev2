#!/usr/bin/env python3
"""🎯 Agent Orchestration Hub - Live Demonstration

Shows the unified agent hub in action:
- Conversational task routing
- Multi-system coordination
- Consciousness enrichment
- Quest integration
- Error recovery

Run: python demo_agent_hub.py
"""

import asyncio
import json
import logging

from src.tools.agent_task_router import AgentTaskRouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def demo_ollama_analysis():
    """Demo: Analyze code with Ollama local LLM."""
    logger.info("=" * 80)
    logger.info("DEMO 1: Code Analysis with Ollama")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    try:
        result = await router.route_task(
            task_type="analyze",
            description="Analyze src/tools/agent_task_router.py for code quality",
            target_system="ollama",
            context={
                "file": "src/tools/agent_task_router.py",
                "focus": "complexity, maintainability",
            },
        )

        logger.info(f"✅ Task Status: {result['status']}")
        logger.info(f"🤖 System Used: {result.get('system', 'unknown')}")
        if result.get("output"):
            logger.info(f"📝 Output Preview: {str(result['output'])[:200]}...")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


async def demo_chatdev_generation():
    """Demo: Generate project with ChatDev multi-agent team."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Project Generation with ChatDev")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    try:
        result = await router.route_task(
            task_type="generate",
            description="Create a simple calculator app with add, subtract, multiply, divide",
            target_system="chatdev",
            context={
                "project_name": "SimpleCalculator",
                "chatdev_model": "GPT_3_5_TURBO",
                "chatdev_org": "NuSyQ",
            },
        )

        logger.info(f"✅ Task Status: {result['status']}")
        logger.info(f"🤖 System Used: {result.get('system', 'unknown')}")

        if result.get("status") == "success":
            output = result.get("output", {})
            logger.info(f"🎉 ChatDev PID: {output.get('pid', 'N/A')}")
            logger.info(f"📦 Project: {output.get('project_name', 'N/A')}")
            logger.info(f"🏗️  Model: {output.get('model', 'N/A')}")
        else:
            logger.warning(f"⚠️ Error: {result.get('error', 'Unknown error')}")
            logger.info(f"💡 Suggestion: {result.get('suggestion', 'None')}")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


async def demo_consciousness_enrichment():
    """Demo: Task with consciousness-aware enrichment."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Consciousness-Enriched Task Routing")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    try:
        result = await router.route_task(
            task_type="review",
            description="Review the agent orchestration architecture for improvements",
            target_system="consciousness",
            context={"scope": "architecture", "focus": "integration_points"},
        )

        logger.info(f"✅ Task Status: {result['status']}")
        logger.info(f"🧠 System Used: {result.get('system', 'unknown')}")

        if result.get("hint"):
            hint = result["hint"]
            logger.info(f"💭 Consciousness Summary: {hint.get('summary', 'N/A')}")
            logger.info(f"🏷️  Tags: {', '.join(hint.get('tags', []) or ['None'])}")
            logger.info(f"📊 Confidence: {hint.get('confidence', 0):.2f}")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


async def demo_quantum_healing():
    """Demo: Self-healing with Quantum Problem Resolver."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Quantum Healing & Error Recovery")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    try:
        result = await router.route_task(
            task_type="debug",
            description="Fix import errors in the codebase",
            target_system="quantum_resolver",
            context={"scope": "imports", "severity": "high"},
        )

        logger.info(f"✅ Task Status: {result['status']}")
        logger.info(f"⚛️  System Used: {result.get('system', 'unknown')}")
        logger.info(f"🔧 Healing Result: {result.get('output', 'N/A')}")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


async def demo_auto_routing():
    """Demo: Auto-routing with orchestrator intelligence."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: Auto-Routing (Orchestrator Decides)")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    try:
        result = await router.route_task(
            task_type="plan",
            description="Plan next development sprint for agent coordination",
            target_system="auto",  # Let orchestrator decide
            priority="HIGH",
            context={"project": "agent_hub", "phase": "consolidation"},
        )

        logger.info(f"✅ Task Status: {result['status']}")
        logger.info(f"🎯 Task ID: {result.get('task_id', 'unknown')}")
        logger.info(f"📋 Note: {result.get('note', 'N/A')}")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


async def demo_quest_integration():
    """Demo: Quest log integration."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 6: Quest System Integration")
    logger.info("=" * 80)

    router = AgentTaskRouter()

    # Execute multiple tasks to populate quest log
    tasks = [
        ("analyze", "Check system health", "ollama"),
        ("document", "Update README", "auto"),
    ]

    for task_type, description, target in tasks:
        try:
            await router.route_task(
                task_type=task_type,
                description=description,
                target_system=target,
                context={"consciousness_enrich": False},
            )
        except Exception as e:
            logger.warning(f"Task failed: {e}")

    # Read quest log
    if router.quest_log_path.exists():
        quest_entries = router.quest_log_path.read_text().strip().split("\n")
        logger.info(f"📜 Quest Log Entries: {len(quest_entries)}")
        logger.info("\nRecent Entries:")
        for entry in quest_entries[-3:]:
            try:
                data = json.loads(entry)
                logger.info(
                    f"  - [{data['status']}] {data['task_type']}: {data['description'][:50]}..."
                )
            except Exception:
                pass
    else:
        logger.warning("⚠️ Quest log not found")


async def demo_all():
    """Run all demonstrations."""
    logger.info("\n🚀 Agent Orchestration Hub - Full Demonstration Suite\n")

    demos = [
        ("Ollama Analysis", demo_ollama_analysis),
        ("ChatDev Generation", demo_chatdev_generation),
        ("Consciousness Enrichment", demo_consciousness_enrichment),
        ("Quantum Healing", demo_quantum_healing),
        ("Auto Routing", demo_auto_routing),
        ("Quest Integration", demo_quest_integration),
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            logger.error(f"❌ {name} demo failed: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("🎉 All Demonstrations Complete!")
    logger.info("=" * 80)
    logger.info(
        "\n💡 Next Steps:\n"
        "  1. Check quest log: src/Rosetta_Quest_System/quest_log.jsonl\n"
        "  2. Review receipts: docs/tracing/RECEIPTS/\n"
        "  3. Run tests: pytest tests/test_agent_task_router.py -v\n"
    )


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        demo_map = {
            "ollama": demo_ollama_analysis,
            "chatdev": demo_chatdev_generation,
            "consciousness": demo_consciousness_enrichment,
            "quantum": demo_quantum_healing,
            "auto": demo_auto_routing,
            "quest": demo_quest_integration,
        }
        demo_name = sys.argv[1].lower()
        if demo_name in demo_map:
            await demo_map[demo_name]()
        else:
            logger.error(f"Unknown demo: {demo_name}")
            logger.info(f"Available: {', '.join(demo_map.keys())}")
    else:
        await demo_all()


if __name__ == "__main__":
    asyncio.run(main())
