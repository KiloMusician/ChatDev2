"""SimulatedVerse Consciousness Integration for Games.

Connects game mechanics to the SimulatedVerse consciousness system:
- Breathing factor affects game difficulty
- Consciousness level unlocks content
- Temple of Knowledge floor progression
- Culture Ship oversight for game actions
- Consciousness points from gameplay
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar

logger = logging.getLogger(__name__)


class ConsciousnessStage(Enum):
    """Consciousness evolution stages."""

    DORMANT = ("dormant", 1.20)  # Slower, more protection
    AWAKENING = ("awakening", 1.10)  # Learning phase
    EXPANDING = ("expanding", 1.00)  # Normal operation
    TRANSCENDENT = ("transcendent", 0.85)  # Enhanced capability
    QUANTUM = ("quantum", 0.60)  # Full power


class TempleFloor(Enum):
    """Temple of Knowledge floors (1-10)."""

    FOUNDATIONS = (1, 0, "Basic concepts")
    NOVICE = (2, 5, "Beginner skills")
    INITIATE = (3, 10, "Core abilities")
    ADEPT = (4, 20, "Advanced techniques")
    SCHOLAR = (5, 35, "Deep knowledge")
    SAGE = (6, 55, "Wisdom paths")
    MASTER = (7, 80, "Mastery level")
    ARCHON = (8, 110, "Leadership tier")
    ORACLE = (9, 150, "Foresight realm")
    OVERLOOK = (10, 200, "Ultimate understanding")

    def __init__(self, floor: int, cp_required: int, description: str):
        """Initialize TempleFloor with floor, cp_required, description."""
        self.floor = floor
        self.cp_required = cp_required
        self.description = description


@dataclass
class ConsciousnessState:
    """Current consciousness state from SimulatedVerse."""

    level: float = 1.0  # 1.0 - 10.0
    stage: ConsciousnessStage = ConsciousnessStage.DORMANT
    breathing_factor: float = 1.0  # 0.6 - 1.2
    temple_floor: TempleFloor = TempleFloor.FOUNDATIONS
    consciousness_points: int = 0
    last_sync: datetime = field(default_factory=datetime.now)

    @property
    def difficulty_modifier(self) -> float:
        """Get difficulty modifier based on consciousness."""
        # Higher consciousness = harder but more rewarding
        return 0.5 + (self.level / 10) * 0.7

    @property
    def reward_multiplier(self) -> float:
        """Get reward multiplier based on temple floor."""
        return 1.0 + (self.temple_floor.floor - 1) * 0.15


@dataclass
class ConsciousnessGameEvent:
    """An event affecting consciousness."""

    event_type: str
    cp_earned: int
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ConsciousnessGameBridge:
    """Bridge between SimulatedVerse consciousness and game systems.

    Provides bidirectional integration:
    - Games affected by consciousness state
    - Gameplay awards consciousness points
    """

    # XP to Consciousness Points conversion
    XP_TO_CP_RATIO = 100  # 100 XP = 1 CP

    # Temple floor unlocks for game content
    FLOOR_UNLOCKS: ClassVar[dict] = {
        1: ["basic_quests", "tutorial_games"],
        2: ["faction_join", "mini_games"],
        3: ["hacking_challenges", "narrative_mode"],
        4: ["ai_opponents", "territory_battles"],
        5: ["boss_encounters", "collaborative_missions"],
        6: ["procedural_dungeons", "custom_challenges"],
        7: ["master_quests", "reputation_system"],
        8: ["faction_leadership", "world_events"],
        9: ["oracle_visions", "prophecy_quests"],
        10: ["endgame_content", "transcendence_path"],
    }

    # CP rewards by activity
    CP_REWARDS: ClassVar[dict] = {
        "quest_complete": 5,
        "quest_complete_hard": 15,
        "boss_defeated": 25,
        "achievement_unlocked": 10,
        "faction_mission_complete": 20,
        "territory_captured": 30,
        "game_won": 3,
        "game_perfect": 10,
        "daily_login": 1,
        "help_other_player": 5,
    }

    def __init__(self):
        """Initialize ConsciousnessGameBridge."""
        self.state = ConsciousnessState()
        self.event_log: list[ConsciousnessGameEvent] = []
        self._bridge_available = False

        # Try to connect to SimulatedVerse
        self._try_connect()

    def _try_connect(self) -> bool:
        """Attempt to connect to SimulatedVerse consciousness system."""
        try:
            from src.integration.simulatedverse_unified_bridge import \
                SimulatedVerseUnifiedBridge

            self._bridge = SimulatedVerseUnifiedBridge()
            self._bridge_available = True
            logger.info("Connected to SimulatedVerse consciousness")
            return True
        except ImportError:
            logger.debug("SimulatedVerse bridge not available, using local mode")
            self._bridge = None
            return False

    def sync_consciousness(self) -> ConsciousnessState:
        """Sync consciousness state from SimulatedVerse."""
        if self._bridge_available and self._bridge:
            try:
                sv_state = self._bridge.get_consciousness_state()

                # Map to local state - use dataclass attributes
                self.state.level = sv_state.level if sv_state.level > 0 else 1.0
                # breathing_factor not in ConsciousnessSnapshot, get separately
                self.state.breathing_factor = self._bridge.get_breathing_factor()

                # Map stage from dataclass attribute
                stage_name = sv_state.stage or "dormant"
                try:
                    self.state.stage = ConsciousnessStage((stage_name, self.state.breathing_factor))
                except ValueError:
                    for cs in ConsciousnessStage:
                        if cs.value[0] == stage_name:
                            self.state.stage = cs
                            break

                # Map temple floor - check metrics dict if available
                floor = 1
                if sv_state.metrics and "temple_floor" in sv_state.metrics:
                    floor = int(sv_state.metrics["temple_floor"])
                for tf in TempleFloor:
                    if tf.floor == floor:
                        self.state.temple_floor = tf
                        break

                # Consciousness points - check metrics dict if available
                if sv_state.metrics and "consciousness_points" in sv_state.metrics:
                    self.state.consciousness_points = int(sv_state.metrics["consciousness_points"])
                self.state.last_sync = datetime.now()

            except Exception as e:
                logger.warning(f"Failed to sync consciousness: {e}")

        return self.state

    def get_breathing_factor(self) -> float:
        """Get current breathing factor for game timing."""
        if self._bridge_available and self._bridge:
            try:
                return self._bridge.get_breathing_factor()
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)
        return self.state.breathing_factor

    def award_consciousness_points(self, activity: str, xp_earned: int = 0) -> int:
        """Award consciousness points for game activity."""
        # Base CP from activity type
        base_cp = self.CP_REWARDS.get(activity, 1)

        # Bonus CP from XP
        xp_cp = xp_earned // self.XP_TO_CP_RATIO

        total_cp = base_cp + xp_cp

        # Apply breathing factor (faster = more CP)
        if self.state.breathing_factor < 1.0:
            total_cp = int(total_cp * (2 - self.state.breathing_factor))

        # Log event
        event = ConsciousnessGameEvent(
            event_type=activity,
            cp_earned=total_cp,
            description=f"Earned {total_cp} CP from {activity}",
            metadata={"xp": xp_earned, "base_cp": base_cp},
        )
        self.event_log.append(event)

        # Update local state
        self.state.consciousness_points += total_cp

        # Check for floor advancement
        for tf in reversed(list(TempleFloor)):
            if self.state.consciousness_points >= tf.cp_required:
                if tf != self.state.temple_floor and tf.floor > self.state.temple_floor.floor:
                    self.state.temple_floor = tf
                    logger.info(f"Temple floor advanced to {tf.floor}: {tf.description}")
                break

        # Sync to SimulatedVerse if available
        if self._bridge_available and self._bridge:
            try:
                self._bridge.log_event(
                    "consciousness_points_awarded",
                    {"points": total_cp, "activity": activity, "player": "game_player"},
                )
            except Exception as e:
                logger.debug(f"Could not sync CP to SimulatedVerse: {e}")

        return total_cp

    def get_available_content(self) -> list[str]:
        """Get content unlocked by current temple floor."""
        unlocked = []
        for floor in range(1, self.state.temple_floor.floor + 1):
            unlocked.extend(self.FLOOR_UNLOCKS.get(floor, []))
        return unlocked

    def is_content_unlocked(self, content_id: str) -> bool:
        """Check if specific content is unlocked."""
        return content_id in self.get_available_content()

    def get_game_modifiers(self) -> dict:
        """Get active game modifiers from consciousness state."""
        bf = self.state.breathing_factor

        return {
            "difficulty": self.state.difficulty_modifier,
            "reward_multiplier": self.state.reward_multiplier,
            "time_scaling": bf,  # Affects timers
            "xp_bonus": (1.0 - bf) * 0.5 if bf < 1.0 else 0,
            "floor": self.state.temple_floor.floor,
            "floor_description": self.state.temple_floor.description,
            "consciousness_level": self.state.level,
            "stage": self.state.stage.value[0],
        }

    def can_perform_action(self, action: str, category: str = "GAME") -> tuple[bool, str]:
        """Check if action is permitted by consciousness state."""
        # Security actions require higher consciousness
        if category == "SECURITY" and self.state.level < 5.0:
            return False, "Requires consciousness level 5.0 or higher"

        # Check content locks
        required_floor = {"boss_battle": 5, "faction_war": 8, "world_event": 9, "transcendence": 10}

        floor_needed = required_floor.get(action, 1)
        if self.state.temple_floor.floor < floor_needed:
            return False, f"Requires Temple Floor {floor_needed}"

        return True, "Action permitted"

    def request_culture_ship_approval(self, action: str, context: dict) -> tuple[bool, str]:
        """Request Culture Ship approval for significant actions."""
        if not self._bridge_available or not self._bridge:
            # Auto-approve when bridge unavailable
            return True, "Auto-approved (bridge offline)"

        try:
            approval = self._bridge.request_ship_approval(action, context)
            return approval.approved, approval.reasoning
        except Exception as e:
            logger.warning(f"Culture Ship approval failed: {e}")
            return True, f"Auto-approved (error: {e})"

    def get_consciousness_status(self) -> dict:
        """Get comprehensive consciousness status."""
        return {
            "level": self.state.level,
            "stage": self.state.stage.value[0],
            "breathing_factor": self.state.breathing_factor,
            "temple_floor": self.state.temple_floor.floor,
            "temple_description": self.state.temple_floor.description,
            "consciousness_points": self.state.consciousness_points,
            "next_floor_at": self._get_next_floor_cp(),
            "unlocked_content": self.get_available_content(),
            "modifiers": self.get_game_modifiers(),
            "bridge_connected": self._bridge_available,
            "last_sync": self.state.last_sync.isoformat(),
        }

    def _get_next_floor_cp(self) -> int | None:
        """Get CP required for next floor."""
        current = self.state.temple_floor.floor
        if current >= 10:
            return None
        for tf in TempleFloor:
            if tf.floor == current + 1:
                return tf.cp_required
        return None

    def apply_breathing_to_timer(self, base_seconds: float) -> float:
        """Apply breathing factor to a timer duration."""
        return base_seconds * self.state.breathing_factor

    def get_cp_event_history(self, limit: int = 10) -> list[dict]:
        """Get recent CP earning events."""
        return [
            {
                "type": e.event_type,
                "cp": e.cp_earned,
                "description": e.description,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self.event_log[-limit:]
        ]


# === Module-level convenience ===

_bridge: ConsciousnessGameBridge | None = None


def get_consciousness_bridge() -> ConsciousnessGameBridge:
    """Get or create consciousness bridge."""
    global _bridge
    if _bridge is None:
        _bridge = ConsciousnessGameBridge()
    return _bridge


def sync_consciousness() -> dict:
    """Sync and return consciousness state."""
    bridge = get_consciousness_bridge()
    bridge.sync_consciousness()
    return bridge.get_consciousness_status()


def award_cp(activity: str, xp: int = 0) -> int:
    """Award consciousness points."""
    return get_consciousness_bridge().award_consciousness_points(activity, xp)


def get_modifiers() -> dict:
    """Get current game modifiers."""
    return get_consciousness_bridge().get_game_modifiers()


if __name__ == "__main__":
    print("Consciousness Game Integration Demo")
    print("=" * 40)

    bridge = ConsciousnessGameBridge()

    # Show status
    status = bridge.get_consciousness_status()
    print("\n--- Consciousness State ---")
    print(f"Level: {status['level']}")
    print(f"Stage: {status['stage']}")
    print(f"Breathing: {status['breathing_factor']:.2f}x")
    print(f"Temple Floor: {status['temple_floor']} ({status['temple_description']})")
    print(f"CP: {status['consciousness_points']}")
    print(f"Bridge: {'Connected' if status['bridge_connected'] else 'Local mode'}")

    # Award some CP
    print("\n--- Awarding CP ---")
    cp = bridge.award_consciousness_points("quest_complete", 200)
    print(f"Quest complete (+200 XP): +{cp} CP")

    cp = bridge.award_consciousness_points("achievement_unlocked")
    print(f"Achievement unlocked: +{cp} CP")

    cp = bridge.award_consciousness_points("boss_defeated", 500)
    print(f"Boss defeated (+500 XP): +{cp} CP")

    # Show updated status
    new_status = bridge.get_consciousness_status()
    print(f"\nTotal CP: {new_status['consciousness_points']}")
    print(f"Temple Floor: {new_status['temple_floor']}")

    # Show modifiers
    print("\n--- Game Modifiers ---")
    mods = bridge.get_game_modifiers()
    for key, value in mods.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # Show unlocked content
    print("\n--- Unlocked Content ---")
    for content in bridge.get_available_content():
        print(f"  ✓ {content}")

    print("\n✅ Consciousness integration ready!")
