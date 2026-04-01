"""Run a sample multi-agent orchestration and export metrics."""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# pylint: disable=wrong-import-position
from config.agent_router import (  # noqa: E402
    Task,
    TaskComplexity,
    TaskType,
)
from mcp_server.main import NuSyQMCPServer  # noqa: E402


async def main():
    """Run sample multi-agent orchestration and export metrics."""
    server = NuSyQMCPServer()
    metrics = server.metrics
    os.environ.setdefault("OLLAMA_MAX_TIMEOUT_SECONDS", "180")

    # Pre-compute router decision for visibility and metrics
    router_task = Task(
        description="Implement cache invalidation for stale build artifacts",
        task_type=TaskType.BUG_FIX,
        complexity=TaskComplexity.MODERATE,
        requires_reasoning=True,
    )

    router_decision = None
    if server.agent_router:
        decision = server.agent_router.route_task(router_task)
        router_decision = {
            "primary_agent": decision.agent.name,
            "alternatives": [a.name for a in decision.alternatives[:2]],
            "coordination": decision.coordination_pattern,
            "estimated_cost": decision.estimated_cost,
            "rationale": decision.rationale,
        }

    start_time = asyncio.get_event_loop().time()
    try:
        # pylint: disable=protected-access
        result = await server._multi_agent_orchestration(
            {
                "task": router_task.description,
                "task_type": router_task.task_type.value,
                "complexity": router_task.complexity.value,
                "mode": "PARALLEL_CONSENSUS",
                "include_ai_council": False,
                "implement_with_chatdev": False,
            }
        )
    except Exception as exc:  # pylint: disable=broad-except
        result = {
            "success": False,
            "error": str(exc),
            "routing_decision": router_decision,
        }
        print("Orchestration failed:", exc)
    finally:
        if metrics and router_decision:
            duration = asyncio.get_event_loop().time() - start_time
            metrics.record_agent(
                agent_name=router_decision["primary_agent"],
                task_type="multi_agent_orchestration",
                duration=duration,
                success=bool(result.get("success", False)),
            )

    print("Routing decision:", result.get("routing_decision") or router_decision)
    print("Agents used:", result.get("agents_used"))

    # Export metrics and agent trends
    if metrics:
        agent_stats = metrics.get_agent_stats()
        print("Agent metrics:", agent_stats)

        agent_trends = metrics.export_agent_trends()
        summary_path = metrics.export_summary()
        print("Agent trends exported to:", agent_trends)
        print("Summary exported to:", summary_path)


if __name__ == "__main__":
    asyncio.run(main())
