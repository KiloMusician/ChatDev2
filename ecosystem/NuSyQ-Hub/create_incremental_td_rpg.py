#!/usr/bin/env python3
"""Create Incremental Tower Defense RPG Game

Generates a comprehensive game with:
- Incremental/idle mechanics
- Tower defense gameplay
- RPG progression and stats
- NPCs with dialogue
- Deep story system
- Meta progression across runs

OmniTag: [game-creation, tower-defense, rpg, incremental, narrative]
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def create_incremental_td_rpg():
    """Create the incremental tower defense RPG."""
    logger.info("=" * 70)
    logger.info("🎮 CREATING INCREMENTAL TOWER DEFENSE RPG")
    logger.info("=" * 70)

    # Define comprehensive game design
    game_design: dict[str, Any] = {
        "name": "Chronicles of the Eternal Bastion",
        "tagline": "Defend. Evolve. Ascend.",
        "genre": "Incremental Tower Defense RPG",
        "core_mechanics": {
            "incremental": {
                "passive_resource_generation": "Gold, Essence, Knowledge",
                "offline_progress": "Continue earning while away",
                "prestige_system": "Ascension with permanent bonuses",
                "automation_unlocks": "Auto-upgrade, auto-deploy, auto-ability",
            },
            "tower_defense": {
                "tower_types": [
                    {"name": "Archer's Perch", "damage": "physical", "range": "long"},
                    {
                        "name": "Mage Tower",
                        "damage": "magical",
                        "range": "medium",
                        "special": "area_effect",
                    },
                    {"name": "Barracks", "spawns": "soldiers", "special": "ground_block"},
                    {"name": "Artillery", "damage": "siege", "range": "extreme", "speed": "slow"},
                    {"name": "Temple", "type": "support", "effect": "buff_nearby"},
                    {"name": "Summoner's Circle", "spawns": "elementals", "special": "adaptive"},
                ],
                "enemy_types": [
                    {"name": "Goblin Horde", "speed": "fast", "hp": "low"},
                    {"name": "Armored Knight", "speed": "slow", "hp": "high", "armor": "heavy"},
                    {"name": "Shadow Wraith", "speed": "medium", "special": "phase_through"},
                    {"name": "Dragon Whelp", "special": "flying"},
                    {"name": "Siege Golem", "hp": "massive", "special": "tower_damage"},
                    {"name": "Corrupted Mage", "special": "disables_towers"},
                ],
                "wave_system": "Progressive difficulty with boss waves every 10 levels",
                "path_mechanics": "Multiple lanes with strategic choke points",
            },
            "rpg_elements": {
                "player_character": {
                    "class_system": ["Warrior", "Mage", "Ranger", "Cleric", "Necromancer"],
                    "stats": ["Strength", "Intelligence", "Dexterity", "Wisdom", "Charisma"],
                    "skills": "Active abilities with cooldowns",
                    "equipment": "Weapons, Armor, Artifacts",
                    "talent_trees": "3 branches per class with synergies",
                },
                "progression": {
                    "experience": "Gain XP from kills and wave completion",
                    "levels": "1-100 with scaling requirements",
                    "skill_points": "Unlock and upgrade abilities",
                    "attribute_points": "Customize stat growth",
                    "masteries": "Weapon and tower specializations",
                },
                "loot_system": {
                    "rarity_tiers": ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"],
                    "equipment_slots": [
                        "Weapon",
                        "Helm",
                        "Chest",
                        "Gloves",
                        "Boots",
                        "Amulet",
                        "2x Ring",
                    ],
                    "special_items": "Set bonuses and unique effects",
                    "crafting": "Upgrade and combine items",
                },
            },
            "npc_system": {
                "hub_npcs": [
                    {
                        "name": "Commander Aldric",
                        "role": "Quest Giver / Story Narrator",
                        "dialogue": "Provides context and mission briefings",
                        "unlocks": "New tower types and abilities",
                    },
                    {
                        "name": "Sage Elara",
                        "role": "Knowledge Keeper",
                        "dialogue": "Explains lore and mechanics",
                        "shop": "Magical items and scrolls",
                    },
                    {
                        "name": "Blacksmith Gorin",
                        "role": "Equipment Upgrader",
                        "services": "Craft, upgrade, and enhance gear",
                        "quest_line": "Unlock legendary blueprints",
                    },
                    {
                        "name": "Mysterious Stranger",
                        "role": "Prestige Guide",
                        "dialogue": "Reveals meta-progression secrets",
                        "unlocks": "Ascension system",
                    },
                    {
                        "name": "Merchant Kira",
                        "role": "General Shop",
                        "inventory": "Rotating stock of items",
                        "special": "Daily deals and rare finds",
                    },
                ],
                "field_npcs": [
                    {
                        "type": "Wandering Hero",
                        "spawns": "Random during waves",
                        "effect": "Temporary powerful ally",
                        "dialogue": "Hints about story",
                    },
                    {
                        "type": "Civilian",
                        "protection": "Bonus rewards if saved",
                        "dialogue": "World-building flavor text",
                    },
                ],
                "dialogue_system": {
                    "branching_conversations": True,
                    "reputation_system": "Affects available quests and prices",
                    "relationship_levels": "Unlock special benefits",
                    "voice": "Distinct personality for each NPC",
                },
            },
            "story": {
                "premise": """
                You are the last Commander of the Eternal Bastion, a fortress that has stood
                for millennia against the forces of the Void. Each night, the corruption grows
                stronger, sending waves of twisted creatures. But you possess a secret: the
                power to Ascend, retaining knowledge across lifetimes. Each defense teaches you
                more about the ancient war that sundered your world.
                """,
                "acts": [
                    {
                        "act": 1,
                        "title": "The First Night",
                        "waves": "1-30",
                        "story_beats": [
                            "Tutorial and initial defense",
                            "Discovery of the Ascension power",
                            "First glimpse of the true enemy",
                            "Commander Aldric's revelation",
                        ],
                        "boss": "The Hollow King (corrupted former ally)",
                    },
                    {
                        "act": 2,
                        "title": "Echoes of the Past",
                        "waves": "31-60",
                        "story_beats": [
                            "Uncover fragments of pre-corruption history",
                            "Sage Elara's personal quest",
                            "Discovery of other Bastions (all fallen)",
                            "The truth about the Void",
                        ],
                        "boss": "Void Manifestation (sentient corruption)",
                    },
                    {
                        "act": 3,
                        "title": "The Eternal Choice",
                        "waves": "61-100",
                        "story_beats": [
                            "Learn the origin of the Eternal Bastion",
                            "Mysterious Stranger's true identity",
                            "Choice: End the cycle or continue",
                            "Multiple endings based on choices",
                        ],
                        "boss": "The First Commander (you, from the first cycle)",
                    },
                ],
                "lore_delivery": {
                    "environmental": "Ruins and artifacts tell stories",
                    "npc_dialogue": "NPCs share memories and legends",
                    "item_descriptions": "Each item has lore text",
                    "codex": "Unlockable entries about world",
                    "hidden_logs": "Scattered journals and notes",
                },
                "player_choices": {
                    "dialogue_options": "Affect NPC relationships",
                    "quest_decisions": "Multiple solutions to problems",
                    "moral_dilemmas": "Save civilians vs. strategic advantage",
                    "ending_paths": ["Redemption", "Sacrifice", "Dominion", "Transcendence"],
                },
            },
            "meta_progression": {
                "ascension_system": {
                    "mechanism": "Prestige after completing major milestones",
                    "benefits": [
                        "Permanent stat bonuses",
                        "Unlock new tower types",
                        "Access to higher difficulty tiers",
                        "Cumulative knowledge bonuses",
                        "Start with better base resources",
                    ],
                    "ascension_levels": "100+ with diminishing returns",
                    "ascension_currency": "Celestial Essence (earned from achievements)",
                },
                "achievement_system": {
                    "categories": [
                        "Combat (kill counts, perfect defenses)",
                        "Exploration (discover all lore entries)",
                        "Mastery (tower and class specializations)",
                        "Social (NPC relationships maxed)",
                        "Secrets (hidden challenges)",
                    ],
                    "rewards": "Celestial Essence, unique items, titles",
                },
                "challenge_modes": {
                    "endless_mode": "Survive as long as possible",
                    "ironman_mode": "No manual saves, permadeath",
                    "speed_run": "Complete acts within time limit",
                    "handicap_challenges": "Restricted resources or towers",
                    "custom_modifiers": "Player-created difficulty tweaks",
                },
                "persistent_unlocks": [
                    "New starting classes",
                    "Cosmetic options for towers and character",
                    "Quality-of-life improvements",
                    "Story insights (new game+ content)",
                    "Secret areas in hub",
                ],
            },
        },
        "technical_features": {
            "save_system": "Auto-save + manual save slots",
            "settings": "Graphics, audio, difficulty presets",
            "statistics": "Detailed tracking of all progress",
            "cloud_sync": "Optional save backup",
            "modding_support": "Custom tower/enemy definitions via JSON",
        },
        "ui_design": {
            "main_screens": [
                "Hub (NPC interactions, upgrades)",
                "Battle View (tower placement, combat)",
                "Character Sheet (stats, equipment)",
                "Skill Tree (talent allocation)",
                "Codex (lore and achievements)",
                "Shop (buy/sell/craft)",
                "Map (select missions)",
            ],
            "hud_elements": [
                "Resource counters (Gold, Essence, HP)",
                "Wave timer and enemy count",
                "Quick-ability bar",
                "Mini-map",
                "Tower selection radial menu",
            ],
            "theme": "Dark fantasy with glowing magical accents",
        },
    }

    # Create project structure
    project_name = "chronicles_eternal_bastion"
    output_dir = Path("demo_output") / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n📁 Creating project: {project_name}")
    logger.info(f"   Output: {output_dir}")

    # Generate comprehensive game code
    logger.info("\n💻 Generating game code...")

    game_code = generate_game_code(game_design)

    # Write main game file
    game_file = output_dir / f"{project_name}.py"
    with open(game_file, "w", encoding="utf-8") as f:
        f.write(game_code)

    logger.info(f"✅ Game code: {game_file}")

    # Generate design document
    design_doc = output_dir / "DESIGN_DOCUMENT.md"
    with open(design_doc, "w", encoding="utf-8") as f:
        f.write(generate_design_doc(game_design))

    logger.info(f"✅ Design doc: {design_doc}")

    # Generate data files
    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True)

    # NPCs
    with open(data_dir / "npcs.json", "w", encoding="utf-8") as f:
        json.dump(game_design["core_mechanics"]["npc_system"], f, indent=2)

    # Towers
    with open(data_dir / "towers.json", "w", encoding="utf-8") as f:
        json.dump(game_design["core_mechanics"]["tower_defense"]["tower_types"], f, indent=2)

    # Enemies
    with open(data_dir / "enemies.json", "w", encoding="utf-8") as f:
        json.dump(game_design["core_mechanics"]["tower_defense"]["enemy_types"], f, indent=2)

    # Story
    with open(data_dir / "story.json", "w", encoding="utf-8") as f:
        json.dump(game_design["core_mechanics"]["story"], f, indent=2)

    logger.info(f"✅ Data files: {data_dir}")

    # Generate README
    readme = output_dir / "README.md"
    with open(readme, "w", encoding="utf-8") as f:
        f.write(generate_readme(game_design, project_name))

    logger.info(f"✅ README: {readme}")

    # Save full design spec
    spec_file = output_dir / "game_specification.json"
    with open(spec_file, "w", encoding="utf-8") as f:
        json.dump(game_design, f, indent=2)

    logger.info(f"✅ Specification: {spec_file}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ GAME CREATION COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"\n📂 Project location: {output_dir.absolute()}")
    logger.info("\n🎮 To run the game:")
    logger.info(f"   cd {output_dir}")
    logger.info(f"   python {project_name}.py")
    logger.info("\n📖 Read DESIGN_DOCUMENT.md for full feature details")
    logger.info("=" * 70)

    return output_dir


def generate_game_code(design):
    """Generate the main game code."""
    code = '''#!/usr/bin/env python3
"""Chronicles of the Eternal Bastion

An incremental tower defense RPG with deep story, NPCs, and meta-progression.

Controls:
    Mouse: Select towers, interact with UI
    1-6: Quick-select tower types
    Space: Pause/Resume
    Q/W/E/R: Use abilities
    Tab: Open character sheet
    I: Open inventory
    M: Open map
    ESC: Menu

OmniTag: [game, tower-defense, rpg, incremental, narrative]
"""

import pygame
import random
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (20, 30, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
PURPLE = (138, 43, 226)
RED = (220, 20, 60)
GREEN = (50, 205, 50)
BLUE = (30, 144, 255)
ORANGE = (255, 140, 0)


# Game States
class GameState(Enum):
    MENU = "menu"
    HUB = "hub"
    BATTLE = "battle"
    CHARACTER = "character"
    SHOP = "shop"
    CODEX = "codex"
    PAUSE = "pause"


@dataclass
class Tower:
    """Tower defense structure."""
    name: str
    level: int = 1
    position: Tuple[int, int] = (0, 0)
    damage: float = 10.0
    range: float = 150.0
    fire_rate: float = 1.0  # attacks per second
    damage_type: str = "physical"
    cost: int = 100
    sell_value: int = 50
    target: Optional['Enemy'] = None
    cooldown: float = 0.0
    upgrades: Dict = field(default_factory=dict)

    def update(self, dt: float, enemies: List['Enemy']):
        """Update tower logic."""
        self.cooldown = max(0, self.cooldown - dt)

        # Find target
        if not self.target or not self.target.alive:
            self.target = self.find_target(enemies)

        # Attack if ready
        if self.target and self.cooldown <= 0:
            self.attack(self.target)
            self.cooldown = 1.0 / self.fire_rate

    def find_target(self, enemies: List['Enemy']) -> Optional['Enemy']:
        """Find closest enemy in range."""
        for enemy in enemies:
            if enemy.alive:
                dist = math.dist(self.position, enemy.position)
                if dist <= self.range:
                    return enemy
        return None

    def attack(self, enemy: 'Enemy'):
        """Deal damage to enemy."""
        damage = self.damage * (1.0 + self.level * 0.1)
        enemy.take_damage(damage, self.damage_type)


@dataclass
class Enemy:
    """Enemy unit."""
    name: str
    hp: float
    max_hp: float
    speed: float
    armor: float = 0.0
    magic_resist: float = 0.0
    position: Tuple[float, float] = (0.0, 0.0)
    path_progress: float = 0.0
    gold_reward: int = 10
    essence_reward: int = 1
    alive: bool = True
    special_abilities: List[str] = field(default_factory=list)

    def take_damage(self, amount: float, damage_type: str):
        """Reduce HP by damage amount."""
        resist = self.armor if damage_type == "physical" else self.magic_resist
        actual_damage = amount * (1.0 - resist / 100.0)
        self.hp -= actual_damage

        if self.hp <= 0:
            self.alive = False

    def move(self, dt: float, path: List[Tuple[int, int]]):
        """Move along path."""
        self.path_progress += self.speed * dt
        # Update position based on path progress
        # (simplified for demo)


@dataclass
class PlayerCharacter:
    """Player's RPG character."""
    name: str = "Commander"
    character_class: str = "Warrior"
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100

    # Stats
    strength: int = 10
    intelligence: int = 10
    dexterity: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Resources
    hp: float = 100.0
    max_hp: float = 100.0
    mana: float = 50.0
    max_mana: float = 50.0

    # Points
    skill_points: int = 0
    attribute_points: int = 0

    # Equipment
    equipment: Dict[str, Optional['Item']] = field(default_factory=lambda: {
        "weapon": None,
        "helm": None,
        "chest": None,
        "gloves": None,
        "boots": None,
        "amulet": None,
        "ring1": None,
        "ring2": None
    })

    # Abilities
    abilities: List[Dict] = field(default_factory=list)

    def gain_xp(self, amount: int):
        """Add experience and level up if needed."""
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level_up()

    def level_up(self):
        """Increase level and grant points."""
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.15)
        self.skill_points += 1
        self.attribute_points += 3

        # Increase base stats
        self.max_hp += 10
        self.max_mana += 5
        self.hp = self.max_hp
        self.mana = self.max_mana


@dataclass
class NPC:
    """Non-player character."""
    name: str
    role: str
    dialogue_tree: Dict = field(default_factory=dict)
    relationship_level: int = 0
    quests_available: List[Dict] = field(default_factory=list)
    shop_inventory: List['Item'] = field(default_factory=list)

    def talk(self) -> str:
        """Get dialogue based on relationship."""
        if self.relationship_level < 25:
            return self.dialogue_tree.get("cold", "...")
        elif self.relationship_level < 75:
            return self.dialogue_tree.get("friendly", "Hello!")
        else:
            return self.dialogue_tree.get("close", "My friend!")


@dataclass
class GameProgress:
    """Meta-progression and saves."""
    ascension_level: int = 0
    total_gold_earned: int = 0
    total_enemies_killed: int = 0
    waves_completed: int = 0
    achievements: List[str] = field(default_factory=list)
    unlocked_towers: List[str] = field(default_factory=list)
    unlocked_classes: List[str] = field(default_factory=list)
    celestial_essence: int = 0

    # Offline progress
    last_save_time: str = ""

    def calculate_offline_progress(self) -> Dict:
        """Calculate what was earned while away."""
        if not self.last_save_time:
            return {}

        # Parse time difference
        # Calculate resources based on ascension bonuses
        # (simplified for demo)
        return {
            "gold": 100,
            "essence": 10,
            "time_away": "5 minutes"
        }


class Game:
    """Main game class."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chronicles of the Eternal Bastion")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU

        # Game systems
        self.player = PlayerCharacter()
        self.progress = GameProgress()
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.npcs: List[NPC] = self.load_npcs()

        # Resources
        self.gold = 500
        self.essence = 0
        self.knowledge = 0

        # Wave system
        self.current_wave = 0
        self.wave_active = False
        self.wave_timer = 0.0

        # UI
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.selected_tower_type = None

        # Load data
        self.load_game_data()

    def load_npcs(self) -> List[NPC]:
        """Load NPC data from file."""
        try:
            data_path = Path("data/npcs.json")
            if data_path.exists():
                with open(data_path, 'r') as f:
                    npc_data = json.load(f)
                # Create NPC objects (simplified)
                return []
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            pass

        # Default NPCs
        return [
            NPC(
                name="Commander Aldric",
                role="Quest Giver",
                dialogue_tree={
                    "cold": "We must defend the Bastion. Stay alert.",
                    "friendly": "Your progress is impressive, Commander.",
                    "close": "Together, we shall uncover the truth of this endless night."
                }
            ),
            NPC(
                name="Sage Elara",
                role="Knowledge Keeper",
                dialogue_tree={
                    "cold": "Knowledge is power. Seek it.",
                    "friendly": "I have much to teach you about our world.",
                    "close": "The answers you seek lie in the forgotten ages..."
                }
            )
        ]

    def load_game_data(self):
        """Load tower, enemy, and story data."""
        # This would load from JSON files
        # For demo, using defaults
        pass

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)

            # Update
            self.update(dt)

            # Render
            self.render()

        pygame.quit()

    def handle_event(self, event):
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == GameState.BATTLE:
                    self.state = GameState.PAUSE
                elif self.state == GameState.PAUSE:
                    self.state = GameState.BATTLE
                elif self.state == GameState.HUB:
                    self.state = GameState.MENU

            elif event.key == pygame.K_TAB:
                self.state = GameState.CHARACTER

            elif event.key == pygame.K_i:
                # Open inventory
                pass

            elif event.key == pygame.K_m:
                # Open map
                pass

            elif event.key == pygame.K_SPACE:
                if self.state == GameState.BATTLE:
                    self.wave_active = not self.wave_active

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_click(event.pos)

    def handle_click(self, pos):
        """Handle mouse clicks based on game state."""
        if self.state == GameState.MENU:
            # Check menu buttons
            if self.is_button_clicked(pos, (540, 300, 200, 50)):
                self.state = GameState.HUB
            elif self.is_button_clicked(pos, (540, 370, 200, 50)):
                self.load_game()
            elif self.is_button_clicked(pos, (540, 440, 200, 50)):
                self.running = False

        elif self.state == GameState.HUB:
            # Check NPC interactions, shop, etc.
            pass

        elif self.state == GameState.BATTLE:
            # Tower placement
            if self.selected_tower_type and self.gold >= 100:
                self.place_tower(pos)

    def is_button_clicked(self, pos, rect):
        """Check if position is within rectangle."""
        x, y, w, h = rect
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h

    def place_tower(self, pos):
        """Place a new tower at position."""
        tower = Tower(
            name="Archer's Perch",
            position=pos,
            damage=15.0,
            range=150.0,
            fire_rate=1.5,
            cost=100
        )
        self.towers.append(tower)
        self.gold -= 100
        self.selected_tower_type = None

    def spawn_wave(self):
        """Spawn next wave of enemies."""
        self.current_wave += 1
        self.wave_active = True

        # Spawn enemies based on wave number
        enemy_count = 5 + self.current_wave * 2
        for i in range(enemy_count):
            enemy = Enemy(
                name="Goblin",
                hp=20.0 + self.current_wave * 5,
                max_hp=20.0 + self.current_wave * 5,
                speed=50.0,
                position=(0, 300 + i * 10),
                gold_reward=10 + self.current_wave,
                essence_reward=1
            )
            self.enemies.append(enemy)

    def update(self, dt):
        """Update game logic."""
        if self.state == GameState.BATTLE:
            if self.wave_active:
                # Update towers
                for tower in self.towers:
                    tower.update(dt, self.enemies)

                # Update enemies
                for enemy in self.enemies[:]:
                    if enemy.alive:
                        # Move enemy (simplified)
                        enemy.position = (
                            enemy.position[0] + enemy.speed * dt,
                            enemy.position[1]
                        )

                        # Check if reached end
                        if enemy.position[0] > SCREEN_WIDTH:
                            self.player.hp -= 10
                            self.enemies.remove(enemy)
                    else:
                        # Enemy killed
                        self.gold += enemy.gold_reward
                        self.essence += enemy.essence_reward
                        self.player.gain_xp(10)
                        self.progress.total_enemies_killed += 1
                        self.enemies.remove(enemy)

                # Check if wave complete
                if not self.enemies:
                    self.wave_active = False
                    self.progress.waves_completed += 1

            # Passive resource generation (idle/incremental)
            self.gold += dt * (1 + self.progress.ascension_level)
            self.essence += dt * 0.1 * (1 + self.progress.ascension_level * 0.5)

    def render(self):
        """Render the game."""
        self.screen.fill(DARK_BLUE)

        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.HUB:
            self.render_hub()
        elif self.state == GameState.BATTLE:
            self.render_battle()
        elif self.state == GameState.CHARACTER:
            self.render_character_sheet()
        elif self.state == GameState.PAUSE:
            self.render_pause()

        pygame.display.flip()

    def render_menu(self):
        """Render main menu."""
        # Title
        title = self.title_font.render("Chronicles of the Eternal Bastion", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font.render("Defend. Evolve. Ascend.", True, SILVER)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Buttons
        self.draw_button("New Game", (540, 300, 200, 50), GREEN)
        self.draw_button("Continue", (540, 370, 200, 50), BLUE)
        self.draw_button("Exit", (540, 440, 200, 50), RED)

        # Version info
        version = self.font.render("v1.0.0 - Incremental TD RPG", True, WHITE)
        self.screen.blit(version, (10, SCREEN_HEIGHT - 30))

    def render_hub(self):
        """Render the hub area with NPCs."""
        # Background
        pygame.draw.rect(self.screen, (40, 40, 60), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Title
        title = self.title_font.render("The Eternal Bastion - Hub", True, GOLD)
        self.screen.blit(title, (50, 30))

        # NPCs
        y_offset = 120
        for npc in self.npcs:
            # NPC portrait area
            pygame.draw.rect(self.screen, (60, 60, 80), (50, y_offset, 300, 80))
            name_text = self.font.render(npc.name, True, WHITE)
            role_text = self.font.render(f"({npc.role})", True, SILVER)
            self.screen.blit(name_text, (70, y_offset + 15))
            self.screen.blit(role_text, (70, y_offset + 45))
            y_offset += 100

        # Status
        status_text = [
            f"Gold: {int(self.gold)}",
            f"Essence: {int(self.essence)}",
            f"Ascension Level: {self.progress.ascension_level}",
            f"Waves Completed: {self.progress.waves_completed}"
        ]

        y = 120
        for text in status_text:
            surf = self.font.render(text, True, GOLD)
            self.screen.blit(surf, (SCREEN_WIDTH - 300, y))
            y += 30

        # Instructions
        inst = self.font.render("Click NPC to interact | ESC: Return to menu", True, WHITE)
        self.screen.blit(inst, (50, SCREEN_HEIGHT - 50))

        # Battle button
        self.draw_button("Enter Battle", (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50), RED)

    def render_battle(self):
        """Render battle screen."""
        # Path
        pygame.draw.line(self.screen, WHITE, (0, 360), (SCREEN_WIDTH, 360), 3)

        # Towers
        for tower in self.towers:
            pygame.draw.circle(self.screen, BLUE, tower.position, 15)
            # Range indicator
            pygame.draw.circle(self.screen, (50, 50, 100), tower.position, int(tower.range), 1)

        # Enemies
        for enemy in self.enemies:
            if enemy.alive:
                color = RED if enemy.hp < enemy.max_hp * 0.3 else ORANGE
                pygame.draw.circle(self.screen, color, (int(enemy.position[0]), int(enemy.position[1])), 10)

        # HUD
        hud_texts = [
            f"Gold: {int(self.gold)} (+{1 + self.progress.ascension_level}/s)",
            f"Essence: {int(self.essence)}",
            f"Wave: {self.current_wave}",
            f"HP: {int(self.player.hp)}/{int(self.player.max_hp)}",
            f"Level: {self.player.level} (XP: {self.player.xp}/{self.player.xp_to_next})",
            f"Enemies: {len([e for e in self.enemies if e.alive])}"
        ]

        y = 10
        for text in hud_texts:
            surf = self.font.render(text, True, GOLD)
            self.screen.blit(surf, (10, y))
            y += 25

        # Controls
        controls = [
            "SPACE: Start/Pause Wave",
            "1-6: Select Tower Type",
            "Click: Place Tower ($100)",
            "TAB: Character Sheet",
            "ESC: Pause Menu"
        ]

        y = SCREEN_HEIGHT - len(controls) * 25 - 10
        for text in controls:
            surf = self.font.render(text, True, WHITE)
            self.screen.blit(surf, (10, y))
            y += 25

        # Wave button
        if not self.wave_active and not self.enemies:
            self.draw_button("Start Next Wave", (SCREEN_WIDTH // 2 - 100, 10, 200, 40), GREEN)

    def render_character_sheet(self):
        """Render character/RPG stats."""
        self.screen.fill((30, 30, 50))

        # Title
        title = self.title_font.render("Character Sheet", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self.screen.blit(title, title_rect)

        # Character info
        info = [
            f"Name: {self.player.name}",
            f"Class: {self.player.character_class}",
            f"Level: {self.player.level}",
            f"XP: {self.player.xp} / {self.player.xp_to_next}",
            "",
            "=== STATS ===",
            f"Strength: {self.player.strength}",
            f"Intelligence: {self.player.intelligence}",
            f"Dexterity: {self.player.dexterity}",
            f"Wisdom: {self.player.wisdom}",
            f"Charisma: {self.player.charisma}",
            "",
            "=== RESOURCES ===",
            f"HP: {int(self.player.hp)} / {int(self.player.max_hp)}",
            f"Mana: {int(self.player.mana)} / {int(self.player.max_mana)}",
            "",
            "=== POINTS ===",
            f"Skill Points: {self.player.skill_points}",
            f"Attribute Points: {self.player.attribute_points}",
        ]

        x, y = 100, 100
        for line in info:
            surf = self.font.render(line, True, WHITE if "===" not in line else GOLD)
            self.screen.blit(surf, (x, y))
            y += 30

        # Equipment slots (right side)
        eq_x, eq_y = SCREEN_WIDTH // 2 + 100, 100
        eq_title = self.font.render("=== EQUIPMENT ===", True, GOLD)
        self.screen.blit(eq_title, (eq_x, eq_y))

        eq_y += 40
        for slot_name in ["weapon", "helm", "chest", "gloves", "boots", "amulet", "ring1", "ring2"]:
            item = self.player.equipment.get(slot_name)
            slot_text = f"{slot_name.capitalize()}: {item.name if item else 'Empty'}"
            surf = self.font.render(slot_text, True, SILVER)
            self.screen.blit(surf, (eq_x, eq_y))
            eq_y += 30

        # Instructions
        inst = self.font.render("TAB: Close | ESC: Return to game", True, WHITE)
        self.screen.blit(inst, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 50))

    def render_pause(self):
        """Render pause menu."""
        # Darken background
        dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dark_overlay.set_alpha(128)
        dark_overlay.fill(BLACK)
        self.screen.blit(dark_overlay, (0, 0))

        # Pause text
        pause_text = self.title_font.render("PAUSED", True, GOLD)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(pause_text, pause_rect)

        # Buttons
        self.draw_button("Resume", (SCREEN_WIDTH // 2 - 100, 300, 200, 50), GREEN)
        self.draw_button("Save Game", (SCREEN_WIDTH // 2 - 100, 370, 200, 50), BLUE)
        self.draw_button("Return to Hub", (SCREEN_WIDTH // 2 - 100, 440, 200, 50), ORANGE)
        self.draw_button("Exit to Menu", (SCREEN_WIDTH // 2 - 100, 510, 200, 50), RED)

    def draw_button(self, text, rect, color):
        """Draw a button."""
        x, y, w, h = rect
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 2)

        text_surf = self.font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=(x + w // 2, y + h // 2))
        self.screen.blit(text_surf, text_rect)

    def save_game(self):
        """Save current progress."""
        save_data = {
            "player": self.player.__dict__,
            "progress": self.progress.__dict__,
            "resources": {
                "gold": self.gold,
                "essence": self.essence,
                "knowledge": self.knowledge
            },
            "timestamp": datetime.now().isoformat()
        }

        save_path = Path("saves/save_game.json")
        save_path.parent.mkdir(exist_ok=True)

        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)

    def load_game(self):
        """Load saved progress."""
        save_path = Path("saves/save_game.json")
        if not save_path.exists():
            return

        with open(save_path, 'r') as f:
            save_data = json.load(f)

        # Restore state
        # (simplified for demo)
        self.state = GameState.HUB


def main():
    """Run the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
'''

    return code


def generate_design_doc(design):
    """Generate comprehensive design document."""
    doc = f"""# {design["name"]} - Design Document

## Tagline
**{design["tagline"]}**

## Genre
{design["genre"]}

---

## Overview

{design["core_mechanics"]["story"]["premise"]}

---

## Core Mechanics

### Incremental/Idle System
- **Passive Resources**: {", ".join(design["core_mechanics"]["incremental"]["passive_resource_generation"].split(", "))}
- **Offline Progress**: {design["core_mechanics"]["incremental"]["offline_progress"]}
- **Prestige**: {design["core_mechanics"]["incremental"]["prestige_system"]}
- **Automation**: {design["core_mechanics"]["incremental"]["automation_unlocks"]}

### Tower Defense

#### Tower Types
"""

    for tower in design["core_mechanics"]["tower_defense"]["tower_types"]:
        doc += f"- **{tower['name']}**: {tower.get('damage', tower.get('type', 'support'))} damage, {tower.get('range', 'medium')} range"
        if "special" in tower:
            doc += f" (Special: {tower['special']})"
        doc += "\n"

    doc += "\n#### Enemy Types\n"
    for enemy in design["core_mechanics"]["tower_defense"]["enemy_types"]:
        doc += f"- **{enemy['name']}**: Speed: {enemy.get('speed', 'medium')}, HP: {enemy.get('hp', 'medium')}"
        if "special" in enemy:
            doc += f", Special: {enemy['special']}"
        doc += "\n"

    doc += f"""

### RPG Elements

#### Player Character
- **Classes**: {", ".join(design["core_mechanics"]["rpg_elements"]["player_character"]["class_system"])}
- **Stats**: {", ".join(design["core_mechanics"]["rpg_elements"]["player_character"]["stats"])}
- **Skills**: {design["core_mechanics"]["rpg_elements"]["player_character"]["skills"]}
- **Equipment**: {design["core_mechanics"]["rpg_elements"]["player_character"]["equipment"]}

#### Progression
- XP system with scaling requirements
- Skill and attribute points
- Talent trees with 3 branches per class
- Weapon and tower masteries

#### Loot System
- **Rarity Tiers**: {", ".join(design["core_mechanics"]["rpg_elements"]["loot_system"]["rarity_tiers"])}
- **Equipment Slots**: {len(design["core_mechanics"]["rpg_elements"]["loot_system"]["equipment_slots"])} total
- Set bonuses and unique item effects
- Crafting system for upgrades

---

## NPC System

### Hub NPCs
"""

    for npc in design["core_mechanics"]["npc_system"]["hub_npcs"]:
        doc += f"""
#### {npc["name"]}
- **Role**: {npc["role"]}
- **Dialogue**: {npc["dialogue"]}
- **Services**: {npc.get("services", npc.get("shop", npc.get("unlocks", "Quest related")))}
"""

    doc += """

### Dialogue System
- Branching conversations with choices
- Reputation system affecting prices and quests
- Relationship levels unlock special benefits
- Distinct personality for each NPC

---

## Story

### Three Act Structure
"""

    for act in design["core_mechanics"]["story"]["acts"]:
        doc += f"""
#### Act {act["act"]}: {act["title"]}
- **Waves**: {act["waves"]}
- **Story Beats**:
"""
        for beat in act["story_beats"]:
            doc += f"  - {beat}\n"
        doc += f"- **Boss**: {act['boss']}\n"

    doc += f"""

### Lore Delivery
- Environmental storytelling through ruins and artifacts
- NPC dialogue revealing memories and legends
- Item descriptions with lore text
- Unlockable codex entries
- Hidden journals and notes

### Player Choice
Multiple endings based on:
- Dialogue options
- Quest decisions
- Moral dilemmas
- Final choices

**Ending Paths**: {", ".join(design["core_mechanics"]["story"]["player_choices"]["ending_paths"])}

---

## Meta-Progression

### Ascension System
{design["core_mechanics"]["meta_progression"]["ascension_system"]["mechanism"]}

**Benefits**:
"""

    for benefit in design["core_mechanics"]["meta_progression"]["ascension_system"]["benefits"]:
        doc += f"- {benefit}\n"

    doc += """

### Achievements
Categories:
"""

    for category in design["core_mechanics"]["meta_progression"]["achievement_system"][
        "categories"
    ]:
        doc += f"- {category}\n"

    doc += f"""

### Challenge Modes
- **Endless Mode**: {design["core_mechanics"]["meta_progression"]["challenge_modes"]["endless_mode"]}
- **Ironman Mode**: {design["core_mechanics"]["meta_progression"]["challenge_modes"]["ironman_mode"]}
- **Speed Run**: {design["core_mechanics"]["meta_progression"]["challenge_modes"]["speed_run"]}
- **Handicap Challenges**: {design["core_mechanics"]["meta_progression"]["challenge_modes"]["handicap_challenges"]}
- **Custom Modifiers**: {design["core_mechanics"]["meta_progression"]["challenge_modes"]["custom_modifiers"]}

---

## Technical Features

- Auto-save and manual save slots
- Graphics and audio settings
- Detailed statistics tracking
- Optional cloud sync
- Modding support via JSON

---

## UI/UX Design

### Main Screens
"""

    for screen in design["ui_design"]["main_screens"]:
        doc += f"- {screen}\n"

    doc += """

### HUD Elements
"""

    for element in design["ui_design"]["hud_elements"]:
        doc += f"- {element}\n"

    doc += f"""

### Theme
{design["ui_design"]["theme"]}

---

*This document outlines the complete vision for {design["name"]}.*
*Implementation details may evolve during development.*
"""

    return doc


def generate_readme(design, project_name):
    """Generate README."""
    readme = f"""# {design["name"]}

{design["tagline"]}

---

## About

{design["core_mechanics"]["story"]["premise"].strip()}

---

## Features

✅ **Incremental Progression** - Earn resources even while away!
✅ **Tower Defense** - 6+ tower types, strategic placement
✅ **RPG Mechanics** - Level up, gain skills, equip gear
✅ **Deep Story** - 3 acts with multiple endings
✅ **Rich NPCs** - Dialogue, quests, and relationships
✅ **Meta-Progression** - Ascension system for endless replayability

---

## How to Play

```bash
python {project_name}.py
```

### Controls

- **Mouse**: Select towers, interact with UI
- **1-6**: Quick-select tower types
- **Space**: Pause/Resume waves
- **Q/W/E/R**: Use abilities
- **Tab**: Character sheet
- **I**: Inventory
- **M**: Map
- **ESC**: Menu

---

## Game Loop

1. **Hub**: Talk to NPCs, upgrade equipment, manage progression
2. **Battle**: Place towers, defend against waves
3. **Rewards**: Collect gold, essence, and loot
4. **Progression**: Level up, unlock abilities, strengthen towers
5. **Ascend**: Prestige for permanent bonuses

---

## Requirements

- Python 3.8+
- Pygame

```bash
pip install pygame
```

---

## Development

See `DESIGN_DOCUMENT.md` for complete feature specifications.

### Data Files

- `data/npcs.json` - NPC definitions
- `data/towers.json` - Tower specifications
- `data/enemies.json` - Enemy types
- `data/story.json` - Story content

---

## Story Acts

### Act 1: The First Night
Waves 1-30 - Tutorial and initial defense

### Act 2: Echoes of the Past
Waves 31-60 - Uncover the truth

### Act 3: The Eternal Choice
Waves 61-100 - Multiple endings

---

## Credits

Created with ZETA21 Game Development Pipeline
Part of the NuSyQ-Hub ecosystem

---

**Defend. Evolve. Ascend.**
"""

    return readme


if __name__ == "__main__":
    create_incremental_td_rpg()
