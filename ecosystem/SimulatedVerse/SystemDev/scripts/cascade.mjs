import {execSync} from "node:child_process";
import {readFileSync, writeFileSync, mkdirSync} from "node:fs";

function run(cmd){ return execSync(cmd,{stdio:"pipe"}).toString().trim(); }
function safe(cmd){ try{ return run(cmd); }catch(e){ return ""; } }

mkdirSync("reports",{recursive:true});
const started = new Date().toISOString();

console.log("🌀 Cascade: Phase A (scans)");
safe("npm run scan:todos");
safe("npm run scan:dupes");
safe("npm run scan:imports");
safe("node scripts/cartograph.mjs");
safe("node scripts/scan-placeholders.mjs");
safe("node scripts/ui-index.mjs");

console.log("🧪 Cascade: Phase B (dry-run fixes)");
safe("npm run fix:imports"); // dry
safe("npm run fix:dupes");   // dry

console.log("📈 Cascade: Phase C (apply when safe)");
const importsPreview = JSON.parse(readFileSync("reports/fix_imports_preview.json","utf8"));
const dupesPreview   = JSON.parse(readFileSync("reports/fix_dupes_preview.json","utf8"));
const willApply = (importsPreview.length<=50 && dupesPreview.length<=50); // conservative

if(willApply){
  process.env.APPLY="1";
  safe("APPLY=1 npm run fix:imports");
  safe("APPLY=1 npm run fix:dupes");
  console.log("🔒 Committing batch");
  safe(`git add -A`);
  safe(`git commit -m "cascade: import/dupe repairs (batch) [culture-ship]"`);
} else {
  console.log("⚠️ Too many changes for auto-apply; leaving previews only.");
}

console.log("🎮 Cascade: Phase D (smoke)");
safe("npm run smoke:game");
safe("node scripts/ascii-smoke.mjs");
safe("node scripts/ship-bind.mjs");
safe("node scripts/idle-sim.mjs");

const finished = new Date().toISOString();
const report = {
  started, finished,
  importsPreviewCount: importsPreview.length,
  dupesPreviewCount: dupesPreview.length,
  applied: willApply
};
writeFileSync(`reports/cascade_${Date.now()}.json`, JSON.stringify(report,null,2));
console.log("✅ Cascade complete. See /reports/");