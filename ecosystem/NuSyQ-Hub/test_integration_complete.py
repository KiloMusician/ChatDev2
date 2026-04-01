"""Integration test: House of Leaves + Quest System + Temple of Knowledge"""

import asyncio

from src.games.house_of_leaves import HouseOfLeaves
from src.integration.game_quest_bridge import HouseOfLeavesGameBridge


async def test_integration():
    print("=" * 70)
    print("🎮 HOUSE OF LEAVES + QUEST SYSTEM + TEMPLE OF KNOWLEDGE INTEGRATION TEST")
    print("=" * 70)

    # Initialize systems
    game = HouseOfLeaves(seed=42)
    game_bridge = HouseOfLeavesGameBridge()

    # Register event handlers
    async def track_quest_creation(event, quest_data):
        if quest_data:
            title = quest_data.get("title", "Unknown")
            print(f"  📋 Quest auto-created: {title}")

    game_bridge.register_event_handler("puzzle_solved", track_quest_creation)

    # Teleport to puzzle room
    game.player.current_room_id = "debug_chamber_1"

    print("\n1️⃣ INITIAL STATE:")
    print(f"   Bugs Fixed: {game.player.bugs_fixed}")
    print(f"   Temple Floor: {game.player.temple_floor_unlocked}")

    print("\n2️⃣ SOLVING PUZZLE:")
    puzzle_result = await game.solve_puzzle()
    # Extract just the key info
    for line in puzzle_result.split("\n"):
        if line.strip() and any(
            x in line for x in ["Puzzle", "Bug", "Temple", "consciousness", "Floor"]
        ):
            print(f"   {line.strip()}")

    # Emit game event
    print("\n3️⃣ EMITTING GAME EVENTS:")
    await game_bridge.on_puzzle_solved("Fix import error")
    print("   ✓ Puzzle solved event emitted")

    # Show final state
    print("\n4️⃣ FINAL STATE:")
    print(f"   Bugs Fixed: {game.player.bugs_fixed}")
    print(f"   Temple Floor: {game.player.temple_floor_unlocked}")
    print(f"   Game Events Logged: {game_bridge.get_game_statistics()['total_events']}")

    print("\n✅ INTEGRATION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_integration())
