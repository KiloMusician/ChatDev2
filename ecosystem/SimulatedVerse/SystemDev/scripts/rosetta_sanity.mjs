#!/usr/bin/env node
import fs from "fs"; import path from "path";
const SRC = "knowledge/rosetta/tiers.json";
if (!fs.existsSync(SRC)) { console.error("Missing tiers.json. Run scripts/rosetta_parse.mjs first."); process.exit(2); }
const data = JSON.parse(fs.readFileSync(SRC,"utf8"));
const tiers = data.tiers || [];
const issues = [];
// continuity
for (let i=1;i<tiers.length;i++){
  if (tiers[i].tier !== tiers[i-1].tier+1) issues.push({kind:"continuity", at: tiers[i].tier});
}
// uniqueness
const titleSet = new Set();
tiers.forEach(t=>{
  const key = `${t.tier}:${(t.title||"").toLowerCase()}`;
  if (titleSet.has(key)) issues.push({kind:"dup_title", tier:t.tier, title:t.title});
  titleSet.add(key);
  if (!t.development_insight) issues.push({kind:"missing_dev_insight", tier:t.tier});
  const slugs=(t.nodes||[]).map(n=>n.slug);
  const seen=new Set(); slugs.forEach(s=> { if (seen.has(s)) issues.push({kind:"dup_node_slug", tier:t.tier, slug:s}); seen.add(s); });
});

const receipt = {
  stage:"rosetta_sanity",
  timestamp:new Date().toISOString(),
  tiers: tiers.length,
  issues: issues,
  summary: {
    total: issues.length,
    kinds: issues.reduce((m,i)=>{m[i.kind]=(m[i.kind]||0)+1;return m;},{})
  }
};
if (!fs.existsSync("reports")) fs.mkdirSync("reports",{recursive:true});
fs.writeFileSync(`reports/rosetta_sanity_${ts()}.json`, JSON.stringify(receipt,null,2));

// also append a human list for next_up
if (issues.length){
  const lines = issues.slice(0,50).map(i=>`- [${i.kind}] tier:${i.tier}${i.title?` title:${i.title}`:""}${i.slug?` slug:${i.slug}`:""}`).join("\n");
  const hdr = `\n\n### Rosetta sanity hints (${new Date().toISOString()})\n${lines}\n`;
  const p="backlog/next_up/rosetta_fixups.md";
  const dir=path.dirname(p); if(!fs.existsSync(dir)) fs.mkdirSync(dir,{recursive:true});
  fs.appendFileSync(p, hdr);
  console.log(`Sanity wrote ${issues.length} issue(s). See ${p}`);
} else {
  console.log("Sanity clean ✓");
}

function ts(){
  const d=new Date(); const p=n=>String(n).padStart(2,"0");
  return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}