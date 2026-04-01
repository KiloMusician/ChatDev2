import math
import numpy as np
from .primitives import canvas_to_braille

def sine_ripple(w,h, t, freq=0.12, speed=0.9, cx=None, cy=None):
    if cx is None: cx = w/2; cy = h/2
    def sample(x,y):
        dx,dy = x-cx, y-cy
        r = (dx*dx+dy*dy)**0.5
        val = 0.5 + 0.5*math.sin(freq*r - speed*t)
        return val
    return canvas_to_braille(w,h, sample)

def noise_flow(w,h,t):
    rng = np.random.default_rng(int(t*30))
    grid = rng.random((h,w))
    return canvas_to_braille(w,h, lambda x,y: grid[y,x])

def heatmap_from_field(field, threshold=0.5):
    h,w = field.shape
    return canvas_to_braille(w,h, lambda x,y: float(field[y,x] > threshold))

def perlin_noise_2d(w, h, t, scale=0.1, octaves=3):
    """Generate Perlin-like noise pattern"""
    def noise(x, y):
        # Simple noise function using sin/cos
        n = math.sin(x * scale) * math.cos(y * scale)
        n += 0.5 * math.sin(x * scale * 2 + t) * math.cos(y * scale * 2)
        n += 0.25 * math.sin(x * scale * 4) * math.cos(y * scale * 4 + t * 0.5)
        return (n + 1) / 2  # Normalize to 0-1
    
    return canvas_to_braille(w, h, noise)

def energy_field(w, h, t, energy_level=1.0):
    """Create energy field effect based on power level"""
    def sample(x, y):
        # Create interference patterns
        phase1 = math.sin(x * 0.3 + t * 2) * math.cos(y * 0.2 + t * 1.5)
        phase2 = math.sin(x * 0.1 + t) * math.sin(y * 0.15 + t * 0.8)
        
        interference = (phase1 + phase2) * energy_level
        return max(0, min(1, (interference + 1) / 2))
    
    return canvas_to_braille(w, h, sample)

def heatmap_from_field(field, threshold=0.5):
    """Convert a 2D field to braille heatmap"""
    h, w = field.shape
    return canvas_to_braille(w, h, lambda x, y: float(field[y, x] > threshold))

def particle_system(w, h, t, particles):
    """Render a particle system"""
    # Create canvas
    canvas = [[0.0 for _ in range(w)] for _ in range(h)]
    
    for particle in particles:
        x = int(particle.get('x', 0)) 
        y = int(particle.get('y', 0))
        size = particle.get('size', 1)
        intensity = particle.get('intensity', 1.0)
        
        # Draw particle with falloff
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                px, py = x + dx, y + dy
                if 0 <= px < w and 0 <= py < h:
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance <= size:
                        falloff = 1.0 - (distance / size)
                        canvas[py][px] = max(canvas[py][px], intensity * falloff)
    
    return canvas_to_braille(w, h, lambda x, y: canvas[y][x])

def radar_sweep(w, h, t, sweep_speed=1.0):
    """Create radar sweep effect"""
    cx, cy = w // 2, h // 2
    sweep_angle = (t * sweep_speed) % (2 * math.pi)
    
    def sample(x, y):
        dx, dy = x - cx, y - cy
        angle = math.atan2(dy, dx)
        
        # Normalize angle difference
        diff = abs(angle - sweep_angle)
        if diff > math.pi:
            diff = 2 * math.pi - diff
        
        # Create sweep beam
        if diff < 0.3:  # Beam width
            intensity = 1.0 - (diff / 0.3)
            return intensity * 0.8
        
        # Fade trail
        trail_diff = (angle - sweep_angle) % (2 * math.pi)
        if trail_diff < math.pi:
            return max(0, 0.3 - trail_diff / math.pi * 0.3)
        
        return 0
    
    return canvas_to_braille(w, h, sample)

def matrix_rain(w, h, t, density=0.1):
    """Create Matrix-style digital rain effect"""
    rng = np.random.default_rng(int(t * 10))
    
    def sample(x, y):
        # Create falling streams
        stream_x = x % 3  # Stream spacing
        if stream_x != 0:
            return 0
        
        # Each column has its own phase
        phase = (t * 3 + x * 0.5) % h
        
        # Bright head of stream
        if abs(y - phase) < 2:
            return 1.0
        
        # Fading tail
        if y > phase and y < phase + 8:
            fade = 1.0 - ((y - phase) / 8)
            return fade * 0.6
        
        # Random sparkles
        if rng.random() < density * 0.1:
            return 0.3
        
        return 0
    
    return canvas_to_braille(w, h, sample)

def star_field(w, h, t, star_count=50):
    """Create animated star field"""
    rng = np.random.default_rng(42)  # Fixed seed for consistent stars
    stars = [(rng.integers(0, w), rng.integers(0, h), rng.random()) for _ in range(star_count)]
    
    def sample(x, y):
        for sx, sy, phase in stars:
            if abs(x - sx) <= 1 and abs(y - sy) <= 1:
                # Twinkling effect
                twinkle = 0.5 + 0.5 * math.sin(t * 2 + phase * 10)
                return twinkle
        return 0
    
    return canvas_to_braille(w, h, sample)

def oscilloscope(data, w, h, scale=1.0):
    """Create oscilloscope-style waveform display"""
    if not data:
        return canvas_to_braille(w, h, lambda x, y: 0)
    
    def sample(x, y):
        if x >= len(data):
            return 0
        
        # Map data to y coordinate
        value = data[x] * scale
        target_y = h // 2 + int(value * h // 4)
        
        # Draw waveform line
        if abs(y - target_y) <= 1:
            return 1.0
        return 0
    
    return canvas_to_braille(w, h, sample)

def cellular_automata(w, h, t, rule=30):
    """Generate cellular automata patterns"""
    # Initialize with random seed based on time
    rng = np.random.default_rng(int(t))
    current_line = rng.integers(0, 2, size=w)
    
    # Apply rule for several generations
    generations = h
    pattern = []
    
    for gen in range(generations):
        pattern.append(current_line.copy())
        new_line = np.zeros_like(current_line)
        
        for i in range(w):
            left = current_line[(i - 1) % w]
            center = current_line[i]
            right = current_line[(i + 1) % w]
            
            # Apply rule (simplified)
            neighborhood = left * 4 + center * 2 + right
            new_line[i] = (rule >> neighborhood) & 1
        
        current_line = new_line
    
    def sample(x, y):
        if y < len(pattern) and x < len(pattern[y]):
            return float(pattern[y][x])
        return 0
    
    return canvas_to_braille(w, h, sample)