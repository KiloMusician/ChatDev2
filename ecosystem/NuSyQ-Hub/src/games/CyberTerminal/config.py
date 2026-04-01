"""CyberTerminal Game Configuration.

Defines game settings, difficulty levels, UI themes, and progression parameters.
"""

from dataclasses import dataclass
from enum import Enum


class DifficultyLevel(Enum):
    """Game difficulty settings."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTER = "master"
    ETHEREAL = "ethereal"  # Ultimate challenge


class TerminalTheme(Enum):
    """Terminal UI themes (cyberpunk aesthetic variants)."""

    NEON_GREEN = "neon_green"  # Classic matrix-style
    SYNTHWAVE = "synthwave"  # 80s-90s aesthetic
    VOID_BLACK = "void_black"  # Dark minimal
    CYBER_PURPLE = "cyber_purple"  # Purple/magenta theme
    HOLOGRAPHIC = "holographic"  # Rainbow glitch effect


@dataclass
class GameConfig:
    """Central game configuration."""

    # Game identity
    game_title: str = "🌐 CYBER TERMINAL 2087"
    version: str = "0.1.0"

    # Display
    theme: TerminalTheme = TerminalTheme.SYNTHWAVE
    terminal_width: int = 100
    terminal_height: int = 40

    # Difficulty
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER

    # Progression
    max_skill_level: int = 100
    lessons_per_tier: int = 5
    xp_per_lesson: int = 25
    xp_multiplier_by_difficulty: dict[DifficultyLevel, float] | None = None

    # Game world
    enable_npc_interactions: bool = True
    enable_network_hacking: bool = False  # Advanced feature
    enable_story_mode: bool = True

    # NuSyQ Integration
    nusyq_enabled: bool = True
    quest_logging: bool = True
    ai_assistance_enabled: bool = True

    # Performance
    command_history_size: int = 100
    save_interval_minutes: int = 5
    enable_debug_mode: bool = False

    def __post_init__(self):
        """Initialize derived configurations."""
        if self.xp_multiplier_by_difficulty is None:
            self.xp_multiplier_by_difficulty = {
                DifficultyLevel.BEGINNER: 1.0,
                DifficultyLevel.INTERMEDIATE: 1.5,
                DifficultyLevel.ADVANCED: 2.0,
                DifficultyLevel.MASTER: 3.0,
                DifficultyLevel.ETHEREAL: 5.0,
            }

    def get_xp_for_lesson(self, difficulty: DifficultyLevel | None = None) -> int:
        """Calculate actual XP for a lesson based on difficulty."""
        difficulty = difficulty or self.difficulty
        multipliers = self.xp_multiplier_by_difficulty or {}
        multiplier = multipliers.get(difficulty, 1.0)
        return int(self.xp_per_lesson * multiplier)


# Default configuration instance
DEFAULT_CONFIG = GameConfig()


# Cyberpunk aesthetic constants
BANNER_ASCII = r"""
   ██████╗██╗   ██╗██████╗ ███████╗██████╗ ████████╗███████╗██████╗ ███╗   ███╗██╗   ██╗
  ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║   ██║
  ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝   ██║   █████╗  ██████╔╝██╔████╔██║██║   ██║
  ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║╚██╗ ██╔╝
  ╚██████╗   ██║   ██████╔╝███████╗██║  ██║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║ ╚████╔╝
   ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═══╝

  🌐 2087 | NEON DISTRICT ACADEMY | LEARN THE SYSTEM OR BECOME IT 🌐
"""

# Progression tier descriptions
PROGRESSION_TIERS = {
    "tier_1_basics": {
        "name": "Tier 1: The Awakening",
        "description": "Learn basic terminal navigation and file operations",
        "skills": ["ls", "cd", "pwd", "cat", "echo", "mkdir"],
        "difficulty": DifficultyLevel.BEGINNER,
    },
    "tier_2_intermediate": {
        "name": "Tier 2: Shadow Operations",
        "description": "Master file manipulation, permissions, and basic scripting",
        "skills": ["chmod", "grep", "find", "sed", "awk", "bash"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
    },
    "tier_3_advanced": {
        "name": "Tier 3: System Mastery",
        "description": "Advanced shell, networking, and system administration",
        "skills": ["ssh", "scp", "netstat", "iptables", "systemctl", "service"],
        "difficulty": DifficultyLevel.ADVANCED,
    },
    "tier_4_master": {
        "name": "Tier 4: The Nexus Protocol",
        "description": "Privilege escalation, advanced scripting, and problem-solving",
        "skills": ["sudo", "kernel_modules", "privilege_escalation", "reverse_shells"],
        "difficulty": DifficultyLevel.MASTER,
    },
    "tier_5_ethereal": {
        "name": "Tier 5: The Infinite Void",
        "description": "Ultimate challenges and integrated system mastery",
        "skills": ["everything", "creativity", "problem_solving", "system_design"],
        "difficulty": DifficultyLevel.ETHEREAL,
    },
}

# Cyberpunk story elements
STORY_ELEMENTS = {
    "protagonist_title": "NetRunner",
    "world_name": "Neon District",
    "year": 2087,
    "setting": "Mega-city corporate network",
    "conflict": "Mega-corporations control all data. You hack the system.",
    "themes": ["freedom", "information", "rebellion", "learning", "mastery"],
}
