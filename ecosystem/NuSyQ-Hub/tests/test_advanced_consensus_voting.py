"""
Integration Test: Advanced Consensus Voting

Tests weighted voting, agent profiling, learning mechanism, and consensus integration.

OmniTag: [testing, consensus, integration, validation]
"""

import logging

# Import the consensus modules
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestration"))

from advanced_consensus_voter import AdvancedConsensusVoter, VotingStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import pytest


@pytest.fixture
def voter():
    """Pre-populated AdvancedConsensusVoter for dependent tests."""
    v = AdvancedConsensusVoter(learning_enabled=True)
    for _i in range(5):
        v.record_agent_result("agent-fast", True, 8.0, 200, "code_review")
        v.record_agent_result("agent-fast", True, 9.0, 210, "code_review")
    for _i in range(4):
        v.record_agent_result("agent-balanced", True, 12.0, 300, "code_review")
        v.record_agent_result("agent-balanced", False, 13.0, 310, "code_review")
    for _i in range(3):
        v.record_agent_result("agent-slow", False, 20.0, 400, "code_review")
    return v


def test_agent_profiling():
    """Test agent profiling and metric calculation."""
    print("\n[TEST 1] Agent Profiling & Metrics\n")

    voter = AdvancedConsensusVoter(learning_enabled=True)

    # Build profiles for 3 agents
    print("Building agent profiles...")

    # Agent 1: Strong performer
    for _i in range(5):
        voter.record_agent_result("agent-fast", True, 8.0, 200, "code_review")
        voter.record_agent_result("agent-fast", True, 9.0, 210, "code_review")

    # Agent 2: Medium performer
    for _i in range(4):
        voter.record_agent_result("agent-balanced", True, 12.0, 300, "code_review")
        voter.record_agent_result("agent-balanced", False, 13.0, 310, "code_review")

    # Agent 3: Weak performer
    for _i in range(3):
        voter.record_agent_result("agent-slow", False, 20.0, 400, "code_review")

    # Verify profiles
    print("\n✓ Agent profiles created:")
    for agent_name, profile in voter.agent_profiles.items():
        print(f"  {agent_name}:")
        print(f"    Accuracy: {profile.accuracy:.1%}")
        print(f"    Avg Latency: {profile.avg_latency:.1f}s")
        print(f"    Reliability Score: {profile.reliability_score:.2f}")
        print(f"    Weight: {profile.get_weight():.2f}")

    return voter, True


def test_majority_voting(voter):
    """Test simple majority voting."""
    print("\n[TEST 2] Majority Voting\n")

    responses = {
        "agent-fast": "Response A",
        "agent-balanced": "Response A",
        "agent-slow": "Response B",
    }

    result = voter.vote(responses, strategy=VotingStrategy.MAJORITY)

    print(f"Responses: {list(responses.values())[:2]}")
    print(f"Selected: {result.selected_response}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Reasoning: {result.reasoning}")

    assert result.selected_response == "Response A", "Majority should select A"
    assert result.confidence >= 0.5, "Confidence should be >= 50%"

    print("\n✓ Majority voting works correctly")
    return True


def test_weighted_voting(voter):
    """Test weighted voting based on agent reliability."""
    print("\n[TEST 3] Weighted Voting\n")

    responses = {
        "agent-fast": "Code quality: Excellent",
        "agent-balanced": "Code quality: Good",
        "agent-slow": "Code quality: Excellent",
    }

    result = voter.vote(responses, task_type="code_review", strategy=VotingStrategy.WEIGHTED)

    print(f"Responses: {list(responses.values())}")
    print(f"Agent votes (weights): {result.agent_votes}")
    print(f"Response scores: {result.response_scores}")
    print(f"Selected: {result.selected_response}")
    print(f"Confidence: {result.confidence:.1%}")

    # Fast agent should have highest weight
    assert (
        result.agent_votes["agent-fast"] > result.agent_votes["agent-slow"]
    ), "Fast agent should outweigh slow agent"

    print("\n✓ Weighted voting correctly applies agent reliability scores")
    return True


def test_specialization_boost(voter):
    """Test task-specific specialization scoring."""
    print("\n[TEST 4] Specialization Boosting\n")

    # Give agents different specializations
    voter.agent_profiles["agent-fast"].specializations["code_review"] = 0.8
    voter.agent_profiles["agent-balanced"].specializations["code_generation"] = 0.7
    voter.agent_profiles["agent-slow"].specializations["documentation"] = 0.5

    # Query with different task types
    ranking_review = voter.get_agent_rankings("code_review")
    ranking_gen = voter.get_agent_rankings("code_generation")

    print("Rankings for code_review:")
    for agent, score in ranking_review:
        print(f"  {agent}: {score:.2f}")

    print("\nRankings for code_generation:")
    for agent, score in ranking_gen:
        print(f"  {agent}: {score:.2f}")

    # Fast agent should rank high for code_review
    assert ranking_review[0][0] == "agent-fast", "Fast agent should rank high for code_review"

    print("\n✓ Specialization boosting correctly prioritizes specialized agents")
    return True


def test_learning_mechanism(voter):
    """Test adaptive weight learning."""
    print("\n[TEST 5] Learning Mechanism\n")

    agent = "agent-fast"
    initial_reliability = voter.agent_profiles[agent].reliability_score

    print(f"Initial reliability for {agent}: {initial_reliability:.2f}")

    # Simulate failures (agent makes mistakes)
    print("Simulating 3 failures...")
    for _i in range(3):
        voter.record_agent_result(agent, False, 9.0, 250, "code_review")

    updated_reliability = voter.agent_profiles[agent].reliability_score
    print(f"Updated reliability for {agent}: {updated_reliability:.2f}")

    # Reliability should decrease after failures
    assert updated_reliability < initial_reliability, "Reliability should decrease after failures"

    # Recover with successes
    print("Simulating 5 successes...")
    for _i in range(5):
        voter.record_agent_result(agent, True, 8.0, 200, "code_review")

    recovered_reliability = voter.agent_profiles[agent].reliability_score
    print(f"Recovered reliability for {agent}: {recovered_reliability:.2f}")

    # Should improve but maybe not back to initial (depends on learning rate)
    assert recovered_reliability > updated_reliability, "Reliability should improve after successes"

    print("\n✓ Learning mechanism correctly adapts agent weights")
    return True


def test_consensus_strategies():
    """Compare different voting strategies."""
    print("\n[TEST 6] Consensus Strategy Comparison\n")

    voter = AdvancedConsensusVoter()

    # Setup agents with different profiles
    voter.record_agent_result("high-accuracy", True, 10.0, 200, "task")
    voter.record_agent_result("high-accuracy", True, 11.0, 210, "task")
    voter.record_agent_result("high-accuracy", True, 10.5, 205, "task")

    voter.record_agent_result("low-accuracy", False, 15.0, 300, "task")
    voter.record_agent_result("low-accuracy", False, 16.0, 310, "task")

    # Same responses but with weighted votes
    responses = {"high-accuracy": "Solution A", "low-accuracy": "Solution B"}

    result_majority = voter.vote(responses, strategy=VotingStrategy.MAJORITY)
    result_weighted = voter.vote(responses, strategy=VotingStrategy.WEIGHTED)
    result_confidence = voter.vote(responses, strategy=VotingStrategy.CONFIDENCE)

    print("Different strategies with same responses:")
    print(
        f"  Majority voting: {result_majority.selected_response} "
        f"(confidence={result_majority.confidence:.0%})"
    )
    print(
        f"  Weighted voting: {result_weighted.selected_response} "
        f"(confidence={result_weighted.confidence:.1%})"
    )
    print(f"  Confidence voting: {result_confidence.selected_response}")

    # Weighted/confidence should prefer high-accuracy agent
    assert (
        result_weighted.selected_response == "Solution A"
    ), "Weighted should select from high-accuracy agent"
    assert (
        result_confidence.selected_response == "Solution A"
    ), "Confidence should select from high-accuracy agent"

    print("\n✓ Different strategies correctly handle varying agent quality")
    return True


def run_all_tests():
    """Run complete test suite."""
    print("=" * 60)
    print("ADVANCED CONSENSUS VOTING - INTEGRATION TEST SUITE")
    print("=" * 60)

    try:
        # Test 1: Basic profiling
        voter, result1 = test_agent_profiling()
        assert result1, "Test 1 failed"

        # Test 2: Majority voting
        result2 = test_majority_voting(voter)
        assert result2, "Test 2 failed"

        # Test 3: Weighted voting
        result3 = test_weighted_voting(voter)
        assert result3, "Test 3 failed"

        # Test 4: Specialization
        result4 = test_specialization_boost(voter)
        assert result4, "Test 4 failed"

        # Test 5: Learning
        result5 = test_learning_mechanism(voter)
        assert result5, "Test 5 failed"

        # Test 6: Strategy comparison
        result6 = test_consensus_strategies()
        assert result6, "Test 6 failed"

        # Summary
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n[SUMMARY]")
        print("✓ Agent profiling and metrics calculation")
        print("✓ Majority voting consensus")
        print("✓ Weighted voting with reliability scoring")
        print("✓ Task-specific specialization boosting")
        print("✓ Adaptive learning mechanism")
        print("✓ Multiple voting strategy support")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
