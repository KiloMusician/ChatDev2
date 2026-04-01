// ui/ascii/engine.ts
// Lightweight ASCII shader engine (DOM + <pre>) with scene graph & context control.
// No external deps. Mobile-safe. Designed for Replit preview.

export type Vec2 = { x: number; y: number };
export type ShaderInit = {
  seed?: number;
  charRamp?: string;
  palette?: string[];
  speed?: number;
  density?: number; // logical columns
  opacity?: number;
};
export type ShaderFrameArgs = {
  t: number;              // seconds
  dt: number;             // seconds since last frame
  cols: number; rows: number;
  center: Vec2;           // 0..1
  pointer: Vec2;          // -1..+1
  state: Record<string, any>; // for "Jarvis" context
  rand: () => number;
};

export interface IAsciiShader {
  name: string;
  init?(init: ShaderInit): void;
  frame(args: ShaderFrameArgs): string[]; // returns array of rows
}

export type Layer = {
  shader: IAsciiShader;
  init?: ShaderInit;
  blend?: 'over' | 'add' | 'multiply'; // for future expansion
  visible?: boolean;
};

export type EngineOptions = {
  parent: HTMLElement;
  fontSize?: number;              // px
  density?: number;               // logical columns (char cells) for base resolution
  maxWidthVw?: number;            // mobile-friendly clamp
  charRamp?: string;              // default ramp
  palette?: string[];
  mobileScale?: number;           // reduce cols on mobile for perf
  onFPS?: (fps: number) => void;
};

export class AsciiEngine {
  private container!: HTMLElement;
  private pre!: HTMLPreElement;
  private raf = 0;
  private last = performance.now();
  private layers: Layer[] = [];
  private running = false;
  private cols = 120;
  private rows = 40;
  private options: EngineOptions;
  private pointer: Vec2 = { x: 0, y: 0 };
  private state: Record<string, any> = {};
  private accFrames = 0;
  private accTime = 0;

  constructor(opts: EngineOptions) {
    this.options = {
      fontSize: 14,
      density: 120,
      maxWidthVw: 96,
      charRamp: ' .:-=+*#%@',
      palette: ['#00FFC6', '#00C9FF', '#7C4DFF'],
      mobileScale: 0.7,
      ...opts
    };
    this.bootstrap();
    this.handleResize();
    window.addEventListener('resize', this.handleResize);
    this.container.addEventListener('pointermove', this.handlePointer);
    this.container.addEventListener('pointerleave', () => (this.pointer = { x: 0, y: 0 }));
  }

  destroy() {
    cancelAnimationFrame(this.raf);
    window.removeEventListener('resize', this.handleResize);
    this.container.removeEventListener('pointermove', this.handlePointer);
  }

  private bootstrap() {
    const wrap = document.createElement('div');
    wrap.className = 'ascii-wrap';
    wrap.style.position = 'relative';
    wrap.style.width = `${this.options.maxWidthVw}vw`;
    wrap.style.maxWidth = '1400px';
    wrap.style.margin = '0 auto';
    wrap.style.perspective = '1200px';

    const frame = document.createElement('div');
    frame.className = 'ascii-frame';
    frame.style.transform = 'rotateX(10deg) translateZ(0)';
    frame.style.border = '1px solid rgba(0,255,200,0.25)';
    frame.style.boxShadow = '0 0 40px rgba(0,255,200,0.15) inset, 0 0 80px rgba(0,200,255,0.2)';
    frame.style.borderRadius = '18px';
    frame.style.backdropFilter = 'blur(3px)';
    frame.style.background = 'linear-gradient(180deg, rgba(0,16,32,0.85), rgba(0,0,0,0.85))';

    const pre = document.createElement('pre');
    pre.className = 'ascii-pre';
    pre.style.margin = '0';
    pre.style.padding = '16px';
    pre.style.fontFamily = `'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`;
    pre.style.fontSize = `${this.options.fontSize}px`;
    pre.style.lineHeight = '1.0';
    pre.style.letterSpacing = '0.5px';
    pre.style.color = this.options.palette?.[0] ?? '#00FFC6';
    pre.style.textShadow = `
      0 0 6px rgba(0,255,200,0.5),
      0 0 18px rgba(0,200,255,0.3)
    `;
    pre.style.userSelect = 'none';
    pre.style.whiteSpace = 'pre';
    pre.style.overflow = 'hidden';
    pre.style.mixBlendMode = 'screen';

    frame.appendChild(pre);
    wrap.appendChild(frame);
    this.options.parent.appendChild(wrap);
    this.container = wrap;
    this.pre = pre;
  }

  private handleResize = () => {
    const rect = this.container.getBoundingClientRect();
    const baseCols = this.options.density!;
    const isMobile = rect.width < 640;
    const cols = Math.max(48, Math.floor(baseCols * (isMobile ? this.options.mobileScale! : 1)));
    const ratio = 3; // cols:rows ~3:1 looks good for monospace with line-height 1.0
    const rows = Math.max(18, Math.floor(cols / ratio));
    this.cols = cols;
    this.rows = rows;
  };

  private handlePointer = (e: PointerEvent) => {
    const rect = this.container.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;  // 0..1
    const y = (e.clientY - rect.top) / rect.height;  // 0..1
    this.pointer = { x: x * 2 - 1, y: y * 2 - 1 };   // -1..1
  };

  // Simple hashed PRNG per frame for shaders
  private makeRand(seed: number) {
    let s = seed >>> 0;
    return () => {
      s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
      return ((s >>> 0) / 0xFFFFFFFF);
    };
  }

  setState(k: string, v: any) { this.state[k] = v; }
  mergeState(partial: Record<string, any>) { Object.assign(this.state, partial); }

  addLayer(layer: Layer) {
    const shader = layer.shader;
    const init = layer.init || {};
    shader.init?.(init);
    this.layers.push({ ...layer, visible: layer.visible ?? true });
  }

  clearLayers() { this.layers = []; }

  start() {
    if (this.running) return;
    this.running = true;
    this.last = performance.now();
    const tick = () => {
      if (!this.running) return;
      const now = performance.now();
      const dt = (now - this.last) / 1000;
      const t = now / 1000;
      this.last = now;

      const rand = this.makeRand(Math.floor(now));
      const center = { x: 0.5, y: 0.5 };

      // Compose layers
      let composite: string[] | null = null;
      for (const L of this.layers) {
        if (!L.visible) continue;
        const frame = L.shader.frame({
          t, dt,
          cols: this.cols, rows: this.rows,
          center, pointer: this.pointer,
          state: this.state,
          rand
        });
        if (!composite) {
          composite = frame;
        } else {
          // Simple "add" blend: choose brighter glyph by ramp index
          const out: string[] = [];
          for (let r = 0; r < this.rows; r++) {
            const a = composite[r] || '';
            const b = frame[r] || '';
            let line = '';
            for (let c = 0; c < this.cols; c++) {
              const ca = a.charCodeAt(c) || 32;
              const cb = b.charCodeAt(c) || 32;
              line += (cb > ca ? (b[c] ?? ' ') : (a[c] ?? ' '));
            }
            out.push(line);
          }
          composite = out;
        }
      }
      // Render
      if (composite) this.pre.textContent = composite.join('\n');

      // FPS sampling
      this.accFrames++;
      this.accTime += dt;
      if (this.accTime >= 1 && this.options.onFPS) {
        this.options.onFPS(this.accFrames / this.accTime);
        this.accFrames = 0; this.accTime = 0;
      }

      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  stop() {
    this.running = false;
    cancelAnimationFrame(this.raf);
  }
}
