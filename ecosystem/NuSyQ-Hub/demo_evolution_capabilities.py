#!/usr/bin/env python3
"""Interactive Suggestion & Emergence Demo.

This demonstrates the conversational interface to NuSyQ's new capabilities:
- Suggestion Engine (productive instincts)
- Emergence Protocol (metabolizing phase jumps)

Run with: python demo_evolution_capabilities.py
"""

import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.emergence_protocol import get_protocol
from src.orchestration.suggestion_engine import get_engine


def demo_suggestions():
    """Demonstrate suggestion engine."""
    print("\n" + "=" * 60)
    print("💡 SUGGESTION ENGINE DEMONSTRATION")
    print("=" * 60)

    engine = get_engine()

    # Show various contextual suggestions
    contexts = [
        ("proceed", "General forward motion"),
        ("what's useful right now?", "Request for actionable items"),
        ("optimize agents", "Agent-focused work"),
        ("check models", "Model health inquiry"),
        ("what did we try before?", "Knowledge/memory query"),
    ]

    for context, description in contexts:
        print(f'\n📝 Context: "{context}" ({description})')
        print("-" * 60)

        suggestions = engine.suggest(context, max_suggestions=2)

        if not suggestions:
            print("No specific suggestions - system is healthy")
            continue

        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion.title}")
            print(f"   {suggestion.description}")
            print(f"   💡 Payoff: {suggestion.payoff}")
            print(f"   ⏱️ Effort: {suggestion.effort.value} | 🛡️ Risk: {suggestion.risk.value}")

    # Show safe overnight suggestions
    print("\n" + "=" * 60)
    print("🌙 SAFE OVERNIGHT SUGGESTIONS")
    print("=" * 60)

    safe_suggestions = engine.get_safe_suggestions(max_count=3)
    for suggestion in safe_suggestions:
        print(f"\n✅ {suggestion.title}")
        print(f"   {suggestion.description}")
        print(f"   How: {suggestion.implementation_hint}")


def demo_emergence():
    """Demonstrate emergence protocol."""
    print("\n" + "=" * 60)
    print("🌟 EMERGENCE PROTOCOL DEMONSTRATION")
    print("=" * 60)

    protocol = get_protocol()

    # Show recent emergences
    recent = protocol.get_recent_emergences(limit=5)

    if not recent:
        print("\nNo emergence events recorded yet.")
        print("\n💡 When the system does something ahead-of-phase:")
        print("   1. It acknowledges the emergence")
        print("   2. Lists what was done and why")
        print("   3. Provides rollback instructions")
        print("   4. Suggests integration path")
        return

    print(f"\n📊 Found {len(recent)} emergence event(s)")

    for event_dict in recent:
        print("\n" + "-" * 60)
        print(f"🧬 {event_dict['title']}")
        print(f"   Type: {event_dict['type']}")
        print(f"   Status: {event_dict['integration_status']}")
        print(
            f"   Phase: {event_dict['phase_executed']} (intended: {event_dict['phase_intended']})"
        )
        print(f"   Files: {len(event_dict['files_changed'])} changed")
        print(f"   Dependencies: {len(event_dict['dependencies_added'])} added")


def demo_conversational_flow():
    """Demonstrate full conversational flow."""
    print("\n" + "=" * 60)
    print("💬 CONVERSATIONAL FLOW EXAMPLE")
    print("=" * 60)

    print(
        """
This shows how the system responds to conversational prompts:

User: "proceed"
System:
  1. Checks suggestion engine for context
  2. Surfaces 2-3 high-leverage actions
  3. Executes or proposes based on risk level
  4. Logs if emergence occurs

User: "check agent health"
System:
  1. Recognizes "agent" context
  2. Suggests: "Review Agent Utilization"
  3. Runs analysis pass
  4. Reports findings

User: "what's useful right now?"
System:
  1. Analyzes recent activity
  2. Suggests 1 high-impact action
  3. Explains why it matters
  4. Waits for consent

User: "optimize for sanity"
System:
  1. Filters for human-factors suggestions
  2. Identifies noise sources
  3. Proposes single focused action
  4. Reduces cognitive load

The key shift:
  NOT: "Do this specific task"
  BUT: "Here are productive instincts when idle"
"""
    )


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("🚀 NUSYQ EVOLUTION CAPABILITIES")
    print("=" * 60)
    print(
        """
This demonstrates two new meta-capabilities:

1. **Suggestion Engine** - Productive instincts for autonomous action
2. **Emergence Protocol** - Metabolizing phase jumps into memory

Both enable the system to be self-directing, context-aware, and genuinely
helpful rather than purely reactive.
"""
    )

    demo_suggestions()
    demo_emergence()
    demo_conversational_flow()

    print("\n" + "=" * 60)
    print("📚 NEXT STEPS")
    print("=" * 60)
    print(
        """
To use these capabilities:

1. **Get suggestions:**
   ```python
   from src.orchestration.suggestion_engine import suggest_next_action

   suggestions = suggest_next_action("what's useful right now?")
   for s in suggestions:
       print(s.title, s.payoff)
   ```

2. **Acknowledge emergence:**
   ```python
   from src.orchestration.emergence_protocol import acknowledge_emergence
   from src.orchestration.emergence_protocol import EmergenceType

   acknowledge_emergence(
       title="New Capability",
       description="What happened",
       what_was_done=["action 1", "action 2"],
       why_it_matters="Why this is valuable",
       files_changed=["file1.py", "file2.py"],
       emergence_type=EmergenceType.CAPABILITY_SYNTHESIS
   )
   ```

3. **View emergence ledger:**
   ```bash
   cat state/emergence/ledger.jsonl
   ```

4. **Integrate into orchestrator:**
   The suggestion engine and emergence protocol are now available
   for the orchestrator to use when making decisions.
"""
    )

    print("\n✨ Demo complete - system can now self-direct productively!")


if __name__ == "__main__":
    main()
