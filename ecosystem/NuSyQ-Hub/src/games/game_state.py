"""Game State Persistence — Save/Load system for NuSyQ game mechanics.

Provides persistent game state storage for hacking quests, player progression,
faction standings, and skill trees. Supports multiple save slots and auto-save.

Zeta30: Build game state persistence with save/load.

OmniTag: {
    "purpose": "game_persistence",
    "tags": ["Games", "Persistence", "SaveLoad", "State"],
    "category": "infrastructure",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default save directory
SAVES_DIR = Path("state/game_saves")


@dataclass
class PlayerProgress:
    """Player progression state."""

    player_id: str = "default"
    level: int = 1
    total_xp: int = 0
    completed_quests: list[str] = field(default_factory=list)
    active_quests: list[str] = field(default_factory=list)
    unlocked_skills: list[str] = field(default_factory=list)
    skill_levels: dict[str, int] = field(default_factory=dict)


@dataclass
class FactionStanding:
    """Player's standing with game factions."""

    faction_id: str
    reputation: int = 0
    rank: str = "neutral"
    completed_missions: list[str] = field(default_factory=list)


@dataclass
class GameState:
    """Complete game state for save/load operations."""

    save_id: str
    save_name: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    play_time_seconds: float = 0.0
    player: PlayerProgress = field(default_factory=PlayerProgress)
    factions: dict[str, FactionStanding] = field(default_factory=dict)
    game_flags: dict[str, bool] = field(default_factory=dict)
    custom_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert game state to dictionary for serialization."""
        return {
            "save_id": self.save_id,
            "save_name": self.save_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "play_time_seconds": self.play_time_seconds,
            "player": asdict(self.player),
            "factions": {k: asdict(v) for k, v in self.factions.items()},
            "game_flags": self.game_flags,
            "custom_data": self.custom_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Create game state from dictionary."""
        player_data = data.get("player", {})
        player = PlayerProgress(
            player_id=player_data.get("player_id", "default"),
            level=player_data.get("level", 1),
            total_xp=player_data.get("total_xp", 0),
            completed_quests=player_data.get("completed_quests", []),
            active_quests=player_data.get("active_quests", []),
            unlocked_skills=player_data.get("unlocked_skills", []),
            skill_levels=player_data.get("skill_levels", {}),
        )

        factions = {}
        for faction_id, faction_data in data.get("factions", {}).items():
            factions[faction_id] = FactionStanding(
                faction_id=faction_id,
                reputation=faction_data.get("reputation", 0),
                rank=faction_data.get("rank", "neutral"),
                completed_missions=faction_data.get("completed_missions", []),
            )

        return cls(
            save_id=data.get("save_id", ""),
            save_name=data.get("save_name", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            play_time_seconds=data.get("play_time_seconds", 0.0),
            player=player,
            factions=factions,
            game_flags=data.get("game_flags", {}),
            custom_data=data.get("custom_data", {}),
        )


class GameStateManager:
    """Manages game state persistence operations."""

    def __init__(self, saves_dir: Path | None = None):
        """Initialize the game state manager.

        Args:
            saves_dir: Directory for save files. Defaults to state/game_saves.
        """
        self.saves_dir = saves_dir or SAVES_DIR
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        self._active_state: GameState | None = None
        self._auto_save_enabled = True
        self._last_save_time: datetime | None = None

    def _get_save_path(self, save_id: str) -> Path:
        """Get the file path for a save ID."""
        return self.saves_dir / f"{save_id}.json"

    def create_new_game(self, save_name: str = "New Game") -> GameState:
        """Create a new game state.

        Args:
            save_name: Human-readable name for the save.

        Returns:
            New GameState instance.
        """
        save_id = f"save_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        state = GameState(save_id=save_id, save_name=save_name)
        self._active_state = state
        logger.info(f"Created new game: {save_name} ({save_id})")
        return state

    def save_game(self, state: GameState | None = None, slot: str | None = None) -> bool:
        """Save game state to disk.

        Args:
            state: GameState to save. Uses active state if None.
            slot: Optional slot name to save to. Uses state's save_id if None.

        Returns:
            True if save succeeded.
        """
        state = state or self._active_state
        if not state:
            logger.error("No game state to save")
            return False

        save_id = slot or state.save_id
        state.updated_at = datetime.now(UTC).isoformat()

        save_path = self._get_save_path(save_id)
        try:
            save_path.write_text(json.dumps(state.to_dict(), indent=2))
            self._last_save_time = datetime.now(UTC)
            logger.info(f"Saved game to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False

    def load_game(self, save_id: str) -> GameState | None:
        """Load game state from disk.

        Args:
            save_id: ID of the save to load.

        Returns:
            Loaded GameState or None if failed.
        """
        save_path = self._get_save_path(save_id)
        if not save_path.exists():
            logger.error(f"Save file not found: {save_path}")
            return None

        try:
            data = json.loads(save_path.read_text())
            state = GameState.from_dict(data)
            self._active_state = state
            logger.info(f"Loaded game: {state.save_name} ({state.save_id})")
            return state
        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return None

    def list_saves(self) -> list[dict[str, Any]]:
        """List all available save files.

        Returns:
            List of save metadata dicts.
        """
        saves = []
        for save_file in self.saves_dir.glob("*.json"):
            try:
                data = json.loads(save_file.read_text())
                saves.append(
                    {
                        "save_id": data.get("save_id", save_file.stem),
                        "save_name": data.get("save_name", "Unknown"),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "play_time_seconds": data.get("play_time_seconds", 0),
                        "player_level": data.get("player", {}).get("level", 1),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read save metadata from {save_file}: {e}")
        return sorted(saves, key=lambda s: s.get("updated_at", ""), reverse=True)

    def delete_save(self, save_id: str) -> bool:
        """Delete a save file.

        Args:
            save_id: ID of the save to delete.

        Returns:
            True if deletion succeeded.
        """
        save_path = self._get_save_path(save_id)
        if not save_path.exists():
            logger.warning(f"Save file not found: {save_id}")
            return False

        try:
            save_path.unlink()
            logger.info(f"Deleted save: {save_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete save: {e}")
            return False

    def get_active_state(self) -> GameState | None:
        """Get the currently active game state."""
        return self._active_state

    def auto_save(self) -> bool:
        """Perform auto-save if enabled.

        Returns:
            True if auto-save succeeded or was skipped.
        """
        if not self._auto_save_enabled:
            return True
        if not self._active_state:
            return True

        # Create auto-save slot
        auto_id = f"autosave_{self._active_state.save_id}"
        return self.save_game(self._active_state, slot=auto_id)


# Module-level convenience functions
_manager: GameStateManager | None = None


def get_game_manager() -> GameStateManager:
    """Get or create the global game state manager."""
    global _manager
    if _manager is None:
        _manager = GameStateManager()
    return _manager


def new_game(save_name: str = "New Game") -> GameState:
    """Create a new game."""
    return get_game_manager().create_new_game(save_name)


def save_game(state: GameState | None = None) -> bool:
    """Save the current game state."""
    return get_game_manager().save_game(state)


def load_game(save_id: str) -> GameState | None:
    """Load a saved game."""
    return get_game_manager().load_game(save_id)


def list_saves() -> list[dict[str, Any]]:
    """List all available saves."""
    return get_game_manager().list_saves()


logger.info("Game state persistence module loaded")
