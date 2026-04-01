"""CyberTerminal - Cyberpunk Terminal Hacking Simulator.

A cyberpunk-themed educational game simulator that teaches Linux/system administration
skills through progressive challenges. Inspired by BitBurner, Grey Hack, HackNet.

Integrates with NuSyQ ecosystem for quest tracking, learning progression, and AI assistance.

Modules:
    config: Game configuration and constants
    virtual_filesystem: VFS system with directories, files, permissions
    command_system: Command parsing and execution
    progression_system: Skill and lesson progression
    tutorial_engine: Tutorial framework and lesson structure
    core_systems: Core game loop and system management
    game: Main game entry point
"""

__version__ = "0.1.0"
__author__ = "NuSyQ Game Development Team"
__description__ = "Cyberpunk Terminal Hacking Simulator with Educational Progression"

# Core exports
from src.games.CyberTerminal.command_system import (CommandResult,
                                                    CommandStatus,
                                                    CommandSystem)
from src.games.CyberTerminal.config import (DifficultyLevel, GameConfig,
                                            TerminalTheme)
from src.games.CyberTerminal.progression_system import (Lesson, PlayerProgress,
                                                        ProgressionSystem,
                                                        SkillLevel)
from src.games.CyberTerminal.tutorial_engine import (Hint, HintLevel,
                                                     ObjectiveProgress,
                                                     ObjectiveStatus,
                                                     TutorialEngine,
                                                     TutorialObjective)
from src.games.CyberTerminal.virtual_filesystem import (FilePermission,
                                                        UserRole,
                                                        VirtualDirectory,
                                                        VirtualFile,
                                                        VirtualFilesystem)

__all__ = [
    "CommandResult",
    "CommandStatus",
    "CommandSystem",
    "DifficultyLevel",
    "FilePermission",
    "GameConfig",
    "Hint",
    "HintLevel",
    "Lesson",
    "ObjectiveProgress",
    "ObjectiveStatus",
    "PlayerProgress",
    "ProgressionSystem",
    "SkillLevel",
    "TerminalTheme",
    "TutorialEngine",
    "TutorialObjective",
    "UserRole",
    "VirtualDirectory",
    "VirtualFile",
    "VirtualFilesystem",
]
