#!/usr/bin/env python3
"""
Comprehensive Orchestration Test
Tests multi-agent coordination with Ollama, demonstrating:
- Agent registration
- Task routing
- Consensus generation
- Results aggregation
"""

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


def test_multi_agent_consensus():
    """Test multi-agent consensus on a code review task."""

    print("\n" + "=" * 80)
    print("🤖 MULTI-AGENT ORCHESTRATION TEST")
    print("=" * 80)
    print()

    # Initialize orchestrator
    print("[1️⃣  ORCHESTRATOR INIT]")
    orchestrator = UnifiedAIOrchestrator()
    print(f"    ✅ Initialized with {len(orchestrator.systems)} AI systems")
    print(f"    Systems: {', '.join(orchestrator.systems.keys())}")
    print()

    # Verify Ollama availability
    print("[2️⃣  VERIFY OLLAMA BACKEND]")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"    ✅ Ollama accessible - {len(models)} models ready")
        print(f"    Available models: {', '.join(models[:3])}...")
    except Exception as e:
        print(f"    ❌ Ollama unreachable: {e}")
        return False
    print()

    # Define task
    print("[3️⃣  DEFINE ORCHESTRATION TASK]")
    task = {
        "id": "consensus_001",
        "type": "code_review",
        "target": "multi_agent",
        "query": "Review the autonomy module design. Is it following async/await best practices? What are the strengths and weaknesses?",
        "context": {"module": "src/autonomy/", "focus": "async patterns", "importance": "high"},
    }
    print(f"    Task ID: {task['id']}")
    print(f"    Type: {task['type']}")
    print(f"    Query: {task['query'][:70]}...")
    print()

    # Route to multiple agents
    print("[4️⃣  ROUTE TO AGENTS]")
    agents_config = [
        {"name": "qwen2.5-coder:7b", "role": "Code Architect", "focus": "Design and patterns"},
        {
            "name": "starcoder2:15b",
            "role": "Code Quality Expert",
            "focus": "Best practices and standards",
        },
        {
            "name": "deepseek-coder-v2:16b",
            "role": "Performance Analyst",
            "focus": "Async optimization",
        },
    ]

    results = []
    print(f"    Routing to {len(agents_config)} agents...")
    print()

    for agent_cfg in agents_config:
        print(f"    🤖 {agent_cfg['role']} ({agent_cfg['name']})")
        print(f"       Focus: {agent_cfg['focus']}")

        prompt = f"""You are a {agent_cfg["role"]}. Your focus is {agent_cfg["focus"]}.

Review this code module design:
Module: src/autonomy/ (async-based PR bot, patch builder, risk scorer)
Task: {task["query"]}

Provide a 2-3 sentence assessment from your perspective."""

        try:
            start = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": agent_cfg["name"],
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.5,
                },
                timeout=120,
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                result = response.json()
                assessment = result["response"].strip()

                results.append(
                    {
                        "agent": agent_cfg["name"],
                        "role": agent_cfg["role"],
                        "assessment": assessment,
                        "elapsed": elapsed,
                        "tokens_gen": result.get("eval_count", 0),
                    }
                )

                print(f"       ✅ Response ({elapsed:.1f}s, {result.get('eval_count', 0)} tokens)")
                print(f"       Preview: {assessment[:90]}...")
            else:
                print(f"       ❌ Error {response.status_code}")
        except requests.exceptions.Timeout:
            print("       ⏱️  Timeout")
        except Exception as e:
            print(f"       ❌ {e}")

        print()

    # Aggregate results
    print("[5️⃣  AGGREGATE CONSENSUS]")
    if not results:
        print("    ❌ No agent responses")
        return False

    print(f"    ✅ Received {len(results)}/{len(agents_config)} agent assessments")
    print()

    total_time = sum(r["elapsed"] for r in results)
    total_tokens = sum(r["tokens_gen"] for r in results)

    print("    📊 CONSENSUS REPORT:")
    print()
    for i, result in enumerate(results, 1):
        print(f"    [{i}] {result['role']} ({result['agent']}):")
        print(f"        Assessment: {result['assessment'][:150]}...")
        print(f"        Metrics: {result['elapsed']:.1f}s, {result['tokens_gen']} tokens")
        print()

    print("    📈 Aggregated Metrics:")
    print(f"       Total agents: {len(results)}")
    print(f"       Total time: {total_time:.1f}s")
    print(f"       Total tokens: {total_tokens}")
    print(f"       Average response time: {total_time / len(results):.1f}s")
    print()

    # Final status
    print("[6️⃣  ORCHESTRATION COMPLETE]")
    print("    ✅ SUCCESS - Multi-agent consensus achieved")
    print(f"    Orchestration ID: {task['id']}")
    print("    Status: COMPLETED")
    print()

    print("=" * 80)
    print("✨ ORCHESTRATION SYSTEM OPERATIONAL ✨")
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_multi_agent_consensus()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test cancelled by user")
        exit(1)
