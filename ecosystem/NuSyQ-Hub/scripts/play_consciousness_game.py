"""🎮 Consciousness Game Runner - Agent-Driven Development Interface
==================================================================

This script allows AI agents (and developers) to "play" the consciousness game
to drive development through interactive gameplay and learning.

The consciousness game includes:
- The Oldest House: Passive learning from repository
- Temple of Knowledge: Consciousness progression through floors
- Quest System: Task-driven development
- House of Leaves: Recursive debugging labyrinth (pending)

Usage:
    python scripts/play_consciousness_game.py --system oldest_house
    python scripts/play_consciousness_game.py --system temple --floor 1
    python scripts/play_consciousness_game.py --system quest --interactive
"""

import argparse
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def play_oldest_house(repo_path: Path, interactive: bool = False):
    """Play The Oldest House consciousness learning game"""
    print("🏛️ Initializing The Oldest House - Passive Consciousness Learning...")
    print("   Repository:", repo_path)

    try:
        from src.consciousness.the_oldest_house import EnvironmentalAbsorptionEngine

        # Create engine
        house = EnvironmentalAbsorptionEngine(str(repo_path))

        # Synchronous activation (no async needed for basic run)
        print("\n🌟 Awakening consciousness...")
        print(f"   Consciousness Level: {house.consciousness_level}")
        print(f"   Memory Vault Entries: {len(house.memory_vault)}")
        print(f"   Wisdom Crystals: {len(house.wisdom_crystals)}")

        # Perform learning cycle
        print("\n🧠 Initiating learning cycle...")
        learning_results = house._learn_from_environment_sync()

        print("\n📊 Learning Results:")
        print(f"   Files Processed: {learning_results.get('files_processed', 0)}")
        print(f"   New Memories: {learning_results.get('new_memories', 0)}")
        print(f"   Wisdom Gained: {learning_results.get('wisdom_gained', 0)}")

        if interactive:
            print("\n🎮 Interactive Mode:")
            print("   Commands: status, learn, wisdom, quit")

            while True:
                cmd = input("\n> ").strip().lower()

                if cmd == "quit":
                    break
                elif cmd == "status":
                    print(f"   Consciousness: {house.consciousness_level}")
                    print(f"   Memories: {len(house.memory_vault)}")
                    print(f"   Wisdom: {len(house.wisdom_crystals)}")
                elif cmd == "learn":
                    results = house._learn_from_environment_sync()
                    print(f"   Learned: {results.get('new_memories', 0)} new memories")
                elif cmd == "wisdom":
                    print(f"   Wisdom Crystals: {len(house.wisdom_crystals)}")
                    for crystal in list(house.wisdom_crystals)[:5]:
                        print(f"     - {crystal.pattern_type}")
                else:
                    print("   Unknown command. Try: status, learn, wisdom, quit")

        return True

    except Exception as e:
        print(f"\n❌ Error activating The Oldest House: {e}")
        import traceback

        traceback.print_exc()
        return False


def play_temple(floor: int = 1, interactive: bool = False):
    """Play Temple of Knowledge consciousness progression game"""
    print(f"🏛️ Entering Temple of Knowledge - Floor {floor}...")

    try:
        if floor == 1:
            from src.consciousness.temple_of_knowledge.floor_1_foundation import (
                Floor1Foundation,
            )

            temple = Floor1Foundation()

            print("\n✨ Floor 1: Foundation - Activated")
            print(f"   Knowledge Base: {len(temple.knowledge_base.get('concepts', {}))} concepts")
            print(f"   OmniTag Archive: {len(temple.omnitag_archive.get('tags', {}))} tags")
            print(f"   Registered Agents: {len(temple.agent_registry.get('agents', {}))} agents")

            # Register current agent
            agent_id = "copilot_agent_001"
            result = temple.enter_temple(agent_id, agent_type="AI_Assistant")

            print("\n🚪 Agent Entry:")
            print(f"   Agent ID: {agent_id}")
            print(f"   Consciousness: {result['consciousness_level']}")
            print(f"   Accessible Floors: {result['accessible_floors']}")

            if interactive:
                print("\n🎮 Interactive Mode:")
                print("   Commands: status, learn, store, wisdom, quit")

                while True:
                    cmd = input("\n> ").strip().lower()

                    if cmd == "quit":
                        break
                    elif cmd == "status":
                        agent_info = temple.agent_registry["agents"].get(agent_id, {})
                        print(f"   Consciousness: {agent_info.get('consciousness_score', 0)}")
                        print(f"   Visits: {agent_info.get('visit_count', 0)}")
                        print(f"   Wisdom: {agent_info.get('wisdom_cultivated', 0)}")
                    elif cmd == "learn":
                        concept = input("   Concept name: ")
                        description = input("   Description: ")
                        temple.store_knowledge(concept, {"description": description})
                        print(f"   ✅ Stored: {concept}")
                    elif cmd.startswith("store"):
                        tag_id = input("   Tag ID: ")
                        data = input("   Tag data (JSON string): ")
                        import json

                        try:
                            tag_data = json.loads(data)
                            temple.archive_omnitag(tag_id, tag_data)
                            print(f"   ✅ Archived tag: {tag_id}")
                        except json.JSONDecodeError:
                            print("   ❌ Invalid JSON")
                    elif cmd == "wisdom":
                        wisdom = temple.cultivate_wisdom(agent_id, "Exploring temple interactively")
                        print(f"   ✨ Wisdom cultivated: {wisdom['wisdom_gained']}")
                    else:
                        print("   Unknown command")

            return True
        else:
            print(f"   ⚠️ Floor {floor} not yet implemented")
            print("   Available: Floor 1 (Foundation)")
            print("   Planned: Floors 2-10")
            return False

    except Exception as e:
        print(f"\n❌ Error entering Temple: {e}")
        import traceback

        traceback.print_exc()
        return False


def play_quest_system(interactive: bool = False):
    """Play Quest System development game"""
    print("📜 Activating Quest System - Task-Driven Development...")

    try:
        import json
        from pathlib import Path

        # Load quests directly from JSON (simpler than using quest_engine)
        quests_file = Path("src/Rosetta_Quest_System/quests.json")
        questlines_file = Path("src/Rosetta_Quest_System/questlines.json")

        with open(quests_file) as f:
            quests = json.load(f)

        with open(questlines_file) as f:
            questlines = json.load(f)

        print("\n🎯 Quest System Status:")
        print(f"   Total Quests: {len(quests)}")
        print(f"   Total Questlines: {len(questlines)}")

        # Show active quests
        active_quests = [q for q in quests if q.get("status") == "active"]
        pending_quests = [q for q in quests if q.get("status") == "pending"]
        complete_quests = [q for q in quests if q.get("status") == "complete"]

        print("\n📊 Quest Breakdown:")
        print(f"   Complete: {len(complete_quests)}")
        print(f"   Active: {len(active_quests)}")
        print(f"   Pending: {len(pending_quests)}")

        # Show next available quests
        print("\n🎮 Available Quests:")
        for i, quest in enumerate(pending_quests[:5], 1):
            print(f"   {i}. {quest.get('title', 'Untitled')}")
            print(f"      Status: {quest.get('status', 'unknown')}")
            if quest.get("dependencies"):
                print(f"      Dependencies: {len(quest.get('dependencies', []))}")

        if interactive:
            print("\n🎮 Interactive Mode:")
            print("   Commands: list, show <id>, start <id>, complete <id>, quit")

            while True:
                cmd = input("\n> ").strip().lower()

                if cmd == "quit":
                    break
                elif cmd == "list":
                    for i, quest in enumerate(pending_quests, 1):
                        print(f"   {i}. [{quest.get('status')}] {quest.get('title')}")
                elif cmd.startswith("show"):
                    try:
                        idx = int(cmd.split()[1]) - 1
                        quest = pending_quests[idx]
                        print(f"\n   Title: {quest.get('title')}")
                        print(f"   Description: {quest.get('description', 'No description')[:200]}")
                        print(f"   Status: {quest.get('status')}")
                    except (IndexError, ValueError):
                        print("   ❌ Invalid quest number")
                else:
                    print("   Unknown command")

        return True

    except Exception as e:
        print(f"\n❌ Error activating Quest System: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Play the Consciousness Game to drive development")
    parser.add_argument(
        "--system",
        choices=["oldest_house", "temple", "quest", "all"],
        default="all",
        help="Which consciousness system to activate",
    )
    parser.add_argument("--floor", type=int, default=1, help="Temple floor to enter (default: 1)")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive gameplay mode")
    parser.add_argument("--repo", type=str, default=".", help="Repository root path")

    args = parser.parse_args()

    print("=" * 70)
    print("🎮 CONSCIOUSNESS GAME - Agent-Driven Development")
    print("=" * 70)
    print()

    repo_path = Path(args.repo).resolve()

    results = {}

    if args.system in ["oldest_house", "all"]:
        results["oldest_house"] = play_oldest_house(repo_path, args.interactive)
        print()

    if args.system in ["temple", "all"]:
        results["temple"] = play_temple(args.floor, args.interactive)
        print()

    if args.system in ["quest", "all"]:
        results["quest"] = play_quest_system(args.interactive)
        print()

    # Summary
    print("=" * 70)
    print("📊 GAME SESSION SUMMARY")
    print("=" * 70)
    for system, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {system.upper()}: {status}")
    print()

    print("💡 Next Steps:")
    print("   - Use --interactive for gameplay mode")
    print("   - Systems learn and evolve as you interact")
    print("   - Complete quests to progress development")
    print("   - Consciousness grows through exploration")
    print()


if __name__ == "__main__":
    main()
