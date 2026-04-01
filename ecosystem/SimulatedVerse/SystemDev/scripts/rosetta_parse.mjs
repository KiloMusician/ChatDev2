#!/usr/bin/env node
/**
 * RosettaStone Tier Parser (dependency-free)
 * - Finds the canonical tiers source
 * - Extracts: tier number, title, bracketed nodes, development insight block, and raw glyph
 * - Emits normalized JSON + minified JSON + receipt
 */
import fs from "fs"; import path from "path"; import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url); const __dirname = path.dirname(__filename);

const CANDIDATES = [
  "knowledge/tiers.md","docs/tiers.md","knowledge/rosetta/tiers.md",
  "docs/rosetta-tiers.md","Tiers.md","tiers.txt","rosetta-tiers.txt",
  "knowledge/RosettaStone.md"
];

function findSource(root=".") {
  for (const p of CANDIDATES) { if (fs.existsSync(p)) return p; }
  // fallback: grep-ish scan for "Tier <n>:" headings
  const files = walk(root).filter(f => /\.(md|txt)$/i.test(f));
  for (const f of files) {
    const head = fs.readFileSync(f, "utf8").slice(0, 150000);
    if (/^Tier\s+\d+:/m.test(head)) return f;
  }
  return null;
}
function walk(dir, list=[]) {
  for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
    if (e.name.startsWith(".git")) continue;
    const p = path.join(dir,e.name);
    if (e.isDirectory()) walk(p,list); else list.push(p);
  }
  return list;
}

function parse(content) {
  // Split by Tier sections: "Tier 1: Title\n ... (until next Tier N or EOF)"
  const re = /^Tier\s+(\d+):\s*([^\n]+)[\s\S]*?(?=^Tier\s+\d+:|$\n?)/gm;
  let m, sections = [];
  while ((m = re.exec(content)) !== null) {
    const [block, numStr, title] = m;
    const tier = Number(numStr);
    const body = block.replace(/^Tier\s+\d+:[^\n]*\n?/, "");
    // Development Insight block
    const diMatch = body.match(/Development Insight:\s*([\s\S]*?)\n(?=[A-Z][a-zA-Z ]+?:|^Tier|\Z)/m) ||
                    body.match(/Development Insight:\s*([\s\S]*?)$/m);
    const development_insight = (diMatch ? diMatch[1].trim() : "").replace(/\s+\n/g, "\n").trim();

    // Bracketed nodes like: [🛡⟂2₅: ⧉Defensive_Systems⟡₅]
    const nodes = [];
    const nb = body.match(/\[[^\]\n]{3,}\]/g) || [];
    for (const raw of nb) {
      const text = raw.slice(1,-1).trim();
      // try to split "X: Y", keep both raw + derived slug
      let label = text;
      const parts = text.split(":");
      if (parts.length >= 2) label = parts.slice(1).join(":").trim();
      // derive a readable slug like "defensive_systems"
      const ascii = label.normalize("NFKD").replace(/[^\p{Letter}\p{Number}\s_-]+/gu, " ").trim();
      const slug = ascii.toLowerCase().replace(/\s+/g,"_").replace(/__+/g,"_").slice(0,80) || "node";
      nodes.push({ raw, label, slug });
    }

    // Keep a small glyph sample (first dense non-Latin line)
    const glyph = (body.match(/[^\x00-\x7F]{4,}.+/) || [null])[0]?.trim() || "";

    sections.push({ tier, title: title.trim(), nodes, development_insight, glyph });
  }
  return sections.sort((a,b)=>a.tier-b.tier);
}

function ensureDir(p){ if(!fs.existsSync(p)) fs.mkdirSync(p,{recursive:true}); }

function main() {
  const t0 = Date.now();
  const src = findSource(".");
  if (!src) {
    console.error("No tiers source found.");
    process.exitCode = 2;
    return;
  }
  const raw = fs.readFileSync(src,"utf8");
  const tiers = parse(raw);

  ensureDir("knowledge/rosetta");
  const outPath = "knowledge/rosetta/tiers.json";
  fs.writeFileSync(outPath, JSON.stringify({ source: src, count: tiers.length, tiers }, null, 2));
  fs.writeFileSync("knowledge/rosetta/tiers.min.json", JSON.stringify({tiers}));

  // receipt
  ensureDir("reports");
  const receipt = {
    stage: "rosetta_parse",
    timestamp: new Date().toISOString(),
    source: src,
    size: raw.length,
    lines: raw.split(/\r?\n/).length,
    parsed_tiers: tiers.length,
    nodes_total: tiers.reduce((s,t)=>s+(t.nodes?.length||0),0),
    took_ms: Date.now()-t0,
    anomalies: collectAnomalies(tiers)
  };
  fs.writeFileSync(`reports/rosetta_parse_${ts()}.json`, JSON.stringify(receipt, null, 2));
  console.log(`Rosetta parsed: ${tiers.length} tiers, nodes=${receipt.nodes_total}`);
}
function collectAnomalies(list){
  const issues = [];
  const nums = list.map(t=>t.tier);
  for (let i=1;i<nums.length;i++){
    if (nums[i] !== nums[i-1]+1) issues.push({ kind:"gap_or_jump", at:list[i].tier, prev:list[i-1].tier });
  }
  list.forEach(t=>{
    if (!t.development_insight) issues.push({ kind:"missing_dev_insight", tier:t.tier });
    if ((t.nodes?.length||0)===0) issues.push({ kind:"no_nodes", tier:t.tier });
  });
  return issues;
}
function ts(){
  const d=new Date();
  const p=n=>String(n).padStart(2,"0");
  return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}
main();