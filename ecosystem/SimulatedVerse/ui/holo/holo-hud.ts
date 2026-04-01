// A self-contained holographic HUD Web Component with depth/parallax, starfield,
// 2D-projected "3D" grid, ASCII viewport overlay, title screen, and control bar.
// No dependencies. Works inside any app (React/Svelte/Vue/vanilla) via <holo-hud>.

const template = document.createElement('template');
template.innerHTML = `
<style>
  :host {
    --bg: #05060a;
    --neon: #00eaff;
    --neon-2: #7c4dff;
    --accent: #23ff8f;
    --scan: rgba(255,255,255,0.03);
    --noise: rgba(255,255,255,0.04);
    --glow: drop-shadow(0 0 12px var(--neon));
    --hud-alpha: .85;
    --grid-alpha: .18;
    --ui: rgba(10,14,20,.6);
    --ui-blur: 12px;
    --border: rgba(255,255,255,.12);
    --text: #e8f7ff;
    --muted: #9bb0bd;
    --ok: #23ff8f;
    --warn: #ffc857;
    --err: #ff5869;

    display: block;
    contain: content;
    position: relative;
    isolation: isolate;
    background: radial-gradient(1200px 800px at 50% 55%, #0b1022 0%, #05060a 60%, #020308 100%);
    color: var(--text);
    font: 13px/1.25 ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow: hidden;
    /* perspective for layered parallax */
    perspective: 1000px;
  }

  .root {
    position: relative;
    width: 100%;
    height: 100%;
  }

  canvas.bg, canvas.grid, canvas.fx {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
  }

  /* layered parallax planes */
  .layer {
    position: absolute;
    inset: 0;
    transform-style: preserve-3d;
    pointer-events: none;
  }

  .overlay {
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-rows: auto 1fr auto;
    pointer-events: none;
  }

  .titlebar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    pointer-events: auto;
    background: color-mix(in oklab, var(--ui) var(--hud-alpha), transparent);
    -webkit-backdrop-filter: blur(var(--ui-blur));
    backdrop-filter: blur(var(--ui-blur));
    border-bottom: 1px solid var(--border);
  }
  .title {
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    filter: var(--glow);
  }
  .state {
    margin-left: auto;
    display: flex;
    gap: 14px;
    font-size: 12px;
    color: var(--muted);
  }
  .state b { color: var(--text); }

  .viewport {
    position: relative;
    display: grid;
    grid-template-columns: minmax(260px, 320px) 1fr;
    gap: 12px;
    padding: 10px 12px;
  }
  @media (max-width: 980px) {
    .viewport { grid-template-columns: 1fr; }
  }

  .panel {
    pointer-events: auto;
    background: color-mix(in oklab, var(--ui) var(--hud-alpha), transparent);
    -webkit-backdrop-filter: blur(var(--ui-blur));
    backdrop-filter: blur(var(--ui-blur));
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,.25);
  }
  .panel h3 {
    margin: 0; padding: 10px 12px;
    font-weight: 600;
    letter-spacing: .03em;
    border-bottom: 1px solid var(--border);
    color: var(--neon);
    text-shadow: 0 0 6px rgba(0,234,255,.35);
  }
  .panel .body {
    padding: 10px 12px;
    max-height: 38vh;
    overflow: auto;
  }
  .kv { display: grid; grid-template-columns: auto 1fr; gap: 6px 10px; }
  .kv span { color: var(--muted); }
  .kv b { color: var(--text); }

  .ascii {
    font: 12px/1.1 "Cascadia Mono","Fira Code","JetBrains Mono",ui-monospace,monospace;
    color: #9ae7ff;
    text-shadow: 0 0 8px rgba(0,234,255,.45);
    white-space: pre;
    overflow: auto;
    max-height: 38vh;
  }
  .ascii .pulse { color: var(--accent); }

  .controls {
    display: flex; gap: 8px; padding: 10px 12px;
    border-top: 1px solid var(--border);
    pointer-events: auto;
  }
  .btn {
    appearance: none;
    border: 1px solid var(--border);
    background: linear-gradient(180deg, rgba(20,26,38,.9), rgba(8,10,14,.9));
    color: var(--text);
    padding: 8px 10px;
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: .02em;
    cursor: pointer;
    transition: transform .06s ease, border-color .2s ease, box-shadow .2s ease, filter .2s ease;
    box-shadow: 0 4px 14px rgba(0,0,0,.25), inset 0 0 0 0 rgba(255,255,255,.05);
    filter: drop-shadow(0 0 6px rgba(0,234,255,.25));
  }
  .btn:hover { transform: translateY(-1px); border-color: color-mix(in oklab, var(--neon) 55%, var(--border)); }
  .btn:active { transform: translateY(0); }
  .btn.red { border-color: rgba(255,90,90,.6); color: #ffdede; text-shadow: 0 0 8px rgba(255,90,90,.55); }
  .btn.ghost { background: transparent; }

  /* Scanlines + film grain for "hologram" */
  .fx-scanlines {
    position: absolute; inset: 0;
    background: repeating-linear-gradient(
      to bottom,
      transparent 0, transparent 2px, var(--scan) 3px
    );
    mix-blend-mode: screen; opacity: .35; pointer-events: none;
  }
  .fx-noise {
    position: absolute; inset: 0;
    background-image: radial-gradient(circle at 10% 20%, var(--noise) 0 1px, transparent 1px),
                      radial-gradient(circle at 80% 50%, var(--noise) 0 1px, transparent 1px),
                      radial-gradient(circle at 30% 80%, var(--noise) 0 1px, transparent 1px);
    background-size: 3px 3px, 3px 3px, 3px 3px;
    mix-blend-mode: soft-light; opacity: .5; pointer-events: none;
  }

  /* Title screen overlay */
  .title-screen {
    position: absolute; inset: 0;
    display: grid; place-items: center;
    background: radial-gradient(1200px 800px at 50% 55%, rgba(0,10,20,.75), rgba(0,0,0,.6));
    backdrop-filter: blur(10px) saturate(1.2);
    -webkit-backdrop-filter: blur(10px) saturate(1.2);
    animation: in .6s ease backwards;
  }
  @keyframes in { from { opacity: 0; transform: scale(.98); } }
  .title-card {
    pointer-events: auto;
    padding: 18px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: color-mix(in oklab, var(--ui) 92%, transparent);
    width: min(720px, 92vw);
    box-shadow: 0 40px 80px rgba(0,0,0,.45);
  }
  .title-card h1 {
    margin: 0 0 6px; font-size: clamp(20px, 4vw, 34px);
    letter-spacing: .08em; text-transform: uppercase;
    color: var(--neon);
    text-shadow: 0 0 16px rgba(0,234,255,.45), 0 0 30px rgba(124,77,255,.25);
  }
  .title-card p { margin: 0 0 12px; color: var(--muted); }
  .title-actions { display: flex; gap: 8px; flex-wrap: wrap; }
</style>

<div class="root">
  <canvas class="bg"></canvas>
  <canvas class="grid"></canvas>
  <div class="layer" id="parallax"></div>
  <canvas class="fx"></canvas>

  <div class="overlay">
    <div class="titlebar">
      <div class="title">ΞNuSyQ — Holographic Command Deck</div>
      <div class="state"><span>Mode:</span> <b id="mode">desktop</b> <span>FPS:</span> <b id="fps">–</b></div>
    </div>

    <div class="viewport">
      <div class="panel">
        <h3>Systems</h3>
        <div class="body">
          <div class="kv">
            <span>Consciousness</span><b id="v-cons">0%</b>
            <span>Agents</span><b id="v-agents">0</b>
            <span>Cascade</span><b id="v-cascade">idle</b>
            <span>Temple</span><b id="v-temple">Floor 1</b>
            <span>Mobile</span><b id="v-mobile">false</b>
          </div>
        </div>
      </div>

      <div class="panel">
        <h3>ASCII Viewport</h3>
        <div class="body ascii" id="ascii"></div>
      </div>
    </div>

    <div class="controls">
      <button class="btn" id="btnPause">⏸ Pause</button>
      <button class="btn ghost" id="btnMute">🔇 Mute</button>
      <button class="btn" id="btnCutscene">🎬 Cutscene</button>
      <button class="btn red" id="btnCascade">🔴 Big Red Cascade</button>
      <button class="btn ghost" id="btnToggleAscii">🖼 ASCII</button>
    </div>
  </div>

  <div class="fx-scanlines"></div>
  <div class="fx-noise"></div>

  <div class="title-screen" id="title">
    <div class="title-card">
      <h1>SimulatedVerse // CoreLink Foundation</h1>
      <p>Peer into a living hologram. Unlock systems as you progress. Everything adapts—mobile or desktop—without jank.</p>
      <div class="title-actions">
        <button class="btn" id="startNew">▶ New Run</button>
        <button class="btn ghost" id="loadGame">⏏ Load</button>
        <button class="btn ghost" id="settings">⚙ Settings</button>
        <button class="btn ghost" id="temple">🛕 Temple</button>
      </div>
    </div>
  </div>
</div>
`;

class HoloHUD extends HTMLElement {
  /** @type {HTMLCanvasElement} */ bg;
  /** @type {HTMLCanvasElement} */ grid;
  /** @type {HTMLCanvasElement} */ fx;
  /** @type {CanvasRenderingContext2D} */ bgctx;
  /** @type {CanvasRenderingContext2D} */ gridctx;
  /** @type {CanvasRenderingContext2D} */ fxctx;
  shadowRoot;
  raf = 0;
  running = true;
  muted = true;
  animStart = performance.now();
  lastFrame = performance.now();
  fpsAvg = 0;
  mobile = false;
  asciiOn = true;

  audioCtx: AudioContext | null = null;
  hum: { o: OscillatorNode; g: GainNode } | null = null;

  constructor(){
    super();
    this.attachShadow({mode:'open'});
    this.shadowRoot.appendChild(template.content.cloneNode(true));
  }

  connectedCallback(){
    const sr = this.shadowRoot!;
    this.bg = sr.querySelector('canvas.bg')!;
    this.grid = sr.querySelector('canvas.grid')!;
    this.fx = sr.querySelector('canvas.fx')!;
    this.bgctx = this.bg.getContext('2d', {alpha:false})!;
    this.gridctx = this.grid.getContext('2d')!;
    this.fxctx = this.fx.getContext('2d')!;

    this.resize = this.resize.bind(this);
    this.tick = this.tick.bind(this);
    this.onVisibility = this.onVisibility.bind(this);
    this.onPointer = this.onPointer.bind(this);

    new ResizeObserver(()=>this.resize()).observe(this);
    window.addEventListener('visibilitychange', this.onVisibility);
    this.addEventListener('pointermove', this.onPointer, {passive:true});
    this.mobile = matchMedia('(max-width: 980px)').matches || 'ontouchstart' in window;
    sr.getElementById('v-mobile')!.textContent = String(this.mobile);
    sr.getElementById('mode')!.textContent = this.mobile ? 'mobile' : 'desktop';

    // Buttons
    sr.getElementById('btnPause')!.addEventListener('click', ()=>this.toggleRun());
    sr.getElementById('btnMute')!.addEventListener('click', ()=>this.toggleHum());
    sr.getElementById('btnCutscene')!.addEventListener('click', ()=>this.playCutscene('blacksmith'));
    sr.getElementById('btnCascade')!.addEventListener('click', ()=>this.triggerCascade());
    sr.getElementById('btnToggleAscii')!.addEventListener('click', ()=>this.toggleAscii());

    // Title screen
    sr.getElementById('startNew')!.addEventListener('click', ()=>this.dismissTitle());
    sr.getElementById('loadGame')!.addEventListener('click', ()=>this.toast('Load: not implemented (stub).'));
    sr.getElementById('settings')!.addEventListener('click', ()=>this.openSettings());
    sr.getElementById('temple')!.addEventListener('click', ()=>this.openTemple());

    // ASCII viewport seed
    this.seedASCII();

    this.resize();
    this.raf = requestAnimationFrame(this.tick);
  }

  disconnectedCallback(){
    cancelAnimationFrame(this.raf);
    window.removeEventListener('visibilitychange', this.onVisibility);
    this.removeEventListener('pointermove', this.onPointer);
    if (this.audioCtx) { this.audioCtx.close().catch(()=>{}); }
  }

  onVisibility(){
    if (document.hidden) { this.running = false; }
    else { this.running = true; this.lastFrame = performance.now(); this.raf = requestAnimationFrame(this.tick); }
  }

  onPointer(e){
    // parallax effect on pointer
    const rect = this.getBoundingClientRect();
    const cx = (e.clientX - rect.left) / rect.width - 0.5;
    const cy = (e.clientY - rect.top) / rect.height - 0.5;
    const parallax = this.shadowRoot!.getElementById('parallax')!;
    parallax.style.transform = `translate3d(${cx*-10}px, ${cy*-10}px, 0) rotateX(${cy*6}deg) rotateY(${cx*-6}deg)`;
  }

  resize(){
    const canvases = [this.bg, this.grid, this.fx];
    const dpr = Math.min(window.devicePixelRatio||1, 2);
    const w = Math.floor(this.clientWidth * dpr);
    const h = Math.floor(this.clientHeight * dpr);
    for (const c of canvases) { c.width = w; c.height = h; c.style.width = '100%'; c.style.height = '100%'; }
  }

  // === RENDER LOOP ===========================================================
  tick(now){
    if (!this.running) return;
    const dt = (now - this.lastFrame) / 1000;
    this.lastFrame = now;
    const fpsInst = 1/Math.max(dt, 1/120);
    this.fpsAvg = this.fpsAvg ? this.fpsAvg*0.9 + fpsInst*0.1 : fpsInst;
    this.shadowRoot!.getElementById('fps')!.textContent = String(Math.round(this.fpsAvg));

    const t = (now - this.animStart) / 1000;

    this.paintStarfield(t);
    this.paintGrid(t);
    this.paintFX(t);

    this.raf = requestAnimationFrame(this.tick);
  }

  // Background starfield with depth shimmer
  paintStarfield(t){
    const ctx = this.bgctx;
    const {width:w, height:h} = this.bg;
    ctx.fillStyle = getComputedStyle(this).getPropertyValue('--bg') || '#05060a';
    ctx.fillRect(0,0,w,h);

    const n = Math.floor((w*h)/6000); // density auto scales
    for (let i=0;i<n;i++){
      const x = (i*9973 % w) + (Math.sin(t*0.2 + i)*20);
      const y = (i*6007 % h) + (Math.cos(t*0.17 + i*0.5)*10);
      const twinkle = (Math.sin(t*2 + i*0.35)*0.5+0.5);
      const lum = 180 + twinkle*75;
      ctx.fillStyle = `rgba(${lum}, ${220}, ${255}, ${0.35+0.35*twinkle})`;
      ctx.fillRect(x%w, y%h, 1, 1);
    }
  }

  // Perspective "3D" grid warp
  paintGrid(t){
    const ctx = this.gridctx;
    const {width:w, height:h} = this.grid;
    ctx.clearRect(0,0,w,h);
    ctx.save();
    ctx.translate(w/2, h*0.68);
    const neon = getComputedStyle(this).getPropertyValue('--neon') || '#00eaff';
    const neon2 = getComputedStyle(this).getPropertyValue('--neon-2') || '#7c4dff';
    const alpha = parseFloat(getComputedStyle(this).getPropertyValue('--grid-alpha')) || .18;
    ctx.strokeStyle = `rgba(0, 234, 255, ${alpha})`;
    ctx.lineWidth = 1;

    const horizon = -h*0.52;
    // horizontal lines (depth)
    for (let i=1;i<32;i++){
      const z = i/32;
      const y = (horizon) * Math.pow(z, 1.3);
      ctx.beginPath();
      ctx.moveTo(-w, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }
    // vertical lines (warped by time for "hologram" sway)
    for (let i=-32;i<=32;i++){
      const sway = Math.sin(t*0.7 + i*0.33) * 10;
      ctx.beginPath();
      ctx.moveTo(i*28 + sway, horizon);
      ctx.lineTo(i*10 + sway*0.2, 0);
      ctx.strokeStyle = i%4===0 ? `rgba(124,77,255,${alpha})` : `rgba(0,234,255,${alpha*0.75})`;
      ctx.stroke();
    }
    ctx.restore();
  }

  // FX overlay (faint bloom rings, cursor halo, occasional sweep)
  paintFX(t){
    const ctx = this.fxctx;
    const {width:w, height:h} = this.fx;
    ctx.clearRect(0,0,w,h);

    // slow radial glow pulsation
    const r = Math.min(w,h)*0.35*(1+0.03*Math.sin(t*0.8));
    const grad = ctx.createRadialGradient(w/2,h*0.6, r*0.2, w/2,h*0.6, r);
    grad.addColorStop(0, 'rgba(0,234,255,0.08)');
    grad.addColorStop(1, 'rgba(0,234,255,0)');
    ctx.fillStyle = grad;
    ctx.beginPath(); ctx.arc(w/2,h*0.6,r,0,Math.PI*2); ctx.fill();

    // periodic horizontal sweep
    const sweep = (Math.sin(t*0.6)*0.5+0.5);
    const sy = h*(0.15 + sweep*0.6);
    const lg = ctx.createLinearGradient(0, sy-30, 0, sy+30);
    lg.addColorStop(0, 'rgba(124,77,255,0)');
    lg.addColorStop(0.5, 'rgba(124,77,255,0.25)');
    lg.addColorStop(1, 'rgba(124,77,255,0)');
    ctx.fillStyle = lg;
    ctx.fillRect(0, sy-30, w, 60);
  }

  // === UI Actions ============================================================
  toggleRun(){
    this.running = !this.running;
    this.shadowRoot!.getElementById('btnPause')!.textContent = this.running ? '⏸ Pause' : '▶ Resume';
    if (this.running) { this.lastFrame = performance.now(); this.raf = requestAnimationFrame(this.tick); }
  }

  async toggleHum(){
    try{
      if (!this.audioCtx){
        this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const o = this.audioCtx.createOscillator();
        const g = this.audioCtx.createGain();
        o.type = 'sawtooth';
        o.frequency.value = 55; // sub-hum
        g.gain.value = 0.002;
        o.connect(g).connect(this.audioCtx.destination);
        o.start();
        this.hum = {o,g};
      }
      this.muted = !this.muted;
      if (this.hum) this.hum.g.gain.value = this.muted ? 0.0 : 0.002;
      this.shadowRoot!.getElementById('btnMute')!.textContent = this.muted ? '🔇 Mute' : '🔊 Hum';
    } catch { /* non-fatal */ }
  }

  dismissTitle(){
    this.shadowRoot!.getElementById('title')!.style.display = 'none';
    this.toast('New Run initialized. Systems unlocking…');
    // seed some "live" numbers to avoid dead UI
    this.shadowRoot!.getElementById('v-cons')!.textContent = '7%';
    this.shadowRoot!.getElementById('v-agents')!.textContent = '3';
    this.shadowRoot!.getElementById('v-cascade')!.textContent = 'armed';
  }

  openSettings(){ this.toast('Settings panel is a stub.'); }
  openTemple(){
    // try to open in-repo doc path if served; otherwise hint
    this.toast('Temple: open modules/culture_ship/temples/index.md in a side panel.');
  }

  async triggerCascade(){
    // Try an app route first, fallback to clipboard command
    try{
      const res = await fetch('/api/cascade', {method:'POST'}); // optional backend
      if (res.ok){ this.toast('Cascade triggered server-side.'); return; }
      throw new Error('no endpoint');
    } catch {
      const cmd = 'npm run cascade';
      await navigator.clipboard.writeText(cmd).catch(()=>{});
      this.toast('No /api/cascade endpoint. Copied "npm run cascade" to clipboard. Run in shell.');
    }
  }

  toggleAscii(){
    this.asciiOn = !this.asciiOn;
    (this.shadowRoot!.getElementById('ascii') as HTMLElement).style.display = this.asciiOn ? 'block' : 'none';
  }

  seedASCII(){
    const el = this.shadowRoot!.getElementById('ascii')!;
    const lines = 28;
    const cols = 92;
    const chars = " .,:;!+*oO0#@";
    let s = '';
    for (let y=0;y<lines;y++){
      let row = '';
      for (let x=0;x<cols;x++){
        const v = Math.sin(y*0.27 + x*0.19) * Math.cos(y*0.12 + x*0.33);
        const i = Math.floor((v*0.5+0.5)*(chars.length-1));
        row += chars[i];
      }
      s += row + "\n";
    }
    el.textContent = s + "\n[ ASCII viewport ready — press 🎬 Cutscene ]";
  }

  playCutscene(kind:'blacksmith'|'encounter'='blacksmith'){
    const el = this.shadowRoot!.getElementById('ascii')!;
    // micro "cinematic" in ASCII (non-blocking, cancellable by toggling)
    const frames = kind==='blacksmith' ? this.blacksmithFrames() : this.encounterFrames();
    let idx = 0;
    const run = ()=>{
      if (!this.asciiOn) return;
      el.textContent = frames[idx];
      idx = (idx+1) % frames.length;
      if (idx!==0) setTimeout(run, 60);
      else setTimeout(()=>el.textContent += "\n\n✨ Legendary forge complete.", 120);
    };
    run();
  }

  blacksmithFrames(){
    // tiny looping ASCII "hammer strike"
    const base = [
`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          ⛭           ⛭          ⛭
       __/\\__    __/\\__    __/\\__
      /      \\  /      \\  /      \\
     |  ████  ||  ████  ||  ████  |
     |  ████  ||  ████  ||  ████  |
     |__████__||__████__||__████__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`,
`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          ⛭           ⛭          ⛭
       __/\\__   ✨ __/\\__ ✨  __/\\__
      /      \\  ✨     ✨   /      \\
     |  ████  ||  ████  ||  ████  |
     |  ████  ||  ████  ||  ████  |
     |__████__||__████__||__████__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`,
`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          ⛭           ⛭          ⛭
       __/\\__  🔥  __/\\__  🔥  __/\\__
      /      \\     🔥     /      \\
     |  ████  ||  ████  ||  ████  |
     |  ████  ||  ████  ||  ████  |
     |__████__||__████__||__████__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`
    ];
    return base;
  }

  encounterFrames(){
    return [
`  ∴    ∵      ∴     ∵     ∴
         🜂           🗡
     @        vs        ϟ
  ∵    ∴      ∵     ∴     ∵`,
`  ∵    ∴      ∵     ∴     ∵
         🗡           🜂
     @        vs        ϟ
  ∴    ∵      ∴     ∵     ∴`
    ];
  }

  toast(msg:string){
    const n = document.createElement('div');
    n.textContent = msg;
    Object.assign(n.style, {
      position:'absolute', right:'12px', bottom:'12px', padding:'10px 12px',
      background:'color-mix(in oklab, var(--ui) 92%, transparent)',
      border:'1px solid var(--border)', borderRadius:'12px', zIndex:'9999',
      backdropFilter:'blur(8px)', color:'var(--text)', fontWeight:'600',
      boxShadow:'0 10px 30px rgba(0,0,0,.35)'
    });
    this.shadowRoot!.appendChild(n);
    setTimeout(()=>n.remove(), 2400);
  }
}

customElements.define('holo-hud', HoloHUD);