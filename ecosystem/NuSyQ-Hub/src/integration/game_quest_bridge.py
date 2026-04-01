"""Game-Quest Integration Bridge - Converts game events to quest system.

This module provides bidirectional communication between game systems
(House of Leaves, etc.) and the Rosetta Quest System, enabling:
- Game feature completion → Quest generation
- Quest tracking through gameplay
- XP/rewards sync between systems
- Achievement system integration

[OmniTag]
{
    "purpose": "Bridge game development events to quest system",
    "dependencies": ["house_of_leaves", "quest_engine", "quest_temple_bridge"],
    "context": "Gamification of quest tracking and development metrics",
    "evolution_stage": "v1.0_implementation"
}
[/OmniTag]
"""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class GameEventType:
    """Event types emitted by game systems."""

    PUZZLE_SOLVED = "puzzle_solved"
    ROOM_DISCOVERED = "room_discovered"
    ENEMY_DEFEATED = "enemy_defeated"
    ITEM_COLLECTED = "item_collected"
    MILESTONE_REACHED = "milestone_reached"
    FLOOR_UNLOCKED = "floor_unlocked"
    SESSION_COMPLETED = "session_completed"


class GameEvent:
    """Represents a game event that can trigger quest updates."""

    def __init__(
        self,
        event_type: str,
        game_id: str,
        game_name: str,
        timestamp: datetime | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a game event.

        Args:
            event_type: Type of event (from GameEventType)
            game_id: ID of the game instance
            game_name: Name of the game
            timestamp: When event occurred (defaults to now)
            data: Additional event data

        """
        self.event_type = event_type
        self.game_id = game_id
        self.game_name = game_name
        self.timestamp = timestamp or datetime.now()
        self.data = data or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "game_id": self.game_id,
            "game_name": self.game_name,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


class GameQuestMapper:
    """Maps game events to quest system updates.

    Provides rules for converting game metrics and achievements
    into quest system artifacts.
    """

    # Default mappings from game events to quest updates
    EVENT_QUEST_MAPPINGS: ClassVar[dict[str, dict[str, str | int]]] = {
        GameEventType.PUZZLE_SOLVED: {
            "questline": "game_systems_implementation",
            "points_awarded": 5,
            "description_template": "Solved puzzle in {game_name}: {puzzle_name}",
        },
        GameEventType.ROOM_DISCOVERED: {
            "questline": "game_systems_implementation",
            "points_awarded": 2,
            "description_template": "Discovered room in {game_name}: {room_name}",
        },
        GameEventType.MILESTONE_REACHED: {
            "questline": "game_systems_implementation",
            "points_awarded": 10,
            "description_template": "Reached milestone in {game_name}: {milestone_name}",
        },
        GameEventType.SESSION_COMPLETED: {
            "questline": "game_systems_implementation",
            "points_awarded": 25,
            "description_template": "Completed session in {game_name}",
        },
    }

    @staticmethod
    def get_quest_data_from_event(event: GameEvent) -> dict[str, Any] | None:
        """Convert a game event to quest system data.

        Args:
            event: Game event to convert

        Returns:
            Quest data dict or None if no mapping exists

        """
        if event.event_type not in GameQuestMapper.EVENT_QUEST_MAPPINGS:
            return None

        mapping = GameQuestMapper.EVENT_QUEST_MAPPINGS[event.event_type]

        # Build description from template
        description_template = str(mapping["description_template"])
        description = description_template.format(
            game_name=event.game_name,
            puzzle_name=event.data.get("puzzle_name", "Unknown"),
            room_name=event.data.get("room_name", "Unknown"),
            milestone_name=event.data.get("milestone_name", "Unknown"),
        )

        return {
            "title": f"[{event.game_name}] {event.event_type}",
            "description": description,
            "questline": mapping["questline"],
            "points": mapping["points_awarded"],
            "tags": ["game_event", event.game_name.lower()],
            "source_event": event.to_dict(),
        }


class GameQuestIntegrationBridge:
    """Main bridge for game-quest integration.

    Handles:
    - Event routing from games to quest system
    - Quest auto-generation from game events
    - Bidirectional state synchronization
    - Metric aggregation
    """

    def __init__(self, event_log_path: Path | None = None) -> None:
        """Initialize the bridge.

        Args:
            event_log_path: Path to store game event logs

        """
        self.event_log_path = event_log_path or Path("data/logs/game_events.jsonl")
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Event handlers registry
        self.event_handlers: dict[str, list[Callable]] = {}

        # Event statistics
        self.event_stats: dict[str, int] = {}

        logger.info("Game-Quest Integration Bridge initialized")

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable,
    ) -> None:
        """Register a handler for specific event type.

        Args:
            event_type: Type of event to handle
            handler: Callable that processes the event

        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.info("Registered handler for %s", event_type)

    async def emit_event(self, event: GameEvent) -> dict[str, Any]:
        """Emit a game event and process it through registered handlers.

        Args:
            event: The game event to emit

        Returns:
            Result dict with processing info

        """
        result: dict[str, Any] = {
            "event_id": f"{event.game_id}_{int(event.timestamp.timestamp())}",
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "quest_data": None,
            "handlers_called": 0,
            "handlers_succeeded": 0,
            "errors": [],
        }

        # Log the event
        self._log_event(event)

        # Track statistics
        if event.event_type not in self.event_stats:
            self.event_stats[event.event_type] = 0
        self.event_stats[event.event_type] += 1

        # Convert to quest data if possible
        quest_data = GameQuestMapper.get_quest_data_from_event(event)
        result["quest_data"] = quest_data

        # Call registered handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                result["handlers_called"] += 1
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, quest_data)
                    else:
                        handler(event, quest_data)
                    result["handlers_succeeded"] += 1
                except Exception as e:
                    result["errors"].append(str(e))
                    logger.exception("Handler error: %s", e)

        logger.info(
            f"Event emitted: {event.event_type} ({result['handlers_succeeded']}/{result['handlers_called']} handlers)",
        )

        return result

    def _log_event(self, event: GameEvent) -> None:
        """Log game event to JSONL file."""
        with open(self.event_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def get_game_statistics(self, _game_name: str | None = None) -> dict[str, Any]:
        """Get statistics about game events.

        Args:
            game_name: Filter by game name (optional)

        Returns:
            Statistics dictionary

        """
        return {
            "total_events": sum(self.event_stats.values()),
            "events_by_type": self.event_stats,
            "timestamp": datetime.now().isoformat(),
        }


class HouseOfLeavesGameBridge(GameQuestIntegrationBridge):
    """Specialized bridge for House of Leaves game events."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize House of Leaves bridge."""
        super().__init__(*args, **kwargs)
        self.game_id = "house_of_leaves_001"
        self.game_name = "House of Leaves"

    async def on_puzzle_solved(self, puzzle_name: str) -> dict[str, Any]:
        """Emit event when puzzle is solved.

        Args:
            puzzle_name: Name of the puzzle

        Returns:
            Event processing result

        """
        event = GameEvent(
            event_type=GameEventType.PUZZLE_SOLVED,
            game_id=self.game_id,
            game_name=self.game_name,
            data={"puzzle_name": puzzle_name},
        )
        return await self.emit_event(event)

    async def on_room_discovered(self, room_name: str, room_type: str) -> dict[str, Any]:
        """Emit event when room is discovered.

        Args:
            room_name: Name of the room
            room_type: Type of the room

        Returns:
            Event processing result

        """
        event = GameEvent(
            event_type=GameEventType.ROOM_DISCOVERED,
            game_id=self.game_id,
            game_name=self.game_name,
            data={"room_name": room_name, "room_type": room_type},
        )
        return await self.emit_event(event)

    async def on_floor_unlocked(self, floor_number: int) -> dict[str, Any]:
        """Emit event when temple floor is unlocked.

        Args:
            floor_number: Number of the unlocked floor

        Returns:
            Event processing result

        """
        event = GameEvent(
            event_type=GameEventType.FLOOR_UNLOCKED,
            game_id=self.game_id,
            game_name=self.game_name,
            data={"floor_number": floor_number},
        )
        return await self.emit_event(event)

    async def on_session_completed(
        self,
        puzzles_solved: int,
        rooms_discovered: int,
        duration_minutes: float,
    ) -> dict[str, Any]:
        """Emit event when play session completes.

        Args:
            puzzles_solved: Number of puzzles solved
            rooms_discovered: Number of rooms discovered
            duration_minutes: Session duration in minutes

        Returns:
            Event processing result

        """
        event = GameEvent(
            event_type=GameEventType.SESSION_COMPLETED,
            game_id=self.game_id,
            game_name=self.game_name,
            data={
                "puzzles_solved": puzzles_solved,
                "rooms_discovered": rooms_discovered,
                "duration_minutes": duration_minutes,
            },
        )
        return await self.emit_event(event)


async def example_game_quest_integration() -> None:
    """Example showing game-quest integration workflow."""
    # Create House of Leaves bridge
    bridge = HouseOfLeavesGameBridge()

    # Register example handlers
    async def log_quest_creation(event: GameEvent, quest_data: dict | None) -> None:
        if quest_data:
            pass

    bridge.register_event_handler(GameEventType.PUZZLE_SOLVED, log_quest_creation)

    # Emit example events

    # Solve a puzzle
    await bridge.on_puzzle_solved("Fix import error")

    # Discover a room
    await bridge.on_room_discovered("Debug Chamber", "debug_chamber")

    # Unlock a floor
    await bridge.on_floor_unlocked(2)

    # Complete session
    await bridge.on_session_completed(
        puzzles_solved=3,
        rooms_discovered=5,
        duration_minutes=15.5,
    )

    # Show statistics
    bridge.get_game_statistics()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(example_game_quest_integration())
