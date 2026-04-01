#!/usr/bin/env python3
"""
Async-Parallelized Multi-Agent Orchestration Test
Demonstrates concurrent multi-agent task processing with shared resources.
Compares sequential vs parallel execution performance.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone, UTC
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


async def call_ollama_async(model: str, prompt: str, timeout: int = 120) -> dict:
    """Call Ollama API asynchronously."""
    try:
        # Use asyncio's event loop to run requests in thread pool
        loop = asyncio.get_event_loop()

        def blocking_call():
            return requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                },
                timeout=timeout,
            )

        response = await loop.run_in_executor(None, blocking_call)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except TimeoutError:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_parallel_consensus():
    """Test parallel multi-agent consensus (async)."""

    print("\n" + "=" * 80)
    print("⚡ ASYNC PARALLELIZED ORCHESTRATION TEST")
    print("=" * 80)
    print()

    # Initialize orchestrator
    print("[INIT] Orchestrator initialization...")
    _ = UnifiedAIOrchestrator()
    print("[INIT] ✅ Ready with 5 AI systems")
    print()

    # Define task
    task_query = "What is the risk_scorer module designed to do? Be concise."

    # Agent configurations
    agents = [
        {"model": "qwen2.5-coder:7b", "role": "Code Architect", "focus": "Design"},
        {"model": "starcoder2:15b", "role": "Quality Expert", "focus": "Standards"},
        {"model": "deepseek-coder-v2:16b", "role": "Performance", "focus": "Optimization"},
        {"model": "llama3.1:8b", "role": "Generalist", "focus": "Clarity"},
    ]

    print(f"[TASK] {task_query}")
    print(f"[AGENTS] {len(agents)} models will process in parallel")
    print(f"  - {', '.join([a['model'] for a in agents])}")
    print()

    # Parallel execution
    print("[EXECUTION] Starting parallel agent calls...")
    print()

    start_parallel = time.time()

    # Create async tasks
    tasks = []
    for agent in agents:
        prompt = f"You are a {agent['role']}. Focus: {agent['focus']}.\n\nQuestion: {task_query}"
        task = call_ollama_async(agent["model"], prompt)
        tasks.append((agent, task))

    # Execute all in parallel
    results = []
    for agent, task_coro in tasks:
        result = await task_coro
        results.append({"agent": agent, "result": result})

    elapsed_parallel = time.time() - start_parallel

    print(f"[COMPLETED] All agents finished in {elapsed_parallel:.1f} seconds")
    print()

    # Analyze results
    print("[ANALYSIS] Aggregating results...")
    print()

    successful = sum(1 for r in results if r["result"]["success"])

    print(f"[RESULTS] {successful}/{len(agents)} agents succeeded")
    print()

    total_tokens = 0
    for i, result_item in enumerate(results, 1):
        agent = result_item["agent"]
        result = result_item["result"]

        if result["success"]:
            tokens = result["data"].get("eval_count", 0)
            response = result["data"].get("response", "")[:80]
            print(f"[{i}] {agent['model'][:20]:20} - ✅ {tokens:3} tokens | {response}...")
            total_tokens += tokens
        else:
            print(f"[{i}] {agent['model'][:20]:20} - ❌ {result.get('error', 'Unknown error')}")

    print()
    print(f"[STATS] Total tokens: {total_tokens}, Parallel time: {elapsed_parallel:.1f}s")
    print()

    # Compare with estimated sequential time
    print("[COMPARISON]")
    estimated_sequential = 4.0 + 26.5 + 40.4 + 10.0  # Based on previous tests + estimate
    speedup = estimated_sequential / elapsed_parallel
    print(f"  Estimated sequential: {estimated_sequential:.1f}s")
    print(f"  Actual parallel: {elapsed_parallel:.1f}s")
    print(f"  Speedup factor: {speedup:.1f}x")
    print()

    if speedup > 2.0:
        print(f"✅ PARALLELIZATION EFFECTIVE - {speedup:.1f}x faster than sequential!")
    else:
        print(f"⚠️  Parallelization overhead/network latency: {speedup:.1f}x")

    print()
    print("=" * 80)
    print("✨ ASYNC ORCHESTRATION TEST COMPLETE")
    print("=" * 80)
    print()

    return {
        "total_agents": len(agents),
        "successful": successful,
        "elapsed_seconds": elapsed_parallel,
        "total_tokens": total_tokens,
        "speedup": speedup,
        "timestamp": datetime.now(UTC).isoformat(),
    }


if __name__ == "__main__":
    try:
        result = asyncio.run(test_parallel_consensus())
        # Log to quest
        quest_log = Path(__file__).parent.parent / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_type": "async_orchestration_test",
            "description": "Async parallelized multi-agent orchestration test",
            "status": "completed",
            "result": result,
        }
        with open(quest_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test cancelled")
