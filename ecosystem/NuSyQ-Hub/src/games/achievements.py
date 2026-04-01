"""Achievement and Leaderboard System — Track player achievements and rankings.

Provides persistent achievement tracking, unlock conditions, and local leaderboards
for NuSyQ game mechanics.

Zeta33: Implement leaderboard and achievement system.

OmniTag: {
    "purpose": "achievements_leaderboard",
    "tags": ["Games", "Achievements", "Leaderboard", "Gamification"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

ACHIEVEMENTS_FILE = Path("state/game_saves/achievements.json")
LEADERBOARD_FILE = Path("state/game_saves/leaderboard.json")


@dataclass
class Achievement:
    """Definition of an unlockable achievement."""

    id: str
    name: str
    description: str
    icon: str = "🏆"
    points: int = 10
    hidden: bool = False
    category: str = "general"
    condition: str | None = None  # Condition description


@dataclass
class UnlockedAchievement:
    """Record of an unlocked achievement."""

    achievement_id: str
    unlocked_at: str
    player_id: str = "default"


@dataclass
class LeaderboardEntry:
    """Entry in the leaderboard."""

    player_id: str
    player_name: str
    score: int
    category: str
    recorded_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# Core achievement definitions
ACHIEVEMENTS: dict[str, Achievement] = {
    # Quest achievements
    "first_quest": Achievement(
        id="first_quest",
        name="First Steps",
        description="Complete your first quest",
        icon="👣",
        points=10,
        category="quests",
    ),
    "quest_master_10": Achievement(
        id="quest_master_10",
        name="Quest Enthusiast",
        description="Complete 10 quests",
        icon="📜",
        points=25,
        category="quests",
    ),
    "quest_master_50": Achievement(
        id="quest_master_50",
        name="Quest Master",
        description="Complete 50 quests",
        icon="🎖️",
        points=100,
        category="quests",
    ),
    # Hacking achievements
    "first_hack": Achievement(
        id="first_hack",
        name="Script Kiddie",
        description="Complete your first hacking quest",
        icon="💻",
        points=15,
        category="hacking",
    ),
    "elite_hacker": Achievement(
        id="elite_hacker",
        name="Elite Hacker",
        description="Complete all hacking quests",
        icon="🔓",
        points=200,
        category="hacking",
    ),
    # XP achievements
    "xp_100": Achievement(
        id="xp_100",
        name="Getting Started",
        description="Earn 100 XP",
        icon="⭐",
        points=10,
        category="progression",
    ),
    "xp_1000": Achievement(
        id="xp_1000",
        name="Rising Star",
        description="Earn 1,000 XP",
        icon="🌟",
        points=50,
        category="progression",
    ),
    "xp_10000": Achievement(
        id="xp_10000",
        name="Veteran",
        description="Earn 10,000 XP",
        icon="💫",
        points=150,
        category="progression",
    ),
    # Skill achievements
    "first_skill": Achievement(
        id="first_skill",
        name="Skill Unlocked",
        description="Unlock your first skill",
        icon="🔧",
        points=10,
        category="skills",
    ),
    "skill_master": Achievement(
        id="skill_master",
        name="Jack of All Trades",
        description="Unlock 10 different skills",
        icon="🛠️",
        points=75,
        category="skills",
    ),
    # Hidden achievements
    "speed_demon": Achievement(
        id="speed_demon",
        name="Speed Demon",
        description="Complete a quest in under 10 seconds",
        icon="⚡",
        points=50,
        hidden=True,
        category="special",
    ),
    "night_owl": Achievement(
        id="night_owl",
        name="Night Owl",
        description="Play between midnight and 4 AM",
        icon="🦉",
        points=25,
        hidden=True,
        category="special",
    ),
}


class AchievementManager:
    """Manages achievement tracking and unlocking."""

    def __init__(self, achievements_file: Path | None = None):
        """Initialize the achievement manager.

        Args:
            achievements_file: Path to store unlocked achievements.
        """
        self.file = achievements_file or ACHIEVEMENTS_FILE
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self._unlocked: dict[str, UnlockedAchievement] = {}
        self._load()

    def _load(self) -> None:
        """Load unlocked achievements from disk."""
        if self.file.exists():
            try:
                data = json.loads(self.file.read_text())
                for entry in data.get("unlocked", []):
                    ua = UnlockedAchievement(
                        achievement_id=entry["achievement_id"],
                        unlocked_at=entry["unlocked_at"],
                        player_id=entry.get("player_id", "default"),
                    )
                    self._unlocked[ua.achievement_id] = ua
            except Exception as e:
                logger.warning(f"Failed to load achievements: {e}")

    def _save(self) -> None:
        """Save unlocked achievements to disk."""
        try:
            data = {"unlocked": [asdict(ua) for ua in self._unlocked.values()]}
            self.file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save achievements: {e}")

    def unlock(self, achievement_id: str, player_id: str = "default") -> Achievement | None:
        """Unlock an achievement.

        Args:
            achievement_id: ID of the achievement to unlock.
            player_id: Player who unlocked it.

        Returns:
            The Achievement if newly unlocked, None if already unlocked or invalid.
        """
        if achievement_id in self._unlocked:
            return None

        achievement = ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            logger.warning(f"Unknown achievement: {achievement_id}")
            return None

        ua = UnlockedAchievement(
            achievement_id=achievement_id,
            unlocked_at=datetime.now(UTC).isoformat(),
            player_id=player_id,
        )
        self._unlocked[achievement_id] = ua
        self._save()
        logger.info(f"🏆 Achievement unlocked: {achievement.name}")
        return achievement

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if an achievement is unlocked."""
        return achievement_id in self._unlocked

    def get_unlocked(self) -> list[Achievement]:
        """Get all unlocked achievements."""
        return [ACHIEVEMENTS[aid] for aid in self._unlocked if aid in ACHIEVEMENTS]

    def get_locked(self, include_hidden: bool = False) -> list[Achievement]:
        """Get all locked achievements."""
        locked = []
        for aid, ach in ACHIEVEMENTS.items():
            if aid not in self._unlocked and (include_hidden or not ach.hidden):
                locked.append(ach)
        return locked

    def get_total_points(self) -> int:
        """Get total achievement points earned."""
        return sum(ACHIEVEMENTS[aid].points for aid in self._unlocked if aid in ACHIEVEMENTS)

    def get_completion_percentage(self) -> float:
        """Get percentage of achievements completed."""
        if not ACHIEVEMENTS:
            return 100.0
        return (len(self._unlocked) / len(ACHIEVEMENTS)) * 100


class LeaderboardManager:
    """Manages local leaderboards."""

    def __init__(self, leaderboard_file: Path | None = None):
        """Initialize the leaderboard manager.

        Args:
            leaderboard_file: Path to store leaderboard data.
        """
        self.file = leaderboard_file or LEADERBOARD_FILE
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, list[LeaderboardEntry]] = {}
        self._load()

    def _load(self) -> None:
        """Load leaderboard from disk."""
        if self.file.exists():
            try:
                data = json.loads(self.file.read_text())
                for category, entries in data.items():
                    self._entries[category] = [
                        LeaderboardEntry(
                            player_id=e["player_id"],
                            player_name=e["player_name"],
                            score=e["score"],
                            category=category,
                            recorded_at=e.get("recorded_at", ""),
                        )
                        for e in entries
                    ]
            except Exception as e:
                logger.warning(f"Failed to load leaderboard: {e}")

    def _save(self) -> None:
        """Save leaderboard to disk."""
        try:
            data = {cat: [asdict(e) for e in entries] for cat, entries in self._entries.items()}
            self.file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save leaderboard: {e}")

    def submit_score(
        self,
        player_id: str,
        player_name: str,
        score: int,
        category: str = "general",
    ) -> int:
        """Submit a score to the leaderboard.

        Args:
            player_id: Unique player identifier.
            player_name: Display name.
            score: Score achieved.
            category: Leaderboard category.

        Returns:
            Rank achieved (1 = first place).
        """
        if category not in self._entries:
            self._entries[category] = []

        entry = LeaderboardEntry(
            player_id=player_id,
            player_name=player_name,
            score=score,
            category=category,
        )

        # Update or add entry
        existing = next((e for e in self._entries[category] if e.player_id == player_id), None)
        if existing:
            if score > existing.score:
                existing.score = score
                existing.recorded_at = entry.recorded_at
        else:
            self._entries[category].append(entry)

        # Sort by score descending
        self._entries[category].sort(key=lambda e: e.score, reverse=True)

        # Keep top 100
        self._entries[category] = self._entries[category][:100]

        self._save()

        # Find rank
        for i, e in enumerate(self._entries[category]):
            if e.player_id == player_id:
                return i + 1
        return len(self._entries[category])

    def get_top(self, category: str = "general", limit: int = 10) -> list[LeaderboardEntry]:
        """Get top entries for a category."""
        return self._entries.get(category, [])[:limit]

    def get_rank(self, player_id: str, category: str = "general") -> int | None:
        """Get a player's rank in a category."""
        entries = self._entries.get(category, [])
        for i, e in enumerate(entries):
            if e.player_id == player_id:
                return i + 1
        return None

    def get_categories(self) -> list[str]:
        """Get all leaderboard categories."""
        return list(self._entries.keys())


# Module-level instances
_achievement_manager: AchievementManager | None = None
_leaderboard_manager: LeaderboardManager | None = None


def get_achievements() -> AchievementManager:
    """Get the global achievement manager."""
    global _achievement_manager
    if _achievement_manager is None:
        _achievement_manager = AchievementManager()
    return _achievement_manager


def get_leaderboard() -> LeaderboardManager:
    """Get the global leaderboard manager."""
    global _leaderboard_manager
    if _leaderboard_manager is None:
        _leaderboard_manager = LeaderboardManager()
    return _leaderboard_manager


# Convenience functions
def unlock_achievement(achievement_id: str) -> Achievement | None:
    """Unlock an achievement."""
    return get_achievements().unlock(achievement_id)


def submit_score(player_name: str, score: int, category: str = "general") -> int:
    """Submit a score to the leaderboard."""
    return get_leaderboard().submit_score(
        player_id="default",
        player_name=player_name,
        score=score,
        category=category,
    )


def check_quest_achievements(completed_count: int) -> list[Achievement]:
    """Check and unlock quest-related achievements."""
    unlocked = []
    mgr = get_achievements()

    if completed_count >= 1 and (ach := mgr.unlock("first_quest")):
        unlocked.append(ach)
    if completed_count >= 10 and (ach := mgr.unlock("quest_master_10")):
        unlocked.append(ach)
    if completed_count >= 50 and (ach := mgr.unlock("quest_master_50")):
        unlocked.append(ach)

    return unlocked


def check_xp_achievements(total_xp: int) -> list[Achievement]:
    """Check and unlock XP-related achievements."""
    unlocked = []
    mgr = get_achievements()

    if total_xp >= 100 and (ach := mgr.unlock("xp_100")):
        unlocked.append(ach)
    if total_xp >= 1000 and (ach := mgr.unlock("xp_1000")):
        unlocked.append(ach)
    if total_xp >= 10000 and (ach := mgr.unlock("xp_10000")):
        unlocked.append(ach)

    return unlocked


logger.info("Achievement and leaderboard system loaded")
