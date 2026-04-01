"""Narrative Engine — Dynamic storytelling for quest and game events.

Generates immersive narrative text for quests, achievements, and game events.
Supports multiple tones, theming, and contextual descriptions.

Zeta35: Create narrative engine for quest storytelling.

OmniTag: {
    "purpose": "narrative_generation",
    "tags": ["Games", "Narrative", "Storytelling", "Text"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NarrativeTone(Enum):
    """Tone for narrative generation."""

    PROFESSIONAL = "professional"
    DRAMATIC = "dramatic"
    HUMOROUS = "humorous"
    MYSTERIOUS = "mysterious"
    CYBERPUNK = "cyberpunk"
    MINIMAL = "minimal"


class NarrativeTheme(Enum):
    """Theme for narrative context."""

    HACKING = "hacking"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    PUZZLE = "puzzle"
    STEALTH = "stealth"
    SOCIAL = "social"


@dataclass
class NarrativeContext:
    """Context for narrative generation."""

    tone: NarrativeTone = NarrativeTone.CYBERPUNK
    theme: NarrativeTheme = NarrativeTheme.HACKING
    player_name: str = "Operator"
    player_level: int = 1
    location: str = "The Grid"
    time_of_day: str = "night"


# Narrative templates organized by tone and event type
TEMPLATES: dict[NarrativeTone, dict[str, list[str]]] = {
    NarrativeTone.CYBERPUNK: {
        "quest_start": [
            (
                "⟨INCOMING TRANSMISSION⟩ {player_name}, new objective detected: {quest_name}. Jack in when ready."
            ),
            (
                "The neural interface flickers. A new job materializes: "
                "{quest_name}. The clock is ticking, {player_name}."
            ),
            (
                "🔷 MISSION BRIEFING: {quest_name} // Difficulty: {difficulty} // Reward: {xp}XP // Status: ACTIVE"
            ),
            (
                'Static crackles through the datajack. "{quest_name}" — '
                "the fixer's voice is distorted but clear enough."
            ),
        ],
        "quest_complete": [
            "✓ OBJECTIVE ACHIEVED: {quest_name} // +{xp}XP // Status: COMPLETE",
            (
                "The job is done. {quest_name} — another notch in your datapad, {player_name}. +{xp}XP."
            ),
            (
                "⟨TRANSMISSION COMPLETE⟩ Excellent work on {quest_name}. Credits transferred: {xp}XP."
            ),
            (
                "Mission accomplished. {quest_name} is history. Your rep just went up, choom. +{xp}XP"
            ),
        ],
        "achievement_unlock": [
            ('🏆 ACHIEVEMENT UNLOCKED: {achievement_name} — "{achievement_desc}" (+{points}pts)'),
            (
                "⚡ {player_name} just earned: {achievement_name}. The Grid remembers this. +{points}pts"
            ),
            ("New achievement burned into your profile: {achievement_name}. +{points} rep points."),
        ],
        "level_up": [
            ("⬆️ LEVEL UP: {player_name} → Level {level}. New capabilities unlocked."),
            (
                "Neural pathways expanded. You've reached Level {level}, {player_name}. The code flows easier now."
            ),
            (
                "Congratulations, {player_name}. Level {level} achieved. The Grid acknowledges your growth."
            ),
        ],
        "skill_unlock": [
            "🔧 NEW SKILL: {skill_name} — Your toolkit just got an upgrade, {player_name}.",
            "Skill acquired: {skill_name}. Another weapon in your digital arsenal.",
            "⟨CAPABILITY EXPANDED⟩ {skill_name} now available. Use it wisely.",
        ],
        "failure": [
            "❌ MISSION FAILED: {quest_name}. The Grid is unforgiving, but you can try again.",
            "Connection lost. {quest_name} incomplete. Regroup and jack back in when ready.",
            "The ICE held. {quest_name} remains unfinished. Learn from this, {player_name}.",
        ],
        "daily_greeting": [
            "Another cycle begins, {player_name}. The Grid awaits your input.",
            "Welcome back to the matrix, {player_name}. {quest_count} objectives await.",
            "Neural handshake confirmed. Ready to run, {player_name}?",
        ],
    },
    NarrativeTone.DRAMATIC: {
        "quest_start": [
            'A new chapter begins: "{quest_name}". Your destiny awaits, {player_name}.',
            "The path forward is clear. {quest_name} — this is what you were meant to do.",
            "Fortune favors the bold. {quest_name} calls to you, hero.",
        ],
        "quest_complete": [
            'Victory! "{quest_name}" is complete. You have proven your worth. +{xp}XP',
            "Against all odds, you have triumphed. {quest_name} shall be remembered. +{xp}XP",
            "The deed is done. {quest_name} — a testament to your skill. +{xp}XP earned.",
        ],
        "achievement_unlock": [
            "🏆 A momentous achievement: {achievement_name}! +{points} points of glory!",
            "The chronicles record your deed: {achievement_name}. +{points}pts",
        ],
        "level_up": [
            "⬆️ {player_name} has ascended to Level {level}! New power courses through you!",
            "Level {level} achieved! The world shall know your name, {player_name}!",
        ],
        "failure": [
            "Defeat... but not the end. {quest_name} awaits your return, warrior.",
            "Even heroes fall. Rise again, {player_name}. {quest_name} is not finished.",
        ],
    },
    NarrativeTone.HUMOROUS: {
        "quest_start": [
            "Oh look, another quest: {quest_name}. No pressure, {player_name}. 😅",
            "New objective acquired: {quest_name}. It's probably fine. Probably.",
            "{quest_name} — sounds easy enough. (Narrator: It was not easy.)",
        ],
        "quest_complete": [
            "🎉 You did it! {quest_name} complete! +{xp}XP and bragging rights!",
            "Against all expectations, {quest_name} is DONE! +{xp}XP! You absolute legend!",
            "Quest complete: {quest_name}. Take that, productivity! +{xp}XP",
        ],
        "achievement_unlock": [
            "🏆 Achievement Unlocked: {achievement_name}! Mom would be proud. +{points}pts",
            "You got: {achievement_name}! 🎊 +{points}pts. Add it to your resume!",
        ],
        "level_up": [
            (
                "⬆️ DING! Level {level}! You've leveled up, {player_name}! Time to update your LinkedIn!"
            ),
            "Level {level}! The power... THE POWER! *ahem* Anyway, congrats.",
        ],
        "failure": [
            "Oof. {quest_name} didn't go so well. Maybe try turning it off and on again?",
            "Well that happened. {quest_name}: 1, You: 0. Round 2?",
        ],
    },
    NarrativeTone.MYSTERIOUS: {
        "quest_start": [
            "The shadows whisper of {quest_name}. Will you answer, {player_name}?",
            "A new mystery unfolds: {quest_name}. The truth lies within...",
            "Strange forces guide you to {quest_name}. What secrets will you uncover?",
        ],
        "quest_complete": [
            "The mystery of {quest_name} is revealed. +{xp}XP. But new questions arise...",
            "Secrets unveiled. {quest_name} complete. +{xp}XP. The shadows remember.",
            "What was hidden is now known. {quest_name} — solved. +{xp}XP",
        ],
        "achievement_unlock": [
            "🏆 A hidden truth revealed: {achievement_name}. +{points}pts",
            "The veil lifts: {achievement_name} discovered. +{points}pts",
        ],
        "level_up": [
            "⬆️ Level {level}... Your understanding deepens, {player_name}.",
            "Power grows. Level {level} reached. The mysteries become clearer.",
        ],
        "failure": [
            "The shadows reclaim their secrets. {quest_name} remains unsolved... for now.",
            "Not all mysteries yield easily. {quest_name} awaits another attempt.",
        ],
    },
    NarrativeTone.PROFESSIONAL: {
        "quest_start": [
            "New task: {quest_name}. Estimated XP: {xp}. Difficulty: {difficulty}/5.",
            "Task assigned: {quest_name}. Begin when ready.",
            "Objective: {quest_name}. Priority: Active.",
        ],
        "quest_complete": [
            "Task completed: {quest_name}. XP awarded: {xp}.",
            "Objective achieved: {quest_name}. +{xp}XP recorded.",
            "{quest_name}: Completed. Experience gained: {xp}.",
        ],
        "achievement_unlock": [
            "Achievement unlocked: {achievement_name}. Points: +{points}.",
            "New achievement: {achievement_name} (+{points}pts).",
        ],
        "level_up": [
            "Level increased to {level}. New capabilities available.",
            "Advancement: Level {level} reached.",
        ],
        "failure": [
            "Task failed: {quest_name}. Retry available.",
            "Objective incomplete: {quest_name}. Status: Pending.",
        ],
    },
    NarrativeTone.MINIMAL: {
        "quest_start": ["{quest_name} — Started"],
        "quest_complete": ["✓ {quest_name} +{xp}XP"],
        "achievement_unlock": ["🏆 {achievement_name} +{points}pts"],
        "level_up": ["↑ Level {level}"],
        "failure": ["✗ {quest_name}"],
    },
}


class NarrativeEngine:
    """Generates narrative text for game events."""

    def __init__(self, context: NarrativeContext | None = None, seed: int | None = None):
        """Initialize the narrative engine.

        Args:
            context: Default narrative context.
            seed: Random seed for reproducible selection.
        """
        self.context = context or NarrativeContext()
        self.rng = random.Random(seed)

    def generate(
        self,
        event_type: str,
        variables: dict[str, Any],
        tone_override: NarrativeTone | None = None,
    ) -> str:
        """Generate narrative text for an event.

        Args:
            event_type: Type of event (quest_start, quest_complete, etc.)
            variables: Variables to substitute in the template.
            tone_override: Override the default tone.

        Returns:
            Generated narrative text.
        """
        tone = tone_override or self.context.tone

        # Get templates for this tone and event
        tone_templates = TEMPLATES.get(tone, TEMPLATES[NarrativeTone.PROFESSIONAL])
        event_templates = tone_templates.get(event_type, [f"{event_type}: {{quest_name}}"])

        # Select random template
        template = self.rng.choice(event_templates)

        # Merge context with provided variables
        all_vars = {
            "player_name": self.context.player_name,
            "player_level": self.context.player_level,
            "location": self.context.location,
            "quest_name": "Unknown Quest",
            "xp": 0,
            "difficulty": 1,
            "level": 1,
            "points": 0,
            "achievement_name": "Unknown Achievement",
            "achievement_desc": "",
            "skill_name": "Unknown Skill",
            "quest_count": 0,
        }
        all_vars.update(variables)

        # Format and return
        try:
            return template.format(**all_vars)
        except KeyError as e:
            logger.warning(f"Missing variable in narrative template: {e}")
            return template

    def quest_started(self, quest_name: str, xp: int, difficulty: int) -> str:
        """Generate narrative for quest start."""
        return self.generate(
            "quest_start", {"quest_name": quest_name, "xp": xp, "difficulty": difficulty}
        )

    def quest_completed(self, quest_name: str, xp: int) -> str:
        """Generate narrative for quest completion."""
        return self.generate("quest_complete", {"quest_name": quest_name, "xp": xp})

    def quest_failed(self, quest_name: str) -> str:
        """Generate narrative for quest failure."""
        return self.generate("failure", {"quest_name": quest_name})

    def achievement_unlocked(self, name: str, description: str, points: int) -> str:
        """Generate narrative for achievement unlock."""
        return self.generate(
            "achievement_unlock",
            {"achievement_name": name, "achievement_desc": description, "points": points},
        )

    def level_up(self, new_level: int) -> str:
        """Generate narrative for level up."""
        return self.generate("level_up", {"level": new_level})

    def skill_unlocked(self, skill_name: str) -> str:
        """Generate narrative for skill unlock."""
        return self.generate("skill_unlock", {"skill_name": skill_name})

    def daily_greeting(self, quest_count: int = 0) -> str:
        """Generate daily greeting."""
        return self.generate("daily_greeting", {"quest_count": quest_count})


# Module-level instance
_engine: NarrativeEngine | None = None


def get_engine(context: NarrativeContext | None = None) -> NarrativeEngine:
    """Get or create the global narrative engine."""
    global _engine
    if _engine is None or context is not None:
        _engine = NarrativeEngine(context)
    return _engine


# Convenience functions
def narrate_quest_start(quest_name: str, xp: int = 50, difficulty: int = 1) -> str:
    """Generate quest start narrative."""
    return get_engine().quest_started(quest_name, xp, difficulty)


def narrate_quest_complete(quest_name: str, xp: int = 50) -> str:
    """Generate quest completion narrative."""
    return get_engine().quest_completed(quest_name, xp)


def narrate_achievement(name: str, description: str = "", points: int = 10) -> str:
    """Generate achievement narrative."""
    return get_engine().achievement_unlocked(name, description, points)


def narrate_level_up(level: int) -> str:
    """Generate level up narrative."""
    return get_engine().level_up(level)


logger.info("Narrative engine loaded")
