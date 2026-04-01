type Controls = {
  atmoDensity: number; // 0..1
  windX: number; windY: number; // -1..1
  ionization: number;  heat: number;  gravLens: number;
  threat: number; serenity: number; anomaly: number; timeScale: number;
};

interface VFXLayer {
  update(dt: number, c: Controls): void;
  draw(): void;
}

export class VFXDirector {
  private controls: Controls = {
    atmoDensity: 0.15, windX: 0.1, windY: 0.0,
    ionization: 0, heat: 0, gravLens: 0, threat: 0, serenity: 0.2, anomaly: 0, timeScale: 1
  };
  private layers: VFXLayer[] = [];
  private t = 0; 
  private raf = 0; 
  private last = performance.now();
  private isRunning = false;

  addLayer(layer: VFXLayer) {
    this.layers.push(layer);
  }

  setControls(next: Partial<Controls>) {
    // Critically damped smoothing for cinematic feel
    for (const k in next) {
      const key = k as keyof Controls;
      const current = this.controls[key];
      const target = next[key] as number;
      
      // Different damping for different control types
      const damping = key === 'threat' || key === 'ionization' ? 0.85 : 0.9;
      this.controls[key] = current * damping + target * (1 - damping);
    }
  }

  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    
    const loop = () => {
      if (!this.isRunning) return;
      
      const now = performance.now();
      const dt = Math.min(0.05, (now - this.last) / 1000);
      this.last = now;
      this.t += dt * this.controls.timeScale;

      // Expose controls globally for shader access
      (window as any).__ATMO_CTRLS = { ...this.controls, iTime: this.t };

      // Update and draw all layers
      for (const layer of this.layers) {
        layer.update(dt, this.controls);
      }
      
      for (const layer of this.layers) {
        layer.draw();
      }

      this.raf = requestAnimationFrame(loop);
    };
    
    this.raf = requestAnimationFrame(loop);
  }

  stop() {
    this.isRunning = false;
    if (this.raf) {
      cancelAnimationFrame(this.raf);
      this.raf = 0;
    }
  }

  getControls(): Controls {
    return { ...this.controls };
  }

  getTime(): number {
    return this.t;
  }
}