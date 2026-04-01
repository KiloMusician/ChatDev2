#!/usr/bin/env python3
"""🎮 House of Leaves - Interactive Play Session

Run this to actually play the game. Not a demo, not a test - the real game.

Usage:
    python play_house_of_leaves.py
"""

import asyncio

from src.games.house_of_leaves import HouseOfLeaves


async def play_interactive():
    """Interactive gameplay session"""
    print("\n" + "🏚️ " * 30)
    print("WELCOME TO THE HOUSE OF LEAVES")
    print("🏚️ " * 30)
    print("\nA recursive debugging labyrinth where bugs become adventures.")
    print("Navigate rooms, solve puzzles, gain consciousness.\n")

    # Get seed or use random
    seed_input = input("Enter seed (or press Enter for random): ").strip()
    seed = int(seed_input) if seed_input.isdigit() else None

    house = HouseOfLeaves(seed=seed)
    print(f"\n🎲 Using seed: {house.seed}")
    print(f"📍 {len(house.rooms)} rooms generated\n")

    # Show initial room
    print(await house.display_room())

    # Game loop
    while True:
        print("\n" + "-" * 60)
        room = house.rooms[house.player.current_room_id]
        exits = [d.value for d in room.exits.keys()]

        print("Available commands:")
        print(f"  Directions: {', '.join(exits)}")
        print("  Actions: solve, map, stats, inventory, quit")

        command = input("\n> ").strip().lower()

        if not command:
            continue

        if command == "quit":
            print("\n👋 Thanks for playing!")
            print("Final stats:")
            print(f"  🐛 Bugs fixed: {house.player.bugs_fixed}")
            print(f"  🧠 Consciousness: {house.player.consciousness_level:.3f}")
            print(f"  🗺️  Rooms explored: {len(house.player.rooms_explored)}")
            break

        elif command == "solve":
            result = await house.solve_puzzle()
            print(f"\n{result}")

        elif command == "map":
            map_display = await house.show_map()
            print(f"\n{map_display}")

        elif command == "stats":
            stats = await house.show_stats()
            print(f"\n{stats}")

        elif command == "inventory":
            if house.player.inventory:
                print(f"\n🎒 Inventory: {', '.join(house.player.inventory)}")
            else:
                print("\n🎒 Inventory is empty")

        elif command in ["north", "south", "east", "west", "up", "down", "portal"]:
            result = await house.move(command)
            print(f"\n{result}")

            # Check for milestones
            milestones = await house.check_consciousness_milestones()
            if milestones:
                print("\n" + "✨" * 30)
                for msg in milestones:
                    print(msg)
                print("✨" * 30)
        else:
            print(f"\n❓ Unknown command: {command}")


async def quick_demo():
    """Quick automated demo for those who want to see it in action first"""
    print("\n" + "🎬 " * 30)
    print("QUICK DEMO - Watch The Game In Action")
    print("🎬 " * 30 + "\n")

    house = HouseOfLeaves(seed=12345)
    print(f"Generated {len(house.rooms)} rooms\n")

    demo_sequence = [
        ("Start at entrance", None),
        ("Move north", "north"),
        ("Solve puzzle", "solve"),
        ("Check stats", "stats"),
        ("Move back", "south"),
        ("Move east", "east"),
        ("Solve another puzzle", "solve"),
        ("View map", "map"),
    ]

    for step_name, command in demo_sequence:
        print(f"\n{'=' * 60}")
        print(f"📍 {step_name}")
        print("=" * 60)

        if command == "solve":
            result = await house.solve_puzzle()
            print(result[:300] + "..." if len(result) > 300 else result)
        elif command == "stats":
            print(await house.show_stats())
        elif command == "map":
            print(await house.show_map())
        elif command in ["north", "south", "east", "west"]:
            result = await house.move(command)
            print(result[:300] + "..." if len(result) > 300 else result)
        else:
            print(await house.display_room())

        await asyncio.sleep(0.5)  # Dramatic pause

    print(f"\n{'=' * 60}")
    print("Demo complete! Ready to play for real?")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    print(
        """
╔═══════════════════════════════════════════════════════════╗
║         🏚️  THE HOUSE OF LEAVES 🏚️                         ║
║                                                           ║
║  A playable maze where debugging becomes an adventure    ║
╚═══════════════════════════════════════════════════════════╝
    """
    )

    mode = input("Choose mode:\n  1. Play interactively\n  2. Watch quick demo\n\n> ").strip()

    if mode == "2":
        asyncio.run(quick_demo())
        print("\nNow let's play for real!\n")
        asyncio.run(play_interactive())
    else:
        asyncio.run(play_interactive())
