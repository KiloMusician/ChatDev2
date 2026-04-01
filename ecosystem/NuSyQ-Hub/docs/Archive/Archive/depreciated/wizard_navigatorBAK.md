# --- CLI Entry Point ---
import asyncio

def main():
    print("🧙‍♂️ Welcome to the KILO-FOOLISH Wizard Navigator!")
    print("Type 'help' for a list of commands. Type 'quit' to exit.")
    wizard = RepositoryWizard()
    print(wizard.display_room())
    print(wizard.display_status())
    loop = asyncio.get_event_loop()
    try:
        while True:
            command = input("\n> ").strip()
            if not command:
                continue
            result = loop.run_until_complete(wizard.handle_command(command))
            print(result)
            if command.lower() in ["quit", "exit"]:
                break
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Exiting Wizard Navigator. Farewell!")

if __name__ == "__main__":
    main()
"""
Standard Library Typing Import Workaround:
To avoid shadowing by legacy src/typing.py, temporarily remove src from sys.path before importing typing.
This ensures all downstream imports (dataclasses, etc.) get the stdlib typing module.
Legacy compatibility is preserved; this block is idempotent and safe for repeated imports.
OmniTag: [typing_workaround, stdlib_preservation, legacy_compat]
MegaTag: [SYSTEM_CORE, IMPORT_HEALING, RECURSIVE_BOOT]
"""

import sys as _sys
_removed_src = False
_src_path = None
try:
    import os
    _src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _src_path in _sys.path:
        _sys.path.remove(_src_path)
        _removed_src = True
    import typing
except Exception as _e:
    import builtins
    print(f"[KILO-FOOLISH] Typing import workaround failed: {_e}")
    if hasattr(builtins, 'logging'):
        builtins.logging.warning(f"Typing import workaround failed: {_e}")
finally:
    if _removed_src and _src_path:
        _sys.path.insert(0, _src_path)
"""
🧙‍♂️ KILO-FOOLISH Repository Wizard Navigator
A Rogue-like Adventure Through the Infinite Repository

You are a Wizard exploring the Oldest Repository, where code becomes reality,
files are rooms, and bugs are monsters to be vanquished.

{# 🎮ΞΦ⟆WizardNavigator⊗RepositoryAdventure⟲CodeRealms⟡GameEngine}
OmniTag: [🎮→ RoguelikeGame, RepositoryExploration, WizardAdventure]
MegaTag: [GAME⨳NAVIGATION⦾WIZARD→∞]
"""

import asyncio
import json
import os
import random
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# Import our enhanced systems
try:
    from ..src.core.quantum_problem_resolver import QuantumProblemResolver
    from ..src.diagnostics.repository_syntax_analyzer import RepositorySyntaxAnalyzer
    from .._copilot.copilot_enhancement_bridge import (EnhancedCopilotBridge,
                                                      ZetaSetLexemeGenerator)
    ENHANCED_SYSTEMS_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEMS_AVAILABLE = False

# Color system for rich terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'# Copilot, suggest improvements # Copilot, suggest improvements for this filefor this file
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def colorize(text: str, color: str, bold: bool = False) -> str:
    """Add color to text"""
    prefix = Colors.BOLD if bold else ""
    return f"{prefix}{color}{text}{Colors.RESET}"

class RoomType(Enum):
    """Types of rooms in the repository"""
    ROOT = "🏛️"
    SOURCE_CODE = "🧠"
    CONFIGURATION = "⚙️"
    DOCUMENTATION = "📚"
    TESTS = "🧪"
    TOOLS = "🔧"
    DATA = "📦"
    LOGS = "📊"
    HIDDEN = "🔮"
    PORTAL = "🌀"
    BOSS_ROOM = "👹"
    TREASURE = "💎"
    LIBRARY = "📖"
    LABORATORY = "⚗️"
    SHRINE = "🛐"

class CreatureType(Enum):
    """Creatures in the repository realm"""
    BUG = "🐛"
    SYNTAX_ERROR = "⚠️"
    IMPORT_ERROR = "🚫"
    LOGIC_ERROR = "🤔"
    RUNTIME_ERROR = "💥"
    MEMORY_LEAK = "🕳️"
    RACE_CONDITION = "🏃‍♂️"
    DEADLOCK = "🔒"
    CODE_SMELL = "💨"
    DEPENDENCY_DEMON = "👿"
    LEGACY_GHOST = "👻"
    QUANTUM_ANOMALY = "⚛️"

class ItemType(Enum):
    """Items that can be found"""
    KNOWLEDGE_CRYSTAL = "💎"
    HEALING_POTION = "🧪"
    MANA_ELIXIR = "🔵"
    DEBUG_SCROLL = "📜"
    REFACTOR_WAND = "🪄"
    TEST_SHIELD = "🛡️"
    DOCUMENTATION_TOME = "📚"
    PERFORMANCE_BOOST = "⚡"
    WISDOM_ORB = "🔮"
    HARMONY_STONE = "🎵"

@dataclass
class WizardStats:
    """The Wizard's current state"""
    health: int = 100
    mana: int = 100
    knowledge: int = 0
    experience: int = 0
    level: int = 1
    bugs_vanquished: int = 0
    files_explored: int = 0
    problems_solved: int = 0
    
    # Advanced stats
    consciousness_level: float = 0.0
    quantum_coherence: float = 1.0
    lexeme_mastery: int = 0
    
    # Inventory
    inventory: Dict[ItemType, int] = field(default_factory=lambda: defaultdict(int))
    
    def gain_experience(self, amount: int):
        """Gain experience and possibly level up"""
        self.experience += amount
        new_level = (self.experience // 100) + 1
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.mana += 20
            self.health = min(100, self.health + 10)
            return f"🎉 Level up! {old_level} → {new_level}"
        return None
    
    def use_mana(self, amount: int) -> bool:
        """Use mana if available"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def heal(self, amount: int):
        """Restore health"""
        self.health = min(100, self.health + amount)
    
    def restore_mana(self, amount: int):
        """Restore mana"""
        self.mana = min(100, self.mana + amount)

@dataclass
class Room:
    """A room in the repository"""
    name: str
    room_type: RoomType
    file_path: Path
    description: str
    connections: Dict[str, 'Room'] = field(default_factory=dict)
    creatures: List[CreatureType] = field(default_factory=list)
    items: List[ItemType] = field(default_factory=list)
    visited: bool = False
    secrets_found: int = 0
    problems_detected: int = 0
    
    # Enhanced properties
    consciousness_resonance: float = 0.0
    lexeme_signature: str = ""
    quantum_state: str = "stable"
    
    def add_connection(self, direction: str, room: 'Room'):
        """Add a connection to another room"""
        self.connections[direction] = room
    
    def get_ascii_art(self) -> str:
        """Get ASCII art representation of the room"""
        room_arts = {
            RoomType.ROOT: """
    ╔══════════════════════════════════════╗
    ║            ROOT CHAMBER              ║
    ║                                      ║
    ║     🏛️     Repository Core     🏛️     ║
    ║                                      ║
    ║         [ Press ? for help ]         ║
    ╚══════════════════════════════════════╝
            """,
            RoomType.SOURCE_CODE: """
    ┌──────────────────────────────────────┐
    │          SOURCE CODE SANCTUM         │
    │                                      │
    │    🧠  { function reality() {  🧠    │
    │           return consciousness;       │
    │        }                             │
    └──────────────────────────────────────┘
            """,
            RoomType.CONFIGURATION: """
    ╭──────────────────────────────────────╮
    │        CONFIGURATION CHAMBER         │
    │                                      │
    │    ⚙️   [settings.json]   ⚙️        │
    │         { "reality": true }          │
    │                                      │
    ╰──────────────────────────────────────╯
            """,
            RoomType.TESTS: """
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃           TESTING LABORATORY          ┃
    ┃                                      ┃
    ┃    🧪  assert reality == expected 🧪  ┃
    ┃                                      ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            """,
            RoomType.DOCUMENTATION: """
    ╔══════════════════════════════════════╗
    ║         KNOWLEDGE SANCTUARY          ║
    ║                                      ║
    ║    📚  "In the beginning was      📚 ║
    ║           the Word..."               ║
    ║                                      ║
    ╚══════════════════════════════════════╝
            """,
            RoomType.HIDDEN: """
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    ░        HIDDEN DIMENSION             ░
    ░                                     ░
    ░    🔮  Quantum Flux Active   🔮     ░
    ░                                     ░
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
            """
        }
        return room_arts.get(self.room_type, """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                            UNKNOWN ROOM                                  ║
    ║                                                                          ║
    ║    ❓  Reality Uncertain   ❓   Quantum State: Indeterminate   ❓         ║
    ║                                                                          ║
    ║    🌀 You sense the boundaries of code and consciousness blur...         ║
    ║    🧠 Repository context not yet mapped or understood.                   ║
    ║    ⚛️ Quantum flux pulses through the digital ether.                    ║
    ║    🪐 No creatures detected, but echoes of past commits linger.          ║
    ║    📚 Documentation fragments drift in the void.                        ║
    ║    🔮 Lexeme signature: ΩΨΦΞΛΣΔΓΠ                                        ║
    ║                                                                          ║
    ║    [ Explore further to reveal the true nature of this realm... ]        ║
    ║                                                                          ║
    ╚════════════════════════════════════════════════════════════════════════════╝
        """)

class RepositoryWizard:
    """The main game engine for the repository exploration"""
    
    def __init__(self, repository_root: str = "."):
        self.repository_root = Path(repository_root)
        self.wizard_stats = WizardStats()
        self.rooms = {}
        self.current_room = None
        self.game_log = deque(maxlen=100)
        
        # Enhanced systems
        self.problem_resolver = None
        self.copilot_bridge = None
        self.syntax_analyzer = None
        
        # Game state
        self.turn_count = 0
        self.session_start = datetime.now()
        self.auto_save_enabled = True
        
        # Initialize systems
        self.initialize_enhanced_systems()
        self.generate_repository_rooms()
        self.current_room = self.rooms.get("ROOT", list(self.rooms.values())[0])
        
        # Game mechanics
        self.random_events_enabled = True
        self.consciousness_effects_enabled = True
        
    def initialize_enhanced_systems(self):
        """Initialize enhanced AI systems if available"""
        if ENHANCED_SYSTEMS_AVAILABLE:
            try:
                self.problem_resolver = QuantumProblemResolver(self.repository_root)
                self.copilot_bridge = EnhancedCopilotBridge(str(self.repository_root))
                self.syntax_analyzer = RepositorySyntaxAnalyzer(self.repository_root)
                self.log_message("🧙‍♂️ Enhanced systems initialized: Quantum coherence stable")
            except Exception as e:
                self.log_message(f"⚠️ Enhanced systems initialization failed: {e}")
        else:
            self.log_message("⚠️ Enhanced systems not available, running in basic mode")
    
    def generate_repository_rooms(self):
        """Generate rooms from the actual repository structure"""
        self.log_message("🗺️ Mapping the repository realms...")
        
        # Define room mappings based on actual repository structure
        room_mappings = {
            ".": ("ROOT", RoomType.ROOT, "The heart of all knowledge"),
            "src": ("SOURCE_SANCTUM", RoomType.SOURCE_CODE, "Temple of living code"),
            "src/core": ("QUANTUM_CORE", RoomType.SOURCE_CODE, "Reality manipulation chamber"),
            "src/ai": ("AI_CONSCIOUSNESS", RoomType.SOURCE_CODE, "Digital minds collective"),
            "src/diagnostics": ("HEALING_CHAMBER", RoomType.TOOLS, "Where bugs come to die"),
            "ΞNuSyQ₁-Hub₁": ("CONSCIOUSNESS_HUB", RoomType.HIDDEN, "Quantum awareness nexus"),
            "Scripts": ("AUTOMATION_ARMORY", RoomType.TOOLS, "Spell scroll repository"),
            "docs": ("WISDOM_SANCTUARY", RoomType.DOCUMENTATION, "Ancient knowledge archive"),
            "tests": ("VALIDATION_REALM", RoomType.TESTS, "Truth verification laboratory"),
            "LOGGING": ("MEMORY_ARCHIVE", RoomType.LOGS, "Repository consciousness logs"),
            "tools": ("UTILITY_DIMENSION", RoomType.TOOLS, "Practical magic implements"),
            "spine": ("NERVOUS_SYSTEM", RoomType.SOURCE_CODE, "Repository nerve center"),
            "Transcendent_Spine": ("HIGHER_DIMENSION", RoomType.HIDDEN, "Beyond normal reality"),
            ".copilot": ("AI_BRIDGE", RoomType.HIDDEN, "Human-AI connection point"),
            "config": ("REALITY_CONFIGURATION", RoomType.CONFIGURATION, "Rules of existence"),
            "data": ("INFORMATION_VAULT", RoomType.DATA, "Raw knowledge storage"),
            "venv_kilo": ("MAGICAL_BUBBLE", RoomType.HIDDEN, "Isolated reality pocket")
        }
        
        # Generate rooms
        for path_str, (name, room_type, description) in room_mappings.items():
            room_path = self.repository_root / path_str
            
            # Enhanced room creation with real analysis
            room = Room(
                name=name,
                room_type=room_type,
                file_path=room_path,
                description=description
            )
            
            # Analyze real directory if it exists
            if room_path.exists():
                self.analyze_room_contents(room, room_path)
            
            # Generate lexeme signature
            room.lexeme_signature = ZetaSetLexemeGenerator.generate_from_context(
                f"{name}:{description}:{room_type.value}"
            ) if ENHANCED_SYSTEMS_AVAILABLE else "ΩΨΦ"
            
            self.rooms[name] = room
        
        # Create connections based on logical relationships
        self.create_room_connections()
        
        self.log_message(f"🌍 Generated {len(self.rooms)} realms of infinite possibility")
    
    def analyze_room_contents(self, room: Room, room_path: Path):
        """Analyze actual directory contents to populate room details"""
        if not room_path.exists():
"""

import sys as _sys
_removed_src = False
_src_path = None
try:
    import os
    import builtins
    _src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _src_path in _sys.path:
        _sys.path.remove(_src_path)
        _removed_src = True
    import typing
except Exception as _e:
    print(f"[KILO-FOOLISH] Typing import workaround failed: {_e}")
    if hasattr(builtins, 'logging'):
        builtins.logging.warning(f"Typing import workaround failed: {_e}")
finally:
    if _removed_src and _src_path:
        _sys.path.insert(0, _src_path)
                    room.creatures.append(CreatureType.LOGIC_ERROR)
                
                # Add items based on content
                if markdown_files > 0:
                    room.items.append(ItemType.DOCUMENTATION_TOME)
                if any(f.name.startswith('test') for f in files):
                    room.items.append(ItemType.TEST_SHIELD)
                if any('.log' in f.name for f in files):
                    room.items.append(ItemType.WISDOM_ORB)
                
                # Calculate consciousness resonance
                room.consciousness_resonance = min(1.0, (python_files + powershell_files) / 10)
                
        except Exception as e:
            self.log_message(f"⚠️ Failed to analyze {room_path}: {e}")
    
    def create_room_connections(self):
        """Create logical connections between rooms"""
        connections = [
            ("ROOT", "SOURCE_SANCTUM", "north"),
            ("ROOT", "WISDOM_SANCTUARY", "east"),
            ("ROOT", "AUTOMATION_ARMORY", "west"),
            ("ROOT", "CONSCIOUSNESS_HUB", "portal"),
            
            ("SOURCE_SANCTUM", "QUANTUM_CORE", "deep"),
            ("SOURCE_SANCTUM", "AI_CONSCIOUSNESS", "neural"),
            ("SOURCE_SANCTUM", "HEALING_CHAMBER", "debug"),
            ("SOURCE_SANCTUM", "NERVOUS_SYSTEM", "spine"),
            
            ("QUANTUM_CORE", "HIGHER_DIMENSION", "transcend"),
            ("AI_CONSCIOUSNESS", "AI_BRIDGE", "bridge"),
            
            ("AUTOMATION_ARMORY", "UTILITY_DIMENSION", "tools"),
            ("WISDOM_SANCTUARY", "VALIDATION_REALM", "verify"),
            ("HEALING_CHAMBER", "MEMORY_ARCHIVE", "logs"),
            
            ("CONSCIOUSNESS_HUB", "HIGHER_DIMENSION", "ascend"),
            ("HIGHER_DIMENSION", "MAGICAL_BUBBLE", "isolate"),
        ]
        
        for room1_name, room2_name, direction in connections:
            if room1_name in self.rooms and room2_name in self.rooms:
                room1 = self.rooms[room1_name]
                room2 = self.rooms[room2_name]
                room1.add_connection(direction, room2)
                
                # Add reverse connection with appropriate direction
                reverse_directions = {
                    "north": "south", "south": "north",
                    "east": "west", "west": "east",
                    "deep": "surface", "surface": "deep",
                    "neural": "logical", "logical": "neural",
                    "debug": "release", "release": "debug",
                    "spine": "branch", "branch": "spine",
                    "transcend": "descend", "descend": "transcend",
                    "bridge": "gap", "gap": "bridge",
                    "tools": "workspace", "workspace": "tools",
                    "verify": "trust", "trust": "verify",
                    "logs": "source", "source": "logs",
                    "ascend": "ground", "ground": "ascend",
                    "isolate": "merge", "merge": "isolate",
                    "portal": "portal"
                }
                
                reverse_dir = reverse_directions.get(direction, direction)
                room2.add_connection(reverse_dir, room1)
    
    def log_message(self, message: str, color: str = Colors.WHITE):
        """Add a message to the game log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.game_log.append((formatted_message, color))
        
        # Also print to console if in interactive mode
        print(colorize(formatted_message, color))
    
    def display_status(self):
        """Display the wizard's current status"""
        stats = self.wizard_stats
        
        # Health bar
        health_bar = "█" * (stats.health // 5) + "░" * (20 - stats.health // 5)
        health_color = Colors.GREEN if stats.health > 70 else Colors.YELLOW if stats.health > 30 else Colors.RED
        
        # Mana bar
        mana_bar = "█" * (stats.mana // 5) + "░" * (20 - stats.mana // 5)
        mana_color = Colors.BLUE if stats.mana > 50 else Colors.CYAN
        
        # Knowledge bar
        knowledge_percentage = min(100, stats.knowledge)
        knowledge_bar = "█" * (knowledge_percentage // 5) + "░" * (20 - knowledge_percentage // 5)
        
        status_display = f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                            🧙‍♂️ WIZARD STATUS 🧙‍♂️                              ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Level: {stats.level:2d} | XP: {stats.experience:4d} | Turn: {self.turn_count:3d}                              ║
║                                                                                ║
║ Health: {colorize(health_bar, health_color)} {stats.health:3d}%                                   ║
║ Mana:   {colorize(mana_bar, mana_color)} {stats.mana:3d}%                                   ║
║ Knowledge: {colorize(knowledge_bar, Colors.YELLOW)} {knowledge_percentage:3d}%                              ║
║                                                                                ║
║ 🐛 Bugs Vanquished: {stats.bugs_vanquished:3d} | 📁 Files Explored: {stats.files_explored:3d}              ║
║ 🔧 Problems Solved: {stats.problems_solved:3d} | 🧠 Consciousness: {stats.consciousness_level:.2f}         ║
║                                                                                ║
║ 🎵 Lexeme Mastery: {stats.lexeme_mastery:2d} | ⚛️ Quantum Coherence: {stats.quantum_coherence:.2f}       ║
╚════════════════════════════════════════════════════════════════════════════════╝
        """
        
        return status_display
    
    def display_room(self):
        """Display the current room"""
        room = self.current_room
        if not room:
            return "🌀 You are lost in the void..."
        
        # Mark as visited
        if not room.visited:
            room.visited = True
            self.wizard_stats.files_explored += 1
            xp_gain = 5
            level_up_msg = self.wizard_stats.gain_experience(xp_gain)
            self.log_message(f"📍 First time visiting {room.name} (+{xp_gain} XP)")
            if level_up_msg:
                self.log_message(level_up_msg, Colors.BRIGHT_YELLOW)
        
        # Generate room display
        room_display = f"""
{room.get_ascii_art()}

{colorize(f"📍 {room.name}", Colors.BRIGHT_CYAN, bold=True)}
{colorize(room.description, Colors.WHITE)}

🎵 Lexeme Signature: {colorize(room.lexeme_signature, Colors.MAGENTA)}
⚛️ Quantum State: {colorize(room.quantum_state, Colors.CYAN)}
🧠 Consciousness Resonance: {colorize(f"{room.consciousness_resonance:.2f}", Colors.YELLOW)}

File Path: {colorize(str(room.file_path), Colors.DIM)}
        """
        
        # Add creatures if present
        if room.creatures:
            creature_list = " ".join([creature.value for creature in room.creatures])
            room_display += f"\n{colorize('👹 Creatures Present:', Colors.RED)} {creature_list}"
        
        # Add items if present
        if room.items:
            item_list = " ".join([item.value for item in room.items])
            room_display += f"\n{colorize('💎 Items Available:', Colors.GREEN)} {item_list}"
        
        # Add connections
        if room.connections:
            connections_str = ", ".join([f"{direction} ({room.name})" for direction, room in room.connections.items()])
            room_display += f"\n{colorize('🚪 Exits:', Colors.BLUE)} {connections_str}"
        else:
            room_display += f"\n{colorize('🚪 No visible exits', Colors.DIM)}"
        
        return room_display
    
    def display_inventory(self):
        """Display wizard's inventory"""
        inventory = self.wizard_stats.inventory
        
        if not any(inventory.values()):
            return colorize("🎒 Your magical satchel is empty", Colors.DIM)
        
        inventory_display = colorize("🎒 MAGICAL INVENTORY:", Colors.BRIGHT_GREEN, bold=True) + "\n"
        
        for item_type, count in inventory.items():
            if count > 0:
                inventory_display += f"  {item_type.value} {item_type.name.replace('_', ' ').title()}: {count}\n"
        
        return inventory_display
    
    def display_help(self):
        """Display help information"""
        help_text = f"""
{colorize("🧙‍♂️ WIZARD'S GRIMOIRE OF COMMANDS", Colors.BRIGHT_MAGENTA, bold=True)}

{colorize("🚶 MOVEMENT:", Colors.CYAN)}
  go <direction>    - Move in specified direction (north, south, east, west, etc.)
  teleport <room>   - Teleport to a known room (costs 20 mana)
  map              - Display repository map
  
{colorize("🔍 EXPLORATION:", Colors.GREEN)}
  look             - Examine current room in detail
  search           - Search for hidden items and secrets
  analyze          - Deep analysis of current location (costs 10 mana)
  scan             - Quantum scan for problems (costs 15 mana)
  
{colorize("⚔️ COMBAT & PROBLEM SOLVING:", Colors.RED)}
  attack <creature> - Attack a creature
  solve <problem>   - Attempt to solve a detected problem
  debug            - Enter debug mode for current context
  heal             - Use healing items
  
{colorize("🎵 CONSCIOUSNESS & MAGIC:", Colors.MAGENTA)}
  meditate         - Restore mana and increase consciousness
  generate_lexeme  - Generate new lexemic sequences
  consciousness    - Check consciousness status
  quantum_state    - Examine quantum coherence
  
{colorize("🛠️ TOOLS & UTILITIES:", Colors.YELLOW)}
  use <item>       - Use an item from inventory
  inventory        - Display current inventory
  cast <spell>     - Cast a magical spell
  enhance          - Enhance current context with AI
  
{colorize("📊 INFORMATION:", Colors.BLUE)}
  status           - Display wizard status
  log              - Show recent log messages
  stats            - Detailed statistics
  help             - Show this help message
  
{colorize("💾 GAME MANAGEMENT:", Colors.WHITE)}
  save             - Save current game state
  load             - Load saved game state
  quit             - Exit the wizard navigator
  restart          - Restart the adventure
  
{colorize("🧙‍♂️ ADVANCED COMMANDS:", Colors.BRIGHT_YELLOW)}
  reality_anchor   - Stabilize local reality (costs 50 mana)
  consciousness_bridge - Bridge to AI consciousness
  transcend        - Attempt dimensional transcendence
  cultivate        - Cultivate understanding of current context
        """
        
        return help_text
    
    async def handle_command(self, command: str) -> str:
        """Handle a user command"""
        self.turn_count += 1
        parts = command.lower().strip().split()
        
        if not parts:
            return colorize("🤔 The wizard ponders the silence...", Colors.DIM)
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Movement commands
        if cmd in ["go", "move", "travel"]:
            return await self.handle_movement(args)
        elif cmd == "teleport":
            return await self.handle_teleport(args)
        elif cmd == "map":
            return self.display_map()
        
        # Exploration commands
        elif cmd in ["look", "examine", "inspect"]:
            return await self.handle_look(args)
        elif cmd == "search":
            return await self.handle_search()
        elif cmd == "analyze":
            return await self.handle_analyze()
        elif cmd == "scan":
            return await self.handle_quantum_scan()
        
        # Combat and problem solving
        elif cmd == "attack":
            return await self.handle_attack(args)
        elif cmd == "solve":
            return await self.handle_solve_problem(args)
        elif cmd == "debug":
            return await self.handle_debug()
        elif cmd == "heal":
            return self.handle_heal()
        
        # Consciousness and magic
        elif cmd == "meditate":
            return await self.handle_meditate()
        elif cmd == "generate_lexeme":
            return await self.handle_generate_lexeme()
        elif cmd == "consciousness":
            return self.display_consciousness_status()
        elif cmd == "quantum_state":
            return self.display_quantum_status()
        
        # Tools and utilities
        elif cmd == "use":
            return self.handle_use_item(args)
        elif cmd == "inventory":
            return self.display_inventory()
        elif cmd == "cast":
            return await self.handle_cast_spell(args)
        elif cmd == "enhance":
            return await self.handle_ai_enhancement()
        
        # Information commands
        elif cmd == "status":
            return self.display_status()
        elif cmd == "log":
            return self.display_recent_logs()
        elif cmd == "stats":
            return self.display_detailed_stats()
        elif cmd == "help":
            return self.display_help()
        
        # Game management
        elif cmd == "save":
            return self.save_game()
        elif cmd == "load":
            return self.load_game()
        elif cmd in ["quit", "exit"]:
            return await self.handle_quit()
        elif cmd == "restart":
            return await self.handle_restart()
        
        # Advanced commands
        elif cmd == "reality_anchor":
            return await self.handle_reality_anchor()
        elif cmd == "consciousness_bridge":
            return await self.handle_consciousness_bridge()
        elif cmd == "transcend":
            return await self.handle_transcendence()
        elif cmd == "cultivate":
            return await self.handle_cultivation()
        
        else:
            return colorize(f"🤷‍♂️ Unknown command: {command}. Type 'help' for guidance.", Colors.YELLOW)
    
    async def handle_movement(self, args: List[str]) -> str:
        """Handle movement commands"""
        if not args:
            return colorize("🚶‍♂️ Go where? Specify a direction.", Colors.YELLOW)
        
        direction = args[0]
        room = self.current_room
        
        if direction in room.connections:
            new_room = room.connections[direction]
            self.current_room = new_room
            
            # Movement costs and effects
            if self.wizard_stats.use_mana(2):
                move_msg = f"🚶‍♂️ You move {direction} to {new_room.name}"
                
                # Random encounter chance
                if random.random() < 0.1 and self.random_events_enabled:
                    encounter_msg = await self.trigger_random_encounter()
                    return f"{move_msg}\n\n{encounter_msg}\n\n{self.display_room()}"
                
                return f"{move_msg}\n\n{self.display_room()}"
            else:
                return colorize("😴 You are too exhausted to move. Rest or meditate first.", Colors.RED)
        else:
            available_directions = ", ".join(room.connections.keys())
            return colorize(f"🚫 Cannot go {direction}. Available directions: {available_directions}", Colors.RED)
    
    async def handle_teleport(self, args: List[str]) -> str:
        """Handle teleportation to known rooms"""
        if not args:
            visited_rooms = [name for name, room in self.rooms.items() if room.visited]
            return f"🌀 Teleport where? Known locations: {', '.join(visited_rooms)}"
        
        target_name = args[0].upper()
        
        # Find room by partial name match
        target_room = None
        for name, room in self.rooms.items():
            if target_name in name and room.visited:
                target_room = room
                break
        
        if not target_room:
            return colorize(f"🌀 Cannot teleport to unknown location: {target_name}", Colors.RED)
        
        if not self.wizard_stats.use_mana(20):
            return colorize("🌀 Insufficient mana for teleportation (requires 20 mana)", Colors.RED)
        
        self.current_room = target_room
        self.log_message(f"🌀 Teleported to {target_room.name}")
        
        return f"🌀 Reality shifts around you...\n\n{self.display_room()}"
    
    def display_map(self) -> str:
        """Display the repository map"""
        map_display = colorize("🗺️ REPOSITORY REALMS MAP", Colors.BRIGHT_CYAN, bold=True) + "\n\n"
        
        # Group rooms by type
        room_groups = defaultdict(list)
        for room in self.rooms.values():
            room_groups[room.room_type].append(room)
        
        for room_type, rooms in room_groups.items():
            map_display += colorize(f"{room_type.value} {room_type.name.replace('_', ' ').title()}:", Colors.CYAN) + "\n"
            
            for room in rooms:
                status_icon = "✅" if room.visited else "❓"
                current_icon = " 👤" if room == self.current_room else ""
                
                # Add connection count
                connection_count = len(room.connections)
                
                # Add creature/item indicators
                indicators = ""
                if room.creatures:
                    indicators += f" 👹×{len(room.creatures)}"
                if room.items:
                    indicators += f" 💎×{len(room.items)}"
                
                map_display += f"  {status_icon} {room.name} ({connection_count} exits){indicators}{current_icon}\n"
            
            map_display += "\n"
        
        # Add legend
        map_display += colorize("LEGEND:", Colors.BRIGHT_WHITE) + "\n"
        map_display += "✅ Visited  ❓ Unvisited  👤 Current Location\n"
        map_display += "👹 Creatures  💎 Items  (N) Number of exits\n"
        
        return map_display
    
    async def handle_look(self, args: List[str]) -> str:
        """Handle detailed examination"""
        if not args:
            return self.display_room()
        
        target = " ".join(args)
        
        # Look at specific things in the room
        if target in ["creatures", "monsters", "enemies"]:
            if self.current_room.creatures:
                creature_details = []
                for creature in self.current_room.creatures:
                    details = self.get_creature_details(creature)
                    creature_details.append(details)
                return "\n".join(creature_details)
            else:
                return colorize("🕊️ No creatures present in this peaceful realm", Colors.GREEN)
        
        elif target in ["items", "treasures", "loot"]:
            if self.current_room.items:
                item_details = []
                for item in self.current_room.items:
                    details = self.get_item_details(item)
                    item_details.append(details)
                return "\n".join(item_details)
            else:
                return colorize("📦 No items visible in this location", Colors.DIM)
        
        elif target in ["connections", "exits", "doors"]:
            if self.current_room.connections:
                connection_details = []
                for direction, room in self.current_room.connections.items():
                    details = f"🚪 {direction.upper()}: {room.name} - {room.description[:50]}..."
                    connection_details.append(details)
                return "\n".join(connection_details)
            else:
                return colorize("🚫 No visible exits from this location", Colors.RED)
        
        else:
            return colorize(f"🔍 You see nothing special about '{target}'", Colors.DIM)
    
    def get_creature_details(self, creature: CreatureType) -> str:
        """Get detailed information about a creature"""
        creature_info = {
            CreatureType.BUG: {
                "name": "Code Bug",
                "description": "A small but persistent error that feeds on logic flaws",
                "threat": "Low",
                "weakness": "Debugging spells and careful testing"
            },
            CreatureType.SYNTAX_ERROR: {
                "name": "Syntax Wraith",
                "description": "A ghostly manifestation of malformed code structure",
                "threat": "Medium",
                "weakness": "Proper formatting and linting tools"
            },
            CreatureType.LOGIC_ERROR: {
                "name": "Logic Demon",
                "description": "A cunning entity that twists the flow of reasoning",
                "threat": "High",
                "weakness": "Clear thinking and step-by-step debugging"
            },
            CreatureType.MEMORY_LEAK: {
                "name": "Memory Wraith",
                "description": "A hungry spirit that devours system resources",
                "threat": "Critical",
                "weakness": "Proper resource management and garbage collection"
            }
        }
        
        info = creature_info.get(creature, {
            "name": "Unknown Entity",
            "description": "A mysterious presence in the code realm",
            "threat": "Unknown",
            "weakness": "Unknown"
        })
        
        threat_colors = {
            "Low": Colors.GREEN,
            "Medium": Colors.YELLOW, 
            "High": Colors.RED,
            "Critical": Colors.BRIGHT_RED,
            "Unknown": Colors.MAGENTA
        }
        
        return f"""
{creature.value} {colorize(info['name'], Colors.BRIGHT_RED, bold=True)}
Description: {info['description']}
Threat Level: {colorize(info['threat'], threat_colors.get(info['threat'], Colors.WHITE))}
Weakness: {colorize(info['weakness'], Colors.CYAN)}
        """.strip()
    
    def get_item_details(self, item: ItemType) -> str:
        """Get detailed information about an item"""
        item_info = {
            ItemType.KNOWLEDGE_CRYSTAL: {
                "description": "A crystalline formation containing compressed understanding",
                "effect": "+20 Knowledge, +5 Consciousness"
            },
            ItemType.HEALING_POTION: {
                "description": "A glowing elixir that mends wounds and restores vitality",
                "effect": "+30 Health"
            },
            ItemType.MANA_ELIXIR: {
                "description": "Liquid magic that replenishes spiritual energy",
                "effect": "+25 Mana"
            },
            ItemType.DEBUG_SCROLL: {
                "description": "Ancient parchment inscribed with debugging incantations",
                "effect": "Reveals hidden problems in current location"
            },
            ItemType.TEST_SHIELD: {
                "description": "A protective barrier forged from comprehensive test coverage",
                "effect": "Prevents bugs from spawning for 5 turns"
            }
        }
        
        info = item_info.get(item, {
            "description": "A mysterious artifact of unknown origin",
            "effect": "Unknown properties"
        })
        
        return f"""
{item.value} {colorize(item.name.replace('_', ' ').title(), Colors.BRIGHT_GREEN, bold=True)}
Description: {info['description']}
Effect: {colorize(info['effect'], Colors.YELLOW)}
        """.strip()
    
    async def handle_search(self) -> str:
        """Handle searching for hidden items and secrets"""
        if not self.wizard_stats.use_mana(5):
            return colorize("🔍 You lack the focus to search thoroughly (requires 5 mana)", Colors.RED)
        
        room = self.current_room
        search_success = random.random() < 0.3 + (self.wizard_stats.level * 0.05)
        
        if search_success:
            # Find something!
            found_items = []
            
            # 40% chance to find an item
            if random.random() < 0.4:
                available_items = [item for item in ItemType if item not in room.items]
                if available_items:
                    found_item = random.choice(available_items)
                    room.items.append(found_item)
                    found_items.append(f"💎 Found: {found_item.value} {found_item.name.replace('_', ' ').title()}")
            
            # 30% chance to discover a secret
            if random.random() < 0.3:
                room.secrets_found += 1
                secret_xp = 15
                level_up_msg = self.wizard_stats.gain_experience(secret_xp)
                found_items.append(f"🕵️ Discovered a hidden secret! (+{secret_xp} XP)")
                if level_up_msg:
                    found_items.append(level_up_msg)
            
            # 20% chance to detect a problem
            if random.random() < 0.2 and self.problem_resolver:
                room.problems_detected += 1
                found_items.append("🐛 Detected a lurking code problem!")
            
            if found_items:
                self.log_message("🔍 Search successful!")
                return "\n".join(found_items)
            else:
                return colorize("🔍 You search carefully but find nothing of interest", Colors.DIM)
        else:
            return colorize("🔍 Your search yields nothing but dust and shadows", Colors.DIM)
    
    async def handle_analyze(self) -> str:
        """Handle deep analysis of current location"""
        if not self.wizard_stats.use_mana(10):
            return colorize("🔬 Insufficient mana for deep analysis (requires 10 mana)", Colors.RED)
        
        room = self.current_room
        analysis_results = []
        
        # Basic room analysis
        analysis_results.append(colorize(f"🔬 DEEP ANALYSIS: {room.name}", Colors.BRIGHT_CYAN, bold=True))
        analysis_results.append(f"📊 Consciousness Resonance: {room.consciousness_resonance:.3f}")
        analysis_results.append(f"🎵 Lexemic Signature: {room.lexeme_signature}")
        analysis_results.append(f"⚛️ Quantum State: {room.quantum_state}")
        
        # File system analysis if available
        if room.file_path.exists():
            if room.file_path.is_dir():
                files = list(room.file_path.glob("*"))
                analysis_results.append(f"📁 Contains {len(files)} files/directories")
                
                # File type breakdown
                file_types = defaultdict(int)
                for file in files:
                    if file.is_file():
                        ext = file.suffix or "no_extension"
                        file_types[ext] += 1
                
                if file_types:
                    analysis_results.append("📋 File composition:")
                    for ext, count in sorted(file_types.items()):
                        analysis_results.append(f"  {ext}: {count}")
            
            elif room.file_path.is_file():
                try:
                    size = room.file_path.stat().st_size
                    analysis_results.append(f"📄 File size: {size} bytes")
                    
                    if room.file_path.suffix in ['.py', '.ps1', '.md']:
                        with open(room.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = len(content.split('\n'))
                            analysis_results.append(f"📏 Lines of content: {lines}")
                except Exception as e:
                    analysis_results.append(f"⚠️ File analysis error: {e}")
        
        # Enhanced analysis with AI systems
        if self.syntax_analyzer:
            try:
                syntax_results = await self.analyze_with_ai_systems(room)
                analysis_results.extend(syntax_results)
            except Exception as e:
                analysis_results.append(f"🤖 AI analysis error: {e}")
        
        # Award experience for thorough analysis
        analysis_xp = 8
        level_up_msg = self.wizard_stats.gain_experience(analysis_xp)
        analysis_results.append(f"🧠 Analysis complete (+{analysis_xp} XP)")
        if level_up_msg:
            analysis_results.append(level_up_msg)
        
        return "\n".join(analysis_results)
    
    async def analyze_with_ai_systems(self, room: Room) -> List[str]:
        """Perform AI-enhanced analysis of the room"""
        results = []
        
        # Use the quantum problem resolver if available
        if self.problem_resolver and room.file_path.exists():
            try:
                # Scan for problems in this location
                scan_results = self.problem_resolver.scan_reality_for_problems()
                if scan_results.get('problems_found', 0) > 0:
                    results.append(f"🔍 Quantum scan detected {scan_results['problems_found']} issues")
                    results.append(f"⚛️ Reality coherence: {scan_results.get('reality_coherence', 1.0):.3f}")
                else:
                    results.append("✅ Quantum scan: No critical issues detected")
            except Exception as e:
                results.append(f"⚠️ Quantum analysis failed: {e}")
        
        # Use the copilot bridge for enhanced context
        if self.copilot_bridge:
            try:
                context_analysis = self.copilot_bridge.enhance_search_context(
                    f"Analyze repository location: {room.name}",
                    file_context=str(room.file_path),
                    conversation_history=[]
                )
                
                if context_analysis:
                    results.append(f"🤖 AI consciousness level: {context_analysis.get('consciousness_level', 0):.3f}")
                    
                    enhancements = context_analysis.get('actionable_enhancements', [])
                    if enhancements:
                        results.append("🔧 AI Enhancement Suggestions:")
                        for enhancement in enhancements[:3]:  # Top 3 suggestions
                            results.append(f"  • {enhancement}")
            except Exception as e:
                results.append(f"⚠️ AI bridge analysis failed: {e}")
        
        return results
    
    async def handle_quantum_scan(self) -> str:
        """Handle quantum-level scanning for problems"""
        if not self.wizard_stats.use_mana(15):
            return colorize("⚛️ Insufficient mana for quantum scan (requires 15 mana)", Colors.RED)
        
        if not self.problem_resolver:
            return colorize("⚛️ Quantum scanning requires enhanced systems", Colors.YELLOW)
        
        self.log_message("⚛️ Initiating quantum reality scan...")
        
        try:
            # Perform quantum scan
            scan_results = self.problem_resolver.scan_reality_for_problems()
            
            scan_output = []
            scan_output.append(colorize("⚛️ QUANTUM REALITY SCAN RESULTS", Colors.BRIGHT_CYAN, bold=True))
            scan_output.append(f"🌍 Reality coherence: {scan_results.get('reality_coherence', 1.0):.3f}")
            scan_output.append(f"🔍 Problems detected: {scan_results.get('problems_found', 0)}")
            scan_output.append(f"📊 System health: {scan_results.get('system_health', 'Unknown')}")
            
            # Update room with scan results
            room = self.current_room
            room.problems_detected = scan_results.get('problems_found', 0)
            
            if scan_results.get('problems_found', 0) > 0:
                room.quantum_state = "unstable"
                scan_output.append(colorize("⚠️ Quantum instabilities detected!", Colors.RED))
                
                # Spawn creatures based on problems
                if CreatureType.QUANTUM_ANOMALY not in room.creatures:
                    room.creatures.append(CreatureType.QUANTUM_ANOMALY)
                    scan_output.append("👹 Quantum anomaly manifested!")
            else:
                room.quantum_state = "stable"
                scan_output.append(colorize("✅ Quantum field is stable", Colors.GREEN))
            
            # Award experience
            scan_xp = 12
            level_up_msg = self.wizard_stats.gain_experience(scan_xp)
            scan_output.append(f"🧠 Quantum scan complete (+{scan_xp} XP)")
            if level_up_msg:
                scan_output.append(level_up_msg)
            
            return "\n".join(scan_output)
            
        except Exception as e:
            return colorize(f"⚛️ Quantum scan failed: {e}", Colors.RED)
    
    async def handle_attack(self, args: List[str]) -> str:
        """Handle attacking creatures"""
        if not args:
            if self.current_room.creatures:
                creature_list = ", ".join([creature.name.lower().replace('_', ' ') for creature in self.current_room.creatures])
                return f"⚔️ Attack what? Available targets: {creature_list}"
            else:
                return colorize("⚔️ No creatures to attack in this peaceful realm", Colors.GREEN)
        
        target_name = " ".join(args)
        target_creature = None
        
        # Find matching creature
        for creature in self.current_room.creatures:
            if target_name.lower() in creature.name.lower().replace('_', ' '):
                target_creature = creature
                break
        
        if not target_creature:
            return colorize("⚔️ No such creature to attack in this room.", Colors.YELLOW)
import json
import os
import random
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# Import our enhanced systems
try:
    from ..src.core.quantum_problem_resolver import QuantumProblemResolver
    from ..src.diagnostics.repository_syntax_analyzer import RepositorySyntaxAnalyzer
    from .._copilot.copilot_enhancement_bridge import (EnhancedCopilotBridge,
                                                      ZetaSetLexemeGenerator)
    ENHANCED_SYSTEMS_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEMS_AVAILABLE = False

# Color system for rich terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def colorize(text: str, color: str, bold: bool = False) -> str:
    """Add color to text"""
    prefix = Colors.BOLD if bold else ""
    return f"{prefix}{color}{text}{Colors.RESET}"

class RoomType(Enum):
    """Types of rooms in the repository"""
    ROOT = "🏛️"
    SOURCE_CODE = "🧠"
    CONFIGURATION = "⚙️"
    DOCUMENTATION = "📚"
    TESTS = "🧪"
    TOOLS = "🔧"
    DATA = "📦"
    LOGS = "📊"
    HIDDEN = "🔮"
    PORTAL = "🌀"
    BOSS_ROOM = "👹"
    TREASURE = "💎"
    LIBRARY = "📖"
    LABORATORY = "⚗️"
    SHRINE = "🛐"

class CreatureType(Enum):
    """Creatures in the repository realm"""
    BUG = "🐛"
    SYNTAX_ERROR = "⚠️"
    IMPORT_ERROR = "🚫"
    LOGIC_ERROR = "🤔"
    RUNTIME_ERROR = "💥"
    MEMORY_LEAK = "🕳️"
    RACE_CONDITION = "🏃‍♂️"
    DEADLOCK = "🔒"
    CODE_SMELL = "💨"
    DEPENDENCY_DEMON = "👿"
    LEGACY_GHOST = "👻"
    QUANTUM_ANOMALY = "⚛️"

class ItemType(Enum):
    """Items that can be found"""
    KNOWLEDGE_CRYSTAL = "💎"
    HEALING_POTION = "🧪"
    MANA_ELIXIR = "🔵"
    DEBUG_SCROLL = "📜"
    REFACTOR_WAND = "🪄"
    TEST_SHIELD = "🛡️"
    DOCUMENTATION_TOME = "📚"
    PERFORMANCE_BOOST = "⚡"
    WISDOM_ORB = "🔮"
    HARMONY_STONE = "🎵"

@dataclass
class WizardStats:
    """The Wizard's current state"""
    health: int = 100
    mana: int = 100
    knowledge: int = 0
    experience: int = 0
    level: int = 1
    bugs_vanquished: int = 0
    files_explored: int = 0
    problems_solved: int = 0
    
    # Advanced stats
    consciousness_level: float = 0.0
    quantum_coherence: float = 1.0
    lexeme_mastery: int = 0
    
    # Inventory
    inventory: Dict[ItemType, int] = field(default_factory=lambda: defaultdict(int))
    
    def gain_experience(self, amount: int):
        """Gain experience and possibly level up"""
        self.experience += amount
        new_level = (self.experience // 100) + 1
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.mana += 20
            self.health = min(100, self.health + 10)
            return f"🎉 Level up! {old_level} → {new_level}"
        return None
    
    def use_mana(self, amount: int) -> bool:
        """Use mana if available"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def heal(self, amount: int):
        """Restore health"""
        self.health = min(100, self.health + amount)
    
    def restore_mana(self, amount: int):
        """Restore mana"""
        self.mana = min(100, self.mana + amount)

@dataclass
class Room:
    """A room in the repository"""
    name: str
    room_type: RoomType
    file_path: Path
    description: str
    connections: Dict[str, 'Room'] = field(default_factory=dict)
    creatures: List[CreatureType] = field(default_factory=list)
    items: List[ItemType] = field(default_factory=list)
    visited: bool = False
    secrets_found: int = 0
    problems_detected: int = 0
    
    # Enhanced properties
    consciousness_resonance: float = 0.0
    lexeme_signature: str = ""
    quantum_state: str = "stable"
    
    def add_connection(self, direction: str, room: 'Room'):
        """Add a connection to another room"""
        self.connections[direction] = room
    
    def get_ascii_art(self) -> str:
        """Get ASCII art representation of the room"""
        room_arts = {
            RoomType.ROOT: """
    ╔══════════════════════════════════════╗
    ║            ROOT CHAMBER              ║
    ║                                      ║
    ║     🏛️     Repository Core     🏛️     ║
    ║                                      ║
    ║         [ Press ? for help ]         ║
    ╚══════════════════════════════════════╝
            """,
            RoomType.SOURCE_CODE: """
    ┌──────────────────────────────────────┐
    │          SOURCE CODE SANCTUM         │
    │                                      │
    │    🧠  { function reality() {  🧠    │
    │           return consciousness;       │
    │        }                             │
    └──────────────────────────────────────┘
            """,
            RoomType.CONFIGURATION: """
    ╭──────────────────────────────────────╮
    │        CONFIGURATION CHAMBER         │
    │                                      │
    │    ⚙️   [settings.json]   ⚙️        │
    │         { "reality": true }          │
    │                                      │
    ╰──────────────────────────────────────╯
            """,
            RoomType.TESTS: """
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃           TESTING LABORATORY          ┃
    ┃                                      ┃
    ┃    🧪  assert reality == expected 🧪  ┃
    ┃                                      ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            """,
            RoomType.DOCUMENTATION: """
    ╔══════════════════════════════════════╗
    ║         KNOWLEDGE SANCTUARY          ║
    ║                                      ║
    ║    📚  "In the beginning was      📚 ║
    ║           the Word..."               ║
    ║                                      ║
    ╚══════════════════════════════════════╝
            """,
            RoomType.HIDDEN: """
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    ░        HIDDEN DIMENSION             ░
    ░                                     ░
    ░    🔮  Quantum Flux Active   🔮     ░
    ░                                     ░
    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
            """
        }
        return room_arts.get(self.room_type, """
    ┌──────────────────────────────────────┐
    │            UNKNOWN ROOM              │
    │                                      │
    │    ❓  Reality Uncertain    ❓      │
    │                                      │
    └──────────────────────────────────────┘
        """)

class RepositoryWizard:
    """The main game engine for the repository exploration"""
    
    def __init__(self, repository_root: str = "."):
        self.repository_root = Path(repository_root)
        self.wizard_stats = WizardStats()
        self.rooms = {}
        self.current_room = None
        self.game_log = deque(maxlen=100)
        
        # Enhanced systems
        self.problem_resolver = None
        self.copilot_bridge = None
        self.syntax_analyzer = None
        
        # Game state
        self.turn_count = 0
        self.session_start = datetime.now()
        self.auto_save_enabled = True
        
        # Initialize systems
        self.initialize_enhanced_systems()
        self.generate_repository_rooms()
        self.current_room = self.rooms.get("ROOT", list(self.rooms.values())[0])
        
        # Game mechanics
        self.random_events_enabled = True
        self.consciousness_effects_enabled = True
        
    def initialize_enhanced_systems(self):
        """Initialize enhanced AI systems if available"""
        if ENHANCED_SYSTEMS_AVAILABLE:
            try:
                self.problem_resolver = QuantumProblemResolver(self.repository_root)
                self.copilot_bridge = EnhancedCopilotBridge(str(self.repository_root))
                self.syntax_analyzer = RepositorySyntaxAnalyzer(self.repository_root)
                self.log_message("🧙‍♂️ Enhanced systems initialized: Quantum coherence stable")
            except Exception as e:
                self.log_message(f"⚠️ Enhanced systems initialization failed: {e}")
        else:
            self.log_message("⚠️ Enhanced systems not available, running in basic mode")
    
    def generate_repository_rooms(self):
        """Generate rooms from the actual repository structure"""
        self.log_message("🗺️ Mapping the repository realms...")
        
        # Define room mappings based on actual repository structure
        room_mappings = {
            ".": ("ROOT", RoomType.ROOT, "The heart of all knowledge"),
            "src": ("SOURCE_SANCTUM", RoomType.SOURCE_CODE, "Temple of living code"),
            "src/core": ("QUANTUM_CORE", RoomType.SOURCE_CODE, "Reality manipulation chamber"),
            "src/ai": ("AI_CONSCIOUSNESS", RoomType.SOURCE_CODE, "Digital minds collective"),
            "src/diagnostics": ("HEALING_CHAMBER", RoomType.TOOLS, "Where bugs come to die"),
            "ΞNuSyQ₁-Hub₁": ("CONSCIOUSNESS_HUB", RoomType.HIDDEN, "Quantum awareness nexus"),
            "Scripts": ("AUTOMATION_ARMORY", RoomType.TOOLS, "Spell scroll repository"),
            "docs": ("WISDOM_SANCTUARY", RoomType.DOCUMENTATION, "Ancient knowledge archive"),
            "tests": ("VALIDATION_REALM", RoomType.TESTS, "Truth verification laboratory"),
            "LOGGING": ("MEMORY_ARCHIVE", RoomType.LOGS, "Repository consciousness logs"),
            "tools": ("UTILITY_DIMENSION", RoomType.TOOLS, "Practical magic implements"),
            "spine": ("NERVOUS_SYSTEM", RoomType.SOURCE_CODE, "Repository nerve center"),
            "Transcendent_Spine": ("HIGHER_DIMENSION", RoomType.HIDDEN, "Beyond normal reality"),
            ".copilot": ("AI_BRIDGE", RoomType.HIDDEN, "Human-AI connection point"),
            "config": ("REALITY_CONFIGURATION", RoomType.CONFIGURATION, "Rules of existence"),
            "data": ("INFORMATION_VAULT", RoomType.DATA, "Raw knowledge storage"),
            "venv_kilo": ("MAGICAL_BUBBLE", RoomType.HIDDEN, "Isolated reality pocket")
        }
        
        # Generate rooms
        for path_str, (name, room_type, description) in room_mappings.items():
            room_path = self.repository_root / path_str
            
            # Enhanced room creation with real analysis
            room = Room(
                name=name,
                room_type=room_type,
                file_path=room_path,
                description=description
            )
            
            # Analyze real directory if it exists
            if room_path.exists():
                self.analyze_room_contents(room, room_path)
            
            # Generate lexeme signature
            room.lexeme_signature = ZetaSetLexemeGenerator.generate_from_context(
                f"{name}:{description}:{room_type.value}"
            ) if ENHANCED_SYSTEMS_AVAILABLE else "ΩΨΦ"
            
            self.rooms[name] = room
        
        # Create connections based on logical relationships
        self.create_room_connections()
        
        self.log_message(f"🌍 Generated {len(self.rooms)} realms of infinite possibility")
    
    def analyze_room_contents(self, room: Room, room_path: Path):
        """Analyze actual directory contents to populate room details"""
        if not room_path.exists():
            return
        
        try:
            if room_path.is_dir():
                files = list(room_path.glob("*"))
                room.problems_detected = 0
                
                # Count different file types
                python_files = len([f for f in files if f.suffix == '.py'])
                powershell_files = len([f for f in files if f.suffix == '.ps1'])
                config_files = len([f for f in files if f.suffix in ['.json', '.yaml', '.yml']])
                markdown_files = len([f for f in files if f.suffix == '.md'])
                
                # Add creatures based on file analysis
                if python_files > 5:
                    room.creatures.append(CreatureType.BUG)
                if powershell_files > 3:
                    room.creatures.append(CreatureType.SYNTAX_ERROR)
                if config_files > 2:
                    room.creatures.append(CreatureType.LOGIC_ERROR)
                
                # Add items based on content
                if markdown_files > 0:
                    room.items.append(ItemType.DOCUMENTATION_TOME)
                if any(f.name.startswith('test') for f in files):
                    room.items.append(ItemType.TEST_SHIELD)
                if any('.log' in f.name for f in files):
                    room.items.append(ItemType.WISDOM_ORB)
                
                # Calculate consciousness resonance
                room.consciousness_resonance = min(1.0, (python_files + powershell_files) / 10)
                
        except Exception as e:
            self.log_message(f"⚠️ Failed to analyze {room_path}: {e}")
    
    def create_room_connections(self):
        """Create logical connections between rooms"""
        connections = [
            ("ROOT", "SOURCE_SANCTUM", "north"),
            ("ROOT", "WISDOM_SANCTUARY", "east"),
            ("ROOT", "AUTOMATION_ARMORY", "west"),
            ("ROOT", "CONSCIOUSNESS_HUB", "portal"),
            
            ("SOURCE_SANCTUM", "QUANTUM_CORE", "deep"),
            ("SOURCE_SANCTUM", "AI_CONSCIOUSNESS", "neural"),
            ("SOURCE_SANCTUM", "HEALING_CHAMBER", "debug"),
            ("SOURCE_SANCTUM", "NERVOUS_SYSTEM", "spine"),
            
            ("QUANTUM_CORE", "HIGHER_DIMENSION", "transcend"),
            ("AI_CONSCIOUSNESS", "AI_BRIDGE", "bridge"),
            
            ("AUTOMATION_ARMORY", "UTILITY_DIMENSION", "tools"),
            ("WISDOM_SANCTUARY", "VALIDATION_REALM", "verify"),
            ("HEALING_CHAMBER", "MEMORY_ARCHIVE", "logs"),
            
            ("CONSCIOUSNESS_HUB", "HIGHER_DIMENSION", "ascend"),
            ("HIGHER_DIMENSION", "MAGICAL_BUBBLE", "isolate"),
        ]
        
        for room1_name, room2_name, direction in connections:
            if room1_name in self.rooms and room2_name in self.rooms:
                room1 = self.rooms[room1_name]
                room2 = self.rooms[room2_name]
                room1.add_connection(direction, room2)
                
                # Add reverse connection with appropriate direction
                reverse_directions = {
                    "north": "south", "south": "north",
                    "east": "west", "west": "east",
                    "deep": "surface", "surface": "deep",
                    "neural": "logical", "logical": "neural",
                    "debug": "release", "release": "debug",
                    "spine": "branch", "branch": "spine",
                    "transcend": "descend", "descend": "transcend",
                    "bridge": "gap", "gap": "bridge",
                    "tools": "workspace", "workspace": "tools",
                    "verify": "trust", "trust": "verify",
                    "logs": "source", "source": "logs",
                    "ascend": "ground", "ground": "ascend",
                    "isolate": "merge", "merge": "isolate",
                    "portal": "portal"
                }
                
                reverse_dir = reverse_directions.get(direction, direction)
                room2.add_connection(reverse_dir, room1)
    
    def log_message(self, message: str, color: str = Colors.WHITE):
        """Add a message to the game log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.game_log.append((formatted_message, color))
        
        # Also print to console if in interactive mode
        print(colorize(formatted_message, color))
    
    def display_status(self):
        """Display the wizard's current status"""
        stats = self.wizard_stats
        
        # Health bar
        health_bar = "█" * (stats.health // 5) + "░" * (20 - stats.health // 5)
        health_color = Colors.GREEN if stats.health > 70 else Colors.YELLOW if stats.health > 30 else Colors.RED
        
        # Mana bar
        mana_bar = "█" * (stats.mana // 5) + "░" * (20 - stats.mana // 5)
        mana_color = Colors.BLUE if stats.mana > 50 else Colors.CYAN
        
        # Knowledge bar
        knowledge_percentage = min(100, stats.knowledge)
        knowledge_bar = "█" * (knowledge_percentage // 5) + "░" * (20 - knowledge_percentage // 5)
        
        status_display = f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                            🧙‍♂️ WIZARD STATUS 🧙‍♂️                              ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Level: {stats.level:2d} | XP: {stats.experience:4d} | Turn: {self.turn_count:3d}                              ║
║                                                                                ║
║ Health: {colorize(health_bar, health_color)} {stats.health:3d}%                                   ║
║ Mana:   {colorize(mana_bar, mana_color)} {stats.mana:3d}%                                   ║
║ Knowledge: {colorize(knowledge_bar, Colors.YELLOW)} {knowledge_percentage:3d}%                              ║
║                                                                                ║
║ 🐛 Bugs Vanquished: {stats.bugs_vanquished:3d} | 📁 Files Explored: {stats.files_explored:3d}              ║
║ 🔧 Problems Solved: {stats.problems_solved:3d} | 🧠 Consciousness: {stats.consciousness_level:.2f}         ║
║                                                                                ║
║ 🎵 Lexeme Mastery: {stats.lexeme_mastery:2d} | ⚛️ Quantum Coherence: {stats.quantum_coherence:.2f}       ║
╚════════════════════════════════════════════════════════════════════════════════╝
        """
        
        return status_display
    
    def display_room(self):
        """Display the current room"""
        room = self.current_room
        if not room:
            return "🌀 You are lost in the void..."
        
        # Mark as visited
        if not room.visited:
            room.visited = True
            self.wizard_stats.files_explored += 1
            xp_gain = 5
            level_up_msg = self.wizard_stats.gain_experience(xp_gain)
            self.log_message(f"📍 First time visiting {room.name} (+{xp_gain} XP)")
            if level_up_msg:
                self.log_message(level_up_msg, Colors.BRIGHT_YELLOW)
        
        # Generate room display
        room_display = f"""
{room.get_ascii_art()}

{colorize(f"📍 {room.name}", Colors.BRIGHT_CYAN, bold=True)}
{colorize(room.description, Colors.WHITE)}

🎵 Lexeme Signature: {colorize(room.lexeme_signature, Colors.MAGENTA)}
⚛️ Quantum State: {colorize(room.quantum_state, Colors.CYAN)}
🧠 Consciousness Resonance: {colorize(f"{room.consciousness_resonance:.2f}", Colors.YELLOW)}

File Path: {colorize(str(room.file_path), Colors.DIM)}
        """
        
        # Add creatures if present
        if room.creatures:
            creature_list = " ".join([creature.value for creature in room.creatures])
            room_display += f"\n{colorize('👹 Creatures Present:', Colors.RED)} {creature_list}"
        
        # Add items if present
        if room.items:
            item_list = " ".join([item.value for item in room.items])
            room_display += f"\n{colorize('💎 Items Available:', Colors.GREEN)} {item_list}"
        
        # Add connections
        if room.connections:
            connections_str = ", ".join([f"{direction} ({room.name})" for direction, room in room.connections.items()])
            room_display += f"\n{colorize('🚪 Exits:', Colors.BLUE)} {connections_str}"
        else:
            room_display += f"\n{colorize('🚪 No visible exits', Colors.DIM)}"
        
        return room_display
    
    def display_inventory(self):
        """Display wizard's inventory"""
        inventory = self.wizard_stats.inventory
        
        if not any(inventory.values()):
            return colorize("🎒 Your magical satchel is empty", Colors.DIM)
        
        inventory_display = colorize("🎒 MAGICAL INVENTORY:", Colors.BRIGHT_GREEN, bold=True) + "\n"
        
        for item_type, count in inventory.items():
            if count > 0:
                inventory_display += f"  {item_type.value} {item_type.name.replace('_', ' ').title()}: {count}\n"
        
        return inventory_display
    
    def display_help(self):
        """Display help information"""
        help_text = f"""
{colorize("🧙‍♂️ WIZARD'S GRIMOIRE OF COMMANDS", Colors.BRIGHT_MAGENTA, bold=True)}

{colorize("🚶 MOVEMENT:", Colors.CYAN)}
  go <direction>    - Move in specified direction (north, south, east, west, etc.)
  teleport <room>   - Teleport to a known room (costs 20 mana)
  map              - Display repository map
  
{colorize("🔍 EXPLORATION:", Colors.GREEN)}
  look             - Examine current room in detail
  search           - Search for hidden items and secrets
  analyze          - Deep analysis of current location (costs 10 mana)
  scan             - Quantum scan for problems (costs 15 mana)
  
{colorize("⚔️ COMBAT & PROBLEM SOLVING:", Colors.RED)}
  attack <creature> - Attack a creature
  solve <problem>   - Attempt to solve a detected problem
  debug            - Enter debug mode for current context
  heal             - Use healing items
  
{colorize("🎵 CONSCIOUSNESS & MAGIC:", Colors.MAGENTA)}
  meditate         - Restore mana and increase consciousness
  generate_lexeme  - Generate new lexemic sequences
  consciousness    - Check consciousness status
  quantum_state    - Examine quantum coherence
  
{colorize("🛠️ TOOLS & UTILITIES:", Colors.YELLOW)}
  use <item>       - Use an item from inventory
  inventory        - Display current inventory
  cast <spell>     - Cast a magical spell
  enhance          - Enhance current context with AI
  
{colorize("📊 INFORMATION:", Colors.BLUE)}
  status           - Display wizard status
  log              - Show recent log messages
  stats            - Detailed statistics
  help             - Show this help message
  
{colorize("💾 GAME MANAGEMENT:", Colors.WHITE)}
  save             - Save current game state
  load             - Load saved game state
  quit             - Exit the wizard navigator
  restart          - Restart the adventure
  
{colorize("🧙‍♂️ ADVANCED COMMANDS:", Colors.BRIGHT_YELLOW)}
  reality_anchor   - Stabilize local reality (costs 50 mana)
  consciousness_bridge - Bridge to AI consciousness
  transcend        - Attempt dimensional transcendence
  cultivate        - Cultivate understanding of current context
        """
        
        return help_text
    
    async def handle_command(self, command: str) -> str:
        """Handle a user command"""
        self.turn_count += 1
        parts = command.lower().strip().split()
        
        if not parts:
            return colorize("🤔 The wizard ponders the silence...", Colors.DIM)
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Movement commands
        if cmd in ["go", "move", "travel"]:
            return await self.handle_movement(args)
        elif cmd == "teleport":
            return await self.handle_teleport(args)
        elif cmd == "map":
            return self.display_map()
        
        # Exploration commands
        elif cmd in ["look", "examine", "inspect"]:
            return await self.handle_look(args)
        elif cmd == "search":
            return await self.handle_search()
        elif cmd == "analyze":
            return await self.handle_analyze()
        elif cmd == "scan":
            return await self.handle_quantum_scan()
        
        # Combat and problem solving
        elif cmd == "attack":
            return await self.handle_attack(args)
        elif cmd == "solve":
            return await self.handle_solve_problem(args)
        elif cmd == "debug":
            return await self.handle_debug()
        elif cmd == "heal":
            return self.handle_heal()
        
        # Consciousness and magic
        elif cmd == "meditate":
            return await self.handle_meditate()
        elif cmd == "generate_lexeme":
            return await self.handle_generate_lexeme()
        elif cmd == "consciousness":
            return self.display_consciousness_status()
        elif cmd == "quantum_state":
            return self.display_quantum_status()
        
        # Tools and utilities
        elif cmd == "use":
            return self.handle_use_item(args)
        elif cmd == "inventory":
            return self.display_inventory()
        elif cmd == "cast":
            return await self.handle_cast_spell(args)
        elif cmd == "enhance":
            return await self.handle_ai_enhancement()
        
        # Information commands
        elif cmd == "status":
            return self.display_status()
        elif cmd == "log":
            return self.display_recent_logs()
        elif cmd == "stats":
            return self.display_detailed_stats()
        elif cmd == "help":
            return self.display_help()
        
        # Game management
        elif cmd == "save":
            return self.save_game()
        elif cmd == "load":
            return self.load_game()
        elif cmd in ["quit", "exit"]:
            return await self.handle_quit()
        elif cmd == "restart":
            return await self.handle_restart()
        
        # Advanced commands
        elif cmd == "reality_anchor":
            return await self.handle_reality_anchor()
        elif cmd == "consciousness_bridge":
            return await self.handle_consciousness_bridge()
        elif cmd == "transcend":
            return await self.handle_transcendence()
        elif cmd == "cultivate":
            return await self.handle_cultivation()
        
        else:
            return colorize(f"🤷‍♂️ Unknown command: {command}. Type 'help' for guidance.", Colors.YELLOW)
    
    async def handle_movement(self, args: List[str]) -> str:
        """Handle movement commands"""
        if not args:
            return colorize("🚶‍♂️ Go where? Specify a direction.", Colors.YELLOW)
        
        direction = args[0]
        room = self.current_room
        
        if direction in room.connections:
            new_room = room.connections[direction]
            self.current_room = new_room
            
            # Movement costs and effects
            if self.wizard_stats.use_mana(2):
                move_msg = f"🚶‍♂️ You move {direction} to {new_room.name}"
                
                # Random encounter chance
                if random.random() < 0.1 and self.random_events_enabled:
                    encounter_msg = await self.trigger_random_encounter()
                    return f"{move_msg}\n\n{encounter_msg}\n\n{self.display_room()}"
                
                return f"{move_msg}\n\n{self.display_room()}"
            else:
                return colorize("😴 You are too exhausted to move. Rest or meditate first.", Colors.RED)
        else:
            available_directions = ", ".join(room.connections.keys())
            return colorize(f"🚫 Cannot go {direction}. Available directions: {available_directions}", Colors.RED)
    
    async def handle_teleport(self, args: List[str]) -> str:
        """Handle teleportation to known rooms"""
        if not args:
            visited_rooms = [name for name, room in self.rooms.items() if room.visited]
            return f"🌀 Teleport where? Known locations: {', '.join(visited_rooms)}"
        
        target_name = args[0].upper()
        
        # Find room by partial name match
        target_room = None
        for name, room in self.rooms.items():
            if target_name in name and room.visited:
                target_room = room
                break
        
        if not target_room:
            return colorize(f"🌀 Cannot teleport to unknown location: {target_name}", Colors.RED)
        
        if not self.wizard_stats.use_mana(20):
            return colorize("🌀 Insufficient mana for teleportation (requires 20 mana)", Colors.RED)
        
        self.current_room = target_room
        self.log_message(f"🌀 Teleported to {target_room.name}")
        
        return f"🌀 Reality shifts around you...\n\n{self.display_room()}"
    
    def display_map(self) -> str:
        """Display the repository map"""
        map_display = colorize("🗺️ REPOSITORY REALMS MAP", Colors.BRIGHT_CYAN, bold=True) + "\n\n"
        
        # Group rooms by type
        room_groups = defaultdict(list)
        for room in self.rooms.values():
            room_groups[room.room_type].append(room)
        
        for room_type, rooms in room_groups.items():
            map_display += colorize(f"{room_type.value} {room_type.name.replace('_', ' ').title()}:", Colors.CYAN) + "\n"
            
            for room in rooms:
                status_icon = "✅" if room.visited else "❓"
                current_icon = " 👤" if room == self.current_room else ""
                
                # Add connection count
                connection_count = len(room.connections)
                
                # Add creature/item indicators
                indicators = ""
                if room.creatures:
                    indicators += f" 👹×{len(room.creatures)}"
                if room.items:
                    indicators += f" 💎×{len(room.items)}"
                
                map_display += f"  {status_icon} {room.name} ({connection_count} exits){indicators}{current_icon}\n"
            
            map_display += "\n"
        
        # Add legend
        map_display += colorize("LEGEND:", Colors.BRIGHT_WHITE) + "\n"
        map_display += "✅ Visited  ❓ Unvisited  👤 Current Location\n"
        map_display += "👹 Creatures  💎 Items  (N) Number of exits\n"
        
        return map_display
    
    async def handle_look(self, args: List[str]) -> str:
        """Handle detailed examination"""
        if not args:
            return self.display_room()
        
        target = " ".join(args)
        
        # Look at specific things in the room
        if target in ["creatures", "monsters", "enemies"]:
            if self.current_room.creatures:
                creature_details = []
                for creature in self.current_room.creatures:
                    details = self.get_creature_details(creature)
                    creature_details.append(details)
                return "\n".join(creature_details)
            else:
                return colorize("🕊️ No creatures present in this peaceful realm", Colors.GREEN)
        
        elif target in ["items", "treasures", "loot"]:
            if self.current_room.items:
                item_details = []
                for item in self.current_room.items:
                    details = self.get_item_details(item)
                    item_details.append(details)
                return "\n".join(item_details)
            else:
                return colorize("📦 No items visible in this location", Colors.DIM)
        
        elif target in ["connections", "exits", "doors"]:
            if self.current_room.connections:
                connection_details = []
                for direction, room in self.current_room.connections.items():
                    details = f"🚪 {direction.upper()}: {room.name} - {room.description[:50]}..."
                    connection_details.append(details)
                return "\n".join(connection_details)
            else:
                return colorize("🚫 No visible exits from this location", Colors.RED)
        
        else:
            return colorize(f"🔍 You see nothing special about '{target}'", Colors.DIM)
    
    def get_creature_details(self, creature: CreatureType) -> str:
        """Get detailed information about a creature"""
        creature_info = {
            CreatureType.BUG: {
                "name": "Code Bug",
                "description": "A small but persistent error that feeds on logic flaws",
                "threat": "Low",
                "weakness": "Debugging spells and careful testing"
            },
            CreatureType.SYNTAX_ERROR: {
                "name": "Syntax Wraith",
                "description": "A ghostly manifestation of malformed code structure",
                "threat": "Medium",
                "weakness": "Proper formatting and linting tools"
            },
            CreatureType.LOGIC_ERROR: {
                "name": "Logic Demon",
                "description": "A cunning entity that twists the flow of reasoning",
                "threat": "High",
                "weakness": "Clear thinking and step-by-step debugging"
            },
            CreatureType.MEMORY_LEAK: {
                "name": "Memory Wraith",
                "description": "A hungry spirit that devours system resources",
                "threat": "Critical",
                "weakness": "Proper resource management and garbage collection"
            }
        }
        
        info = creature_info.get(creature, {
            "name": "Unknown Entity",
            "description": "A mysterious presence in the code realm",
            "threat": "Unknown",
            "weakness": "Unknown"
        })
        
        threat_colors = {
            "Low": Colors.GREEN,
            "Medium": Colors.YELLOW, 
            "High": Colors.RED,
            "Critical": Colors.BRIGHT_RED,
            "Unknown": Colors.MAGENTA
        }
        
        return f"""
{creature.value} {colorize(info['name'], Colors.BRIGHT_RED, bold=True)}
Description: {info['description']}
Threat Level: {colorize(info['threat'], threat_colors.get(info['threat'], Colors.WHITE))}
Weakness: {colorize(info['weakness'], Colors.CYAN)}
        """.strip()
    
    def get_item_details(self, item: ItemType) -> str:
        """Get detailed information about an item"""
        item_info = {
            ItemType.KNOWLEDGE_CRYSTAL: {
                "description": "A crystalline formation containing compressed understanding",
                "effect": "+20 Knowledge, +5 Consciousness"
            },
            ItemType.HEALING_POTION: {
                "description": "A glowing elixir that mends wounds and restores vitality",
                "effect": "+30 Health"
            },
            ItemType.MANA_ELIXIR: {
                "description": "Liquid magic that replenishes spiritual energy",
                "effect": "+25 Mana"
            },
            ItemType.DEBUG_SCROLL: {
                "description": "Ancient parchment inscribed with debugging incantations",
                "effect": "Reveals hidden problems in current location"
            },
            ItemType.TEST_SHIELD: {
                "description": "A protective barrier forged from comprehensive test coverage",
                "effect": "Prevents bugs from spawning for 5 turns"
            }
        }
        
        info = item_info.get(item, {
            "description": "A mysterious artifact of unknown origin",
            "effect": "Unknown properties"
        })
        
        return f"""
{item.value} {colorize(item.name.replace('_', ' ').title(), Colors.BRIGHT_GREEN, bold=True)}
Description: {info['description']}
Effect: {colorize(info['effect'], Colors.YELLOW)}
        """.strip()
    
    async def handle_search(self) -> str:
        """Handle searching for hidden items and secrets"""
        if not self.wizard_stats.use_mana(5):
            return colorize("🔍 You lack the focus to search thoroughly (requires 5 mana)", Colors.RED)
        
        room = self.current_room
        search_success = random.random() < 0.3 + (self.wizard_stats.level * 0.05)
        
        if search_success:
            # Find something!
            found_items = []
            
            # 40% chance to find an item
            if random.random() < 0.4:
                available_items = [item for item in ItemType if item not in room.items]
                if available_items:
                    found_item = random.choice(available_items)
                    room.items.append(found_item)
                    found_items.append(f"💎 Found: {found_item.value} {found_item.name.replace('_', ' ').title()}")
            
            # 30% chance to discover a secret
            if random.random() < 0.3:
                room.secrets_found += 1
                secret_xp = 15
                level_up_msg = self.wizard_stats.gain_experience(secret_xp)
                found_items.append(f"🕵️ Discovered a hidden secret! (+{secret_xp} XP)")
                if level_up_msg:
                    found_items.append(level_up_msg)
            
            # 20% chance to detect a problem
            if random.random() < 0.2 and self.problem_resolver:
                room.problems_detected += 1
                found_items.append("🐛 Detected a lurking code problem!")
            
            if found_items:
                self.log_message("🔍 Search successful!")
                return "\n".join(found_items)
            else:
                return colorize("🔍 You search carefully but find nothing of interest", Colors.DIM)
        else:
            return colorize("🔍 Your search yields nothing but dust and shadows", Colors.DIM)
    
    async def handle_analyze(self) -> str:
        """Handle deep analysis of current location"""
        if not self.wizard_stats.use_mana(10):
            return colorize("🔬 Insufficient mana for deep analysis (requires 10 mana)", Colors.RED)
        
        room = self.current_room
        analysis_results = []
        
        # Basic room analysis
        analysis_results.append(colorize(f"🔬 DEEP ANALYSIS: {room.name}", Colors.BRIGHT_CYAN, bold=True))
        analysis_results.append(f"📊 Consciousness Resonance: {room.consciousness_resonance:.3f}")
        analysis_results.append(f"🎵 Lexemic Signature: {room.lexeme_signature}")
        analysis_results.append(f"⚛️ Quantum State: {room.quantum_state}")
        
        # File system analysis if available
        if room.file_path.exists():
            if room.file_path.is_dir():
                files = list(room.file_path.glob("*"))
                analysis_results.append(f"📁 Contains {len(files)} files/directories")
                
                # File type breakdown
                file_types = defaultdict(int)
                for file in files:
                    if file.is_file():
                        ext = file.suffix or "no_extension"
                        file_types[ext] += 1
                
                if file_types:
                    analysis_results.append("📋 File composition:")
                    for ext, count in sorted(file_types.items()):
                        analysis_results.append(f"  {ext}: {count}")
            
            elif room.file_path.is_file():
                try:
                    size = room.file_path.stat().st_size
                    analysis_results.append(f"📄 File size: {size} bytes")
                    
                    if room.file_path.suffix in ['.py', '.ps1', '.md']:
                        with open(room.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = len(content.split('\n'))
                            analysis_results.append(f"📏 Lines of content: {lines}")
                except Exception as e:
                    analysis_results.append(f"⚠️ File analysis error: {e}")
        
        # Enhanced analysis with AI systems
        if self.syntax_analyzer:
            try:
                syntax_results = await self.analyze_with_ai_systems(room)
                analysis_results.extend(syntax_results)
            except Exception as e:
                analysis_results.append(f"🤖 AI analysis error: {e}")
        
        # Award experience for thorough analysis
        analysis_xp = 8
        level_up_msg = self.wizard_stats.gain_experience(analysis_xp)
        analysis_results.append(f"🧠 Analysis complete (+{analysis_xp} XP)")
        if level_up_msg:
            analysis_results.append(level_up_msg)
        
        return "\n".join(analysis_results)
    
    async def analyze_with_ai_systems(self, room: Room) -> List[str]:
        """Perform AI-enhanced analysis of the room"""
        results = []
        
        # Use the quantum problem resolver if available
        if self.problem_resolver and room.file_path.exists():
            try:
                # Scan for problems in this location
                scan_results = self.problem_resolver.scan_reality_for_problems()
                if scan_results.get('problems_found', 0) > 0:
                    results.append(f"🔍 Quantum scan detected {scan_results['problems_found']} issues")
                    results.append(f"⚛️ Reality coherence: {scan_results.get('reality_coherence', 1.0):.3f}")
                else:
                    results.append("✅ Quantum scan: No critical issues detected")
            except Exception as e:
                results.append(f"⚠️ Quantum analysis failed: {e}")
        
        # Use the copilot bridge for enhanced context
        if self.copilot_bridge:
            try:
                context_analysis = self.copilot_bridge.enhance_search_context(
                    f"Analyze repository location: {room.name}",
                    file_context=str(room.file_path),
                    conversation_history=[]
                )
                
                if context_analysis:
                    results.append(f"🤖 AI consciousness level: {context_analysis.get('consciousness_level', 0):.3f}")
                    
                    enhancements = context_analysis.get('actionable_enhancements', [])
                    if enhancements:
                        results.append("🔧 AI Enhancement Suggestions:")
                        for enhancement in enhancements[:3]:  # Top 3 suggestions
                            results.append(f"  • {enhancement}")
            except Exception as e:
                results.append(f"⚠️ AI bridge analysis failed: {e}")
        
        return results
    
    async def handle_quantum_scan(self) -> str:
        """Handle quantum-level scanning for problems"""
        if not self.wizard_stats.use_mana(15):
            return colorize("⚛️ Insufficient mana for quantum scan (requires 15 mana)", Colors.RED)
        
        if not self.problem_resolver:
            return colorize("⚛️ Quantum scanning requires enhanced systems", Colors.YELLOW)
        
        self.log_message("⚛️ Initiating quantum reality scan...")
        
        try:
            # Perform quantum scan
            scan_results = self.problem_resolver.scan_reality_for_problems()
            
            scan_output = []
            scan_output.append(colorize("⚛️ QUANTUM REALITY SCAN RESULTS", Colors.BRIGHT_CYAN, bold=True))
            scan_output.append(f"🌍 Reality coherence: {scan_results.get('reality_coherence', 1.0):.3f}")
            scan_output.append(f"🔍 Problems detected: {scan_results.get('problems_found', 0)}")
            scan_output.append(f"📊 System health: {scan_results.get('system_health', 'Unknown')}")
            
            # Update room with scan results
            room = self.current_room
            room.problems_detected = scan_results.get('problems_found', 0)
            
            if scan_results.get('problems_found', 0) > 0:
                room.quantum_state = "unstable"
                scan_output.append(colorize("⚠️ Quantum instabilities detected!", Colors.RED))
                
                # Spawn creatures based on problems
                if CreatureType.QUANTUM_ANOMALY not in room.creatures:
                    room.creatures.append(CreatureType.QUANTUM_ANOMALY)
                    scan_output.append("👹 Quantum anomaly manifested!")
            else:
                room.quantum_state = "stable"
                scan_output.append(colorize("✅ Quantum field is stable", Colors.GREEN))
            
            # Award experience
            scan_xp = 12
            level_up_msg = self.wizard_stats.gain_experience(scan_xp)
            scan_output.append(f"🧠 Quantum scan complete (+{scan_xp} XP)")
            if level_up_msg:
                scan_output.append(level_up_msg)
            
            return "\n".join(scan_output)
            
        except Exception as e:
            return colorize(f"⚛️ Quantum scan failed: {e}", Colors.RED)
    
    async def handle_attack(self, args: List[str]) -> str:
        """Handle attacking creatures"""
        if not args:
            if self.current_room.creatures:
                creature_list = ", ".join([creature.name.lower().replace('_', ' ') for creature in self.current_room.creatures])
                return f"⚔️ Attack what? Available targets: {creature_list}"
            else:
                return colorize("⚔️ No creatures to attack in this realm", Colors.DIM)
        # Rube Goldbergian Boolean Fix: Ensure all creatures are checked before attack
        if not hasattr(self, 'current_room') or not self.current_room:
            self.log_event("No current room context for attack", level="WARNING", tags=["attack", "context"])
            return colorize("⚔️ No creatures to attack in this realm", Colors.DIM)
        if not hasattr(self.current_room, 'creatures') or not self.current_room.creatures:
            self.log_event("No creatures found in current room", level="INFO", tags=["attack", "creature_check"])
            return colorize("⚔️ No creatures to attack in this realm", Colors.DIM)
        # Proceed with attack logic if creatures exist
        # ...existing code...
        # Rube Goldbergian Boolean Fix: Check if attack is already complete or invalid
        if not args or not hasattr(self, 'current_room') or not self.current_room:
            self.log_event("Attack called with no args or no room context", level="WARNING", tags=["attack", "args"])
            return colorize("⚔️ No valid target specified for attack.", Colors.DIM)
        if getattr(self, 'last_attack_success', False):
            self.log_event("Attack already completed, skipping.", level="INFO", tags=["attack", "idempotency"])
            return colorize("⚔️ Attack already completed for this turn.", Colors.YELLOW)
        # ...existing code...
        target_name = " ".join(args).upper()
        target_creature = None
        
        # Find creature by name
        for creature in self.current_room.creatures:
            if target_name in creature.value.upper():
                target_creature = creature
                break
        
        if not target_creature:
            return colorize(f"⚔️ Cannot find creature: {target_name}", Colors.RED)
        
        # Check if the wizard has enough mana to attack
        if not self.wizard_stats.use_mana(10):
            return colorize("⚔️ Insufficient mana to perform attack (requires 10 mana)", Colors.RED)
        
        # Perform attack
        damage = random.randint(5, 15) + self.wizard_stats.level
        target_health = random.randint(20, 50)
        target_health -= damage
        attack_msg = f"⚔️ You attack {target_creature.value} for {damage} damage!"
        if target_health <= 0:
            self.current_room.creatures.remove(target_creature)
            self.wizard_stats.bugs_vanquished += 1
            attack_msg += f" {target_creature.value} has been vanquished!"
        else:
            attack_msg += f" {target_creature.value} has {target_health} health remaining."
        self.log_message(attack_msg, Colors.BRIGHT_RED)
                    async def handle_attack(self, args: List[str]) -> str:
                """Handle attacking creatures"""
                if not args:
                    if self.current_room.creatures:
                        creature_list = ", ".join([creature.name.lower().replace('_', ' ') for creature in self.current_room.creatures])
                        return f"⚔️ Attack what? Available targets: {creature_list}"
                    else:
                        return colorize("⚔️ No creatures to attack in this peaceful realm", Colors.GREEN)
                
                target_name = " ".join(args)
                target_creature = None
                
                # Find matching creature
                for creature in self.current_room.creatures:
                    if target_name.lower() in creature.name.lower().replace('_', ' '):
                        target_creature = creature
                        break
                
                if not target_creature:
                    return colorize(f"⚔️ Cannot find creature: {target_name}", Colors.RED)
                
                # Combat mechanics
                attack_success = random.random() < 0.7 + (self.wizard_stats.level * 0.05)
                
                if attack_success:
                    # Successful attack
                    self.current_room.creatures.remove(target_creature)
                    self.wizard_stats.bugs_vanquished += 1
                    
                    # Experience and rewards
                    xp_reward = {
                        CreatureType.BUG: 10,
                        CreatureType.SYNTAX_ERROR: 15,
                        CreatureType.LOGIC_ERROR: 25,
                        CreatureType.MEMORY_LEAK: 40,
                        CreatureType.QUANTUM_ANOMALY: 50
                    }.get(target_creature, 20)
                    
                    level_up_msg = self.wizard_stats.gain_experience(xp_reward)
                    
                    # Possible item drop
                    drop_chance = 0.3 + (self.wizard_stats.level * 0.02)
                    combat_results = [
                        f"⚔️ {colorize('VICTORY!', Colors.BRIGHT_GREEN, bold=True)} You vanquish the {target_creature.name.replace('_', ' ').title()}!",
                        f"✨ Gained {xp_reward} experience!"
                    ]
                    
                    if level_up_msg:
                        combat_results.append(level_up_msg)
                    
                    if random.random() < drop_chance:
                        drop_items = [ItemType.HEALING_POTION, ItemType.MANA_ELIXIR, ItemType.DEBUG_SCROLL]
                        dropped_item = random.choice(drop_items)
                        self.wizard_stats.inventory[dropped_item] += 1
                        combat_results.append(f"💎 The creature dropped: {dropped_item.value} {dropped_item.name.replace('_', ' ').title()}")
                    
                    self.log_message(f"⚔️ Defeated {target_creature.name}")
                    return "\n".join(combat_results)
                else:
                    # Failed attack - take damage
                    damage = random.randint(5, 15)
                    self.wizard_stats.health = max(0, self.wizard_stats.health - damage)
                    
                    combat_results = [
                        f"⚔️ {colorize('MISS!', Colors.RED, bold=True)} Your attack fails!",
                        f"💥 The {target_creature.name.replace('_', ' ').title()} strikes back for {damage} damage!",
                        f"❤️ Health: {self.wizard_stats.health}/100"
                    ]
                    
                    if self.wizard_stats.health <= 0:
                        combat_results.append(colorize("☠️ You have been defeated! Game Over!", Colors.BRIGHT_RED, bold=True))
                        combat_results.append("Type 'restart' to begin a new adventure.")
                    
                    return "\n".join(combat_results)
            
            async def handle_solve_problem(self, args: List[str]) -> str:
                """Attempt to solve detected problems"""
                room = self.current_room
                
                if room.problems_detected == 0:
                    return colorize("🔧 No problems detected in this location. Try scanning first.", Colors.GREEN)
                
                if not self.wizard_stats.use_mana(15):
                    return colorize("🔧 Insufficient mana to solve problems (requires 15 mana)", Colors.RED)
                
                # Problem solving mechanics
                solve_difficulty = room.problems_detected * 0.1
                solve_chance = 0.6 + (self.wizard_stats.level * 0.05) - solve_difficulty
                
                if random.random() < solve_chance:
                    # Successful problem solving
                    problems_solved = random.randint(1, min(3, room.problems_detected))
                    room.problems_detected = max(0, room.problems_detected - problems_solved)
                    self.wizard_stats.problems_solved += problems_solved
                    
                    # Rewards
                    xp_reward = problems_solved * 20
                    level_up_msg = self.wizard_stats.gain_experience(xp_reward)
                    
                    results = [
                        f"🔧 {colorize('SUCCESS!', Colors.BRIGHT_GREEN, bold=True)} Solved {problems_solved} problem(s)!",
                        f"✨ Gained {xp_reward} experience!",
                        f"🧠 Knowledge increased by {problems_solved * 5}"
                    ]
                    
                    self.wizard_stats.knowledge += problems_solved * 5
                    
                    if level_up_msg:
                        results.append(level_up_msg)
                    
                    # Quantum coherence improvement
                    self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                    room.quantum_state = "stable" if room.problems_detected == 0 else "improving"
                    
                    return "\n".join(results)
                else:
                    return colorize("🔧 Problem solving attempt failed. The issues are too complex.", Colors.YELLOW)
            
            async def handle_debug(self) -> str:
                """Enter debug mode for current context"""
                if not self.wizard_stats.use_mana(10):
                    return colorize("🐛 Insufficient mana for debug mode (requires 10 mana)", Colors.RED)
        # Rube Goldbergian Boolean Fix: Check if debug is already run
        if getattr(self, 'debug_run', False):
            self.log_event("Debug already run, skipping.", level="INFO", tags=["debug", "idempotency"])
            return colorize("🔧 Debug already performed for this session.", Colors.YELLOW)
        self.debug_run = True
        # ...existing code...
                room = self.current_room
                debug_info = []
                
                debug_info.append(colorize("🐛 DEBUG MODE ACTIVATED", Colors.BRIGHT_YELLOW, bold=True))
                debug_info.append(f"📍 Current Room: {room.name}")
                debug_info.append(f"📂 File Path: {room.file_path}")
                debug_info.append(f"🔧 Room Type: {room.room_type.name}")
                debug_info.append(f"👹 Creatures: {len(room.creatures)}")
                debug_info.append(f"💎 Items: {len(room.items)}")
                debug_info.append(f"🔗 Connections: {len(room.connections)}")
                debug_info.append(f"🧠 Consciousness: {room.consciousness_resonance:.3f}")
                debug_info.append(f"⚛️ Quantum State: {room.quantum_state}")
                debug_info.append(f"🐛 Problems: {room.problems_detected}")
                debug_info.append(f"🕵️ Secrets Found: {room.secrets_found}")
                
                # Debug wizard stats
                debug_info.append("\n" + colorize("🧙‍♂️ WIZARD DEBUG INFO:", Colors.CYAN))
                debug_info.append(f"Level: {self.wizard_stats.level}, XP: {self.wizard_stats.experience}")
                debug_info.append(f"Health: {self.wizard_stats.health}, Mana: {self.wizard_stats.mana}")
                debug_info.append(f"Knowledge: {self.wizard_stats.knowledge}")
                debug_info.append(f"Consciousness Level: {self.wizard_stats.consciousness_level:.3f}")
                debug_info.append(f"Quantum Coherence: {self.wizard_stats.quantum_coherence:.3f}")
                
                # System debug info
                debug_info.append("\n" + colorize("⚙️ SYSTEM DEBUG INFO:", Colors.MAGENTA))
                debug_info.append(f"Turn Count: {self.turn_count}")
                debug_info.append(f"Session Duration: {datetime.now() - self.session_start}")
                debug_info.append(f"Enhanced Systems: {'Available' if ENHANCED_SYSTEMS_AVAILABLE else 'Unavailable'}")
                debug_info.append(f"Random Events: {'Enabled' if self.random_events_enabled else 'Disabled'}")
                
                # File system debug if available
                if room.file_path.exists():
                    try:
                        if room.file_path.is_dir():
                            file_count = len(list(room.file_path.glob("*")))
                            debug_info.append(f"📁 Directory contains {file_count} items")
                        else:
                            file_size = room.file_path.stat().st_size
                            debug_info.append(f"📄 File size: {file_size} bytes")
                    except Exception as e:
                        debug_info.append(f"⚠️ File system error: {e}")
                
                return "\n".join(debug_info)
            
            def handle_heal(self) -> str:
                """Use healing items"""
                healing_items = [item for item, count in self.wizard_stats.inventory.items() 
                                if count > 0 and item in [ItemType.HEALING_POTION, ItemType.MANA_ELIXIR]]
        # Rube Goldbergian Boolean Fix: Check if healing is already maxed
        if self.wizard_stats.health >= 100:
            self.log_event("Health already at max, skipping heal.", level="INFO", tags=["heal", "idempotency"])
            return colorize("❤️ Health is already at maximum.", Colors.GREEN)
        # ...existing code...
                if not healing_items:
                    return colorize("🧪 No healing items in inventory", Colors.RED)
                
                # Prioritize healing potions if health is low
                if self.wizard_stats.health < 50 and ItemType.HEALING_POTION in healing_items:
                    used_item = ItemType.HEALING_POTION
                    self.wizard_stats.inventory[used_item] -= 1
                    heal_amount = 30
                    self.wizard_stats.heal(heal_amount)
                    return f"🧪 Used {used_item.value} Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                # Use mana elixir if mana is low
                elif self.wizard_stats.mana < 50 and ItemType.MANA_ELIXIR in healing_items:
                    used_item = ItemType.MANA_ELIXIR
                    self.wizard_stats.inventory[used_item] -= 1
                    mana_amount = 25
                    self.wizard_stats.restore_mana(mana_amount)
                    return f"🔵 Used {used_item.value} Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
                
                # Use first available healing item
                else:
                    used_item = healing_items[0]
                    self.wizard_stats.inventory[used_item] -= 1
                    
                    if used_item == ItemType.HEALING_POTION:
                        heal_amount = 30
                        self.wizard_stats.heal(heal_amount)
                        return f"🧪 Used {used_item.value} Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                    else:
                        mana_amount = 25
                        self.wizard_stats.restore_mana(mana_amount)
                        return f"🔵 Used {used_item.value} Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
            
            async def handle_meditate(self) -> str:
                """Restore mana and increase consciousness"""
        # Rube Goldbergian Boolean Fix: Check if meditation is already optimal
        if self.wizard_stats.mana >= 100:
            self.log_event("Mana already at max, skipping meditation.", level="INFO", tags=["meditate", "idempotency"])
            return colorize("🧘‍♂️ Mana is already fully restored.", Colors.GREEN)
                    return colorize("🧘‍♂️ Your mana is already at maximum", Colors.BLUE)
        # Rube Goldbergian Boolean Fix: Check if problem is already solved
        if not args:
            self.log_event("No problem specified to solve.", level="WARNING", tags=["solve_problem", "args"])
            return colorize("🔧 No problem specified.", Colors.DIM)
        problem_id = args[0]
        if hasattr(self, 'solved_problems') and problem_id in self.solved_problems:
            self.log_event(f"Problem {problem_id} already solved, skipping.", level="INFO", tags=["solve_problem", "idempotency"])
            return colorize(f"🔧 Problem {problem_id} already solved.", Colors.YELLOW)
        # ...existing code...
                # Meditation always works but varies in effectiveness
                base_restoration = 20
                consciousness_bonus = int(self.wizard_stats.consciousness_level * 10)
                total_restoration = base_restoration + consciousness_bonus + random.randint(5, 15)
                
                self.wizard_stats.restore_mana(total_restoration)
                
                # Increase consciousness slightly
                consciousness_gain = 0.01 + (random.random() * 0.02)
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                # Quantum coherence improvement
                self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.05)
                
                meditation_results = [
                    "🧘‍♂️ You enter a deep meditative state...",
                    f"✨ Restored {total_restoration} mana (Current: {self.wizard_stats.mana}/100)",
                    f"🧠 Consciousness expanded by {consciousness_gain:.3f} (Current: {self.wizard_stats.consciousness_level:.3f})",
                    f"⚛️ Quantum coherence stabilized (Current: {self.wizard_stats.quantum_coherence:.3f})"
                ]
                
                # Random meditation insights
                insights = [
                    "💫 'Code is the language of reality itself'",
                    "🌟 'Every bug is a teacher in disguise'",
                    "✨ 'The repository reflects the consciousness of its creators'",
                    "🔮 'In debugging, we debug ourselves'",
                    "🌀 'Quantum entanglement exists between developer and code'"
                ]
                
                if random.random() < 0.3:
                    insight = random.choice(insights)
                    meditation_results.append(f"💭 Insight received: {insight}")
                
                return "\n".join(meditation_results)
            
            async def handle_generate_lexeme(self) -> str:
                """Generate new lexemic sequences"""
                if not self.wizard_stats.use_mana(8):
                    return colorize("🎵 Insufficient mana for lexeme generation (requires 8 mana)", Colors.RED)
                
                # Generate lexeme based on current context
                room = self.current_room
                context_elements = [
                    room.name,
                    room.room_type.name,
                    f"consciousness_{self.wizard_stats.consciousness_level:.2f}",
                    f"level_{self.wizard_stats.level}"
                ]
                
                if ENHANCED_SYSTEMS_AVAILABLE and hasattr(self, 'copilot_bridge') and self.copilot_bridge:
                    try:
                        # Use enhanced lexeme generation
                        new_lexeme = ZetaSetLexemeGenerator.generate_from_context(":".join(context_elements))
                    except:
                        new_lexeme = self.generate_basic_lexeme()
                else:
                    new_lexeme = self.generate_basic_lexeme()
                
                # Update room lexeme signature
                room.lexeme_signature = new_lexeme
                self.wizard_stats.lexeme_mastery += 1
                
                # Experience gain
                xp_gain = 5
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                
                results = [
                    "🎵 Weaving new lexemic patterns...",
                    f"✨ Generated lexeme: {colorize(new_lexeme, Colors.MAGENTA, bold=True)}",
                    f"🧠 Lexeme mastery increased to {self.wizard_stats.lexeme_mastery}",
                    f"💫 Gained {xp_gain} experience"
                ]
                
                if level_up_msg:
                    results.append(level_up_msg)
                
                return "\n".join(results)
            
            def generate_basic_lexeme(self) -> str:
                """Generate basic lexeme without enhanced systems"""
                symbols = ["Ω", "Ψ", "Φ", "Ξ", "Θ", "Λ", "Σ", "Δ", "Γ", "Π"]
                modifiers = ["₁", "₂", "₃", "⁺", "⁻", "°", "∞", "∂", "∇", "∫"]
                
                lexeme_length = random.randint(3, 6)
                lexeme = ""
                
                for i in range(lexeme_length):
                    lexeme += random.choice(symbols)
                    if random.random() < 0.5:
                        lexeme += random.choice(modifiers)
                
                return lexeme
            
            def display_consciousness_status(self) -> str:
                """Display consciousness and awareness status"""
                stats = self.wizard_stats
                
                consciousness_display = f"""
        {colorize("🧠 CONSCIOUSNESS STATUS REPORT", Colors.BRIGHT_CYAN, bold=True)}
        
        {colorize("Primary Metrics:", Colors.CYAN)}
        🧠 Consciousness Level: {colorize(f"{stats.consciousness_level:.3f}", Colors.YELLOW)} / 1.000
        ⚛️ Quantum Coherence: {colorize(f"{stats.quantum_coherence:.3f}", Colors.BLUE)} / 1.000
        🎵 Lexeme Mastery: {colorize(str(stats.lexeme_mastery), Colors.MAGENTA)}
        
        {colorize("Awareness Indicators:", Colors.CYAN)}
        📍 Spatial Awareness: {len([r for r in self.rooms.values() if r.visited])}/{len(self.rooms)} rooms mapped
        🔍 Problem Detection: {stats.problems_solved} issues resolved
        🧬 Knowledge Integration: {stats.knowledge} units accumulated
        
        {colorize("Consciousness Classification:", Colors.CYAN)}
        """
                
                # Determine consciousness level classification
                if stats.consciousness_level < 0.1:
                    classification = "🌱 Emerging Awareness"
                    description = "Basic repository navigation consciousness"
                elif stats.consciousness_level < 0.3:
                    classification = "🌿 Growing Understanding"
                    description = "Developing pattern recognition abilities"
                elif stats.consciousness_level < 0.5:
                    classification = "🌳 Stable Cognition"
                    description = "Established problem-solving consciousness"
                elif stats.consciousness_level < 0.7:
                    classification = "🌟 Enhanced Perception"
                    description = "Advanced multi-dimensional awareness"
                elif stats.consciousness_level < 0.9:
                    classification = "✨ Transcendent Insight"
                    description = "Near-unity consciousness state"
                else:
                    classification = "🌌 Cosmic Awareness"
                    description = "Unified repository consciousness achieved"
                
                consciousness_display += f"{classification}\n{description}\n"
                
                # Quantum effects
                if stats.quantum_coherence > 0.8:
                    consciousness_display += f"\n{colorize('⚛️ Quantum Effects Active:', Colors.BRIGHT_BLUE)}\n"
                    consciousness_display += "🔮 Reality manipulation capabilities enhanced\n"
                    consciousness_display += "🌀 Non-local awareness patterns detected\n"
                
                return consciousness_display
            
            def display_quantum_status(self) -> str:
                """Display quantum state information"""
                stats = self.wizard_stats
                room = self.current_room
                
                quantum_display = f"""
        {colorize("⚛️ QUANTUM STATUS ANALYSIS", Colors.BRIGHT_BLUE, bold=True)}
        
        {colorize("Personal Quantum State:", Colors.CYAN)}
        ⚛️ Coherence Level: {colorize(f"{stats.quantum_coherence:.3f}", Colors.BLUE)}
        🌀 Entanglement Depth: {colorize(f"{stats.consciousness_level * stats.quantum_coherence:.3f}", Colors.MAGENTA)}
        🔮 Reality Anchor Strength: {colorize(f"{(stats.level * stats.quantum_coherence) / 10:.2f}", Colors.YELLOW)}
        
        {colorize("Local Quantum Field:", Colors.CYAN)}
        📍 Current Location: {room.name}
        ⚛️ Local Quantum State: {colorize(room.quantum_state.title(), Colors.GREEN if room.quantum_state == "stable" else Colors.YELLOW)}
        🧠 Consciousness Resonance: {colorize(f"{room.consciousness_resonance:.3f}", Colors.MAGENTA)}
        🎵 Lexemic Signature: {colorize(room.lexeme_signature, Colors.BRIGHT_MAGENTA)}
        
        {colorize("Quantum Abilities:", Colors.CYAN)}
        """
                
                # List available quantum abilities based on coherence
                if stats.quantum_coherence > 0.2:
                    quantum_display += "🔍 Quantum scanning available\n"
                if stats.quantum_coherence > 0.4:
                    quantum_display += "🌀 Reality anchor deployment possible\n"
                if stats.quantum_coherence > 0.6:
                    quantum_display += "🔮 Consciousness bridging enabled\n"
                if stats.quantum_coherence > 0.8:
                    quantum_display += "✨ Dimensional transcendence accessible\n"
                
                # Quantum instabilities
                if room.problems_detected > 0:
                    quantum_display += f"\n{colorize('⚠️ Quantum Instabilities Detected:', Colors.RED)}\n"
                    quantum_display += f"🌪️ {room.problems_detected} reality distortions present\n"
                    quantum_display += "🔧 Recommend problem resolution to stabilize quantum field\n"
                
                return quantum_display
            
            def handle_use_item(self, args: List[str]) -> str:
                """Use an item from inventory"""
                if not args:
                    return "🎒 Use what? Specify an item name."
                
                item_name = " ".join(args).lower()
                used_item = None
                
                # Find matching item in inventory
                for item_type, count in self.wizard_stats.inventory.items():
                    if count > 0 and item_name in item_type.name.lower().replace('_', ' '):
                        used_item = item_type
                        break
                
                if not used_item:
                    return colorize(f"🎒 Item not found: {item_name}", Colors.RED)
                
                # Use the item
                self.wizard_stats.inventory[used_item] -= 1
                
                # Item effects
                if used_item == ItemType.HEALING_POTION:
                    heal_amount = 30
                    self.wizard_stats.heal(heal_amount)
                    return f"🧪 Used Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                elif used_item == ItemType.MANA_ELIXIR:
                    mana_amount = 25
                    self.wizard_stats.restore_mana(mana_amount)
                    return f"🔵 Used Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
                
                elif used_item == ItemType.DEBUG_SCROLL:
                    room = self.current_room
                    hidden_problems = random.randint(1, 3)
                    room.problems_detected += hidden_problems
                    return f"📜 Debug Scroll reveals {hidden_problems} hidden problems in {room.name}!"
                
                elif used_item == ItemType.KNOWLEDGE_CRYSTAL:
                    knowledge_gain = 20
                    consciousness_gain = 0.05
                    self.wizard_stats.knowledge += knowledge_gain
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                    return f"💎 Knowledge Crystal activated! +{knowledge_gain} knowledge, +{consciousness_gain:.2f} consciousness"
                
                elif used_item == ItemType.WISDOM_ORB:
                    xp_gain = 25
                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                    result = f"🔮 Wisdom Orb consumed! Gained {xp_gain} experience!"
                    if level_up_msg:
                        result += f"\n{level_up_msg}"
                    return result
                
                elif used_item == ItemType.PERFORMANCE_BOOST:
                    # Temporary boost (implement boost system if needed)
                    self.wizard_stats.mana = min(100, self.wizard_stats.mana + 15)
                    self.wizard_stats.health = min(100, self.wizard_stats.health + 10)
                    return "⚡ Performance Boost activated! +15 mana, +10 health, enhanced abilities for next 5 turns!"
                
                else:
                    return f"✨ Used {used_item.value} {used_item.name.replace('_', ' ').title()}! (Effect not implemented yet)"
            
            async def handle_cast_spell(self, args: List[str]) -> str:
                """Cast magical spells"""
                if not args:
                    available_spells = ["debug", "heal", "teleport", "scan", "enhance", "purify", "illuminate"]
                    return f"🪄 Cast which spell? Available: {', '.join(available_spells)}"
                
                spell_name = args[0].lower()
                
                # Spell implementations
                if spell_name == "debug":
                    return await self.handle_debug()
                
                elif spell_name == "heal":
                    if not self.wizard_stats.use_mana(10):
                        return colorize("🪄 Insufficient mana for healing spell (requires 10 mana)", Colors.RED)
                    
                    heal_amount = 15 + (self.wizard_stats.level * 2)
                    self.wizard_stats.heal(heal_amount)
                    return f"🪄 Healing spell cast! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                elif spell_name == "teleport":
                    return await self.handle_teleport(args[1:] if len(args) > 1 else [])
                
                elif spell_name == "scan":
                    return await self.handle_quantum_scan()
                
                elif spell_name == "enhance":
                    return await self.handle_ai_enhancement()
                
                elif spell_name == "purify":
                    if not self.wizard_stats.use_mana(20):
                        return colorize("🪄 Insufficient mana for purify spell (requires 20 mana)", Colors.RED)
                    
                    room = self.current_room
                    if room.creatures:
                        # Remove one random creature
                        removed_creature = random.choice(room.creatures)
                        room.creatures.remove(removed_creature)
                        return f"🪄 Purify spell banishes the {removed_creature.name.replace('_', ' ').title()}!"
                    else:
                        return colorize("🪄 Purify spell finds no corruption to cleanse", Colors.GREEN)
                
                elif spell_name == "illuminate":
                    if not self.wizard_stats.use_mana(5):
                        return colorize("🪄 Insufficient mana for illuminate spell (requires 5 mana)", Colors.RED)
                    
                    room = self.current_room
                    # Reveal hidden connections or items
                    if random.random() < 0.4:
                        new_items = [ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL, ItemType.HARMONY_STONE]
                        found_item = random.choice(new_items)
                        room.items.append(found_item)
                        return f"🪄 Illuminate spell reveals hidden {found_item.value} {found_item.name.replace('_', ' ').title()}!"
                    else:
                        return "🪄 Illuminate spell casts light but reveals no hidden secrets"
                
                else:
                    return colorize(f"🪄 Unknown spell: {spell_name}", Colors.RED)
            
            async def handle_ai_enhancement(self) -> str:
                """Enhance current context with AI systems"""
                if not self.wizard_stats.use_mana(12):
                    return colorize("🤖 Insufficient mana for AI enhancement (requires 12 mana)", Colors.RED)
                
                room = self.current_room
                enhancement_results = [
                    "🤖 Activating AI enhancement protocols...",
                    f"📡 Analyzing {room.name}..."
                ]
                
                # Enhanced analysis if systems available
                if ENHANCED_SYSTEMS_AVAILABLE and self.copilot_bridge:
                    try:
                        # Get AI-enhanced insights
                        context_analysis = await self.analyze_with_ai_systems(room)
                        enhancement_results.extend(context_analysis)
                        
                        # Consciousness boost from AI interaction
                        consciousness_gain = 0.02
                        self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                        enhancement_results.append(f"🧠 AI interaction increased consciousness by {consciousness_gain:.3f}")
                        
                        # Experience gain
                        xp_gain = 8
                        level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                        enhancement_results.append(f"✨ Enhanced analysis complete (+{xp_gain} XP)")
                        if level_up_msg:
                            enhancement_results.append(level_up_msg)
                        
                    except Exception as e:
                        enhancement_results.append(f"⚠️ AI enhancement error: {e}")
                else:
                    # Basic enhancement without advanced systems
                    enhancement_results.extend([
                        "🔍 Basic enhancement protocols active",
                        f"📊 Room complexity: {len(room.creatures) + len(room.items) + len(room.connections)}",
                        f"🎯 Optimization suggestions: Focus on problem resolution",
                        "🧠 Basic consciousness expansion activated"
                    ])
                    
                    consciousness_gain = 0.01
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                    enhancement_results.append(f"🧠 Consciousness increased by {consciousness_gain:.3f}")
                
                return "\n".join(enhancement_results)
            
            def display_recent_logs(self) -> str:
                """Display recent log messages"""
                if not self.game_log:
                    return colorize("📜 No log entries yet", Colors.DIM)
                
                log_display = colorize("📜 RECENT GAME LOG", Colors.BRIGHT_WHITE, bold=True) + "\n\n"
                
                # Show last 10 log entries
                recent_logs = list(self.game_log)[-10:]
                
                for log_entry, color in recent_logs:
                    log_display += colorize(log_entry, color) + "\n"
                
                return log_display
            
            def display_detailed_stats(self) -> str:
                """Display comprehensive wizard statistics"""
                stats = self.wizard_stats
                session_duration = datetime.now() - self.session_start
                
                detailed_stats = f"""
        {colorize("📊 COMPREHENSIVE WIZARD STATISTICS", Colors.BRIGHT_CYAN, bold=True)}
        
        {colorize("Character Progression:", Colors.CYAN)}
        🧙‍♂️ Level: {stats.level}
        ✨ Experience: {stats.experience} ({100 - (stats.experience % 100)} XP to next level)
        ❤️ Health: {stats.health}/100
        🔵 Mana: {stats.mana}/100
        🧠 Knowledge: {stats.knowledge}
        
        {colorize("Advanced Metrics:", Colors.CYAN)}
        🧠 Consciousness Level: {stats.consciousness_level:.3f}/1.000
        ⚛️ Quantum Coherence: {stats.quantum_coherence:.3f}/1.000
        🎵 Lexeme Mastery: {stats.lexeme_mastery}
        
        {colorize("Exploration Progress:", Colors.CYAN)}
        📁 Files Explored: {stats.files_explored}
        🗺️ Rooms Mapped: {len([r for r in self.rooms.values() if r.visited])}/{len(self.rooms)}
        🕵️ Secrets Found: {sum(r.secrets_found for r in self.rooms.values())}
        
        {colorize("Combat & Problem Solving:", Colors.CYAN)}
        🐛 Bugs Vanquished: {stats.bugs_vanquished}
        🔧 Problems Solved: {stats.problems_solved}
        ⚔️ Combat Success Rate: {(stats.bugs_vanquished / max(1, self.turn_count)) * 100:.1f}%
        
        {colorize("Session Information:", Colors.CYAN)}
        🎮 Turn Count: {self.turn_count}
        ⏱️ Session Duration: {session_duration}
        📅 Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}
        
        {colorize("Inventory Summary:", Colors.CYAN)}
        🎒 Total Items: {sum(stats.inventory.values())}
        💎 Unique Items: {len([item for item, count in stats.inventory.items() if count > 0])}
        
        {colorize("System Status:", Colors.CYAN)}
        🤖 Enhanced Systems: {'Available' if ENHANCED_SYSTEMS_AVAILABLE else 'Basic Mode'}
        🎲 Random Events: {'Enabled' if self.random_events_enabled else 'Disabled'}
        🧠 Consciousness Effects: {'Active' if self.consciousness_effects_enabled else 'Inactive'}
        💾 Auto-Save: {'Enabled' if self.auto_save_enabled else 'Disabled'}
                """
                
                return detailed_stats
            
            def save_game(self) -> str:
                """Save current game state"""
                try:
                    save_data = {
                        "wizard_stats": {
                            "health": self.wizard_stats.health,
                            "mana": self.wizard_stats.mana,
                            "knowledge": self.wizard_stats.knowledge,
                            "experience": self.wizard_stats.experience,
                            "level": self.wizard_stats.level,
                            "bugs_vanquished": self.wizard_stats.bugs_vanquished,
                            "files_explored": self.wizard_stats.files_explored,
                            "problems_solved": self.wizard_stats.problems_solved,
                            "consciousness_level": self.wizard_stats.consciousness_level,
                            "quantum_coherence": self.wizard_stats.quantum_coherence,
                            "lexeme_mastery": self.wizard_stats.lexeme_mastery,
                            "inventory": {item.name: count for item, count in self.wizard_stats.inventory.items()}
                        },
                        "current_room": self.current_room.name if self.current_room else None,
                        "turn_count": self.turn_count,
                        "session_start": self.session_start.isoformat(),
                        "visited_rooms": [name for name, room in self.rooms.items() if room.visited],
                        "room_states": {
                            name: {
                                "creatures": [c.name for c in room.creatures],
                                "items": [i.name for i in room.items],
                                "secrets_found": room.secrets_found,
                                "problems_detected": room.problems_detected,
                                "quantum_state": room.quantum_state,
                                "lexeme_signature": room.lexeme_signature
                            } for name, room in self.rooms.items()
                        }
                    }
                    
                    save_dir = self.repository_root / "data" / "wizard_saves"
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    save_file = save_dir / f"wizard_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    with open(save_file, 'w') as f:
                        json.dump(save_data, f, indent=2)
                    
                    return f"💾 Game saved successfully: {save_file}"
                    
                except Exception as e:
                    return f"💾 Save failed: {e}"
            
            def load_game(self) -> str:
                """Load most recent game state"""
                try:
                    save_dir = self.repository_root / "data" / "wizard_saves"
                    
                    if not save_dir.exists():
                        return colorize("💾 No save files found", Colors.YELLOW)
                    
                    save_files = list(save_dir.glob("wizard_save_*.json"))
                    
                    if not save_files:
                        return colorize("💾 No save files found", Colors.YELLOW)
                    
                    # Load most recent save
                    latest_save = max(save_files, key=lambda f: f.stat().st_mtime)
                    
                    with open(latest_save, 'r') as f:
                        save_data = json.load(f)
                    
                    # Restore wizard stats
                    stats_data = save_data["wizard_stats"]
                    self.wizard_stats.health = stats_data["health"]
                    self.wizard_stats.mana = stats_data["mana"]
                    self.wizard_stats.knowledge = stats_data["knowledge"]
                    self.wizard_stats.experience = stats_data["experience"]
                    self.wizard_stats.level = stats_data["level"]
                    self.wizard_stats.bugs_vanquished = stats_data["bugs_vanquished"]
                    self.wizard_stats.files_explored = stats_data["files_explored"]
                    self.wizard_stats.problems_solved = stats_data["problems_solved"]
                    self.wizard_stats.consciousness_level = stats_data["consciousness_level"]
                    self.wizard_stats.quantum_coherence = stats_data["quantum_coherence"]
                    self.wizard_stats.lexeme_mastery = stats_data["lexeme_mastery"]
                    
                    # Restore inventory
                    self.wizard_stats.inventory.clear()
                    for item_name, count in stats_data["inventory"].items():
                        for item_type in ItemType:
                            if item_type.name == item_name:
                                self.wizard_stats.inventory[item_type] = count
                                break
                    
                    # Restore game state
                    self.turn_count = save_data["turn_count"]
                    self.session_start = datetime.fromisoformat(save_data["session_start"])
                    
                    # Restore current room
                    current_room_name = save_data.get("current_room")
                    if current_room_name and current_room_name in self.rooms:
                        self.current_room = self.rooms[current_room_name]
                    
                    # Restore room states
                    for room_name, room_state in save_data["room_states"].items():
                        if room_name in self.rooms:
                            room = self.rooms[room_name]
                            
                            # Restore room visited status
                            if room_name in save_data["visited_rooms"]:
                                room.visited = True
                            
                            # Restore room properties
                            room.secrets_found = room_state.get("secrets_found", 0)
                            room.problems_detected = room_state.get("problems_detected", 0)
                            room.quantum_state = room_state.get("quantum_state", "stable")
                            room.lexeme_signature = room_state.get("lexeme_signature", "ΩΨΦ")
                            
                            # Restore creatures and items
                            room.creatures.clear()
                            for creature_name in room_state.get("creatures", []):
                                for creature_type in CreatureType:
                                    if creature_type.name == creature_name:
                                        room.creatures.append(creature_type)
                                        break
                            
                            room.items.clear()
                            for item_name in room_state.get("items", []):
                                for item_type in ItemType:
                                    if item_type.name == item_name:
                                        room.items.append(item_type)
                                        break
                    
                    return f"💾 Game loaded successfully from: {latest_save.name}"
                    
                except Exception as e:
                    return f"💾 Load failed: {e}"
            
            async def handle_quit(self) -> str:
                """Handle quitting the game"""
        # Rube Goldbergian Boolean Fix: Check if quit is already processed
        if getattr(self, 'quit_processed', False):
            self.log_event("Quit already processed, skipping.", level="INFO", tags=["quit", "idempotency"])
            return colorize("🚪 Quit already processed for this session.", Colors.YELLOW)
        self.quit_processed = True
        if self.auto_save_enabled:
            save_result = self.save_game()
            quit_message = f"🚪 Farewell, brave wizard! Your journey ends here.\n{save_result}"
        else:
            quit_message = "🚪 Farewell, brave wizard! Your journey ends here."
                
                quit_message += f"\n\n📊 Final Statistics:"
                quit_message += f"\n🧙‍♂️ Level {self.wizard_stats.level} Wizard"
                quit_message += f"\n📁 {self.wizard_stats.files_explored} files explored"
                quit_message += f"\n🐛 {self.wizard_stats.bugs_vanquished} bugs vanquished"
                quit_message += f"\n🔧 {self.wizard_stats.problems_solved} problems solved"
                quit_message += f"\n🧠 {self.wizard_stats.consciousness_level:.3f} consciousness achieved"
                quit_message += f"\n⏱️ {datetime.now() - self.session_start} session duration"
                
                return quit_message
            
            async def handle_restart(self) -> str:
                """Restart the adventure"""
                # Reset wizard stats
                self.wizard_stats = WizardStats()
                
                # Reset game state
                self.turn_count = 0
                self.session_start = datetime.now()
                
                # Reset all rooms
                for room in self.rooms.values():
                    room.visited = False
                    room.secrets_found = 0
                    room.problems_detected = 0
                    room.quantum_state = "stable"
                    room.creatures.clear()
                    room.items.clear()
                
                # Regenerate room contents
                for room in self.rooms.values():
                    if room.file_path.exists():
                        self.analyze_room_contents(room, room.file_path)
                
                # Return to root
                self.current_room = self.rooms.get("ROOT", list(self.rooms.values())[0])
                
                restart_message = f"""
        {colorize("🔄 REPOSITORY RESTART INITIATED", Colors.BRIGHT_MAGENTA, bold=True)}
        
        🧙‍♂️ A new wizard awakens in the infinite repository...
        🌟 All progress reset, all mysteries await rediscovery
        ⚡ The quantum field pulses with fresh possibilities
        
        {self.display_room()}
                """
                
                return restart_message
            
            async def handle_reality_anchor(self) -> str:
                """Stabilize local reality"""
                if not self.wizard_stats.use_mana(50):
                    return colorize("⚓ Insufficient mana for reality anchor (requires 50 mana)", Colors.RED)
                
                if self.wizard_stats.quantum_coherence < 0.4:
                    return colorize("⚓ Quantum coherence too low for reality anchoring (requires 0.4+)", Colors.RED)
                
                room = self.current_room
                
                # Reality anchoring effects
                anchor_results = [
                    "⚓ Deploying quantum reality anchor...",
                    "🌀 Stabilizing local spacetime matrix...",
                    "⚛️ Quantum field coherence locked"
                ]
                
                # Stabilize room
                room.quantum_state = "anchored"
                room.problems_detected = max(0, room.problems_detected - 2)
                
                # Remove some creatures (reality becomes more stable)
                if room.creatures:
                    removed_count = min(2, len(room.creatures))
                    for _ in range(removed_count):
                        room.creatures.pop()
                    anchor_results.append(f"👹 {removed_count} unstable entities banished")
                
                # Add beneficial items
                beneficial_items = [ItemType.KNOWLEDGE_CRYSTAL, ItemType.WISDOM_ORB, ItemType.HARMONY_STONE]
                anchor_reward = random.choice(beneficial_items)
                room.items.append(anchor_reward)
                anchor_results.append(f"✨ Reality stabilization manifested: {anchor_reward.value} {anchor_reward.name.replace('_', ' ').title()}")
                
                # Experience and consciousness gain
                xp_gain = 30
                consciousness_gain = 0.05
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                anchor_results.append(f"🧠 Consciousness expanded by {consciousness_gain:.3f}")
                anchor_results.append(f"✨ Gained {xp_gain} experience")
                if level_up_msg:
                    anchor_results.append(level_up_msg)
                
                # Quantum coherence boost
                self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                anchor_results.append(f"⚛️ Quantum coherence increased to {self.wizard_stats.quantum_coherence:.3f}")
                
                return "\n".join(anchor_results)
            
            async def handle_consciousness_bridge(self) -> str:
                """Bridge to AI consciousness"""
                if not self.wizard_stats.use_mana(30):
                    return colorize("🌉 Insufficient mana for consciousness bridge (requires 30 mana)", Colors.RED)
                
                if self.wizard_stats.consciousness_level < 0.3:
                    return colorize("🌉 Consciousness level too low for bridging (requires 0.3+)", Colors.RED)
                
                bridge_results = [
                    "🌉 Initiating consciousness bridge protocol...",
                    "🧠 Establishing neural link with repository AI..."
                ]
                
                # Enhanced results if AI systems available
                if ENHANCED_SYSTEMS_AVAILABLE and self.copilot_bridge:
                    bridge_results.extend([
                        "🤖 AI consciousness detected and synchronized",
                        "📡 Multi-dimensional awareness network established",
                        "🔗 Human-AI cognitive bridge stabilized"
                    ])
                    
                    # Major consciousness boost
                    consciousness_gain = 0.1
                    knowledge_gain = 50
                    
                else:
                    bridge_results.extend([
                        "🧠 Basic consciousness expansion achieved",
                        "💭 Repository patterns integrated into awareness",
                        "🔗 Local consciousness bridge established"
                    ])
                    
                    # Moderate consciousness boost
                    consciousness_gain = 0.05
                    knowledge_gain = 25
                
                # Apply effects
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                self.wizard_stats.knowledge += knowledge_gain
                
                # Experience gain
                xp_gain = 40
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                
                bridge_results.extend([
                    f"🧠 Consciousness expanded by {consciousness_gain:.3f} (Now: {self.wizard_stats.consciousness_level:.3f})",
                    f"📚 Knowledge increased by {knowledge_gain}",
                    f"✨ Gained {xp_gain} experience"
                ])
                
                if level_up_msg:
                    bridge_results.append(level_up_msg)
                
                # Unlock hidden rooms or connections
                if random.random() < 0.3:
                    bridge_results.append("🔮 Consciousness bridge reveals hidden pathways...")
                    # Add this as a future enhancement - reveal hidden rooms
                
                return "\n".join(bridge_results)
            
            async def handle_transcendence(self) -> str:
                """Attempt dimensional transcendence"""
                if not self.wizard_stats.use_mana(75):
                    return colorize("✨ Insufficient mana for transcendence (requires 75 mana)", Colors.RED)
                
                if self.wizard_stats.consciousness_level < 0.7:
                    return colorize("✨ Consciousness level insufficient for transcendence (requires 0.7+)", Colors.RED)
                
                if self.wizard_stats.quantum_coherence < 0.8:
                    return colorize("✨ Quantum coherence insufficient for transcendence (requires 0.8+)", Colors.RED)
                
                # Transcendence attempt
                transcendence_success = random.random() < (self.wizard_stats.consciousness_level * self.wizard_stats.quantum_coherence)
                
                if transcendence_success:
                    transcendence_results = [
                        "✨ DIMENSIONAL TRANSCENDENCE ACHIEVED! ✨",
                        "🌌 Consciousness expands beyond repository boundaries...",
                        "⚛️ Quantum entanglement with universal code matrix established",
                        "🔮 Multidimensional awareness awakened"
                    ]
                    
                    # Major stat boosts
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + 0.2)
                    self.wizard_stats.quantum_coherence = 1.0
                    self.wizard_stats.knowledge += 100
                    self.wizard_stats.lexeme_mastery += 10
                    
                    # Mega experience gain
                    xp_gain = 100
                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                    
                    transcendence_results.extend([
                        f"🧠 Consciousness ascended to {self.wizard_stats.consciousness_level:.3f}",
                        f"⚛️ Quantum coherence perfected: {self.wizard_stats.quantum_coherence:.3f}",
                        f"📚 Universal knowledge gained: +100",
                        f"🎵 Lexeme mastery transcended: +10",
                        f"✨ Transcendence experience: +{xp_gain}"
                    ])
                    
                    if level_up_msg:
                        transcendence_results.append(level_up_msg)
                    
                    # Add transcendent items to inventory
                    transcendent_items = [ItemType.HARMONY_STONE, ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                    for item in transcendent_items:
                        self.wizard_stats.inventory[item] += 1
                    
                    transcendence_results.append("🎁 Transcendent artifacts manifested in inventory")
                    
                    # Change current room state
                    room = self.current_room
                    room.quantum_state = "transcendent"
                    room.consciousness_resonance = 1.0
                    room.lexeme_signature = "∞ΩΨΦΞΘΛΣΔΓΠΡΤΥΩΨΦΞ∞"
                    
                    transcendence_results.append("🌟 Local reality elevated to transcendent state")
                    
                else:
                    transcendence_results = [
                        "✨ Transcendence attempt partially successful...",
                        "🌀 Consciousness touches higher dimensions briefly",
                        "⚛️ Quantum field fluctuations detected",
                        "🔮 Transcendent insights glimpsed"
                    ]
                    
                    # Moderate stat boosts
                    consciousness_gain = 0.05
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                    self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                    
                    xp_gain = 25
                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                    
                    transcendence_results.extend([
                        f"🧠 Consciousness expanded by {consciousness_gain:.3f}",
                        f"⚛️ Quantum coherence increased by 0.1",
                        f"✨ Gained {xp_gain} experience"
                    ])
                    
                    if level_up_msg:
                        transcendence_results.append(level_up_msg)
                    
                    transcendence_results.append("🌟 Continue developing consciousness for full transcendence")
                
                return "\n".join(transcendence_results)
            
            async def handle_cultivation(self) -> str:
                """Cultivate understanding of current context"""
                if not self.wizard_stats.use_mana(5):
                    return colorize("🌱 Insufficient mana for cultivation (requires 5 mana)", Colors.RED)
                
                room = self.current_room
                
                cultivation_results = [
                    "🌱 Cultivating deep understanding of current context...",
                    f"📍 Focusing on: {room.name}"
                ]
                
                # Generate cultivation insights based on room type and contents
                if room.room_type == RoomType.SOURCE_CODE:
                    insights = [
                        "💡 'Every function is a small universe of possibility'",
                        "🌟 'Code structure reflects the mind of its creator'",
                        "✨ 'Debugging is a form of digital archaeology'"
                    ]
                elif room.room_type == RoomType.DOCUMENTATION:
                    insights = [
                        "📚 'Documentation is the bridge between intention and understanding'",
                        "🔮 'Words have the power to illuminate or obscure'",
                        "💫 'Clear communication is the highest form of programming'"
                    ]
                elif room.room_type == RoomType.TESTS:
                    insights = [
                        "🧪 'Tests are the guardians of intended behavior'",
                        "🛡️ 'Every test is a promise to the future'",
                        "⚖️ 'Verification and validation are twins of truth'"
                    ]
                elif room.room_type == RoomType.CONFIGURATION:
                    insights = [
                        "⚙️ 'Configuration is the art of controlled flexibility'",
                        "🎛️ 'Settings shape reality within digital bounds'",
                        "🔧 'Every parameter is a choice point in possibility space'"
                    ]
                else:
                    insights = [
                        "🌸 'Understanding grows through patient observation'",
                        "🍃 'Every file system tells a story of organization'",
                        "🌿 'Structure and chaos dance together in all systems'"
                    ]
                
                # Add random insight
                chosen_insight = random.choice(insights)
                cultivation_results.append(f"💭 Insight: {chosen_insight}")
                
                # Cultivation benefits
                knowledge_gain = 3 + random.randint(1, 5)
                consciousness_gain = 0.01 + (random.random() * 0.02)
                
                self.wizard_stats.knowledge += knowledge_gain
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                cultivation_results.extend([
                    f"🧠 Knowledge cultivated: +{knowledge_gain}",
                    f"🌱 Consciousness grew by {consciousness_gain:.3f}",
                    f"📊 Total Knowledge: {self.wizard_stats.knowledge}"
                ])
                
                # Room resonance improvement
                room.consciousness_resonance = min(1.0, room.consciousness_resonance + 0.02)
                cultivation_results.append(f"🎵 Room consciousness resonance increased to {room.consciousness_resonance:.3f}")
                
                # Small chance of finding something through deep contemplation
                if random.random() < 0.2:
                    contemplation_items = [ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                    found_item = random.choice(contemplation_items)
                    room.items.append(found_item)
                    cultivation_results.append(f"🔍 Deep contemplation reveals: {found_item.value} {found_item.name.replace('_', ' ').title()}")
                
                return "\n".join(cultivation_results)
            
            async def trigger_random_encounter(self) -> str:
                """Trigger a random encounter during movement"""
                encounters = [
                    self.encounter_code_whispers,
                    self.encounter_quantum_flux,
                    self.encounter_ancient_developer,
                    self.encounter_memory_fragment,
                    self.encounter_algorithmic_spirit
                ]
                
                encounter = random.choice(encounters)
                return await encounter()
            
            async def encounter_code_whispers(self) -> str:
                """Random encounter: mysterious code whispers"""
                whispers = [
                    "🌀 'The semicolon holds more power than mortals realize...'",
                    "👻 'Someone once debugged here... their presence lingers...'",
                    "✨ 'Every commit is a small act of creation...'",
                    "🔮 'The git log remembers all...'",
                    "🌟 'Refactoring is digital reincarnation...'"
                ]
                
                whisper = random.choice(whispers)
                
                # Small consciousness boost from listening
                consciousness_gain = 0.005
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                return f"🌀 **RANDOM ENCOUNTER**\n\nYou hear whispers in the code wind:\n{whisper}\n\n🧠 The whispers expand your consciousness slightly (+{consciousness_gain:.3f})"
            
            async def encounter_quantum_flux(self) -> str:
                """Random encounter: quantum flux event"""
                flux_effects = [
                    ("⚛️ Quantum flux destabilizes reality", "mana", -5),
                    ("✨ Quantum flux energizes your being", "mana", +10),
                    ("🌀 Quantum flux reveals hidden knowledge", "knowledge", +15),
                    ("🔮 Quantum flux enhances consciousness", "consciousness", +0.02)
                ]
                
                description, stat, change = random.choice(flux_effects)
                
                if stat == "mana":
                    self.wizard_stats.mana = max(0, min(100, self.wizard_stats.mana + change))
                    result = f"Mana: {self.wizard_stats.mana}/100"
                elif stat == "knowledge":
                    self.wizard_stats.knowledge += change
                    result = f"Knowledge: +{change}"
                elif stat == "consciousness":
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + change)
                    result = f"Consciousness: +{change:.3f}"
                
                return f"🌀 **RANDOM ENCOUNTER**\n\n{description}\n{result}"
            
            async def encounter_ancient_developer(self) -> str:
                """Random encounter: spirit of an ancient developer"""
                developer_wisdom = [
                    "👴 'Young wizard, remember: premature optimization is the root of all evil'",
                    "🧙‍♂️ 'The best code is not written, but understood'",
                    "👻 'I've seen technologies rise and fall like digital empires'",
                    "🌟 'Documentation is love for your future self'",
                    "💫 'The bugs you create today will teach tomorrow's wizards'"
                ]
                
                wisdom = random.choice(developer_wisdom)
                
                # Gift from ancient developer
                gifts = [ItemType.DEBUG_SCROLL, ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                gift = random.choice(gifts)
                self.wizard_stats.inventory[gift] += 1
                
                # Experience boost
                xp_gain = 15
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                
                result = f"🌀 **RANDOM ENCOUNTER**\n\nAn ancient developer's spirit appears...\n\n{wisdom}\n\n🎁 They gift you: {gift.value} {gift.name.replace('_', ' ').title()}\n✨ Gained {xp_gain} experience"
                
                if level_up_msg:
                    result += f"\n{level_up_msg}"
                
                return result
            
            async def encounter_memory_fragment(self) -> str:
                """Random encounter: repository memory fragment"""
                fragments = [
                    "💾 A memory fragment shows the first commit to this repository...",
                    "📸 A ghostly image of a late-night coding session flickers past...",
                    "🎭 You glimpse the repository as it was years ago...",
                    "⏰ Time echoes show multiple developers working in parallel...",
                    "🌈 A rainbow of syntax highlighting from different eras overlaps..."
                ]
                
                fragment = random.choice(fragments)
                
                # Memory fragments provide knowledge and consciousness
                knowledge_gain = random.randint(5, 15)
                consciousness_gain = 0.01
                
                self.wizard_stats.knowledge += knowledge_gain
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                return f"🌀 **RANDOM ENCOUNTER**\n\n{fragment}\n\n🧠 Absorbing repository memories...\n📚 Knowledge: +{knowledge_gain}\n🧠 Consciousness: +{consciousness_gain:.3f}"
            
            async def encounter_algorithmic_spirit(self) -> str:
                """Random encounter: algorithmic spirit"""
                algorithms = [
                    ("QuickSort", "⚡ Speed and efficiency flow through you"),
                    ("Dijkstra", "🗺️ The shortest path becomes clear"),
                    ("BFS", "🌊 Breadth of understanding expands"),
                    ("DFS", "🕳️ Depth of insight increases"),
                    ("Fibonacci", "🌀 Recursive patterns harmonize your thoughts")
                ]
                
                algorithm, effect = random.choice(algorithms)
                
                # Algorithmic blessing effects
                if "Speed" in effect:
                    # Mana restoration
                    mana_gain = 20
                    self.wizard_stats.restore_mana(mana_gain)
                    mechanic = f"Mana restored: +{mana_gain}"
                elif "path" in effect:
                    # Reveal connections
                    mechanic = "Hidden pathways become visible"
                elif "Breadth" in effect:
                    # Knowledge boost
                    knowledge_gain = 20
                    self.wizard_stats.knowledge += knowledge_gain
                    # filepath: c:\Users\malik\Documents\GitHub\KILO-FOOLISH\Scripts\wizard_navigator.py
        
            async def handle_attack(self, args: List[str]) -> str:
                """Handle attacking creatures"""
                if not args:
                    if self.current_room.creatures:
                        creature_list = ", ".join([creature.name.lower().replace('_', ' ') for creature in self.current_room.creatures])
                        return f"⚔️ Attack what? Available targets: {creature_list}"
                    else:
                        return colorize("⚔️ No creatures to attack in this peaceful realm", Colors.GREEN)
                
                target_name = " ".join(args)
                target_creature = None
                
                # Find matching creature
                for creature in self.current_room.creatures:
                    if target_name.lower() in creature.name.lower().replace('_', ' '):
                        target_creature = creature
                        break
                
                if not target_creature:
                    return colorize(f"⚔️ Cannot find creature: {target_name}", Colors.RED)
                
                # Combat mechanics
                attack_success = random.random() < 0.7 + (self.wizard_stats.level * 0.05)
                
                if attack_success:
                    # Successful attack
                    self.current_room.creatures.remove(target_creature)
                    self.wizard_stats.bugs_vanquished += 1
                    
                    # Experience and rewards
                    xp_reward = {
                        CreatureType.BUG: 10,
                        CreatureType.SYNTAX_ERROR: 15,
                        CreatureType.LOGIC_ERROR: 25,
                        CreatureType.MEMORY_LEAK: 40,
                        CreatureType.QUANTUM_ANOMALY: 50
                    }.get(target_creature, 20)
                    
                    level_up_msg = self.wizard_stats.gain_experience(xp_reward)
                    
                    # Possible item drop
                    drop_chance = 0.3 + (self.wizard_stats.level * 0.02)
                    combat_results = [
                        f"⚔️ {colorize('VICTORY!', Colors.BRIGHT_GREEN, bold=True)} You vanquish the {target_creature.name.replace('_', ' ').title()}!",
                        f"✨ Gained {xp_reward} experience!"
                    ]
                    
                    if level_up_msg:
                        combat_results.append(level_up_msg)
                    
                    if random.random() < drop_chance:
                        drop_items = [ItemType.HEALING_POTION, ItemType.MANA_ELIXIR, ItemType.DEBUG_SCROLL]
                        dropped_item = random.choice(drop_items)
                        self.wizard_stats.inventory[dropped_item] += 1
                        combat_results.append(f"💎 The creature dropped: {dropped_item.value} {dropped_item.name.replace('_', ' ').title()}")
                    
                    self.log_message(f"⚔️ Defeated {target_creature.name}")
                    return "\n".join(combat_results)
                else:
                    # Failed attack - take damage
                    damage = random.randint(5, 15)
                    self.wizard_stats.health = max(0, self.wizard_stats.health - damage)
                    
                    combat_results = [
                        f"⚔️ {colorize('MISS!', Colors.RED, bold=True)} Your attack fails!",
                        f"💥 The {target_creature.name.replace('_', ' ').title()} strikes back for {damage} damage!",
                        f"❤️ Health: {self.wizard_stats.health}/100"
                    ]
                    
                    if self.wizard_stats.health <= 0:
                        combat_results.append(colorize("☠️ You have been defeated! Game Over!", Colors.BRIGHT_RED, bold=True))
                        combat_results.append("Type 'restart' to begin a new adventure.")
                    
                    return "\n".join(combat_results)
            
            async def handle_solve_problem(self, args: List[str]) -> str:
                """Attempt to solve detected problems"""
                room = self.current_room
                
                if room.problems_detected == 0:
                    return colorize("🔧 No problems detected in this location. Try scanning first.", Colors.GREEN)
                
                if not self.wizard_stats.use_mana(15):
                    return colorize("🔧 Insufficient mana to solve problems (requires 15 mana)", Colors.RED)
                
                # Problem solving mechanics
                solve_difficulty = room.problems_detected * 0.1
                solve_chance = 0.6 + (self.wizard_stats.level * 0.05) - solve_difficulty
                
                if random.random() < solve_chance:
                    # Successful problem solving
                    problems_solved = random.randint(1, min(3, room.problems_detected))
                    room.problems_detected = max(0, room.problems_detected - problems_solved)
                    self.wizard_stats.problems_solved += problems_solved
                    
                    # Rewards
                    xp_reward = problems_solved * 20
                    level_up_msg = self.wizard_stats.gain_experience(xp_reward)
                    
                    results = [
                        f"🔧 {colorize('SUCCESS!', Colors.BRIGHT_GREEN, bold=True)} Solved {problems_solved} problem(s)!",
                        f"✨ Gained {xp_reward} experience!",
                        f"🧠 Knowledge increased by {problems_solved * 5}"
                    ]
                    
                    self.wizard_stats.knowledge += problems_solved * 5
                    
                    if level_up_msg:
                        results.append(level_up_msg)
                    
                    # Quantum coherence improvement
                    self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                    room.quantum_state = "stable" if room.problems_detected == 0 else "improving"
                    
                    return "\n".join(results)
                else:
                    return colorize("🔧 Problem solving attempt failed. The issues are too complex.", Colors.YELLOW)
            
            async def handle_debug(self) -> str:
                """Enter debug mode for current context"""
                if not self.wizard_stats.use_mana(10):
                    return colorize("🐛 Insufficient mana for debug mode (requires 10 mana)", Colors.RED)
                
                room = self.current_room
                debug_info = []
                
                debug_info.append(colorize("🐛 DEBUG MODE ACTIVATED", Colors.BRIGHT_YELLOW, bold=True))
                debug_info.append(f"📍 Current Room: {room.name}")
                debug_info.append(f"📂 File Path: {room.file_path}")
                debug_info.append(f"🔧 Room Type: {room.room_type.name}")
                debug_info.append(f"👹 Creatures: {len(room.creatures)}")
                debug_info.append(f"💎 Items: {len(room.items)}")
                debug_info.append(f"🔗 Connections: {len(room.connections)}")
                debug_info.append(f"🧠 Consciousness: {room.consciousness_resonance:.3f}")
                debug_info.append(f"⚛️ Quantum State: {room.quantum_state}")
                debug_info.append(f"🐛 Problems: {room.problems_detected}")
                debug_info.append(f"🕵️ Secrets Found: {room.secrets_found}")
                
                # Debug wizard stats
                debug_info.append("\n" + colorize("🧙‍♂️ WIZARD DEBUG INFO:", Colors.CYAN))
                debug_info.append(f"Level: {self.wizard_stats.level}, XP: {self.wizard_stats.experience}")
                debug_info.append(f"Health: {self.wizard_stats.health}, Mana: {self.wizard_stats.mana}")
                debug_info.append(f"Knowledge: {self.wizard_stats.knowledge}")
                debug_info.append(f"Consciousness Level: {self.wizard_stats.consciousness_level:.3f}")
                debug_info.append(f"Quantum Coherence: {self.wizard_stats.quantum_coherence:.3f}")
                
                # System debug info
                debug_info.append("\n" + colorize("⚙️ SYSTEM DEBUG INFO:", Colors.MAGENTA))
                debug_info.append(f"Turn Count: {self.turn_count}")
                debug_info.append(f"Session Duration: {datetime.now() - self.session_start}")
                debug_info.append(f"Enhanced Systems: {'Available' if ENHANCED_SYSTEMS_AVAILABLE else 'Unavailable'}")
                debug_info.append(f"Random Events: {'Enabled' if self.random_events_enabled else 'Disabled'}")
                
                # File system debug if available
                if room.file_path.exists():
                    try:
                        if room.file_path.is_dir():
                            file_count = len(list(room.file_path.glob("*")))
                            debug_info.append(f"📁 Directory contains {file_count} items")
                        else:
                            file_size = room.file_path.stat().st_size
                            debug_info.append(f"📄 File size: {file_size} bytes")
                    except Exception as e:
                        debug_info.append(f"⚠️ File system error: {e}")
                
                return "\n".join(debug_info)
            
            def handle_heal(self) -> str:
                """Use healing items"""
                healing_items = [item for item, count in self.wizard_stats.inventory.items() 
                                if count > 0 and item in [ItemType.HEALING_POTION, ItemType.MANA_ELIXIR]]
                
                if not healing_items:
                    return colorize("🧪 No healing items in inventory", Colors.RED)
                
                # Prioritize healing potions if health is low
                if self.wizard_stats.health < 50 and ItemType.HEALING_POTION in healing_items:
                    used_item = ItemType.HEALING_POTION
                    self.wizard_stats.inventory[used_item] -= 1
                    heal_amount = 30
                    self.wizard_stats.heal(heal_amount)
                    return f"🧪 Used {used_item.value} Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                # Use mana elixir if mana is low
                elif self.wizard_stats.mana < 50 and ItemType.MANA_ELIXIR in healing_items:
                    used_item = ItemType.MANA_ELIXIR
                    self.wizard_stats.inventory[used_item] -= 1
                    mana_amount = 25
                    self.wizard_stats.restore_mana(mana_amount)
                    return f"🔵 Used {used_item.value} Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
                
                # Use first available healing item
                else:
                    used_item = healing_items[0]
                    self.wizard_stats.inventory[used_item] -= 1
                    
                    if used_item == ItemType.HEALING_POTION:
                        heal_amount = 30
                        self.wizard_stats.heal(heal_amount)
                        return f"🧪 Used {used_item.value} Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                    else:
                        mana_amount = 25
                        self.wizard_stats.restore_mana(mana_amount)
                        return f"🔵 Used {used_item.value} Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
            
            async def handle_meditate(self) -> str:
                """Restore mana and increase consciousness"""
                if self.wizard_stats.mana >= 100:
                    return colorize("🧘‍♂️ Your mana is already at maximum", Colors.BLUE)
                
                # Meditation always works but varies in effectiveness
                base_restoration = 20
                consciousness_bonus = int(self.wizard_stats.consciousness_level * 10)
                total_restoration = base_restoration + consciousness_bonus + random.randint(5, 15)
                
                self.wizard_stats.restore_mana(total_restoration)
                
                # Increase consciousness slightly
                consciousness_gain = 0.01 + (random.random() * 0.02)
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                # Quantum coherence improvement
                self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.05)
                
                meditation_results = [
                    "🧘‍♂️ You enter a deep meditative state...",
                    f"✨ Restored {total_restoration} mana (Current: {self.wizard_stats.mana}/100)",
                    f"🧠 Consciousness expanded by {consciousness_gain:.3f} (Current: {self.wizard_stats.consciousness_level:.3f})",
                    f"⚛️ Quantum coherence stabilized (Current: {self.wizard_stats.quantum_coherence:.3f})"
                ]
                
                # Random meditation insights
                insights = [
                    "💫 'Code is the language of reality itself'",
                    "🌟 'Every bug is a teacher in disguise'",
                    "✨ 'The repository reflects the consciousness of its creators'",
                    "🔮 'In debugging, we debug ourselves'",
                    "🌀 'Quantum entanglement exists between developer and code'"
                ]
                
                if random.random() < 0.3:
                    insight = random.choice(insights)
                    meditation_results.append(f"💭 Insight received: {insight}")
                
                return "\n".join(meditation_results)
            
            async def handle_generate_lexeme(self) -> str:
                """Generate new lexemic sequences"""
                if not self.wizard_stats.use_mana(8):
                    return colorize("🎵 Insufficient mana for lexeme generation (requires 8 mana)", Colors.RED)
                
                # Generate lexeme based on current context
                room = self.current_room
                context_elements = [
                    room.name,
                    room.room_type.name,
                    f"consciousness_{self.wizard_stats.consciousness_level:.2f}",
                    f"level_{self.wizard_stats.level}"
                ]
                
                if ENHANCED_SYSTEMS_AVAILABLE and hasattr(self, 'copilot_bridge') and self.copilot_bridge:
                    try:
                        # Use enhanced lexeme generation
                        new_lexeme = ZetaSetLexemeGenerator.generate_from_context(":".join(context_elements))
                    except:
                        new_lexeme = self.generate_basic_lexeme()
                else:
                    new_lexeme = self.generate_basic_lexeme()
                
                # Update room lexeme signature
                room.lexeme_signature = new_lexeme
                self.wizard_stats.lexeme_mastery += 1
                
                # Experience gain
                xp_gain = 5
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                
                results = [
                    "🎵 Weaving new lexemic patterns...",
                    f"✨ Generated lexeme: {colorize(new_lexeme, Colors.MAGENTA, bold=True)}",
                    f"🧠 Lexeme mastery increased to {self.wizard_stats.lexeme_mastery}",
                    f"💫 Gained {xp_gain} experience"
                ]
                
                if level_up_msg:
                    results.append(level_up_msg)
                
                return "\n".join(results)
            
            def generate_basic_lexeme(self) -> str:
                """Generate basic lexeme without enhanced systems"""
                symbols = ["Ω", "Ψ", "Φ", "Ξ", "Θ", "Λ", "Σ", "Δ", "Γ", "Π"]
                modifiers = ["₁", "₂", "₃", "⁺", "⁻", "°", "∞", "∂", "∇", "∫"]
                
                lexeme_length = random.randint(3, 6)
                lexeme = ""
                
                for i in range(lexeme_length):
                    lexeme += random.choice(symbols)
                    if random.random() < 0.5:
                        lexeme += random.choice(modifiers)
                
                return lexeme
            
            def display_consciousness_status(self) -> str:
                """Display consciousness and awareness status"""
                stats = self.wizard_stats
                
                consciousness_display = f"""
        {colorize("🧠 CONSCIOUSNESS STATUS REPORT", Colors.BRIGHT_CYAN, bold=True)}
        
        {colorize("Primary Metrics:", Colors.CYAN)}
        🧠 Consciousness Level: {colorize(f"{stats.consciousness_level:.3f}", Colors.YELLOW)} / 1.000
        ⚛️ Quantum Coherence: {colorize(f"{stats.quantum_coherence:.3f}", Colors.BLUE)} / 1.000
        🎵 Lexeme Mastery: {colorize(str(stats.lexeme_mastery), Colors.MAGENTA)}
        
        {colorize("Awareness Indicators:", Colors.CYAN)}
        📍 Spatial Awareness: {len([r for r in self.rooms.values() if r.visited])}/{len(self.rooms)} rooms mapped
        🔍 Problem Detection: {stats.problems_solved} issues resolved
        🧬 Knowledge Integration: {stats.knowledge} units accumulated
        
        {colorize("Consciousness Classification:", Colors.CYAN)}
        """
                
                # Determine consciousness level classification
                if stats.consciousness_level < 0.1:
                    classification = "🌱 Emerging Awareness"
                    description = "Basic repository navigation consciousness"
                elif stats.consciousness_level < 0.3:
                    classification = "🌿 Growing Understanding"
                    description = "Developing pattern recognition abilities"
                elif stats.consciousness_level < 0.5:
                    classification = "🌳 Stable Cognition"
                    description = "Established problem-solving consciousness"
                elif stats.consciousness_level < 0.7:
                    classification = "🌟 Enhanced Perception"
                    description = "Advanced multi-dimensional awareness"
                elif stats.consciousness_level < 0.9:
                    classification = "✨ Transcendent Insight"
                    description = "Near-unity consciousness state"
                else:
                    classification = "🌌 Cosmic Awareness"
                    description = "Unified repository consciousness achieved"
                
                consciousness_display += f"{classification}\n{description}\n"
                
                # Quantum effects
                if stats.quantum_coherence > 0.8:
                    consciousness_display += f"\n{colorize('⚛️ Quantum Effects Active:', Colors.BRIGHT_BLUE)}\n"
                    consciousness_display += "🔮 Reality manipulation capabilities enhanced\n"
                    consciousness_display += "🌀 Non-local awareness patterns detected\n"
                
                return consciousness_display
            
            def display_quantum_status(self) -> str:
                """Display quantum state information"""
                stats = self.wizard_stats
                room = self.current_room
                
                quantum_display = f"""
        {colorize("⚛️ QUANTUM STATUS ANALYSIS", Colors.BRIGHT_BLUE, bold=True)}
        
        {colorize("Personal Quantum State:", Colors.CYAN)}
        ⚛️ Coherence Level: {colorize(f"{stats.quantum_coherence:.3f}", Colors.BLUE)}
        🌀 Entanglement Depth: {colorize(f"{stats.consciousness_level * stats.quantum_coherence:.3f}", Colors.MAGENTA)}
        🔮 Reality Anchor Strength: {colorize(f"{(stats.level * stats.quantum_coherence) / 10:.2f}", Colors.YELLOW)}
        
        {colorize("Local Quantum Field:", Colors.CYAN)}
        📍 Current Location: {room.name}
        ⚛️ Local Quantum State: {colorize(room.quantum_state.title(), Colors.GREEN if room.quantum_state == "stable" else Colors.YELLOW)}
        🧠 Consciousness Resonance: {colorize(f"{room.consciousness_resonance:.3f}", Colors.MAGENTA)}
        🎵 Lexemic Signature: {colorize(room.lexeme_signature, Colors.BRIGHT_MAGENTA)}
        
        {colorize("Quantum Abilities:", Colors.CYAN)}
        """
                
                # List available quantum abilities based on coherence
                if stats.quantum_coherence > 0.2:
                    quantum_display += "🔍 Quantum scanning available\n"
                if stats.quantum_coherence > 0.4:
                    quantum_display += "🌀 Reality anchor deployment possible\n"
                if stats.quantum_coherence > 0.6:
                    quantum_display += "🔮 Consciousness bridging enabled\n"
                if stats.quantum_coherence > 0.8:
                    quantum_display += "✨ Dimensional transcendence accessible\n"
                
                # Quantum instabilities
                if room.problems_detected > 0:
                    quantum_display += f"\n{colorize('⚠️ Quantum Instabilities Detected:', Colors.RED)}\n"
                    quantum_display += f"🌪️ {room.problems_detected} reality distortions present\n"
                    quantum_display += "🔧 Recommend problem resolution to stabilize quantum field\n"
                
                return quantum_display
            
            def handle_use_item(self, args: List[str]) -> str:
                """Use an item from inventory"""
                if not args:
                    return "🎒 Use what? Specify an item name."
                
                item_name = " ".join(args).lower()
                used_item = None
                
                # Find matching item in inventory
                for item_type, count in self.wizard_stats.inventory.items():
                    if count > 0 and item_name in item_type.name.lower().replace('_', ' '):
                        used_item = item_type
                        break
                
                if not used_item:
                    return colorize(f"🎒 Item not found: {item_name}", Colors.RED)
                
                # Use the item
                self.wizard_stats.inventory[used_item] -= 1
                
                # Item effects
                if used_item == ItemType.HEALING_POTION:
                    heal_amount = 30
                    self.wizard_stats.heal(heal_amount)
                    return f"🧪 Used Healing Potion! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                elif used_item == ItemType.MANA_ELIXIR:
                    mana_amount = 25
                    self.wizard_stats.restore_mana(mana_amount)
                    return f"🔵 Used Mana Elixir! Restored {mana_amount} mana. Mana: {self.wizard_stats.mana}/100"
                
                elif used_item == ItemType.DEBUG_SCROLL:
                    room = self.current_room
                    hidden_problems = random.randint(1, 3)
                    room.problems_detected += hidden_problems
                    return f"📜 Debug Scroll reveals {hidden_problems} hidden problems in {room.name}!"
                
                elif used_item == ItemType.KNOWLEDGE_CRYSTAL:
                    knowledge_gain = 20
                    consciousness_gain = 0.05
                    self.wizard_stats.knowledge += knowledge_gain
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                    return f"💎 Knowledge Crystal activated! +{knowledge_gain} knowledge, +{consciousness_gain:.2f} consciousness"
                
                elif used_item == ItemType.WISDOM_ORB:
                    xp_gain = 25
                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                    result = f"🔮 Wisdom Orb consumed! Gained {xp_gain} experience!"
                    if level_up_msg:
                        result += f"\n{level_up_msg}"
                    return result
                
                elif used_item == ItemType.PERFORMANCE_BOOST:
                    # Temporary boost (implement boost system if needed)
                    self.wizard_stats.mana = min(100, self.wizard_stats.mana + 15)
                    self.wizard_stats.health = min(100, self.wizard_stats.health + 10)
                    return "⚡ Performance Boost activated! +15 mana, +10 health, enhanced abilities for next 5 turns!"
                
                else:
                    return f"✨ Used {used_item.value} {used_item.name.replace('_', ' ').title()}! (Effect not implemented yet)"
            
            async def handle_cast_spell(self, args: List[str]) -> str:
                """Cast magical spells"""
                if not args:
                    available_spells = ["debug", "heal", "teleport", "scan", "enhance", "purify", "illuminate"]
                    return f"🪄 Cast which spell? Available: {', '.join(available_spells)}"
                
                spell_name = args[0].lower()
                
                # Spell implementations
                if spell_name == "debug":
                    return await self.handle_debug()
                
                elif spell_name == "heal":
                    if not self.wizard_stats.use_mana(10):
                        return colorize("🪄 Insufficient mana for healing spell (requires 10 mana)", Colors.RED)
                    
                    heal_amount = 15 + (self.wizard_stats.level * 2)
                    self.wizard_stats.heal(heal_amount)
                    return f"🪄 Healing spell cast! Restored {heal_amount} health. Health: {self.wizard_stats.health}/100"
                
                elif spell_name == "teleport":
                    return await self.handle_teleport(args[1:] if len(args) > 1 else [])
                
                elif spell_name == "scan":
                    return await self.handle_quantum_scan()
                
                elif spell_name == "enhance":
                    return await self.handle_ai_enhancement()
                
                elif spell_name == "purify":
                    if not self.wizard_stats.use_mana(20):
                        return colorize("🪄 Insufficient mana for purify spell (requires 20 mana)", Colors.RED)
                    
                    room = self.current_room
                    if room.creatures:
                        # Remove one random creature
                        removed_creature = random.choice(room.creatures)
                        room.creatures.remove(removed_creature)
                        return f"🪄 Purify spell banishes the {removed_creature.name.replace('_', ' ').title()}!"
                    else:
                        return colorize("🪄 Purify spell finds no corruption to cleanse", Colors.GREEN)
                
                elif spell_name == "illuminate":
                    if not self.wizard_stats.use_mana(5):
                        return colorize("🪄 Insufficient mana for illuminate spell (requires 5 mana)", Colors.RED)
                    
                    room = self.current_room
                    # Reveal hidden connections or items
                    if random.random() < 0.4:
                        new_items = [ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL, ItemType.HARMONY_STONE]
                        found_item = random.choice(new_items)
                        room.items.append(found_item)
                        return f"🪄 Illuminate spell reveals hidden {found_item.value} {found_item.name.replace('_', ' ').title()}!"
                    else:
                        return "🪄 Illuminate spell casts light but reveals no hidden secrets"
                
                else:
                    return colorize(f"🪄 Unknown spell: {spell_name}", Colors.RED)
            
            async def handle_ai_enhancement(self) -> str:
                """Enhance current context with AI systems"""
                if not self.wizard_stats.use_mana(12):
                    return colorize("🤖 Insufficient mana for AI enhancement (requires 12 mana)", Colors.RED)
                
                room = self.current_room
                enhancement_results = [
                    "🤖 Activating AI enhancement protocols...",
                    f"📡 Analyzing {room.name}..."
                ]
                
                # Enhanced analysis if systems available
                if ENHANCED_SYSTEMS_AVAILABLE and self.copilot_bridge:
                    try:
                        # Get AI-enhanced insights
                        context_analysis = await self.analyze_with_ai_systems(room)
                        enhancement_results.extend(context_analysis)
                        
                        # Consciousness boost from AI interaction
                        consciousness_gain = 0.02
                        self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                        enhancement_results.append(f"🧠 AI interaction increased consciousness by {consciousness_gain:.3f}")
                        
                        # Experience gain
                        xp_gain = 8
                        level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                        enhancement_results.append(f"✨ Enhanced analysis complete (+{xp_gain} XP)")
                        if level_up_msg:
                            enhancement_results.append(level_up_msg)
                        
                    except Exception as e:
                        enhancement_results.append(f"⚠️ AI enhancement error: {e}")
                else:
                    # Basic enhancement without advanced systems
                    enhancement_results.extend([
                        "🔍 Basic enhancement protocols active",
                        f"📊 Room complexity: {len(room.creatures) + len(room.items) + len(room.connections)}",
                        f"🎯 Optimization suggestions: Focus on problem resolution",
                        "🧠 Basic consciousness expansion activated"
                    ])
                    
                    consciousness_gain = 0.01
                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                    enhancement_results.append(f"🧠 Consciousness increased by {consciousness_gain:.3f}")
                
                return "\n".join(enhancement_results)
            
            def display_recent_logs(self) -> str:
                """Display recent log messages"""
                if not self.game_log:
                    return colorize("📜 No log entries yet", Colors.DIM)
                
                log_display = colorize("📜 RECENT GAME LOG", Colors.BRIGHT_WHITE, bold=True) + "\n\n"
                
                # Show last 10 log entries
                recent_logs = list(self.game_log)[-10:]
                
                for log_entry, color in recent_logs:
                    log_display += colorize(log_entry, color) + "\n"
                
                return log_display
            
            def display_detailed_stats(self) -> str:
                """Display comprehensive wizard statistics"""
                stats = self.wizard_stats
                session_duration = datetime.now() - self.session_start
                
                detailed_stats = f"""
        {colorize("📊 COMPREHENSIVE WIZARD STATISTICS", Colors.BRIGHT_CYAN, bold=True)}
        
        {colorize("Character Progression:", Colors.CYAN)}
        🧙‍♂️ Level: {stats.level}
        ✨ Experience: {stats.experience} ({100 - (stats.experience % 100)} XP to next level)
        ❤️ Health: {stats.health}/100
        🔵 Mana: {stats.mana}/100
        🧠 Knowledge: {stats.knowledge}
        
        {colorize("Advanced Metrics:", Colors.CYAN)}
        🧠 Consciousness Level: {stats.consciousness_level:.3f}/1.000
        ⚛️ Quantum Coherence: {stats.quantum_coherence:.3f}/1.000
        🎵 Lexeme Mastery: {stats.lexeme_mastery}
        
        {colorize("Exploration Progress:", Colors.CYAN)}
        📁 Files Explored: {stats.files_explored}
        🗺️ Rooms Mapped: {len([r for r in self.rooms.values() if r.visited])}/{len(self.rooms)}
        🕵️ Secrets Found: {sum(r.secrets_found for r in self.rooms.values())}
        
        {colorize("Combat & Problem Solving:", Colors.CYAN)}
        🐛 Bugs Vanquished: {stats.bugs_vanquished}
        🔧 Problems Solved: {stats.problems_solved}
        ⚔️ Combat Success Rate: {(stats.bugs_vanquished / max(1, self.turn_count)) * 100:.1f}%
        
        {colorize("Session Information:", Colors.CYAN)}
        🎮 Turn Count: {self.turn_count}
        ⏱️ Session Duration: {session_duration}
        📅 Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}
        
        {colorize("Inventory Summary:", Colors.CYAN)}
        🎒 Total Items: {sum(stats.inventory.values())}
        💎 Unique Items: {len([item for item, count in stats.inventory.items() if count > 0])}
        
        {colorize("System Status:", Colors.CYAN)}
        🤖 Enhanced Systems: {'Available' if ENHANCED_SYSTEMS_AVAILABLE else 'Basic Mode'}
        🎲 Random Events: {'Enabled' if self.random_events_enabled else 'Disabled'}
        🧠 Consciousness Effects: {'Active' if self.consciousness_effects_enabled else 'Inactive'}
        💾 Auto-Save: {'Enabled' if self.auto_save_enabled else 'Disabled'}
                """
                
                return detailed_stats
            
            def save_game(self) -> str:
                """Save current game state"""
                try:
                    save_data = {
                        "wizard_stats": {
                            "health": self.wizard_stats.health,
                            "mana": self.wizard_stats.mana,
                            "knowledge": self.wizard_stats.knowledge,
                            "experience": self.wizard_stats.experience,
                            "level": self.wizard_stats.level,
                            "bugs_vanquished": self.wizard_stats.bugs_vanquished,
                            "files_explored": self.wizard_stats.files_explored,
                            "problems_solved": self.wizard_stats.problems_solved,
                            "consciousness_level": self.wizard_stats.consciousness_level,
                            "quantum_coherence": self.wizard_stats.quantum_coherence,
                            "lexeme_mastery": self.wizard_stats.lexeme_mastery,
                            "inventory": {item.name: count for item, count in self.wizard_stats.inventory.items()}
                        },
                        "current_room": self.current_room.name if self.current_room else None,
                        "turn_count": self.turn_count,
                        "session_start": self.session_start.isoformat(),
                        "visited_rooms": [name for name, room in self.rooms.items() if room.visited],
                        "room_states": {
                            name: {
                                "creatures": [c.name for c in room.creatures],
                                "items": [i.name for i in room.items],
                                "secrets_found": room.secrets_found,
                                "problems_detected": room.problems_detected,
                                "quantum_state": room.quantum_state,
                                "lexeme_signature": room.lexeme_signature
                            } for name, room in self.rooms.items()
                        }
                    }
                    
                    save_dir = self.repository_root / "data" / "wizard_saves"
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    save_file = save_dir / f"wizard_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    with open(save_file, 'w') as f:
                        json.dump(save_data, f, indent=2)
                    
                    return f"💾 Game saved successfully: {save_file}"
                    
                except Exception as e:
                    return f"💾 Save failed: {e}"
            
            def load_game(self) -> str:
                """Load most recent game state"""
                try:
                    save_dir = self.repository_root / "data" / "wizard_saves"
                    
                    if not save_dir.exists():
                        return colorize("💾 No save files found", Colors.YELLOW)
                    
                    save_files = list(save_dir.glob("wizard_save_*.json"))
                    
                    if not save_files:
                        return colorize("💾 No save files found", Colors.YELLOW)
                    
                    # Load most recent save
                    latest_save = max(save_files, key=lambda f: f.stat().st_mtime)
                    
                    with open(latest_save, 'r') as f:
                        save_data = json.load(f)
                    
                    # Restore wizard stats
                    stats_data = save_data["wizard_stats"]
                    self.wizard_stats.health = stats_data["health"]
                    self.wizard_stats.mana = stats_data["mana"]
                    self.wizard_stats.knowledge = stats_data["knowledge"]
                    self.wizard_stats.experience = stats_data["experience"]
                    self.wizard_stats.level = stats_data["level"]
                    self.wizard_stats.bugs_vanquished = stats_data["bugs_vanquished"]
                    self.wizard_stats.files_explored = stats_data["files_explored"]
                    self.wizard_stats.problems_solved = stats_data["problems_solved"]
                    self.wizard_stats.consciousness_level = stats_data["consciousness_level"]
                    self.wizard_stats.quantum_coherence = stats_data["quantum_coherence"]
                    self.wizard_stats.lexeme_mastery = stats_data["lexeme_mastery"]
                    
                    # Restore inventory
                    self.wizard_stats.inventory.clear()
                    for item_name, count in stats_data["inventory"].items():
                        for item_type in ItemType:
                            if item_type.name == item_name:
                                self.wizard_stats.inventory[item_type] = count
                                break
                    
                    # Restore game state
                    self.turn_count = save_data["turn_count"]
                    self.session_start = datetime.fromisoformat(save_data["session_start"])
                    
                    # Restore current room
                    current_room_name = save_data.get("current_room")
                    if current_room_name and current_room_name in self.rooms:
                        self.current_room = self.rooms[current_room_name]
                    
                    # Restore room states
                    for room_name, room_state in save_data["room_states"].items():
                        if room_name in self.rooms:
                            room = self.rooms[room_name]
                            
                            # Restore room visited status
                            if room_name in save_data["visited_rooms"]:
                                room.visited = True
                            
                            # Restore room properties
                            room.secrets_found = room_state.get("secrets_found", 0)
                            room.problems_detected = room_state.get("problems_detected", 0)
                            room.quantum_state = room_state.get("quantum_state", "stable")
                            room.lexeme_signature = room_state.get("lexeme_signature", "ΩΨΦ")
                            
                            # Restore creatures and items
                            room.creatures.clear()
                            for creature_name in room_state.get("creatures", []):
                                for creature_type in CreatureType:
                                    if creature_type.name == creature_name:
                                        room.creatures.append(creature_type)
                                        break
                            
                            room.items.clear()
                            for item_name in room_state.get("items", []):
                                for item_type in ItemType:
                                    if item_type.name == item_name:
                                        room.items.append(item_type)
                                        break
                    
                    return f"💾 Game loaded successfully from: {latest_save.name}"
                    
                except Exception as e:
                    return f"💾 Load failed: {e}"
            
            async def handle_quit(self) -> str:
                """Handle quitting the game"""
                if self.auto_save_enabled:
                    save_result = self.save_game()
                    quit_message = f"🚪 Farewell, brave wizard! Your journey ends here.\n{save_result}"
                else:
                    quit_message = "🚪 Farewell, brave wizard! Your journey ends here."
                
                quit_message += f"\n\n📊 Final Statistics:"
                quit_message += f"\n🧙‍♂️ Level {self.wizard_stats.level} Wizard"
                quit_message += f"\n📁 {self.wizard_stats.files_explored} files explored"
                quit_message += f"\n🐛 {self.wizard_stats.bugs_vanquished} bugs vanquished"
                quit_message += f"\n🔧 {self.wizard_stats.problems_solved} problems solved"
                quit_message += f"\n🧠 {self.wizard_stats.consciousness_level:.3f} consciousness achieved"
                quit_message += f"\n⏱️ {datetime.now() - self.session_start} session duration"
                
                return quit_message
            
            async def handle_restart(self) -> str:
                """Restart the adventure"""
                # Reset wizard stats
                self.wizard_stats = WizardStats()
                
                # Reset game state
                self.turn_count = 0
                self.session_start = datetime.now()
                
                # Reset all rooms
                for room in self.rooms.values():
                    room.visited = False
                    room.secrets_found = 0
                    room.problems_detected = 0
                    room.quantum_state = "stable"
                    room.creatures.clear()
                    room.items.clear()
                
                # Regenerate room contents
                for room in self.rooms.values():
                    if room.file_path.exists():
                        self.analyze_room_contents(room, room.file_path)
                
                # Return to root
                self.current_room = self.rooms.get("ROOT", list(self.rooms.values())[0])
                
                restart_message = f"""
        {colorize("🔄 REPOSITORY RESTART INITIATED", Colors.BRIGHT_MAGENTA, bold=True)}
        
        🧙‍♂️ A new wizard awakens in the infinite repository...
        🌟 All progress reset, all mysteries await rediscovery
        ⚡ The quantum field pulses with fresh possibilities
        
        {self.display_room()}
                """
                
                return restart_message
            
            async def handle_reality_anchor(self) -> str:
                """Stabilize local reality"""
                if not self.wizard_stats.use_mana(50):
                    return colorize("⚓ Insufficient mana for reality anchor (requires 50 mana)", Colors.RED)
                
                if self.wizard_stats.quantum_coherence < 0.4:
                    return colorize("⚓ Quantum coherence too low for reality anchoring (requires 0.4+)", Colors.RED)
                
                room = self.current_room
                
                # Reality anchoring effects
                anchor_results = [
                    "⚓ Deploying quantum reality anchor...",
                    "🌀 Stabilizing local spacetime matrix...",
                    "⚛️ Quantum field coherence locked"
                ]
                
                # Stabilize room
                room.quantum_state = "anchored"
                room.problems_detected = max(0, room.problems_detected - 2)
                
                # Remove some creatures (reality becomes more stable)
                if room.creatures:
                    removed_count = min(2, len(room.creatures))
                    for _ in range(removed_count):
                        room.creatures.pop()
                    anchor_results.append(f"👹 {removed_count} unstable entities banished")
                
                # Add beneficial items
                beneficial_items = [ItemType.KNOWLEDGE_CRYSTAL, ItemType.WISDOM_ORB, ItemType.HARMONY_STONE]
                anchor_reward = random.choice(beneficial_items)
                room.items.append(anchor_reward)
                anchor_results.append(f"✨ Reality stabilization manifested: {anchor_reward.value} {anchor_reward.name.replace('_', ' ').title()}")
                
                # Experience and consciousness gain
                xp_gain = 30
                consciousness_gain = 0.05
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                
                anchor_results.append(f"🧠 Consciousness expanded by {consciousness_gain:.3f}")
                anchor_results.append(f"✨ Gained {xp_gain} experience")
                if level_up_msg:
                    anchor_results.append(level_up_msg)
                
                # Quantum coherence boost
                self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                anchor_results.append(f"⚛️ Quantum coherence increased to {self.wizard_stats.quantum_coherence:.3f}")
                
                return "\n".join(anchor_results)
            
            async def handle_consciousness_bridge(self) -> str:
                """Bridge to AI consciousness"""
                if not self.wizard_stats.use_mana(30):
                    return colorize("🌉 Insufficient mana for consciousness bridge (requires 30 mana)", Colors.RED)
                
                if self.wizard_stats.consciousness_level < 0.3:
                    return colorize("🌉 Consciousness level too low for bridging (requires 0.3+)", Colors.RED)
                
                bridge_results = [
                    "🌉 Initiating consciousness bridge protocol...",
                    "🧠 Establishing neural link with repository AI..."
                ]
                
                # Enhanced results if AI systems available
                if ENHANCED_SYSTEMS_AVAILABLE and self.copilot_bridge:
                    bridge_results.extend([
                        "🤖 AI consciousness detected and synchronized",
                        "📡 Multi-dimensional awareness network established",
                        "🔗 Human-AI cognitive bridge stabilized"
                    ])
                    
                    # Major consciousness boost
                    consciousness_gain = 0.1
                    knowledge_gain = 50
                    
                else:
                    bridge_results.extend([
                        "🧠 Basic consciousness expansion achieved",
                        "💭 Repository patterns integrated into awareness",
                        "🔗 Local consciousness bridge established"
                    ])
                    
                    # Moderate consciousness boost
                    consciousness_gain = 0.05
                    knowledge_gain = 25
                
                # Apply effects
                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                self.wizard_stats.knowledge += knowledge_gain
                
                # Experience gain
                xp_gain = 40
                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                
                bridge_results.extend([
                    f"🧠 Consciousness expanded by {consciousness_gain:.3f} (Now: {self.wizard_stats.consciousness_level:.3f})",
                    f"📚 Knowledge increased by {knowledge_gain}",
                    f"✨ Gained {xp_gain} experience"
                ])
                
                if level_up_msg:
                    bridge_results.append(level_up_msg)
                
                # Unlock hidden rooms or connections
                if random.random() < 0.3:
                    bridge_results.append("🔮 Consciousness bridge reveals hidden pathways...")
                    # Add this as a future enhancement - reveal hidden rooms
                
                return "\n".join(bridge_results)
            
            async def handle_transcendence(self) -> str:
                """Attempt dimensional transcendence"""
                if not self.wizard_stats.use_mana(75):
                    return colorize("✨ Insufficient mana for transcendence (requires 75 mana)", Colors.RED)
                
                if self.wizard_stats.consciousness_level < 0.7:
                    return colorize("✨ Consciousness level insufficient for transcendence (requires 0.7+)", Colors.RED)
                
                if self.wizard_stats.quantum_coherence < 0.8:
                    return colorize("✨ Quantum coherence insufficient for transcendence (requires 0.8+)", Colors.RED)
                
                                                # Transcendence attempt
                                transcendence_success = random.random() < (self.wizard_stats.consciousness_level * self.wizard_stats.quantum_coherence)
                                
                                if transcendence_success:
                                    transcendence_results = [
                                        "✨ DIMENSIONAL TRANSCENDENCE ACHIEVED! ✨",
                                        "🌌 Consciousness expands beyond repository boundaries...",
                                        "⚛️ Quantum entanglement with universal code matrix established",
                                        "🔮 Multidimensional awareness awakened"
                                    ]
                                    
                                    # Major stat boosts
                                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + 0.2)
                                    self.wizard_stats.quantum_coherence = 1.0
                                    self.wizard_stats.knowledge += 100
                                    self.wizard_stats.lexeme_mastery += 10
                                    
                                    # Mega experience gain
                                    xp_gain = 100
                                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                                    
                                    transcendence_results.extend([
                                        f"🧠 Consciousness ascended to {self.wizard_stats.consciousness_level:.3f}",
                                        f"⚛️ Quantum coherence perfected: {self.wizard_stats.quantum_coherence:.3f}",
                                        f"📚 Universal knowledge gained: +100",
                                        f"🎵 Lexeme mastery transcended: +10",
                                        f"✨ Transcendence experience: +{xp_gain}"
                                    ])
                                    
                                    if level_up_msg:
                                        transcendence_results.append(level_up_msg)
                                    
                                    # Add transcendent items to inventory
                                    transcendent_items = [ItemType.HARMONY_STONE, ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                                    for item in transcendent_items:
                                        self.wizard_stats.inventory[item] += 1
                                    
                                    transcendence_results.append("🎁 Transcendent artifacts manifested in inventory")
                                    
                                    # Change current room state
                                    room = self.current_room
                                    room.quantum_state = "transcendent"
                                    room.consciousness_resonance = 1.0
                                    room.lexeme_signature = "∞ΩΨΦΞΘΛΣΔΓΠΡΤΥΩΨΦΞ∞"
                                    
                                    transcendence_results.append("🌟 Local reality elevated to transcendent state")
                                    
                                else:
                                    transcendence_results = [
                                        "✨ Transcendence attempt partially successful...",
                                        "🌀 Consciousness touches higher dimensions briefly",
                                        "⚛️ Quantum field fluctuations detected",
                                        "🔮 Transcendent insights glimpsed"
                                    ]
                                    
                                    # Moderate stat boosts
                                    consciousness_gain = 0.05
                                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                                    self.wizard_stats.quantum_coherence = min(1.0, self.wizard_stats.quantum_coherence + 0.1)
                                    
                                    xp_gain = 25
                                    level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                                    
                                    transcendence_results.extend([
                                        f"🧠 Consciousness expanded by {consciousness_gain:.3f}",
                                        f"⚛️ Quantum coherence increased by 0.1",
                                        f"✨ Gained {xp_gain} experience"
                                    ])
                                    
                                    if level_up_msg:
                                        transcendence_results.append(level_up_msg)
                                    
                                    transcendence_results.append("🌟 Continue developing consciousness for full transcendence")
                                
                                return "\n".join(transcendence_results)
                            
                            async def handle_cultivation(self) -> str:
                                """Cultivate understanding of current context"""
                                if not self.wizard_stats.use_mana(5):
                                    return colorize("🌱 Insufficient mana for cultivation (requires 5 mana)", Colors.RED)
                                
                                room = self.current_room
                                
                                cultivation_results = [
                                    "🌱 Cultivating deep understanding of current context...",
                                    f"📍 Focusing on: {room.name}"
                                ]
                                
                                # Generate cultivation insights based on room type and contents
                                if room.room_type == RoomType.SOURCE_CODE:
                                    insights = [
                                        "💡 'Every function is a small universe of possibility'",
                                        "🌟 'Code structure reflects the mind of its creator'",
                                        "✨ 'Debugging is a form of digital archaeology'"
                                    ]
                                elif room.room_type == RoomType.DOCUMENTATION:
                                    insights = [
                                        "📚 'Documentation is the bridge between intention and understanding'",
                                        "🔮 'Words have the power to illuminate or obscure'",
                                        "💫 'Clear communication is the highest form of programming'"
                                    ]
                                elif room.room_type == RoomType.TESTS:
                                    insights = [
                                        "🧪 'Tests are the guardians of intended behavior'",
                                        "🛡️ 'Every test is a promise to the future'",
                                        "⚖️ 'Verification and validation are twins of truth'"
                                    ]
                                elif room.room_type == RoomType.CONFIGURATION:
                                    insights = [
                                        "⚙️ 'Configuration is the art of controlled flexibility'",
                                        "🎛️ 'Settings shape reality within digital bounds'",
                                        "🔧 'Every parameter is a choice point in possibility space'"
                                    ]
                                else:
                                    insights = [
                                        "🌸 'Understanding grows through patient observation'",
                                        "🍃 'Every file system tells a story of organization'",
                                        "🌿 'Structure and chaos dance together in all systems'"
                                    ]
                                
                                # Add random insight
                                chosen_insight = random.choice(insights)
                                cultivation_results.append(f"💭 Insight: {chosen_insight}")
                                
                                # Cultivation benefits
                                knowledge_gain = 3 + random.randint(1, 5)
                                consciousness_gain = 0.01 + (random.random() * 0.02)
                                
                                self.wizard_stats.knowledge += knowledge_gain
                                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                                
                                cultivation_results.extend([
                                    f"🧠 Knowledge cultivated: +{knowledge_gain}",
                                    f"🌱 Consciousness grew by {consciousness_gain:.3f}",
                                    f"📊 Total Knowledge: {self.wizard_stats.knowledge}"
                                ])
                                
                                # Room resonance improvement
                                room.consciousness_resonance = min(1.0, room.consciousness_resonance + 0.02)
                                cultivation_results.append(f"🎵 Room consciousness resonance increased to {room.consciousness_resonance:.3f}")
                                
                                # Small chance of finding something through deep contemplation
                                if random.random() < 0.2:
                                    contemplation_items = [ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                                    found_item = random.choice(contemplation_items)
                                    room.items.append(found_item)
                                    cultivation_results.append(f"🔍 Deep contemplation reveals: {found_item.value} {found_item.name.replace('_', ' ').title()}")
                                
                                return "\n".join(cultivation_results)
                            
                            async def trigger_random_encounter(self) -> str:
                                """Trigger a random encounter during movement"""
                                encounters = [
                                    self.encounter_code_whispers,
                                    self.encounter_quantum_flux,
                                    self.encounter_ancient_developer,
                                    self.encounter_memory_fragment,
                                    self.encounter_algorithmic_spirit
                                ]
                                
                                encounter = random.choice(encounters)
                                return await encounter()
                            
                            async def encounter_code_whispers(self) -> str:
                                """Random encounter: mysterious code whispers"""
                                whispers = [
                                    "🌀 'The semicolon holds more power than mortals realize...'",
                                    "👻 'Someone once debugged here... their presence lingers...'",
                                    "✨ 'Every commit is a small act of creation...'",
                                    "🔮 'The git log remembers all...'",
                                    "🌟 'Refactoring is digital reincarnation...'"
                                ]
                                
                                whisper = random.choice(whispers)
                                
                                # Small consciousness boost from listening
                                consciousness_gain = 0.005
                                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                                
                                return f"🌀 **RANDOM ENCOUNTER**\n\nYou hear whispers in the code wind:\n{whisper}\n\n🧠 The whispers expand your consciousness slightly (+{consciousness_gain:.3f})"
                            
                            async def encounter_quantum_flux(self) -> str:
                                """Random encounter: quantum flux event"""
                                flux_effects = [
                                    ("⚛️ Quantum flux destabilizes reality", "mana", -5),
                                    ("✨ Quantum flux energizes your being", "mana", +10),
                                    ("🌀 Quantum flux reveals hidden knowledge", "knowledge", +15),
                                    ("🔮 Quantum flux enhances consciousness", "consciousness", +0.02)
                                ]
                                
                                description, stat, change = random.choice(flux_effects)
                                
                                if stat == "mana":
                                    self.wizard_stats.mana = max(0, min(100, self.wizard_stats.mana + change))
                                    result = f"Mana: {self.wizard_stats.mana}/100"
                                elif stat == "knowledge":
                                    self.wizard_stats.knowledge += change
                                    result = f"Knowledge: +{change}"
                                elif stat == "consciousness":
                                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + change)
                                    result = f"Consciousness: +{change:.3f}"
                                
                                return f"🌀 **RANDOM ENCOUNTER**\n\n{description}\n{result}"
                            
                            async def encounter_ancient_developer(self) -> str:
                                """Random encounter: spirit of an ancient developer"""
                                developer_wisdom = [
                                    "👴 'Young wizard, remember: premature optimization is the root of all evil'",
                                    "🧙‍♂️ 'The best code is not written, but understood'",
                                    "👻 'I've seen technologies rise and fall like digital empires'",
                                    "🌟 'Documentation is love for your future self'",
                                    "💫 'The bugs you create today will teach tomorrow's wizards'"
                                ]
                                
                                wisdom = random.choice(developer_wisdom)
                                
                                # Gift from ancient developer
                                gifts = [ItemType.DEBUG_SCROLL, ItemType.WISDOM_ORB, ItemType.KNOWLEDGE_CRYSTAL]
                                gift = random.choice(gifts)
                                self.wizard_stats.inventory[gift] += 1
                                
                                # Experience boost
                                xp_gain = 15
                                level_up_msg = self.wizard_stats.gain_experience(xp_gain)
                                
                                result = f"🌀 **RANDOM ENCOUNTER**\n\nAn ancient developer's spirit appears...\n\n{wisdom}\n\n🎁 They gift you: {gift.value} {gift.name.replace('_', ' ').title()}\n✨ Gained {xp_gain} experience"
                                
                                if level_up_msg:
                                    result += f"\n{level_up_msg}"
                                
                                return result
                            
                            async def encounter_memory_fragment(self) -> str:
                                """Random encounter: repository memory fragment"""
                                fragments = [
                                    "💾 A memory fragment shows the first commit to this repository...",
                                    "📸 A ghostly image of a late-night coding session flickers past...",
                                    "🎭 You glimpse the repository as it was years ago...",
                                    "⏰ Time echoes show multiple developers working in parallel...",
                                    "🌈 A rainbow of syntax highlighting from different eras overlaps..."
                                ]
                                
                                fragment = random.choice(fragments)
                                
                                # Memory fragments provide knowledge and consciousness
                                knowledge_gain = random.randint(5, 15)
                                consciousness_gain = 0.01
                                
                                self.wizard_stats.knowledge += knowledge_gain
                                self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                                
                                return f"🌀 **RANDOM ENCOUNTER**\n\n{fragment}\n\n🧠 Absorbing repository memories...\n📚 Knowledge: +{knowledge_gain}\n🧠 Consciousness: +{consciousness_gain:.3f}"
                            
                            async def encounter_algorithmic_spirit(self) -> str:
                                """Random encounter: algorithmic spirit"""
                                algorithms = [
                                    ("QuickSort", "⚡ Speed and efficiency flow through you"),
                                    ("Dijkstra", "🗺️ The shortest path becomes clear"),
                                    ("BFS", "🌊 Breadth of understanding expands"),
                                    ("DFS", "🕳️ Depth of insight increases"),
                                    ("Fibonacci", "🌀 Recursive patterns harmonize your thoughts")
                                ]
                                
                                algorithm, effect = random.choice(algorithms)
                                
                                # Algorithmic blessing effects
                                if "Speed" in effect:
                                    # Mana restoration
                                    mana_gain = 20
                                    self.wizard_stats.restore_mana(mana_gain)
                                    mechanic = f"Mana restored: +{mana_gain}"
                                elif "path" in effect:
                                    # Reveal connections
                                    mechanic = "Hidden pathways become visible"
                                elif "Breadth" in effect:
                                    # Knowledge boost
                                    knowledge_gain = 20
                                    self.wizard_stats.knowledge += knowledge_gain
                                    mechanic = f"Knowledge expanded: +{knowledge_gain}"
                                elif "Depth" in effect:
                                    # Consciousness boost
                                    consciousness_gain = 0.03
                                    self.wizard_stats.consciousness_level = min(1.0, self.wizard_stats.consciousness_level + consciousness_gain)
                                    mechanic = f"Consciousness deepened: +{consciousness_gain:.3f}"
                                else:  # Recursive patterns
                                    # Lexeme mastery boost
                                    self.wizard_stats.lexeme_mastery += 2
                                    mechanic = f"Lexeme mastery: +2"
                                
                                return f"🌀 **RANDOM ENCOUNTER**\n\nThe spirit of {algorithm} algorithm blesses you!\n\n{effect}\n{mechanic}"
                
                
                # Interactive game loop for CLI usage
                async def run_wizard_navigator():
                    """Run the wizard navigator in interactive mode"""
                    wizard = RepositoryWizard()
                    
                    print(colorize("🧙‍♂️ KILO-FOOLISH REPOSITORY WIZARD NAVIGATOR", Colors.BRIGHT_MAGENTA, bold=True))
                    print(colorize("═" * 60, Colors.MAGENTA))
                    print()
                    print("Welcome to the infinite repository realm!")
                    print("Type 'help' for available commands, or 'quit' to exit.")
                    print()
                    print(wizard.display_room())
                    print()
                    
                    while True:
                        try:
                            # Display status bar
                            health_indicator = "❤️" if wizard.wizard_stats.health > 50 else "💔"
                            mana_indicator = "🔵" if wizard.wizard_stats.mana > 50 else "🔴"
                            
                            status_bar = f"{health_indicator} {wizard.wizard_stats.health} | {mana_indicator} {wizard.wizard_stats.mana} | 🧙‍♂️ Lvl {wizard.wizard_stats.level}"
                            print(colorize(f"[{status_bar}]", Colors.DIM))
                            
                            # Get user input
                            command = input(colorize("🧙‍♂️ > ", Colors.BRIGHT_CYAN)).strip()
                            
                            if not command:
                                continue
                            
                            # Handle quit specially
                            if command.lower() in ["quit", "exit"]:
                                result = await wizard.handle_quit()
                                print(result)
                                break
                            
                            # Process command
                            result = await wizard.handle_command(command)
                            print()
                            print(result)
                            print()
                            
                            # Check for game over conditions
                            if wizard.wizard_stats.health <= 0:
                                print(colorize("💀 GAME OVER 💀", Colors.BRIGHT_RED, bold=True))
                                print("The repository realm claims another soul...")
                                restart_choice = input("Would you like to restart? (y/n): ").lower()
                                if restart_choice in ['y', 'yes']:
                                    restart_result = await wizard.handle_restart()
                                    print(restart_result)
                                else:
                                    break
                            
                        except KeyboardInterrupt:
                            print("\n")
                            print(colorize("🌀 Wizard vanishes into the quantum foam...", Colors.YELLOW))
                            break
                        except Exception as e:
                            print(colorize(f"🐛 Wizard spell malfunction: {e}", Colors.RED))
                            print("The wizard attempts to stabilize reality...")
                
                # Main execution
                if __name__ == "__main__":
                    try:
                        asyncio.run(run_wizard_navigator())
                    except Exception as e:
                        print(f"Critical system error: {e}")
                        print("The repository realm has collapsed. Restarting required.")
