#!/usr/bin/env tsx
/**
 * Repo Triage — mines attic/containment for abilities & knowledge.
 * Non-destructive. Emits:
 *  - reports/triage/triage.summary.json        (counts)
 *  - reports/triage/triage.items.ndjson        (per-file results)
 *  - reports/triage/triage.near_dups.json      (near-duplicate map)
 *  - reports/triage/triage.move_plan.sh        (suggested moves)
 */
import { promises as fs } from "node:fs";
import * as fsp from "node:fs/promises";
import * as path from "node:path";
import * as crypto from "node:crypto";

type Cfg = {
  scanRoots: string[];
  activeRoots: string[];
  reportDir: string;
  maxBytesKnowledge: number;
  maxBytesAbility: number;
  spamMinLines: number;
  dupBlockBytes: number;
  nearDupShingle: number;
  codeExt: string[];
  abilityHints: string[];
  abilityRegex: string[];
  knowledgeRegex: string[];
  spamRegex: string[];
  reintegrationTargets: { abilities: string; knowledge: string; spam: string };
};

const enc = new TextEncoder();

async function loadCfg(): Promise<Cfg> {
  const raw = await fs.readFile("ops/repo-triage.config.json", "utf8");
  return JSON.parse(raw);
}

async function ensureDir(p: string) {
  await fs.mkdir(p, { recursive: true });
}

async function walk(root: string, out: string[] = []): Promise<string[]> {
  let entries: any[];
  try {
    entries = await fs.readdir(root, { withFileTypes: true });
  } catch { return out; }
  for (const e of entries) {
    const p = path.join(root, e.name);
    if (e.isDirectory()) await walk(p, out);
    else out.push(p);
  }
  return out;
}

function extOf(p: string) { return path.extname(p).toLowerCase(); }

async function statSafe(p: string) {
  try { return await fs.stat(p); } catch { return null; }
}

async function readHead(p: string, limit = 1024 * 256) {
  const fh = await fsp.open(p, "r");
  try {
    const { size } = await fh.stat();
    const toRead = Math.min(size, limit);
    const buf = Buffer.alloc(toRead);
    await fh.read(buf, 0, toRead, 0);
    return buf.toString("utf8");
  } finally {
    await fh.close();
  }
}

function sha256(buf: Buffer | string) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

// very light shingle hash for near-dup suggestion
function shingles(text: string, k: number) {
  const tokens = text.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  for (let i = 0; i + k <= tokens.length; i++) {
    const s = tokens.slice(i, i + k).join(" ");
    out.push(sha256(s).slice(0, 16));
  }
  return out;
}

function jaccard(a: Set<string>, b: Set<string>) {
  const inter = new Set([...a].filter(x => b.has(x))).size;
  const uni = new Set([...a, ...b]).size || 1;
  return inter / uni;
}

function compile(regexes: string[]) { return regexes.map(r => new RegExp(r, "im")); }

type Item = {
  file: string;
  size: number;
  lines: number;
  ext: string;
  sha: string;
  headSample: string;
  score: { ability: number; knowledge: number; spam: number };
  class: "ability" | "knowledge" | "spam" | "unknown";
  hints: string[];
  rationale: string[];
  suggestedTarget?: string;
}

async function main() {
  const cfg = await loadCfg();
  const reportDir = cfg.reportDir;
  await ensureDir(reportDir);

  const abilityRx = compile(cfg.abilityRegex);
  const knowledgeRx = compile(cfg.knowledgeRegex);
  const spamRx = compile(cfg.spamRegex);

  const files: string[] = [];
  for (const root of cfg.scanRoots) files.push(...await walk(root));

  const results: Item[] = [];
  const hashToActivePath = new Map<string, string>();
  // Pre-hash active roots (first block) to spot exact dup heads quickly
  for (const root of cfg.activeRoots) {
    const act = await walk(root);
    for (const p of act) {
      const st = await statSafe(p);
      if (!st || !st.isFile()) continue;
      const head = await readHead(p, cfg.dupBlockBytes);
      const key = sha256(head || "");
      if (!hashToActivePath.has(key)) hashToActivePath.set(key, p);
    }
  }

  for (const file of files) {
    const st = await statSafe(file);
    if (!st || !st.isFile()) continue;
    const ext = extOf(file);
    const head = await readHead(file, cfg.dupBlockBytes);
    const headHash = sha256(head || "");
    const lines = (head.match(/\n/g) || []).length + 1;

    let ability = 0, knowledge = 0, spam = 0;
    const rationale: string[] = [];
    const hints: string[] = [];

    // size heuristics
    if (st.size <= cfg.maxBytesAbility && cfg.codeExt.includes(ext)) {
      ability += 1; rationale.push(`size<=abilityMax & codeExt(${ext})`);
    }
    if (st.size <= cfg.maxBytesKnowledge && (ext === ".md" || ext === ".txt" || ext === ".rtf" || ext === ".json")) {
      knowledge += 1; rationale.push(`size<=knowledgeMax & docExt(${ext})`);
    }
    if (lines >= cfg.spamMinLines) { spam += 1; rationale.push(`manyLines>=${cfg.spamMinLines}`); }

    // hints
    for (const h of cfg.abilityHints) {
      if (head && head.toLowerCase().includes(h.toLowerCase())) { hints.push(h); ability += 0.5; }
    }

    // regex classification
    if (head) {
      if (abilityRx.some(rx => rx.test(head))) { ability += 1.5; rationale.push("abilityRegex"); }
      if (knowledgeRx.some(rx => rx.test(head))) { knowledge += 1.0; rationale.push("knowledgeRegex"); }
      if (spamRx.some(rx => rx.test(head))) { spam += 1.0; rationale.push("spamRegex"); }
    }

    // duplicates (exact head block)
    const dupActive = hashToActivePath.get(headHash);
    if (dupActive) { spam += 0.75; rationale.push(`headDupWithActive:${dupActive}`); }

    let klass: Item["class"] = "unknown";
    const maxScore = Math.max(ability, knowledge, spam);
    if (maxScore === ability && ability >= 1.5) klass = "ability";
    else if (maxScore === knowledge && knowledge >= 1.25) klass = "knowledge";
    else if (maxScore === spam && spam >= 1.2) klass = "spam";

    let suggestedTarget: string | undefined;
    if (klass === "ability") suggestedTarget = cfg.reintegrationTargets.abilities;
    if (klass === "knowledge") suggestedTarget = cfg.reintegrationTargets.knowledge;
    if (klass === "spam") suggestedTarget = cfg.reintegrationTargets.spam;

    results.push({
      file, size: st.size, lines, ext,
      sha: headHash, headSample: head?.slice(0, 1024) ?? "",
      score: { ability, knowledge, spam },
      class: klass, hints, rationale, suggestedTarget
    });
  }

  // near-duplicate detector (cheap shingles on head)
  const shingleMap = new Map<string, { file: string; set: Set<string> }>();
  for (const it of results) {
    const sh = new Set(shingles(it.headSample, cfg.nearDupShingle));
    shingleMap.set(it.file, { file: it.file, set: sh });
  }
  const nearDupPairs: Array<{ a: string; b: string; jaccard: number }> = [];
  const filesArr = [...shingleMap.values()];
  for (let i = 0; i < filesArr.length; i++) {
    for (let j = i + 1; j < filesArr.length; j++) {
      const a = filesArr[i], b = filesArr[j];
      if (a.set.size < 5 || b.set.size < 5) continue; // skip tiny
      const jac = jaccard(a.set, b.set);
      if (jac >= 0.85) nearDupPairs.push({ a: a.file, b: b.file, jaccard: +jac.toFixed(3) });
    }
  }

  await ensureDir(reportDir);
  await fs.writeFile(path.join(reportDir, "triage.items.ndjson"),
    results.map(r => JSON.stringify(r)).join("\n"));

  const summary = {
    scanned: results.length,
    byClass: {
      ability: results.filter(r => r.class === "ability").length,
      knowledge: results.filter(r => r.class === "knowledge").length,
      spam: results.filter(r => r.class === "spam").length,
      unknown: results.filter(r => r.class === "unknown").length
    }
  };
  await fs.writeFile(path.join(reportDir, "triage.summary.json"), JSON.stringify(summary, null, 2));
  await fs.writeFile(path.join(reportDir, "triage.near_dups.json"), JSON.stringify(nearDupPairs, null, 2));

  // move plan (shell): only for ability/knowledge/spam with targets
  const planLines: string[] = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    "# Non-destructive: creates target dirs and moves from attic/containment",
    ""
  ];
  for (const r of results) {
    if (!r.suggestedTarget) continue;
    const rel = path.relative(".", r.file);
    const base = path.basename(r.file);
    const destDir = r.suggestedTarget;
    const destPath = path.join(destDir, base);
    planLines.push(`mkdir -p "${destDir}"`);
    planLines.push(`# ${r.class} :: ${r.rationale.join("; ")}`);
    planLines.push(`mv -n "${rel}" "${destPath}" || true`);
    planLines.push("");
  }
  await fs.writeFile(path.join(reportDir, "triage.move_plan.sh"), planLines.join("\n"), { mode: 0o755 });

  console.log("=== TRIAGE COMPLETE ===");
  console.log(summary);
  console.log(`Reports in ${reportDir}`);
}
main().catch(e => { console.error(e); process.exit(1); });