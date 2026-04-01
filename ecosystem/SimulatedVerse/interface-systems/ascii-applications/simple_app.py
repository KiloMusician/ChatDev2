"""
🌟 NuSyQ Simple App - Your Exact Specifications
TouchDesigner-style TUI following your exact code structure
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static, TabbedContent, TabPane
from textual.reactive import reactive
from textual import events
from rich.text import Text

from . import effects
from .palette import pick

class Viewport(Static):
    tick = reactive(0.0)
    mode = reactive("ripple")  # ripple|noise|map

    def on_mount(self):
        self.set_interval(1/20, self.animate)  # 20 FPS

    def animate(self):
        self.tick += 0.05
        self.refresh()

    def render(self):
        w,h = self.size.width*2, self.size.height*4  # braille density
        if self.mode == "ripple":
            art = effects.sine_ripple(w,h,self.tick)
        elif self.mode == "noise":
            art = effects.noise_flow(w,h,self.tick)
        else:
            art = "map pending…"
        return Text(art, style="bold color(50)")

    async def on_key(self, event: events.Key):
        if event.key == "m":
            self.mode = "map" if self.mode!="map" else "ripple"
        elif event.key == "n":
            self.mode = "noise"
        self.refresh()

def build_menu():
    return TabbedContent(
        TabPane(Static("Inventory / 🧰 / ⚙️"), title="Inventory", id="inventory"),
        TabPane(Static("Build / 🏗️ / ♜"), title="Build", id="build"),
        TabPane(Static("Research / 🔬"), title="Research", id="research"),
        TabPane(Static("Quests / 📜"), title="Quests", id="quests"),
        TabPane(Static("Settings / ⚙"), title="Settings", id="settings"),
    )

class InfoBar(Static):
    def render(self):
        t = Text(" ⌘ NuSyQ HUD — [m]ode [space]pause [tab]menu [F1]help ")
        t.stylize(pick("accent_b"))
        return t

class NuAscii(App):
    CSS = """
    Screen { background: #000000; }
    .col { width: 1fr; }
    .menu { dock: right; width: 32; border: round #444444; }
    .hud  { dock: bottom; height: 1; }
    """
    BINDINGS = [("q","quit","Quit"), ("tab","toggle_menu","Menu"),
                ("space","pause","Pause"), ("m","mode","Mode")]

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                self.viewport = Viewport(classes="col")
                yield self.viewport
                self.menu = build_menu()
                self.menu.visible = False
                self.menu.classes="menu"
                yield self.menu
            yield InfoBar(classes="hud")
            yield Footer()

    def action_toggle_menu(self):
        self.menu.visible = not self.menu.visible

    def action_mode(self): 
        self.viewport.mode = "noise" if self.viewport.mode=="ripple" else "ripple"

if __name__ == "__main__":
    NuAscii().run()