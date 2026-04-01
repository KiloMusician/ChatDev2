#!/usr/bin/env tsx
/**
 * Fixed shebang placement and removed problematic imports
 */
/**
 * NuSyQ Repo Scanner
 * - Walks tree (respecting ignore)
 * - Scores "placeholder smell"
 * - Emits JSON, CSV, NDJSON task hints
 * - Detects dup file names, broken imports, empty/near-empty files
 */
import fs from "node:fs";
import path from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

type FileInfo = {
  path: string; bytes: number; lines: number; lang: string;
  smells: string[]; score: number; mtime: number;
};

const config = JSON.parse(fs.readFileSync("ops/repo-scan.config.json","utf8"));
const IGNORES = (config.ignore||[]).map((p:string)=> new RegExp("^"+p.replace("**",".*").replace("*","[^/]*")+"$"));
const INCLUDE = (config.include||[]).map((p:string)=> new RegExp("^"+p.replace("**",".*").replace("*","[^/]*")+"$"));

function shouldSkip(p:string){ return IGNORES.some(r=>r.test(p)); }
function shouldTake(p:string){ return INCLUDE.some(r=>r.test(p)); }

const smells = [
  { id:"fake-print", r:/(console\.log|print\(|echo\s+['"].*(active|ok|ready|✅|working)['"])/i, w:15 },
  { id:"todo-fixme", r:/\b(TODO|FIXME|HACK|XXX)\b/, w:8 },
  { id:"not-impl", r:/NotImplementedError|throw\s+new\s+Error\(["']not implemented|pass\s*#\s*stub/i, w:12 },
  { id:"empty-file", r:/^$/m, w:20 }, // checked separately by size/lines too
  { id:"dead-return", r:/return\s+(true|false|null|undefined)\s*;?\s*\/\/\s*stub/i, w:10 },
  { id:"print-banner", r:/^#{3,}|^[-=]{5,}/m, w:3 },
  { id:"placeholder-text", r:/lorem ipsum|placeholder|foo|bar/i, w:6 }
];

const langs: Record<string,string> = {
  ".ts":"ts",".tsx":"tsx",".js":"js",".jsx":"jsx",".py":"py",".md":"md",".gd":"gd",".json":"json",".yaml":"yaml",".yml":"yaml",".toml":"toml"
};

const files: FileInfo[] = [];
function walk(dir:string){
  for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
    const p = path.join(dir, entry.name);
    const norm = p.replace(/\\/g,"/");
    if(shouldSkip(norm)) continue;
    if(entry.isDirectory()){ walk(p); continue; }
    if(!shouldTake(norm)) continue;

    const stat = fs.statSync(p);
    const ext = path.extname(p).toLowerCase();
    const lang = langs[ext] || "other";
    const raw = fs.readFileSync(p,"utf8");
    const lineCount = raw.split(/\r?\n/).length;
    let score = 0; const matches:string[] = [];
    if(stat.size < 4 || lineCount <= 1){ score += 25; matches.push("empty/trivial"); }
    for(const s of smells){
      if(s.r.test(raw)){ score += s.w; matches.push(s.id); }
    }
    files.push({ path:norm, bytes: stat.size, lines: lineCount, lang, smells: matches, score, mtime: stat.mtimeMs });
  }
}
walk(config.root);

// Duplicate base names (risk of "README.md" collisions across dirs)
const byName = new Map<string,string[]>();
for(const f of files){
  const base = path.basename(f.path);
  byName.set(base, [...(byName.get(base)||[]), f.path]);
}
const dups = [...byName.entries()].filter(([_,arr])=>arr.length>1);

// Broken imports (lightweight): only JS/TS — look for local relative imports that don't exist
const importMisses: string[] = [];
for(const f of files.filter(x=>x.lang==="ts"||x.lang==="tsx"||x.lang==="js"||x.lang==="jsx")){
  const raw = fs.readFileSync(f.path,"utf8");
  const re = /from\s+["'](\.\/[^"']+|\.{2}\/[^"']+)["']/g;
  let m:RegExpExecArray|null;
  while((m=re.exec(raw))){
    const rel = m[1];
    const abs = path.resolve(path.dirname(f.path), rel);
    const exists = [".ts",".tsx",".js",".jsx",".json","/index.ts","/index.tsx","/index.js","/index.jsx"].some(s=>fs.existsSync(abs+s)||fs.existsSync(abs));
    if(!exists) importMisses.push(`${f.path} -> ${rel}`);
  }
}

// Output
fs.mkdirSync("data/_scan", { recursive: true });
fs.writeFileSync("data/_scan/repo_map.json", JSON.stringify({ files, duplicates: dups }, null, 2));
fs.writeFileSync("data/_scan/import_misses.json", JSON.stringify(importMisses, null, 2));
fs.writeFileSync("data/_scan/repo_map.csv", [
  "path,lang,bytes,lines,score,smells",
  ...files.map(f=>[
    JSON.stringify(f.path),f.lang,f.bytes,f.lines,f.score,JSON.stringify(f.smells.join("|"))
  ].join(","))
].join("\n"));

// NDJSON PUs (only for worst offenders)
const offenders = files.filter(f=>f.score>=20).sort((a,b)=>b.score-a.score).slice(0,300);
const ndjson = offenders.map((f,i)=>({
  id: `RSWEEP-${i+1}`,
  phase: "foundational",
  type: "RefactorPU",
  priority: f.score > 40 ? "critical":"high",
  title: `Refactor placeholder/print in ${f.path} (score ${f.score})`,
  meta: { smells: f.smells, bytes: f.bytes, lines: f.lines, lang: f.lang },
  plan: { patcher: "print-to-telemetry", file: f.path }
}));
fs.writeFileSync("data/_scan/refactor_sweep.ndjson", ndjson.map(o=>JSON.stringify(o)).join("\n"));
__log.info({ msg:`[RepoScan] files=${files.length} offenders=${offenders.length} dups=${dups.length} importMisses=${importMisses.length}` }); emitMsg({ rune:"telemetry", data:`[RepoScan] files=${files.length} offenders=${offenders.length} dups=${dups.length} importMisses=${importMisses.length}` })