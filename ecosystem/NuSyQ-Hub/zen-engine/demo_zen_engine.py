#!/usr/bin/env python3
"""Zen-Engine Complete Demonstration

Showcases all capabilities of the Zen-Engine:
1. Error observation and pattern detection
2. Rule matching and confidence scoring
3. Command interception and prevention
4. Automatic rule generation
5. NuSyQ-Hub integration
6. Lore and glyph system

OmniTag: [zen-engine, demo, showcase, comprehensive]
MegaTag: ZEN_ENGINE⨳DEMO⦾FULL_SYSTEM_SHOWCASE→∞
"""

import sys
from pathlib import Path

# Add zen-engine to path
sys.path.insert(0, str(Path(__file__).parent))

from zen_engine.agents import (
    CodexLoader,
    ErrorObserver,
    Matcher,
    ReflexEngine,
)
from zen_engine.agents.builder import CodexBuilder


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_error_observation():
    """Demonstrate error observation capabilities."""
    print_header("1. ERROR OBSERVATION & PATTERN DETECTION")

    observer = ErrorObserver()

    test_cases = [
        {
            "error": "The term 'import' is not recognized as the name of a cmdlet",
            "command": "import os",
            "shell": "powershell",
            "description": "Python in PowerShell",
        },
        {
            "error": "ModuleNotFoundError: No module named 'requests'",
            "command": "import requests",
            "shell": "python",
            "description": "Missing Python module",
        },
        {
            "error": "error: Your local changes would be overwritten by checkout",
            "command": "git checkout main",
            "shell": "bash",
            "description": "Git uncommitted changes",
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"  Command: {test['command']}")
        print(f"  Shell: {test['shell']}")

        event = observer.observe_error(
            error_text=test["error"],
            command=test["command"],
            shell=test["shell"],
            platform="windows",
            agent="demo",
        )

        if event:
            print(f"  ✅ Detected: {event.symptom}")
            print(f"  📋 Patterns: {', '.join(event.patterns_detected)}")
            print(f"  🔧 Auto-fixable: {event.auto_fixable}")
            print(f"  📍 Suggested rules: {', '.join(event.suggested_rules)}")
        else:
            print("  ❌ No pattern detected")

        print()


def demo_rule_matching():
    """Demonstrate rule matching and advice generation."""
    print_header("2. RULE MATCHING & WISDOM RETRIEVAL")

    observer = ErrorObserver()
    matcher = Matcher()

    # Create an error event
    event = observer.observe_error(
        error_text="The term 'import' is not recognized",
        command="import os",
        shell="powershell",
        platform="windows",
    )

    if not event:
        print("❌ Could not create event for demonstration")
        return

    print(f"Event: {event.id}")
    print(f"Symptom: {event.symptom}\n")

    # Match against rules
    matches = matcher.match_event_to_rules(event)

    print(f"Found {len(matches)} matching rules:\n")

    for i, match in enumerate(matches[:2], 1):  # Show top 2
        print(f"Match {i}: {match.rule.id}")
        print(f"Confidence: {match.confidence:.2%}")
        print(f"Reasons: {', '.join(match.match_reasons)}")
        print()

    # Show full advice
    if matches:
        print("Full Zen Advice:")
        print("-" * 70)
        advice = matcher.compose_multi_rule_advice(event, matches)
        print(advice)


def demo_command_interception():
    """Demonstrate proactive command interception."""
    print_header("3. COMMAND INTERCEPTION & PREVENTION")

    reflex = ReflexEngine()

    test_commands = [
        ("import os", "powershell"),
        ("git checkout main", "bash"),
        ("subprocess.run(['ls'])", "python"),
        ("open('file.txt', 'r')", "python"),
    ]

    for command, shell in test_commands:
        print(f"Command: {command}")
        print(f"Shell: {shell}")

        final_cmd, advice = reflex.intercept_and_advise(command, shell=shell, auto_apply_fix=False)

        if advice:
            print(advice)

        if final_cmd != command:
            print(f"🔄 Suggested: {final_cmd}")
        elif final_cmd:
            print("✅ Approved")
        else:
            print("🛑 Blocked")

        print()


def demo_automatic_rule_generation():
    """Demonstrate automatic rule generation from patterns."""
    print_header("4. AUTOMATIC RULE GENERATION")

    observer = ErrorObserver()
    builder = CodexBuilder()

    # Simulate multiple similar errors
    print("Simulating 3 similar TypeError events...\n")

    events = [
        observer.observe_error(
            error_text="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            command="result = 5 + '10'",
            shell="python",
        ),
        observer.observe_error(
            error_text='TypeError: can only concatenate str (not "int") to str',
            command="text = 'Number: ' + 42",
            shell="python",
        ),
        observer.observe_error(
            error_text="TypeError: unsupported operand type(s)",
            command="x = 10 + '5'",
            shell="python",
        ),
    ]

    events = [e for e in events if e is not None]

    if not events:
        print("❌ Could not generate events")
        return

    # Analyze and generate proposals
    proposals = builder.analyze_events(events)

    print(f"Generated {len(proposals)} rule proposals:\n")

    for proposal in proposals:
        print(f"Proposed Rule: {proposal.proposed_id}")
        print(f"  Confidence: {proposal.confidence:.2%}")
        print(f"  Lesson: {proposal.lesson_short}")
        print(f"  Tags: {', '.join(proposal.tags)}")
        if proposal.proposed_glyph:
            print(f"  Glyph: {proposal.proposed_glyph}")
        print(f"  Supporting Events: {len(proposal.supporting_events or [])}")
        print()


def demo_codex_statistics():
    """Show codex statistics and capabilities."""
    print_header("5. ZENCODEX STATISTICS & CAPABILITIES")

    codex = CodexLoader()

    stats = codex.stats()

    print("📊 Codex Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n🎓 Foundational Rules:")
    foundational = codex.get_foundational_rules()
    for rule in foundational[:5]:
        print(f"  - {rule.id}: {rule.lesson['short']}")

    print("\n🔧 Auto-Fixable Rules:")
    auto_fix = codex.get_auto_fixable_rules()
    for rule in auto_fix[:5]:
        print(f"  - {rule.id}: {rule.actions.get('fix_strategy', 'N/A')}")

    print("\n📚 Rule Clusters:")
    clusters = codex.get_rule_clusters()
    for cluster_name, rule_ids in clusters.items():
        print(f"  {cluster_name}: {len(rule_ids)} rules")


def demo_glyph_system():
    """Demonstrate the glyph and lore system."""
    print_header("6. GLYPH & LORE SYSTEM")

    codex = CodexLoader()

    # Show rules with glyphs
    rules_with_lore = [
        rule for rule in codex.rules.values() if rule.lore and rule.lore.get("glyph")
    ]

    print(f"Rules with glyphs: {len(rules_with_lore)}\n")

    for rule in rules_with_lore[:3]:
        print(f"Rule: {rule.id}")
        print(f"  Glyph: {rule.lore.get('glyph', 'N/A')}")
        print(f"  Story: {rule.lore.get('story', 'N/A')[:100]}...")
        print(f"  Moral: {rule.lore.get('moral', 'N/A')}")
        print()


def demo_nusyq_integration():
    """Demonstrate NuSyQ-Hub integration."""
    print_header("7. NUSYQ-HUB INTEGRATION")

    try:
        from zen_engine.systems.nusyq_integration import NuSyQIntegrationBridge

        bridge = NuSyQIntegrationBridge()

        status = bridge.status_report()

        print("🌐 Integration Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

        print("\n📊 Available Systems:")
        print(f"  Culture Ship: {'✅' if bridge.culture_ship else '❌'}")
        print(f"  SimulatedVerse: {'✅' if bridge.simulatedverse else '❌'}")
        print(f"  MultiAI Orchestrator: {'✅' if bridge.multi_ai else '❌'}")

    except Exception as e:
        print(f"⚠️  Integration demo skipped: {e}")


def demo_end_to_end_workflow():
    """Demonstrate complete end-to-end workflow."""
    print_header("8. END-TO-END WORKFLOW")

    print("Scenario: Developer tries to run Python in PowerShell\n")

    # 1. Error occurs
    print("1️⃣  Error occurs:")
    error_text = "The term 'import' is not recognized"
    command = "import os"
    shell = "powershell"
    print(f"   Command: {command}")
    print(f"   Error: {error_text}\n")

    # 2. ErrorObserver captures it
    print("2️⃣  ErrorObserver captures event:")
    observer = ErrorObserver()
    event = observer.observe_error(error_text=error_text, command=command, shell=shell)
    if event:
        print(f"   Event ID: {event.id}")
        print(f"   Symptom: {event.symptom}\n")

    # 3. Matcher finds relevant rules
    print("3️⃣  Matcher finds relevant rules:")
    matcher = Matcher()
    matches = matcher.match_event_to_rules(event)
    if matches:
        best = matches[0]
        print(f"   Best match: {best.rule.id}")
        print(f"   Confidence: {best.confidence:.2%}\n")

    # 4. Advice is provided
    print("4️⃣  Zen advice provided:")
    if matches:
        print(f"   {best.rule.lesson['short']}")
        if best.suggested_action:
            print(f"   Suggested: {best.suggested_action.get('example_after', 'N/A')}\n")

    # 5. Future prevention
    print("5️⃣  Future prevention active:")
    reflex = ReflexEngine()
    final_cmd, advice = reflex.intercept_and_advise(command, shell=shell)
    print("   Next time this command is attempted:")
    print(f"   Reflex Engine will suggest: {final_cmd}")


def main():
    """Run complete demonstration."""
    print("\n" + "🧘" * 35)
    print("\n   ZEN-ENGINE: RECURSIVE WISDOM SYSTEM")
    print("   Complete System Demonstration")
    print("\n" + "🧘" * 35)

    try:
        demo_error_observation()
        demo_rule_matching()
        demo_command_interception()
        demo_automatic_rule_generation()
        demo_codex_statistics()
        demo_glyph_system()
        demo_nusyq_integration()
        demo_end_to_end_workflow()

        print_header("DEMONSTRATION COMPLETE")
        print("✅ All systems operational")
        print("📚 Codex loaded and ready")
        print("🔮 Wisdom flows recursively")
        print("\n🧘 May your code flow like water, and your errors teach like masters.")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
