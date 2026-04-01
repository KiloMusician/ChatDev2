import {readFileSync, writeFileSync} from "node:fs";
import {dirname, resolve, extname} from "node:path";
import {globSync} from "glob";

const MODE = process.env.APPLY==="1" ? "apply" : "dry";
const issues = JSON.parse(readFileSync("reports/scan_imports.json","utf8"));
const allFiles = new Set(globSync("**/*.{ts,tsx,js,jsx,mjs,cjs}", {ignore:["**/node_modules/**","**/dist/**","**/.next/**","**/.git/**"]}));

function resolveCandidate(file, imp){
  const baseDir = dirname(file);
  const candidates = [
    `${imp}.ts`, `${imp}.tsx`, `${imp}.js`, `${imp}.jsx`, `${imp}.mjs`, `${imp}.cjs`,
    `${imp}/index.ts`, `${imp}/index.tsx`, `${imp}/index.js`, `${imp}/index.jsx`
  ].map(p=>resolve(baseDir,p));
  for(const c of candidates){
    const rel = c.replace(resolve("."),"").replace(/^\/+/,"");
    if(allFiles.has(rel)) return rel.startsWith(".")?rel:`./${rel}`;
  }
  return null;
}

let changed=0, reviewed=0;
const changes=[];
for(const it of issues){
  reviewed++;
  const {file, import:imp} = it;
  const src = readFileSync(file,"utf8");
  const cand = resolveCandidate(file, imp);
  if(!cand) continue;
  const newImp = cand.startsWith(".")?cand:("./"+cand);
  const next = src.replace(new RegExp(`(from\\s+['"])${imp}(['"];)|(require\\(['"])${imp}(['"]\\))`,"g"),
                           (m,a1,a2,b1,b2)=> a1?`${a1}${newImp}${a2}`:`${b1}${newImp}${b2}`);
  if(next!==src){
    changes.push({file, from: imp, to: newImp});
    if(MODE==="apply"){ writeFileSync(file,next,"utf8"); changed++; }
  }
}
writeFileSync("reports/fix_imports_preview.json", JSON.stringify(changes,null,2));
console.log(`🔧 fix:imports ${MODE} complete. Reviewed=${reviewed} Changed=${changed}`);
console.log("Preview saved to reports/fix_imports_preview.json");