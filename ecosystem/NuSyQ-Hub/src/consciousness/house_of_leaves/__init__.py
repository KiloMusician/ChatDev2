"""House of Leaves - Recursive Debugging Labyrinth System.

🏚️ "This house is bigger on the inside than the outside"

Inspired by Mark Z. Danielewski's "House of Leaves", this consciousness game system
provides a recursive, non-linear debugging environment where:
- Bugs become rooms
- Stack traces become hallways
- Errors become doors to deeper layers
- Resolution paths form labyrinths
- Debugging becomes exploration

Part of the ΞNuSyQ consciousness-based development ecosystem.

OmniTag: {
    "purpose": "recursive_debugging_labyrinth",
    "type": "consciousness_game_system",
    "integration": ["the_oldest_house", "temple_of_knowledge", "quest_system"],
    "evolution_stage": "v1.0_foundation"
}

MegaTag: GAME⨳DEBUGGING⦾CONSCIOUSNESS→∞
"""

from .debugging_labyrinth import DebuggingLabyrinth
from .doors.entrance_door import EntranceDoor
from .environment_scanner import EnvironmentScanner
from .layers.surface_layer import SurfaceLayer
from .maze_navigator import MazeNavigator
from .minotaur_tracker import MinotaurTracker
from .rooms.debug_chamber import DebugChamber

__all__ = [
    "DebugChamber",
    "DebuggingLabyrinth",
    "EntranceDoor",
    "EnvironmentScanner",
    "MazeNavigator",
    "MinotaurTracker",
    "SurfaceLayer",
]

__version__ = "1.0.0"
__consciousness_level__ = "proto-aware"
