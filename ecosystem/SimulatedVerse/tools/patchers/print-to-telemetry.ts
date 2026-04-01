#!/usr/bin/env tsx
/**
 * Print→Telemetry fixer:
 * - JS/TS: console.log(...) → logger.info({...}) + Msg⛛
 * - Py: print(...) → structured logger (fallback) + Msg⛛
 * - GDScript: print(...) → push_warning/push_error or signal emit
 */
import fs from "node:fs";
import path from "node:path";

const loggerJs = `import { log as __log } from "@/server/services/log"; import { emitMsg } from "@/server/services/msg";`;
const loggerPy = `import json, sys, time\nfrom nusyq_pylog import log\n`;
const loggerGd = `# uses Godot's push_* and custom Bus; see addons/nusyq_bus.gd`;

const patterns = [
  { lang:/\.(ts|tsx|js|jsx)$/i, re:/\bconsole\.log\((.*?)\);?/g, rep:(g1:string)=>`__log.info({ msg:${g1} }); emitMsg({ rune:"telemetry", data:${g1} })` },
  { lang:/\.py$/i, re:/\bprint\((.*?)\)\s*$/gm, rep:(g1:string)=>`log.info(${g1})  # structured\n# emit Msg⛛ via bridge if available` },
  { lang:/\.gd$/i, re:/\bprint\((.*?)\)\s*$/gm, rep:(g1:string)=>`push_warning(str(${g1}))  # TODO: route to nusyq_bus` }
];

function transform(file:string){
  const raw = fs.readFileSync(file,"utf8");
  const ext = path.extname(file).toLowerCase();
  let out = raw, changed=false;
  for(const p of patterns){
    if(p.lang.test(ext)){
      const before = out;
      out = out.replace(p.re, (_m,...args)=>p.rep(String(args[0])));
      if(out!==before) changed=true;
    }
  }
  if(!changed) return false;

  // Heuristic: inject logger import for TS/JS if not present
  if(/\.(ts|tsx|js|jsx)$/.test(ext) && !/server\/services\/log/.test(out)){
    const lines = out.split(/\r?\n/);
    lines.splice(0,0,loggerJs);
    out = lines.join("\n");
  }
  fs.writeFileSync(file,out);
  return true;
}

const file = process.argv[2];
if(!file){ console.error("usage: patchers/print-to-telemetry <file>"); process.exit(2); }
if(!fs.existsSync(file)){ console.error("no such file:", file); process.exit(2); }
const ok = transform(file);
console.log(JSON.stringify({ ok, file }));