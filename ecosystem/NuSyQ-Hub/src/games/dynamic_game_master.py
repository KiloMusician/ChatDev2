"""Dynamic Game Master - Orchestrates AI-driven gameplay.

Provides a unified game master that:
- Manages game sessions
- Adapts difficulty dynamically
- Creates emergent storylines
- Orchestrates NPC interactions
- Generates contextual challenges
- Tracks player progress and patterns
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar

logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """Current phase of the game."""

    TUTORIAL = "tutorial"
    EXPLORATION = "exploration"
    MISSION = "mission"
    BOSS = "boss"
    ENDGAME = "endgame"


class EventType(Enum):
    """Types of dynamic events."""

    RANDOM_ENCOUNTER = "random_encounter"
    STORY_BEAT = "story_beat"
    CHALLENGE = "challenge"
    REWARD = "reward"
    ENVIRONMENT = "environment"
    NPC_INTERACTION = "npc_interaction"


@dataclass
class DynamicEvent:
    """A dynamic game event."""

    event_type: EventType
    title: str
    description: str
    choices: list[str] = field(default_factory=list)
    rewards: dict = field(default_factory=dict)
    consequences: dict = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlayerProfile:
    """Player pattern tracking for adaptive gameplay."""

    player_id: str
    play_style: str = "balanced"  # aggressive, cautious, explorer, completionist
    avg_session_minutes: float = 30.0
    preferred_challenges: list[str] = field(default_factory=lambda: ["puzzle"])
    avoided_challenges: list[str] = field(default_factory=list)
    skill_ratings: dict[str, float] = field(default_factory=dict)
    story_choices: list[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class GameSession:
    """Active game session state."""

    session_id: str
    player_id: str
    started_at: datetime
    phase: GamePhase
    current_objective: str = ""
    active_events: list[DynamicEvent] = field(default_factory=list)
    session_xp: int = 0
    session_score: int = 0
    choices_made: list[str] = field(default_factory=list)


class DynamicGameMaster:
    """AI-powered game master for dynamic gameplay.

    Orchestrates all game systems to create emergent experiences.
    """

    # Story arc templates
    STORY_ARCS: ClassVar[list] = [
        {
            "name": "The Awakening",
            "phases": [
                ("tutorial", "Learn the basics of hacking"),
                ("exploration", "Discover the network"),
                ("mission", "Your first real target"),
                ("boss", "Face the system guardian"),
            ],
            "theme": "growth",
        },
        {
            "name": "Corporate Infiltration",
            "phases": [
                ("exploration", "Gather intelligence"),
                ("mission", "Breach outer defenses"),
                ("mission", "Navigate internal systems"),
                ("boss", "Confront the AI overseer"),
            ],
            "theme": "stealth",
        },
        {
            "name": "The Underground",
            "phases": [
                ("exploration", "Find the hacker collective"),
                ("mission", "Prove your worth"),
                ("mission", "Join the operation"),
                ("boss", "The final heist"),
            ],
            "theme": "alliance",
        },
    ]

    # Random encounter templates
    ENCOUNTERS: ClassVar[dict] = {
        "patrol": {
            "title": "Security Patrol",
            "description": "A routine security scan approaches your position.",
            "choices": ["Hide", "Distract", "Confront"],
            "outcomes": {
                "Hide": {"success_rate": 0.7, "xp": 10, "consequence": "stealth"},
                "Distract": {"success_rate": 0.5, "xp": 20, "consequence": "neutral"},
                "Confront": {"success_rate": 0.3, "xp": 50, "consequence": "combat"},
            },
        },
        "data_cache": {
            "title": "Hidden Data Cache",
            "description": "You've found an encrypted data store.",
            "choices": ["Decrypt", "Clone", "Ignore"],
            "outcomes": {
                "Decrypt": {"success_rate": 0.6, "xp": 30, "consequence": "treasure"},
                "Clone": {"success_rate": 0.9, "xp": 15, "consequence": "neutral"},
                "Ignore": {"success_rate": 1.0, "xp": 0, "consequence": "safe"},
            },
        },
        "friendly_npc": {
            "title": "Mysterious Contact",
            "description": "An anonymous message appears: 'I can help you...'",
            "choices": ["Trust", "Verify", "Ignore"],
            "outcomes": {
                "Trust": {"success_rate": 0.5, "xp": 40, "consequence": "alliance"},
                "Verify": {"success_rate": 0.8, "xp": 20, "consequence": "neutral"},
                "Ignore": {"success_rate": 1.0, "xp": 5, "consequence": "missed"},
            },
        },
        "system_glitch": {
            "title": "System Anomaly",
            "description": "A glitch in the matrix reveals a vulnerability.",
            "choices": ["Exploit", "Report", "Observe"],
            "outcomes": {
                "Exploit": {"success_rate": 0.4, "xp": 60, "consequence": "risky"},
                "Report": {"success_rate": 1.0, "xp": 10, "consequence": "ethical"},
                "Observe": {"success_rate": 1.0, "xp": 15, "consequence": "intel"},
            },
        },
    }

    def __init__(self, player_id: str = "player"):
        """Initialize DynamicGameMaster with player_id."""
        self.player_id = player_id
        self.current_session: GameSession | None = None
        self.player_profile: PlayerProfile | None = None
        self.event_history: list[DynamicEvent] = []
        self.difficulty_modifier: float = 1.0

        # Try to load AI components
        self._ai_available = False
        try:
            from .ai_opponents import \
                AIGameMaster  # type: ignore[import-not-found]

            self.ai = AIGameMaster()
            self._ai_available = True
        except ImportError:
            self.ai = None

    def start_session(self, story_arc: str | None = None) -> GameSession:
        """Start a new game session."""
        # Select or continue story arc
        if story_arc:
            arc = next((a for a in self.STORY_ARCS if a["name"] == story_arc), None)
        else:
            arc = random.choice(self.STORY_ARCS)

        # Initialize session
        self.current_session = GameSession(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            player_id=self.player_id,
            started_at=datetime.now(),
            phase=GamePhase.TUTORIAL,
            current_objective=arc["phases"][0][1] if arc else "Begin your journey",
        )

        # Initialize or load player profile
        self.player_profile = PlayerProfile(player_id=self.player_id)

        logger.info(f"Game session started: {self.current_session.session_id}")
        return self.current_session

    def end_session(self) -> dict:
        """End the current session and return summary."""
        if not self.current_session:
            return {"error": "No active session"}

        duration = (datetime.now() - self.current_session.started_at).total_seconds()

        summary = {
            "session_id": self.current_session.session_id,
            "duration_seconds": duration,
            "xp_earned": self.current_session.session_xp,
            "score": self.current_session.session_score,
            "events_experienced": len(self.event_history),
            "choices_made": len(self.current_session.choices_made),
            "final_phase": self.current_session.phase.value,
        }

        self.current_session = None
        return summary

    def trigger_event(self, event_type: EventType | None = None) -> DynamicEvent:
        """Trigger a dynamic event."""
        if not self.current_session:
            self.current_session = self.start_session()

        # Select event type based on context
        if event_type is None:
            weights = self._get_event_weights()
            event_type = random.choices(list(weights.keys()), weights=list(weights.values()))[0]

        # Generate event
        if event_type == EventType.RANDOM_ENCOUNTER:
            event = self._generate_encounter()
        elif event_type == EventType.CHALLENGE:
            event = self._generate_challenge()
        elif event_type == EventType.NPC_INTERACTION:
            event = self._generate_npc_event()
        elif event_type == EventType.STORY_BEAT:
            event = self._generate_story_beat()
        else:
            event = self._generate_environment_event()

        self.event_history.append(event)
        self.current_session.active_events.append(event)

        return event

    def _get_event_weights(self) -> dict[EventType, float]:
        """Get weighted probabilities for event types."""
        # Base weights
        weights = {
            EventType.RANDOM_ENCOUNTER: 0.3,
            EventType.CHALLENGE: 0.25,
            EventType.NPC_INTERACTION: 0.2,
            EventType.STORY_BEAT: 0.15,
            EventType.ENVIRONMENT: 0.1,
        }

        # Modify based on player profile
        if self.player_profile:
            if self.player_profile.play_style == "explorer":
                weights[EventType.ENVIRONMENT] *= 2
            elif self.player_profile.play_style == "aggressive":
                weights[EventType.CHALLENGE] *= 1.5
                weights[EventType.RANDOM_ENCOUNTER] *= 1.5

        return weights

    def _generate_encounter(self) -> DynamicEvent:
        """Generate a random encounter."""
        encounter_key = random.choice(list(self.ENCOUNTERS.keys()))
        template = self.ENCOUNTERS[encounter_key]

        return DynamicEvent(
            event_type=EventType.RANDOM_ENCOUNTER,
            title=template["title"],
            description=template["description"],
            choices=template["choices"],
            rewards={"xp_potential": max(o["xp"] for o in template["outcomes"].values())},
        )

    def _generate_challenge(self) -> DynamicEvent:
        """Generate a challenge event."""
        # Use AI if available
        if self._ai_available and self.ai:
            from .ai_opponents import \
                Difficulty  # type: ignore[import-not-found]

            diff_level = min(5, int(self.difficulty_modifier * 3))
            challenge = self.ai.generate_challenge(Difficulty(diff_level))

            return DynamicEvent(
                event_type=EventType.CHALLENGE,
                title="Hacking Challenge",
                description=challenge["question"],
                rewards={"xp": challenge["xp_reward"]},
                consequences={"hint": challenge["hint"]},
            )

        # Fallback
        return DynamicEvent(
            event_type=EventType.CHALLENGE,
            title="Code Puzzle",
            description="Decrypt the message: KHOOR (Caesar +3)",
            choices=["HELLO", "WORLD", "HACK"],
            rewards={"xp": 30},
        )

    def _generate_npc_event(self) -> DynamicEvent:
        """Generate an NPC interaction event."""
        npcs = ["Oracle", "Cipher", "Ghost", "Nexus", "SynthEx"]
        npc = random.choice(npcs)

        # Get dialogue if AI available
        dialogue = "Greetings, hacker."
        if self._ai_available and self.ai:
            response = self.ai.get_npc_dialogue(npc, "greeting")
            dialogue = response.text

        return DynamicEvent(
            event_type=EventType.NPC_INTERACTION,
            title=f"Encounter: {npc}",
            description=dialogue,
            choices=["Talk", "Trade", "Challenge", "Leave"],
            rewards={"relationship": npc},
        )

    def _generate_story_beat(self) -> DynamicEvent:
        """Generate a story progression event."""
        phase = self.current_session.phase if self.current_session else GamePhase.EXPLORATION

        beats = {
            GamePhase.TUTORIAL: [
                "Your first successful hack gives you confidence.",
                "The system recognizes your potential.",
                "A message arrives: 'We've been watching you.'",
            ],
            GamePhase.EXPLORATION: [
                "You discover a hidden node in the network.",
                "Patterns emerge in the data streams.",
                "Someone has left breadcrumbs for you to follow.",
            ],
            GamePhase.MISSION: [
                "The target is in sight. Time to move.",
                "Security is tighter than expected.",
                "An unexpected ally provides assistance.",
            ],
            GamePhase.BOSS: [
                "The guardian awakens.",
                "All systems converge against you.",
                "This is what you've been training for.",
            ],
        }

        description = random.choice(beats.get(phase, beats[GamePhase.EXPLORATION]))

        return DynamicEvent(
            event_type=EventType.STORY_BEAT,
            title="Story Development",
            description=description,
            rewards={"story_progress": 1},
        )

    def _generate_environment_event(self) -> DynamicEvent:
        """Generate an environment event."""
        environments = [
            ("Network Storm", "Data packets scatter. Navigation is difficult."),
            ("System Maintenance", "Windows of opportunity appear."),
            ("Power Surge", "Systems flicker. Something has changed."),
            ("Silent Mode", "The network goes quiet. Too quiet."),
            ("Data Rain", "Information flows freely. What will you capture?"),
        ]

        title, desc = random.choice(environments)
        return DynamicEvent(
            event_type=EventType.ENVIRONMENT,
            title=title,
            description=desc,
            rewards={"atmosphere": title},
        )

    def resolve_choice(self, event: DynamicEvent, choice: str) -> dict:
        """Resolve a player's choice for an event."""
        if not self.current_session:
            return {"error": "No active session"}

        result = {
            "choice": choice,
            "success": True,
            "xp_earned": 0,
            "narrative": "",
            "consequences": [],
        }

        # Track choice
        self.current_session.choices_made.append(f"{event.title}:{choice}")

        # Handle based on event type
        if event.event_type == EventType.RANDOM_ENCOUNTER:
            result = self._resolve_encounter(event, choice)
        elif event.event_type == EventType.CHALLENGE:
            result = self._resolve_challenge(event, choice)
        elif event.event_type == EventType.NPC_INTERACTION:
            result = self._resolve_npc_choice(event, choice)
        else:
            result["xp_earned"] = 10
            result["narrative"] = "Your choice shapes the story."

        # Update session
        self.current_session.session_xp += result.get("xp_earned", 0)

        # Remove from active events
        if event in self.current_session.active_events:
            self.current_session.active_events.remove(event)

        return result

    def _resolve_encounter(self, event: DynamicEvent, choice: str) -> dict:
        """Resolve an encounter choice."""
        # Find matching encounter template
        for _key, template in self.ENCOUNTERS.items():
            if template["title"] == event.title and choice in template["outcomes"]:
                outcome = template["outcomes"][choice]
                success = random.random() < outcome["success_rate"]
                status = "Success!" if success else "Partial success..."

                return {
                    "choice": choice,
                    "success": success,
                    "xp_earned": outcome["xp"] if success else outcome["xp"] // 2,
                    "narrative": f"{status} {outcome['consequence']}",
                    "consequences": [outcome["consequence"]],
                }

        # Default resolution
        return {
            "choice": choice,
            "success": True,
            "xp_earned": 15,
            "narrative": "You handled the situation.",
            "consequences": [],
        }

    def _resolve_challenge(self, event: DynamicEvent, answer: str) -> dict:
        """Resolve a challenge answer."""
        # For the fallback challenge (KHOOR -> HELLO)
        correct = answer.upper() == "HELLO"

        xp = event.rewards.get("xp", 30)

        return {
            "choice": answer,
            "success": correct,
            "xp_earned": xp if correct else 5,
            "narrative": "Correct! Access granted." if correct else "Incorrect. Access denied.",
            "consequences": ["challenge_complete" if correct else "challenge_failed"],
        }

    def _resolve_npc_choice(self, event: DynamicEvent, choice: str) -> dict:
        """Resolve an NPC interaction choice."""
        npc = event.rewards.get("relationship", "Unknown")

        narratives = {
            "Talk": f"{npc} shares valuable information with you.",
            "Trade": f"You exchange resources with {npc}.",
            "Challenge": f"{npc} accepts your challenge!",
            "Leave": f"You leave {npc} behind.",
        }

        xp_values = {"Talk": 15, "Trade": 20, "Challenge": 30, "Leave": 5}

        return {
            "choice": choice,
            "success": True,
            "xp_earned": xp_values.get(choice, 10),
            "narrative": narratives.get(choice, "The interaction concludes."),
            "consequences": [f"npc_{choice.lower()}_{npc.lower()}"],
        }

    def advance_phase(self) -> GamePhase | None:
        """Advance to the next game phase."""
        if not self.current_session:
            return None

        phase_order = [
            GamePhase.TUTORIAL,
            GamePhase.EXPLORATION,
            GamePhase.MISSION,
            GamePhase.BOSS,
            GamePhase.ENDGAME,
        ]

        current_idx = phase_order.index(self.current_session.phase)
        if current_idx < len(phase_order) - 1:
            self.current_session.phase = phase_order[current_idx + 1]
            logger.info(f"Phase advanced to: {self.current_session.phase.value}")
            return self.current_session.phase

        return None

    def adjust_difficulty(self, performance: float) -> None:
        """Adjust difficulty based on player performance."""
        # performance: 0.0 (struggling) to 1.0 (excelling)
        if performance > 0.8:
            self.difficulty_modifier = min(2.0, self.difficulty_modifier * 1.1)
        elif performance < 0.4:
            self.difficulty_modifier = max(0.5, self.difficulty_modifier * 0.9)

        logger.debug(f"Difficulty modifier: {self.difficulty_modifier:.2f}")

    def get_session_status(self) -> dict:
        """Get current session status."""
        if not self.current_session:
            return {"active": False}

        return {
            "active": True,
            "session_id": self.current_session.session_id,
            "phase": self.current_session.phase.value,
            "objective": self.current_session.current_objective,
            "xp": self.current_session.session_xp,
            "score": self.current_session.session_score,
            "active_events": len(self.current_session.active_events),
            "difficulty": self.difficulty_modifier,
        }


# === Module-level convenience ===

_game_master: DynamicGameMaster | None = None


def get_game_master(player_id: str = "player") -> DynamicGameMaster:
    """Get or create the dynamic game master."""
    global _game_master
    if _game_master is None or _game_master.player_id != player_id:
        _game_master = DynamicGameMaster(player_id)
    return _game_master


def start_game(player_id: str = "player") -> dict:
    """Start a new game session."""
    gm = get_game_master(player_id)
    session = gm.start_session()
    return {
        "session_id": session.session_id,
        "phase": session.phase.value,
        "objective": session.current_objective,
    }


def trigger_event() -> dict:
    """Trigger a random event."""
    gm = get_game_master()
    event = gm.trigger_event()
    return {
        "type": event.event_type.value,
        "title": event.title,
        "description": event.description,
        "choices": event.choices,
    }


def make_choice(event_title: str, choice: str) -> dict:
    """Make a choice for an event."""
    gm = get_game_master()
    # Find event by title
    for event in gm.event_history:
        if event.title == event_title:
            return gm.resolve_choice(event, choice)
    return {"error": f"Event not found: {event_title}"}


if __name__ == "__main__":
    print("Dynamic Game Master Demo")
    print("=" * 40)

    gm = DynamicGameMaster("TestPlayer")

    # Start session
    session = gm.start_session()
    print(f"\nSession: {session.session_id}")
    print(f"Phase: {session.phase.value}")
    print(f"Objective: {session.current_objective}")

    # Generate some events
    print("\n--- Events ---")
    for _ in range(3):
        event = gm.trigger_event()
        print(f"\n[{event.event_type.value}] {event.title}")
        print(f"  {event.description}")
        if event.choices:
            print(f"  Choices: {event.choices}")

    # Show status
    status = gm.get_session_status()
    print("\n--- Status ---")
    print(f"XP: {status['xp']}")
    print(f"Active events: {status['active_events']}")
    print(f"Difficulty: {status['difficulty']:.2f}")

    # End session
    summary = gm.end_session()
    print("\n--- Session Summary ---")
    print(f"Duration: {summary['duration_seconds']:.1f}s")
    print(f"Events: {summary['events_experienced']}")

    print("\n✅ Dynamic Game Master ready!")
