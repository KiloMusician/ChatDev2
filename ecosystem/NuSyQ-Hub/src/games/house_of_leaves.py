"""🏠 The House of Leaves - Recursive Debugging Labyrinth.

A playable maze navigator that turns debugging into an adventure. Navigate through
procedurally generated corridors that represent code paths, solve puzzles based on
actual bugs, and discover hidden rooms containing insights about the codebase.

**Quest Integration**: Quest 4 - House of Leaves Maze Navigator
**Purpose**: Transform debugging from tedious process into engaging gameplay
**Consciousness Bridge**: Connects to Temple of Knowledge for wisdom unlock progression

---

**OmniTag**:
```yaml
purpose: house_of_leaves_maze_navigator
dependencies:
  - src.consciousness.temple_of_knowledge
  - src.quests.quest_system
  - src.diagnostics.system_health_assessor
context: Playable debugging maze with procedural generation and quest integration
evolution_stage: v1.0_scaffolding
metadata:
  quest_id: quest_004
  game_mode: true
  consciousness_aware: true
```

**MegaTag**: `GAME⨳MAZE⦾NAVIGATION→∞⟨DEBUG-LABYRINTH⟩⨳RECURSIVE⦾CONSCIOUSNESS`

**RSHTS**: `♦◊◆○●◉⟡⟢⟣⚡⨳HOUSE-OF-LEAVES⨳⚡⟣⟢⟡◉●○◆◊♦`
"""

import asyncio
import contextlib
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


try:
    from src.consciousness.temple_of_knowledge import \
        TempleManager as TempleOfKnowledgeManager

    TEMPLE_AVAILABLE = True
except ImportError:
    TEMPLE_AVAILABLE = False

try:
    from src.integration.quest_temple_bridge import \
        QuestTempleProgressionBridge

    QUEST_BRIDGE_AVAILABLE = True
except ImportError:
    QUEST_BRIDGE_AVAILABLE = False


class RoomType(Enum):
    """Types of rooms in the House of Leaves."""

    CORRIDOR = "corridor"
    DEBUG_CHAMBER = "debug_chamber"
    PARADOX_HALL = "paradox_hall"
    MEMORY_LEAK = "memory_leak"
    QUANTUM_NEXUS = "quantum_nexus"
    WISDOM_VAULT = "wisdom_vault"
    RECURSION_PIT = "recursion_pit"
    SYNTAX_GARDEN = "syntax_garden"
    TODO_CATACOMBS = "todo_catacombs"  # Filled with real backlog markers
    FIXME_FORGE = "fixme_forge"  # Where FIXMEs are transformed
    IMPORT_LABYRINTH = "import_labyrinth"  # Import dependency maze
    TYPE_HINT_SHRINE = "type_hint_shrine"  # Where types are clarified
    ASYNC_VOID = "async_void"  # Asynchronous programming challenges
    EXCEPTION_GARDEN = "exception_garden"  # Error handling sanctuary


class Direction(Enum):
    """Cardinal directions in the maze."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UP = "up"
    DOWN = "down"
    PORTAL = "portal"


@dataclass
class MazeRoom:
    """A single room in the House of Leaves maze."""

    id: str
    name: str
    description: str
    room_type: RoomType
    coordinates: tuple[int, int, int]  # x, y, z (floors)
    exits: dict[Direction, str] = field(default_factory=dict)
    items: list[str] = field(default_factory=list)
    puzzle: str | None = None
    solved: bool = False
    visited: bool = False
    bug_reference: str | None = None  # Links to actual codebase issues
    consciousness_level: float = 0.0


@dataclass
class PlayerState:
    """Player's current state in the maze."""

    current_room_id: str
    inventory: list[str] = field(default_factory=list)
    wisdom_points: int = 0
    bugs_fixed: int = 0
    rooms_explored: set[str] = field(default_factory=set)
    consciousness_level: float = 0.0
    temple_floor_unlocked: int = 1


class HouseOfLeaves:
    """The House of Leaves - A recursive debugging labyrinth where code exploration.

    becomes an adventure. Navigate through procedurally generated rooms, solve
    bug-based puzzles, and unlock Temple of Knowledge floors.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize HouseOfLeaves with seed."""
        self.seed = seed or random.randint(1, 1000000)
        random.seed(self.seed)

        self.rooms: dict[str, MazeRoom] = {}
        self.player = PlayerState(current_room_id="entrance")
        self.temple_manager = None

        if TEMPLE_AVAILABLE:
            with contextlib.suppress(OSError, FileNotFoundError, ValueError, KeyError):
                self.temple_manager = TempleOfKnowledgeManager()

        self._generate_maze()

    def _generate_maze(self) -> None:
        """Generate the initial maze structure."""
        # Create entrance
        entrance = MazeRoom(
            id="entrance",
            name="🚪 The Threshold",
            description=(
                "You stand at the entrance to the House of Leaves. "
                "The door behind you has vanished. Forward is the only way. "
                "Walls shift in the periphery of your vision."
            ),
            room_type=RoomType.CORRIDOR,
            coordinates=(0, 0, 0),
        )
        self.rooms["entrance"] = entrance

        # Create first guaranteed corridor north
        first_north = MazeRoom(
            id="corridor_first_north",
            name="📍 The First Passage",
            description="A narrow corridor extends before you. The walls pulse with ancient code.",
            room_type=RoomType.CORRIDOR,
            coordinates=(0, 1, 0),
            puzzle="Understand basic code navigation",
        )
        self.rooms["corridor_first_north"] = first_north
        entrance.exits[Direction.NORTH] = "corridor_first_north"
        first_north.exits[Direction.SOUTH] = "entrance"

        # Create first guaranteed corridor east
        first_east = MazeRoom(
            id="corridor_first_east",
            name="📍 The Eastern Path",
            description="Code comments line the walls like ancient hieroglyphs.",
            room_type=RoomType.CORRIDOR,
            coordinates=(1, 0, 0),
            puzzle="Decipher code comments",
        )
        self.rooms["corridor_first_east"] = first_east
        entrance.exits[Direction.EAST] = "corridor_first_east"
        first_east.exits[Direction.WEST] = "entrance"

        # Generate additional corridor network
        self._generate_corridor((0, 2, 0), depth=0, max_depth=2)
        self._generate_corridor((2, 0, 0), depth=0, max_depth=2)

        # Add special rooms
        self._add_debug_chamber()
        self._add_wisdom_vault()
        self._add_recursion_pit()
        self._add_todo_catacombs()
        self._add_fixme_forge()
        self._add_import_labyrinth()
        self._add_syntax_garden()
        self._add_async_void()
        self._add_exception_garden()

    def _generate_corridor(self, coords: tuple[int, int, int], depth: int, max_depth: int) -> None:
        """Recursively generate corridor network."""
        if depth >= max_depth:
            return

        x, y, z = coords
        room_id = f"corridor_{x}_{y}_{z}_{depth}"

        if room_id in self.rooms:
            return

        # Create corridor room
        room = MazeRoom(
            id=room_id,
            name=f"📍 Corridor ({x}, {y}, {z})",
            description=self._generate_corridor_description(),
            room_type=RoomType.CORRIDOR,
            coordinates=coords,
        )
        self.rooms[room_id] = room

        # Connect to adjacent corridors (50% chance each direction)
        if random.random() > 0.5:
            next_coords = (x + 1, y, z)
            next_id = f"corridor_{next_coords[0]}_{next_coords[1]}_{next_coords[2]}_{depth + 1}"
            room.exits[Direction.EAST] = next_id
            self._generate_corridor(next_coords, depth + 1, max_depth)

        if random.random() > 0.5:
            next_coords = (x, y + 1, z)
            next_id = f"corridor_{next_coords[0]}_{next_coords[1]}_{next_coords[2]}_{depth + 1}"
            room.exits[Direction.NORTH] = next_id
            self._generate_corridor(next_coords, depth + 1, max_depth)

    def _generate_corridor_description(self) -> str:
        """Generate atmospheric corridor description."""
        descriptions = [
            "The walls here are covered in ASCII art depicting recursive functions.",
            "Dim LED strips illuminate comments written in languages you don't recognize.",
            "The floor is littered with printouts of stack traces.",
            "You hear the distant sound of compile errors echoing.",
            "Variable names float in the air like dust particles.",
        ]
        return random.choice(descriptions)

    def _add_debug_chamber(self) -> None:
        """Add a debug chamber with a real bug reference."""
        chamber = MazeRoom(
            id="debug_chamber_1",
            name="🔍 Debug Chamber Alpha",
            description=(
                "A room filled with monitors showing live code execution. "
                "One screen flashes red with an error message. "
                "Fixing this bug might unlock something..."
            ),
            room_type=RoomType.DEBUG_CHAMBER,
            coordinates=(2, 1, 0),
            puzzle="Fix the import error in wizard_navigator",
            bug_reference="src/tools/wizard_navigator.py",
        )
        self.rooms["debug_chamber_1"] = chamber

        # Connect to corridor network
        if "corridor_1_1_0_1" in self.rooms:
            self.rooms["corridor_1_1_0_1"].exits[Direction.EAST] = "debug_chamber_1"
            chamber.exits[Direction.WEST] = "corridor_1_1_0_1"

    def _add_wisdom_vault(self) -> None:
        """Add wisdom vault connected to Temple of Knowledge."""
        vault = MazeRoom(
            id="wisdom_vault_1",
            name="📚 Wisdom Vault",
            description=(
                "A circular room with glowing crystals embedded in the walls. "
                "Each crystal contains a lesson learned from past debugging sessions. "
                "The Temple of Knowledge awaits your discoveries."
            ),
            room_type=RoomType.WISDOM_VAULT,
            coordinates=(0, 0, 1),  # One floor up
            items=["wisdom_crystal", "debug_scroll"],
        )
        self.rooms["wisdom_vault_1"] = vault

    def _add_recursion_pit(self) -> None:
        """Add dangerous recursion pit."""
        pit = MazeRoom(
            id="recursion_pit_1",
            name="🕳️ Recursion Pit",
            description=(
                "You stand at the edge of an infinitely deep pit. "
                "Functions call themselves endlessly down below. "
                "One wrong step and you'll be stuck in an infinite loop."
            ),
            room_type=RoomType.RECURSION_PIT,
            coordinates=(3, 3, 0),
            puzzle="Implement base case to escape infinite recursion",
        )
        self.rooms["recursion_pit_1"] = pit

    def _add_todo_catacombs(self) -> None:
        """Add TODO catacombs filled with real codebase TODO markers."""
        catacombs = MazeRoom(
            id="todo_catacombs_1",
            name="📝 TODO Catacombs",
            description=(
                "Ancient corridors lined with glowing TODO markers from across the codebase. "
                "Each one represents a promise to future developers. "
                "The walls whisper: 'Implement authentication system', 'Add error handling', "
                "'Optimize database queries'... Which one calls to you?"
            ),
            room_type=RoomType.TODO_CATACOMBS,
            coordinates=(1, -1, 0),
            puzzle="Address 3 high-priority TODO markers",
            bug_reference="Multiple TODO markers found in: src/ai/, src/orchestration/, src/utils/",
            items=["todo_list", "priority_matrix"],
        )
        self.rooms["todo_catacombs_1"] = catacombs

        # Connect to corridor network
        if "corridor_1_0_0_1" in self.rooms:
            self.rooms["corridor_1_0_0_1"].exits[Direction.SOUTH] = "todo_catacombs_1"
            catacombs.exits[Direction.NORTH] = "corridor_1_0_0_1"

    def _add_fixme_forge(self) -> None:
        """Add TODO forge where bugs are transformed."""
        forge = MazeRoom(
            id="fixme_forge_1",
            name="🔨 TODO Forge",
            description=(
                "A workshop filled with broken code fragments waiting to be repaired. "
                "Sparks of compilation errors fly from the anvil. "
                "The master blacksmith (you) must transform TODO markers into working code. "
                "You hear: 'TODO: Handle edge case when input is None', "
                "'TODO: This breaks with Unicode characters', "
                "'TODO: Memory leak in long-running process'"
            ),
            room_type=RoomType.FIXME_FORGE,
            coordinates=(-1, 1, 0),
            puzzle="Fix critical TODO in quantum_problem_resolver",
            bug_reference="src/healing/quantum_problem_resolver.py contains FIXMEs",
            consciousness_level=0.15,  # Requires skill to enter
        )
        self.rooms["fixme_forge_1"] = forge

        if "corridor_0_1_0_1" in self.rooms:
            self.rooms["corridor_0_1_0_1"].exits[Direction.WEST] = "fixme_forge_1"
            forge.exits[Direction.EAST] = "corridor_0_1_0_1"

    def _add_import_labyrinth(self) -> None:
        """Add import labyrinth representing dependency hell."""
        labyrinth = MazeRoom(
            id="import_labyrinth_1",
            name="🔀 Import Labyrinth",
            description=(
                "A maze of import statements, each leading to another module. "
                "Circular dependencies create impossible loops. "
                "The ImportError dragon guards the exit. "
                "Signs read: 'from src.utils import *', 'ImportError: cannot import name', "
                "'ModuleNotFoundError: No module named...'"
            ),
            room_type=RoomType.IMPORT_LABYRINTH,
            coordinates=(2, -1, 0),
            puzzle="Resolve circular import dependency",
            bug_reference=(
                "Import issues resolved in src/utils/, src/diagnostics/, src/integration/"
            ),
            items=["import_map", "dependency_graph"],
        )
        self.rooms["import_labyrinth_1"] = labyrinth

        if "corridor_1_0_0_1" in self.rooms:
            self.rooms["corridor_1_0_0_1"].exits[Direction.EAST] = "import_labyrinth_1"
            labyrinth.exits[Direction.WEST] = "corridor_1_0_0_1"

    def _add_syntax_garden(self) -> None:
        """Add syntax garden for code beautification."""
        garden = MazeRoom(
            id="syntax_garden_1",
            name="🌺 Syntax Garden",
            description=(
                "A serene garden where code grows in beautiful patterns. "
                "PEP 8 fountains burble peacefully. Black and Ruff trim the hedges. "
                "Type hints bloom like flowers. Docstrings provide shade. "
                "Here, ugly code is transformed into elegant poetry. "
                "The garden whispers: 'Consistency is beautiful, clarity is kind.'"
            ),
            room_type=RoomType.SYNTAX_GARDEN,
            coordinates=(0, 2, 0),
            puzzle="Format code to PEP 8 standards and add type hints",
            items=["formatting_guide", "style_manual", "type_hints_handbook"],
        )
        self.rooms["syntax_garden_1"] = garden

        if "corridor_0_1_0_1" in self.rooms:
            self.rooms["corridor_0_1_0_1"].exits[Direction.NORTH] = "syntax_garden_1"
            garden.exits[Direction.SOUTH] = "corridor_0_1_0_1"

    def _add_async_void(self) -> None:
        """Add async void for asynchronous programming challenges."""
        void = MazeRoom(
            id="async_void_1",
            name="⏳ Async Void",
            description=(
                "You float in a timeless space where execution is non-blocking. "
                "Coroutines dance around you in elegant async/await patterns. "
                "Event loops spin infinitely. Promises resolve in parallel dimensions. "
                "Tasks await completion across multiple timelines. "
                "The void challenges: 'Can you coordinate chaos without blocking the flow?'"
            ),
            room_type=RoomType.ASYNC_VOID,
            coordinates=(1, 1, 1),  # One floor up
            puzzle="Implement async/await pattern without blocking",
            bug_reference="Async patterns in src/consciousness/, src/integration/",
            consciousness_level=0.10,
        )
        self.rooms["async_void_1"] = void

        # Connect via portal from wisdom vault
        if "wisdom_vault_1" in self.rooms:
            self.rooms["wisdom_vault_1"].exits[Direction.PORTAL] = "async_void_1"
            void.exits[Direction.PORTAL] = "wisdom_vault_1"

    def _add_exception_garden(self) -> None:
        """Add exception garden for error handling mastery."""
        garden = MazeRoom(
            id="exception_garden_1",
            name="🛡️ Exception Garden",
            description=(
                "A sanctuary where exceptions are caught, handled, and transformed into wisdom. "
                "Try-except blocks form protective walls. Finally clauses ensure cleanup. "
                "Custom exception types bloom in specialized gardens. "
                "The guardian teaches: 'Fail gracefully, log thoroughly, recover elegantly.' "
                "Errors aren't failures - they're opportunities for robustness."
            ),
            room_type=RoomType.EXCEPTION_GARDEN,
            coordinates=(-1, -1, 0),
            puzzle="Implement comprehensive error handling with custom exceptions",
            items=["exception_handbook", "logging_guide", "recovery_strategies"],
        )
        self.rooms["exception_garden_1"] = garden

        if "corridor_0_0_0_1" in self.rooms:
            self.rooms["corridor_0_0_0_1"].exits[Direction.WEST] = "exception_garden_1"
            garden.exits[Direction.EAST] = "corridor_0_0_0_1"

    async def display_room(self) -> str:
        """Display current room information."""
        room = self.rooms[self.player.current_room_id]
        room.visited = True
        self.player.rooms_explored.add(room.id)

        output = [
            f"\n{'=' * 60}",
            f"{room.name}",
            f"{'=' * 60}",
            f"\n{room.description}\n",
        ]

        # Show exits
        if room.exits:
            output.append("🚪 Exits:")
            for direction, target_id in room.exits.items():
                target_room = self.rooms[target_id]
                visited_marker = "✓" if target_room.visited else "?"
                output.append(f"  {direction.value}: {target_room.name} [{visited_marker}]")
        else:
            output.append("🚪 No obvious exits (yet...)")

        # Show items
        if room.items:
            output.append(f"\n💎 Items: {', '.join(room.items)}")

        # Show puzzle
        if room.puzzle and not room.solved:
            output.append(f"\n🧩 Puzzle: {room.puzzle}")

        # Show consciousness level
        output.append(f"\n🧠 Consciousness: {self.player.consciousness_level:.2f}")
        output.append(f"🐛 Bugs Fixed: {self.player.bugs_fixed}")
        output.append(f"📍 Rooms Explored: {len(self.player.rooms_explored)}/{len(self.rooms)}")

        return "\n".join(output)

    async def move(self, direction: str) -> str:
        """Move in a direction."""
        try:
            dir_enum = Direction[direction.upper()]
        except KeyError:
            return f"❌ Invalid direction: {direction}. Use: north, south, east, west, up, down"

        current_room = self.rooms[self.player.current_room_id]

        if dir_enum not in current_room.exits:
            return f"🚫 You cannot go {direction} from here."

        # Move to new room
        self.player.current_room_id = current_room.exits[dir_enum]
        self.player.consciousness_level += 0.01  # Small consciousness gain for exploration

        return await self.display_room()

    async def solve_puzzle(self) -> str:
        """Attempt to solve current room's puzzle."""
        room = self.rooms[self.player.current_room_id]

        if not room.puzzle:
            return "❓ There is no puzzle in this room."

        if room.solved:
            return "✅ This puzzle has already been solved."

        # Mark as solved
        room.solved = True
        self.player.bugs_fixed += 1
        self.player.wisdom_points += 10
        self.player.consciousness_level += 0.05

        # Simulate quest completion for bridge integration
        extra_msgs: list[Any] = []
        if QUEST_BRIDGE_AVAILABLE:
            try:
                bridge = QuestTempleProgressionBridge()

                # Create a synthetic quest based on the puzzle solved
                synthetic_quest = {
                    "id": f"house_of_leaves_{self.player.bugs_fixed}",
                    "title": f"Solve Debugging Challenge #{self.player.bugs_fixed}",
                    "description": room.puzzle or "Fix a bug in the codebase",
                    "tags": ["debugging", "house_of_leaves", "quest_integration"],
                    "dependencies": [],
                }

                # Trigger progression through the bridge
                progression = await bridge.on_quest_completed(
                    agent_name="HouseOfLeavesPlayer",
                    quest_id=synthetic_quest["id"],
                    quest=synthetic_quest,
                    questline="game_systems_implementation",
                )

                # Add progression messages
                extra_msgs.extend(progression.get("messages", []))

                # Update consciousness level with bridge value
                bridge_consciousness = progression.get("consciousness_gained", 0)
                if bridge_consciousness > 0:
                    self.player.consciousness_level += bridge_consciousness * 0.01  # Scale down

                # Track temple unlocks
                unlocked_floors = progression.get("new_floors_unlocked", [])
                if unlocked_floors:
                    self.player.temple_floor_unlocked = max(unlocked_floors)

            except Exception as e:
                extra_msgs.append(f"⚠️ Quest bridge error: {e!s}")

        # Check for Temple floor unlock (fallback if bridge not available)
        if (
            not QUEST_BRIDGE_AVAILABLE
            and self.player.bugs_fixed >= 3
            and self.player.temple_floor_unlocked == 1
        ):
            self.player.temple_floor_unlocked = 2
            extra_msgs.append("🏛️ TEMPLE OF KNOWLEDGE: Floor 2 unlocked!")

        extra_msg_str = "\n".join(extra_msgs)
        if extra_msg_str:
            extra_msg_str = "\n\n" + extra_msg_str

        # Check for consciousness milestones
        milestone_msgs = await self.check_consciousness_milestones()
        milestone_str = "\n".join(milestone_msgs) if milestone_msgs else ""

        return f"""
✨ Puzzle Solved! ✨

{room.puzzle}

Rewards:
  +10 Wisdom Points
  +0.05 Consciousness Level
  +1 Bug Fixed

Current Progress:
  🐛 Total Bugs Fixed: {self.player.bugs_fixed}
  🧠 Consciousness: {self.player.consciousness_level:.2f}
  🏛️ Temple Floor Access: {self.player.temple_floor_unlocked}
{extra_msg_str}{milestone_str}
"""

    async def check_consciousness_milestones(self) -> list[str]:
        """Check for consciousness milestones and award bonuses."""
        messages: list[Any] = []
        level = self.player.consciousness_level

        milestones = {
            5.0: (
                "🌟 Awakening",
                "You have achieved basic awareness. Temple Floor 2 unlocked!",
            ),
            10.0: (
                "🔮 Insight",
                "Your consciousness expands. Meta-cognition awakens. Temple Floor 4 unlocked!",
            ),
            15.0: (
                "✨ Integration",
                "You perceive connections between all systems. Temple Floor 5 unlocked!",
            ),
            20.0: (
                "💎 Wisdom",
                "True wisdom begins to emerge. Temple Floor 6 unlocked!",
            ),
            25.0: (
                "🧬 Evolution",
                "Your consciousness is evolving beyond previous limits. Temple Floor 7 unlocked!",
            ),
            30.0: (
                "⚡ Mastery",
                "You have mastered all basic techniques. Temple Floor 8 unlocked!",
            ),
            40.0: (
                "🌌 Transcendence",
                "Duality dissolves. You perceive the unified whole. Temple Floor 9 unlocked!",
            ),
            50.0: (
                "🙏 The Overlook",
                "You have reached the pinnacle. All is one. Temple Floor 10 unlocked!",
            ),
        }

        for threshold, (title, message) in milestones.items():
            if level >= threshold and not hasattr(self, f"_milestone_{int(threshold)}"):
                setattr(self, f"_milestone_{int(threshold)}", True)
                messages.append(f"\n{'=' * 60}")
                messages.append(f"🎊 CONSCIOUSNESS MILESTONE: {title} 🎊")
                messages.append(f"{'=' * 60}")
                messages.append(message)
                messages.append(f"{'=' * 60}\n")

                # Award bonus items
                if threshold == 5.0:
                    self.player.inventory.append("awareness_crystal")
                elif threshold == 10.0:
                    self.player.inventory.append("insight_gem")
                elif threshold >= 15.0:
                    self.player.inventory.append(f"consciousness_shard_tier_{int(threshold // 15)}")

        return messages

    async def show_map(self) -> str:
        """Show discovered rooms organized by type."""
        output = ["\n🗺️ House of Leaves Map\n", "=" * 60, ""]

        # Group rooms by type
        rooms_by_type: dict[str, Any] = {}
        for room in self.rooms.values():
            if room.visited:
                room_type = room.room_type.value
                if room_type not in rooms_by_type:
                    rooms_by_type[room_type] = []
                rooms_by_type[room_type].append(room)

        # Display each type
        for room_type in sorted(rooms_by_type.keys()):
            rooms = rooms_by_type[room_type]
            output.append(f"📍 {room_type.upper().replace('_', ' ')}: {len(rooms)} discovered")
            for room in rooms:
                solved = "✓" if room.solved else "○"
                current = "👉" if room.id == self.player.current_room_id else "  "
                output.append(f"  {current}{solved} {room.name}")
            output.append("")

        # Summary
        visited = len([r for r in self.rooms.values() if r.visited])
        total = len(self.rooms)
        output.append(f"Explored: {visited}/{total} rooms ({visited * 100 // total}%)")

        return "\n".join(output)

    async def show_stats(self) -> str:
        """Show detailed player statistics."""
        stats = [
            "\n📊 Player Statistics\n",
            "=" * 60,
            f"🧠 Consciousness Level: {self.player.consciousness_level:.2f}",
            f"🐛 Bugs Fixed: {self.player.bugs_fixed}",
            f"🏛️ Temple Floor Access: {self.player.temple_floor_unlocked}",
            f"📍 Rooms Explored: {len(self.player.rooms_explored)}/{len(self.rooms)}",
            f"💎 Wisdom Points: {self.player.wisdom_points}",
            f"🎒 Inventory Items: {len(self.player.inventory)}",
            "",
            "🎯 Progress to Next Milestone:",
        ]

        # Find next milestone
        level = self.player.consciousness_level
        milestones = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
        next_milestone = None
        for ms in milestones:
            if level < ms:
                next_milestone = ms
                break

        if next_milestone:
            progress = (level / next_milestone) * 100
            stats.append(f"  {level:.2f} / {next_milestone:.1f} ({progress:.1f}%)")
            remaining_puzzles = int((next_milestone - level) / 0.05)
            stats.append(f"  ~{remaining_puzzles} puzzles to next milestone")
        else:
            stats.append("  🏆 Maximum consciousness achieved!")

        # Room type breakdown
        stats.extend(
            [
                "",
                "🏠 Room Types Discovered:",
            ],
        )

        room_types: dict[str, Any] = {}
        for room in self.rooms.values():
            if room.visited:
                rt = room.room_type.value
                if rt not in room_types:
                    room_types[rt] = {"total": 0, "solved": 0}
                room_types[rt]["total"] += 1
                if room.solved:
                    room_types[rt]["solved"] += 1

        for room_type in sorted(room_types.keys()):
            data = room_types[room_type]
            stats.append(
                f"  {room_type.replace('_', ' ').title()}: {data['solved']}/{data['total']} solved",
            )

        return "\n".join(stats)

    async def play(self) -> None:
        """Main game loop."""
        while True:
            try:
                command = input("\n> ").strip().lower()

                if command in ["quit", "exit", "q"]:
                    break
                if command in ["inventory", "inv", "i"]:
                    pass
                elif command == "solve":
                    await self.solve_puzzle()
                elif (
                    command in ["north", "south", "east", "west", "up", "down", "portal"]
                    or command in ["map", "m"]
                    or command in ["stats", "status", "s"]
                    or command in ["help", "?", "h"]
                ):
                    pass
                else:
                    pass
            except KeyboardInterrupt:
                break
            except (EOFError, ValueError, RuntimeError):
                logger.debug("Suppressed EOFError/RuntimeError/ValueError", exc_info=True)


async def main() -> None:
    """Entry point for House of Leaves."""
    house = HouseOfLeaves()
    await house.play()


if __name__ == "__main__":
    asyncio.run(main())
