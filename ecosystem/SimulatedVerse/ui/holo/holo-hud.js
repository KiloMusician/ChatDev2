"use strict";(()=>{var h=document.createElement("template");h.innerHTML=`
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
      <div class="title">\u039ENuSyQ \u2014 Holographic Command Deck</div>
      <div class="state"><span>Mode:</span> <b id="mode">desktop</b> <span>FPS:</span> <b id="fps">\u2013</b></div>
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
      <button class="btn" id="btnPause">\u23F8 Pause</button>
      <button class="btn ghost" id="btnMute">\u{1F507} Mute</button>
      <button class="btn" id="btnCutscene">\u{1F3AC} Cutscene</button>
      <button class="btn red" id="btnCascade">\u{1F534} Big Red Cascade</button>
      <button class="btn ghost" id="btnToggleAscii">\u{1F5BC} ASCII</button>
    </div>
  </div>

  <div class="fx-scanlines"></div>
  <div class="fx-noise"></div>

  <div class="title-screen" id="title">
    <div class="title-card">
      <h1>SimulatedVerse // CoreLink Foundation</h1>
      <p>Peer into a living hologram. Unlock systems as you progress. Everything adapts\u2014mobile or desktop\u2014without jank.</p>
      <div class="title-actions">
        <button class="btn" id="startNew">\u25B6 New Run</button>
        <button class="btn ghost" id="loadGame">\u23CF Load</button>
        <button class="btn ghost" id="settings">\u2699 Settings</button>
        <button class="btn ghost" id="temple">\u{1F6D5} Temple</button>
      </div>
    </div>
  </div>
</div>
`;var c=class extends HTMLElement{bg;grid;fx;bgctx;gridctx;fxctx;shadowRoot;raf=0;running=!0;muted=!0;animStart=performance.now();lastFrame=performance.now();fpsAvg=0;mobile=!1;asciiOn=!0;audioCtx=null;hum=null;constructor(){super(),this.attachShadow({mode:"open"}),this.shadowRoot.appendChild(h.content.cloneNode(!0))}connectedCallback(){let e=this.shadowRoot;this.bg=e.querySelector("canvas.bg"),this.grid=e.querySelector("canvas.grid"),this.fx=e.querySelector("canvas.fx"),this.bgctx=this.bg.getContext("2d",{alpha:!1}),this.gridctx=this.grid.getContext("2d"),this.fxctx=this.fx.getContext("2d"),this.resize=this.resize.bind(this),this.tick=this.tick.bind(this),this.onVisibility=this.onVisibility.bind(this),this.onPointer=this.onPointer.bind(this),new ResizeObserver(()=>this.resize()).observe(this),window.addEventListener("visibilitychange",this.onVisibility),this.addEventListener("pointermove",this.onPointer,{passive:!0}),this.mobile=matchMedia("(max-width: 980px)").matches||"ontouchstart"in window,e.getElementById("v-mobile").textContent=String(this.mobile),e.getElementById("mode").textContent=this.mobile?"mobile":"desktop",e.getElementById("btnPause").addEventListener("click",()=>this.toggleRun()),e.getElementById("btnMute").addEventListener("click",()=>this.toggleHum()),e.getElementById("btnCutscene").addEventListener("click",()=>this.playCutscene("blacksmith")),e.getElementById("btnCascade").addEventListener("click",()=>this.triggerCascade()),e.getElementById("btnToggleAscii").addEventListener("click",()=>this.toggleAscii()),e.getElementById("startNew").addEventListener("click",()=>this.dismissTitle()),e.getElementById("loadGame").addEventListener("click",()=>this.toast("Load: not implemented (stub).")),e.getElementById("settings").addEventListener("click",()=>this.openSettings()),e.getElementById("temple").addEventListener("click",()=>this.openTemple()),this.seedASCII(),this.resize(),this.raf=requestAnimationFrame(this.tick)}disconnectedCallback(){cancelAnimationFrame(this.raf),window.removeEventListener("visibilitychange",this.onVisibility),this.removeEventListener("pointermove",this.onPointer),this.audioCtx&&this.audioCtx.close().catch(()=>{})}onVisibility(){document.hidden?this.running=!1:(this.running=!0,this.lastFrame=performance.now(),this.raf=requestAnimationFrame(this.tick))}onPointer(e){let t=this.getBoundingClientRect(),a=(e.clientX-t.left)/t.width-.5,i=(e.clientY-t.top)/t.height-.5,n=this.shadowRoot.getElementById("parallax");n.style.transform=`translate3d(${a*-10}px, ${i*-10}px, 0) rotateX(${i*6}deg) rotateY(${a*-6}deg)`}resize(){let e=[this.bg,this.grid,this.fx],t=Math.min(window.devicePixelRatio||1,2),a=Math.floor(this.clientWidth*t),i=Math.floor(this.clientHeight*t);for(let n of e)n.width=a,n.height=i,n.style.width="100%",n.style.height="100%"}tick(e){if(!this.running)return;let t=(e-this.lastFrame)/1e3;this.lastFrame=e;let a=1/Math.max(t,1/120);this.fpsAvg=this.fpsAvg?this.fpsAvg*.9+a*.1:a,this.shadowRoot.getElementById("fps").textContent=String(Math.round(this.fpsAvg));let i=(e-this.animStart)/1e3;this.paintStarfield(i),this.paintGrid(i),this.paintFX(i),this.raf=requestAnimationFrame(this.tick)}paintStarfield(e){let t=this.bgctx,{width:a,height:i}=this.bg;t.fillStyle=getComputedStyle(this).getPropertyValue("--bg")||"#05060a",t.fillRect(0,0,a,i);let n=Math.floor(a*i/6e3);for(let o=0;o<n;o++){let l=o*9973%a+Math.sin(e*.2+o)*20,r=o*6007%i+Math.cos(e*.17+o*.5)*10,s=Math.sin(e*2+o*.35)*.5+.5,d=180+s*75;t.fillStyle=`rgba(${d}, 220, 255, ${.35+.35*s})`,t.fillRect(l%a,r%i,1,1)}}paintGrid(e){let t=this.gridctx,{width:a,height:i}=this.grid;t.clearRect(0,0,a,i),t.save(),t.translate(a/2,i*.68);let n=getComputedStyle(this).getPropertyValue("--neon")||"#00eaff",o=getComputedStyle(this).getPropertyValue("--neon-2")||"#7c4dff",l=parseFloat(getComputedStyle(this).getPropertyValue("--grid-alpha"))||.18;t.strokeStyle=`rgba(0, 234, 255, ${l})`,t.lineWidth=1;let r=-i*.52;for(let s=1;s<32;s++){let d=s/32,p=r*Math.pow(d,1.3);t.beginPath(),t.moveTo(-a,p),t.lineTo(a,p),t.stroke()}for(let s=-32;s<=32;s++){let d=Math.sin(e*.7+s*.33)*10;t.beginPath(),t.moveTo(s*28+d,r),t.lineTo(s*10+d*.2,0),t.strokeStyle=s%4===0?`rgba(124,77,255,${l})`:`rgba(0,234,255,${l*.75})`,t.stroke()}t.restore()}paintFX(e){let t=this.fxctx,{width:a,height:i}=this.fx;t.clearRect(0,0,a,i);let n=Math.min(a,i)*.35*(1+.03*Math.sin(e*.8)),o=t.createRadialGradient(a/2,i*.6,n*.2,a/2,i*.6,n);o.addColorStop(0,"rgba(0,234,255,0.08)"),o.addColorStop(1,"rgba(0,234,255,0)"),t.fillStyle=o,t.beginPath(),t.arc(a/2,i*.6,n,0,Math.PI*2),t.fill();let l=Math.sin(e*.6)*.5+.5,r=i*(.15+l*.6),s=t.createLinearGradient(0,r-30,0,r+30);s.addColorStop(0,"rgba(124,77,255,0)"),s.addColorStop(.5,"rgba(124,77,255,0.25)"),s.addColorStop(1,"rgba(124,77,255,0)"),t.fillStyle=s,t.fillRect(0,r-30,a,60)}toggleRun(){this.running=!this.running,this.shadowRoot.getElementById("btnPause").textContent=this.running?"\u23F8 Pause":"\u25B6 Resume",this.running&&(this.lastFrame=performance.now(),this.raf=requestAnimationFrame(this.tick))}async toggleHum(){try{if(!this.audioCtx){this.audioCtx=new(window.AudioContext||window.webkitAudioContext);let e=this.audioCtx.createOscillator(),t=this.audioCtx.createGain();e.type="sawtooth",e.frequency.value=55,t.gain.value=.002,e.connect(t).connect(this.audioCtx.destination),e.start(),this.hum={o:e,g:t}}this.muted=!this.muted,this.hum&&(this.hum.g.gain.value=this.muted?0:.002),this.shadowRoot.getElementById("btnMute").textContent=this.muted?"\u{1F507} Mute":"\u{1F50A} Hum"}catch{}}dismissTitle(){this.shadowRoot.getElementById("title").style.display="none",this.toast("New Run initialized. Systems unlocking\u2026"),this.shadowRoot.getElementById("v-cons").textContent="7%",this.shadowRoot.getElementById("v-agents").textContent="3",this.shadowRoot.getElementById("v-cascade").textContent="armed"}openSettings(){this.toast("Settings panel is a stub.")}openTemple(){this.toast("Temple: open modules/culture_ship/temples/index.md in a side panel.")}async triggerCascade(){try{if((await fetch("/api/cascade",{method:"POST"})).ok){this.toast("Cascade triggered server-side.");return}throw new Error("no endpoint")}catch{await navigator.clipboard.writeText("npm run cascade").catch(()=>{}),this.toast('No /api/cascade endpoint. Copied "npm run cascade" to clipboard. Run in shell.')}}toggleAscii(){this.asciiOn=!this.asciiOn,this.shadowRoot.getElementById("ascii").style.display=this.asciiOn?"block":"none"}seedASCII(){let e=this.shadowRoot.getElementById("ascii"),t=28,a=92,i=" .,:;!+*oO0#@",n="";for(let o=0;o<t;o++){let l="";for(let r=0;r<a;r++){let s=Math.sin(o*.27+r*.19)*Math.cos(o*.12+r*.33),d=Math.floor((s*.5+.5)*(i.length-1));l+=i[d]}n+=l+`
`}e.textContent=n+`
[ ASCII viewport ready \u2014 press \u{1F3AC} Cutscene ]`}playCutscene(e="blacksmith"){let t=this.shadowRoot.getElementById("ascii"),a=e==="blacksmith"?this.blacksmithFrames():this.encounterFrames(),i=0,n=()=>{this.asciiOn&&(t.textContent=a[i],i=(i+1)%a.length,i!==0?setTimeout(n,60):setTimeout(()=>t.textContent+=`

\u2728 Legendary forge complete.`,120))};n()}blacksmithFrames(){return[`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          \u26ED           \u26ED          \u26ED
       __/\\__    __/\\__    __/\\__
      /      \\  /      \\  /      \\
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`,`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          \u26ED           \u26ED          \u26ED
       __/\\__   \u2728 __/\\__ \u2728  __/\\__
      /      \\  \u2728     \u2728   /      \\
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`,`      (  )      (  )      (  )
       )  (      )  (      )  (
      (    )    (    )    (    )
          \u26ED           \u26ED          \u26ED
       __/\\__  \u{1F525}  __/\\__  \u{1F525}  __/\\__
      /      \\     \u{1F525}     /      \\
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  ||  \u2588\u2588\u2588\u2588  |
     |__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__||__\u2588\u2588\u2588\u2588__|
        /  \\       /  \\      /  \\
       /____\\     /____\\    /____\\
      /      \\   /      \\  /      \\
`]}encounterFrames(){return[`  \u2234    \u2235      \u2234     \u2235     \u2234
         \u{1F702}           \u{1F5E1}
     @        vs        \u03DF
  \u2235    \u2234      \u2235     \u2234     \u2235`,`  \u2235    \u2234      \u2235     \u2234     \u2235
         \u{1F5E1}           \u{1F702}
     @        vs        \u03DF
  \u2234    \u2235      \u2234     \u2235     \u2234`]}toast(e){let t=document.createElement("div");t.textContent=e,Object.assign(t.style,{position:"absolute",right:"12px",bottom:"12px",padding:"10px 12px",background:"color-mix(in oklab, var(--ui) 92%, transparent)",border:"1px solid var(--border)",borderRadius:"12px",zIndex:"9999",backdropFilter:"blur(8px)",color:"var(--text)",fontWeight:"600",boxShadow:"0 10px 30px rgba(0,0,0,.35)"}),this.shadowRoot.appendChild(t),setTimeout(()=>t.remove(),2400)}};customElements.define("holo-hud",c);})();
