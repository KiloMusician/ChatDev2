#!/usr/bin/env node
import { readdirSync, statSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, extname } from "node:path";

const IGNORES = new Set(["node_modules",".git","dist",".next",".cache",".vercel","build"]);
const CODE_EXT = new Set([".ts",".tsx",".js",".jsx",".mjs",".cjs",".py",".rs",".go",".cs",".json",".yml",".yaml",".md",".css",".scss",".svelte",".vue",".gd",".ipynb"]);
const HINTS = {
  system: [/^modules\/culture_ship|^scripts\/|^config\/|^tools\/|^infra\/|temples?|cicd|pipeline/i],
  game: [/^src\/game|^assets\/(tiles|ascii|maps)|rogue|dungeon|combat|inventory|quests|lore/i],
  hybrid: [/^src\/(hud|ui|app|routes)|interface|bridge|adapter|services/i]
};

function* walk(d="."){ 
  for (const n of readdirSync(d)){ 
    if(IGNORES.has(n)) continue;
    const p=join(d,n), s=statSync(p); 
    if(s.isDirectory()) yield* walk(p);
    else if(CODE_EXT.has(extname(p))) yield p; 
  } 
}

function classify(path){
  const hit = (k)=>HINTS[k].some(r=>r.test(path));
  if(hit("system") && hit("game")) return "hybrid";
  if(hit("system")) return "system";
  if(hit("game")) return "game";
  if(hit("hybrid")) return "hybrid";
  // fallback by content
  const body = readFileSync(path,"utf8").slice(0,3000);
  const sys = /(pipeline|cascade|temple|ship|orchestrator|telemetry|lint|eslint|tsconfig|ci)/i.test(body);
  const gam = /(entity|sprite|rogue|mapgen|biome|craft|quest|hud|ascii)/i.test(body);
  if(sys && gam) return "hybrid";
  if(sys) return "system";
  if(gam) return "game";
  return "hybrid"; // neutral default routes to hybrid
}

const rows=[];
for(const f of walk(".")){
  rows.push({ file:f, type: classify(f) });
}
mkdirSync("reports",{recursive:true});
writeFileSync("reports/cartograph.json", JSON.stringify(rows,null,2));
console.log(`🗺️ Cartograph complete: ${rows.length} files. Breakdown:`,
  rows.reduce((a,{type})=>(a[type]=(a[type]||0)+1,a),{}));