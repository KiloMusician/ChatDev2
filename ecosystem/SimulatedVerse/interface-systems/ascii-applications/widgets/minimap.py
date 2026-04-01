from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
import numpy as np
from .. import effects
from ..palette import pick

class Minimap(Widget):
    """Minimap widget using braille characters for high density display"""
    
    map_data = reactive(None)
    viewport_x = reactive(0)
    viewport_y = reactive(0)
    zoom_level = reactive(1.0)
    show_units = reactive(True)
    
    def __init__(self, width=16, height=8, **kwargs):
        super().__init__(**kwargs)
        self.map_width = width
        self.map_height = height
    
    def render(self):
        """Render the minimap using braille characters"""
        if self.map_data is None:
            return self.render_placeholder()
        
        # Use braille for 2x4 pixel density
        braille_w = self.map_width * 2
        braille_h = self.map_height * 4
        
        def sample(x, y):
            # Sample from map data
            if hasattr(self.map_data, 'shape'):
                # Numpy array map data
                map_h, map_w = self.map_data.shape
                map_x = int((x / braille_w) * map_w)
                map_y = int((y / braille_h) * map_h)
                
                if 0 <= map_x < map_w and 0 <= map_y < map_h:
                    return float(self.map_data[map_y, map_x] > 0.5)
            else:
                # Dictionary-based map data
                map_x = int(x / 2)  # Scale down
                map_y = int(y / 4)
                
                # Sample from dictionary map
                if (map_x, map_y) in self.map_data:
                    cell = self.map_data[(map_x, map_y)]
                    if hasattr(cell, 'terrain'):
                        return 1.0 if cell.terrain.value != '.' else 0.0
                    return 1.0 if cell != '.' else 0.0
            
            return 0.0
        
        # Generate braille map
        braille_map = effects.canvas_to_braille(braille_w, braille_h, sample)
        
        # Add viewport indicator if applicable
        map_text = Text(braille_map, style=pick("accent_a"))
        
        return map_text
    
    def render_placeholder(self):
        """Render placeholder when no map data available"""
        # Generate a simple pattern
        braille_w = self.map_width * 2
        braille_h = self.map_height * 4
        
        def sample(x, y):
            # Create a simple checkerboard pattern
            return 1.0 if (x // 4 + y // 4) % 2 == 0 else 0.0
        
        pattern = effects.canvas_to_braille(braille_w, braille_h, sample)
        return Text(pattern, style=pick("text_dim"))
    
    def set_map_data(self, map_data):
        """Update the map data"""
        self.map_data = map_data
        self.refresh()
    
    def set_viewport(self, x, y):
        """Update viewport position"""
        self.viewport_x = x
        self.viewport_y = y
        self.refresh()

class RadarMap(Widget):
    """Radar-style minimap with sweep animation"""
    
    contacts = reactive([])
    sweep_angle = reactive(0.0)
    range_rings = reactive(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_interval(1/10, self.update_sweep)  # 10 FPS sweep
    
    def update_sweep(self):
        """Update radar sweep angle"""
        self.sweep_angle = (self.sweep_angle + 0.2) % (2 * 3.14159)
        self.refresh()
    
    def render(self):
        """Render radar-style display"""
        width = max(16, self.size.width)
        height = max(8, self.size.height)
        
        # Use radar sweep effect
        radar_display = effects.radar_sweep(
            width * 2, height * 4, 
            self.sweep_angle / 0.2,  # Convert to time
            sweep_speed=1.0
        )
        
        return Text(radar_display, style=pick("good"))
    
    def add_contact(self, x, y, contact_type="unknown"):
        """Add a contact to the radar"""
        contact = {"x": x, "y": y, "type": contact_type}
        new_contacts = [contact] + self.contacts
        self.contacts = new_contacts[:20]  # Limit to 20 contacts

class HeatMap(Widget):
    """Heat map display for resource density, danger levels, etc."""
    
    heat_data = reactive(None)
    color_scheme = reactive("thermal")  # thermal, rainbow, monochrome
    
    def render(self):
        """Render heat map visualization"""
        if self.heat_data is None:
            return self.render_demo_heat()
        
        # Convert heat data to braille visualization
        heat_display = effects.heatmap_from_field(self.heat_data)
        
        # Apply color scheme
        if self.color_scheme == "thermal":
            style = pick("warn")  # Orange/red for heat
        elif self.color_scheme == "cold":
            style = pick("accent_a")  # Blue for cold
        else:
            style = pick("text_bright")
        
        return Text(heat_display, style=style)
    
    def render_demo_heat(self):
        """Render demo heat pattern"""
        width = max(16, self.size.width)
        height = max(8, self.size.height)
        
        # Create demo heat field
        demo_field = np.random.random((height * 2, width * 2))
        heat_display = effects.heatmap_from_field(demo_field, threshold=0.6)
        
        return Text(heat_display, style=pick("warn"))
    
    def set_heat_data(self, data):
        """Update heat map data"""
        self.heat_data = data
        self.refresh()

class FlowField(Widget):
    """Flow field visualization for showing movement patterns"""
    
    flow_data = reactive(None)
    show_vectors = reactive(True)
    
    def render(self):
        """Render flow field using directional characters"""
        if self.flow_data is None:
            return self.render_demo_flow()
        
        # Convert flow vectors to directional characters
        flow_text = Text()
        
        # Directional characters
        arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        
        for y in range(self.size.height):
            if y > 0:
                flow_text.append("\n")
            
            for x in range(self.size.width):
                # Get flow direction (in demo, use position-based pattern)
                angle = (x + y) % 8  # Simple pattern
                arrow = arrows[angle]
                
                # Color based on flow strength
                flow_text.append(arrow, style=pick("accent_b"))
        
        return flow_text
    
    def render_demo_flow(self):
        """Render demo flow pattern"""
        demo_text = Text()
        
        for y in range(8):
            if y > 0:
                demo_text.append("\n")
            
            for x in range(16):
                # Create spiral pattern
                center_x, center_y = 8, 4
                dx, dy = x - center_x, y - center_y
                
                if dx == 0 and dy == 0:
                    arrow = "●"
                else:
                    # Simplified directional calculation
                    if abs(dx) > abs(dy):
                        arrow = "→" if dx > 0 else "←"
                    else:
                        arrow = "↓" if dy > 0 else "↑"
                
                demo_text.append(arrow, style=pick("accent_b"))
        
        return demo_text

class OverviewMap(Widget):
    """Overview map showing multiple layers of information"""
    
    terrain_layer = reactive(True)
    units_layer = reactive(True)
    buildings_layer = reactive(True)
    effects_layer = reactive(False)
    
    def render(self):
        """Render multi-layer overview map"""
        # For now, render a combined view
        map_text = Text("🗺️ OVERVIEW\n", style=pick("text_bright"))
        
        # Legend
        if self.terrain_layer:
            map_text.append("Terrain: █ land ░ water\n", style=pick("text_dim"))
        
        if self.units_layer:
            map_text.append("Units: ♦ colonists ⚙ drones\n", style=pick("text_dim"))
        
        if self.buildings_layer:
            map_text.append("Buildings: H shelter W workshop\n", style=pick("text_dim"))
        
        # Simple map representation
        sample_map = [
            "████░░░░████████",
            "██♦░░░░░██W░░H██",
            "██░░░░░░██░░░░██",
            "████░░░░████⚙░██",
            "████████████████"
        ]
        
        for line in sample_map:
            map_text.append(line + "\n", style=pick("accent_a"))
        
        return map_text
    
    def toggle_layer(self, layer_name):
        """Toggle a map layer on/off"""
        if layer_name == "terrain":
            self.terrain_layer = not self.terrain_layer
        elif layer_name == "units":
            self.units_layer = not self.units_layer
        elif layer_name == "buildings":
            self.buildings_layer = not self.buildings_layer
        elif layer_name == "effects":
            self.effects_layer = not self.effects_layer
        
        self.refresh()