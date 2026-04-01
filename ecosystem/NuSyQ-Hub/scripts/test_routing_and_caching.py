"""
Integration Test: Intelligent Routing + Response Caching

Demonstrates how the routing and caching systems work together
to optimize orchestration task assignment and response retrieval.

OmniTag: [integration test, orchestration, routing, caching, performance]
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.orchestration.agent_response_cache import AgentResponseCache
    from src.orchestration.intelligent_agent_router import IntelligentAgentRouter, TaskType
except ImportError:
    # Fallback for running from scripts directory
    from orchestration.agent_response_cache import AgentResponseCache
    from orchestration.intelligent_agent_router import IntelligentAgentRouter, TaskType

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class OptimizedOrchestrationEngine:
    """
    Orchestration engine that combines routing and caching.

    Workflow:
    1. Classify incoming task
    2. Check cache for previous results
    3. Route to optimal agent if cache miss
    4. Cache result upon completion
    5. Track metrics for observability
    """

    def __init__(self):
        self.router = IntelligentAgentRouter()
        self.cache = AgentResponseCache(max_entries=500, ttl_minutes=15)
        self.execution_log: List[Dict] = []

    def process_task(self, task_description: str, available_agents: List[str], simulate_execution: bool = True) -> Dict:
        """
        Process a task using routing and caching.

        Args:
            task_description: Description of the task
            available_agents: List of available agent models
            simulate_execution: If True, simulate the execution

        Returns:
            Result dict with agent, response, metrics
        """
        start_time = time.time()

        # Step 1: Classify task
        task_type = self.router.classify_task(task_description)
        logger.info(f"📋 Task classified as: {task_type.value}")

        # Step 2: Route task to optimal agent
        selected_agent, route_info = self.router.route_task(task_description, task_type, available_agents)
        logger.info(f"🎯 Routed to: {selected_agent}")
        logger.info(f"   Temperature: {route_info['temperature']}, Max tokens: {route_info['max_tokens']}")

        # Step 3: Check cache
        cached_response = self.cache.get(selected_agent, task_description)

        if cached_response is not None:
            logger.info("💾 CACHE HIT - Retrieved instantly")
            result = {
                "source": "cache",
                "agent": selected_agent,
                "task_type": task_type.value,
                "response": cached_response,
                "cache_age_seconds": cached_response.get("_cache_age", 0),
                "latency": time.time() - start_time,
            }
        else:
            logger.info("🔄 Cache miss - Executing task...")

            # Step 4: Simulate execution
            if simulate_execution:
                execution_time = 5 + (hash(selected_agent) % 10)  # Simulate 5-15s
                time.sleep(0.1)  # Simulate some work

                response = {
                    "content": f"Resolved by {selected_agent}: {task_description[:50]}...",
                    "tokens": 200 + (hash(task_description) % 300),
                    "execution_time": execution_time,
                }

            # Step 5: Cache the result
            self.cache.set(selected_agent, task_description, response)
            logger.info(f"💾 Cached response ({len(json.dumps(response))} bytes)")

            result = {
                "source": "execution",
                "agent": selected_agent,
                "task_type": task_type.value,
                "response": response,
                "latency": time.time() - start_time,
            }

        # Log execution
        self.execution_log.append(result)
        logger.info(f"✅ Completed in {result['latency']:.2f}s\n")

        return result

    def run_scenario(
        self,
        scenario_name: str,
        tasks: List[Tuple[str, TaskType]],
        available_agents: List[str],
        simulate_execution: bool = True,
    ) -> Dict:
        """
        Run a scenario with multiple tasks.

        Args:
            scenario_name: Name of the scenario
            tasks: List of (task_description, expected_type) tuples
            available_agents: Available agent models
            simulate_execution: If True, simulate execution

        Returns:
            Scenario results with metrics
        """
        logger.info(f"{'=' * 60}")
        logger.info(f"🎬 SCENARIO: {scenario_name}")
        logger.info(f"{'=' * 60}\n")

        results = []
        cache_hits = 0
        total_latency = 0

        for task_desc, _expected_type in tasks:
            logger.info(f"📌 Task: {task_desc[:60]}...")
            result = self.process_task(task_desc, available_agents, simulate_execution)

            if result["source"] == "cache":
                cache_hits += 1

            total_latency += result["latency"]
            results.append(result)

        scenario_result = {
            "scenario": scenario_name,
            "tasks_run": len(tasks),
            "cache_hits": cache_hits,
            "cache_hit_rate": f"{(cache_hits / len(tasks) * 100):.1f}%",
            "total_latency": total_latency,
            "avg_latency": total_latency / len(tasks),
            "results": results,
        }

        return scenario_result

    def generate_integration_report(self) -> str:
        """Generate report of integration test results."""
        report = ["🔗 ORCHESTRATION INTEGRATION TEST REPORT\n"]

        # Routing stats
        routing_report = self.router.generate_routing_report()
        report.append(routing_report)

        report.append("\n" + "-" * 60 + "\n")

        # Cache stats
        cache_report = self.cache.generate_report()
        report.append(cache_report)

        report.append("\n[INTEGRATION METRICS]")

        if self.execution_log:
            cache_hits = sum(1 for e in self.execution_log if e["source"] == "cache")
            total_tasks = len(self.execution_log)
            total_latency = sum(e["latency"] for e in self.execution_log)

            report.append(f"  Total tasks: {total_tasks}")
            report.append(f"  Cache hits: {cache_hits}")
            report.append(f"  Cache hit rate: {(cache_hits / total_tasks * 100):.1f}%")
            report.append(f"  Total execution time: {total_latency:.2f}s")
            report.append(f"  Average latency: {total_latency / total_tasks:.2f}s")

        return "\n".join(report)


def run_integration_tests():
    """Run comprehensive integration tests."""
    engine = OptimizedOrchestrationEngine()

    # Available agents (subset for testing)
    available = ["qwen2.5-coder:7b", "starcoder2:15b", "deepseek-coder-v2:16b", "llama3.1:8b"]

    # Scenario 1: Code review workflow with repeated queries
    print("\n" + "=" * 70)
    print("INTEGRATION TEST PHASE 1: CODE REVIEW WITH CACHE REUSE")
    print("=" * 70 + "\n")

    code_review_tasks = [
        ("Review this Python code for security issues", TaskType.CODE_REVIEW),
        (
            "Review this Python code for security issues",
            TaskType.CODE_REVIEW,
        ),  # Duplicate - should hit cache
        ("Audit this authentication module for vulnerabilities", TaskType.CODE_REVIEW),
        ("Review this Python code for security issues", TaskType.CODE_REVIEW),  # Another duplicate
    ]

    scenario1 = engine.run_scenario("Code Review with Cache Reuse", code_review_tasks, available)

    print("\n📊 SCENARIO RESULTS:")
    print(f"  Tasks: {scenario1['tasks_run']}")
    print(f"  Cache hits: {scenario1['cache_hits']} ({scenario1['cache_hit_rate']})")
    print(f"  Total time: {scenario1['total_latency']:.2f}s")
    print(f"  Avg per task: {scenario1['avg_latency']:.2f}s")

    # Scenario 2: Mixed workload
    print("\n" + "=" * 70)
    print("INTEGRATION TEST PHASE 2: MIXED WORKLOAD WITH OPTIMIZATION")
    print("=" * 70 + "\n")

    mixed_tasks = [
        ("Generate a REST API implementation", TaskType.CODE_GENERATION),
        ("Generate a REST API implementation", TaskType.CODE_GENERATION),  # Cache hit
        ("Debug this intermittent timeout error", TaskType.DEBUGGING),
        ("Write documentation for the auth module", TaskType.DOCUMENTATION),
        ("Analyze performance bottlenecks", TaskType.ANALYSIS),
        ("Generate a REST API implementation", TaskType.CODE_GENERATION),  # Cache hit
    ]

    scenario2 = engine.run_scenario("Mixed Workload Optimization", mixed_tasks, available)

    print("\n📊 SCENARIO RESULTS:")
    print(f"  Tasks: {scenario2['tasks_run']}")
    print(f"  Cache hits: {scenario2['cache_hits']} ({scenario2['cache_hit_rate']})")
    print(f"  Total time: {scenario2['total_latency']:.2f}s")
    print(f"  Avg per task: {scenario2['avg_latency']:.2f}s")

    # Final report
    print("\n" + "=" * 70)
    print(engine.generate_integration_report())
    print("=" * 70)

    # Persist cache
    print("\n💾 Persisting cache to disk...")
    engine.cache.persist_to_disk()
    print("✅ Cache persisted successfully")


if __name__ == "__main__":
    run_integration_tests()
