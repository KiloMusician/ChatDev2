#!/usr/bin/env python3
"""
🚀 CoreLink Foundation Complete Demo
TouchDesigner-style ASCII/Unicode interface with all widgets and effects
Python 3.11 + Textual + 20 FPS animations + Braille micro-pixels
"""

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer
from textual.binding import Binding

# Import all widgets
from widgets.viewport import Viewport
from widgets.minimap import Minimap
from widgets.oscilloscope import Oscilloscope, DataMonitor
from widgets.color_themes import ThemeSelector, ThemeManager
from widgets.tile_renderer import TileRenderer

import math
import random
import time

class CoreLinkDemo(App):
    """Complete TouchDesigner-style interface demo"""
    
    TITLE = "CoreLink Foundation - TouchDesigner ASCII Interface"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "fullscreen", "Fullscreen"),
        Binding("1", "mode_overview", "Overview"),
        Binding("2", "mode_debug", "Debug"),
        Binding("3", "mode_analysis", "Analysis"),
        Binding("4", "mode_themes", "Themes"),
        Binding("5", "mode_nodes", "Nodes"),
    ]
    
    CSS = """
    .demo-grid {
        layout: grid;
        grid-size: 4 3;
        grid-gutter: 1;
        margin: 1;
    }
    
    .widget-panel {
        border: solid $accent;
        padding: 1;
        height: 100%;
    }
    
    .main-viewport {
        column-span: 2;
        row-span: 2;
    }
    
    .side-panel {
        column-span: 1;
        row-span: 1;
    }
    
    .bottom-panel {
        column-span: 4;
        row-span: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.mode = "overview"
        self.theme_manager = ThemeManager()
        
        # Initialize data for demos
        self.oscilloscope_data = []
        self.metrics_data = {}
        self.simulation_time = 0.0
        
    def compose(self) -> ComposeResult:
        """Create the complete interface"""
        yield Header(show_clock=True)
        
        # Main grid layout
        with Grid(classes="demo-grid"):
            # Main viewport (top-left, 2x2)
            yield Viewport(
                classes="widget-panel main-viewport",
                id="main-viewport"
            )
            
            # Minimap (top-right)
            yield Minimap(
                classes="widget-panel side-panel",
                id="minimap"
            )
            
            # Oscilloscope (middle-right)
            yield Oscilloscope(
                buffer_size=256,
                classes="widget-panel side-panel",
                id="oscilloscope"
            )
            
            # System metrics (bottom-left)
            yield DataMonitor(
                classes="widget-panel side-panel",
                id="data-monitor"
            )
            
            # Tile renderer (bottom-middle)
            yield TileRenderer(
                map_width=40, map_height=20,
                classes="widget-panel side-panel",
                id="tile-renderer"
            )
            
            # Theme selector (bottom-right)
            yield ThemeSelector(
                self.theme_manager,
                classes="widget-panel side-panel",
                id="theme-selector"
            )
        
        yield Footer()
    
    def on_mount(self):
        """Initialize the application"""
        # Start simulation timer
        self.set_interval(1/20, self.update_simulation)  # 20 FPS
        self.set_interval(1/4, self.update_slow_data)    # 4 FPS for some data
        
        # Initialize widgets with demo data
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for all widgets"""
        # Set up oscilloscope with sine wave
        oscilloscope = self.query_one("#oscilloscope", Oscilloscope)
        for i in range(100):
            sample = math.sin(i * 0.1) * 0.8
            oscilloscope.add_sample(sample)
        
        # Set up data monitor with system metrics
        monitor = self.query_one("#data-monitor", DataMonitor)
        monitor.add_metric("CPU", 45.2, "%")
        monitor.add_metric("Memory", 2048, "MB")
        monitor.add_metric("Network", 1.5, "Mbps")
        monitor.add_metric("Energy", 890.3, "W")
        monitor.add_metric("Temperature", 42.1, "°C")
    
    def update_simulation(self):
        """Update simulation at 20 FPS"""
        self.simulation_time += 1/20
        
        # Update oscilloscope with dynamic waveform
        oscilloscope = self.query_one("#oscilloscope", Oscilloscope)
        
        # Generate complex waveform
        freq1 = 2.0  # Primary frequency
        freq2 = 0.5  # Modulation frequency
        sample = (math.sin(self.simulation_time * freq1) * 
                 (0.5 + 0.3 * math.sin(self.simulation_time * freq2)) +
                 0.1 * random.uniform(-1, 1))  # Add noise
        
        oscilloscope.add_sample(sample)
        
        # Update viewport with animation
        viewport = self.query_one("#main-viewport", Viewport)
        viewport.tick = self.simulation_time
        
    def update_slow_data(self):
        """Update slower changing data"""
        monitor = self.query_one("#data-monitor", DataMonitor)
        
        # Simulate realistic system metrics
        base_time = time.time()
        
        # CPU with realistic variation
        cpu_usage = 30 + 20 * math.sin(base_time * 0.1) + 5 * random.random()
        monitor.add_metric("CPU", max(0, min(100, cpu_usage)), "%")
        
        # Memory with slow growth
        memory_base = 2000 + 100 * math.sin(base_time * 0.05)
        memory = memory_base + 50 * random.random()
        monitor.add_metric("Memory", memory, "MB")
        
        # Network with bursts
        network_base = 1.0 + 0.5 * math.sin(base_time * 0.2)
        if random.random() < 0.1:  # 10% chance of burst
            network_base += 2.0
        monitor.add_metric("Network", network_base, "Mbps")
        
        # Energy with realistic server patterns
        energy_base = 850 + 100 * math.sin(base_time * 0.08)
        monitor.add_metric("Energy", energy_base, "W")
        
        # Temperature correlates with energy
        temp_base = 35 + (energy_base - 850) * 0.1 + 2 * random.random()
        monitor.add_metric("Temperature", temp_base, "°C")
    
    def action_refresh(self):
        """Refresh all widgets"""
        for widget in self.query("Widget"):
            widget.refresh()
        
        self.notify("🔄 All widgets refreshed")
    
    def action_fullscreen(self):
        """Toggle fullscreen mode"""
        # This would toggle fullscreen if supported
        self.notify("🖥️ Fullscreen mode (simulated)")
    
    def action_mode_overview(self):
        """Switch to overview mode"""
        self.mode = "overview"
        self.notify("📊 Overview Mode")
    
    def action_mode_debug(self):
        """Switch to debug mode"""
        self.mode = "debug"
        self.notify("🐛 Debug Mode")
    
    def action_mode_analysis(self):
        """Switch to analysis mode"""
        self.mode = "analysis"
        self.notify("📈 Analysis Mode")
    
    def action_mode_themes(self):
        """Switch to themes mode"""
        self.mode = "themes"
        self.notify("🎨 Themes Mode")
    
    def action_mode_nodes(self):
        """Switch to nodes mode"""
        self.mode = "nodes"
        self.notify("🔗 Nodes Mode")

def main():
    """Run the complete demo"""
    app = CoreLinkDemo()
    app.run()

if __name__ == "__main__":
    main()