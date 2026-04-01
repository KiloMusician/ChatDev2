"""
Multi-Agent System Performance Test
====================================

Tests how many concurrent LLM agents this laptop can handle.

Hardware:
"""

import concurrent.futures
import os
import subprocess
import time

from config.collaboration_advisor import get_collaboration_advisor

new_file_path = os.path.join("tests", "legacy_root", "test_multi_agent_system.py")
print(f"Moving this file to {new_file_path}")


def query_ollama_model(model_name: str, prompt: str, timeout: int = 30):
    """Query a single Ollama model"""
    try:
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration = time.time() - start

        return {
            "model": model_name,
            "success": result.returncode == 0,
            "duration": duration,
            "output_length": len(result.stdout) if result.stdout else 0,
            "error": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "model": model_name,
            "success": False,
            "duration": timeout,
            "error": "Timeout",
        }
    except (subprocess.SubprocessError, OSError, ValueError, TypeError) as e:
        return {"model": model_name, "success": False, "error": str(e)}


def test_concurrent_agents(num_agents: int):
    """Test running multiple Ollama agents concurrently"""
    print(f"\n🧪 Testing {num_agents} concurrent agents...\n")

    models = ["qwen2.5-coder:7b", "codellama:7b", "phi3.5:latest", "llama3.1:8b"][:num_agents]

    prompt = "Write a Python function to calculate fibonacci. Just code."

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_agents) as executor:
        futures = {executor.submit(query_ollama_model, model, prompt): model for model in models}

        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['model']}: {result['duration']:.1f}s")

    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r["success"])

    print("\n📊 Results:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Success rate: {success_count}/{num_agents}")
    print(f"   Avg time per agent: {total_time / num_agents:.1f}s")

    return results


def test_collaboration_advisor():
    """Test the collaboration advisor system"""
    print("\n🤖 Testing Collaboration Advisor\n")

    advisor = get_collaboration_advisor()

    print(f"Available agents: {len(advisor.available_agents)}")
    for agent_type, info in advisor.available_agents.items():
        print(f"  • {agent_type.value}")
        print(f"    Status: {info['status']}")
        print(f"    Max concurrent: {info.get('max_concurrent', 1)}")

    # Test scenarios
    scenarios = [
        {
            "name": "Small bug fix",
            "description": "Fix import error in quantum_workflows",
            "files": ["src/quantum/quantum_workflows.py"],
            "complexity": 5,
        },
        {
            "name": "Large refactor",
            "description": "Refactor entire agent system architecture",
            "files": [
                "config/agent_router.py",
                "config/agent_registry.py",
                "config/agent_config.py",
                "src/core/base_agent.py",
                "src/agents/consciousness_agent.py",
                "tests/test_agents.py",
            ],
            "complexity": 22,
        },
        {
            "name": "Parallel code generation",
            "description": "Generate test files for all 18 modules",
            "files": [f"tests/test_module_{i}.py" for i in range(18)],
            "complexity": 8,
        },
    ]

    print("\n" + "=" * 60)
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Files: {len(scenario['files'])}")
        print(f"   Complexity: {scenario['complexity']}")

        assessment = advisor.assess_workload(
            task_description=scenario["description"],
            files_to_modify=scenario["files"],
            complexity_indicators={"cognitive_complexity": scenario["complexity"]},
        )

        print("\n   🎯 Recommendation:")
        current = assessment.current_agent.value if assessment.current_agent else "unknown"
        recommended = (
            assessment.recommended_agent.value if assessment.recommended_agent else "unknown"
        )
        print(f"      Current: {current}")
        print(f"      Recommended: {recommended}")
        print(f"      Should handoff: {assessment.should_handoff}")
        print(f"      Can parallelize: {assessment.can_parallelize}")

        if assessment.can_parallelize and assessment.parallel_agents:
            print(f"      Parallel agents available: {len(assessment.parallel_agents)}")

        print("\n   📊 Top 3 Agents:")
        for i, score in enumerate(assessment.agent_scores[:3], 1):
            print(
                f"      {i}. {score.agent_type.value}: "
                f"{score.confidence:.0%} confidence, "
                f"~{score.estimated_time:.0f}s"
            )

        if assessment.suggestion:
            print(f"\n   💡 {assessment.suggestion}")

        print("   " + "-" * 56)


def main():
    """Run all tests"""
    print("=" * 60)
    print("  NuSyQ Multi-Agent System Performance Test")
    print("=" * 60)

    # Test 1: Collaboration Advisor
    test_collaboration_advisor()

    # Test 2: Concurrent Ollama agents
    print("\n" + "=" * 60)
    print("  Concurrent Agent Load Testing")
    print("=" * 60)

    for num_agents in [1, 2, 4]:
        test_concurrent_agents(num_agents)
        time.sleep(2)  # Brief pause between tests

    # Final recommendations
    print("\n" + "=" * 60)
    print("  💡 Recommendations")
    print("=" * 60)
    print("""
Based on your hardware (32 cores, 32GB RAM):

✅ Optimal Setup:
   • Run 2-4 Ollama models concurrently for parallel tasks
   • Use Copilot for investigation/small edits
   • Hand off large refactors to Claude Code
   • Parallelize code generation across Ollama models

⚡ Performance Modes:
   1. Speed Mode: Use smaller models (7B) in parallel
   2. Quality Mode: Use larger models (14B-15B) sequentially
   3. Hybrid Mode: Mix of both based on task complexity

🎯 Agent Roles:
   • Copilot: Investigation, planning, validation
   • Claude Code: Complex refactoring, architecture
   • Ollama Qwen/StarCoder: Code generation
   • Ollama Gemma/Llama: Analysis and reasoning
   • ChatDev: Full project orchestration
    """)


if __name__ == "__main__":
    main()
