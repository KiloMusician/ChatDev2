#!/usr/bin/env python3
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

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

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
class Item:
    """Game item (weapon, armor, accessory)."""

    name: str
    item_type: str
    stats: dict[str, float] = field(default_factory=dict)
    level: int = 1
    rarity: str = "common"


@dataclass
class Tower:
    """Tower defense structure."""

    name: str
    level: int = 1
    position: tuple[int, int] = (0, 0)
    damage: float = 10.0
    range: float = 150.0
    fire_rate: float = 1.0  # attacks per second
    damage_type: str = "physical"
    cost: int = 100
    sell_value: int = 50
    target: Optional["Enemy"] = None
    cooldown: float = 0.0
    upgrades: dict = field(default_factory=dict)

    def update(self, dt: float, enemies: list["Enemy"]):
        """Update tower logic."""
        self.cooldown = max(0, self.cooldown - dt)

        # Find target
        if not self.target or not self.target.alive:
            self.target = self.find_target(enemies)

        # Attack if ready
        if self.target and self.cooldown <= 0:
            self.attack(self.target)
            self.cooldown = 1.0 / self.fire_rate

    def find_target(self, enemies: list["Enemy"]) -> Optional["Enemy"]:
        """Find closest enemy in range."""
        for enemy in enemies:
            if enemy.alive:
                dist = math.dist(self.position, enemy.position)
                if dist <= self.range:
                    return enemy
        return None

    def attack(self, enemy: "Enemy"):
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
    position: tuple[float, float] = (0.0, 0.0)
    path_progress: float = 0.0
    gold_reward: int = 10
    essence_reward: int = 1
    alive: bool = True
    special_abilities: list[str] = field(default_factory=list)

    def take_damage(self, amount: float, damage_type: str):
        """Reduce HP by damage amount."""
        resist = self.armor if damage_type == "physical" else self.magic_resist
        actual_damage = amount * (1.0 - resist / 100.0)
        self.hp -= actual_damage

        if self.hp <= 0:
            self.alive = False

    def move(self, dt: float, path: list[tuple[int, int]]):
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
    equipment: dict[str, Optional["Item"]] = field(
        default_factory=lambda: {
            "weapon": None,
            "helm": None,
            "chest": None,
            "gloves": None,
            "boots": None,
            "amulet": None,
            "ring1": None,
            "ring2": None,
        }
    )

    # Abilities
    abilities: list[dict] = field(default_factory=list)

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
    dialogue_tree: dict = field(default_factory=dict)
    relationship_level: int = 0
    quests_available: list[dict] = field(default_factory=list)
    shop_inventory: list["Item"] = field(default_factory=list)

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
    achievements: list[str] = field(default_factory=list)
    unlocked_towers: list[str] = field(default_factory=list)
    unlocked_classes: list[str] = field(default_factory=list)
    celestial_essence: int = 0

    # Offline progress
    last_save_time: str = ""

    def calculate_offline_progress(self) -> dict:
        """Calculate what was earned while away."""
        if not self.last_save_time:
            return {}

        # Parse time difference
        # Calculate resources based on ascension bonuses
        # (simplified for demo)
        return {"gold": 100, "essence": 10, "time_away": "5 minutes"}


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
        self.towers: list[Tower] = []
        self.enemies: list[Enemy] = []
        self.npcs: list[NPC] = self.load_npcs()

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

    def load_npcs(self) -> list[NPC]:
        """Load NPC data from file."""
        try:
            data_path = Path("data/npcs.json")
            if data_path.exists():
                with open(data_path) as f:
                    _npc_data = json.load(f)
                # Create NPC objects (simplified - npc_data loaded but not yet implemented)
                return []
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Default NPCs
        return [
            NPC(
                name="Commander Aldric",
                role="Quest Giver",
                dialogue_tree={
                    "cold": "We must defend the Bastion. Stay alert.",
                    "friendly": "Your progress is impressive, Commander.",
                    "close": "Together, we shall uncover the truth of this endless night.",
                },
            ),
            NPC(
                name="Sage Elara",
                role="Knowledge Keeper",
                dialogue_tree={
                    "cold": "Knowledge is power. Seek it.",
                    "friendly": "I have much to teach you about our world.",
                    "close": "The answers you seek lie in the forgotten ages...",
                },
            ),
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
            name="Archer's Perch", position=pos, damage=15.0, range=150.0, fire_rate=1.5, cost=100
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
                essence_reward=1,
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
                        enemy.position = (enemy.position[0] + enemy.speed * dt, enemy.position[1])

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
            f"Waves Completed: {self.progress.waves_completed}",
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
        self.draw_button(
            "Enter Battle", (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50), RED
        )

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
                pygame.draw.circle(
                    self.screen, color, (int(enemy.position[0]), int(enemy.position[1])), 10
                )

        # HUD
        hud_texts = [
            f"Gold: {int(self.gold)} (+{1 + self.progress.ascension_level}/s)",
            f"Essence: {int(self.essence)}",
            f"Wave: {self.current_wave}",
            f"HP: {int(self.player.hp)}/{int(self.player.max_hp)}",
            f"Level: {self.player.level} (XP: {self.player.xp}/{self.player.xp_to_next})",
            f"Enemies: {len([e for e in self.enemies if e.alive])}",
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
            "ESC: Pause Menu",
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
            "resources": {"gold": self.gold, "essence": self.essence, "knowledge": self.knowledge},
            "timestamp": datetime.now().isoformat(),
        }

        save_path = Path("saves/save_game.json")
        save_path.parent.mkdir(exist_ok=True)

        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)

    def load_game(self):
        """Load saved progress."""
        save_path = Path("saves/save_game.json")
        if not save_path.exists():
            return

        with open(save_path) as f:
            _save_data = json.load(f)

        # Restore state
        # (simplified for demo - save_data loaded but restoration not yet implemented)
        self.state = GameState.HUB


def main():
    """Run the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
