#!/usr/bin/env python3
"""NuSyQ - Multi-AI Development Ecosystem CLI

Simple command-line interface for users to interact with the NuSyQ ecosystem.

Usage:
    python nusyq.py status              # Check system health
    python nusyq.py generate webapp     # Generate a web application
    python nusyq.py generate game       # Generate a game
    python nusyq.py generate cli        # Generate a CLI tool
    python nusyq.py quests              # View active quests
    python nusyq.py wisdom              # View consciousness status
    python nusyq.py help                # Show detailed help
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def _out(message: str = "") -> None:
    sys.stdout.write(f"{message}\n")


def cmd_status(args):
    """Show system status and health."""
    from orchestration.multi_ai_orchestrator import MultiAIOrchestrator

    _out("\n🔍 NuSyQ Ecosystem Status")
    _out("=" * 70)

    try:
        orchestrator = MultiAIOrchestrator()
        health = orchestrator.health_check()

        _out("\n💊 System Health:")
        for system, is_healthy in health.items():
            status = "✅ HEALTHY" if is_healthy else "❌ UNAVAILABLE"
            _out(f"  {system:20s} {status}")

        active_count = sum(1 for v in health.values() if v)
        total_count = len(health)

        _out(f"\n📊 Summary: {active_count}/{total_count} systems active")

        if active_count == total_count:
            _out("\n🟢 All systems operational!")
        elif active_count > 0:
            _out(f"\n🟡 {total_count - active_count} systems need attention")
        else:
            _out("\n🔴 No systems available - check installation")

    except Exception as e:
        _out(f"\n❌ Error checking status: {e}")
        return 1

    return 0


def cmd_generate(args):
    """Generate a project using multi-AI collaboration."""
    from agents.code_generator import CodeGenerator

    project_type = args.type

    _out(f"\n🎨 Generating {project_type}...")
    _out("=" * 70)

    try:
        generator = CodeGenerator()

        if project_type == "webapp":
            name = args.name or input("Project name: ").strip() or "my_webapp"
            description = args.description or input("Description: ").strip() or "A web application"
            framework = args.framework or "fastapi"

            _out(f"\n🌐 Generating web app: {name}")
            _out(f"   Framework: {framework}")
            _out(f"   Description: {description}")
            _out("\n⏳ This may take 1-2 minutes...\n")

            files = generator.generate_webapp(description, framework)

        elif project_type == "game":
            concept = args.concept or input("Game concept: ").strip() or "Simple arcade game"
            complexity = args.complexity or "simple"

            _out(f"\n🎮 Generating game: {concept}")
            _out(f"   Complexity: {complexity}")
            _out("\n⏳ This may take 1 minute...\n")

            files = generator.generate_game(concept, complexity)

        elif project_type == "cli":
            name = args.name or input("Package name: ").strip() or "my_cli_tool"
            functionality = args.functionality or input("Functionality: ").strip() or "CLI tool"

            _out(f"\n🛠️  Generating CLI tool: {name}")
            _out(f"   Functionality: {functionality}")
            _out("\n⏳ This may take 1 minute...\n")

            files = generator.generate_package(name, functionality)

        else:
            _out(f"❌ Unknown project type: {project_type}")
            _out("   Supported: webapp, game, cli")
            return 1

        # Save files
        output_dir = Path("projects") / (args.name or project_type)
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        _out(f"\n✅ Generated {len(files)} files:")
        for filename in sorted(files.keys()):
            _out(f"   📄 {filename}")

        _out(f"\n📂 Project location: {output_dir.absolute()}")
        _out("\n🎉 Generation complete!")

    except Exception as e:
        _out(f"\n❌ Error generating project: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


def cmd_quests(args):
    """Show active quests and development tasks."""
    from Rosetta_Quest_System.quest_engine import QuestEngine

    _out("\n🎯 Quest System Status")
    _out("=" * 70)

    try:
        engine = QuestEngine()

        _out("\n📊 Overview:")
        _out(f"   Total Quests: {len(engine.quests)}")
        _out(f"   Total Questlines: {len(engine.questlines)}")

        # Count by status
        statuses = {}
        for quest in engine.quests.values():
            statuses[quest.status] = statuses.get(quest.status, 0) + 1

        _out("\n📋 Quest Status:")
        for status, count in sorted(statuses.items()):
            _out(f"   {status}: {count}")

        # Show active quests
        active = [q for q in engine.quests.values() if q.status == "active"]
        if active:
            _out(f"\n🔥 Active Quests ({len(active)}):")
            for quest in active:
                _out(f"   • {quest.title}")
                _out(f"     [{quest.questline}]")

        # Show pending high-priority quests
        pending_high = [
            q for q in engine.quests.values() if q.status == "pending" and q.priority == "high"
        ]
        if pending_high:
            _out(f"\n⚠️  High Priority Pending ({len(pending_high)}):")
            for quest in pending_high[:3]:
                _out(f"   • {quest.title}")

    except Exception as e:
        _out(f"\n❌ Error loading quests: {e}")
        return 1

    return 0


def cmd_wisdom(args):
    """Show consciousness and wisdom cultivation status."""
    from consciousness.temple_of_knowledge.temple_manager import TempleManager

    _out("\n🏛️  Temple of Knowledge Status")
    _out("=" * 70)

    try:
        temple_data_dir = Path("data/temple_of_knowledge")
        temple = TempleManager(str(temple_data_dir))

        _out("\n📚 Temple Status:")
        _out("   Active Floor: Floor 1 (Foundation)")
        _out(f"   Registered Agents: {len(temple.floor_1.agent_registry)}")

        if temple.floor_1.agent_registry:
            _out("\n👥 Agents:")
            for agent_name, agent_data in list(temple.floor_1.agent_registry.items())[:3]:
                knowledge = agent_data.get("knowledge_accumulated", 0)
                cultivations = agent_data.get("wisdom_cultivations", 0)
                _out(f"   • {agent_name}")
                _out(f"     Knowledge: {knowledge:.2f}")
                _out(f"     Cultivations: {cultivations}")

        _out("\n💡 Use wisdom cultivation to progress through temple floors")

    except Exception as e:
        _out(f"\n❌ Error loading temple: {e}")
        return 1

    return 0


def cmd_help(args):
    """Show detailed help and examples."""
    _out("\n📖 NuSyQ - Multi-AI Development Ecosystem")
    _out("=" * 70)
    _out("\nA system that uses multiple AI models to generate complete projects.")
    _out()
    _out("COMMANDS:")
    _out()
    _out("  status              Check system health and AI availability")
    _out("  generate <type>     Generate a project (webapp, game, cli)")
    _out("  quests              View development quests and tasks")
    _out("  wisdom              View consciousness cultivation status")
    _out("  help                Show this help message")
    _out()
    _out("EXAMPLES:")
    _out()
    _out("  # Check if systems are running")
    _out("  python nusyq.py status")
    _out()
    _out("  # Generate a web application")
    _out("  python nusyq.py generate webapp --name my_app --framework fastapi")
    _out()
    _out("  # Generate a game (interactive prompts)")
    _out("  python nusyq.py generate game")
    _out()
    _out("  # Generate a CLI tool")
    _out("  python nusyq.py generate cli --name my_tool")
    _out()
    _out("  # View active development quests")
    _out("  python nusyq.py quests")
    _out()
    _out("  # View consciousness cultivation")
    _out("  python nusyq.py wisdom")
    _out()
    _out("REQUIREMENTS:")
    _out()
    _out("  • Ollama running locally (http://localhost:11434)")
    _out("  • At least one code-generation model installed")
    _out("  • Recommended: qwen2.5-coder:7b or qwen2.5-coder:14b")
    _out()
    _out("INSTALL OLLAMA MODELS:")
    _out()
    _out("  ollama pull qwen2.5-coder:7b")
    _out("  ollama pull qwen2.5-coder:14b")
    _out()
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NuSyQ Multi-AI Development Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status command
    subparsers.add_parser("status", help="Check system health")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a project")
    generate_parser.add_argument("type", choices=["webapp", "game", "cli"], help="Project type")
    generate_parser.add_argument("--name", help="Project name")
    generate_parser.add_argument("--description", help="Project description")
    generate_parser.add_argument("--framework", help="Framework (webapp only)")
    generate_parser.add_argument("--concept", help="Game concept (game only)")
    generate_parser.add_argument(
        "--complexity", choices=["simple", "medium", "complex"], help="Complexity"
    )
    generate_parser.add_argument("--functionality", help="Functionality (cli only)")

    # Quests command
    subparsers.add_parser("quests", help="View development quests")

    # Wisdom command
    subparsers.add_parser("wisdom", help="View consciousness status")

    # Help command
    subparsers.add_parser("help", help="Show detailed help")

    args = parser.parse_args()

    if not args.command:
        cmd_help(args)
        return 0

    # Route to appropriate command
    commands = {
        "status": cmd_status,
        "generate": cmd_generate,
        "quests": cmd_quests,
        "wisdom": cmd_wisdom,
        "help": cmd_help,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
