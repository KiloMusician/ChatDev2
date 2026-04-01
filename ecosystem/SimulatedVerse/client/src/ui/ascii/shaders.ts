// ui/ascii/shaders.ts
import type { IAsciiShader, ShaderFrameArgs, ShaderInit } from './engine';

function rampIndexFor(val: number, ramp: string) {
  const i = Math.max(0, Math.min(ramp.length - 1, Math.floor(val * ramp.length)));
  return i;
}

const DEFAULT_RAMP = ' .:-=+*#%@';

export class Starfield implements IAsciiShader {
  name = 'Starfield';
  private ramp = DEFAULT_RAMP;
  private seed = 1;
  private speed = 0.5;
  private density = 120;
  init(i: ShaderInit = {}) {
    this.ramp = i.charRamp || DEFAULT_RAMP;
    this.seed = i.seed ?? 1;
    this.speed = i.speed ?? 0.5;
    this.density = i.density ?? 120;
  }
  frame({ t, cols, rows, pointer, state, rand }: ShaderFrameArgs): string[] {
    const lines: string[] = [];
    const twinkle = (Math.sin(t * 2.1) + 1) * 0.5;
    const sceneBoost = (state.sceneEnergy ?? 0) * 0.5;
    const speed = this.speed + sceneBoost + Math.abs(pointer.x) * 0.2;
    const cx = cols * 0.5, cy = rows * 0.5;

    for (let r = 0; r < rows; r++) {
      let line = '';
      for (let c = 0; c < cols; c++) {
        // Polar-ish warp for depth
        const dx = (c - cx) / cols;
        const dy = (r - cy) / rows;
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.0001;
        const flare = Math.max(0, 1 - dist * 3.0);
        // Noise-like sparkle
        const sparkle = (Math.sin((c * 12.9898 + r * 78.233 + this.seed * 43758.5453) * 0.5) * 43758.5453) % 1;
        let v = flare * 0.7 + twinkle * 0.15 + (sparkle < 0.02 ? 1.0 : 0.0);
        // radial flow
        v += Math.sin((t * speed + dist * 12) - pointer.y * 2) * 0.05;
        v = Math.max(0, Math.min(1, v));
        line += this.ramp[rampIndexFor(v, this.ramp)];
      }
      lines.push(line);
    }
    return lines;
  }
}

export class WaveTunnel implements IAsciiShader {
  name = 'WaveTunnel';
  private ramp = DEFAULT_RAMP;
  private speed = 1.2;
  init(i: ShaderInit = {}) {
    this.ramp = i.charRamp || DEFAULT_RAMP;
    this.speed = i.speed ?? 1.2;
  }
  frame({ t, dt, cols, rows, pointer, state }: ShaderFrameArgs): string[] {
    const lines: string[] = [];
    const freq = 0.12 + (state.tunnelFreq ?? 0) * 0.1;
    const amp = 0.85 + Math.abs(pointer.y) * 0.25;
    for (let r = 0; r < rows; r++) {
      let line = '';
      for (let c = 0; c < cols; c++) {
        const u = c / cols, v = r / rows;
        const w = Math.sin((u + t * this.speed) * 2 * Math.PI * freq) * amp
                + Math.cos((v - t * this.speed) * 2 * Math.PI * freq) * amp * 0.6;
        const val = (w * 0.5 + 0.5);
        line += this.ramp[rampIndexFor(val, this.ramp)];
      }
      lines.push(line);
    }
    return lines;
  }
}

export class LatticeGrid implements IAsciiShader {
  name = 'Lattice';
  private ramp = ' ░▒▓█';
  frame({ t, cols, rows, pointer, state }: ShaderFrameArgs): string[] {
    const lines: string[] = [];
    const cell = Math.max(2, Math.floor( (state.latticeCell ?? 6) + (pointer.x * 2) ));
    for (let r = 0; r < rows; r++) {
      let line = '';
      for (let c = 0; c < cols; c++) {
        const on = (c % cell === 0) || (r % cell === 0);
        const flare = on ? (Math.sin(t * 6 + c * 0.2 + r * 0.2) * 0.5 + 0.5) : 0;
        const idx = on ? rampIndexFor(flare, this.ramp) : 0;
        line += this.ramp[idx];
      }
      lines.push(line);
    }
    return lines;
  }
}

export class ParticleBurst implements IAsciiShader {
  name = 'Particles';
  private ramp = " .'`:,-~;!*oO0@#";
  private particles: {x:number;y:number;vx:number;vy:number;life:number}[] = [];
  init(i: ShaderInit = {}) {
    // seeded burst in center
    this.particles = [];
    const count = i.density ? Math.max(50, Math.min(500, i.density)) : 180;
    for (let k=0;k<count;k++){
      const a = (k / count) * Math.PI * 2;
      const s = (Math.random()*0.8+0.2);
      this.particles.push({x:0.5,y:0.5,vx:Math.cos(a)*s*0.06,vy:Math.sin(a)*s*0.03,life:1});
    }
  }
  frame({ t, dt, cols, rows, pointer, state }: ShaderFrameArgs): string[] {
    const grid = Array.from({length: rows}, ()=>' '.repeat(cols).split(''));
    for (const p of this.particles) {
      p.x += p.vx + pointer.x * 0.0009;
      p.y += p.vy + pointer.y * 0.0009;
      p.vy += 0.0004; // gravity
      p.life -= 0.003;
      if (p.life <= 0 || p.x<0 || p.x>1 || p.y<0 || p.y>1) { p.x=0.5;p.y=0.5;p.vx*=-0.7;p.vy*=-0.9;p.life=1;}
      const cx = Math.floor(p.x * cols);
      const cy = Math.floor(p.y * rows);
      if (cy>=0 && cy<rows && cx>=0 && cx<cols){
        const idx = Math.min(this.ramp.length-1, Math.floor((1-p.life)*this.ramp.length));
        const row = grid[cy];
        if (row) {
          row[cx] = this.ramp[idx] ?? ' ';
        }
      }
    }
    return grid.map(a => a.join(''));
  }
}
