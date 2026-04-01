interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  type: 'dust' | 'spark' | 'ember';
}

export class Particles2DLayer {
  private ctx: CanvasRenderingContext2D;
  private particles: Particle[] = [];
  private maxParticles: number;

  constructor(private canvas: HTMLCanvasElement, count = 200) {
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("2D canvas context not available");
    }
    this.ctx = ctx;
    this.maxParticles = count;
    
    // Initialize particles
    for (let i = 0; i < count; i++) {
      this.spawnParticle();
    }
  }

  private spawnParticle() {
    const w = this.canvas.width || window.innerWidth;
    const h = this.canvas.height || window.innerHeight;
    
    const types: Particle['type'][] = ['dust', 'spark', 'ember'];
    const type = types[Math.floor(Math.random() * types.length)];
    
    this.particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 20,
      vy: (Math.random() - 0.5) * 10,
      life: Math.random() * 2 + 1,
      maxLife: 2 + Math.random() * 3,
      size: type === 'dust' ? 0.5 + Math.random() * 1 : 1 + Math.random() * 2,
      type
    });
  }

  update(dt: number, controls: any) {
    // Update canvas size
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    this.canvas.width = w;
    this.canvas.height = h;
    
    const windX = (controls.windX || 0) * 40;
    const windY = (controls.windY || 0) * 10;
    const heat = controls.heat || 0;
    const threat = controls.threat || 0;
    const ionization = controls.ionization || 0;
    
    // Update existing particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      
      // Apply forces
      p.vx += windX * dt * 0.5;
      p.vy += windY * dt * 0.5;
      
      // Heat makes particles rise
      if (heat > 0.1) {
        p.vy -= 30 * dt * heat;
      }
      
      // Ionization adds erratic movement
      if (ionization > 0.1) {
        p.vx += (Math.random() - 0.5) * 50 * dt * ionization;
        p.vy += (Math.random() - 0.5) * 30 * dt * ionization;
      }
      
      // Apply gravity
      p.vy += 20 * dt;
      
      // Update position
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      
      // Update life
      p.life -= dt;
      
      // Remove dead or out-of-bounds particles
      if (p.life <= 0 || p.x < -10 || p.x > w + 10 || p.y < -10 || p.y > h + 10) {
        this.particles.splice(i, 1);
      }
    }
    
    // Spawn new particles to maintain count
    const spawnRate = 1 + threat * 2 + ionization * 3;
    const particlesToSpawn = Math.floor(spawnRate * dt);
    
    for (let i = 0; i < particlesToSpawn && this.particles.length < this.maxParticles; i++) {
      this.spawnParticle();
    }
  }

  draw() {
    const ctx = this.ctx;
    
    // Clear canvas
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Set up for additive blending
    ctx.globalCompositeOperation = "lighter";
    
    for (const p of this.particles) {
      const alpha = Math.max(0, p.life / p.maxLife);
      
      // Different rendering for different particle types
      switch (p.type) {
        case 'dust':
          ctx.globalAlpha = 0.1 * alpha;
          ctx.fillStyle = "#8B7355";
          break;
          
        case 'spark':
          ctx.globalAlpha = 0.3 * alpha;
          ctx.fillStyle = "#FFD700";
          break;
          
        case 'ember':
          ctx.globalAlpha = 0.2 * alpha;
          ctx.fillStyle = "#FF6B35";
          break;
      }
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
      
      // Add glow for sparks and embers
      if (p.type !== 'dust') {
        ctx.globalAlpha = 0.05 * alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    
    // Reset blend mode and alpha
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
  }

  dispose() {
    this.particles = [];
  }
}