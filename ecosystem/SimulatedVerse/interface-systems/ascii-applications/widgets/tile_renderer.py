"""
🗺️ Advanced Tile Renderer
FOV, lighting, multi-layer rendering for roguelike maps
"""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import numpy as np

from ..palette import pick

class TileType(Enum):
    EMPTY = "empty"
    WALL = "wall"
    FLOOR = "floor"
    DOOR = "door"
    WATER = "water"
    LAVA = "lava"
    GRASS = "grass"
    ROCK = "rock"
    TREE = "tree"
    CRYSTAL = "crystal"

@dataclass
class Tile:
    type: TileType
    char: str
    style: str
    solid: bool = False
    transparent: bool = True
    elevation: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Light:
    x: int
    y: int
    radius: float
    intensity: float
    color: Tuple[int, int, int] = (255, 255, 255)

@dataclass
class Entity:
    x: int
    y: int
    char: str
    style: str
    name: str
    visible: bool = True
    z_order: int = 0

class FOVAlgorithm(Enum):
    SHADOWCASTING = "shadowcasting"
    RAYCASTING = "raycasting"
    SIMPLE = "simple"

class TileRenderer(Widget):
    """Advanced tile-based map renderer with FOV and lighting"""
    
    camera_x = reactive(0)
    camera_y = reactive(0)
    player_x = reactive(10)
    player_y = reactive(10)
    fov_radius = reactive(12)
    fov_algorithm = reactive(FOVAlgorithm.SHADOWCASTING)
    show_explored = reactive(True)
    lighting_enabled = reactive(True)
    
    def __init__(self, map_width=50, map_height=30, **kwargs):
        super().__init__(**kwargs)
        self.map_width = map_width
        self.map_height = map_height
        
        # Initialize maps
        self.tile_map = self.create_example_map()
        self.visible_tiles = set()
        self.explored_tiles = set()
        self.light_map = np.zeros((map_height, map_width), dtype=float)
        self.lights = []
        self.entities = []
        
        # Tile definitions
        self.tile_definitions = {
            TileType.EMPTY: Tile(TileType.EMPTY, " ", "black", False, True),
            TileType.WALL: Tile(TileType.WALL, "█", "white", True, False),
            TileType.FLOOR: Tile(TileType.FLOOR, "·", "dim", False, True),
            TileType.DOOR: Tile(TileType.DOOR, "+", "yellow", False, True),
            TileType.WATER: Tile(TileType.WATER, "~", "blue", False, True),
            TileType.LAVA: Tile(TileType.LAVA, "≈", "red", False, True),
            TileType.GRASS: Tile(TileType.GRASS, ",", "green", False, True),
            TileType.ROCK: Tile(TileType.ROCK, "▒", "dim", True, False),
            TileType.TREE: Tile(TileType.TREE, "♣", "green", True, False),
            TileType.CRYSTAL: Tile(TileType.CRYSTAL, "*", "cyan", False, True),
        }
        
        # Add some lights
        self.add_light(self.player_x, self.player_y, 8, 1.0, (255, 255, 200))
        self.add_light(25, 15, 5, 0.7, (100, 200, 255))
        
        # Add some entities
        self.add_entity(15, 12, "@", "cyan", "Player")
        self.add_entity(20, 8, "G", "green", "Goblin")
        self.add_entity(30, 20, "D", "red", "Dragon")
    
    def create_example_map(self) -> List[List[TileType]]:
        """Create an example map"""
        # Initialize with floor
        tile_map = [[TileType.FLOOR for _ in range(self.map_width)] 
                   for _ in range(self.map_height)]
        
        # Add walls around the edges
        for x in range(self.map_width):
            tile_map[0][x] = TileType.WALL
            tile_map[self.map_height - 1][x] = TileType.WALL
        
        for y in range(self.map_height):
            tile_map[y][0] = TileType.WALL
            tile_map[y][self.map_width - 1] = TileType.WALL
        
        # Add some rooms and corridors
        self.add_room(tile_map, 5, 5, 10, 8)
        self.add_room(tile_map, 20, 10, 8, 6)
        self.add_room(tile_map, 35, 5, 12, 10)
        self.add_room(tile_map, 15, 20, 15, 8)
        
        # Add corridors
        self.add_corridor(tile_map, 15, 9, 20, 13)
        self.add_corridor(tile_map, 28, 13, 35, 10)
        self.add_corridor(tile_map, 22, 16, 22, 20)
        
        # Add some water
        for x in range(40, 45):
            for y in range(18, 22):
                if tile_map[y][x] == TileType.FLOOR:
                    tile_map[y][x] = TileType.WATER
        
        # Add some trees
        for _ in range(10):
            x, y = np.random.randint(1, self.map_width-1), np.random.randint(1, self.map_height-1)
            if tile_map[y][x] == TileType.FLOOR:
                tile_map[y][x] = TileType.TREE
        
        # Add some crystals
        for _ in range(5):
            x, y = np.random.randint(1, self.map_width-1), np.random.randint(1, self.map_height-1)
            if tile_map[y][x] == TileType.FLOOR:
                tile_map[y][x] = TileType.CRYSTAL
        
        return tile_map
    
    def add_room(self, tile_map: List[List[TileType]], x: int, y: int, width: int, height: int):
        """Add a room to the map"""
        for dy in range(height):
            for dx in range(width):
                map_x, map_y = x + dx, y + dy
                if (0 <= map_x < self.map_width and 0 <= map_y < self.map_height):
                    if dx == 0 or dx == width-1 or dy == 0 or dy == height-1:
                        tile_map[map_y][map_x] = TileType.WALL
                    else:
                        tile_map[map_y][map_x] = TileType.FLOOR
        
        # Add doors
        if width > 4:
            door_x = x + width // 2
            tile_map[y][door_x] = TileType.DOOR
            tile_map[y + height - 1][door_x] = TileType.DOOR
        
        if height > 4:
            door_y = y + height // 2
            tile_map[door_y][x] = TileType.DOOR
            tile_map[door_y][x + width - 1] = TileType.DOOR
    
    def add_corridor(self, tile_map: List[List[TileType]], x1: int, y1: int, x2: int, y2: int):
        """Add a corridor between two points"""
        # L-shaped corridor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.map_width and 0 <= y1 < self.map_height:
                tile_map[y1][x] = TileType.FLOOR
        
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x2 < self.map_width and 0 <= y < self.map_height:
                tile_map[y][x2] = TileType.FLOOR
    
    def add_light(self, x: int, y: int, radius: float, intensity: float, 
                  color: Tuple[int, int, int] = (255, 255, 255)):
        """Add a light source"""
        self.lights.append(Light(x, y, radius, intensity, color))
        self.update_lighting()
    
    def add_entity(self, x: int, y: int, char: str, style: str, name: str):
        """Add an entity to the map"""
        self.entities.append(Entity(x, y, char, style, name))
    
    def update_lighting(self):
        """Update the lighting map"""
        if not self.lighting_enabled:
            self.light_map.fill(0.3)  # Ambient light
            return
        
        self.light_map.fill(0.1)  # Low ambient light
        
        for light in self.lights:
            self.apply_light(light)
    
    def apply_light(self, light: Light):
        """Apply a single light source to the light map"""
        for y in range(max(0, int(light.y - light.radius)), 
                      min(self.map_height, int(light.y + light.radius) + 1)):
            for x in range(max(0, int(light.x - light.radius)), 
                          min(self.map_width, int(light.x + light.radius) + 1)):
                
                distance = math.sqrt((x - light.x)**2 + (y - light.y)**2)
                if distance <= light.radius:
                    # Check line of sight
                    if self.has_line_of_sight(light.x, light.y, x, y):
                        # Calculate light intensity with falloff
                        intensity = light.intensity * (1.0 - distance / light.radius)
                        self.light_map[y, x] = min(1.0, self.light_map[y, x] + intensity)
    
    def has_line_of_sight(self, x1: float, y1: float, x2: int, y2: int) -> bool:
        """Check if there's line of sight between two points"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = int(x1), int(y1)
        n = 1 + int(dx + dy)
        x_inc = 1 if x2 > x1 else -1
        y_inc = 1 if y2 > y1 else -1
        error = dx - dy
        
        dx *= 2
        dy *= 2
        
        for _ in range(n):
            if not self.is_transparent(x, y):
                return False
            
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
        
        return True
    
    def is_transparent(self, x: int, y: int) -> bool:
        """Check if a tile is transparent"""
        if not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        
        tile_type = self.tile_map[y][x]
        tile_def = self.tile_definitions[tile_type]
        return tile_def.transparent
    
    def calculate_fov(self):
        """Calculate field of view"""
        if self.fov_algorithm == FOVAlgorithm.SIMPLE:
            self.calculate_simple_fov()
        elif self.fov_algorithm == FOVAlgorithm.SHADOWCASTING:
            self.calculate_shadowcasting_fov()
        else:
            self.calculate_raycasting_fov()
    
    def calculate_simple_fov(self):
        """Simple circular FOV"""
        self.visible_tiles.clear()
        
        for dy in range(-self.fov_radius, self.fov_radius + 1):
            for dx in range(-self.fov_radius, self.fov_radius + 1):
                if dx*dx + dy*dy <= self.fov_radius*self.fov_radius:
                    x, y = self.player_x + dx, self.player_y + dy
                    if (0 <= x < self.map_width and 0 <= y < self.map_height):
                        self.visible_tiles.add((x, y))
                        self.explored_tiles.add((x, y))
    
    def calculate_shadowcasting_fov(self):
        """Shadowcasting FOV algorithm"""
        self.visible_tiles.clear()
        self.visible_tiles.add((self.player_x, self.player_y))
        
        # Cast shadows in 8 octants
        for octant in range(8):
            self.cast_shadow(1, 0.0, 1.0, octant)
    
    def cast_shadow(self, row: int, start_slope: float, end_slope: float, octant: int):
        """Cast shadows for shadowcasting algorithm"""
        if start_slope >= end_slope:
            return
        
        next_start_slope = start_slope
        
        for col in range(row, self.fov_radius + 1):
            blocked = False
            
            for dx in range(col, -1, -1):
                dy = row
                x, y = self.player_x, self.player_y
                
                # Transform coordinates based on octant
                if octant == 0:
                    x, y = x + dx, y - dy
                elif octant == 1:
                    x, y = x + dy, y - dx
                elif octant == 2:
                    x, y = x - dy, y - dx
                elif octant == 3:
                    x, y = x - dx, y - dy
                elif octant == 4:
                    x, y = x - dx, y + dy
                elif octant == 5:
                    x, y = x - dy, y + dx
                elif octant == 6:
                    x, y = x + dy, y + dx
                elif octant == 7:
                    x, y = x + dx, y + dy
                
                if not (0 <= x < self.map_width and 0 <= y < self.map_height):
                    continue
                
                left_slope = (dx - 0.5) / (dy + 0.5)
                right_slope = (dx + 0.5) / (dy - 0.5)
                
                if start_slope >= right_slope:
                    continue
                elif end_slope <= left_slope:
                    break
                
                if dx*dx + dy*dy <= self.fov_radius*self.fov_radius:
                    self.visible_tiles.add((x, y))
                    self.explored_tiles.add((x, y))
                
                if blocked:
                    if not self.is_transparent(x, y):
                        next_start_slope = right_slope
                        continue
                    else:
                        blocked = False
                        start_slope = next_start_slope
                else:
                    if not self.is_transparent(x, y) and row < self.fov_radius:
                        blocked = True
                        self.cast_shadow(row + 1, start_slope, left_slope, octant)
                        next_start_slope = right_slope
            
            if blocked:
                break
    
    def calculate_raycasting_fov(self):
        """Raycasting FOV algorithm"""
        self.visible_tiles.clear()
        
        num_rays = 360
        for angle in range(0, 360, 360 // num_rays):
            self.cast_ray(angle)
    
    def cast_ray(self, angle: int):
        """Cast a single ray for raycasting FOV"""
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        x, y = float(self.player_x), float(self.player_y)
        
        for step in range(self.fov_radius):
            x += dx * 0.5
            y += dy * 0.5
            
            tile_x, tile_y = int(x), int(y)
            
            if not (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height):
                break
            
            self.visible_tiles.add((tile_x, tile_y))
            self.explored_tiles.add((tile_x, tile_y))
            
            if not self.is_transparent(tile_x, tile_y):
                break
    
    def render(self):
        """Render the map with FOV and lighting"""
        self.calculate_fov()
        self.update_lighting()
        
        width = min(self.size.width, 80)
        height = min(self.size.height - 3, 24)  # Leave room for status
        
        # Calculate camera bounds
        start_x = max(0, min(self.map_width - width, self.camera_x))
        start_y = max(0, min(self.map_height - height, self.camera_y))
        end_x = min(self.map_width, start_x + width)
        end_y = min(self.map_height, start_y + height)
        
        lines = []
        
        for y in range(start_y, end_y):
            line = ""
            styles = []
            
            for x in range(start_x, end_x):
                char, style = self.get_tile_display(x, y)
                line += char
                styles.append(style)
            
            lines.append((line, styles))
        
        # Build styled text
        result = Text("🗺️ MAP VIEW\n", style=pick("accent_a"))
        
        for line, styles in lines:
            for i, (char, style) in enumerate(zip(line, styles)):
                result.append(char, style=style)
            result.append("\n")
        
        # Add status line
        status = f"Pos: ({self.player_x}, {self.player_y}) | "
        status += f"FOV: {len(self.visible_tiles)} | "
        status += f"Explored: {len(self.explored_tiles)}"
        result.append(status, style=pick("text_dim"))
        
        return result
    
    def get_tile_display(self, x: int, y: int) -> Tuple[str, str]:
        """Get the character and style for a tile"""
        # Check if tile is visible
        if (x, y) in self.visible_tiles:
            # Tile is currently visible
            tile_type = self.tile_map[y][x]
            tile_def = self.tile_definitions[tile_type]
            
            # Check for entities at this position
            for entity in self.entities:
                if entity.x == x and entity.y == y and entity.visible:
                    char = entity.char
                    style = entity.style
                    break
            else:
                char = tile_def.char
                style = tile_def.style
            
            # Apply lighting if enabled
            if self.lighting_enabled:
                light_level = self.light_map[y, x]
                if light_level < 0.3:
                    style = "dim " + style
                elif light_level > 0.8:
                    style = "bold " + style
            
            return char, style
            
        elif self.show_explored and (x, y) in self.explored_tiles:
            # Tile was explored but not currently visible
            tile_type = self.tile_map[y][x]
            tile_def = self.tile_definitions[tile_type]
            return tile_def.char, "dim " + tile_def.style
        
        else:
            # Tile is unexplored
            return " ", "black"
    
    def move_camera_to_player(self):
        """Center camera on player"""
        viewport_width = min(self.size.width, 80)
        viewport_height = min(self.size.height - 3, 24)
        
        self.camera_x = max(0, min(self.map_width - viewport_width, 
                                  self.player_x - viewport_width // 2))
        self.camera_y = max(0, min(self.map_height - viewport_height, 
                                  self.player_y - viewport_height // 2))