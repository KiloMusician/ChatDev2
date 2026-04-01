"""Progression System for CyberTerminal.

Manages skill progression, lessons, and experience points.
Integrates with NuSyQ quest system for XP rewards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SkillLevel(Enum):
    """Player skill level progression."""

    NOVICE = 0
    APPRENTICE = 25
    COMPETENT = 50
    PROFICIENT = 75
    MASTER = 100


@dataclass
class Lesson:
    """A single lesson in the progression system."""

    id: str
    tier: int  # 1-5
    name: str
    description: str
    commands_taught: list[str]
    difficulty: int  # 1-5, increases with tier
    estimated_time_minutes: int
    success_criteria: dict[str, int]  # {command: min_uses}
    xp_reward: int
    prerequisites: list[str] = field(default_factory=list)
    story_segment: str = ""


@dataclass
class PlayerProgress:
    """Player progression state."""

    username: str
    total_xp: int = 0
    current_skill_level: SkillLevel = SkillLevel.NOVICE
    completed_lessons: set[str] = field(default_factory=set)
    current_lesson_id: str | None = None
    lesson_progress: dict[str, int] = field(default_factory=dict)
    lesson_attempts: dict[str, int] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)


class ProgressionSystem:
    """Manages lesson progression and XP system."""

    def __init__(self, difficulty_multiplier: float = 1.0):
        """Initialize progression system.

        Args:
            difficulty_multiplier: XP multiplier based on game difficulty (1.0-5.0)
        """
        self.difficulty_multiplier = difficulty_multiplier
        self.lessons: dict[str, Lesson] = {}
        self.players: dict[str, PlayerProgress] = {}
        self.command_usage_stats: dict[str, dict[str, int]] = {}

        self._initialize_lessons()

    def _initialize_lessons(self) -> None:
        """Initialize all 25 lessons (5 tiers x 5 lessons each)."""
        tier_1 = [
            Lesson(
                id="tier1_lesson1",
                tier=1,
                name="Welcome to the Terminal",
                description="Learn basic terminal concepts and safety",
                commands_taught=["pwd"],
                difficulty=1,
                estimated_time_minutes=3,
                success_criteria={"pwd": 3},
                xp_reward=10,
                story_segment="You boot up a terminal in Neon District...",
            ),
            Lesson(
                id="tier1_lesson2",
                tier=1,
                name="Navigation Basics",
                description="Navigate the filesystem with cd and ls",
                commands_taught=["cd", "ls"],
                difficulty=1,
                estimated_time_minutes=5,
                success_criteria={"cd": 3, "ls": 5},
                xp_reward=15,
                prerequisites=["tier1_lesson1"],
            ),
            Lesson(
                id="tier1_lesson3",
                tier=1,
                name="Viewing Files",
                description="Read file contents with cat",
                commands_taught=["cat"],
                difficulty=1,
                estimated_time_minutes=4,
                success_criteria={"cat": 5},
                xp_reward=15,
                prerequisites=["tier1_lesson2"],
            ),
            Lesson(
                id="tier1_lesson4",
                tier=1,
                name="Text Generation",
                description="Create output with echo",
                commands_taught=["echo"],
                difficulty=1,
                estimated_time_minutes=4,
                success_criteria={"echo": 5},
                xp_reward=15,
                prerequisites=["tier1_lesson1"],
            ),
            Lesson(
                id="tier1_lesson5",
                tier=1,
                name="File Creation",
                description="Create files and directories",
                commands_taught=["touch", "mkdir"],
                difficulty=2,
                estimated_time_minutes=6,
                success_criteria={"touch": 3, "mkdir": 3},
                xp_reward=20,
                prerequisites=["tier1_lesson2"],
            ),
        ]

        tier_2 = [
            Lesson(
                id="tier2_lesson1",
                tier=2,
                name="Permission Fundamentals",
                description="Understand Linux file permissions",
                commands_taught=["chmod"],
                difficulty=2,
                estimated_time_minutes=8,
                success_criteria={"chmod": 5},
                xp_reward=25,
                prerequisites=["tier1_lesson5"],
            ),
            Lesson(
                id="tier2_lesson2",
                tier=2,
                name="File Inspection",
                description="Use ls to inspect file metadata",
                commands_taught=["ls"],
                difficulty=2,
                estimated_time_minutes=7,
                success_criteria={"ls": 10},
                xp_reward=25,
                prerequisites=["tier1_lesson2"],
            ),
            Lesson(
                id="tier2_lesson3",
                tier=2,
                name="Directory Structures",
                description="Organize files and directories",
                commands_taught=["mkdir", "cd"],
                difficulty=2,
                estimated_time_minutes=8,
                success_criteria={"mkdir": 5, "cd": 5},
                xp_reward=25,
                prerequisites=["tier1_lesson5"],
            ),
            Lesson(
                id="tier2_lesson4",
                tier=2,
                name="File Manipulation",
                description="Move and rename files safely",
                commands_taught=["touch"],
                difficulty=2,
                estimated_time_minutes=8,
                success_criteria={"touch": 8},
                xp_reward=25,
                prerequisites=["tier2_lesson1"],
            ),
            Lesson(
                id="tier2_lesson5",
                tier=2,
                name="Automation Intro",
                description="Combine commands for efficiency",
                commands_taught=["echo", "cat"],
                difficulty=3,
                estimated_time_minutes=10,
                success_criteria={"echo": 8, "cat": 8},
                xp_reward=30,
                prerequisites=["tier2_lesson4"],
            ),
        ]

        # Tier 3-5 placeholders (simplified for now)
        tier_3 = [
            Lesson(
                id="tier3_lesson1",
                tier=3,
                name="System Mastery",
                description="Advanced system exploration",
                commands_taught=["pwd", "whoami"],
                difficulty=3,
                estimated_time_minutes=12,
                success_criteria={"pwd": 5, "whoami": 5},
                xp_reward=40,
                prerequisites=["tier2_lesson5"],
            ),
        ]

        # Register all lessons
        for tier_lessons in [tier_1, tier_2, tier_3]:
            for lesson in tier_lessons:
                self.lessons[lesson.id] = lesson

    def register_player(self, username: str) -> PlayerProgress:
        """Register a new player."""
        if username not in self.players:
            self.players[username] = PlayerProgress(username=username)
            self.command_usage_stats[username] = {}
        return self.players[username]

    def get_player(self, username: str) -> PlayerProgress | None:
        """Get player progress."""
        return self.players.get(username)

    def start_lesson(self, username: str, lesson_id: str) -> bool:
        """Start a lesson for a player."""
        player = self.get_player(username)
        if not player:
            return False

        lesson = self.lessons.get(lesson_id)
        if not lesson:
            return False

        # Check prerequisites
        for prereq in lesson.prerequisites:
            if prereq not in player.completed_lessons:
                return False

        player.current_lesson_id = lesson_id
        player.lesson_progress[lesson_id] = 0
        player.lesson_attempts[lesson_id] = player.lesson_attempts.get(lesson_id, 0) + 1

        return True

    def record_command_usage(self, username: str, command: str) -> None:
        """Record command usage for a player."""
        if username not in self.command_usage_stats:
            self.command_usage_stats[username] = {}

        if command not in self.command_usage_stats[username]:
            self.command_usage_stats[username][command] = 0

        self.command_usage_stats[username][command] += 1

        # Update current lesson progress
        player = self.get_player(username)
        if player and player.current_lesson_id:
            lesson = self.lessons.get(player.current_lesson_id)
            if lesson and command in lesson.commands_taught:
                usage_count = self.command_usage_stats[username].get(command, 0)
                required = lesson.success_criteria.get(command, 0)
                if usage_count > 0:
                    player.lesson_progress[player.current_lesson_id] = min(
                        100, int((usage_count / required) * 100)
                    )

    def check_lesson_completion(self, username: str) -> bool:
        """Check if current lesson is completed."""
        player = self.get_player(username)
        if not player or not player.current_lesson_id:
            return False

        lesson = self.lessons.get(player.current_lesson_id)
        if not lesson:
            return False

        # Check if all success criteria met
        for command, required in lesson.success_criteria.items():
            actual = self.command_usage_stats[username].get(command, 0)
            if actual < required:
                return False

        return True

    def complete_lesson(self, username: str) -> int:
        """Mark lesson as complete and award XP."""
        player = self.get_player(username)
        if not player or not player.current_lesson_id:
            return 0

        lesson = self.lessons.get(player.current_lesson_id)
        if not lesson:
            return 0

        # Award XP with difficulty multiplier
        xp_earned = int(lesson.xp_reward * self.difficulty_multiplier)
        player.total_xp += xp_earned
        player.completed_lessons.add(player.current_lesson_id)

        # Update skill level
        self._update_skill_level(player)

        player.current_lesson_id = None
        return xp_earned

    def _update_skill_level(self, player: PlayerProgress) -> None:
        """Update player skill level based on total XP."""
        for level in SkillLevel:
            if player.total_xp >= level.value:
                player.current_skill_level = level

    def get_lesson(self, lesson_id: str) -> Lesson | None:
        """Get lesson by ID."""
        return self.lessons.get(lesson_id)

    def get_available_lessons(self, username: str) -> list[Lesson]:
        """Get available lessons for a player."""
        player = self.get_player(username)
        if not player:
            return []

        available = []
        for lesson in self.lessons.values():
            # Check if not completed
            if lesson.id in player.completed_lessons:
                continue

            # Check prerequisites
            prereqs_met = all(prereq in player.completed_lessons for prereq in lesson.prerequisites)

            if prereqs_met:
                available.append(lesson)

        return sorted(available, key=lambda lesson: (lesson.tier, lesson.id))

    def get_player_stats(self, username: str) -> dict:
        """Get detailed player statistics."""
        player = self.get_player(username)
        if not player:
            return {}

        return {
            "username": player.username,
            "total_xp": player.total_xp,
            "skill_level": player.current_skill_level.name,
            "lessons_completed": len(player.completed_lessons),
            "total_lessons": len(self.lessons),
            "current_lesson": player.current_lesson_id,
            "command_usage": self.command_usage_stats.get(username, {}),
        }
