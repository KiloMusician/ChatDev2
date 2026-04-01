// Strong shell: tiny no-dep API server that fronts local scripts & task queue.
import http from "node:http";
import {exec} from "node:child_process";
import {readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync} from "node:fs";
import {join} from "node:path";

const PORT = process.env.PORT ? Number(process.env.PORT) : 3030;
const TASKS = "tasks";
const REPORTS = "reports";

function json(res, code, data){
  res.writeHead(code, {"Content-Type":"application/json", "Access-Control-Allow-Origin":"*"});
  res.end(JSON.stringify(data));
}
function ok(res, data={ok:true}){ json(res, 200, data); }
function bad(res, msg="bad request"){ json(res, 400, {ok:false, error: msg}); }
function run(cmd){
  return new Promise((resolve)=>exec(cmd, {timeout: 10*60*1000}, (err, stdout, stderr)=>{
    resolve({err: !!err, code: err?.code ?? 0, stdout, stderr});
  }));
}

try{ mkdirSync(TASKS, {recursive:true}); }catch{}
try{ mkdirSync(REPORTS, {recursive:true}); }catch{}

function readTasks(){
  const files = readdirSync(TASKS).filter(f=>f.endsWith(".json"));
  const all = [];
  for(const f of files){
    try{ all.push(JSON.parse(readFileSync(join(TASKS,f),"utf8"))); }catch{}
  }
  return all.sort((a,b)=> (a.ts||0)-(b.ts||0));
}

async function handle(req, res){
  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;

  // CORS preflight
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin":"*",
      "Access-Control-Allow-Methods":"GET,POST,OPTIONS",
      "Access-Control-Allow-Headers":"Content-Type"
    });
    return res.end();
  }

  if (path === "/api/health"){
    return ok(res, {ok:true, ts: Date.now(), routes:["/api/health","/api/tasks","/api/enqueue","/api/run/cascade","/api/run/smoke","/api/hud"]});
  }

  if (path === "/api/tasks"){
    return ok(res, {tasks: readTasks()});
  }

  if (path === "/api/enqueue" && req.method === "POST"){
    let body=""; req.on("data",(c)=>body+=c.toString());
    req.on("end", ()=>{
      try{
        const data = JSON.parse(body||"{}");
        const item = {
          id: `task_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          ts: Date.now(),
          type: data.type || "surgical-edit",
          payload: data.payload || {},
          priority: data.priority ?? 5,
          note: data.note || "queued via rescue UI"
        };
        const path = join(TASKS, `${item.id}.json`);
        writeFileSync(path, JSON.stringify(item,null,2));
        ok(res, {queued: item.id});
      }catch(e){ bad(res, e.message); }
    });
    return;
  }

  if (path === "/api/run/cascade"){
    const start = Date.now();
    const result = await run("npm run cascade");
    const entry = {
      kind: "cascade",
      at: new Date().toISOString(),
      ms: Date.now()-start,
      code: result.code,
      stdout: result.stdout.slice(-64000),
      stderr: result.stderr.slice(-64000)
    };
    writeFileSync(join(REPORTS, `devshell_cascade_${Date.now()}.json`), JSON.stringify(entry,null,2));
    return ok(res, {ok:true, summary: {ms: entry.ms, code: entry.code}});
  }

  if (path === "/api/run/smoke"){
    const start = Date.now();
    const result = await run("npm run smoke:game");
    const entry = {
      kind: "smoke",
      at: new Date().toISOString(),
      ms: Date.now()-start,
      code: result.code,
      stdout: result.stdout.slice(-64000),
      stderr: result.stderr.slice(-64000)
    };
    writeFileSync(join(REPORTS, `devshell_smoke_${Date.now()}.json`), JSON.stringify(entry,null,2));
    return ok(res, {ok:true, summary: {ms: entry.ms, code: entry.code}});
  }

  if (path === "/api/hud"){
    // Minimal HUD state; expand to include health, cascade counts, temple unlocks, etc.
    const hud = {
      title: "ΞNuSyQ — Rescue HUD",
      health: "degraded", // will improve as cascades pass
      buttons: ["Big Red Button (Cascade)", "Smoke Test", "Enqueue"],
      ascii: {fontStack: "'JetBrains Mono','Fira Code','Noto Sans Mono',monospace", cell: {w: 9, h: 18}}
    };
    return ok(res, hud);
  }

  // Serve UI files (super simple)
  if (path === "/" || path.startsWith("/ui")){
    const file = path === "/" ? "ui/rescue/index.html" : path.slice(1);
    try{
      const body = readFileSync(file);
      res.writeHead(200, {"Content-Type": file.endsWith(".css")?"text/css" : file.endsWith(".js")?"text/javascript":"text/html"});
      return res.end(body);
    }catch(e){
      res.writeHead(404); return res.end("Not found");
    }
  }

  res.writeHead(404); res.end("Not found");
}

http.createServer(handle).listen(PORT, ()=>{
  console.log(`🛡️  DevShell up on http://localhost:${PORT}`);
  console.log("Routes: /api/health /api/tasks /api/enqueue /api/run/cascade /api/run/smoke /api/hud");
  console.log("UI:     /  (rescue dashboard)");
});