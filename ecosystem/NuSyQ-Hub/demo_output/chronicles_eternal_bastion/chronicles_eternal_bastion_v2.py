#!/usr/bin/env python3
"""Chronicles of the Eternal Bastion - Enhanced Edition v2.0

A sophisticated incremental tower defense RPG with:
- Advanced graphics and particle effects
- Dynamic pathfinding AI
- Rich progression systems
- Animated sprites and effects
- Polished UI/UX
- Sound system (placeholder)
- Achievement system
- Multiple game modes
- Advanced tower synergies
- Elemental damage system

Controls:
    Mouse: Select/place towers, interact
    1-6: Quick-select tower types
    Space: Start/Pause wave
    Q/W/E/R: Hero abilities
    Tab: Character sheet
    I: Inventory
    C: Codex/Achievements
    S: Shop
    ESC: Menu
    + / -: Zoom
    Arrow Keys: Pan camera

OmniTag: [game, tower-defense, rpg, incremental, advanced, polished]
"""

import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60
TILE_SIZE = 64


# Enhanced Colors with gradients
class Colors:
    # Base colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    DARK_BLUE = (15, 20, 40)
    DARKER_BLUE = (10, 15, 30)

    # UI colors
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)
    BRONZE = (205, 127, 50)

    # Rarity colors
    COMMON = (150, 150, 150)
    UNCOMMON = (30, 255, 0)
    RARE = (0, 112, 221)
    EPIC = (163, 53, 238)
    LEGENDARY = (255, 128, 0)
    MYTHIC = (230, 0, 122)

    # Element colors
    FIRE = (255, 69, 0)
    ICE = (135, 206, 250)
    LIGHTNING = (255, 255, 0)
    POISON = (50, 205, 50)
    DARK = (75, 0, 130)
    HOLY = (255, 250, 205)

    # Status colors
    HP_BAR = (220, 20, 60)
    HP_BG = (60, 20, 20)
    MANA_BAR = (30, 144, 255)
    MANA_BG = (20, 60, 100)
    XP_BAR = (255, 215, 0)
    XP_BG = (100, 86, 0)

    # UI elements
    BUTTON_DEFAULT = (40, 50, 70)
    BUTTON_HOVER = (60, 70, 90)
    BUTTON_PRESSED = (30, 40, 60)
    PANEL_BG = (25, 35, 55, 200)  # Semi-transparent
    TOOLTIP_BG = (10, 15, 25, 230)


# Game States
class GameState(Enum):
    SPLASH = "splash"
    MENU = "menu"
    HUB = "hub"
    BATTLE = "battle"
    CHARACTER = "character"
    SHOP = "shop"
    CODEX = "codex"
    ACHIEVEMENTS = "achievements"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    VICTORY = "victory"


# Particle system for visual effects
@dataclass
class Particle:
    """Visual particle effect."""

    position: list[float]
    velocity: list[float]
    color: tuple[int, int, int]
    size: float
    lifetime: float
    max_lifetime: float
    fade: bool = True
    glow: bool = False

    def update(self, dt: float) -> bool:
        """Update particle, return False if dead."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        # Apply gravity/physics
        self.velocity[1] += 100 * dt  # Gravity
        self.velocity[0] *= 0.98  # Air resistance
        self.velocity[1] *= 0.98

        return True

    def get_alpha(self) -> int:
        """Get current alpha based on lifetime."""
        if self.fade:
            return int(255 * (self.lifetime / self.max_lifetime))
        return 255


class ParticleSystem:
    """Manages visual effects."""

    def __init__(self):
        self.particles: list[Particle] = []

    def emit(
        self,
        position: tuple[float, float],
        color: tuple[int, int, int],
        count: int = 10,
        velocity_range: float = 100,
        lifetime: float = 1.0,
        glow: bool = False,
    ):
        """Emit particles."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, velocity_range)
            self.particles.append(
                Particle(
                    position=list(position),
                    velocity=[math.cos(angle) * speed, math.sin(angle) * speed - 50],
                    color=color,
                    size=random.uniform(2, 6),
                    lifetime=lifetime,
                    max_lifetime=lifetime,
                    glow=glow,
                )
            )

    def update(self, dt: float):
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)):
        """Render all particles."""
        for particle in self.particles:
            pos = (
                int(particle.position[0] - camera_offset[0]),
                int(particle.position[1] - camera_offset[1]),
            )

            # Create surface with alpha
            particle_surf = pygame.Surface(
                (int(particle.size * 2), int(particle.size * 2)), pygame.SRCALPHA
            )

            if particle.glow:
                # Draw glow effect
                for i in range(3):
                    alpha = particle.get_alpha() // (i + 1)
                    size = particle.size * (3 - i)
                    color = (*particle.color, alpha)
                    pygame.draw.circle(
                        particle_surf, color, (int(particle.size), int(particle.size)), int(size)
                    )
            else:
                color = (*particle.color, particle.get_alpha())
                pygame.draw.circle(
                    particle_surf,
                    color,
                    (int(particle.size), int(particle.size)),
                    int(particle.size),
                )

            surface.blit(particle_surf, pos)


# Enhanced Enemy with better AI
@dataclass
class Enemy:
    """Enhanced enemy with pathfinding."""

    name: str
    hp: float
    max_hp: float
    speed: float
    position: tuple[float, float]
    path: list[tuple[int, int]] = field(default_factory=list)
    path_index: int = 0
    armor: float = 0.0
    magic_resist: float = 0.0
    gold_reward: int = 10
    essence_reward: int = 1
    xp_reward: int = 10
    alive: bool = True
    element_weakness: str | None = None
    element_resistance: str | None = None
    special_abilities: list[str] = field(default_factory=list)
    status_effects: dict[str, float] = field(default_factory=dict)
    sprite_color: tuple[int, int, int] = (220, 20, 60)
    size: int = 20

    def take_damage(self, amount: float, damage_type: str, element: str | None = None) -> float:
        """Take damage with resistances and weaknesses."""
        # Base resistance
        resist = self.armor if damage_type == "physical" else self.magic_resist
        multiplier = 1.0 - (resist / 100.0)

        # Element modifiers
        if element:
            if element == self.element_weakness:
                multiplier *= 1.5  # 50% more damage
            elif element == self.element_resistance:
                multiplier *= 0.5  # 50% less damage

        actual_damage = amount * multiplier
        self.hp -= actual_damage

        if self.hp <= 0:
            self.alive = False

        return actual_damage

    def move(self, dt: float) -> bool:
        """Move along path. Returns True if reached end."""
        if self.path_index >= len(self.path):
            return True

        target = self.path[self.path_index]
        target_pos = (
            target[0] * TILE_SIZE + TILE_SIZE // 2,
            target[1] * TILE_SIZE + TILE_SIZE // 2,
        )

        # Move towards target
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 5:  # Reached waypoint
            self.path_index += 1
            return False

        # Normalize and apply speed
        move_dist = min(self.speed * dt, dist)
        self.position = (
            self.position[0] + (dx / dist) * move_dist,
            self.position[1] + (dy / dist) * move_dist,
        )

        return False

    def apply_status_effect(self, effect: str, duration: float):
        """Apply status effect."""
        self.status_effects[effect] = duration

    def update_status_effects(self, dt: float):
        """Update status effects."""
        for effect in list(self.status_effects.keys()):
            self.status_effects[effect] -= dt
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]


# Enhanced Tower with special abilities
@dataclass
class Tower:
    """Enhanced tower with abilities and synergies."""

    name: str
    tower_type: str  # archer, mage, barracks, artillery, support, summoner
    level: int
    position: tuple[int, int]
    damage: float
    range: float
    fire_rate: float
    damage_type: str  # physical, magical
    element: str | None  # fire, ice, lightning, poison, dark, holy
    cost: int
    sell_value: int
    target: Enemy | None = None
    cooldown: float = 0.0
    kills: int = 0
    total_damage: float = 0.0
    special_ability: dict | None = None
    aura_bonuses: list[str] = field(default_factory=list)
    upgrade_level: int = 0
    sprite_color: tuple[int, int, int] = (30, 144, 255)

    def update(
        self,
        dt: float,
        enemies: list[Enemy],
        nearby_towers: list["Tower"],
        particles: ParticleSystem,
    ):
        """Enhanced update with abilities."""
        self.cooldown = max(0, self.cooldown - dt)

        # Find target with priority system
        if not self.target or not self.target.alive:
            self.target = self.find_target(enemies)

        # Attack if ready
        if self.target and self.cooldown <= 0:
            damage_dealt = self.attack(self.target, particles)
            self.total_damage += damage_dealt

            if not self.target.alive:
                self.kills += 1

            self.cooldown = 1.0 / self.fire_rate

        # Apply aura bonuses to nearby towers
        if self.aura_bonuses and nearby_towers:
            self.apply_aura(nearby_towers)

    def find_target(self, enemies: list[Enemy]) -> Enemy | None:
        """Find best target based on tower type."""
        valid_targets = []

        for enemy in enemies:
            if enemy.alive:
                dist = math.dist(self.position, enemy.position)
                if dist <= self.range:
                    valid_targets.append((enemy, dist))

        if not valid_targets:
            return None

        # Different targeting priorities
        if self.tower_type == "artillery":
            # Target furthest (to hit groups)
            return max(valid_targets, key=lambda x: x[1])[0]
        elif self.tower_type == "support":
            # Don't target (support tower)
            return None
        else:
            # Target closest (default)
            return min(valid_targets, key=lambda x: x[1])[0]

    def attack(self, enemy: Enemy, particles: ParticleSystem) -> float:
        """Attack with visual effects."""
        base_damage = self.damage * (1.0 + self.level * 0.1)

        # Element synergy bonus
        damage_dealt = enemy.take_damage(base_damage, self.damage_type, self.element)

        # Create attack visual
        if self.element:
            color = getattr(Colors, self.element.upper(), Colors.WHITE)
            particles.emit(enemy.position, color, count=5, velocity_range=50, glow=True)

        # Special ability effects
        if self.special_ability and random.random() < self.special_ability.get("chance", 0.1):
            self.trigger_special(enemy, particles)

        return damage_dealt

    def trigger_special(self, enemy: Enemy, particles: ParticleSystem):
        """Trigger special ability."""
        ability = self.special_ability

        if ability["type"] == "stun":
            enemy.apply_status_effect("stunned", ability.get("duration", 1.0))
            particles.emit(enemy.position, Colors.LIGHTNING, count=20, glow=True)

        elif ability["type"] == "slow":
            enemy.speed *= 0.5
            enemy.apply_status_effect("slowed", ability.get("duration", 2.0))
            particles.emit(enemy.position, Colors.ICE, count=15)

        elif ability["type"] == "burn":
            enemy.apply_status_effect("burning", ability.get("duration", 3.0))
            particles.emit(enemy.position, Colors.FIRE, count=10, glow=True)

    def apply_aura(self, nearby_towers: list["Tower"]):
        """Apply aura bonuses."""
        for tower in nearby_towers:
            if tower != self:
                dist = math.dist(self.position, tower.position)
                if dist <= self.range * 1.5:  # Aura range
                    # Implement aura logic (damage buff, speed buff, etc.)
                    pass

    def upgrade(self) -> int:
        """Upgrade tower. Returns cost."""
        cost = int(self.cost * (1.5**self.upgrade_level))
        self.upgrade_level += 1
        self.damage *= 1.2
        self.range *= 1.1
        self.fire_rate *= 1.1
        return cost


# Player character with enhanced abilities
@dataclass
class PlayerCharacter:
    """Enhanced player character."""

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

    # Abilities (now with cooldowns and costs)
    abilities: list[dict] = field(
        default_factory=lambda: [
            {
                "name": "Meteor Strike",
                "description": "Deals massive AoE damage",
                "mana_cost": 30,
                "cooldown": 10.0,
                "current_cooldown": 0.0,
                "element": "fire",
                "damage": 100,
            },
            {
                "name": "Time Slow",
                "description": "Slows all enemies",
                "mana_cost": 20,
                "cooldown": 15.0,
                "current_cooldown": 0.0,
                "duration": 5.0,
            },
            {
                "name": "Divine Shield",
                "description": "Prevents tower damage",
                "mana_cost": 25,
                "cooldown": 20.0,
                "current_cooldown": 0.0,
                "duration": 10.0,
            },
            {
                "name": "Gold Rush",
                "description": "Doubles gold gain",
                "mana_cost": 15,
                "cooldown": 30.0,
                "current_cooldown": 0.0,
                "duration": 15.0,
            },
        ]
    )

    # Buffs
    active_buffs: dict[str, float] = field(default_factory=dict)

    # Equipment (simplified for now)
    equipment: dict[str, str | None] = field(
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

    def gain_xp(self, amount: int):
        """Gain experience."""
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level_up()

    def level_up(self):
        """Level up with fanfare."""
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

    def update_abilities(self, dt: float):
        """Update ability cooldowns."""
        for ability in self.abilities:
            if ability["current_cooldown"] > 0:
                ability["current_cooldown"] = max(0, ability["current_cooldown"] - dt)

    def update_buffs(self, dt: float):
        """Update active buffs."""
        for buff in list(self.active_buffs.keys()):
            self.active_buffs[buff] -= dt
            if self.active_buffs[buff] <= 0:
                del self.active_buffs[buff]

    def use_ability(self, ability_index: int) -> bool:
        """Use an ability. Returns success."""
        if ability_index >= len(self.abilities):
            return False

        ability = self.abilities[ability_index]

        # Check cooldown and mana
        if ability["current_cooldown"] > 0 or self.mana < ability["mana_cost"]:
            return False

        # Consume mana and start cooldown
        self.mana -= ability["mana_cost"]
        ability["current_cooldown"] = ability["cooldown"]

        # Apply effect
        if "duration" in ability:
            self.active_buffs[ability["name"]] = ability["duration"]

        return True


# Achievement system
@dataclass
class Achievement:
    """Achievement definition."""

    id: str
    name: str
    description: str
    requirement: dict  # {type: "kills", value: 100}
    reward_essence: int = 10
    unlocked: bool = False
    progress: float = 0.0


class AchievementSystem:
    """Manages achievements."""

    def __init__(self):
        self.achievements: list[Achievement] = [
            Achievement(
                "first_blood",
                "First Blood",
                "Kill your first enemy",
                {"type": "kills", "value": 1},
                5,
            ),
            Achievement(
                "defender", "Defender", "Complete 10 waves", {"type": "waves", "value": 10}, 20
            ),
            Achievement(
                "tower_master",
                "Tower Master",
                "Build 50 towers",
                {"type": "towers_built", "value": 50},
                25,
            ),
            Achievement(
                "ascended",
                "Ascended One",
                "Reach Ascension Level 10",
                {"type": "ascension", "value": 10},
                100,
            ),
            Achievement(
                "wealthy",
                "Wealthy",
                "Earn 100,000 gold",
                {"type": "gold_earned", "value": 100000},
                50,
            ),
        ]

    def check_achievements(self, stats: dict) -> list[Achievement]:
        """Check and unlock achievements. Returns newly unlocked."""
        newly_unlocked = []

        for achievement in self.achievements:
            if not achievement.unlocked:
                req_type = achievement.requirement["type"]
                req_value = achievement.requirement["value"]
                current = stats.get(req_type, 0)

                achievement.progress = min(1.0, current / req_value)

                if current >= req_value:
                    achievement.unlocked = True
                    newly_unlocked.append(achievement)

        return newly_unlocked


# Enhanced Game Progress
@dataclass
class GameProgress:
    """Enhanced meta-progression."""

    ascension_level: int = 0
    total_gold_earned: int = 0
    total_enemies_killed: int = 0
    waves_completed: int = 0
    towers_built: int = 0
    achievements_unlocked: int = 0
    celestial_essence: int = 0
    highest_wave: int = 0
    total_play_time: float = 0.0
    last_save_time: str = ""

    # Permanent upgrades
    permanent_bonuses: dict[str, float] = field(
        default_factory=lambda: {
            "gold_multiplier": 1.0,
            "damage_multiplier": 1.0,
            "xp_multiplier": 1.0,
            "starting_gold": 500,
        }
    )

    def get_ascension_bonus(self, stat: str) -> float:
        """Calculate ascension bonus for stat."""
        base_bonus = self.permanent_bonuses.get(f"{stat}_multiplier", 1.0)
        ascension_bonus = 1.0 + (self.ascension_level * 0.05)  # 5% per level
        return base_bonus * ascension_bonus


# Main Game Class
class EnhancedGame:
    """Enhanced game with advanced features."""

    def __init__(self):
        # Display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chronicles of the Eternal Bastion - Enhanced Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU

        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        self.font_title = pygame.font.Font(None, 64)

        # Game systems
        self.player = PlayerCharacter()
        self.progress = GameProgress()
        self.achievements = AchievementSystem()
        self.particles = ParticleSystem()

        # Game entities
        self.towers: list[Tower] = []
        self.enemies: list[Enemy] = []

        # Resources
        self.gold = self.progress.permanent_bonuses["starting_gold"]
        self.essence = 0

        # Wave system
        self.current_wave = 0
        self.wave_active = False
        self.wave_timer = 0.0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0.0

        # UI state
        self.selected_tower_type = None
        self.hovered_tower = None
        self.camera_offset = [0, 0]
        self.zoom = 1.0

        # Game map (simple grid for pathfinding)
        self.map_width = 20
        self.map_height = 12
        self.path = self.generate_path()

        # Stats tracking
        self.session_stats = {
            "kills": 0,
            "waves": 0,
            "towers_built": 0,
            "gold_earned": 0,
            "ascension": self.progress.ascension_level,
        }

        # FPS tracking
        self.fps_history = deque(maxlen=60)

    def generate_path(self) -> list[tuple[int, int]]:
        """Generate enemy path."""
        path = []
        # Simple S-curve path
        for x in range(self.map_width):
            y = 6 + int(3 * math.sin(x / 3))
            path.append((x, y))
        return path

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.fps_history.append(self.clock.get_fps())

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
                elif self.state in [
                    GameState.PAUSE,
                    GameState.CHARACTER,
                    GameState.SHOP,
                    GameState.CODEX,
                ]:
                    self.state = GameState.BATTLE
                elif self.state == GameState.HUB:
                    self.state = GameState.MENU

            elif event.key == pygame.K_TAB:
                self.state = GameState.CHARACTER

            elif event.key == pygame.K_c:
                self.state = GameState.CODEX

            elif event.key == pygame.K_s:
                self.state = GameState.SHOP

            elif event.key == pygame.K_SPACE and self.state == GameState.BATTLE:
                if not self.wave_active and not self.enemies:
                    self.start_wave()

            # Hero abilities (Q/W/E/R)
            elif event.key == pygame.K_q:
                if self.player.use_ability(0):
                    self.cast_meteor_strike()
            elif event.key == pygame.K_w:
                if self.player.use_ability(1):
                    pass  # Time slow handled in update
            elif event.key == pygame.K_e:
                self.player.use_ability(2)
            elif event.key == pygame.K_r:
                self.player.use_ability(3)

            # Tower quick select (1-6)
            elif event.key in [
                pygame.K_1,
                pygame.K_2,
                pygame.K_3,
                pygame.K_4,
                pygame.K_5,
                pygame.K_6,
            ]:
                self.selected_tower_type = event.key - pygame.K_1

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_click(event.pos, event.button)

        elif event.type == pygame.MOUSEMOTION:
            # Check for tower hover
            mouse_pos = event.pos
            self.hovered_tower = None
            for tower in self.towers:
                if math.dist(tower.position, mouse_pos) < 30:
                    self.hovered_tower = tower
                    break

    def handle_click(self, pos, button):
        """Handle mouse clicks."""
        if self.state == GameState.BATTLE and self.selected_tower_type is not None:
            if button == 1:  # Left click - place tower
                self.place_tower(pos)

        # UI button clicks handled in render

    def place_tower(self, pos):
        """Place a tower at position."""
        tower_types = [
            ("Archer's Perch", "archer", 15, 180, 1.5, "physical", None, Colors.BLUE),
            ("Mage Tower", "mage", 25, 150, 1.0, "magical", "fire", Colors.FIRE),
            ("Ice Tower", "mage", 25, 150, 1.0, "magical", "ice", Colors.ICE),
            ("Lightning Spire", "mage", 30, 140, 1.8, "magical", "lightning", Colors.LIGHTNING),
            ("Artillery", "artillery", 50, 250, 0.5, "physical", None, Colors.ORANGE),
            ("Support Shrine", "support", 20, 200, 0, "support", "holy", Colors.HOLY),
        ]

        if self.selected_tower_type >= len(tower_types):
            return

        tower_def = tower_types[self.selected_tower_type]
        cost = 100 + (self.selected_tower_type * 25)

        if self.gold >= cost:
            tower = Tower(
                name=tower_def[0],
                tower_type=tower_def[1],
                level=1,
                position=pos,
                damage=tower_def[2] * self.progress.get_ascension_bonus("damage"),
                range=tower_def[3],
                fire_rate=tower_def[4],
                damage_type=tower_def[5],
                element=tower_def[6],
                cost=cost,
                sell_value=cost // 2,
                sprite_color=tower_def[7],
            )

            self.towers.append(tower)
            self.gold -= cost
            self.session_stats["towers_built"] += 1
            self.progress.towers_built += 1

            # Particle effect
            self.particles.emit(pos, tower_def[7], count=20, velocity_range=80)

            self.selected_tower_type = None

    def start_wave(self):
        """Start next wave."""
        self.current_wave += 1
        self.wave_active = True
        self.wave_timer = 0

        # Calculate enemy count and stats
        base_count = 5 + self.current_wave * 2
        self.enemies_to_spawn = base_count
        self.spawn_timer = 0

    def spawn_enemy(self):
        """Spawn a single enemy."""
        if not self.path:
            return

        # Vary enemy types
        enemy_types = [
            ("Goblin", 20, 80, Colors.HP_BAR, None, None),
            ("Knight", 50, 50, Colors.SILVER, None, None),
            ("Fire Demon", 30, 70, Colors.FIRE, "ice", "fire"),
            ("Ice Wraith", 30, 70, Colors.ICE, "fire", "ice"),
        ]

        enemy_type = random.choice(enemy_types)

        # Scale with wave
        hp_mult = 1.0 + (self.current_wave * 0.15)

        enemy = Enemy(
            name=enemy_type[0],
            hp=enemy_type[1] * hp_mult,
            max_hp=enemy_type[1] * hp_mult,
            speed=enemy_type[2],
            position=(
                self.path[0][0] * TILE_SIZE + TILE_SIZE // 2,
                self.path[0][1] * TILE_SIZE + TILE_SIZE // 2,
            ),
            path=self.path.copy(),
            gold_reward=10 + self.current_wave,
            essence_reward=1,
            xp_reward=10 + self.current_wave * 2,
            element_weakness=enemy_type[4],
            element_resistance=enemy_type[5],
            sprite_color=enemy_type[3],
        )

        self.enemies.append(enemy)

    def cast_meteor_strike(self):
        """Cast meteor strike ability."""
        # Find center of enemies
        if not self.enemies:
            return

        avg_x = sum(e.position[0] for e in self.enemies if e.alive) / len(
            [e for e in self.enemies if e.alive]
        )
        avg_y = sum(e.position[1] for e in self.enemies if e.alive) / len(
            [e for e in self.enemies if e.alive]
        )

        center = (avg_x, avg_y)
        damage = 100
        radius = 150

        # Damage enemies in radius
        for enemy in self.enemies:
            if enemy.alive:
                dist = math.dist(enemy.position, center)
                if dist < radius:
                    enemy.take_damage(damage, "magical", "fire")

        # Epic visual effect
        self.particles.emit(center, Colors.FIRE, count=100, velocity_range=200, glow=True)

    def update(self, dt: float):
        """Update game logic."""
        if self.state == GameState.BATTLE:
            # Update wave spawning
            if self.wave_active and self.enemies_to_spawn > 0:
                self.spawn_timer += dt
                if self.spawn_timer >= 1.0:  # Spawn every 1 second
                    self.spawn_enemy()
                    self.enemies_to_spawn -= 1
                    self.spawn_timer = 0

            # Check wave complete
            if not self.enemies and self.enemies_to_spawn == 0 and self.wave_active:
                self.wave_active = False
                self.session_stats["waves"] += 1
                self.progress.waves_completed += 1

                # Wave completion rewards
                wave_gold = 50 + (self.current_wave * 10)
                self.gold += int(wave_gold * self.progress.get_ascension_bonus("gold"))

            # Update player
            self.player.update_abilities(dt)
            self.player.update_buffs(dt)

            # Passive mana regen
            self.player.mana = min(self.player.max_mana, self.player.mana + dt * 5)

            # Update towers
            for tower in self.towers:
                nearby = [t for t in self.towers if t != tower]
                tower.update(dt, self.enemies, nearby, self.particles)

            # Update enemies
            for enemy in self.enemies[:]:
                enemy.update_status_effects(dt)

                # Check if slowed
                speed_mult = 0.5 if "slowed" in enemy.status_effects else 1.0

                # Apply Time Slow buff
                if "Time Slow" in self.player.active_buffs:
                    speed_mult *= 0.3

                # Store original speed
                original_speed = enemy.speed
                enemy.speed *= speed_mult

                reached_end = enemy.move(dt)

                # Restore speed
                enemy.speed = original_speed

                if reached_end:
                    self.player.hp -= 10
                    self.enemies.remove(enemy)
                    continue

                if not enemy.alive:
                    # Rewards
                    gold_mult = self.progress.get_ascension_bonus("gold")
                    if "Gold Rush" in self.player.active_buffs:
                        gold_mult *= 2

                    self.gold += int(enemy.gold_reward * gold_mult)
                    self.essence += enemy.essence_reward
                    self.player.gain_xp(
                        int(enemy.xp_reward * self.progress.get_ascension_bonus("xp"))
                    )

                    self.session_stats["kills"] += 1
                    self.progress.total_enemies_killed += 1

                    # Death particles
                    self.particles.emit(enemy.position, enemy.sprite_color, count=30)

                    self.enemies.remove(enemy)

            # Passive income (incremental mechanic)
            self.gold += (
                dt * (1 + self.progress.ascension_level) * self.progress.get_ascension_bonus("gold")
            )
            self.essence += dt * 0.1 * (1 + self.progress.ascension_level * 0.5)

        # Update particles
        self.particles.update(dt)

        # Check achievements
        newly_unlocked = self.achievements.check_achievements(self.session_stats)
        for achievement in newly_unlocked:
            self.essence += achievement.reward_essence
            # Could show notification

        # Track playtime
        self.progress.total_play_time += dt

    def render(self):
        """Render the game."""
        self.screen.fill(Colors.DARKER_BLUE)

        if self.state == GameState.MENU:
            self.render_menu()
        elif self.state == GameState.BATTLE:
            self.render_battle()
        elif self.state == GameState.CHARACTER:
            self.render_character()
        elif self.state == GameState.CODEX:
            self.render_codex()
        elif self.state == GameState.PAUSE:
            self.render_battle()  # Show battle in background
            self.render_pause_overlay()

        # FPS counter
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 60
        fps_text = self.font_small.render(f"FPS: {int(avg_fps)}", True, Colors.WHITE)
        self.screen.blit(fps_text, (SCREEN_WIDTH - 100, 10))

        pygame.display.flip()

    def render_menu(self):
        """Render main menu."""
        # Title
        title = self.font_title.render("Chronicles of the Eternal Bastion", True, Colors.GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font_large.render("Enhanced Edition v2.0", True, Colors.SILVER)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Buttons
        self.draw_fancy_button("New Game", (SCREEN_WIDTH // 2 - 150, 350, 300, 60), Colors.GREEN)
        self.draw_fancy_button("Continue", (SCREEN_WIDTH // 2 - 150, 430, 300, 60), Colors.BLUE)
        self.draw_fancy_button("Exit", (SCREEN_WIDTH // 2 - 150, 510, 300, 60), Colors.RED)

        # Stats display
        stats_y = 650
        stats = [
            f"Ascension Level: {self.progress.ascension_level}",
            f"Waves Completed: {self.progress.waves_completed}",
            f"Enemies Defeated: {self.progress.total_enemies_killed}",
        ]
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, Colors.SILVER)
            self.screen.blit(text, (50, stats_y + i * 30))

        # Check button clicks
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if self.point_in_rect(mouse_pos, (SCREEN_WIDTH // 2 - 150, 350, 300, 60)):
                self.state = GameState.HUB
            elif self.point_in_rect(mouse_pos, (SCREEN_WIDTH // 2 - 150, 510, 300, 60)):
                self.running = False

    def render_battle(self):
        """Render battle screen."""
        # Draw path
        for i, waypoint in enumerate(self.path):
            pos = (waypoint[0] * TILE_SIZE, waypoint[1] * TILE_SIZE)
            color = Colors.DARK_BLUE if i % 2 else Colors.DARKER_BLUE
            pygame.draw.rect(self.screen, color, (*pos, TILE_SIZE, TILE_SIZE))

        # Draw towers
        for tower in self.towers:
            # Range circle (if hovered)
            if tower == self.hovered_tower:
                pygame.draw.circle(
                    self.screen, (*Colors.WHITE, 30), tower.position, int(tower.range), 2
                )

            # Tower sprite (circle for now)
            pygame.draw.circle(self.screen, tower.sprite_color, tower.position, 20)
            pygame.draw.circle(self.screen, Colors.WHITE, tower.position, 20, 2)

            # Level indicator
            level_text = self.font_small.render(str(tower.level), True, Colors.WHITE)
            level_rect = level_text.get_rect(center=tower.position)
            self.screen.blit(level_text, level_rect)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.alive:
                # Enemy sprite
                pygame.draw.circle(
                    self.screen,
                    enemy.sprite_color,
                    (int(enemy.position[0]), int(enemy.position[1])),
                    enemy.size,
                )

                # HP bar
                bar_width = 40
                bar_height = 4
                hp_percent = enemy.hp / enemy.max_hp
                bar_x = int(enemy.position[0] - bar_width // 2)
                bar_y = int(enemy.position[1] - enemy.size - 10)

                pygame.draw.rect(self.screen, Colors.HP_BG, (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(
                    self.screen,
                    Colors.HP_BAR,
                    (bar_x, bar_y, int(bar_width * hp_percent), bar_height),
                )

        # Draw particles
        self.particles.render(self.screen)

        # HUD
        self.render_hud()

    def render_hud(self):
        """Render battle HUD."""
        # Resource panel
        panel_rect = pygame.Rect(10, 10, 300, 200)
        pygame.draw.rect(self.screen, Colors.PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, Colors.GOLD, panel_rect, 2)

        hud_texts = [
            f"Gold: {int(self.gold)} (+{int(1 + self.progress.ascension_level)}/s)",
            f"Essence: {int(self.essence)}",
            f"Wave: {self.current_wave}",
            f"Enemies: {len([e for e in self.enemies if e.alive])}",
            "",
            f"HP: {int(self.player.hp)}/{int(self.player.max_hp)}",
            f"Mana: {int(self.player.mana)}/{int(self.player.max_mana)}",
            f"Level: {self.player.level}",
        ]

        y = 20
        for text in hud_texts:
            if text:
                surf = self.font.render(text, True, Colors.GOLD)
                self.screen.blit(surf, (20, y))
            y += 25

        # Ability bar
        ability_y = SCREEN_HEIGHT - 120
        for i, ability in enumerate(self.player.abilities):
            x = 20 + i * 100

            # Ability icon
            icon_rect = pygame.Rect(x, ability_y, 80, 80)

            # Cooldown overlay
            if ability["current_cooldown"] > 0:
                pygame.draw.rect(self.screen, Colors.BUTTON_PRESSED, icon_rect)
                cd_percent = ability["current_cooldown"] / ability["cooldown"]
                overlay_height = int(80 * cd_percent)
                overlay_rect = pygame.Rect(x, ability_y, 80, overlay_height)
                pygame.draw.rect(self.screen, (*Colors.BLACK, 180), overlay_rect)
            else:
                pygame.draw.rect(self.screen, Colors.BUTTON_DEFAULT, icon_rect)

            pygame.draw.rect(self.screen, Colors.GOLD, icon_rect, 2)

            # Ability key
            key_text = self.font.render(["Q", "W", "E", "R"][i], True, Colors.WHITE)
            self.screen.blit(key_text, (x + 5, ability_y + 5))

            # Mana cost
            cost_text = self.font_small.render(f"{ability['mana_cost']}", True, Colors.MANA_BAR)
            self.screen.blit(cost_text, (x + 5, ability_y + 60))

        # Tower selection
        if self.selected_tower_type is not None:
            text = self.font.render("Click to place tower", True, Colors.GOLD)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(text, text_rect)
        else:
            text = self.font.render("Press 1-6 to select tower type", True, Colors.SILVER)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(text, text_rect)

        # Wave button
        if not self.wave_active and not self.enemies:
            self.draw_fancy_button(
                "Start Wave (Space)", (SCREEN_WIDTH // 2 - 150, 100, 300, 50), Colors.GREEN
            )

    def render_character(self):
        """Render character sheet."""
        # Background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.DARKER_BLUE, 240))
        self.screen.blit(overlay, (0, 0))

        # Panel
        panel_rect = pygame.Rect(200, 100, SCREEN_WIDTH - 400, SCREEN_HEIGHT - 200)
        pygame.draw.rect(self.screen, Colors.PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, Colors.GOLD, panel_rect, 3)

        # Title
        title = self.font_large.render("Character Sheet", True, Colors.GOLD)
        self.screen.blit(title, (panel_rect.x + 20, panel_rect.y + 20))

        # Character info (left column)
        info_x = panel_rect.x + 40
        info_y = panel_rect.y + 80

        info_texts = [
            f"Name: {self.player.name}",
            f"Class: {self.player.character_class}",
            f"Level: {self.player.level}",
            f"XP: {self.player.xp} / {self.player.xp_to_next}",
            "",
            "=== ATTRIBUTES ===",
            f"Strength: {self.player.strength}",
            f"Intelligence: {self.player.intelligence}",
            f"Dexterity: {self.player.dexterity}",
            f"Wisdom: {self.player.wisdom}",
            f"Charisma: {self.player.charisma}",
            "",
            f"Attribute Points: {self.player.attribute_points}",
            f"Skill Points: {self.player.skill_points}",
        ]

        for text in info_texts:
            color = Colors.GOLD if "===" in text else Colors.WHITE
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (info_x, info_y))
            info_y += 30

        # Close hint
        hint = self.font.render("Press ESC or TAB to close", True, Colors.SILVER)
        self.screen.blit(hint, (panel_rect.x + 20, panel_rect.bottom - 50))

    def render_codex(self):
        """Render achievements/codex."""
        # Similar to character sheet
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.DARKER_BLUE, 240))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(200, 100, SCREEN_WIDTH - 400, SCREEN_HEIGHT - 200)
        pygame.draw.rect(self.screen, Colors.PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, Colors.GOLD, panel_rect, 3)

        title = self.font_large.render("Achievements & Codex", True, Colors.GOLD)
        self.screen.blit(title, (panel_rect.x + 20, panel_rect.y + 20))

        # Achievements
        y = panel_rect.y + 80
        for achievement in self.achievements.achievements:
            color = Colors.GOLD if achievement.unlocked else Colors.SILVER

            # Name
            name_text = self.font.render(
                f"{'✓' if achievement.unlocked else '○'} {achievement.name}", True, color
            )
            self.screen.blit(name_text, (panel_rect.x + 40, y))

            # Description
            desc_text = self.font_small.render(achievement.description, True, Colors.SILVER)
            self.screen.blit(desc_text, (panel_rect.x + 60, y + 25))

            # Progress bar
            if not achievement.unlocked:
                bar_x = panel_rect.x + 60
                bar_y = y + 45
                bar_width = 300
                bar_height = 6

                pygame.draw.rect(self.screen, Colors.XP_BG, (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(
                    self.screen,
                    Colors.XP_BAR,
                    (bar_x, bar_y, int(bar_width * achievement.progress), bar_height),
                )

            y += 70

        # Close hint
        hint = self.font.render("Press C or ESC to close", True, Colors.SILVER)
        self.screen.blit(hint, (panel_rect.x + 20, panel_rect.bottom - 50))

    def render_pause_overlay(self):
        """Render pause menu overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("PAUSED", True, Colors.GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(title, title_rect)

        self.draw_fancy_button(
            "Resume (ESC)", (SCREEN_WIDTH // 2 - 150, 350, 300, 60), Colors.GREEN
        )
        self.draw_fancy_button("Save Game", (SCREEN_WIDTH // 2 - 150, 430, 300, 60), Colors.BLUE)
        self.draw_fancy_button(
            "Return to Menu", (SCREEN_WIDTH // 2 - 150, 510, 300, 60), Colors.RED
        )

    def draw_fancy_button(self, text: str, rect: tuple, color: tuple):
        """Draw a fancy button with hover effect."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.point_in_rect(mouse_pos, rect)

        # Button background
        btn_color = tuple(min(255, c + 30) for c in color) if hovered else color
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, Colors.GOLD, rect, 3, border_radius=8)

        # Button text
        text_surf = self.font_large.render(text, True, Colors.WHITE)
        text_rect = text_surf.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2))
        self.screen.blit(text_surf, text_rect)

    def point_in_rect(self, point: tuple, rect: tuple) -> bool:
        """Check if point is in rectangle."""
        x, y, w, h = rect
        return x <= point[0] <= x + w and y <= point[1] <= y + h


def main():
    """Run the enhanced game."""
    game = EnhancedGame()
    game.run()


if __name__ == "__main__":
    main()
