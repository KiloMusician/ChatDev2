#!/usr/bin/env python3
"""
🛡️ Defense Module - Tower Defense mechanics
Mindustry/Factorio-style defense against swarms
"""

import json
import os
import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from math import sqrt

class TowerType(Enum):
    BASIC_TURRET = "basic_turret"
    LASER_CANNON = "laser_cannon"
    MISSILE_LAUNCHER = "missile_launcher"
    SHIELD_GENERATOR = "shield_generator"
    REPAIR_STATION = "repair_station"

class EnemyType(Enum):
    SCOUT = "scout"
    FIGHTER = "fighter"
    HEAVY = "heavy"
    SWARM = "swarm"
    BOSS = "boss"

@dataclass
class Tower:
    tower_type: TowerType
    x: int
    y: int
    health: int = 100
    range: int = 5
    damage: int = 20
    fire_rate: float = 1.0  # attacks per second
    last_fire_time: float = 0.0
    target_id: Optional[str] = None
    energy_cost: int = 5  # per shot
    
@dataclass
class Enemy:
    enemy_type: EnemyType
    id: str
    x: float
    y: float
    health: int = 50
    max_health: int = 50
    speed: float = 1.0
    path_index: int = 0
    loot: Dict[str, int] = None
    
    def __post_init__(self):
        if self.loot is None:
            self.loot = {"materials": 5, "energy": 2}

@dataclass
class Wave:
    wave_number: int
    enemies: List[Dict]  # Enemy spawn definitions
    spawn_delay: float = 2.0
    status: str = "pending"  # pending, active, completed

@dataclass
class DefenseState:
    towers: List[Tower]
    enemies: List[Enemy]
    waves: List[Wave]
    current_wave: int = 0
    resources: Dict[str, int] = None
    core_health: int = 100
    wave_timer: float = 0.0
    last_spawn_time: float = 0.0
    
    def __post_init__(self):
        if self.resources is None:
            self.resources = {
                "materials": 200,
                "energy": 150,
                "research": 0
            }

class DefenseEngine:
    def __init__(self, state_file=".local/defense_state.json"):
        self.state_file = state_file
        self.map_width = 25
        self.map_height = 20
        
        # Define path that enemies follow to the core
        self.enemy_path = [
            (0, 10), (5, 10), (5, 5), (10, 5), (10, 15), 
            (15, 15), (15, 8), (20, 8), (20, 12), (24, 12)
        ]
        
        self.state = self.load_state()
        
        # Tower costs and stats
        self.tower_definitions = {
            TowerType.BASIC_TURRET: {
                "cost": {"materials": 25, "energy": 10},
                "health": 80,
                "range": 4,
                "damage": 15,
                "fire_rate": 1.2,
                "energy_cost": 3
            },
            TowerType.LASER_CANNON: {
                "cost": {"materials": 50, "energy": 30},
                "health": 60,
                "range": 6,
                "damage": 35,
                "fire_rate": 0.8,
                "energy_cost": 8
            },
            TowerType.MISSILE_LAUNCHER: {
                "cost": {"materials": 80, "energy": 45},
                "health": 100,
                "range": 8,
                "damage": 60,
                "fire_rate": 0.5,
                "energy_cost": 15
            },
            TowerType.SHIELD_GENERATOR: {
                "cost": {"materials": 60, "energy": 40},
                "health": 120,
                "range": 3,
                "damage": 0,
                "fire_rate": 0.0,
                "energy_cost": 5
            },
            TowerType.REPAIR_STATION: {
                "cost": {"materials": 40, "energy": 25},
                "health": 100,
                "range": 3,
                "damage": 0,
                "fire_rate": 2.0,
                "energy_cost": 4
            }
        }
        
        # Enemy definitions
        self.enemy_definitions = {
            EnemyType.SCOUT: {
                "health": 30,
                "speed": 2.0,
                "loot": {"materials": 3, "energy": 1}
            },
            EnemyType.FIGHTER: {
                "health": 60,
                "speed": 1.5,
                "loot": {"materials": 8, "energy": 3}
            },
            EnemyType.HEAVY: {
                "health": 120,
                "speed": 0.8,
                "loot": {"materials": 15, "energy": 8}
            },
            EnemyType.SWARM: {
                "health": 20,
                "speed": 2.5,
                "loot": {"materials": 2, "energy": 1}
            },
            EnemyType.BOSS: {
                "health": 300,
                "speed": 1.0,
                "loot": {"materials": 50, "energy": 25, "research": 10}
            }
        }
    
    def load_state(self) -> DefenseState:
        """Load defense state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return DefenseState(
                        towers=[Tower(**t) for t in data.get('towers', [])],
                        enemies=[Enemy(**e) for e in data.get('enemies', [])],
                        waves=[Wave(**w) for w in data.get('waves', [])],
                        current_wave=data.get('current_wave', 0),
                        resources=data.get('resources', {}),
                        core_health=data.get('core_health', 100),
                        wave_timer=data.get('wave_timer', 0.0),
                        last_spawn_time=data.get('last_spawn_time', 0.0)
                    )
            except Exception as e:
                print(f"⚠️  Error loading defense state: {e}")
        
        return self.create_initial_state()
    
    def create_initial_state(self) -> DefenseState:
        """Create initial defense setup"""
        # Generate initial waves
        waves = []
        for wave_num in range(1, 11):  # 10 waves
            wave_enemies = []
            
            # Scale difficulty with wave number
            enemy_count = 3 + wave_num * 2
            
            for i in range(enemy_count):
                if wave_num <= 3:
                    enemy_type = random.choice([EnemyType.SCOUT, EnemyType.FIGHTER])
                elif wave_num <= 6:
                    enemy_type = random.choice([EnemyType.SCOUT, EnemyType.FIGHTER, EnemyType.HEAVY])
                elif wave_num <= 8:
                    enemy_type = random.choice([EnemyType.FIGHTER, EnemyType.HEAVY, EnemyType.SWARM])
                else:
                    enemy_type = random.choice([EnemyType.HEAVY, EnemyType.SWARM, EnemyType.BOSS])
                
                wave_enemies.append({
                    "type": enemy_type.value,
                    "spawn_delay": i * 1.5  # Delay between spawns
                })
            
            waves.append(Wave(
                wave_number=wave_num,
                enemies=wave_enemies,
                spawn_delay=2.0 if wave_num <= 5 else 1.0
            ))
        
        return DefenseState(
            towers=[],
            enemies=[],
            waves=waves,
            resources={"materials": 200, "energy": 150, "research": 0}
        )
    
    def save_state(self):
        """Save defense state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            'towers': [asdict(t) for t in self.state.towers],
            'enemies': [asdict(e) for e in self.state.enemies],
            'waves': [asdict(w) for w in self.state.waves],
            'current_wave': self.state.current_wave,
            'resources': self.state.resources,
            'core_health': self.state.core_health,
            'wave_timer': self.state.wave_timer,
            'last_spawn_time': self.state.last_spawn_time
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def build_tower(self, tower_type: TowerType, x: int, y: int) -> bool:
        """Build a tower at the specified position"""
        if not (0 <= x < self.map_width and 0 <= y < self.map_height):
            print("❌ Invalid position")
            return False
        
        # Check if position is occupied
        for tower in self.state.towers:
            if tower.x == x and tower.y == y:
                print("❌ Position occupied")
                return False
        
        # Check if position is on the path
        if (x, y) in self.enemy_path:
            print("❌ Cannot build on enemy path")
            return False
        
        # Check resources
        tower_def = self.tower_definitions[tower_type]
        cost = tower_def["cost"]
        
        for resource, amount in cost.items():
            if self.state.resources.get(resource, 0) < amount:
                print(f"❌ Insufficient {resource}: need {amount}, have {self.state.resources.get(resource, 0)}")
                return False
        
        # Deduct resources
        for resource, amount in cost.items():
            self.state.resources[resource] -= amount
        
        # Create tower
        tower = Tower(
            tower_type=tower_type,
            x=x,
            y=y,
            health=tower_def["health"],
            range=tower_def["range"],
            damage=tower_def["damage"],
            fire_rate=tower_def["fire_rate"],
            energy_cost=tower_def["energy_cost"]
        )
        
        self.state.towers.append(tower)
        print(f"🏗️  Built {tower_type.value} at ({x}, {y})")
        return True
    
    def start_wave(self) -> bool:
        """Start the next wave"""
        if self.state.current_wave >= len(self.state.waves):
            print("🎉 All waves completed! Victory!")
            return False
        
        current_wave = self.state.waves[self.state.current_wave]
        if current_wave.status != "pending":
            print("⚠️  Wave already in progress")
            return False
        
        current_wave.status = "active"
        self.state.wave_timer = 0.0
        self.state.last_spawn_time = 0.0
        
        print(f"🌊 Wave {current_wave.wave_number} starting!")
        print(f"   Enemies: {len(current_wave.enemies)}")
        return True
    
    def spawn_enemy(self, enemy_type: EnemyType) -> Enemy:
        """Spawn a new enemy"""
        enemy_def = self.enemy_definitions[enemy_type]
        
        enemy = Enemy(
            enemy_type=enemy_type,
            id=f"enemy_{len(self.state.enemies)}_{time.time()}",
            x=float(self.enemy_path[0][0]),
            y=float(self.enemy_path[0][1]),
            health=enemy_def["health"],
            max_health=enemy_def["health"],
            speed=enemy_def["speed"],
            loot=enemy_def["loot"].copy()
        )
        
        self.state.enemies.append(enemy)
        return enemy
    
    def update_wave_spawning(self, delta_time: float):
        """Handle enemy spawning for current wave"""
        if self.state.current_wave >= len(self.state.waves):
            return
        
        current_wave = self.state.waves[self.state.current_wave]
        if current_wave.status != "active":
            return
        
        self.state.wave_timer += delta_time
        
        # Check if it's time to spawn next enemy
        enemies_to_spawn = []
        for enemy_data in current_wave.enemies:
            spawn_time = enemy_data.get("spawn_delay", 0)
            if (self.state.wave_timer >= spawn_time and 
                spawn_time > self.state.last_spawn_time):
                enemies_to_spawn.append(enemy_data)
        
        # Spawn enemies
        for enemy_data in enemies_to_spawn:
            enemy_type = EnemyType(enemy_data["type"])
            self.spawn_enemy(enemy_type)
            self.state.last_spawn_time = enemy_data["spawn_delay"]
        
        # Check if wave is complete
        if (self.state.wave_timer > max([e.get("spawn_delay", 0) for e in current_wave.enemies]) + 5.0 and
            len(self.state.enemies) == 0):
            current_wave.status = "completed"
            self.state.current_wave += 1
            print(f"✅ Wave {current_wave.wave_number} completed!")
            
            # Bonus resources for wave completion
            self.state.resources["materials"] += 50
            self.state.resources["energy"] += 30
    
    def update_enemies(self, delta_time: float):
        """Update enemy movement and check for core damage"""
        enemies_to_remove = []
        
        for enemy in self.state.enemies:
            # Move along path
            if enemy.path_index < len(self.enemy_path) - 1:
                current_pos = self.enemy_path[enemy.path_index]
                next_pos = self.enemy_path[enemy.path_index + 1]
                
                # Calculate direction
                dx = next_pos[0] - current_pos[0]
                dy = next_pos[1] - current_pos[1]
                distance = sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    move_distance = enemy.speed * delta_time
                    enemy.x += (dx / distance) * move_distance
                    enemy.y += (dy / distance) * move_distance
                    
                    # Check if reached next waypoint
                    if (abs(enemy.x - next_pos[0]) < 0.5 and 
                        abs(enemy.y - next_pos[1]) < 0.5):
                        enemy.path_index += 1
            else:
                # Reached the core
                damage = 10
                if enemy.enemy_type == EnemyType.HEAVY:
                    damage = 20
                elif enemy.enemy_type == EnemyType.BOSS:
                    damage = 50
                
                self.state.core_health -= damage
                print(f"💥 Core hit by {enemy.enemy_type.value}! Core health: {self.state.core_health}")
                enemies_to_remove.append(enemy)
        
        # Remove enemies that reached core
        for enemy in enemies_to_remove:
            self.state.enemies.remove(enemy)
    
    def update_towers(self, delta_time: float):
        """Update tower targeting and firing"""
        current_time = time.time()
        
        for tower in self.state.towers:
            # Find target if none or current target is invalid
            if not tower.target_id or not any(e.id == tower.target_id for e in self.state.enemies):
                tower.target_id = self.find_best_target(tower)
            
            # Fire at target if possible
            if tower.target_id and current_time - tower.last_fire_time >= (1.0 / tower.fire_rate):
                target = next((e for e in self.state.enemies if e.id == tower.target_id), None)
                if target and self.in_range(tower, target):
                    self.fire_at_target(tower, target)
                    tower.last_fire_time = current_time
    
    def find_best_target(self, tower: Tower) -> Optional[str]:
        """Find the best target for a tower"""
        valid_targets = []
        
        for enemy in self.state.enemies:
            if self.in_range(tower, enemy):
                # Priority: closest to core (highest path_index)
                valid_targets.append((enemy, enemy.path_index))
        
        if valid_targets:
            # Sort by path progress (descending) - target enemies closest to core
            valid_targets.sort(key=lambda x: x[1], reverse=True)
            return valid_targets[0][0].id
        
        return None
    
    def in_range(self, tower: Tower, enemy: Enemy) -> bool:
        """Check if enemy is in tower range"""
        distance = sqrt((tower.x - enemy.x)**2 + (tower.y - enemy.y)**2)
        return distance <= tower.range
    
    def fire_at_target(self, tower: Tower, target: Enemy):
        """Tower fires at target"""
        # Check energy cost
        if self.state.resources.get("energy", 0) < tower.energy_cost:
            return
        
        self.state.resources["energy"] -= tower.energy_cost
        
        # Apply damage
        damage = tower.damage
        if tower.tower_type == TowerType.LASER_CANNON:
            damage += random.randint(0, 10)  # Variable damage
        elif tower.tower_type == TowerType.MISSILE_LAUNCHER:
            # Area damage - affect nearby enemies
            for enemy in self.state.enemies:
                distance = sqrt((target.x - enemy.x)**2 + (target.y - enemy.y)**2)
                if distance <= 2.0:  # Splash radius
                    enemy.health -= damage // 2
        
        target.health -= damage
        
        # Check if enemy died
        if target.health <= 0:
            print(f"💀 {target.enemy_type.value} destroyed!")
            
            # Give loot
            for resource, amount in target.loot.items():
                self.state.resources[resource] = self.state.resources.get(resource, 0) + amount
            
            self.state.enemies.remove(target)
            tower.target_id = None
    
    def render_defense_view(self) -> str:
        """Render ASCII view of defense map"""
        # Create empty map
        defense_map = [["." for _ in range(self.map_width)] for _ in range(self.map_height)]
        
        # Draw path
        for x, y in self.enemy_path:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                defense_map[y][x] = "─"
        
        # Draw towers
        tower_symbols = {
            TowerType.BASIC_TURRET: "T",
            TowerType.LASER_CANNON: "L",
            TowerType.MISSILE_LAUNCHER: "M",
            TowerType.SHIELD_GENERATOR: "S",
            TowerType.REPAIR_STATION: "R"
        }
        
        for tower in self.state.towers:
            if 0 <= tower.x < self.map_width and 0 <= tower.y < self.map_height:
                symbol = tower_symbols.get(tower.tower_type, "?")
                defense_map[tower.y][tower.x] = symbol
        
        # Draw enemies
        enemy_symbols = {
            EnemyType.SCOUT: "s",
            EnemyType.FIGHTER: "f",
            EnemyType.HEAVY: "H",
            EnemyType.SWARM: "*",
            EnemyType.BOSS: "B"
        }
        
        for enemy in self.state.enemies:
            x, y = int(enemy.x), int(enemy.y)
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                symbol = enemy_symbols.get(enemy.enemy_type, "?")
                defense_map[y][x] = symbol
        
        # Draw core
        core_x, core_y = self.enemy_path[-1]
        if 0 <= core_x < self.map_width and 0 <= core_y < self.map_height:
            defense_map[core_y][core_x] = "■"
        
        return "\n".join("".join(row) for row in defense_map)
    
    def get_defense_status(self) -> str:
        """Get defense game status"""
        current_wave_info = "Complete" if self.state.current_wave >= len(self.state.waves) else f"{self.state.current_wave + 1}/{len(self.state.waves)}"
        
        return f"""
🛡️  DEFENSE STATUS
==================
Core Health: {self.state.core_health}/100
Current Wave: {current_wave_info}
Active Enemies: {len(self.state.enemies)}
Towers: {len(self.state.towers)}

📦 Resources:
{chr(10).join(f"  {resource}: {amount}" for resource, amount in self.state.resources.items())}

🏗️  Tower Costs:
  Basic Turret: 25 materials, 10 energy
  Laser Cannon: 50 materials, 30 energy  
  Missile Launcher: 80 materials, 45 energy
  Shield Generator: 60 materials, 40 energy
  Repair Station: 40 materials, 25 energy
        """.strip()
    
    def tick(self, delta_time: float = 1.0):
        """Main defense simulation tick"""
        self.update_wave_spawning(delta_time)
        self.update_enemies(delta_time)
        self.update_towers(delta_time)
        self.save_state()

def main():
    """Interactive defense game"""
    engine = DefenseEngine()
    
    print("🛡️  NuSyQ Defense Engine")
    print("Commands: status, view, build <type> <x> <y>, wave, tick, auto, quit")
    print("Tower types: basic_turret, laser_cannon, missile_launcher, shield_generator, repair_station")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "status":
                print(engine.get_defense_status())
            elif command == "view":
                print("\n" + engine.render_defense_view())
            elif command == "wave":
                engine.start_wave()
            elif command == "tick":
                engine.tick(1.0)
                print("⏰ Defense simulation advanced")
            elif command == "auto":
                for _ in range(30):  # Run 30 ticks
                    engine.tick(0.5)
                print("⏰ Defense simulation advanced 30 ticks")
            elif command.startswith("build "):
                parts = command.split(" ")
                if len(parts) >= 4:
                    tower_type_name = parts[1]
                    try:
                        x, y = int(parts[2]), int(parts[3])
                        tower_type = TowerType(tower_type_name)
                        engine.build_tower(tower_type, x, y)
                    except (ValueError, KeyError):
                        print("Invalid tower type or coordinates")
                        print("Available types:", [t.value for t in TowerType])
                else:
                    print("Usage: build <tower_type> <x> <y>")
            else:
                print("Unknown command. Try: status, view, build <type> <x> <y>, wave, tick, auto, quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()