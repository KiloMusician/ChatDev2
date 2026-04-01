#!/usr/bin/env python3
"""Demo: Route Analysis Request to Ollama via AgentTaskRouter.

This demonstrates the conversational orchestration interface where we
ask the router to analyze a complex function using Ollama.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from src.tools.agent_task_router import AgentTaskRouter


async def main():
    router = AgentTaskRouter()

    print("=" * 70)
    print("🤖 AGENT TASK ROUTER - CONVERSATIONAL ORCHESTRATION DEMO")
    print("=" * 70)
    print()
    print("📤 Routing analysis request to Ollama local LLM...")
    print()

    result = await router.route_task(
        task_type="analyze",
        description="""The _route_to_ollama() function at lines 1121-1210 in agent_task_router.py
has cognitive complexity 19, exceeds limit of 15. Key issues:
1. model_map defined twice (lines 1125 and 1147)
2. Nested try-except with integrator then adapter fallback (lines 1138-1210)
3. 6-level deep conditionals for response type checking/normalization
4. Error message extraction duplicated (lines 1200-1204)

Suggest specific extract-method refactorings with line ranges and new method signatures.""",
        context={
            "file": "src/tools/agent_task_router.py",
            "lines": "1121-1210",
            "language": "python",
            "constraint": "Keep backwards compatibility with existing callers",
        },
        target_system="ollama",
        priority="high",
    )

    print("=" * 70)
    print("🎯 ORCHESTRATION RESPONSE")
    print("=" * 70)
    print(f"Status: {result.get('status')}")
    print(f"System: {result.get('system')}")
    print(f"Model: {result.get('model', 'N/A')}")
    print()

    if result.get("output"):
        print("📊 Analysis from Ollama:")
        print("-" * 70)
        print(result["output"])
        print("-" * 70)
    elif result.get("error"):
        print(f"⚠️  Error: {result['error']}")
    else:
        print("No analysis output received")

    print()
    print("✅ Orchestration demonstration complete")
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.get("status") == "success" else 1)
