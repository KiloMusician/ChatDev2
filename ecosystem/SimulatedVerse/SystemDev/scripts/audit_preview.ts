#!/usr/bin/env tsx
/**
 * Quadpartite Preview Auditor
 * - Scans repo for entrypoints (web/mobile/huds/storyboards + godot exports)
 * - Detects conflicts (multiple index.html, overlapping static roots, stale SW)
 * - Emits receipts + a prioritized switch plan (no writes outside SystemDev)
 */
import fs from "node:fs";
import path from "node:path";

type Finding = { type:string; file:string; note?:string; };
type Entrypoint = {
  kind: "web"|"mobile"|"hud"|"storybook"|"godot"|"static";
  root: string;
  index?: string;
  scriptHints: string[];
  weight: number; // higher wins
};

const ROOT = process.cwd();
const outDir = "SystemDev/reports";
fs.mkdirSync(outDir, { recursive: true });

const globs = [
  ["web",      ["PreviewUI/web","src/web","apps/web","packages/web","docs","public","site"]],
  ["mobile",   ["PreviewUI/mobile","apps/mobile","packages/mobile","expo","native"]],
  ["hud",      ["PreviewUI/huds"]],
  ["storybook",["PreviewUI/storyboards",".storybook","stories"]],
  ["godot",    ["GameDev/engine/godot","GameDev/engine/godot/export","GameDev/engine/godot/exports"]],
  ["static",   ["dist","build","out","static","public","docs"]],
] as const;

const hints = [
  /vite|next|nuxt|astro|svelte|remix|expo|react-native|storyboard|storybook/i,
  /godot|export|pck|gdscript/i,
  /serve|http-server|live-server|webpack-dev-server/i
];

function exists(p:string){ try{ return fs.existsSync(p); }catch{ return false; } }
function isDir(p:string){ try{ return exists(p)&&fs.statSync(p).isDirectory(); }catch{ return false; } }
function walk(dir:string, out:string[]=[]){
  const s = fs.readdirSync(dir,{withFileTypes:true});
  for(const d of s){
    const p=path.join(dir,d.name);
    if(d.isDirectory()){
      if(d.name==="node_modules"||d.name===".git") continue;
      out.push(p+"/"); walk(p,out);
    } else out.push(p);
  } return out;
}

function weightFor(kind:Entrypoint["kind"]){
  switch(kind){
    case "web": return 100;
    case "hud": return 80;
    case "storybook": return 70;
    case "mobile": return 60;
    case "godot": return 50;
    case "static": return 40;
    default: return 10;
  }
}

const findings: Finding[] = [];
const entrypoints: Entrypoint[] = [];

for (const [kind, roots] of globs){
  for (const r of roots){
    const abs = path.join(ROOT, r);
    if(!exists(abs)) continue;
    // look for index.html / godot exports / package scripts
    let indexCandidate:string|undefined;
    const files = isDir(abs) ? walk(abs).slice(0, 4000) : [];
    for (const f of files){
      const name = path.basename(f).toLowerCase();
      if (name==="index.html"||name==="index.htm") indexCandidate=f;
      if (/serviceworker|workbox|sw\./i.test(f)) {
        findings.push({type:"service_worker", file:f, note:"SW present – may cache old UI"});
      }
    }
    // script hints
    const scriptHints:string[] = [];
    try{
      const pkg = JSON.parse(fs.readFileSync("package.json","utf8"));
      const scripts = pkg?.scripts ? Object.values<string>(pkg.scripts) : [];
      for (const s of scripts){
        if (hints.some(h=>h.test(String(s)))) scriptHints.push(String(s));
      }
    }catch{}

    entrypoints.push({
      kind: kind as Entrypoint["kind"],
      root: r,
      index: indexCandidate,
      scriptHints,
      weight: weightFor(kind as Entrypoint["kind"]),
    });
  }
}

// conflict detection: multiple indices with higher/equal weight
const indices = entrypoints.filter(e=>e.index);
const byName = new Map<string, Entrypoint[]>();
for (const e of indices){
  const name = path.basename(e.index!);
  const arr = byName.get(name) ?? [];
  arr.push(e); byName.set(name, arr);
}
for (const [name, arr] of byName){
  if (arr.length>1){
    arr.sort((a,b)=>b.weight-a.weight);
    const winners = arr.filter(a=>a.weight===arr[0].weight);
    if (winners.length>1){
      findings.push({
        type:"index_conflict",
        file: name,
        note: `Same priority across: ${arr.map(a=>`${a.kind}:${a.root}`).join(" | ")}`
      });
    } else {
      findings.push({
        type:"index_shadowing",
        file: path.join(arr[0].root,name),
        note: `Higher-priority ${arr[0].kind} shadows ${arr.slice(1).map(a=>a.root).join(", ")}`
      });
    }
  }
}

// .replit / replit.nix alignment
try{
  const replitCfg = fs.readFileSync(".replit","utf8");
  findings.push({type:"replit_config", file:".replit", note: replitCfg.split("\n").slice(0,6).join("\\n")});
}catch{}
try{
  const nix = fs.readFileSync("replit.nix","utf8");
  findings.push({type:"replit_nix", file:"replit.nix", note: nix.split("\n").slice(0,8).join("\\n")});
}catch{}

const report = {
  stage: "preview_audit",
  timestamp: new Date().toISOString(),
  entrypoints,
  conflicts: findings.filter(f=>/conflict|shadow/.test(f.type)),
  service_workers: findings.filter(f=>f.type==="service_worker"),
  replit: findings.filter(f=>/^replit_/.test(f.type)),
  recommendation: (() => {
    const sorted = [...entrypoints].sort((a,b)=>b.weight-a.weight);
    const best = sorted.find(e=>e.index) ?? sorted[0];
    return {
      preferred: best,
      envSwitch: {
        var: "PREVIEW_FLAVOR",
        value: `${best.kind}:${best.root}`,
        note: "Use switcher middleware to serve from this root without moving files."
      }
    };
  })()
};

const out = path.join(outDir, `preview_audit_${Date.now()}.json`);
fs.writeFileSync(out, JSON.stringify(report,null,2));
console.log("Wrote", out);