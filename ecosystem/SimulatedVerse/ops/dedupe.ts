#!/usr/bin/env tsx
import { createHash } from "node:crypto";
import { createReadStream, renameSync, mkdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { readdirSync } from "node:fs";

const ROOT=".";
const OUT="attic/duplicates";
const SKIP_DIRS=new Set(["node_modules",".git",".next","dist","build",".cache","coverage","models","ollama"]);

function* files(d:string):Generator<string>{
  for(const e of readdirSync(d)){ if(SKIP_DIRS.has(e)) continue;
    const p=join(d,e);
    try{ const s=statSync(p); if(s.isDirectory()) yield* files(p); else yield p; }catch{}
  }
}
function sha1(path:string):Promise<string>{
  return new Promise((res,rej)=>{
    const h=createHash("sha1"); const rs=createReadStream(path);
    rs.on("data",d=>h.update(d)); rs.on("error",rej); rs.on("end",()=>res(h.digest("hex")));
  });
}

const seen=new Map<string,string>(); // hash -> keptFile
let moved=0, bytes=0;
mkdirSync(OUT,{recursive:true});

(async()=>{
  for await (const f of files(ROOT)){
    const s=statSync(f); if(s.size<64) continue;                // ignore tiny
    const hash=await sha1(f);
    if(seen.has(hash)){
      const dest=join(OUT, f.replace(/[\/\\:]/g,"__"));
      try{ renameSync(f,dest); moved++; bytes+=s.size; }catch{}
    } else seen.set(hash,f);
  }
  console.log(`[dedupe] moved=${moved} totalMB=${(bytes/1e6).toFixed(2)} → ${OUT}`);
})();