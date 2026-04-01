"""
🎨 Color Theme Management
Dynamic theme switching and color palette management
"""

from textual.widget import Widget
from textual.widgets import Select, Button, Static, Slider
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from rich.color import Color
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ThemeCategory(Enum):
    CYBERPUNK = "cyberpunk"
    NATURE = "nature"
    SPACE = "space"
    RETRO = "retro"
    MONOCHROME = "monochrome"
    CUSTOM = "custom"

@dataclass
class ColorScheme:
    name: str
    category: ThemeCategory
    primary: Tuple[int, int, int]
    secondary: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    background: Tuple[int, int, int]
    text: Tuple[int, int, int]
    text_dim: Tuple[int, int, int]
    success: Tuple[int, int, int]
    warning: Tuple[int, int, int]
    error: Tuple[int, int, int]
    
class ThemeManager:
    """Manages color themes and provides theme switching"""
    
    def __init__(self):
        self.themes = self.load_default_themes()
        self.current_theme = "cyberpunk_neon"
        self.custom_themes = {}
    
    def load_default_themes(self) -> Dict[str, ColorScheme]:
        """Load default color themes"""
        themes = {}
        
        # Cyberpunk themes
        themes["cyberpunk_neon"] = ColorScheme(
            name="Cyberpunk Neon",
            category=ThemeCategory.CYBERPUNK,
            primary=(0, 255, 255),      # Cyan
            secondary=(255, 0, 255),    # Magenta
            accent=(255, 255, 0),       # Yellow
            background=(0, 0, 20),      # Dark blue
            text=(220, 220, 255),       # Light blue
            text_dim=(120, 120, 160),   # Dim blue
            success=(0, 255, 150),      # Green cyan
            warning=(255, 150, 0),      # Orange
            error=(255, 50, 100)        # Pink red
        )
        
        themes["cyberpunk_dark"] = ColorScheme(
            name="Cyberpunk Dark",
            category=ThemeCategory.CYBERPUNK,
            primary=(100, 255, 100),    # Green
            secondary=(255, 100, 100),  # Red
            accent=(255, 255, 100),     # Yellow
            background=(10, 10, 10),    # Almost black
            text=(200, 255, 200),       # Light green
            text_dim=(100, 150, 100),   # Dim green
            success=(100, 255, 100),    # Bright green
            warning=(255, 200, 100),    # Orange
            error=(255, 100, 100)       # Red
        )
        
        # Nature themes
        themes["forest"] = ColorScheme(
            name="Forest",
            category=ThemeCategory.NATURE,
            primary=(34, 139, 34),      # Forest green
            secondary=(139, 69, 19),    # Saddle brown
            accent=(255, 215, 0),       # Gold
            background=(25, 50, 25),    # Dark green
            text=(220, 255, 220),       # Light green
            text_dim=(140, 180, 140),   # Dim green
            success=(50, 205, 50),      # Lime green
            warning=(255, 165, 0),      # Orange
            error=(220, 20, 60)         # Crimson
        )
        
        themes["ocean"] = ColorScheme(
            name="Ocean",
            category=ThemeCategory.NATURE,
            primary=(70, 130, 180),     # Steel blue
            secondary=(32, 178, 170),   # Light sea green
            accent=(255, 218, 185),     # Peach puff
            background=(25, 25, 112),   # Midnight blue
            text=(240, 248, 255),       # Alice blue
            text_dim=(119, 136, 153),   # Light slate gray
            success=(102, 205, 170),    # Medium aquamarine
            warning=(255, 160, 122),    # Light salmon
            error=(220, 20, 60)         # Crimson
        )
        
        # Space themes
        themes["deep_space"] = ColorScheme(
            name="Deep Space",
            category=ThemeCategory.SPACE,
            primary=(138, 43, 226),     # Blue violet
            secondary=(75, 0, 130),     # Indigo
            accent=(255, 20, 147),      # Deep pink
            background=(0, 0, 0),       # Black
            text=(230, 230, 250),       # Lavender
            text_dim=(128, 128, 128),   # Gray
            success=(50, 205, 50),      # Lime green
            warning=(255, 140, 0),      # Dark orange
            error=(255, 69, 0)          # Red orange
        )
        
        themes["nebula"] = ColorScheme(
            name="Nebula",
            category=ThemeCategory.SPACE,
            primary=(255, 105, 180),    # Hot pink
            secondary=(138, 43, 226),   # Blue violet
            accent=(0, 255, 255),       # Cyan
            background=(25, 25, 112),   # Midnight blue
            text=(255, 240, 245),       # Lavender blush
            text_dim=(176, 196, 222),   # Light steel blue
            success=(127, 255, 212),    # Aquamarine
            warning=(255, 215, 0),      # Gold
            error=(255, 99, 71)         # Tomato
        )
        
        # Retro themes
        themes["retro_amber"] = ColorScheme(
            name="Retro Amber",
            category=ThemeCategory.RETRO,
            primary=(255, 191, 0),      # Amber
            secondary=(255, 140, 0),    # Dark orange
            accent=(255, 215, 0),       # Gold
            background=(0, 0, 0),       # Black
            text=(255, 191, 0),         # Amber
            text_dim=(139, 105, 20),    # Dark goldenrod
            success=(154, 205, 50),     # Yellow green
            warning=(255, 140, 0),      # Dark orange
            error=(255, 69, 0)          # Red orange
        )
        
        themes["retro_green"] = ColorScheme(
            name="Retro Green",
            category=ThemeCategory.RETRO,
            primary=(0, 255, 0),        # Lime
            secondary=(50, 205, 50),    # Lime green
            accent=(154, 205, 50),      # Yellow green
            background=(0, 0, 0),       # Black
            text=(0, 255, 0),           # Lime
            text_dim=(0, 128, 0),       # Green
            success=(50, 205, 50),      # Lime green
            warning=(255, 215, 0),      # Gold
            error=(255, 0, 0)           # Red
        )
        
        # Monochrome themes
        themes["high_contrast"] = ColorScheme(
            name="High Contrast",
            category=ThemeCategory.MONOCHROME,
            primary=(255, 255, 255),    # White
            secondary=(192, 192, 192),  # Silver
            accent=(255, 255, 255),     # White
            background=(0, 0, 0),       # Black
            text=(255, 255, 255),       # White
            text_dim=(128, 128, 128),   # Gray
            success=(255, 255, 255),    # White
            warning=(192, 192, 192),    # Silver
            error=(128, 128, 128)       # Gray
        )
        
        themes["grayscale"] = ColorScheme(
            name="Grayscale",
            category=ThemeCategory.MONOCHROME,
            primary=(200, 200, 200),    # Light gray
            secondary=(150, 150, 150),  # Gray
            accent=(255, 255, 255),     # White
            background=(30, 30, 30),    # Dark gray
            text=(220, 220, 220),       # Light gray
            text_dim=(120, 120, 120),   # Dim gray
            success=(180, 180, 180),    # Light gray
            warning=(160, 160, 160),    # Gray
            error=(100, 100, 100)       # Dark gray
        )
        
        return themes
    
    def get_theme(self, theme_name: str) -> Optional[ColorScheme]:
        """Get a theme by name"""
        return self.themes.get(theme_name) or self.custom_themes.get(theme_name)
    
    def get_themes_by_category(self, category: ThemeCategory) -> List[str]:
        """Get all theme names in a category"""
        themes = []
        for name, theme in self.themes.items():
            if theme.category == category:
                themes.append(name)
        for name, theme in self.custom_themes.items():
            if theme.category == category:
                themes.append(name)
        return themes
    
    def apply_theme(self, theme_name: str):
        """Apply a theme to the current session"""
        theme = self.get_theme(theme_name)
        if theme:
            self.current_theme = theme_name
            # Update global palette - this would integrate with the main palette system
            return True
        return False
    
    def create_custom_theme(self, name: str, base_theme: str = None) -> ColorScheme:
        """Create a new custom theme"""
        if base_theme and base_theme in self.themes:
            # Copy from existing theme
            base = self.themes[base_theme]
            custom = ColorScheme(
                name=name,
                category=ThemeCategory.CUSTOM,
                primary=base.primary,
                secondary=base.secondary,
                accent=base.accent,
                background=base.background,
                text=base.text,
                text_dim=base.text_dim,
                success=base.success,
                warning=base.warning,
                error=base.error
            )
        else:
            # Create default custom theme
            custom = ColorScheme(
                name=name,
                category=ThemeCategory.CUSTOM,
                primary=(100, 150, 200),
                secondary=(150, 100, 200),
                accent=(200, 150, 100),
                background=(20, 20, 30),
                text=(220, 220, 240),
                text_dim=(120, 120, 140),
                success=(100, 200, 150),
                warning=(200, 180, 100),
                error=(200, 100, 120)
            )
        
        self.custom_themes[name] = custom
        return custom
    
    def save_themes(self, filename: str):
        """Save custom themes to file"""
        data = {
            "custom_themes": {
                name: {
                    "name": theme.name,
                    "category": theme.category.value,
                    "primary": theme.primary,
                    "secondary": theme.secondary,
                    "accent": theme.accent,
                    "background": theme.background,
                    "text": theme.text,
                    "text_dim": theme.text_dim,
                    "success": theme.success,
                    "warning": theme.warning,
                    "error": theme.error
                }
                for name, theme in self.custom_themes.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_themes(self, filename: str):
        """Load custom themes from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            for name, theme_data in data.get("custom_themes", {}).items():
                theme = ColorScheme(
                    name=theme_data["name"],
                    category=ThemeCategory(theme_data["category"]),
                    primary=tuple(theme_data["primary"]),
                    secondary=tuple(theme_data["secondary"]),
                    accent=tuple(theme_data["accent"]),
                    background=tuple(theme_data["background"]),
                    text=tuple(theme_data["text"]),
                    text_dim=tuple(theme_data["text_dim"]),
                    success=tuple(theme_data["success"]),
                    warning=tuple(theme_data["warning"]),
                    error=tuple(theme_data["error"])
                )
                self.custom_themes[name] = theme
        except Exception as e:
            print(f"Error loading themes: {e}")

class ThemePreview(Widget):
    """Widget to preview a color theme"""
    
    theme_name = reactive("cyberpunk_neon")
    
    def __init__(self, theme_manager: ThemeManager, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager
    
    def render(self):
        """Render theme preview"""
        theme = self.theme_manager.get_theme(self.theme_name)
        if not theme:
            return Text("Theme not found", style="red")
        
        preview = Text()
        
        # Theme name
        preview.append(f"🎨 {theme.name}\n\n", style="bold")
        
        # Color swatches
        colors = [
            ("Primary", theme.primary),
            ("Secondary", theme.secondary),
            ("Accent", theme.accent),
            ("Success", theme.success),
            ("Warning", theme.warning),
            ("Error", theme.error)
        ]
        
        for name, (r, g, b) in colors:
            # Create color style
            color_style = Style(color=Color.from_rgb(r, g, b))
            bg_style = Style(bgcolor=Color.from_rgb(r, g, b))
            
            preview.append(f"{name:10}", style="white")
            preview.append("████", style=bg_style)
            preview.append(f" rgb({r:3},{g:3},{b:3})", style=color_style)
            preview.append("\n")
        
        # Sample text
        preview.append("\nSample Text:\n", style="bold")
        
        text_style = Style(color=Color.from_rgb(*theme.text))
        dim_style = Style(color=Color.from_rgb(*theme.text_dim))
        
        preview.append("Normal text ", style=text_style)
        preview.append("(dimmed text)\n", style=dim_style)
        
        # Sample UI elements
        preview.append("\nUI Elements:\n", style="bold")
        
        success_style = Style(color=Color.from_rgb(*theme.success))
        warning_style = Style(color=Color.from_rgb(*theme.warning))
        error_style = Style(color=Color.from_rgb(*theme.error))
        
        preview.append("✅ Success message\n", style=success_style)
        preview.append("⚠️  Warning message\n", style=warning_style)
        preview.append("❌ Error message\n", style=error_style)
        
        return preview

class ThemeSelector(Widget):
    """Widget for selecting and managing themes"""
    
    selected_theme = reactive("cyberpunk_neon")
    selected_category = reactive(ThemeCategory.CYBERPUNK)
    
    def __init__(self, theme_manager: ThemeManager, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = theme_manager
    
    def compose(self):
        """Compose the theme selector interface"""
        yield Static("🎨 THEME SELECTOR", classes="header")
        
        with Horizontal():
            with Vertical(classes="selector-panel"):
                yield Static("Category:")
                yield Select(
                    [(cat.value.title(), cat) for cat in ThemeCategory],
                    value=self.selected_category,
                    id="category-select"
                )
                
                yield Static("Theme:")
                yield Select(
                    self.get_theme_options(),
                    value=self.selected_theme,
                    id="theme-select"
                )
                
                with Horizontal():
                    yield Button("Apply", id="apply-theme", variant="primary")
                    yield Button("Duplicate", id="duplicate-theme")
                    yield Button("Delete", id="delete-theme", variant="error")
            
            yield ThemePreview(self.theme_manager, classes="preview-panel")
    
    def get_theme_options(self):
        """Get theme options for current category"""
        themes = self.theme_manager.get_themes_by_category(self.selected_category)
        return [(self.theme_manager.get_theme(name).name, name) for name in themes]
    
    async def on_select_changed(self, event):
        """Handle selection changes"""
        if event.select.id == "category-select":
            self.selected_category = event.value
            # Update theme select with new category
            theme_select = self.query_one("#theme-select", Select)
            theme_select.set_options(self.get_theme_options())
        elif event.select.id == "theme-select":
            self.selected_theme = event.value
            # Update preview
            preview = self.query_one(ThemePreview)
            preview.theme_name = event.value
    
    async def on_button_pressed(self, event):
        """Handle button presses"""
        if event.button.id == "apply-theme":
            self.theme_manager.apply_theme(self.selected_theme)
            self.notify(f"Applied theme: {self.selected_theme}")
        elif event.button.id == "duplicate-theme":
            # Create duplicate with "_copy" suffix
            base_theme = self.theme_manager.get_theme(self.selected_theme)
            if base_theme:
                new_name = f"{base_theme.name} Copy"
                self.theme_manager.create_custom_theme(new_name, self.selected_theme)
                self.notify(f"Created theme: {new_name}")
        elif event.button.id == "delete-theme":
            # Only allow deleting custom themes
            if self.selected_theme in self.theme_manager.custom_themes:
                del self.theme_manager.custom_themes[self.selected_theme]
                self.notify(f"Deleted theme: {self.selected_theme}")

class ColorPicker(Widget):
    """Simple color picker for theme editing"""
    
    red = reactive(128)
    green = reactive(128) 
    blue = reactive(128)
    
    def compose(self):
        """Compose color picker interface"""
        yield Static("🎨 COLOR PICKER")
        
        yield Static("Red:")
        yield Slider(0, 255, self.red, id="red-slider")
        
        yield Static("Green:")
        yield Slider(0, 255, self.green, id="green-slider")
        
        yield Static("Blue:")
        yield Slider(0, 255, self.blue, id="blue-slider")
        
        yield Static("Preview:", id="color-preview")
    
    def render_preview(self):
        """Render color preview"""
        color_style = Style(bgcolor=Color.from_rgb(self.red, self.green, self.blue))
        text = Text("████████", style=color_style)
        text.append(f" RGB({self.red}, {self.green}, {self.blue})")
        return text
    
    async def on_slider_changed(self, event):
        """Handle slider changes"""
        if event.slider.id == "red-slider":
            self.red = event.value
        elif event.slider.id == "green-slider":
            self.green = event.value
        elif event.slider.id == "blue-slider":
            self.blue = event.value
        
        # Update preview
        preview = self.query_one("#color-preview", Static)
        preview.update(self.render_preview())
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get current color as RGB tuple"""
        return (self.red, self.green, self.blue)
    
    def set_color(self, r: int, g: int, b: int):
        """Set color values"""
        self.red = max(0, min(255, r))
        self.green = max(0, min(255, g))
        self.blue = max(0, min(255, b))