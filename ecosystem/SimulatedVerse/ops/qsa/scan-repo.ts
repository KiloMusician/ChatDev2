#!/usr/bin/env tsx
import { promises as fs } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { execSync } from "node:child_process";
import { createRequire } from "node:module";
const _require = createRequire(import.meta.url);
import { jaccardSimilarity } from "./near-dup.js";

// Lightweight glob without adding deps
async function walk(dir: string, ignore: RegExp[]): Promise<string[]> {
  const out: string[] = [];
  async function recur(p: string) {
    for (const ig of ignore) if (ig.test(p)) return;
    const ent = await fs.readdir(p, { withFileTypes: true });
    for (const e of ent) {
      const full = join(p, e.name);
      if (e.isDirectory()) await recur(full);
      else out.push(full);
    }
  }
  await recur(dir);
  return out;
}

function sha1(buf: Buffer) { return createHash("sha1").update(buf).digest("hex"); }
function normText(txt: string) {
  return txt
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\/\/.*$/gm, "")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .trim();
}

async function main() {
  const cfg = YAML(await fs.readFile("ops/qsa/triage-rules.yaml", "utf8"));
  console.log("[qsa] Config loaded:", Object.keys(cfg));
  
  const ignore = (cfg.ignore || []).map((s: string) => new RegExp(s));
  const files = await walk(".", ignore);

  const abilityHints = new RegExp((cfg.ability_hints || []).join("|"), "i");
  const issuePlaceholders = new RegExp((cfg.issue_patterns?.placeholders || []).join("|"), "i");
  const issueHard = new RegExp((cfg.issue_patterns?.hardcoded_errors || []).join("|"), "i");

  const quadRules = Object.entries(cfg.quad_tags as Record<string,string[]>)
    .map(([k, vals]) => [k, new RegExp(vals.join("|"))] as const);

  const stats = { files: files.length, scanned: 0 };
  const abilities: any[] = [];
  const issues: any[] = [];
  const spam: any[] = [];
  const byStem: Record<string, string[]> = {};
  const hashes: Record<string, string[]> = {}; // hash -> paths

  for (const path of files) {
    const ext = path.split(".").pop() || "";
    const stem = path.replace(/\.\w+$/, "");
    const buf = await fs.readFile(path).catch(()=>Buffer.from(""));
    const size = buf.byteLength;
    const text = /\.(txt|md|js|ts|tsx|json|yaml|yml|py|gd|cfg|log)$/i.test(path) ? buf.toString("utf8") : "";
    const norm = normText(text);
    const hash = sha1(Buffer.from(norm));
    (hashes[hash] ||= []).push(path);
    (byStem[stem] ||= []).push(path);

    // Quad tag by path
    const quad = quadRules.find(([_, rx]) => rx.test(path))?.[0] || "unknown";

    // Ability hints
    if (abilityHints.test(path) || abilityHints.test(text.slice(0, 400))) {
      abilities.push({ path, quad, size });
    }

    // Issues
    const placeholders = issuePlaceholders.test(text);
    const hard = issueHard.test(text);
    if (placeholders || hard) {
      issues.push({
        path, quad, size,
        placeholders: placeholders ? true : false,
        hardcoded: hard ? true : false,
        sample: text.split("\n").slice(0, 6).join("\n")
      });
    }

    // Spam heuristics: huge file, low useful ratio, or bucket storms
    if (/\.(log|txt|md|json|ndjson)$/i.test(path)) {
      const lines = text.split("\n");
      const uniq = new Set(lines.map(l=>l.trim())).size;
      const usefulRatio = lines.length ? uniq/lines.length : 1;
      const huge = size >= (cfg.spam.huge_file_bytes as number);
      if (huge || usefulRatio < (cfg.spam.min_useful_ratio as number)) {
        spam.push({ path, quad, size, lines: lines.length, usefulRatio });
      }
    }

    stats.scanned++;
    if (stats.scanned % 1000 === 0) console.log(`[qsa] scanned ${stats.scanned}/${stats.files}`);
  }

  // Exact dupes by SHA1
  const dupes: any[] = [];
  for (const [h, paths] of Object.entries(hashes)) {
    if (paths.length > 1) dupes.push({ hash: h, paths });
  }

  // Near-dup pass: same stem but different files
  const near: any[] = [];
  const th = cfg.near_dup_threshold as number;
  for (const [stem, paths] of Object.entries(byStem)) {
    if (paths.length < 2) continue;
    for (let i=0;i<paths.length;i++) {
      for (let j=i+1;j<paths.length;j++) {
        const a = await fs.readFile(paths[i], "utf8").catch(()=> "");
        const b = await fs.readFile(paths[j], "utf8").catch(()=> "");
        const sim = jaccardSimilarity(normText(a), normText(b));
        if (sim >= th) near.push({ stem, a: paths[i], b: paths[j], sim: Number(sim.toFixed(3)) });
      }
    }
  }

  // Spam bucket storms by stem
  const storms = Object.entries(byStem)
    .filter(([_, arr]) => arr.length > (cfg.spam.max_files_per_bucket as number))
    .map(([stem, arr]) => ({ stem, count: arr.length, samples: arr.slice(0,8) }));

  await fs.mkdir("reports/qsa", { recursive: true });
  await fs.writeFile("reports/qsa/repo_audit.json", JSON.stringify({ stats, quadRules: Object.keys(cfg.quad_tags), ts: Date.now() }, null, 2));
  await fs.writeFile("reports/qsa/abilities.json", JSON.stringify(abilities, null, 2));
  await fs.writeFile("reports/qsa/issues.json", JSON.stringify(issues, null, 2));
  await fs.writeFile("reports/qsa/dupes.json", JSON.stringify({ exact: dupes, near }, null, 2));
  await fs.writeFile("reports/qsa/spam.json", JSON.stringify({ spam, storms }, null, 2));
  console.log("[qsa] wrote reports in reports/qsa/");
}

// Minimal YAML parser (prefer existing js-yaml if installed)
function YAML(str: string) {
  try { return _require("js-yaml").load(str); }
  catch {
    // ultra-light YAML subset (k: v, arrays of scalars). Good enough fallback.
    const out: any = {}; let currentKey = ""; let currentObj: any = null;
    for (const raw of str.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      if (/^\w/.test(line) && line.endsWith(":")) { 
        currentKey = line.slice(0,-1); 
        out[currentKey] = {}; 
        currentObj = out[currentKey];
      }
      else if (line.startsWith("  ") && line.includes(":") && currentObj) {
        const [k,v] = line.trim().split(":");
        if (v.trim().startsWith("[")) {
          currentObj[k.trim()] = v.trim().replace(/[\[\]]/g, "").split(",").map(s => s.trim().replace(/"/g,""));
        } else {
          currentObj[k.trim()] = v.trim().replace(/"/g,"");
        }
      }
      else if (line.startsWith("- ")) { 
        if (!Array.isArray(out[currentKey])) out[currentKey] = [];
        out[currentKey].push(line.slice(2).trim().replace(/^"|"$/g,"")); 
      }
      else if (line.includes(":") && !currentObj) { 
        const [k,v] = line.split(":"); 
        out[k.trim()] = v.trim().replace(/"/g,""); 
      }
    }
    return out;
  }
}

main().catch(e => { console.error("[qsa] fatal", e); process.exit(1); });