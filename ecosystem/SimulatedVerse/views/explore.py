#!/usr/bin/env python3
"""
🗺️ Exploration Module - Roguelike/Noita-style exploration
ASCII-based exploration engine with procedural generation
"""

import random
import json
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class TerrainType(Enum):
    EMPTY = "."
    WALL = "#"
    DOOR = "+"
    STAIRS_UP = "<"
    STAIRS_DOWN = ">"
    WATER = "~"
    CRYSTAL = "*"
    ARTIFACT = "?"
    ANOMALY = "!"

@dataclass
class MapCell:
    terrain: TerrainType
    visible: bool = False
    explored: bool = False
    items: List[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []

@dataclass
class Player:
    x: int
    y: int
    level: int = 1
    hp: int = 100
    energy: int = 100
    inventory: List[str] = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

class ExplorationEngine:
    def __init__(self, state_file=".local/exploration_state.json"):
        self.state_file = state_file
        self.width = 80
        self.height = 25
        self.view_radius = 8
        
        # Load or generate initial state
        self.player = Player(x=self.width//2, y=self.height//2)
        self.current_map = self.generate_map()
        self.discovered_locations = set()
        
        self.load_state()
    
    def generate_map(self, seed: int = None) -> Dict[Tuple[int, int], MapCell]:
        """Generate a procedural map using cellular automata"""
        if seed:
            random.seed(seed)
        
        game_map = {}
        
        # Initialize with random noise
        for x in range(self.width):
            for y in range(self.height):
                if random.random() < 0.45:  # 45% chance of wall
                    terrain = TerrainType.WALL
                else:
                    terrain = TerrainType.EMPTY
                game_map[(x, y)] = MapCell(terrain=terrain)
        
        # Apply cellular automata rules for cave-like structure
        for iteration in range(3):
            new_map = {}
            for x in range(self.width):
                for y in range(self.height):
                    wall_count = self.count_walls_around(game_map, x, y)
                    
                    if wall_count >= 4:
                        new_map[(x, y)] = MapCell(terrain=TerrainType.WALL)
                    elif wall_count <= 2:
                        new_map[(x, y)] = MapCell(terrain=TerrainType.EMPTY)
                    else:
                        new_map[(x, y)] = game_map[(x, y)]
            
            game_map = new_map
        
        # Ensure player starting position is empty
        start_x, start_y = self.width//2, self.height//2
        game_map[(start_x, start_y)] = MapCell(terrain=TerrainType.EMPTY)
        
        # Add interesting features
        self.add_features(game_map)
        
        return game_map
    
    def count_walls_around(self, game_map: Dict[Tuple[int, int], MapCell], x: int, y: int) -> int:
        """Count walls in the 3x3 area around a position"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if (nx < 0 or nx >= self.width or 
                    ny < 0 or ny >= self.height or
                    game_map.get((nx, ny), MapCell(TerrainType.WALL)).terrain == TerrainType.WALL):
                    count += 1
        return count
    
    def add_features(self, game_map: Dict[Tuple[int, int], MapCell]):
        """Add interesting features to the map"""
        empty_cells = [(x, y) for (x, y), cell in game_map.items() 
                       if cell.terrain == TerrainType.EMPTY]
        
        if not empty_cells:
            return
        
        # Add water areas
        for _ in range(random.randint(2, 5)):
            if empty_cells:
                x, y = random.choice(empty_cells)
                game_map[(x, y)] = MapCell(terrain=TerrainType.WATER)
                empty_cells.remove((x, y))
        
        # Add crystals
        for _ in range(random.randint(3, 8)):
            if empty_cells:
                x, y = random.choice(empty_cells)
                game_map[(x, y)] = MapCell(terrain=TerrainType.CRYSTAL)
                empty_cells.remove((x, y))
        
        # Add artifacts
        for _ in range(random.randint(1, 3)):
            if empty_cells:
                x, y = random.choice(empty_cells)
                game_map[(x, y)] = MapCell(terrain=TerrainType.ARTIFACT)
                empty_cells.remove((x, y))
        
        # Add anomalies (rare)
        if random.random() < 0.3 and empty_cells:
            x, y = random.choice(empty_cells)
            game_map[(x, y)] = MapCell(terrain=TerrainType.ANOMALY)
    
    def update_visibility(self):
        """Update what the player can see using simple line-of-sight"""
        # Clear previous visibility
        for cell in self.current_map.values():
            cell.visible = False
        
        px, py = self.player.x, self.player.y
        
        # Mark cells within view radius as visible if no walls block line of sight
        for x in range(max(0, px - self.view_radius), min(self.width, px + self.view_radius + 1)):
            for y in range(max(0, py - self.view_radius), min(self.height, py + self.view_radius + 1)):
                distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if distance <= self.view_radius:
                    if self.has_line_of_sight(px, py, x, y):
                        cell = self.current_map.get((x, y))
                        if cell:
                            cell.visible = True
                            cell.explored = True
    
    def has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Simple line-of-sight check using Bresenham's line algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            if x == x2 and y == y2:
                return True
            
            # Check if current cell blocks sight
            cell = self.current_map.get((x, y))
            if cell and cell.terrain == TerrainType.WALL:
                return False
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def move_player(self, dx: int, dy: int) -> bool:
        """Move player and return True if successful"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check bounds
        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return False
        
        # Check if cell is passable
        cell = self.current_map.get((new_x, new_y))
        if not cell or cell.terrain == TerrainType.WALL:
            return False
        
        # Move player
        self.player.x = new_x
        self.player.y = new_y
        
        # Handle special terrain
        self.handle_terrain_interaction(cell)
        
        # Update visibility
        self.update_visibility()
        
        return True
    
    def handle_terrain_interaction(self, cell: MapCell):
        """Handle player interaction with special terrain"""
        if cell.terrain == TerrainType.WATER:
            print("💧 You step into shallow water. Your feet feel refreshed.")
        elif cell.terrain == TerrainType.CRYSTAL:
            print("✨ You approach a glowing crystal. Energy courses through you.")
            self.player.energy = min(100, self.player.energy + 10)
        elif cell.terrain == TerrainType.ARTIFACT:
            artifact_name = f"Ancient Relic #{len(self.player.inventory) + 1}"
            self.player.inventory.append(artifact_name)
            print(f"🏺 You discover: {artifact_name}")
            cell.terrain = TerrainType.EMPTY  # Remove artifact after pickup
        elif cell.terrain == TerrainType.ANOMALY:
            print("⚡ You encounter a strange anomaly. Reality warps around you...")
            # Could trigger special events or quests
            self.discovered_locations.add("anomaly")
    
    def render_map(self) -> str:
        """Render the current view of the map"""
        output = []
        
        # Calculate view window
        px, py = self.player.x, self.player.y
        start_x = max(0, px - self.view_radius)
        end_x = min(self.width, px + self.view_radius + 1)
        start_y = max(0, py - self.view_radius)
        end_y = min(self.height, py + self.view_radius + 1)
        
        for y in range(start_y, end_y):
            line = ""
            for x in range(start_x, end_x):
                if x == px and y == py:
                    line += "@"  # Player
                else:
                    cell = self.current_map.get((x, y))
                    if cell and cell.visible:
                        line += cell.terrain.value
                    elif cell and cell.explored:
                        # Show explored but not visible areas dimmed
                        if cell.terrain == TerrainType.WALL:
                            line += "▓"
                        else:
                            line += "·"
                    else:
                        line += " "  # Unexplored
            output.append(line)
        
        return "\n".join(output)
    
    def get_status(self) -> str:
        """Get player status information"""
        return f"""
🗺️  EXPLORATION STATUS
====================
Position: ({self.player.x}, {self.player.y})
HP: {self.player.hp}/100
Energy: {self.player.energy}/100
Inventory: {len(self.player.inventory)} items
Discovered: {len(self.discovered_locations)} locations

🎒 Inventory:
{chr(10).join(f"  - {item}" for item in self.player.inventory) if self.player.inventory else "  (empty)"}
        """.strip()
    
    def load_state(self):
        """Load exploration state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.player.x = data.get('player_x', self.player.x)
                    self.player.y = data.get('player_y', self.player.y)
                    self.player.hp = data.get('player_hp', self.player.hp)
                    self.player.energy = data.get('player_energy', self.player.energy)
                    self.player.inventory = data.get('inventory', [])
                    self.discovered_locations = set(data.get('discovered', []))
            except Exception as e:
                print(f"⚠️  Error loading exploration state: {e}")
    
    def save_state(self):
        """Save exploration state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            'player_x': self.player.x,
            'player_y': self.player.y,
            'player_hp': self.player.hp,
            'player_energy': self.player.energy,
            'inventory': self.player.inventory,
            'discovered': list(self.discovered_locations)
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

def main():
    """Interactive exploration game"""
    engine = ExplorationEngine()
    engine.update_visibility()
    
    print("🗺️  NuSyQ Exploration Engine")
    print("Controls: WASD to move, 'status' for info, 'new' for new map, 'quit' to exit")
    
    while True:
        # Render current view
        print("\n" + "="*50)
        print(engine.render_map())
        print("="*50)
        
        try:
            command = input("Move (WASD) or command: ").strip().lower()
            
            if command == "quit":
                break
            elif command == "status":
                print(engine.get_status())
            elif command == "new":
                engine.current_map = engine.generate_map()
                engine.player.x = engine.width // 2
                engine.player.y = engine.height // 2
                engine.update_visibility()
                print("🌍 Generated new area to explore!")
            elif command in "wasd":
                # Movement
                if command == "w":
                    engine.move_player(0, -1)
                elif command == "a":
                    engine.move_player(-1, 0)
                elif command == "s":
                    engine.move_player(0, 1)
                elif command == "d":
                    engine.move_player(1, 0)
            else:
                print("Unknown command. Use WASD to move, 'status', 'new', or 'quit'")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break
        
        engine.save_state()

if __name__ == "__main__":
    main()