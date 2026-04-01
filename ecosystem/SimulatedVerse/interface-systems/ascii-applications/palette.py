from rich.style import Style
from rich.color import Color

def rgb(r,g,b): return Style(color=Color.from_rgb(r,g,b))
TRUECOLOR = True

def pick(style_name, fallback="white"):
    # In production, load from TOML; here quick map:
    named = {
      "accent_a": rgb(50,200,255),
      "accent_b": rgb(255,120,80),
      "good":     rgb(120,220,120),
      "warn":     rgb(255,210,90),
      "bad":      rgb(255,90,120),
    }
    return named.get(style_name, Style(color=fallback))

# Gradient functions for smooth color transitions
def lerp_rgb(color1, color2, t):
    """Linear interpolation between two RGB tuples"""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    return (
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t)
    )

def gradient_style(value, min_val=0, max_val=1, start_color=(255,90,120), end_color=(120,220,120)):
    """Create a gradient style based on a value between min_val and max_val"""
    t = max(0, min(1, (value - min_val) / (max_val - min_val)))
    r, g, b = lerp_rgb(start_color, end_color, t)
    return rgb(r, g, b)

# Theme definitions
THEMES = {
    "neon": {
        "primary": rgb(0, 255, 255),
        "secondary": rgb(255, 0, 255),
        "accent": rgb(255, 255, 0),
        "background": Style(bgcolor=Color.from_rgb(0, 0, 20))
    },
    "earth": {
        "primary": rgb(139, 69, 19),
        "secondary": rgb(34, 139, 34),
        "accent": rgb(255, 215, 0),
        "background": Style(bgcolor=Color.from_rgb(25, 25, 15))
    },
    "ice": {
        "primary": rgb(173, 216, 230),
        "secondary": rgb(135, 206, 235),
        "accent": rgb(255, 255, 255),
        "background": Style(bgcolor=Color.from_rgb(10, 15, 25))
    }
}

current_theme = "neon"

def themed(element):
    """Get themed color for an element"""
    return THEMES[current_theme].get(element, pick("text_bright"))