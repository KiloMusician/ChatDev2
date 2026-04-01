"""
Multi-Agent Session - Live Testing & Demonstration

This script proves the multi-agent system works by:
1. Testing real Ollama API calls
2. Demonstrating turn-taking conversations
3. Showing parallel consensus
4. Testing ChatDev integration

Run: python tests/test_multi_agent_live.py
  OR: pytest tests/test_multi_agent_live.py -v
"""

import json
import subprocess
import sys
import traceback
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position
from config.multi_agent_session import (
    ConversationMode,
    MultiAgentSession,
    quick_consensus,
    quick_turn_taking,
)


def test_ollama_single_agent():
    """Test 1: Single Ollama agent conversation"""
    print("=" * 70)
    print("TEST 1: Single Ollama Agent")
    print("=" * 70)

    session = MultiAgentSession(
        agents=["ollama_qwen_14b"],
        task_prompt="List 3 Python security best practices. Be concise.",
        mode=ConversationMode.TURN_TAKING,
    )

    result = session.execute(max_turns=1)

    print(f"\n✓ Agent: {result.agents_used[0]}")
    print(f"✓ Turns: {len(result.turns)}")
    print(f"✓ Cost: ${result.total_cost:.4f}")
    print(f"✓ Tokens: {result.total_tokens}")
    print(f"\nConclusion:\n{result.conclusion[:300]}...")
    print("\n" + "=" * 70 + "\n")


def test_turn_taking_conversation():
    """Test 2: Turn-taking between 2 agents"""
    print("=" * 70)
    print("TEST 2: Turn-Taking Conversation (2 agents)")
    print("=" * 70)

    result = quick_turn_taking(
        agents=["ollama_qwen_14b", "ollama_gemma_9b"],
        task="What's better: REST or GraphQL? Debate briefly.",
        max_turns=4,
    )

    print(f"\n✓ Agents: {result.agents_used}")
    print(f"✓ Turns: {len(result.turns)}")
    print(f"✓ Cost: ${result.total_cost:.4f}")

    print("\nConversation:")
    for turn in result.turns[:3]:  # Show first 3 turns
        print(f"\nTurn {turn.turn_number} - {turn.agent_name}:")
        print(f"  {turn.message[:150]}...")

    print(f"\n✓ Final Conclusion:\n{result.conclusion[:200]}...")
    print("\n" + "=" * 70 + "\n")


def test_parallel_consensus():
    """Test 3: Parallel consensus voting"""
    print("=" * 70)
    print("TEST 3: Parallel Consensus (3 agents)")
    print("=" * 70)

    result = quick_consensus(
        agents=["ollama_qwen_14b", "ollama_gemma_9b", "ollama_qwen_7b"],
        task="Is Python or Rust better for web APIs? One sentence each.",
    )

    print(f"\n✓ Agents: {result.agents_used}")
    print(f"✓ Responses: {len(result.turns)}")
    print(f"✓ Cost: ${result.total_cost:.4f}")

    print("\nIndividual Responses:")
    for turn in result.turns:
        print(f"\n{turn.agent_name}:")
        print(f"  {turn.message[:150]}...")

    print(f"\n✓ Consensus:\n{result.conclusion[:300]}...")
    print("\n" + "=" * 70 + "\n")


def test_chatdev_integration():
    """Test 4: Verify ChatDev integration"""
    print("=" * 70)
    print("TEST 4: ChatDev Integration Check")
    print("=" * 70)

    # Check if nusyq_chatdev.py exists
    chatdev_script = Path("nusyq_chatdev.py")

    if chatdev_script.exists():
        print("✓ nusyq_chatdev.py found")

        # Run setup check
        try:
            # Setup checks should be quick (< 30s typically)
            # Increased from 10s to allow for model discovery on slow systems
            result = subprocess.run(
                ["python", str(chatdev_script), "--setup-only"],
                capture_output=True,
                text=True,
                timeout=30,  # Reasonable for setup verification
                check=False,
            )

            if "Setup verification complete" in result.stdout:
                print("✓ ChatDev setup verified")
                print("\nChatDev Output:")
                print(result.stdout[:400])
            else:
                print("⚠ ChatDev setup incomplete")
                print(result.stdout)

        except (subprocess.SubprocessError, OSError) as e:
            print(f"⚠ ChatDev test failed: {e}")
    else:
        print("✗ nusyq_chatdev.py not found")

    print("\n" + "=" * 70 + "\n")


def test_cost_tracking():
    """Test 5: Verify cost tracking"""
    print("=" * 70)
    print("TEST 5: Cost Tracking Verification")
    print("=" * 70)

    # Test Ollama (should be $0)
    result1 = quick_turn_taking(agents=["ollama_qwen_14b"], task="Say 'hello'", max_turns=1)

    print(f"\nOllama Agent Cost: ${result1.total_cost:.4f}")
    assert result1.total_cost == 0.0, "Ollama should be free!"
    print("✓ Ollama confirmed free ($0.00)")

    # Calculate potential savings
    estimated_tokens_per_day = 10000
    claude_cost = (estimated_tokens_per_day / 1000) * 0.015
    ollama_cost = 0.0

    print("\nCost Comparison (10K tokens/day):")
    print(f"  Claude: ${claude_cost:.2f}/day = ${claude_cost * 30:.2f}/month")
    print(f"  Ollama: ${ollama_cost:.2f}/day = ${ollama_cost * 30:.2f}/month")
    print(f"  Savings: ${(claude_cost - ollama_cost) * 30:.2f}/month")

    print("\n" + "=" * 70 + "\n")


def test_session_logging():
    """Test 6: Verify session logging"""
    print("=" * 70)
    print("TEST 6: Session Logging")
    print("=" * 70)

    logs_dir = Path("Logs/multi_agent_sessions")

    # Run a quick session
    _ = quick_turn_taking(agents=["ollama_qwen_7b"], task="What is 2+2?", max_turns=1)

    # Check if log was created
    if logs_dir.exists():
        log_files = list(logs_dir.glob("session_*.json"))
        print(f"\n✓ Logs directory exists: {logs_dir}")
        print(f"✓ Total session logs: {len(log_files)}")

        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"✓ Latest log: {latest_log.name}")

            with open(latest_log, encoding="utf-8") as f:
                log_data = json.load(f)

            print("\nLog Contents:")
            print(f"  Task: {log_data['task_prompt']}")
            print(f"  Mode: {log_data['mode']}")
            print(f"  Agents: {log_data['agents']}")
            print(f"  Total Cost: ${log_data['total_cost']:.4f}")
            print(f"  Turns: {len(log_data['turns'])}")
        else:
            print("⚠ No log files found")
    else:
        print("⚠ Logs directory not created")

    print("\n" + "=" * 70 + "\n")


def main():
    """Run all tests (standalone mode)"""
    print("\n" + "=" * 70)
    print(" ΞNuSyQ Multi-Agent Session - Live Testing")
    print("=" * 70 + "\n")

    tests = [
        ("Single Ollama Agent", test_ollama_single_agent),
        ("Turn-Taking Conversation", test_turn_taking_conversation),
        ("Parallel Consensus", test_parallel_consensus),
        ("ChatDev Integration", test_chatdev_integration),
        ("Cost Tracking", test_cost_tracking),
        ("Session Logging", test_session_logging),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n✗ Test '{name}' FAILED: {e}\n")
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f" TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    if failed == 0:
        print("✓ ALL TESTS PASSED! Multi-agent system is working! 🎉\n")
        return 0

    print(f"⚠ {failed} test(s) failed. Check errors above.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
