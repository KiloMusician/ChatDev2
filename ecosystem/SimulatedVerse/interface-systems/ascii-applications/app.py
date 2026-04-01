from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Footer, Header
from textual import events
from textual.reactive import reactive

from .widgets.viewport import GameViewport
from .widgets.menu import GameMenu, QuickMenu
from .widgets.infobar import InfoBar, StatusBar, NotificationArea
from .widgets.minimap import Minimap, RadarMap
from .palette import THEMES

class NuSyQApp(App):
    """Main NuSyQ ASCII interface application"""
    
    CSS = """
    Screen {
        background: black;
    }
    
    .viewport-container {
        width: 1fr;
        height: 1fr;
        border: round white;
        margin: 1;
    }
    
    .sidebar {
        dock: right;
        width: 32;
        border: round white;
    }
    
    .bottom-panel {
        dock: bottom;
        height: 6;
        border: round white;
    }
    
    .infobar {
        dock: bottom;
        height: 1;
    }
    
    .menu-container {
        height: 1fr;
        margin: 1;
    }
    
    .minimap-container {
        height: 12;
        margin: 1;
        border: round white;
    }
    
    .quick-menu {
        height: 3;
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "toggle_sidebar", "Menu"),
        ("space", "toggle_pause", "Pause"),
        ("m", "cycle_viewport_mode", "Mode"),
        ("F1", "show_help", "Help"),
        ("F2", "toggle_minimap", "Minimap"),
        ("F3", "cycle_theme", "Theme"),
        ("ctrl+s", "save_game", "Save"),
        ("ctrl+l", "load_game", "Load"),
        ("1", "set_game_mode_exploration", "Exploration"),
        ("2", "set_game_mode_colony", "Colony"),
        ("3", "set_game_mode_defense", "Defense"),
        ("4", "set_game_mode_idle", "Idle"),
    ]
    
    # Reactive state
    sidebar_visible = reactive(True)
    current_game_mode = reactive("exploration")
    paused = reactive(False)
    current_theme = reactive("neon")
    
    def compose(self) -> ComposeResult:
        """Build the app layout"""
        yield Header()
        
        with Container(classes="main-container"):
            with Horizontal():
                # Main viewport area
                with Vertical(classes="viewport-container"):
                    self.viewport = GameViewport()
                    yield self.viewport
                    
                    # Bottom panel with notifications and status
                    with Container(classes="bottom-panel"):
                        with Horizontal():
                            yield StatusBar()
                            yield NotificationArea()
                
                # Right sidebar (toggleable)
                with Vertical(classes="sidebar"):
                    # Minimap area
                    with Container(classes="minimap-container"):
                        self.minimap = Minimap()
                        yield self.minimap
                        self.radar = RadarMap()
                        yield self.radar
                    
                    # Quick actions
                    with Container(classes="quick-menu"):
                        yield QuickMenu()
                    
                    # Main menu
                    with Container(classes="menu-container"):
                        self.menu = GameMenu()
                        yield self.menu
            
            # Info bar at bottom
            yield InfoBar(classes="infobar")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize the app"""
        self.title = "NuSyQ - Neural Unity Quantum System"
        self.sub_title = "Autonomous AI Development Ecosystem"
        
        # Set up periodic updates
        self.set_interval(1.0, self.update_game_state)
        
        # Initial notifications
        self.add_notification("Welcome to NuSyQ!", "success")
        self.add_notification("Press F1 for help", "info")
    
    def update_game_state(self):
        """Periodic game state updates"""
        # This would integrate with the actual game engines
        # For now, just update some demo data
        pass
    
    def add_notification(self, message, type="info"):
        """Add a notification to the notification area"""
        notification_area = self.query_one(NotificationArea)
        notification_area.add_notification(message, type)
    
    # Action handlers
    def action_toggle_sidebar(self):
        """Toggle sidebar visibility"""
        sidebar = self.query_one(".sidebar")
        sidebar.visible = not sidebar.visible
        self.sidebar_visible = sidebar.visible
        self.add_notification(f"Sidebar {'shown' if sidebar.visible else 'hidden'}")
    
    def action_toggle_pause(self):
        """Toggle game pause state"""
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        self.add_notification(f"Game {status}", "info")
    
    def action_cycle_viewport_mode(self):
        """Cycle through viewport modes"""
        modes = ["ripple", "noise", "energy", "radar", "matrix", "stars", "perlin", "cellular"]
        current_mode = self.viewport.mode
        current_index = modes.index(current_mode) if current_mode in modes else 0
        new_mode = modes[(current_index + 1) % len(modes)]
        self.viewport.mode = new_mode
        self.add_notification(f"Viewport mode: {new_mode}")
    
    def action_show_help(self):
        """Show help information"""
        self.add_notification("Help displayed", "info")
        # In a full implementation, this would show a modal dialog
    
    def action_toggle_minimap(self):
        """Toggle between minimap and radar"""
        minimap = self.query_one(Minimap)
        radar = self.query_one(RadarMap)
        
        if minimap.visible:
            minimap.visible = False
            radar.visible = True
            self.add_notification("Switched to radar view")
        else:
            minimap.visible = True
            radar.visible = False
            self.add_notification("Switched to minimap view")
    
    def action_cycle_theme(self):
        """Cycle through visual themes"""
        themes = list(THEMES.keys())
        current_index = themes.index(self.current_theme) if self.current_theme in themes else 0
        new_theme = themes[(current_index + 1) % len(themes)]
        self.current_theme = new_theme
        # In a full implementation, this would update the global theme
        self.add_notification(f"Theme: {new_theme}")
    
    def action_save_game(self):
        """Save game state"""
        self.add_notification("Game saved", "success")
        # Here we would trigger the actual save
    
    def action_load_game(self):
        """Load game state"""
        self.add_notification("Game loaded", "success")
        # Here we would trigger the actual load
    
    # Game mode actions
    def action_set_game_mode_exploration(self):
        """Switch to exploration mode"""
        self.current_game_mode = "exploration"
        self.viewport.game_mode = "exploration"
        self.add_notification("Exploration mode activated")
    
    def action_set_game_mode_colony(self):
        """Switch to colony management mode"""
        self.current_game_mode = "colony"
        self.viewport.game_mode = "colony"
        self.add_notification("Colony mode activated")
    
    def action_set_game_mode_defense(self):
        """Switch to defense mode"""
        self.current_game_mode = "defense"
        self.viewport.game_mode = "defense"
        self.add_notification("Defense mode activated")
    
    def action_set_game_mode_idle(self):
        """Switch to idle progression mode"""
        self.current_game_mode = "idle"
        self.viewport.game_mode = "idle"
        self.add_notification("Idle mode activated")
    
    async def on_key(self, event: events.Key):
        """Handle additional key events"""
        # Energy level adjustment
        if event.key == "plus":
            self.viewport.energy_level = min(2.0, self.viewport.energy_level + 0.1)
            self.add_notification(f"Energy: {self.viewport.energy_level:.1f}")
        elif event.key == "minus":
            self.viewport.energy_level = max(0.1, self.viewport.energy_level - 0.1)
            self.add_notification(f"Energy: {self.viewport.energy_level:.1f}")

def main():
    """Run the NuSyQ ASCII app"""
    app = NuSyQApp()
    app.run()

if __name__ == "__main__":
    main()