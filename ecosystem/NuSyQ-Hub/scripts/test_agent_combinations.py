#!/usr/bin/env python3
"""
Agent-Specific Test Combinations
Tests specialized agent pairings for common orchestration scenarios.
"""

import json
import sys
import time
from datetime import datetime, timezone, UTC
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator


class AgentTestScenario:
    """Test specialized agent combinations."""

    def __init__(self, name: str, agents: list, query: str, scenario_type: str):
        self.name = name
        self.agents = agents
        self.query = query
        self.scenario_type = scenario_type
        self.results = []

    def run(self, timeout: int = 120) -> dict:
        """Execute test scenario."""
        print(f"\n{'=' * 80}")
        print(f"🎯 {self.name}")
        print(f"{'=' * 80}")
        print(f"Scenario: {self.scenario_type}")
        print(f"Query: {self.query[:70]}...")
        print(f"Agents: {len(self.agents)}")
        print()

        start = time.time()

        for agent in self.agents:
            print(f"  Testing {agent['model'][:20]}...", end=" ")

            prompt = f"Role: {agent['role']}\n\nQuestion: {self.query}"

            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": agent["model"],
                        "prompt": prompt,
                        "stream": False,
                        "temperature": agent.get("temperature", 0.3),
                    },
                    timeout=timeout,
                )

                if response.status_code == 200:
                    result = response.json()
                    self.results.append(
                        {
                            "model": agent["model"],
                            "role": agent["role"],
                            "success": True,
                            "tokens": result.get("eval_count", 0),
                            "response_length": len(result.get("response", "")),
                        }
                    )
                    print(f"✅ ({result.get('eval_count', 0)} tokens)")
                else:
                    self.results.append(
                        {
                            "model": agent["model"],
                            "role": agent["role"],
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                        }
                    )
                    print("❌")
            except Exception as e:
                self.results.append(
                    {
                        "model": agent["model"],
                        "role": agent["role"],
                        "success": False,
                        "error": str(e),
                    }
                )
                print("❌")

        elapsed = time.time() - start

        print()
        successful = sum(1 for r in self.results if r["success"])
        print(f"Results: {successful}/{len(self.agents)} successful in {elapsed:.1f}s")
        print()

        return {
            "scenario": self.name,
            "scenario_type": self.scenario_type,
            "agents_tested": len(self.agents),
            "successful": successful,
            "elapsed": elapsed,
            "results": self.results,
            "timestamp": datetime.now(UTC).isoformat(),
        }


def run_all_scenarios():
    """Run comprehensive agent combination tests."""

    print("\n" + "=" * 80)
    print("🤖 AGENT-SPECIFIC TEST COMBINATIONS")
    print("=" * 80)
    print()

    # Initialize orchestrator
    print("[INIT] Orchestrator initialization...")
    _ = UnifiedAIOrchestrator()
    print("[INIT] ✅ Ready")
    print()

    # Define scenarios
    scenarios = [
        # Scenario 1: Code Review Team
        AgentTestScenario(
            name="Code Review Team",
            agents=[
                {"model": "qwen2.5-coder:7b", "role": "Code Architecture Reviewer"},
                {"model": "starcoder2:15b", "role": "Performance Reviewer"},
                {"model": "deepseek-coder-v2:16b", "role": "Security Reviewer"},
            ],
            query="Review the autonomy module design - is it following best practices for async/await?",
            scenario_type="code_review",
        ),
        # Scenario 2: Fast Analysis Team (speed-focused)
        AgentTestScenario(
            name="Fast Analysis Team",
            agents=[
                {"model": "qwen2.5-coder:7b", "role": "Quick Analyst"},
                {"model": "phi3.5:latest", "role": "Fast Processor"},
            ],
            query="What does the risk_scorer module do in 1-2 sentences?",
            scenario_type="fast_analysis",
        ),
        # Scenario 3: Deep Analysis Team (comprehensiveness-focused)
        AgentTestScenario(
            name="Deep Analysis Team",
            agents=[
                {"model": "deepseek-coder-v2:16b", "role": "Deep Analyzer"},
                {"model": "llama3.1:8b", "role": "Comprehensive Analyst"},
            ],
            query="Explain the complete flow of autonomy module: PR creation → patching → risk assessment",
            scenario_type="deep_analysis",
        ),
        # Scenario 4: Specialized Experts
        AgentTestScenario(
            name="Specialized Experts",
            agents=[
                {"model": "starcoder2:15b", "role": "Coding Standard Expert", "temperature": 0.2},
                {"model": "llama3.1:8b", "role": "Documentation Expert", "temperature": 0.3},
                {"model": "gemma2:9b", "role": "Integration Expert", "temperature": 0.4},
            ],
            query="How should Python async/await be documented and integrated into team standards?",
            scenario_type="specialized",
        ),
    ]

    # Run all scenarios
    all_results = []
    for scenario in scenarios:
        result = scenario.run()
        all_results.append(result)

    # Summary
    print()
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print()

    total_agents = sum(r["agents_tested"] for r in all_results)
    total_successful = sum(r["successful"] for r in all_results)
    total_time = sum(r["elapsed"] for r in all_results)

    print(f"Scenarios tested: {len(all_results)}")
    print(f"Total agents: {total_agents}")
    print(f"Successful: {total_successful}/{total_agents}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Success rate: {100 * total_successful / total_agents:.0f}%")
    print()

    for result in all_results:
        print(f"  ✓ {result['scenario']}: {result['successful']}/{result['agents_tested']}")

    print()
    print("=" * 80)

    # Log to quest
    quest_log = Path(__file__).parent.parent / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "task_type": "agent_combination_tests",
        "description": "Agent-specific test combinations for specialized scenarios",
        "status": "completed",
        "result": {
            "scenarios": len(all_results),
            "total_agents": total_agents,
            "successful": total_successful,
            "success_rate": f"{100 * total_successful / total_agents:.0f}%",
            "elapsed": total_time,
            "scenario_results": all_results,
        },
    }

    with open(quest_log, "a") as f:
        f.write(json.dumps(entry) + "\n")

    print("\n✅ Results logged to quest_log.jsonl")
    print()

    return all_results


if __name__ == "__main__":
    try:
        run_all_scenarios()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test cancelled")
