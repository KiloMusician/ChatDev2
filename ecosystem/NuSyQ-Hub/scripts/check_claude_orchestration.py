#!/usr/bin/env python3
"""Check that the AgentTaskRouter can delegate tasks to Claude.

This script sends a simple analyze task to Claude via the orchestration layer and
prints the result.
"""

import asyncio
import sys
from pathlib import Path

# Ensure repo root is on python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tools.agent_task_router import AgentTaskRouter


async def main() -> None:
    router = AgentTaskRouter()
    result = await router.route_task(
        task_type="analyze",
        description="Smoke test: can Claude respond via AgentTaskRouter?",
        context={},
        target_system="claude_cli",
    )
    print("RESULT:\n", result)


if __name__ == "__main__":
    asyncio.run(main())
