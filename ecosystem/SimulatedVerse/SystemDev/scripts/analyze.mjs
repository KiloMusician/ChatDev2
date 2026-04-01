#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import process from "process";
import crypto from "crypto";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const CONFIG_PATH = path.join(ROOT, "modules/culture_ship/config/culture-ship.config.json");
const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));

const argv = new Map();
for (let i = 2; i < process.argv.length; i++) {
  const arg = process.argv[i];
  if (arg.startsWith("--")) {
    if (arg.includes("=")) {
      const [k, v] = arg.slice(2).split("=", 2);
      argv.set(k, v);
    } else {
      const k = arg.slice(2);
      const nextArg = process.argv[i + 1];
      if (nextArg && !nextArg.startsWith("--")) {
        argv.set(k, nextArg);
        i++; // skip next arg
      } else {
        argv.set(k, true);
      }
    }
  }
}
const reportJsonPath = argv.get("report") || "reports/analysis.json";
const reportMdPath = argv.get("md") || null;

const glob = (await import("glob")).glob;

// ---------- Utils ----------
const slurp = p => fs.readFileSync(p, "utf8");
const hash = s => crypto.createHash("sha1").update(s).digest("hex");
const norm = p => p.replace(/\\/g, "/");
const exists = p => { try { fs.accessSync(p); return true; } catch { return false; } };
const readMaybe = p => exists(p) ? slurp(p) : "";

// ---------- File list ----------
const files = (await glob(config.includeGlobs, {
  ignore: config.excludeGlobs, nodir: true, absolute: true
})).filter(p => config.importFileExtensions.includes(path.extname(p)));

const rel = p => norm(path.relative(ROOT, p));

// ---------- Analyzer: Placeholders ----------
function analyzePlaceholders() {
  const pats = config.placeholderPatterns.map(x => new RegExp(`\\b${x}\\b`, "i"));
  const results = [];
  for (const f of files) {
    const text = readMaybe(f);
    let hit = false;
    const lines = text.split(/\r?\n/);
    lines.forEach((line, i) => {
      if (pats.some(r => r.test(line))) {
        hit = true;
        results.push({ file: rel(f), line: i + 1, snippet: line.trim().slice(0, 200) });
      }
    });
    if (hit && text.trim() === "") {
      results.push({ file: rel(f), line: 0, snippet: "<EMPTY PLACEHOLDER FILE>" });
    }
  }
  return { kind: "placeholders", count: results.length, results };
}

// ---------- Analyzer: Duplicates (exact hash match) ----------
function analyzeDuplicates() {
  const groups = new Map(); // hash -> [file]
  for (const f of files) {
    const text = readMaybe(f);
    const content = text.replace(/\s+/g, " ").trim(); // normalize whitespace
    if (content.length < 10) continue; // skip tiny files
    const h = hash(content);
    if (!groups.has(h)) groups.set(h, []);
    groups.get(h).push(rel(f));
  }
  const dupGroups = [...groups.entries()]
    .map(([h, arr]) => ({ hash: h, files: arr }))
    .filter(g => g.files.length > 1);
  return { kind: "duplicates", count: dupGroups.length, groups: dupGroups };
}

// ---------- Build naive import graph + broken imports ----------
import { createRequire } from "module";
const require = createRequire(import.meta.url);

const IMPORT_RE = /\bimport\s+(?:[^'"]+\s+from\s+)?["']([^"']+)["']|require\(\s*["']([^"']+)["']\s*\)/g;

function resolveImport(fromFile, spec) {
  if (!spec || spec.startsWith("http")) return null; // ignore urls
  if (!spec.startsWith(".") && !spec.startsWith("/")) return null; // bare module
  const base = path.resolve(ROOT, path.dirname(fromFile));
  const tryPaths = [];
  // direct file
  tryPaths.push(path.resolve(base, spec));
  // with extensions
  for (const ext of config.importFileExtensions) tryPaths.push(path.resolve(base, spec + ext));
  // index.* in folder
  for (const ext of config.importFileExtensions) tryPaths.push(path.resolve(base, spec, "index" + ext));
  return tryPaths.find(exists) || null;
}

function analyzeImports() {
  const edges = [];
  const broken = [];
  for (const f of files) {
    const text = readMaybe(f);
    IMPORT_RE.lastIndex = 0;
    let m;
    while ((m = IMPORT_RE.exec(text))) {
      const spec = m[1] || m[2];
      const target = resolveImport(f, spec);
      if (target) {
        edges.push([rel(f), rel(target)]);
      } else if (spec && (spec.startsWith(".") || spec.startsWith("/"))) {
        // Suggest target by basename search
        const base = path.basename(spec).replace(/\.[^.]+$/, "");
        const candidates = files.filter(p => path.basename(p, path.extname(p)) === base).map(rel);
        broken.push({
          from: rel(f),
          spec,
          suggestion: candidates.slice(0, 5)
        });
      }
    }
  }
  // naive cycles (DFS)
  const graph = new Map();
  for (const [a, b] of edges) {
    if (!graph.has(a)) graph.set(a, new Set());
    graph.get(a).add(b);
  }
  const cycles = [];
  const temp = new Set(), perm = new Set(), stack = [];
  function dfs(u) {
    if (perm.has(u)) return false;
    if (temp.has(u)) {
      const i = stack.indexOf(u);
      if (i !== -1) cycles.push(stack.slice(i).concat(u));
      return true;
    }
    temp.add(u); stack.push(u);
    for (const v of (graph.get(u) || [])) dfs(v);
    temp.delete(u); perm.add(u); stack.pop();
    return false;
  }
  [...graph.keys()].forEach(dfs);
  return { kind: "imports", edgesCount: edges.length, brokenCount: broken.length, broken, cycles };
}

// ---------- Analyzer: Dead/Unreachable (not imported by anyone) ----------
async function analyzeUnreachable() {
  const { broken, edgesCount } = analyzeImports(); // reuse parse pass
  // quick rebuild edge set
  const edgeSet = new Map();
  for (const f of files) edgeSet.set(rel(f), new Set());
  const textCache = new Map(files.map(f => [rel(f), readMaybe(f)]));
  for (const f of files) {
    const text = textCache.get(rel(f));
    let m; IMPORT_RE.lastIndex = 0;
    while ((m = IMPORT_RE.exec(text))) {
      const spec = m[1] || m[2];
      const tgt = resolveImport(f, spec);
      if (tgt) edgeSet.get(rel(f)).add(rel(tgt));
    }
  }
  // mark reachable from any entry
  const entries = (await glob(config.entryGlobs, { ignore: config.excludeGlobs, nodir: true, absolute: true }))
    .map(rel);
  const seen = new Set();
  function walk(u) {
    if (seen.has(u)) return;
    seen.add(u);
    for (const v of (edgeSet.get(u) || [])) walk(v);
  }
  entries.forEach(walk);
  const unreachable = [...edgeSet.keys()].filter(k => !seen.has(k));
  return { kind: "unreachable", totalEdges: edgesCount, entries, count: unreachable.length, files: unreachable.slice(0, 1000) };
}

// ---------- Analyzer: Softlocks (heuristics) ----------
function analyzeSoftlocks() {
  const results = [];
  const TIGHT = [
    /\bwhile\s*\(\s*true\s*\)\s*\{/,
    /\bfor\s*\(\s*;\s*;\s*\)\s*\{/,
    /new\s+Promise\s*\(\s*\(\s*resolve,\s*reject\s*\)\s*=>\s*{}\s*\)/,
    /\bsetInterval\s*\(\s*[^,]+,\s*0\s*\)/,
    /\bsetTimeout\s*\(\s*[^,]+,\s*0\s*\)/
  ];
  for (const f of files) {
    const text = readMaybe(f);
    TIGHT.forEach((rx, i) => {
      if (rx.test(text)) {
        results.push({ file: rel(f), pattern: rx.toString(), severity: i < 2 ? "high" : "medium" });
      }
    });
  }
  return { kind: "softlocks", count: results.length, results };
}

// ---------- Main ----------
async function runAnalysis() {
  console.log("🔍 Culture-Ship Analysis Starting...");
  console.log(`📁 Root: ${ROOT}`);
  console.log(`📊 Scanning ${files.length} files...`);

  const analyses = [
    analyzePlaceholders(),
    analyzeDuplicates(),
    analyzeImports(),
    await analyzeUnreachable(),
    analyzeSoftlocks()
  ];

  return analyses;
}

const analyses = await runAnalysis();

const summary = {
  generatedAt: new Date().toISOString(),
  root: ROOT,
  config: path.relative(ROOT, CONFIG_PATH),
  fileCount: files.length,
  stats: analyses.reduce((acc, a) => ({ ...acc, [a.kind]: a.count ?? a.brokenCount ?? a.edgesCount ?? 0 }), {}),
  analyses
};

fs.mkdirSync(path.dirname(reportJsonPath), { recursive: true });
fs.writeFileSync(reportJsonPath, JSON.stringify(summary, null, 2));

if (reportMdPath) {
  const lines = [];
  lines.push(`# Culture-Ship Analysis Report`);
  lines.push(`Generated: ${summary.generatedAt}`);
  lines.push(`Files scanned: ${summary.fileCount}`);
  lines.push(``);
  
  lines.push(`## Summary`);
  Object.entries(summary.stats).forEach(([k,v]) => lines.push(`- **${k}**: ${v}`));
  lines.push(``);
  
  for (const a of analyses) {
    lines.push(`## ${a.kind.toUpperCase()}`);
    if (a.kind === "imports") {
      lines.push(`- Total edges: ${a.edgesCount}`);
      lines.push(`- Broken imports: ${a.brokenCount}`);
      if (a.broken?.length) {
        lines.push(`\n### Broken Import Details`);
        a.broken.slice(0, 20).forEach(b => lines.push(`- **${b.from}** → \`${b.spec}\` (suggest: ${b.suggestion.join(", ") || "none"})`));
      }
      if (a.cycles?.length) {
        lines.push(`\n### Circular Dependencies`);
        lines.push(`- Found ${a.cycles.length} cycles`);
        a.cycles.slice(0, 10).forEach(c => lines.push(`  - ${c.join(" → ")}`));
      }
    } else if (Array.isArray(a.results)) {
      lines.push(`- Count: ${a.results.length}`);
      if (a.results.length) {
        lines.push(`\n### Details`);
        a.results.slice(0, 20).forEach(r => {
          const loc = r.line ? `:${r.line}` : "";
          const info = r.snippet || r.pattern || r.severity || "";
          lines.push(`- **${r.file}${loc}** ${info}`);
        });
      }
    } else if (a.kind === "duplicates") {
      lines.push(`- Duplicate groups: ${a.count}`);
      if (a.groups?.length) {
        lines.push(`\n### Duplicate Groups`);
        a.groups.slice(0, 10).forEach(g => lines.push(`- **${g.files.length} files**: ${g.files.join(", ")}`));
      }
    } else if (a.kind === "unreachable") {
      lines.push(`- Entry points: ${a.entries.length}`);
      lines.push(`- Unreachable files: ${a.count}`);
      if (a.files?.length) {
        lines.push(`\n### Unreachable Files`);
        a.files.slice(0, 20).forEach(f => lines.push(`- ${f}`));
      }
    }
    lines.push("");
  }
  fs.writeFileSync(reportMdPath, lines.join("\n"));
}

console.log(`✅ Analysis complete!`);
console.log(`📋 Report: ${reportJsonPath}`);
if (reportMdPath) console.log(`📝 Markdown: ${reportMdPath}`);
console.log(`📊 Stats: ${JSON.stringify(summary.stats, null, 2)}`);