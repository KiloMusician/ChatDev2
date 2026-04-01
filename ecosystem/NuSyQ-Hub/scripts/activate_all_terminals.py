#!/usr/bin/env python3
"""Activate All Terminals - One-Click Terminal Ecosystem Startup

Activates all 23 specialized terminals and establishes intelligent routing.

Usage:
    python scripts/activate_all_terminals.py
    python scripts/activate_all_terminals.py --dashboard  # Show live dashboard
    python scripts/activate_all_terminals.py --test        # Test routing
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.system.terminal_intelligence_orchestrator import get_orchestrator


async def activate_terminals(show_dashboard: bool = True, run_tests: bool = False):
    """Activate all terminals and optionally show dashboard/tests."""
    print("🎯 Terminal Intelligence Orchestrator")
    print("=" * 80)
    print("Activating 23 specialized AI development terminals...")
    print()

    orchestrator = get_orchestrator()

    # Activate all terminals
    results = orchestrator.activate_all_terminals()

    # Show results
    activated = sum(results.values())
    total = len(results)

    print(f"\n✅ Successfully activated {activated}/{total} terminals")

    # Show failures
    failures = [name for name, success in results.items() if not success]
    if failures:
        print(f"\n⚠️  Failed to activate: {', '.join(failures)}")

    # Show dashboard
    if show_dashboard:
        print("\n" + await orchestrator.generate_terminal_dashboard())

    # Run routing tests
    if run_tests:
        await run_routing_tests(orchestrator)

    # Show command suggestions
    print("\n📋 Quick Command Reference:")
    print("-" * 80)

    sample_terminals = ["Claude", "ChatDev", "Errors", "Tasks", "Tests", "Ollama"]
    for term_name in sample_terminals:
        suggestions = orchestrator.get_command_suggestions(term_name)
        if suggestions:
            state = orchestrator.terminals[term_name]
            print(f"\n{state.config.emoji} {term_name}:")
            for suggestion in suggestions[:2]:  # Show first 2 suggestions
                print(f"  • {suggestion}")

    print("\n" + "=" * 80)
    print("🎉 Terminal ecosystem ready!")
    print("\nNext steps:")
    print("  • Messages will be intelligently routed to appropriate terminals")
    print("  • Check data/terminal_logs/ for terminal output")
    print("  • Use VS Code tasks to watch terminal activity")
    print()


async def run_routing_tests(orchestrator):
    """Test intelligent routing with sample messages."""
    print("\n🧪 Testing Intelligent Routing")
    print("-" * 80)

    test_messages = [
        ("Error in module X: FileNotFoundException", "ERROR"),
        ("Suggestion: Improve caching strategy for 25% performance gain", "INFO"),
        ("Task completed: Fix bare except clauses", "INFO"),
        ("pytest passed 42 tests with 90% coverage", "INFO"),
        ("Performance metric: 250ms average response time", "INFO"),
        ("Ollama model qwen2.5-coder:7b loaded successfully", "INFO"),
        ("ChatDev team consensus reached: Implement feature X", "INFO"),
        ("Anomaly detected: Unusual spike in error rate", "WARNING"),
        ("Future prediction: System will need scaling in 3 months", "INFO"),
        ("Culture Ship: Ethics review required for new AI feature", "WARNING"),
    ]

    for message, level in test_messages:
        routed = await orchestrator.route_message(message, level=level)
        print(f"  [{level:7}] '{message[:50]}...' → {', '.join(routed)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Activate all 23 specialized AI development terminals")
    parser.add_argument("--dashboard", action="store_true", help="Show live terminal dashboard")
    parser.add_argument("--test", action="store_true", help="Run intelligent routing tests")
    parser.add_argument("--no-dashboard", action="store_true", help="Skip dashboard display")

    args = parser.parse_args()

    show_dashboard = not args.no_dashboard or args.dashboard

    asyncio.run(activate_terminals(show_dashboard=show_dashboard, run_tests=args.test))


if __name__ == "__main__":
    main()
