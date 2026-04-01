"""
🎨 Layer management system for complex UI composition
TouchDesigner-style layering with z-index, blending, and effects
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class BlendMode(Enum):
    NORMAL = "normal"
    ADD = "add"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"

@dataclass
class Layer:
    name: str
    z_index: int = 0
    visible: bool = True
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    transform: Dict = None
    content: str = ""
    style: str = "white"
    
    def __post_init__(self):
        if self.transform is None:
            self.transform = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0.0}

class LayerComposer:
    """Compose multiple layers with blending and effects"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.layers: List[Layer] = []
        self.background_char = " "
        
    def add_layer(self, layer: Layer):
        """Add a layer to the composition"""
        self.layers.append(layer)
        self.layers.sort(key=lambda l: l.z_index)
    
    def remove_layer(self, name: str):
        """Remove a layer by name"""
        self.layers = [l for l in self.layers if l.name != name]
    
    def get_layer(self, name: str) -> Optional[Layer]:
        """Get a layer by name"""
        return next((l for l in self.layers if l.name == name), None)
    
    def compose(self) -> List[str]:
        """Compose all layers into final output"""
        # Create canvas
        canvas = [[self.background_char for _ in range(self.width)] for _ in range(self.height)]
        
        # Render each visible layer
        for layer in self.layers:
            if not layer.visible or layer.opacity <= 0:
                continue
                
            self.render_layer_to_canvas(layer, canvas)
        
        # Convert canvas to strings
        return ["".join(row) for row in canvas]
    
    def render_layer_to_canvas(self, layer: Layer, canvas: List[List[str]]):
        """Render a single layer to the canvas"""
        if not layer.content:
            return
            
        lines = layer.content.split('\n')
        
        # Apply transform
        x_offset = layer.transform.get("x", 0)
        y_offset = layer.transform.get("y", 0)
        scale = layer.transform.get("scale", 1.0)
        
        for y, line in enumerate(lines):
            canvas_y = int(y * scale + y_offset)
            if canvas_y < 0 or canvas_y >= self.height:
                continue
                
            for x, char in enumerate(line):
                canvas_x = int(x * scale + x_offset)
                if canvas_x < 0 or canvas_x >= self.width:
                    continue
                
                # Apply blending
                if char != ' ':  # Don't blend transparent characters
                    canvas[canvas_y][canvas_x] = self.blend_char(
                        canvas[canvas_y][canvas_x], char, layer.blend_mode, layer.opacity
                    )
    
    def blend_char(self, base: str, overlay: str, mode: BlendMode, opacity: float) -> str:
        """Blend two characters based on blend mode"""
        if opacity <= 0:
            return base
        if opacity >= 1 and mode == BlendMode.NORMAL:
            return overlay
            
        # For ASCII blending, we'll use character intensity
        if mode == BlendMode.ADD:
            return self.add_chars(base, overlay, opacity)
        elif mode == BlendMode.MULTIPLY:
            return self.multiply_chars(base, overlay, opacity)
        else:
            return overlay if opacity > 0.5 else base
    
    def add_chars(self, base: str, overlay: str, opacity: float) -> str:
        """Add character intensities"""
        intensity_map = {' ': 0, '░': 0.25, '▒': 0.5, '▓': 0.75, '█': 1.0}
        reverse_map = {0: ' ', 0.25: '░', 0.5: '▒', 0.75: '▓', 1.0: '█'}
        
        base_intensity = intensity_map.get(base, 0.5)
        overlay_intensity = intensity_map.get(overlay, 0.5)
        
        result_intensity = min(1.0, base_intensity + overlay_intensity * opacity)
        
        # Find closest character
        closest = min(reverse_map.keys(), key=lambda x: abs(x - result_intensity))
        return reverse_map[closest]
    
    def multiply_chars(self, base: str, overlay: str, opacity: float) -> str:
        """Multiply character intensities"""
        intensity_map = {' ': 0, '░': 0.25, '▒': 0.5, '▓': 0.75, '█': 1.0}
        reverse_map = {0: ' ', 0.25: '░', 0.5: '▒', 0.75: '▓', 1.0: '█'}
        
        base_intensity = intensity_map.get(base, 0.5)
        overlay_intensity = intensity_map.get(overlay, 0.5)
        
        result_intensity = base_intensity * (1 - opacity + overlay_intensity * opacity)
        
        # Find closest character
        closest = min(reverse_map.keys(), key=lambda x: abs(x - result_intensity))
        return reverse_map[closest]

class EffectLayer(Layer):
    """Layer with built-in effects"""
    
    def __init__(self, name: str, effect_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.effect_func = effect_func
        self.effect_params = {}
        
    def update(self, time: float, **params):
        """Update layer content with effect"""
        self.effect_params.update(params)
        self.content = self.effect_func(time, **self.effect_params)

class ParticleLayer(Layer):
    """Layer for particle systems"""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.particles = []
        
    def add_particle(self, x: float, y: float, vx: float = 0, vy: float = 0, life: float = 1.0, char: str = "*"):
        """Add a particle"""
        self.particles.append({
            "x": x, "y": y, "vx": vx, "vy": vy, 
            "life": life, "max_life": life, "char": char
        })
        
    def update(self, dt: float):
        """Update particle positions and life"""
        for particle in self.particles[:]:
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["life"] -= dt
            
            if particle["life"] <= 0:
                self.particles.remove(particle)
        
        # Render particles to content
        if self.particles:
            # Find bounds
            min_x = int(min(p["x"] for p in self.particles))
            max_x = int(max(p["x"] for p in self.particles))
            min_y = int(min(p["y"] for p in self.particles))
            max_y = int(max(p["y"] for p in self.particles))
            
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            
            # Create particle canvas
            canvas = [[' ' for _ in range(width)] for _ in range(height)]
            
            for particle in self.particles:
                x = int(particle["x"] - min_x)
                y = int(particle["y"] - min_y)
                
                if 0 <= x < width and 0 <= y < height:
                    # Fade based on life
                    life_ratio = particle["life"] / particle["max_life"]
                    if life_ratio > 0.75:
                        char = "█"
                    elif life_ratio > 0.5:
                        char = "▓"
                    elif life_ratio > 0.25:
                        char = "▒"
                    else:
                        char = "░"
                    
                    canvas[y][x] = char
            
            self.content = "\n".join("".join(row) for row in canvas)
            
            # Update transform to position correctly
            self.transform["x"] = min_x
            self.transform["y"] = min_y
        else:
            self.content = ""
            
class UILayer(Layer):
    """Layer for UI elements with layout"""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.elements = []
        
    def add_element(self, x: int, y: int, content: str, style: str = "white"):
        """Add a UI element"""
        self.elements.append({"x": x, "y": y, "content": content, "style": style})
        
    def render_elements(self, width: int, height: int):
        """Render all UI elements to content"""
        canvas = [[' ' for _ in range(width)] for _ in range(height)]
        
        for element in self.elements:
            x, y = element["x"], element["y"]
            content = element["content"]
            
            lines = content.split('\n')
            for dy, line in enumerate(lines):
                canvas_y = y + dy
                if canvas_y < 0 or canvas_y >= height:
                    continue
                    
                for dx, char in enumerate(line):
                    canvas_x = x + dx
                    if canvas_x < 0 or canvas_x >= width:
                        continue
                    
                    if char != ' ':
                        canvas[canvas_y][canvas_x] = char
        
        self.content = "\n".join("".join(row) for row in canvas)

def create_ripple_layer(name: str, z_index: int = 0) -> EffectLayer:
    """Create a ripple effect layer"""
    def ripple_effect(time: float, **params):
        from .effects import sine_ripple
        width = params.get("width", 40)
        height = params.get("height", 20)
        return sine_ripple(width, height, time)
    
    return EffectLayer(name, ripple_effect, z_index=z_index)

def create_noise_layer(name: str, z_index: int = 0) -> EffectLayer:
    """Create a noise effect layer"""
    def noise_effect(time: float, **params):
        from .effects import noise_flow
        width = params.get("width", 40)
        height = params.get("height", 20)
        return noise_flow(width, height, time)
    
    return EffectLayer(name, noise_effect, z_index=z_index)

def create_star_field_layer(name: str, z_index: int = 0) -> EffectLayer:
    """Create a star field effect layer"""
    def star_effect(time: float, **params):
        from .effects import star_field
        width = params.get("width", 40)
        height = params.get("height", 20)
        return star_field(width, height, time)
    
    return EffectLayer(name, star_effect, z_index=z_index)