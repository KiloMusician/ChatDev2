#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

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
const planPath = argv.get("plan") || "reports/analysis.json";
const APPLY = argv.has("apply");
const DRY = argv.has("dry-run") || (!APPLY && config.safety.dryRunDefault);

console.log(`🩺 Culture-Ship Self-Healing ${DRY ? "(DRY-RUN)" : "(APPLY)"}`);

const plan = JSON.parse(fs.readFileSync(planPath, "utf8"));
fs.mkdirSync("reports/patches", { recursive: true });

let fileWriteCount = 0;

const write = (p, content) => {
  if (++fileWriteCount > config.safety.maxFileWrite) {
    console.warn(`⚠️ Reached max file write limit (${config.safety.maxFileWrite}), skipping: ${p}`);
    return;
  }
  if (DRY) return console.log(`DRY-WRITE ${p} (${content.length} bytes)`);
  if (config.safety.createBackups && fs.existsSync(p)) {
    fs.writeFileSync(`${p}.bak`, fs.readFileSync(p));
  }
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content);
};
const patchNote = (msg) => fs.appendFileSync("reports/patches/changes.log", `${new Date().toISOString()} - ${msg}\n`);

function unique(arr) { return [...new Set(arr)]; }

// -------- Healer: Fix broken imports by best suggestion ----------
function healImports() {
  const imports = plan.analyses.find(a => a.kind === "imports");
  if (!imports?.broken?.length) return [];
  
  const fixes = [];
  console.log(`🔧 Processing ${imports.broken.length} broken imports...`);
  
  for (const b of imports.broken) {
    if (b.suggestion?.length) {
      const fromPath = path.join(ROOT, b.from);
      if (!fs.existsSync(fromPath)) continue;
      
      const text = fs.readFileSync(fromPath, "utf8");
      const relativeTarget = relativeImport(b.from, b.suggestion[0]);
      const safe = text.replace(new RegExp(`(from|require\\()\\s*["']${escapeRegex(b.spec)}["']`, "g"),
        m => m.replace(b.spec, relativeTarget));
      
      if (safe !== text) {
        fixes.push({ file: b.from, old: b.spec, new: relativeTarget });
        write(fromPath, safe);
        patchNote(`import-fix: ${b.from}: ${b.spec} -> ${relativeTarget}`);
      }
    }
  }
  return fixes;
}

function relativeImport(from, to) {
  const rel = path.relative(path.dirname(from), to);
  return (rel.startsWith(".") ? rel : "./" + rel).replace(/\\/g, "/").replace(/\.(ts|tsx|js|jsx|mjs|cjs)$/, "");
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// -------- Healer: Consolidate duplicates ----------
function healDuplicates() {
  const dups = plan.analyses.find(a => a.kind === "duplicates");
  if (!dups?.groups?.length) return [];
  
  const ops = [];
  console.log(`🔧 Processing ${dups.groups.length} duplicate groups...`);
  
  for (const g of dups.groups) {
    if (g.files.length < 2) continue;
    
    // pick canonical in preferred dir or shortest path
    const canonical = g.files.find(f => f.startsWith(config.preferCanonicalDir + "/")) || 
                     g.files.sort((a,b)=>a.length-b.length)[0];
    
    for (const f of g.files) {
      if (f === canonical) continue;
      
      const abs = path.join(ROOT, f);
      if (!fs.existsSync(abs)) continue;
      
      // strategy: reexport stub
      const relTarget = relativeImport(f, canonical);
      const stub = `// Culture-Ship: Consolidated duplicate\nexport * from "${relTarget}";\nexport { default } from "${relTarget}";\n`;
      
      write(abs, stub);
      ops.push({ reexport: f, target: canonical });
      patchNote(`duplicate-merge: ${f} -> ${canonical} (reexport stub)`);
    }
  }
  return ops;
}

// -------- Healer: Stub empty placeholders ----------
function healPlaceholders() {
  const ph = plan.analyses.find(a => a.kind === "placeholders");
  if (!ph?.results?.length) return [];
  
  const seen = new Map();
  const ops = [];
  console.log(`🔧 Processing ${ph.results.length} placeholders...`);
  
  for (const item of ph.results) {
    if (item.snippet === "<EMPTY PLACEHOLDER FILE>") {
      if (seen.has(item.file)) continue;
      seen.set(item.file, true);
      
      const abs = path.join(ROOT, item.file);
      const basename = path.basename(item.file, path.extname(item.file));
      const ext = path.extname(item.file);
      
      let stub;
      if (ext === ".ts" || ext === ".tsx") {
        stub = `/**
 * Culture-Ship Placeholder Stub
 * File: ${item.file}
 * This stub prevents softlocks by exporting safe no-op symbols.
 */
export const ${camelSafe(basename)}Ready = true;
export default function ${camelSafe(basename)}() { return null; }
`;
      } else {
        stub = `// Culture-Ship placeholder stub for ${item.file}\nexport const ready = true;\n`;
      }
      
      write(abs, stub);
      ops.push({ stubbed: item.file });
      patchNote(`placeholder-stub: ${item.file}`);
    }
  }
  return ops;
}

function camelSafe(s) { 
  return s.replace(/[^a-zA-Z0-9]+(.)/g, (_,c)=>c.toUpperCase()).replace(/^[^a-zA-Z]+/,"X") || "X"; 
}

// -------- Healer: Soften softlocks ----------
function healSoftlocks() {
  const sl = plan.analyses.find(a => a.kind === "softlocks");
  if (!sl?.results?.length) return [];
  
  const ops = [];
  console.log(`🔧 Processing ${sl.results.length} potential softlocks...`);
  
  for (const { file, pattern, severity } of sl.results) {
    const abs = path.join(ROOT, file);
    if (!fs.existsSync(abs)) continue;
    
    const t = fs.readFileSync(abs, "utf8");
    let s = t;
    
    // Apply softlock guards
    s = s.replace(/\bwhile\s*\(\s*true\s*\)\s*\{/g, "for (let __cs_guard=0; __cs_guard++<1e7; ) {");
    s = s.replace(/\bfor\s*\(\s*;\s*;\s*\)\s*\{/g, "for (let __cs_guard=0; __cs_guard++<1e7; ) {");
    s = s.replace(/setInterval\s*\(\s*([^,]+),\s*0\s*\)/g, "setInterval($1, 16)");
    s = s.replace(/setTimeout\s*\(\s*([^,]+),\s*0\s*\)/g, "setTimeout($1, 1)");
    
    if (s !== t) {
      write(abs, s);
      ops.push({ softened: file, pattern, severity });
      patchNote(`softlock-guard: ${file} (${severity}): ${pattern}`);
    }
  }
  return ops;
}

// -------- Healer: Directory barrels (index.ts) ----------
function healBarrels() {
  const imports = plan.analyses.find(a => a.kind === "imports");
  const dirs = new Set();
  
  // Look for directories with broken imports
  for (const b of imports?.broken || []) {
    dirs.add(path.dirname(b.from));
  }
  
  const ops = [];
  console.log(`🔧 Checking ${dirs.size} directories for barrel files...`);
  
  dirs.forEach(d => {
    const abs = path.join(ROOT, d);
    if (!fs.existsSync(abs)) return;
    
    const entries = fs.readdirSync(abs)
      .filter(x => /\.(ts|tsx|js|jsx|mjs|cjs)$/.test(x) && !/^index\./.test(x))
      .filter(x => fs.statSync(path.join(abs, x)).isFile());
      
    if (!entries.length) return;
    
    const indexPath = path.join(abs, "index.ts");
    if (!fs.existsSync(indexPath)) {
      const lines = [
        "// Culture-Ship Auto-Generated Barrel",
        ...entries.map(x => `export * from "./${x.replace(/\.[^.]+$/, "")}";`)
      ];
      
      write(indexPath, lines.join("\n") + "\n");
      ops.push({ barrel: path.relative(ROOT, indexPath) });
      patchNote(`barrel-create: ${path.relative(ROOT, indexPath)}`);
    }
  });
  return ops;
}

// -------- Orchestrate --------
console.log(`📋 Analyzing plan from: ${planPath}`);

const healers = [
  { name: "Import Fixes", fn: healImports },
  { name: "Duplicate Merges", fn: healDuplicates },
  { name: "Placeholder Stubs", fn: healPlaceholders },
  { name: "Softlock Guards", fn: healSoftlocks },
  { name: "Barrel Files", fn: healBarrels }
];

const summary = {
  dryRun: DRY,
  appliedAt: new Date().toISOString(),
  fileWriteCount,
  fixes: {}
};

for (const { name, fn } of healers) {
  try {
    console.log(`\n🔄 Running: ${name}`);
    const result = fn();
    summary.fixes[name.replace(/ /g, "")] = result;
    console.log(`  ✅ ${name}: ${Array.isArray(result) ? result.length : 0} operations`);
  } catch (error) {
    console.error(`  ❌ ${name}: ${error.message}`);
    summary.fixes[name.replace(/ /g, "")] = { error: error.message };
  }
}

summary.fileWriteCount = fileWriteCount;

fs.writeFileSync("reports/patches/summary.json", JSON.stringify(summary, null, 2));
console.log(`\n${DRY ? "🔎 DRY-RUN" : "🩺 APPLIED"} self-healing summary written to reports/patches/summary.json`);
console.log(`📊 File writes: ${fileWriteCount}/${config.safety.maxFileWrite}`);