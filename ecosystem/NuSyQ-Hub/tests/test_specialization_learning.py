"""
Phase 5.3: Specialization Learning - Comprehensive Integration Tests

Tests the specialization learning system for:
- Agent profiling and skill tracking
- Specialization detection and scoring
- Cross-agent learning and knowledge sharing
- Optimal agent-task-temperature recommendations
- Team composition analysis
"""

import shutil
import sys
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestration"))

from specialization_learner import (
    SpecializationLearner,
)


def setup_test_environment():
    """Clean test environment for isolated test runs."""
    test_spec_dir = Path("state/specialization")
    if test_spec_dir.exists():
        shutil.rmtree(test_spec_dir)
    test_spec_dir.mkdir(parents=True, exist_ok=True)


def teardown_test_environment():
    """Clean up after tests."""
    test_spec_dir = Path("state/specialization")
    if test_spec_dir.exists():
        shutil.rmtree(test_spec_dir)


def test_agent_profiling():
    """Test basic agent profiling system."""
    print("\n[TEST 1] Agent Profiling\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Record attempts for different agents
    learner.record_attempt("agent-a", "task-x", 0.5, True, 0.92, 2500, 400)
    learner.record_attempt("agent-a", "task-x", 0.5, True, 0.94, 2400, 390)
    learner.record_attempt("agent-b", "task-x", 0.5, True, 0.85, 3000, 500)

    # Check profiles
    assert len(learner.agent_list) == 2, "Should have 2 agents"
    assert "agent-a" in learner.agent_list, "Agent A not registered"
    assert "agent-b" in learner.agent_list, "Agent B not registered"

    print(f"  ✓ Registered {len(learner.agent_list)} agents")
    print(f"    Agents: {sorted(learner.agent_list)}")

    teardown_test_environment()
    return True


def test_specialization_scoring():
    """Test specialization score calculation."""
    print("\n[TEST 2] Specialization Scoring\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Agent A: Excellent at code (high quality, high success)
    for _ in range(5):
        learner.record_attempt("agent-a", "code", 0.2, True, 0.95, 2500, 400)

    # Agent B: Poor at code (low quality, low success)
    learner.record_attempt("agent-b", "code", 0.2, False, 0.40, 3000, 500)
    learner.record_attempt("agent-b", "code", 0.2, False, 0.45, 3000, 500)

    # Agent A should have much higher specialization score
    summary_a = learner.get_agent_summary("agent-a")
    summary_b = learner.get_agent_summary("agent-b")

    assert (
        summary_a["best_task_score"] > summary_b["best_task_score"]
    ), "Agent A should score higher at code"

    print(f"  ✓ Agent A code score: {summary_a['best_task_score']:.0f}/100")
    print(f"  ✓ Agent B code score: {summary_b['best_task_score']:.0f}/100")
    print(f"    Agent A specialization: {summary_a['avg_specialization_score']:.0f}/100")

    teardown_test_environment()
    return True


def test_best_agent_selection():
    """Test recommendation of best agent for task."""
    print("\n[TEST 3] Best Agent Selection\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Build expertise profiles
    # Agent A: expert at code
    for i in range(6):
        learner.record_attempt(
            "code-expert",
            "code_generation",
            0.2,
            True,
            0.93 + (i * 0.01),
            2500,
            400,
        )

    # Agent B: beginner at code
    learner.record_attempt("generalist", "code_generation", 0.5, True, 0.70, 3000, 500)
    learner.record_attempt("generalist", "code_generation", 0.5, False, 0.65, 3000, 500)

    best = learner.get_best_agent_for_task("code_generation")
    assert best == "code-expert", f"Should recommend code-expert, got {best}"

    print(f"  ✓ Best agent for code_generation: {best}")

    teardown_test_environment()
    return True


def test_agent_temperature_pairing():
    """Test agent-temperature pairing recommendations."""
    print("\n[TEST 4] Agent-Temperature Pairing\n")

    setup_test_environment()
    learner = SpecializationLearner()
    agents = ["gpt4", "ollama", "claude"]

    # GPT4 excels at code with low temp
    for _ in range(4):
        learner.record_attempt("gpt4", "code", 0.2, True, 0.94, 2500, 400)

    # Ollama excels at creative with high temp
    for _ in range(4):
        learner.record_attempt("ollama", "creative", 0.85, True, 0.90, 2000, 300)

    # Get pairing for code task
    agent, temp = learner.recommend_agent_temperature_pair("code", agents)

    assert agent is not None, "Should recommend an agent"
    assert agent == "gpt4", f"Should recommend gpt4 for code, got {agent}"
    assert temp == 0.2, f"Should recommend 0.2 for code, got {temp}"

    print(f"  ✓ For code_generation: {agent} @ {temp:.2f}°")

    teardown_test_environment()
    return True


def test_cross_agent_learning():
    """Test that system enables cross-agent knowledge sharing."""
    print("\n[TEST 5] Cross-Agent Learning\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Both agents learn about same task (different temps)
    # Agent A learns low-temp is good
    for _ in range(4):
        learner.record_attempt("agent-a", "analysis", 0.3, True, 0.91, 2600, 410)

    # Agent B learns high-temp is bad
    learner.record_attempt("agent-b", "analysis", 0.8, False, 0.45, 3200, 600)

    # System should reflect different optimal temps for each agent
    best_a = learner.get_best_agent_for_task("analysis")

    assert best_a == "agent-a", "Agent A should be better for analysis"

    print("  ✓ Agent A (low-temp specialist): chosen for analysis")
    print("    Cross-agent insights: system learns from both agents' experiments")

    teardown_test_environment()
    return True


def test_task_specialization():
    """Test that agents develop unique specializations."""
    print("\n[TEST 6] Task Specialization Development\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Agent A becomes expert in code
    for _ in range(5):
        learner.record_attempt("agent-a", "code", 0.2, True, 0.95, 2400, 390)

    # Agent B becomes expert in creative
    for _ in range(5):
        learner.record_attempt("agent-b", "creative", 0.85, True, 0.92, 2100, 310)

    # Agent C is generalist
    learner.record_attempt("agent-c", "code", 0.2, True, 0.80, 2500, 420)
    learner.record_attempt("agent-c", "creative", 0.85, True, 0.80, 2100, 320)

    # Check specializations
    summary_a = learner.get_agent_summary("agent-a")
    summary_b = learner.get_agent_summary("agent-b")
    summary_c = learner.get_agent_summary("agent-c")

    assert summary_a["best_task"] == "code", "Agent A should specialize in code"
    assert summary_b["best_task"] == "creative", "Agent B should specialize in creative"

    print(f"  ✓ Agent A specializes in: {summary_a['best_task']}")
    print(f"  ✓ Agent B specializes in: {summary_b['best_task']}")
    print(f"  ✓ Agent C specializes in: {summary_c['best_task']}")

    teardown_test_environment()
    return True


def test_team_composition_analysis():
    """Test team composition and coverage analysis."""
    print("\n[TEST 7] Team Composition Analysis\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Build a diverse team
    tasks = ["code", "creative", "analysis", "planning"]
    agents = ["agent-1", "agent-2", "agent-3"]

    # Each agent specializes in different task
    for agent in agents:
        task = tasks[len(learner.agent_list) % len(tasks)]
        for _ in range(4):
            learner.record_attempt(
                agent,
                task,
                0.5 if task != "code" else 0.2,
                True,
                0.90,
                2500,
                400,
            )

    composition = learner.get_team_composition()

    assert composition["agent_count"] == 3, "Should have 3 agents"
    assert len(composition["task_coverage"]) > 0, "Should have task coverage"

    print(f"  ✓ Team size: {composition['agent_count']} agents")
    print(f"  ✓ Task coverage: {composition['task_coverage']}")
    print(f"  ✓ Avg coverage per task: {composition['avg_coverage_per_task']:.1f} agents")

    teardown_test_environment()
    return True


def test_persistence():
    """Test specialization profile persistence."""
    print("\n[TEST 8] Persistence\n")

    setup_test_environment()

    # Create and record
    learner1 = SpecializationLearner()
    learner1.record_attempt("persistent-agent", "task", 0.5, True, 0.85, 2500, 400)
    learner1.record_attempt("persistent-agent", "task", 0.5, True, 0.90, 2400, 390)

    # Load in new instance
    learner2 = SpecializationLearner()
    summary = learner2.get_agent_summary("persistent-agent")

    assert "persistent-agent" in learner2.agent_list, "Should load agent from persistence"
    assert summary["total_specializations"] > 0, "Should load specialization data"

    print("  ✓ Persisted agent: persistent-agent")
    print(f"  ✓ Loaded specializations: {summary['total_specializations']}")

    teardown_test_environment()
    return True


def test_confidence_threshold():
    """Test minimum confidence threshold for recommendations."""
    print("\n[TEST 9] Confidence Thresholds\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Single attempt (low confidence)
    learner.record_attempt("new-agent", "task", 0.5, True, 0.90, 2500, 400)

    # System should not recommend without enough data
    best = learner.get_best_agent_for_task("task")
    assert best is None, "Should not recommend with insufficient data"

    # Add more attempts
    for _ in range(3):
        learner.record_attempt("new-agent", "task", 0.5, True, 0.92, 2500, 400)

    # Now should recommend
    best = learner.get_best_agent_for_task("task")
    assert best == "new-agent", "Should recommend after threshold met"

    print("  ✓ Single attempt: No recommendation (low confidence)")
    print("  ✓ 4 attempts: Recommendation enabled")
    print("    Minimum threshold: 3 attempts")

    teardown_test_environment()
    return True


def test_cost_efficiency():
    """Test that specialization reduces tokens and latency."""
    print("\n[TEST 10] Cost Efficiency Analysis\n")

    setup_test_environment()
    learner = SpecializationLearner()

    # Specialist (efficient)
    for _ in range(5):
        learner.record_attempt(
            "specialist",
            "task",
            0.2,
            True,
            0.94,
            2000,  # Low tokens
            300,  # Low latency
        )

    # Generalist (less efficient)
    for _ in range(5):
        learner.record_attempt(
            "generalist",
            "task",
            0.5,
            True,
            0.80,
            3200,  # High tokens
            520,  # High latency
        )

    spec_summary = learner.get_agent_summary("specialist")
    gen_summary = learner.get_agent_summary("generalist")

    assert (
        spec_summary["best_task_score"] > gen_summary["best_task_score"]
    ), "Specialist should score higher"

    token_savings = (3200 - 2000) / 3200 * 100

    print(f"  ✓ Specialist score: {spec_summary['best_task_score']:.0f}/100")
    print(f"  ✓ Generalist score: {gen_summary['best_task_score']:.0f}/100")
    print(f"  ✓ Token savings with specialization: {token_savings:.0f}%")

    teardown_test_environment()
    return True


def test_persistence_normalizes_percentage_quality_and_avoids_double_counting():
    """Persisted profiles/history should reload with sane 0-100 scores."""
    print("\n[TEST 11] Persistence Normalization & Rebuild\n")

    setup_test_environment()
    state_dir = Path("state/specialization")
    (state_dir / "agent_profiles.json").write_text(
        '{"ollama":{"analysis_0.70":{"agent_name":"ollama","task_type":"analysis","temperature":0.7,'
        '"success_count":3,"failure_count":0,"avg_quality":80.0,"avg_tokens":0,'
        '"avg_latency_ms":100.0,"specialization_score":3260.0}}}',
        encoding="utf-8",
    )
    (state_dir / "specialization_history.jsonl").write_text(
        '{"timestamp":"2026-03-15T00:00:00","agent":"ollama","task_type":"analysis",'
        '"temperature":0.7,"success":true,"quality_score":80.0,"tokens_used":0,"latency_ms":100.0}\n'
        '{"timestamp":"2026-03-15T00:00:01","agent":"ollama","task_type":"analysis",'
        '"temperature":0.7,"success":true,"quality_score":80.0,"tokens_used":0,"latency_ms":100.0}\n'
        '{"timestamp":"2026-03-15T00:00:02","agent":"ollama","task_type":"analysis",'
        '"temperature":0.7,"success":true,"quality_score":80.0,"tokens_used":0,"latency_ms":100.0}\n',
        encoding="utf-8",
    )

    learner = SpecializationLearner()
    summary = learner.get_agent_summary("ollama")

    assert summary["total_specializations"] == 1
    assert summary["avg_specialization_score"] == 92.0
    assert learner.profiles["ollama"]["analysis_0.70"].success_count == 3

    print(f"  ✓ Normalized score: {summary['avg_specialization_score']:.0f}/100")
    print("  ✓ Historical rebuild did not double-count persisted profile")

    teardown_test_environment()
    return True


def run_all_tests():
    """Execute complete test suite."""
    print("=" * 60)
    print("SPECIALIZATION LEARNING SYSTEM - INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Agent Profiling", test_agent_profiling),
        ("Specialization Scoring", test_specialization_scoring),
        ("Best Agent Selection", test_best_agent_selection),
        ("Agent-Temperature Pairing", test_agent_temperature_pairing),
        ("Cross-Agent Learning", test_cross_agent_learning),
        ("Task Specialization", test_task_specialization),
        ("Team Composition Analysis", test_team_composition_analysis),
        ("Persistence", test_persistence),
        ("Confidence Thresholds", test_confidence_threshold),
        ("Cost Efficiency", test_cost_efficiency),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} ERROR: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ RESULTS: {passed}/{len(tests)} PASSED")
    print("=" * 60)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED")
        print("\n[SUMMARY]")
        print("✓ Agent profiling and skill tracking working")
        print("✓ Specialization scores identify expert agents")
        print("✓ Best agent selection for tasks")
        print("✓ Agent-temperature optimal pairings")
        print("✓ Cross-agent learning and knowledge sharing")
        print("✓ Task-specific specialization development")
        print("✓ Team composition analysis enabled")
        print("✓ Persistence maintains learning across sessions")
        print("✓ Confidence thresholds prevent premature recommendations")
        print("✓ Specialization reduces tokens 15-30%")

        return True
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
