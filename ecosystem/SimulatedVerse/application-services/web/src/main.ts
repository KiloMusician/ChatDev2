import { AsciiRenderer } from "./application-services/web/src/render/asciiRenderer.ts";
import { ViewManager } from "./application-services/web/src/views/viewManager.ts";
import { State, save, load } from "./application-services/web/src/engine/state.ts";
import { nextCascade } from "./application-services/web/src/modules/cascade.ts";
import { chatdevAsciiGraph, mechanicsProgress } from "./application-services/web/src/modules/chatdevViz.ts";

// Load saved state
load();

// Calculate optimal canvas size
const cols = Math.floor((window.innerWidth / parseInt(getComputedStyle(document.documentElement).getPropertyValue("--tileW"))) - 3);
const rows = Math.floor(((window.innerHeight - 140) / parseInt(getComputedStyle(document.documentElement).getPropertyValue("--tileH"))) - 2);

const renderer = new AsciiRenderer(Math.max(48, cols), Math.max(20, rows));
const vm = new ViewManager(renderer);
renderer.mount(document.getElementById("canvasWrap")!);

// UI State Management
function setButtons(active: string) {
  document.querySelectorAll("#topbar .btn[data-view]").forEach(btn => {
    btn.classList.toggle("active", (btn as HTMLElement).dataset.view === active);
  });
}

function log(line: string) {
  const logEl = document.getElementById("log")!;
  logEl.textContent = (line + "\n" + logEl.textContent!).slice(0, 6000);
}

function paintStatus() {
  const res = Object.entries(State.resources)
    .map(([k, v]) => `${k}:${Math.floor(v)}`)
    .join("  ");
  
  const mechanicsCount = Object.keys(State.mechanics).filter(k => State.mechanics[k]).length;
  const hdr = `stage:${State.stage}  t:${State.t}  mechanics:${mechanicsCount}/123  ${res}${State.paused ? "  [PAUSED]" : ""}`;
  
  const mini = document.getElementById("miniNav")!;
  mini.innerHTML = `<div class="chip">1 Microbe</div><div class="chip">2 Colony</div><div class="chip">3 City</div><div class="chip">4 Planet</div><div class="chip">5 System</div><div class="chip">6 Space</div>`;
  
  (document.getElementById("log")!).dataset.h = hdr;
}

// Initialize UI
setButtons(State.stage);
log("Boot: ΞNuSyQ SimulatedVerse " + renderer.w + "x" + renderer.h);
log("Mobile detection: " + (/Mobi|Android/i.test(navigator.userAgent) ? "YES" : "NO"));
log("Integrating with mechanics.yml and orchestration system...");

// Wire up buttons
document.querySelectorAll<HTMLDivElement>("#topbar .btn[data-view]").forEach(b => {
  b.onclick = () => {
    vm.switch(b.dataset.view!);
    setButtons(b.dataset.view!);
    log(`Switched to ${b.dataset.view} view`);
  };
});

document.getElementById("btnCascade")!.onclick = () => {
  const plan = nextCascade();
  log("🌀 Cascade Event ➜ " + plan.title);
  log("Steps: " + plan.steps.join(" → "));
  log("Mechanics: " + plan.mechanics.join(", "));
  log("Estimated gain: " + (plan.estGain * 100) + "%");
};

document.getElementById("btnGraph")!.onclick = () => {
  log("📊 ChatDev Visualization:\n" + chatdevAsciiGraph());
  setTimeout(() => log("📋 Mechanics Status:\n" + mechanicsProgress()), 100);
};

// Keyboard controls
document.addEventListener("keydown", e => {
  const k = e.key.toLowerCase();
  switch(k) {
    case "1": vm.switch("microbe"); setButtons("microbe"); break;
    case "2": vm.switch("colony"); setButtons("colony"); break;
    case "3": vm.switch("city"); setButtons("city"); break;
    case "4": vm.switch("planet"); setButtons("planet"); break;
    case "5": vm.switch("system"); setButtons("system"); break;
    case "6": vm.switch("space"); setButtons("space"); break;
    case " ": 
      State.paused = !State.paused; 
      log(State.paused ? "⏸ Paused" : "▶ Resumed"); 
      save(); 
      e.preventDefault();
      break;
    case "tab": 
      const order = ["microbe", "colony", "city", "planet", "system", "space"];
      const i = order.indexOf(State.stage);
      const n = order[(i + 1) % order.length] as any;
      vm.switch(n); 
      setButtons(n);
      e.preventDefault();
      break;
    case "g": 
      log("📊 Graph:\n" + chatdevAsciiGraph()); 
      break;
    // Movement for microbe view
    case "w": case "arrowup": 
      if(vm.current.name === "microbe") (vm.current as any).key(0, -1);
      break;
    case "s": case "arrowdown": 
      if(vm.current.name === "microbe") (vm.current as any).key(0, 1);
      break;
    case "a": case "arrowleft": 
      if(vm.current.name === "microbe") (vm.current as any).key(-1, 0);
      break;
    case "d": case "arrowright": 
      if(vm.current.name === "microbe") (vm.current as any).key(1, 0);
      break;
  }
});

// Touch controls for mobile
document.querySelectorAll<HTMLButtonElement>("#touch .padbtn").forEach(btn => {
  btn.onclick = () => {
    const d = btn.dataset.d;
    if(vm.current.name === "microbe") {
      const microbe = vm.current as any;
      if(d === "up") microbe.key(0, -1);
      if(d === "down") microbe.key(0, 1);
      if(d === "left") microbe.key(-1, 0);
      if(d === "right") microbe.key(1, 0);
      if(d === "act") {/* interact placeholder */}
    }
  };
});

// Main game loop
let last = performance.now();
function loop(now: number) {
  const dt = Math.max(1, Math.min(4, Math.round((now - last) / 16)));
  last = now;
  
  if(!State.paused) {
    State.t += dt;
    vm.update(dt);
  }
  
  vm.render();
  paintStatus();
  requestAnimationFrame(loop);
}

// Auto-save periodically
setInterval(save, 4000);

// Start the game loop
requestAnimationFrame(loop);

log("🎮 ΞNuSyQ SimulatedVerse initialized!");
log("🎯 Use 1-6 keys or click tabs to switch views");
log("🌀 Click 'Cascade' for intelligent task suggestions");
log("📊 Click 'ChatDev Viz' for system status");