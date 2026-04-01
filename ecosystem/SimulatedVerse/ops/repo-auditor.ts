#!/usr/bin/env tsx
/**
 * Repo Auditor — scans the workspace, scores usefulness/duplication/spam,
 * detects "abilities", and emits reports + a safe anneal move plan.
 * Non-destructive. Designed for large repos; no heavy deps.
 */
import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

type Cfg = {
  root: string;
  ignoreGlobs: string[];
  maxFileBytes: number;
  minConsiderBytes: number;
  dupNearJaccard: number;
  spam: { placeholderWords: string[]; maxRepeatLineRatio: number; minTextLines: number; };
  weights: { util: number; dup: number; spam: number; };
  atticDir: string;
  abilityMarkers: Record<string, string[]>;
};
const cfg: Cfg = JSON.parse(fs.readFileSync("ops/repo-auditor.config.json","utf8"));

const START = Date.now();
const isBinary = (buf: Buffer) => {
  const slice = buf.subarray(0, 8000);
  let suspicious = 0;
  for (const b of slice) if (b === 0) { suspicious++; if (suspicious > 1) return true; }
  return false;
};

const normWS = (s: string) => s.replace(/\r/g,"").trim();
const sha1 = (b: Buffer) => crypto.createHash("sha1").update(b).digest("hex");
const ext = (p: string) => path.extname(p).toLowerCase();
const within = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

const igGlobs = cfg.ignoreGlobs.map(g => {
  // very light glob-ish: we just skip if path includes segment prefix
  const norm = g.replace("/**","").replace("**/","").replace("**","");
  return norm.startsWith("/") ? norm.slice(1) : norm;
});

const shouldIgnore = (rel: string) =>
  igGlobs.some(g => rel.startsWith(g)) ||
  rel.includes(`${path.sep}${cfg.atticDir}${path.sep}`);

type FileInfo = {
  rel: string;
  size: number;
  sha1: string;
  text?: string;
  isText: boolean;
  utilScore: number;
  spamScore: number;
  dupKey: string;     // exact dup
  softSig: string;    // near-dup signature
  ability: string[];  // tags
  class: "system"|"ui"|"simulation"|"knowledge";
};
const files: FileInfo[] = [];

// Use signal-only scanning instead of filesystem walk
async function scanSignalFiles() {
  // Import signal files from repo-targets.yaml
  const { execa } = await import("execa");
  let signalFiles: string[];
  
  try {
    // Use ops/only-repo.ts for authoritative signal set
    const { stdout } = await execa("tsx", ["ops/only-repo.ts"]);
    signalFiles = stdout.split("\n").filter(Boolean);
  } catch (error) {
    console.warn("Falling back to git ls-files:", error.message);
    // Fallback to git tracked files
    const { stdout } = await execa("git", ["ls-files"]);
    signalFiles = stdout.split("\n").filter(Boolean);
  }
  
  console.log(`[AUDITOR] Scanning ${signalFiles.length} signal files (vendor noise excluded)`);
  
  for (const rel of signalFiles) {
    const p = path.resolve(rel);
    try {
      const st = await fsp.stat(p);
      if (st.size > cfg.maxFileBytes) continue;
      if (st.size < cfg.minConsiderBytes) continue;

      const buf = await fsp.readFile(p);
      const bin = isBinary(buf);
      let text = "";
      if (!bin) {
        // rough cap to keep memory sane
        text = buf.length > 800_000 ? buf.subarray(0, 800_000).toString("utf8") : buf.toString("utf8");
      }
      const info: FileInfo = {
        rel,
        size: st.size,
        sha1: sha1(buf),
        text: bin ? undefined : normWS(text),
        isText: !bin,
        utilScore: 0,
        spamScore: 0,
        dupKey: sha1(buf),
        softSig: "",
        ability: [],
        class: classifyByPath(rel)
      };
      score(info);
      files.push(info);
    } catch {}
  }
}

function classifyByPath(rel: string): FileInfo["class"] {
  const p = rel.replace(/\\/g,"/");
  if (p.startsWith("apps/web/src/pages/Game/Simulation") || /simulation|sim\//i.test(p)) return "simulation";
  if (p.startsWith("apps/web") || /ui|client|frontend|react/i.test(p)) return "ui";
  if (p.startsWith("packages") || p.startsWith("ops") || /server|api|council|agent|bus/i.test(p)) return "system";
  return "knowledge";
}

function textTokens(s: string) {
  return s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").split(/\s+/).filter(Boolean);
}

function jaccard(a: Set<string>, b: Set<string>) {
  const inter = [...a].filter(x => b.has(x)).length;
  const uni = a.size + b.size - inter;
  return uni === 0 ? 0 : inter / uni;
}

function buildSoftSig(s: string) {
  // strip noise words, keep top tokens for near-dup
  const toks = textTokens(s).filter(t => t.length > 2 && !STOP.has(t));
  const freq = new Map<string, number>();
  for (const t of toks) freq.set(t, (freq.get(t)||0)+1);
  const top = [...freq.entries()].sort((a,b)=>b[1]-a[1]).slice(0, 80).map(x=>x[0]);
  return top.join("|");
}
const STOP = new Set<string>(["the","and","for","with","from","that","this","have","into","your","you","are","not","use","using","used","file","code","data","json"]);

function detectAbilityTags(txt?: string) {
  if (!txt) return [];
  const tags: string[] = [];
  for (const [k, needles] of Object.entries(cfg.abilityMarkers)) {
    if (needles.some(n => txt.includes(n))) tags.push(k);
  }
  return tags;
}

function score(f: FileInfo) {
  if (f.isText && f.text) {
    f.softSig = buildSoftSig(f.text);
    f.ability = detectAbilityTags(f.text);
    // util score: code-ish contents + abilities + known markers
    let util = 0;
    if (/\b(export|import|class|def|function)\b/.test(f.text)) util += 1;
    util += f.ability.length * 0.8;
    if (/\$schema|z\.object\(|ajv|schema|types/i.test(f.text)) util += 0.8;
    if (/ollama|langchain|llamaindex|openai|fastapi|express\(|router\.|tsx/.test(f.text)) util += 1.0;

    // spam score: lots of placeholders / repeated lines / giant flat logs
    let spam = 0;
    const lines = f.text.split("\n");
    if (lines.length >= cfg.spam.minTextLines) {
      const map = new Map<string, number>();
      for (const L of lines) {
        const k = L.trim();
        if (!k) continue;
        map.set(k, (map.get(k)||0)+1);
      }
      const repeats = [...map.values()].filter(v => v>1).reduce((a,b)=>a+b,0);
      const repeatRatio = repeats / Math.max(1, lines.length);
      if (repeatRatio > cfg.spam.maxRepeatLineRatio) spam += 1.0;
    }
    const ph = cfg.spam.placeholderWords.filter(w => f.text!.includes(w)).length;
    spam += ph * 0.3;

    f.utilScore = within(util, 0, 6);
    f.spamScore = within(spam, 0, 6);
  } else {
    f.utilScore = 0.2; // binaries could be assets; keep tiny utility
    f.spamScore = 0;
  }
}

function summarize() {
  // exact duplicates
  const bySha = new Map<string, FileInfo[]>();
  for (const fi of files) {
    const arr = bySha.get(fi.sha1) || [];
    arr.push(fi);
    bySha.set(fi.sha1, arr);
  }
  const exactDupGroups = [...bySha.values()].filter(g => g.length > 1);

  // near duplicates (softSig + Jaccard on token sets)
  const sigBuckets = new Map<string, FileInfo[]>();
  for (const fi of files) {
    if (!fi.softSig) continue;
    const arr = sigBuckets.get(fi.softSig) || [];
    arr.push(fi);
    sigBuckets.set(fi.softSig, arr);
  }
  const nearDupPairs: Array<{a:string,b:string,score:number}> = [];
  for (const [,bucket] of sigBuckets) {
    if (bucket.length < 2) continue;
    const sets = bucket.map(b => new Set(b.softSig.split("|")));
    for (let i=0;i<bucket.length;i++){
      for (let j=i+1;j<bucket.length;j++){
        const s = jaccard(sets[i], sets[j]);
        if (s >= cfg.dupNearJaccard && bucket[i].sha1 !== bucket[j].sha1) {
          nearDupPairs.push({ a: bucket[i].rel, b: bucket[j].rel, score: +s.toFixed(3) });
        }
      }
    }
  }

  // spammy/noisy candidates
  const spammy = files
    .filter(f => f.spamScore >= 1.0 && f.utilScore < 1.0)
    .sort((a,b)=> (b.spamScore - a.spamScore) || (b.size - a.size))
    .slice(0, 1000);

  // abilities index
  const abilities = files
    .filter(f => f.ability.length)
    .map(f => ({ rel: f.rel, ability: f.ability, class: f.class }));

  // Ψ_audit score per file
  const { util, dup, spam } = cfg.weights;
  const shaSet = new Set(exactDupGroups.flatMap(g => g.map(x => x.rel)));
  const ndSet = new Set(nearDupPairs.flatMap(p => [p.a, p.b]));
  const report = files.map(f => ({
    rel: f.rel,
    class: f.class,
    size: f.size,
    util: f.utilScore,
    spam: f.spamScore,
    exactDup: shaSet.has(f.rel),
    nearDup: ndSet.has(f.rel),
    psi: +(f.utilScore*util - (shaSet.has(f.rel)?1:0)*dup - f.spamScore*spam).toFixed(3),
    ability: f.ability
  }));

  // move plan (dry-run): which dups/spam to archive → .attic (keep one canonical)
  const moves: Array<{from:string,to:string,reason:string}> = [];
  for (const g of exactDupGroups) {
    // choose canonical: prefer file under packages/ or apps/ (code), otherwise shortest path
    const canon = [...g].sort((a,b)=>{
      const aw = canonicalWeight(a.rel), bw = canonicalWeight(b.rel);
      if (aw !== bw) return bw - aw;
      return a.rel.length - b.rel.length;
    })[0].rel;
    for (const other of g) {
      if (other.rel === canon) continue;
      const to = path.join(cfg.atticDir, "duplicates", other.rel);
      moves.push({ from: other.rel, to, reason: `duplicate_of:${canon}`});
    }
  }
  for (const s of spammy) {
    const to = path.join(cfg.atticDir, "spam", s.rel.replace(/[\/\\]+/g,"/"));
    moves.push({ from: s.rel, to, reason: "spam_noise" });
  }

  // write reports
  fs.mkdirSync("reports", { recursive: true });
  fs.writeFileSync("reports/repo_audit.summary.json", JSON.stringify({
    scanned: files.length,
    timeMs: Date.now()-START,
    byClass: countBy(files.map(f=>f.class)),
    exactDupGroups: exactDupGroups.length,
    nearDupPairs: nearDupPairs.length,
    spamCandidates: spammy.length
  }, null, 2));
  fs.writeFileSync("reports/repo_audit.abilities.json", JSON.stringify(abilities, null, 2));
  fs.writeFileSync("reports/repo_audit.files.json", JSON.stringify(report, null, 2));
  fs.writeFileSync("reports/repo_audit.duplicates.json", JSON.stringify({
    exactDupGroups: exactDupGroups.map(g => g.map(x=>x.rel)),
    nearDupPairs
  }, null, 2));
  fs.writeFileSync("reports/repo_anneal.moves.json", JSON.stringify(moves, null, 2));

  // emit a safe .sh plan (no execution)
  const sh = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    `mkdir -p ${cfg.atticDir}/duplicates ${cfg.atticDir}/spam`,
    ...moves.map(m => `mkdir -p "$(dirname "${m.to}")"; [ -f "${m.from}" ] && git mv -f "${m.from}" "${m.to}" || true # ${m.reason}`)
  ].join("\n");
  fs.writeFileSync("reports/repo_anneal.moves.sh", sh, "utf8");

  console.log(`[audit] scanned=${files.length} exactDupGroups=${exactDupGroups.length} nearDupPairs=${nearDupPairs.length} spam=${spammy.length}`);
  console.log(`[audit] reports written to ./reports/  (review repo_anneal.moves.sh before running)`);
}

function canonicalWeight(rel: string) {
  const r = rel.replace(/\\/g,"/");
  if (r.startsWith("packages/")) return 3;
  if (r.startsWith("apps/")) return 2;
  if (r.startsWith("ops/")) return 1.5;
  if (/lexicon|OmniTag|Rosetta|QGL/i.test(r)) return 1.2;
  return 1;
}
function countBy<T extends string | number>(arr: T[]) {
  const m = new Map<T, number>();
  for (const a of arr) m.set(a, (m.get(a)||0)+1);
  return Object.fromEntries(m);
}

(async () => {
  await walk(path.resolve(cfg.root), path.resolve(cfg.root));
  summarize();
})();