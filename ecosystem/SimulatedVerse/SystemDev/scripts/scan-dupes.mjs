import {execSync} from "node:child_process";
import {createHash} from "node:crypto";
import {readdirSync, statSync, readFileSync, writeFileSync, mkdirSync} from "node:fs";
import {join} from "node:path";

const IGNORES = new Set(["node_modules",".git","dist",".next",".vercel",".cache"]);
const FILE_EXTS = new Set([".ts",".tsx",".js",".jsx",".json",".yml",".yaml",".md",".css",".scss",".mjs",".cjs",".py"]);

function* walk(dir){
  try {
    for (const f of readdirSync(dir)){ 
      if (IGNORES.has(f)) continue;
      const p = join(dir,f); 
      try {
        const s = statSync(p);
        if (s.isDirectory()) yield* walk(p); 
        else if (s.isFile()) yield p;
      } catch(e) {
        // Skip broken symlinks or permission issues
        continue;
      }
    }
  } catch(e) {
    // Skip directories we can't read
    return;
  }
}
function hash(buf){ return createHash("sha1").update(buf).digest("hex"); }

const map = new Map(); // hash -> [paths]
for (const p of walk(".")){
  const ext = p.slice(p.lastIndexOf("."));
  if (!FILE_EXTS.has(ext)) continue;
  const h = hash(readFileSync(p));
  if (!map.has(h)) map.set(h, []);
  map.get(h).push(p);
}
const dupes = [...map.entries()].filter(([,arr])=>arr.length>1);
mkdirSync("reports",{recursive:true});
writeFileSync("reports/scan_dupes.json", JSON.stringify(dupes, null, 2));
console.log(`✅ Duplicate scan: ${dupes.length} groups found`);