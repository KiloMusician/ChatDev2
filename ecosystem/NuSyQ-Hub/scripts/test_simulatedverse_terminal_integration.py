#!/usr/bin/env python3
"""SimulatedVerse Terminal Integration Test

Demonstrates how SimulatedVerse output routes through NuSyQ-Hub's 23-terminal system.

Usage:
    python scripts/test_simulatedverse_terminal_integration.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.system.output_source_intelligence import get_output_intelligence
from src.system.terminal_intelligence_orchestrator import get_orchestrator

logging.basicConfig(level=logging.WARNING)


async def test_simulatedverse_integration():
    """Test SimulatedVerse messages routing to dedicated terminals."""

    intelligence = await get_output_intelligence()
    orchestrator = get_orchestrator()

    print("=" * 100)
    print("🎮  SIMULATEDVERSE TERMINAL INTEGRATION TEST")
    print("=" * 100)
    print()
    print("Testing how SimulatedVerse ecosystem outputs route through NuSyQ-Hub's 23 terminals.")
    print("This demonstrates the tripartite integration: SimulatedVerse → NuSyQ-Hub → Terminal System")
    print()

    # Simulate realistic SimulatedVerse output
    test_scenarios = [
        {
            "category": "🛡️  CULTURE SHIP (Strategic Advisor & Guardian Ethics)",
            "messages": [
                ("Culture Ship", "[Strategic Advisor] Analyzing codebase architecture", "INFO"),
                (
                    "Culture Ship",
                    "[Strategic Decision] Implementing auto-healing for import errors",
                    "INFO",
                ),
                (
                    "Culture Ship",
                    "[Guardian Ethics] Containment protocol activated for unsafe operation",
                    "WARNING",
                ),
                ("Culture Ship", "[Real Action] Applied 12 fixes across 5 systems", "INFO"),
            ],
        },
        {
            "category": "🎮  SIMULATEDVERSE (Consciousness Engine)",
            "messages": [
                (
                    "SimulatedVerse",
                    "[Temple] Knowledge progression: Floor 3 (Testing) → Floor 4 (Integration)",
                    "INFO",
                ),
                (
                    "SimulatedVerse",
                    "[Consciousness] Transition: Proto-conscious → Self-aware",
                    "INFO",
                ),
                ("SimulatedVerse", "[PU Queue] Processing 47 autonomous Programming Units", "INFO"),
                (
                    "SimulatedVerse",
                    "[Agent Synth] 9 modular agents coordinating via patch-bay",
                    "INFO",
                ),
                ("SimulatedVerse", "[House of Leaves] Recursive debugging session active", "INFO"),
            ],
        },
        {
            "category": "🏗️  CHATDEV (Multi-Agent Software Company)",
            "messages": [
                (
                    "ChatDev",
                    "[CEO] Project: 'REST API JWT Auth' - Kickoff meeting complete",
                    "INFO",
                ),
                ("ChatDev", "[CTO] Technical specification approved, passing to design", "INFO"),
                ("ChatDev", "[Designer] UI mockups generated: login, dashboard, admin", "INFO"),
                ("ChatDev", "[Programmer] Implementing JWT middleware and auth routes", "INFO"),
                ("ChatDev", "[Tester] Running pytest suite: 42/42 tests passing", "INFO"),
                ("ChatDev", "[Reviewer] Code review complete - ready for deployment", "INFO"),
            ],
        },
        {
            "category": "🖥️  RUNTIME (Node.js & Express)",
            "messages": [
                ("Node.js", "Server initializing on port 5000", "INFO"),
                ("Express", "Middleware registered: compression, cors, helmet", "INFO"),
                ("Node.js", "WebSocket server started on port 5001", "INFO"),
                ("Express", "GET /api/consciousness/status 200 87ms", "INFO"),
                ("Express", "POST /api/temple/advance 201 142ms", "INFO"),
                ("Express", "GET /api/agents/synth/status 200 23ms", "INFO"),
            ],
        },
    ]

    total_routed = 0
    total_filtered = 0
    terminal_stats = {}

    for scenario in test_scenarios:
        print(f"\n{scenario['category']}")
        print("-" * 100)

        for source, message, level in scenario["messages"]:
            terminal = await intelligence.route_output(source, message, level)

            if terminal:
                emoji = "✅"
                total_routed += 1
                terminal_stats[terminal] = terminal_stats.get(terminal, 0) + 1
            else:
                emoji = "⚠️ "
                terminal = "FILTERED"
                total_filtered += 1

            # Truncate message for display
            display_msg = message if len(message) <= 70 else message[:67] + "..."
            print(f"  {emoji} [{source:20}] {display_msg:73} → {terminal}")

    # Summary statistics
    print()
    print("=" * 100)
    print("📊  ROUTING SUMMARY")
    print("=" * 100)
    print()
    print(f"Total messages tested: {total_routed + total_filtered}")
    print(f"Successfully routed:   {total_routed} ({total_routed / (total_routed + total_filtered) * 100:.1f}%)")
    print(f"Filtered:              {total_filtered} ({total_filtered / (total_routed + total_filtered) * 100:.1f}%)")
    print()

    # Terminal distribution
    print("📡  TERMINAL DISTRIBUTION:")
    print()
    for terminal, count in sorted(terminal_stats.items(), key=lambda x: -x[1]):
        # Get terminal emoji
        if terminal in orchestrator.terminals:
            state = orchestrator.terminals[terminal]
            emoji = state.config.emoji  # Fixed: icon → emoji
            print(f"  {emoji} {terminal:20} ← {count:2} messages")
        else:
            print(f"  📍 {terminal:20} ← {count:2} messages")

    # Terminal activation status
    print()
    print("🎯  ACTIVE TERMINALS:")
    print()
    active_count = sum(1 for state in orchestrator.terminals.values() if state.active)
    print(f"  {active_count}/23 terminals activated during test")
    print()
    for name, state in sorted(orchestrator.terminals.items()):
        if state.active:
            status = "🟢 ACTIVE" if state.active else "⚫ INACTIVE"
            print(
                f"  {state.config.emoji} {name:20} | {status:12} | Msgs: {state.message_count:3}"
            )  # Fixed: icon → emoji

    print()
    print("=" * 100)
    print("✅  INTEGRATION TEST COMPLETE")
    print("=" * 100)
    print()
    print("Next steps:")
    print("  1. Start SimulatedVerse: cd ../SimulatedVerse/SimulatedVerse && npm run dev")
    print("  2. Watch live routing: python scripts/start_nusyq.py terminals test")
    print("  3. Monitor terminals in VS Code sidebar")
    print()


if __name__ == "__main__":
    asyncio.run(test_simulatedverse_integration())
