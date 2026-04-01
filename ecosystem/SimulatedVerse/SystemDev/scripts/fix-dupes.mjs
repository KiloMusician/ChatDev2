import {readFileSync, writeFileSync, unlinkSync} from "node:fs";
import {dirname, basename} from "node:path";

const MODE = process.env.APPLY==="1" ? "apply" : "dry";
const groups = JSON.parse(readFileSync("reports/scan_dupes.json","utf8"));
const actions=[];
for(const [,paths] of groups){
  // keep the longest path (most contextual), clean empty exact duplicates
  const keep = paths.sort((a,b)=>b.length-a.length)[0];
  for(const p of paths){
    if(p===keep) continue;
    const body = readFileSync(p,"utf8").trim();
    if(body===""){
      actions.push({remove:p, reason:"empty duplicate", keep});
      if(MODE==="apply"){ unlinkSync(p); }
    }
  }
}
writeFileSync("reports/fix_dupes_preview.json",JSON.stringify(actions,null,2));
console.log(`🧹 fix:dupes ${MODE} complete. Planned actions: ${actions.length}`);