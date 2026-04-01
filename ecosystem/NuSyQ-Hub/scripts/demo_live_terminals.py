#!/usr/bin/env python3
"""Live Terminal Demonstration

This script demonstrates the terminal routing system in action by simulating
various agent activities and system events across all terminals.

Run this to see your terminals come ALIVE!
"""

import logging
import sys
import time
from pathlib import Path

# Ensure demo outputs are visible in the TerminalManager when run interactively
try:
    from src.system.init_terminal import init_terminal_logging

    try:
        init_terminal_logging(channel="Demo-Live-Terminals", level=logging.INFO)
    except Exception:
        pass
except Exception:
    pass

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.output.terminal_integration import (
    route_agent_output,
    setup_terminal_logging,
    to_chatdev,
    to_claude,
    to_codex,
    to_copilot,
    to_council,
    to_errors,
    to_metrics,
    to_suggestions,
    to_tasks,
    to_zeta,
)


def animate_output(message: str, delay: float = 0.05):
    """Print message with slight animation effect."""
    for char in message:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def demo_agent_terminals():
    """Demonstrate agent-specific terminal routing."""
    print("\n" + "=" * 70)
    print("🤖 AGENT TERMINALS DEMONSTRATION")
    print("=" * 70)

    # Claude Agent
    print("\n🧠 Claude Agent Activity:")
    to_claude("Initializing Claude Code analysis engine...")
    time.sleep(0.3)
    to_claude("Analyzing repository structure: 487 files, 52,341 lines of code")
    time.sleep(0.3)
    to_claude("Detected 3 potential optimization opportunities")
    time.sleep(0.3)
    to_claude("Generating refactoring suggestions...")
    time.sleep(0.5)

    # Copilot Agent
    print("\n🧩 Copilot Agent Activity:")
    to_copilot("GitHub Copilot activated for session")
    time.sleep(0.3)
    to_copilot("Analyzing context: Python file, function definition")
    time.sleep(0.3)
    to_copilot("Generating completion: async def process_request()")
    time.sleep(0.3)
    to_copilot("Suggestion confidence: 94%")
    time.sleep(0.5)

    # Codex Agent
    print("\n🧠 Codex Agent Activity:")
    to_codex("OpenAI Codex transformation engine started")
    time.sleep(0.3)
    to_codex("Legacy code detected: Python 2.7 syntax")
    time.sleep(0.3)
    to_codex("Migrating to Python 3.11+ syntax...")
    time.sleep(0.3)
    to_codex("Migration complete: 42 transformations applied")
    time.sleep(0.5)

    # ChatDev Multi-Agent
    print("\n🏗️ ChatDev Multi-Agent Team:")
    to_chatdev("[CEO] Reviewing project requirements for new authentication system")
    time.sleep(0.3)
    to_chatdev("[CTO] Recommending OAuth 2.0 with JWT tokens")
    time.sleep(0.3)
    to_chatdev("[Designer] Creating UI mockups for login flow")
    time.sleep(0.3)
    to_chatdev("[Coder] Implementing authentication middleware")
    time.sleep(0.3)
    to_chatdev("[Tester] Writing integration tests for auth flow")
    time.sleep(0.5)

    # AI Council
    print("\n🏛️ AI Council Deliberation:")
    to_council("Council session initiated: Architectural decision required")
    time.sleep(0.3)
    to_council("[Claude] Vote: Microservices architecture (confidence: 0.85)")
    time.sleep(0.3)
    to_council("[GPT-4] Vote: Microservices architecture (confidence: 0.92)")
    time.sleep(0.3)
    to_council("[Gemini] Vote: Modular monolith (confidence: 0.78)")
    time.sleep(0.3)
    to_council("Consensus reached: Microservices architecture (75% agreement)")
    time.sleep(0.5)

    print("\n✅ Agent terminal demonstrations complete!")


def demo_operational_terminals():
    """Demonstrate operational terminal routing."""
    print("\n" + "=" * 70)
    print("⚙️  OPERATIONAL TERMINALS DEMONSTRATION")
    print("=" * 70)

    # Errors
    print("\n🔥 Error Monitoring:")
    to_errors("WARNING: Configuration file not found at expected location")
    time.sleep(0.3)
    to_errors("ERROR: Database connection failed - retrying in 5 seconds")
    time.sleep(0.3)
    to_errors("CRITICAL: Out of memory - terminating non-essential processes")
    time.sleep(0.5)

    # Tasks
    print("\n✅ Task Processing:")
    to_tasks("Task #1042: Analyze codebase - Status: IN_PROGRESS")
    time.sleep(0.3)
    to_tasks("Task #1043: Update dependencies - Status: QUEUED")
    time.sleep(0.3)
    to_tasks("Task #1042: Analyze codebase - Status: COMPLETED (15.3s)")
    time.sleep(0.3)
    to_tasks("Processing unified PU queue: 23 items remaining")
    time.sleep(0.5)

    # Metrics
    print("\n📊 System Metrics:")
    to_metrics("System Health: CPU 45%, Memory 62%, Disk 78%")
    time.sleep(0.3)
    to_metrics("Active Agents: 6 | Completed Tasks: 142 | Queue Depth: 23")
    time.sleep(0.3)
    to_metrics("Average Response Time: 1.2s | Success Rate: 98.3%")
    time.sleep(0.3)
    to_metrics("Database Queries: 1,284 | Cache Hit Rate: 87%")
    time.sleep(0.5)

    # Suggestions
    print("\n💡 AI Suggestions:")
    to_suggestions("💡 Consider caching frequently accessed configuration data")
    time.sleep(0.3)
    to_suggestions("💡 Detected duplicate code in modules A and B - extract to shared utility")
    time.sleep(0.3)
    to_suggestions("💡 Database query can be optimized with index on 'created_at' column")
    time.sleep(0.3)
    to_suggestions("💡 Add retry logic for external API calls")
    time.sleep(0.5)

    # Zeta Autonomous
    print("\n🎯 Zeta Autonomous Control:")
    to_zeta("Autonomous cycle #47 initiated")
    time.sleep(0.3)
    to_zeta("Self-assessment: System health 94% - within normal parameters")
    time.sleep(0.3)
    to_zeta("Auto-healing: Restarted stalled background worker")
    time.sleep(0.3)
    to_zeta("Predictive maintenance: Scheduling log rotation in 2 hours")
    time.sleep(0.3)
    to_zeta("Autonomous cycle #47 completed successfully (duration: 3.2s)")
    time.sleep(0.5)

    print("\n✅ Operational terminal demonstrations complete!")


def demo_context_routing():
    """Demonstrate context-based routing with agent sessions."""
    print("\n" + "=" * 70)
    print("🔄 CONTEXT-BASED ROUTING DEMONSTRATION")
    print("=" * 70)

    # Claude session
    print("\n🧠 Claude Agent Session:")
    with route_agent_output("Claude"):
        print("Starting code analysis...")
        time.sleep(0.2)
        print("Scanning src/ directory...")
        time.sleep(0.2)
        print("Found 15 Python files to analyze")
        time.sleep(0.2)
        print("Analysis complete!")
        time.sleep(0.5)

    # Copilot session
    print("\n🧩 Copilot Agent Session:")
    with route_agent_output("Copilot"):
        print("Generating code suggestions...")
        time.sleep(0.2)
        print("Context: async function definition")
        time.sleep(0.2)
        print("Suggested 3 completions")
        time.sleep(0.5)

    print("\n✅ Context routing demonstrations complete!")


def demo_cross_terminal_scenario():
    """Demonstrate a realistic multi-terminal scenario."""
    print("\n" + "=" * 70)
    print("🎬 REALISTIC MULTI-TERMINAL SCENARIO")
    print("=" * 70)
    print("\nScenario: Processing a new feature request")
    print("-" * 70)

    time.sleep(1)

    # Task received
    to_tasks("NEW TASK: Implement user authentication system")
    time.sleep(0.5)

    # Council deliberates
    to_council("Evaluating authentication approaches...")
    time.sleep(0.5)
    to_council("Consensus: OAuth 2.0 with JWT tokens")
    time.sleep(0.5)

    # ChatDev team starts work
    to_chatdev("[CEO] Assigning authentication implementation to team")
    time.sleep(0.3)
    to_chatdev("[CTO] Creating technical specification")
    time.sleep(0.5)

    # Claude analyzes existing code
    to_claude("Analyzing existing authentication patterns in codebase...")
    time.sleep(0.5)
    to_claude("Found 3 authentication endpoints to modify")
    time.sleep(0.5)

    # Copilot helps with implementation
    to_copilot("Generating OAuth middleware implementation...")
    time.sleep(0.5)

    # Codex modernizes legacy auth code
    to_codex("Refactoring legacy authentication to modern patterns...")
    time.sleep(0.5)

    # Suggestions emerge
    to_suggestions("💡 Add rate limiting to authentication endpoints")
    time.sleep(0.3)
    to_suggestions("💡 Implement refresh token rotation for security")
    time.sleep(0.5)

    # Metrics track progress
    to_metrics("Implementation progress: 35% complete")
    time.sleep(0.3)
    to_metrics("Implementation progress: 70% complete")
    time.sleep(0.3)
    to_metrics("Implementation progress: 100% complete")
    time.sleep(0.5)

    # Task completes
    to_tasks("TASK COMPLETED: User authentication system (duration: 2.5m)")
    time.sleep(0.5)

    # Zeta observes and learns
    to_zeta("Pattern learned: Authentication tasks typically require 2-3 minutes")
    time.sleep(0.5)

    print("\n✅ Multi-terminal scenario complete!")


def main():
    """Run full terminal demonstration."""
    print("\n" + "=" * 70)
    print("🎭 NUSYQ-HUB LIVE TERMINAL ROUTING DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstration shows output routing to themed terminals.")
    print("Watch each terminal to see coordinated multi-agent activity!")
    print("\nStarting in 2 seconds...")
    time.sleep(2)

    # Set up terminal logging
    setup_terminal_logging()

    # Run demonstrations
    demo_agent_terminals()
    time.sleep(1)

    demo_operational_terminals()
    time.sleep(1)

    demo_context_routing()
    time.sleep(1)

    demo_cross_terminal_scenario()

    # Final summary
    print("\n" + "=" * 70)
    print("✨ DEMONSTRATION COMPLETE!")
    print("=" * 70)
    print("\n📁 Check terminal output logs:")
    print(f"   {repo_root / 'data' / 'terminal_logs'}")
    print("\n🔍 To watch terminals in real-time:")
    print("   1. Ctrl+Shift+P → Tasks: Run Task → Watch All Agent Terminals")
    print("   2. Or run: python scripts/launch_all_terminal_watchers.py")
    print("\n💡 To integrate into your scripts:")
    print("   from src.output.terminal_integration import to_claude, to_tasks, ...")
    print("   to_claude('Your message here')")
    print("\n✅ Your terminals are now ALIVE and ready to use!")


if __name__ == "__main__":
    main()
