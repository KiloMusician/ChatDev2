from textual.widgets import TabbedContent, TabPane, Static, Button, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive

def build_menu():
    """Build simple menu for NuAscii app"""
    return TabbedContent(
        TabPane(Static("Inventory / 🧰 / ⚙️\n\nResources:\n• Energy: 890 W\n• Matter: 2.4k kg\n• Rare: 23 units"), 
                title="Inventory", id="inventory"),
        TabPane(Static("Build / 🏗️ / ♜\n\nAvailable:\n• Shelter\n• Workshop\n• Defense\n• Research"), 
                title="Build", id="build"),
        TabPane(Static("Research / 🔬\n\nActive:\n• Advanced AI\n• Energy Tech\n• Materials"), 
                title="Research", id="research"),
        TabPane(Static("Quests / 📜\n\nCurrent:\n• Establish base\n• Gather resources\n• Contact home"), 
                title="Quests", id="quests"),
        TabPane(Static("Settings / ⚙\n\nGraphics:\n• Quality: High\n• Effects: On\n• Sound: On"), 
                title="Settings", id="settings"),
    )

class GameMenu(TabbedContent):
    """Main game menu with tabs for different game systems"""
    
    def __init__(self):
        super().__init__(
            TabPane(InventoryTab(), title="🧰 Inventory", id="inventory"),
            TabPane(BuildTab(), title="🏗️ Build", id="build"),
            TabPane(ResearchTab(), title="🔬 Research", id="research"),
            TabPane(QuestsTab(), title="📜 Quests", id="quests"),
            TabPane(SettingsTab(), title="⚙ Settings", id="settings"),
        )

class InventoryTab(Container):
    """Inventory management tab"""
    
    inventory_items = reactive([])
    
    def compose(self):
        yield Label("🧰 INVENTORY", classes="tab-header")
        yield Container(
            Label("Items: 0/100"),
            Label("Resources:"),
            Label("  Food: 50"),
            Label("  Water: 40"), 
            Label("  Materials: 100"),
            Label("  Energy: 150"),
            classes="inventory-list"
        )
    
    def on_mount(self):
        self.set_interval(2, self.update_inventory)
    
    def update_inventory(self):
        """Update inventory display"""
        # Here we would fetch real game data
        pass

class BuildTab(Container):
    """Building construction tab"""
    
    def compose(self):
        yield Label("🏗️ BUILD MENU", classes="tab-header")
        yield Vertical(
            Label("Available Structures:"),
            Button("Shelter (25 materials)", id="build-shelter", classes="build-button"),
            Button("Workshop (50 materials)", id="build-workshop", classes="build-button"),
            Button("Greenhouse (40 materials)", id="build-greenhouse", classes="build-button"),
            Button("Laboratory (80 materials)", id="build-lab", classes="build-button"),
            Label("\nDefensive Structures:"),
            Button("Basic Turret (25 materials)", id="build-turret", classes="build-button"),
            Button("Laser Cannon (50 materials)", id="build-laser", classes="build-button"),
            Button("Shield Generator (60 materials)", id="build-shield", classes="build-button"),
        )
    
    async def on_button_pressed(self, event):
        """Handle build button presses"""
        button_id = event.button.id
        if button_id.startswith("build-"):
            structure = button_id.replace("build-", "")
            # Here we would trigger the build action
            self.notify(f"Building {structure}...")

class ResearchTab(Container):
    """Research and technology tab"""
    
    research_points = reactive(0)
    
    def compose(self):
        yield Label("🔬 RESEARCH", classes="tab-header")
        yield Vertical(
            Label(f"Research Points: {self.research_points}"),
            Label("\nAvailable Research:"),
            Button("Advanced Materials (10 RP)", id="research-materials", classes="research-button"),
            Button("Energy Efficiency (15 RP)", id="research-energy", classes="research-button"),
            Button("Automation Systems (25 RP)", id="research-automation", classes="research-button"),
            Button("Xenobiology (30 RP)", id="research-xeno", classes="research-button"),
            Label("\nCompleted Research:"),
            Label("  ✅ Basic Construction"),
            Label("  ✅ Food Production"),
        )
    
    async def on_button_pressed(self, event):
        """Handle research button presses"""
        button_id = event.button.id
        if button_id.startswith("research-"):
            tech = button_id.replace("research-", "")
            self.notify(f"Researching {tech}...")

class QuestsTab(Container):
    """Quest and mission tracking tab"""
    
    active_quests = reactive([])
    
    def compose(self):
        yield Label("📜 QUESTS", classes="tab-header")
        yield Vertical(
            Label("Active Quests:"),
            Label("  🎯 Investigate the Crystal Cave"),
            Label("     Explore coordinates (15, 8)"),
            Label("     Reward: 10 XP, Ancient Artifact"),
            Label(""),
            Label("  🏗️ Expand the Colony"),
            Label("     Build 3 new structures"),
            Label("     Progress: 1/3"),
            Label("     Reward: 20 XP, 50 Materials"),
            Label(""),
            Label("Completed Quests:"),
            Label("  ✅ Establish Base Camp"),
            Label("  ✅ First Contact Protocol"),
            Label("  ✅ Survive 7 Days"),
        )

class SettingsTab(Container):
    """Game settings and configuration"""
    
    def compose(self):
        yield Label("⚙ SETTINGS", classes="tab-header")
        yield Vertical(
            Label("Display Settings:"),
            Button("Theme: Neon", id="toggle-theme", classes="setting-button"),
            Button("Effects: High", id="toggle-effects", classes="setting-button"),
            Button("Animation: On", id="toggle-animation", classes="setting-button"),
            Label(""),
            Label("Game Settings:"),
            Button("Auto-Save: On", id="toggle-autosave", classes="setting-button"),
            Button("Difficulty: Normal", id="toggle-difficulty", classes="setting-button"),
            Button("Speed: 1x", id="toggle-speed", classes="setting-button"),
            Label(""),
            Label("Audio Settings:"),
            Button("SFX: On", id="toggle-sfx", classes="setting-button"),
            Button("Music: On", id="toggle-music", classes="setting-button"),
            Label(""),
            Button("Reset Game", id="reset-game", classes="danger-button"),
        )
    
    async def on_button_pressed(self, event):
        """Handle settings button presses"""
        button_id = event.button.id
        
        if button_id == "toggle-theme":
            self.notify("Theme cycled")
        elif button_id == "toggle-effects":
            self.notify("Effects quality changed")
        elif button_id == "toggle-animation":
            self.notify("Animation toggled")
        elif button_id == "reset-game":
            self.notify("Game reset confirmed")
        else:
            self.notify(f"Setting changed: {button_id}")

class QuickMenu(Container):
    """Quick access menu for common actions"""
    
    def compose(self):
        yield Horizontal(
            Button("⏸", id="pause", classes="quick-button"),
            Button("💾", id="save", classes="quick-button"),
            Button("📊", id="stats", classes="quick-button"),
            Button("❓", id="help", classes="quick-button"),
        )
    
    async def on_button_pressed(self, event):
        """Handle quick menu button presses"""
        button_id = event.button.id
        
        if button_id == "pause":
            self.notify("Game paused")
        elif button_id == "save":
            self.notify("Game saved")
        elif button_id == "stats":
            self.notify("Stats panel opened")
        elif button_id == "help":
            self.notify("Help system activated")