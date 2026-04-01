from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer
from widgets.viewport import Viewport
from widgets.menu import build_menu
from widgets.infobar import InfoBar

class NuAscii(App):
    """TouchDesigner-style TUI with your exact specifications"""
    
    CSS = """
    Screen { background: #000000; }
    .col { width: 1fr; }
    .menu { dock: right; width: 32; border: round #444444; }
    .hud  { dock: bottom; height: 1; }
    """
    
    BINDINGS = [
        ("q","quit","Quit"), 
        ("tab","toggle_menu","Menu"),
        ("space","pause","Pause"), 
        ("m","mode","Mode"),
        ("1","mode_ripple","Ripple"),
        ("2","mode_noise","Noise"),
        ("3","mode_radar","Radar"),
        ("4","mode_matrix","Matrix"),
        ("5","mode_stars","Stars")
    ]

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
        modes = ["ripple", "noise", "radar", "matrix", "stars"]
        current = self.viewport.mode
        current_idx = modes.index(current) if current in modes else 0
        next_idx = (current_idx + 1) % len(modes)
        self.viewport.mode = modes[next_idx]
    
    def action_mode_ripple(self): self.viewport.mode = "ripple"
    def action_mode_noise(self): self.viewport.mode = "noise"
    def action_mode_radar(self): self.viewport.mode = "radar"
    def action_mode_matrix(self): self.viewport.mode = "matrix"
    def action_mode_stars(self): self.viewport.mode = "stars"

if __name__ == "__main__":
    NuAscii().run()