"""
🎨 Color Themes for TouchDesigner ASCII Interface
Multiple palettes with automatic fallback and gradient support
"""

from rich.style import Style
from rich.color import Color
from typing import Dict, Tuple, List
import os

class ColorTheme:
    """A complete color theme with primary, accent, and semantic colors"""
    
    def __init__(self, name: str, colors: Dict[str, Tuple[int, int, int]]):
        self.name = name
        self.colors = colors
        self._styles = {}
        self._generate_styles()
    
    def _generate_styles(self):
        """Generate Rich styles from color tuples"""
        for color_name, (r, g, b) in self.colors.items():
            self._styles[color_name] = Style(color=Color.from_rgb(r, g, b))
    
    def get_style(self, color_name: str, fallback: str = "white") -> Style:
        """Get a style by name with fallback"""
        return self._styles.get(color_name, Style(color=fallback))
    
    def get_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Get RGB tuple for a color"""
        return self.colors.get(color_name, (255, 255, 255))

# TouchDesigner-inspired themes
THEMES = {
    "touchdesigner": ColorTheme("TouchDesigner", {
        "primary": (255, 255, 255),      # White
        "secondary": (128, 128, 128),    # Gray
        "accent_a": (50, 200, 255),      # Cyan
        "accent_b": (255, 120, 80),      # Orange
        "accent_c": (255, 255, 100),     # Yellow
        "background": (30, 30, 30),      # Dark gray
        "good": (120, 220, 120),         # Green
        "warn": (255, 210, 90),          # Amber
        "bad": (255, 90, 120),           # Red
        "text_bright": (240, 240, 240),  # Bright text
        "text_dim": (120, 120, 120),     # Dim text
        "grid": (60, 60, 60),            # Grid lines
    }),
    
    "cyberpunk": ColorTheme("Cyberpunk", {
        "primary": (0, 255, 255),        # Cyan
        "secondary": (255, 0, 255),      # Magenta
        "accent_a": (0, 255, 100),       # Neon green
        "accent_b": (255, 50, 150),      # Hot pink
        "accent_c": (255, 255, 0),       # Electric yellow
        "background": (10, 10, 20),      # Deep blue-black
        "good": (0, 255, 100),           # Neon green
        "warn": (255, 150, 0),           # Orange
        "bad": (255, 20, 80),            # Hot red
        "text_bright": (200, 255, 255),  # Cyan white
        "text_dim": (80, 120, 140),      # Blue gray
        "grid": (40, 80, 100),           # Blue grid
    }),
    
    "terminal": ColorTheme("Terminal", {
        "primary": (0, 255, 0),          # Green
        "secondary": (100, 255, 100),    # Light green
        "accent_a": (0, 255, 0),         # Green
        "accent_b": (255, 255, 0),       # Yellow
        "accent_c": (0, 255, 255),       # Cyan
        "background": (0, 0, 0),         # Black
        "good": (0, 255, 0),             # Green
        "warn": (255, 255, 0),           # Yellow
        "bad": (255, 100, 100),          # Light red
        "text_bright": (200, 255, 200),  # Light green
        "text_dim": (100, 150, 100),     # Dim green
        "grid": (50, 100, 50),           # Dark green
    }),
    
    "amber": ColorTheme("Amber", {
        "primary": (255, 191, 0),        # Amber
        "secondary": (255, 140, 0),      # Dark amber
        "accent_a": (255, 191, 0),       # Amber
        "accent_b": (255, 100, 0),       # Orange
        "accent_c": (255, 255, 100),     # Light yellow
        "background": (20, 15, 0),       # Dark brown
        "good": (200, 255, 100),         # Yellow-green
        "warn": (255, 150, 0),           # Orange
        "bad": (255, 80, 0),             # Red-orange
        "text_bright": (255, 220, 100),  # Light amber
        "text_dim": (150, 100, 50),      # Brown
        "grid": (80, 60, 20),            # Dark amber
    }),
    
    "ice": ColorTheme("Ice", {
        "primary": (200, 230, 255),      # Ice blue
        "secondary": (150, 200, 255),    # Blue
        "accent_a": (100, 200, 255),     # Sky blue
        "accent_b": (200, 255, 255),     # Cyan
        "accent_c": (255, 255, 255),     # White
        "background": (10, 20, 30),      # Dark blue
        "good": (150, 255, 200),         # Mint
        "warn": (255, 200, 150),         # Warm
        "bad": (255, 150, 150),          # Pink
        "text_bright": (230, 240, 255),  # Very light blue
        "text_dim": (100, 120, 150),     # Blue gray
        "grid": (50, 80, 120),           # Blue grid
    }),
    
    "synthwave": ColorTheme("Synthwave", {
        "primary": (255, 20, 147),       # Deep pink
        "secondary": (138, 43, 226),     # Blue violet
        "accent_a": (0, 255, 255),       # Cyan
        "accent_b": (255, 20, 147),      # Deep pink
        "accent_c": (255, 255, 0),       # Yellow
        "background": (25, 25, 112),     # Midnight blue
        "good": (50, 205, 50),           # Lime green
        "warn": (255, 165, 0),           # Orange
        "bad": (255, 69, 0),             # Red orange
        "text_bright": (255, 192, 203),  # Pink
        "text_dim": (147, 112, 219),     # Medium slate blue
        "grid": (72, 61, 139),           # Dark slate blue
    })
}

# Global theme state
current_theme = THEMES["touchdesigner"]

def set_theme(theme_name: str):
    """Set the global theme"""
    global current_theme
    if theme_name in THEMES:
        current_theme = THEMES[theme_name]
        return True
    return False

def get_current_theme() -> ColorTheme:
    """Get the current theme"""
    return current_theme

def list_themes() -> List[str]:
    """Get list of available theme names"""
    return list(THEMES.keys())

def pick(color_name: str, fallback: str = "white") -> Style:
    """Pick a color from the current theme"""
    return current_theme.get_style(color_name, fallback)

def gradient_style(value: float, min_val: float, max_val: float, 
                  start_color: Tuple[int, int, int], 
                  end_color: Tuple[int, int, int]) -> Style:
    """Create a gradient style between two colors"""
    if max_val <= min_val:
        return Style(color=Color.from_rgb(*start_color))
    
    # Normalize value to 0-1
    t = max(0, min(1, (value - min_val) / (max_val - min_val)))
    
    # Interpolate RGB
    r = int(start_color[0] + t * (end_color[0] - start_color[0]))
    g = int(start_color[1] + t * (end_color[1] - start_color[1]))
    b = int(start_color[2] + t * (end_color[2] - start_color[2]))
    
    return Style(color=Color.from_rgb(r, g, b))

def theme_preview() -> str:
    """Generate a preview string showing all colors in current theme"""
    preview_lines = [
        f"🎨 {current_theme.name.upper()} THEME",
        "═" * 30
    ]
    
    # Color samples
    color_samples = [
        ("Primary", "primary"),
        ("Secondary", "secondary"),
        ("Accent A", "accent_a"),
        ("Accent B", "accent_b"),
        ("Accent C", "accent_c"),
        ("Good", "good"),
        ("Warning", "warn"),
        ("Bad", "bad"),
        ("Bright Text", "text_bright"),
        ("Dim Text", "text_dim")
    ]
    
    for label, color_key in color_samples:
        r, g, b = current_theme.get_rgb(color_key)
        preview_lines.append(f"{label:12} ■■■ RGB({r:3},{g:3},{b:3})")
    
    return "\n".join(preview_lines)

def adaptive_colors():
    """Return colors adapted to terminal capabilities"""
    # Detect color capability
    colorterm = os.environ.get("COLORTERM", "")
    term = os.environ.get("TERM", "")
    
    if colorterm == "truecolor" or "256color" in term:
        # Full color support
        return current_theme
    elif "color" in term:
        # Basic color support - use simplified palette
        simplified = {
            "primary": (255, 255, 255),
            "accent_a": (0, 255, 255),
            "accent_b": (255, 165, 0),
            "good": (0, 255, 0),
            "warn": (255, 255, 0),
            "bad": (255, 0, 0),
            "text_bright": (255, 255, 255),
            "text_dim": (128, 128, 128)
        }
        return ColorTheme("Basic", simplified)
    else:
        # Monochrome fallback
        mono = {
            "primary": (255, 255, 255),
            "accent_a": (255, 255, 255),
            "accent_b": (255, 255, 255),
            "good": (255, 255, 255),
            "warn": (255, 255, 255),
            "bad": (255, 255, 255),
            "text_bright": (255, 255, 255),
            "text_dim": (128, 128, 128)
        }
        return ColorTheme("Mono", mono)

# Specialized palettes for different data types
DATA_TYPE_COLORS = {
    "audio": {
        "signal": (50, 200, 255),     # Cyan for audio signals
        "level": (255, 200, 50),      # Yellow for levels
        "spectrum": (255, 100, 200)   # Pink for spectrum
    },
    "visual": {
        "brightness": (255, 255, 255), # White for brightness
        "color": (255, 100, 100),      # Red for color data
        "alpha": (100, 100, 255)       # Blue for transparency
    },
    "control": {
        "parameter": (100, 255, 100),  # Green for parameters
        "trigger": (255, 255, 100),    # Yellow for triggers
        "gate": (255, 100, 255)        # Magenta for gates
    }
}

def get_data_type_color(data_type: str, sub_type: str = "signal") -> Style:
    """Get color for specific data types"""
    colors = DATA_TYPE_COLORS.get(data_type, {})
    color_rgb = colors.get(sub_type, (255, 255, 255))
    return Style(color=Color.from_rgb(*color_rgb))

# Special effects using color
def pulse_color(base_color: Tuple[int, int, int], intensity: float) -> Style:
    """Create pulsing color effect"""
    r, g, b = base_color
    factor = 0.5 + 0.5 * intensity  # Scale 0.5 to 1.0
    
    pulse_r = int(r * factor)
    pulse_g = int(g * factor)
    pulse_b = int(b * factor)
    
    return Style(color=Color.from_rgb(pulse_r, pulse_g, pulse_b))

def danger_gradient(danger_level: float) -> Style:
    """Create color gradient from safe (green) to dangerous (red)"""
    safe_color = (120, 220, 120)    # Green
    danger_color = (255, 90, 120)   # Red
    
    return gradient_style(danger_level, 0.0, 1.0, safe_color, danger_color)