#!/usr/bin/env tsx
import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

type Row = { path: string; bytes: number; ext: string; group: string };

const ROOT = process.argv[2] || ".";
const SKIP_DIRS = new Set([
  "node_modules",".git",".next","dist","build",".cache","coverage","logs",
  ".ipynb_checkpoints","__pycache__","reports/raw","artifacts","models","ollama"
]);

const GROUPS: [string, RegExp][] = [
  ["code", /\.(ts|tsx|js|jsx|py|rs|go|java|cs|cpp|c|gd|yaml|yml|json|toml|ini)$/i],
  ["docs", /\.(md|rtf|txt|rst)$/i],
  ["assets", /\.(png|jpg|jpeg|gif|svg|webp|mp3|wav|mp4|glb|gltf|ttf|otf)$/i],
  ["logs", /\.(log|out|err)$/i],
  ["archives", /\.(zip|gz|tar|tgz)$/i],
];

function groupOf(file: string) {
  for (const [g, rx] of GROUPS) if (rx.test(file)) return g;
  return "other";
}

function* walk(dir: string): Generator<string> {
  for (const e of readdirSync(dir)) {
    if (SKIP_DIRS.has(e)) continue;
    const p = join(dir, e);
    try {
      const st = statSync(p);
      if (st.isDirectory()) yield* walk(p);
      else yield p;
    } catch {
      // skip broken symlinks or inaccessible files
      continue;
    }
  }
}

let total = 0, count = 0;
const buckets = new Map<string, { files: number; bytes: number }>();
const biggest: Row[] = [];

for (const file of walk(ROOT)) {
  const st = statSync(file);
  const ext = (file.split(".").pop() || "").toLowerCase();
  const g = groupOf(file);
  total += st.size; count++;
  const b = buckets.get(g) ?? { files: 0, bytes: 0 };
  b.files++; b.bytes += st.size; buckets.set(g, b);

  if (biggest.length < 100) {
    biggest.push({ path: file, bytes: st.size, ext, group: g });
    biggest.sort((a,b)=>b.bytes-a.bytes);
  } else if (st.size > biggest[biggest.length-1].bytes) {
    biggest[biggest.length-1] = { path:file, bytes:st.size, ext, group:g };
    biggest.sort((a,b)=>b.bytes-a.bytes);
  }
}

console.log("== Repo Inventory ==");
console.table([...buckets.entries()].map(([g,v])=>({group:g,...v, mb:+(v.bytes/1e6).toFixed(2)})));
console.log(`Files: ${count}, Size: ${(total/1e6).toFixed(2)} MB`);
console.log("== Top 100 largest files (skip dirs excluded) ==");
console.table(biggest.map(r=>({mb:+(r.bytes/1e6).toFixed(2), group:r.group, path:r.path})));