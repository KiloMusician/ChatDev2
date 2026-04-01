"""
📊 Oscilloscope and Data Visualization Widgets
Real-time waveform displays and sparklines
"""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
import math
from collections import deque
from typing import List

from ..palette import pick

class Oscilloscope(Widget):
    """Real-time oscilloscope display"""
    
    data_buffer = reactive([])
    sample_rate = reactive(44100)
    time_scale = reactive(1.0)
    amplitude_scale = reactive(1.0)
    trigger_level = reactive(0.0)
    
    def __init__(self, buffer_size=512, **kwargs):
        super().__init__(**kwargs)
        self.buffer_size = buffer_size
        self.buffer = deque(maxlen=buffer_size)
        self.trigger_pos = 0
        
    def add_sample(self, value: float):
        """Add a new sample to the oscilloscope"""
        self.buffer.append(value)
        
    def add_samples(self, values: List[float]):
        """Add multiple samples"""
        for value in values:
            self.buffer.append(value)
        self.refresh()
    
    def render(self):
        """Render oscilloscope display"""
        if not self.buffer:
            return Text("No signal", style=pick("text_dim"))
        
        width = max(40, self.size.width)
        height = max(8, self.size.height - 2)  # Leave room for labels
        
        # Create waveform display
        lines = ["📊 OSCILLOSCOPE", "─" * width]
        
        # Convert buffer to display coordinates
        samples = list(self.buffer)
        if len(samples) < width:
            # Pad with zeros
            samples.extend([0.0] * (width - len(samples)))
        else:
            # Downsample to fit width
            step = len(samples) / width
            samples = [samples[int(i * step)] for i in range(width)]
        
        # Create waveform canvas
        canvas = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Draw waveform
        center_y = height // 2
        for x, sample in enumerate(samples):
            # Scale sample to display range
            y_offset = int(sample * self.amplitude_scale * center_y)
            y = center_y - y_offset
            
            if 0 <= y < height:
                canvas[y][x] = "█"
            
            # Draw trigger level
            trigger_y = center_y - int(self.trigger_level * center_y)
            if 0 <= trigger_y < height and x % 4 == 0:
                if canvas[trigger_y][x] == ' ':
                    canvas[trigger_y][x] = "·"
        
        # Convert canvas to text
        for row in canvas:
            lines.append("".join(row))
        
        # Add statistics
        if samples:
            peak = max(abs(s) for s in samples)
            rms = math.sqrt(sum(s*s for s in samples) / len(samples))
            lines.append(f"Peak: {peak:.3f} RMS: {rms:.3f}")
        
        return Text("\n".join(lines), style=pick("accent_a"))

class Sparkline(Widget):
    """Compact sparkline display"""
    
    data = reactive([])
    max_points = reactive(60)
    auto_scale = reactive(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = deque(maxlen=self.max_points)
    
    def add_value(self, value: float):
        """Add a new value to the sparkline"""
        self.history.append(value)
        self.refresh()
    
    def render(self):
        """Render sparkline"""
        if not self.history:
            return Text("─" * 20, style=pick("text_dim"))
        
        values = list(self.history)
        width = min(len(values), self.size.width)
        
        if self.auto_scale and values:
            min_val = min(values)
            max_val = max(values)
            if max_val > min_val:
                # Normalize to 0-1 range
                values = [(v - min_val) / (max_val - min_val) for v in values]
            else:
                values = [0.5] * len(values)
        
        # Create sparkline using vertical characters
        spark_chars = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        spark_line = ""
        for i in range(width):
            if i < len(values):
                val = max(0, min(1, values[i]))
                char_index = int(val * (len(spark_chars) - 1))
                spark_line += spark_chars[char_index]
            else:
                spark_line += " "
        
        return Text(spark_line, style=pick("good"))

class SpectrumAnalyzer(Widget):
    """Frequency spectrum display"""
    
    fft_size = reactive(256)
    frequency_range = reactive((0, 22050))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.spectrum_data = []
    
    def set_spectrum(self, frequencies: List[float], magnitudes: List[float]):
        """Set frequency spectrum data"""
        self.spectrum_data = list(zip(frequencies, magnitudes))
        self.refresh()
    
    def render(self):
        """Render spectrum analyzer"""
        if not self.spectrum_data:
            return Text("🎵 No spectrum data", style=pick("text_dim"))
        
        width = max(30, self.size.width)
        height = max(6, self.size.height - 2)
        
        lines = ["🎵 SPECTRUM", "─" * width]
        
        # Create frequency bins
        bins = []
        if self.spectrum_data:
            min_freq, max_freq = self.frequency_range
            freq_step = (max_freq - min_freq) / width
            
            for i in range(width):
                bin_freq = min_freq + i * freq_step
                
                # Find magnitude for this frequency bin
                magnitude = 0.0
                for freq, mag in self.spectrum_data:
                    if abs(freq - bin_freq) < freq_step / 2:
                        magnitude = max(magnitude, mag)
                
                bins.append(magnitude)
        
        # Draw spectrum bars
        if bins:
            max_mag = max(bins) if bins else 1.0
            
            for y in range(height):
                line = ""
                for x in range(width):
                    if x < len(bins):
                        bar_height = (bins[x] / max_mag) * height
                        if (height - y - 1) < bar_height:
                            intensity = bar_height - (height - y - 1)
                            if intensity > 0.75:
                                char = "█"
                            elif intensity > 0.5:
                                char = "▓"
                            elif intensity > 0.25:
                                char = "▒"
                            else:
                                char = "░"
                        else:
                            char = " "
                    else:
                        char = " "
                    line += char
                lines.append(line)
        
        return Text("\n".join(lines), style=pick("accent_b"))

class WaveformDisplay(Widget):
    """Multi-channel waveform display"""
    
    channels = reactive(1)
    sample_window = reactive(1024)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel_data = {}
        
    def set_channel_data(self, channel: int, data: List[float]):
        """Set data for a specific channel"""
        self.channel_data[channel] = data[-self.sample_window:]
        self.refresh()
    
    def render(self):
        """Render multi-channel waveform"""
        if not self.channel_data:
            return Text("🌊 No waveform data", style=pick("text_dim"))
        
        width = max(40, self.size.width)
        height = max(8, self.size.height)
        
        lines = []
        
        # Calculate height per channel
        channels = sorted(self.channel_data.keys())
        if not channels:
            return Text("No channels", style=pick("text_dim"))
        
        channel_height = max(2, height // len(channels))
        
        for i, channel in enumerate(channels):
            data = self.channel_data[channel]
            
            lines.append(f"CH{channel}: {'─' * (width - 6)}")
            
            if data:
                # Downsample to fit width
                if len(data) > width:
                    step = len(data) / width
                    samples = [data[int(j * step)] for j in range(width)]
                else:
                    samples = data + [0.0] * (width - len(data))
                
                # Create channel waveform
                channel_canvas = [[' ' for _ in range(width)] for _ in range(channel_height - 1)]
                center_y = (channel_height - 1) // 2
                
                for x, sample in enumerate(samples):
                    y_offset = int(sample * center_y * 0.8)  # Scale down a bit
                    y = center_y - y_offset
                    
                    if 0 <= y < channel_height - 1:
                        channel_canvas[y][x] = "█"
                
                # Add channel waveform to lines
                for row in channel_canvas:
                    lines.append("".join(row))
            else:
                # No data for this channel
                for _ in range(channel_height - 1):
                    lines.append("─" * width)
        
        # Color channels differently
        colors = [pick("accent_a"), pick("accent_b"), pick("good"), pick("warn")]
        styled_text = Text()
        
        for i, line in enumerate(lines):
            channel_index = i // channel_height
            color = colors[channel_index % len(colors)] if channel_index < len(colors) else pick("text_bright")
            styled_text.append(line + "\n", style=color)
        
        return styled_text

class DataMonitor(Widget):
    """Real-time data monitoring with multiple metrics"""
    
    metrics = reactive({})
    update_rate = reactive(2.0)  # Hz
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metric_history = {}
        self.set_interval(1.0 / self.update_rate, self.update_display)
    
    def add_metric(self, name: str, value: float, unit: str = "", format_str: str = ".2f"):
        """Add or update a metric"""
        if name not in self.metric_history:
            self.metric_history[name] = deque(maxlen=20)
        
        self.metric_history[name].append(value)
        
        new_metrics = dict(self.metrics)
        new_metrics[name] = {
            "value": value,
            "unit": unit,
            "format": format_str,
            "history": list(self.metric_history[name])
        }
        self.metrics = new_metrics
    
    def update_display(self):
        """Update the display"""
        self.refresh()
    
    def render(self):
        """Render data monitor"""
        if not self.metrics:
            return Text("📊 No metrics", style=pick("text_dim"))
        
        lines = ["📊 DATA MONITOR", "═" * 20]
        
        for name, data in self.metrics.items():
            value = data["value"]
            unit = data["unit"]
            fmt = data["format"]
            history = data["history"]
            
            # Format value
            value_str = f"{value:{fmt}}"
            line = f"{name}: {value_str}{unit}"
            
            # Add trend indicator
            if len(history) >= 2:
                trend = history[-1] - history[-2]
                if trend > 0:
                    line += " ↗"
                elif trend < 0:
                    line += " ↘"
                else:
                    line += " →"
            
            lines.append(line)
            
            # Add mini sparkline
            if len(history) > 1:
                sparkline = ""
                if history:
                    min_val = min(history)
                    max_val = max(history)
                    if max_val > min_val:
                        normalized = [(v - min_val) / (max_val - min_val) for v in history]
                    else:
                        normalized = [0.5] * len(history)
                    
                    spark_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
                    for val in normalized[-10:]:  # Last 10 values
                        char_index = int(val * (len(spark_chars) - 1))
                        sparkline += spark_chars[char_index]
                
                lines.append(f"  {sparkline}")
        
        return Text("\n".join(lines), style=pick("accent_a"))