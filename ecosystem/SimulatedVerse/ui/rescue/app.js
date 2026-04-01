const API = (p)=>fetch(p, {headers:{"Content-Type":"application/json"}});
const qs = (s)=>document.querySelector(s);

const ascii = qs("#ascii");
const ctx = ascii.getContext("2d");
let anim=true, grid=false, theme="matrix", t=0, cols=120, rows=24;
let snd= null;

function resize(){
  const ratio = window.devicePixelRatio || 1;
  const w = ascii.clientWidth|0;
  const h = ascii.clientHeight|0;
  ascii.width = w*ratio; ascii.height = h*ratio;
  ctx.setTransform(ratio,0,0,ratio,0,0);
  ctx.font = "16px " + getComputedStyle(document.documentElement).getPropertyValue("--mono");
  ctx.textBaseline = "top";
}
window.addEventListener("resize", resize); resize();

function rnd(a,b){ return a + Math.random()*(b-a); }
function colorForTheme(ch){
  switch(theme){
    case "matrix": return `hsl(${rnd(110,140)},90%,${rnd(55,75)}%)`;
    case "amber": return `hsl(35,90%,${rnd(60,75)}%)`;
    case "cogmind": return `hsl(${rnd(105,125)},70%,${rnd(55,70)}%)`;
    default: return `hsl(210,10%,${rnd(70,90)}%)`;
  }
}

function drawGrid(){
  ctx.strokeStyle = "rgba(255,255,255,.06)";
  const cw = ctx.measureText("M").width*0.6 + 6;
  const ch = 18;
  for(let x=0;x<ascii.width;x+=cw) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x, ascii.height); ctx.stroke(); }
  for(let y=0;y<ascii.height;y+=ch){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(ascii.width,y); ctx.stroke(); }
}
function drawAsciiFrame(){
  ctx.clearRect(0,0,ascii.width,ascii.height);
  if(grid) drawGrid();
  const charSet = " .,:;+*?%$#@ΞΣΦΩΔ";
  const cw = 9, ch = 18;
  cols = Math.floor(ascii.width / cw);
  rows = Math.floor(ascii.height / ch);
  for(let y=0;y<rows;y++){
    for(let x=0;x<cols;x++){
      const n = Math.sin((x+t*0.09)*0.22 + (y-t*0.05)*0.13)*0.5 + 0.5;
      const idx = Math.floor(n*(charSet.length-1));
      const ch = charSet[idx];
      ctx.fillStyle = colorForTheme(ch);
      ctx.fillText(ch, x*cw, y*ch);
    }
  }
  t++;
}

let raf=null;
function loop(){ if(anim){ drawAsciiFrame(); raf = requestAnimationFrame(loop); } }
loop();

function beep(){
  if(snd) { snd.stop && snd.stop(); snd=null; return; }
  try{
    const a = new AudioContext();
    const o = a.createOscillator();
    const g = a.createGain();
    o.type="sawtooth"; o.frequency.value = 220;
    o.connect(g); g.connect(a.destination);
    g.gain.value=.03; o.start();
    setTimeout(()=>{ o.stop(); a.close(); }, 160);
    snd = o;
  }catch{}
}

async function refreshHUD(){
  const r = await API("/api/hud"); const d = await r.json();
  qs("#hud-health").textContent = `health: ${d.health}`;
  qs("#hud-msg").textContent = `font: ${d.ascii?.fontStack || "mono"}`;
}
async function refreshTasks(){
  const r = await API("/api/tasks"); const d = await r.json();
  const ul = qs("#tasks"); ul.innerHTML = "";
  for(const it of d.tasks.slice(-18)){
    const li = document.createElement("li");
    li.textContent = `[${new Date(it.ts).toLocaleTimeString()}] (${it.priority}) ${it.type} — ${it.note}`;
    ul.appendChild(li);
  }
}

qs("#btn-cascade").addEventListener("click", async ()=>{
  qs("#hud-msg").textContent = "running cascade…";
  await API("/api/run/cascade");
  qs("#hud-msg").textContent = "cascade finished (see reports/)";
  beep(); refreshTasks(); refreshHUD();
});
qs("#btn-smoke").addEventListener("click", async ()=>{
  qs("#hud-msg").textContent = "smoke test…";
  await API("/api/run/smoke");
  qs("#hud-msg").textContent = "smoke done";
  refreshHUD();
});
qs("#btn-enqueue").addEventListener("click", async ()=>{
  const note = prompt("Brief task note?");
  if(!note) return;
  await fetch("/api/enqueue", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({
    type:"surgical-edit", priority:5, note, payload:{ scope:"ui/rescue" }
  })});
  refreshTasks();
});
qs("#btn-sound").addEventListener("click", ()=>beep());
qs("#btn-full").addEventListener("click", ()=>document.documentElement.requestFullscreen?.());

qs("#tick-anim").addEventListener("change", (e)=>{ anim = e.target.checked; if(anim && !raf) loop(); else cancelAnimationFrame(raf); });
qs("#tick-grid").addEventListener("change", (e)=> grid = e.target.checked);
qs("#sel-theme").addEventListener("change", (e)=> theme = e.target.value);

qs("#btn-new").addEventListener("click", ()=> { qs("#hud-msg").textContent="(new game) boot sequence… UI unlocks will appear as you progress."; });
qs("#btn-load").addEventListener("click", ()=> { qs("#hud-msg").textContent="(load) not implemented yet — enqueue a task to implement save/load."; });
qs("#btn-settings").addEventListener("click", ()=> { alert("Settings: coming online — add mobile/desktop toggles, font size, theme") });
qs("#btn-temple").addEventListener("click", ()=> { window.open("/ui/rescue/index.html#temple","_self"); });

setInterval(refreshTasks, 2000);
refreshHUD(); refreshTasks();