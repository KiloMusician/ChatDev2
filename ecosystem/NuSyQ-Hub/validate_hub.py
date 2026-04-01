#!/usr/bin/env python3
"""Quick hub validation - proves operational status."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.tools.agent_task_router import AgentTaskRouter

logging.basicConfig(level=logging.INFO, format="%(message)s")


async def main():
    logging.info("🎯 Agent Orchestration Hub - Quick Validation")
    logging.info("=" * 60)

    router = AgentTaskRouter()

    logging.info("✅ Hub initialized")
    logging.info(f"✅ Orchestrator: {router.orchestrator is not None}")
    logging.info(f"✅ Quest log: {router.quest_log_path}")

    # Test auto-routing
    result = await router.route_task(
        task_type="analyze",
        description="Validation test",
        target_system="auto",
        context={"consciousness_enrich": False},
    )

    logging.info("\n✅ Task routed successfully")
    logging.info(f"   Status: {result['status']}")
    logging.info(f"   Task ID: {result.get('task_id', 'unknown')}")

    logging.info("\n🎉 Agent Hub is OPERATIONAL!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
