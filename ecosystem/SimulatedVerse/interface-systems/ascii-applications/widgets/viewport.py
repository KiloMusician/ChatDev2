from textual.widget import Widget
from textual.reactive import reactive
from textual import events
from .. import effects

class Viewport(Widget):
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
        from rich.text import Text
        return Text(art, style="bold color(50)")

    async def on_key(self, event: events.Key):
        if event.key == "m":
            self.mode = "map" if self.mode!="map" else "ripple"
        elif event.key == "n":
            self.mode = "noise"
        self.refresh()