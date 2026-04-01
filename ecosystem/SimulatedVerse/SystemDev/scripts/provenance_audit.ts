#!/usr/bin/env tsx
/**
 * Provenance & Scope Auditor (receipts-first)
 * Classifies files by category; counts packages vs "our code";
 * flags externals (symlinks resolving outside repo); estimates dedupe targets;
 * emits JSON receipts and a next_up plan.
 */

import { promises as fs } from "fs";
import path from "path";
import crypto from "crypto";

type Tally = Record<string, number>;
type Bytes = number;

const repoRoot = process.cwd();
const isWithin = (p: string) => path.resolve(p).startsWith(repoRoot + path.sep);

// ---- Category rules ----
const catRules: { name: string; test: (rel: string, abs: string, size: Bytes) => boolean }[] = [
  { name: "pkg.node", test: (r) => r.startsWith("node_modules/") || r.startsWith(".yarn/") || r.startsWith(".pnpm-store/") || /(pnpm-lock\.yaml|yarn\.lock|package-lock\.json|\.npmrc|^patches\/)/.test(r) },
  { name: "pkg.py",   test: (r) => r.startsWith(".venv/") || r.includes("site-packages/") || /poetry\.lock|requirements(\.|$)/.test(r) },
  { name: "pkg.godot",test: (r) => r.startsWith("GameDev/engine/godot/.import/") || r.startsWith(".godot/") },
  { name: "build",    test: (r) => /(^|\/)(dist|build|out|coverage|\.next|\.vite|\.svelte-kit|\.cache)\//.test(r) || r.endsWith(".map") || /\.min\.[a-z0-9]+$/.test(r) },
  { name: "tools",    test: (r) => r.startsWith(".git/") || r.startsWith(".github/") || r.startsWith(".githooks/") || r.startsWith(".vscode/") || r.startsWith(".idea/") || /(replit\.nix|Dockerfile|docker-compose\.yml|\.gitmodules)$/.test(r) },
  { name: "assets",   test: (r,_a,size) => /(^|\/)(assets|GameDev\/content)\//.test(r) || size > 512*1024 && /\.(png|jpg|jpeg|gif|mp3|wav|ogg|mp4|mov|ttf|otf|woff2?)$/i.test(r) },
  { name: "ours.systemdev", test: (r) => r.startsWith("SystemDev/") },
  { name: "ours.chatdev",   test: (r) => r.startsWith("ChatDev/") },
  { name: "ours.gamedev",   test: (r) => r.startsWith("GameDev/") && !r.startsWith("GameDev/engine/godot/.import/") },
  { name: "ours.previewui", test: (r) => r.startsWith("PreviewUI/") },
  { name: "ours.src",       test: (r) => /^(src|scripts|config|logger|kpulse|knowledge|Sectors)\//.test(r) },
  { name: "third_party_vendored", test: (r) => r.startsWith("vendor/") || r.startsWith("third_party/") },
];

const ignoreDirs = new Set<string>([
  ".git", ".github", ".githooks", ".vscode", ".idea",
  "node_modules", ".yarn", ".pnpm-store", ".venv",
  "dist", "build", "out", "coverage", ".next", ".vite", ".svelte-kit", ".cache",
  "GameDev/engine/godot/.import", ".godot"
]);

const hashable = (r: string) => /\.(md|txt|rtf|json|ya?ml|toml|lock|ts|tsx|js|jsx|cjs|mjs|gd|cs|py|cfg|ini)$/i.test(r);

const walk = async (dir: string, acc: string[] = []) => {
  const ents = await fs.readdir(dir, { withFileTypes: true });
  for (const e of ents) {
    const abs = path.join(dir, e.name);
    const rel = path.relative(repoRoot, abs).replace(/\\/g, "/");
    if (e.isDirectory()) {
      // Skip massive tool/build dirs during first pass classification, but still count sizes via du later if needed.
      if (ignoreDirs.has(rel) || Array.from(ignoreDirs).some(x => rel.startsWith(x + "/"))) continue;
      await walk(abs, acc);
    } else if (e.isFile()) {
      acc.push(rel);
    } else if (e.isSymbolicLink()) {
      acc.push(rel); // handled in symlink probe
    }
  }
  return acc;
};

const fileSize = async (abs: string) => (await fs.stat(abs)).size;

const sha1 = async (abs: string) => {
  const data = await fs.readFile(abs);
  return crypto.createHash("sha1").update(data).digest("hex");
};

async function main() {
  const started = new Date().toISOString();
  console.log('🔍 SAGE-PILOT Provenance Audit Starting...');
  
  const all = await walk(repoRoot, []);
  const tally: Tally = {};
  const bytes: Record<string, Bytes> = {};
  const externals: { rel: string; resolvesTo: string }[] = [];
  const nameHistogram: Record<string, number> = {};
  const dirNameHistogram: Record<string, number> = {};
  const similarNameDirs: Record<string, string[]> = {};
  const shaToPaths: Record<string, string[]> = {};
  let filesClassified = 0;

  for (const rel of all) {
    const abs = path.join(repoRoot, rel);
    // symlink/external check (best-effort)
    try {
      const real = await fs.realpath(abs);
      if (!isWithin(real)) {
        externals.push({ rel, resolvesTo: real });
      }
    } catch { /* ignore */ }

    const size = await fileSize(abs);
    let cat = "unknown";
    for (const rule of catRules) {
      if (rule.test(rel, abs, size)) { cat = rule.name; break; }
    }
    tally[cat] = (tally[cat] || 0) + 1;
    bytes[cat] = (bytes[cat] || 0) + size;
    filesClassified++;

    // duplicate & name histos
    const base = path.basename(rel);
    nameHistogram[base] = (nameHistogram[base] || 0) + 1;
    const dirname = path.dirname(rel);
    const leaf = path.basename(dirname);
    dirNameHistogram[leaf] = (dirNameHistogram[leaf] || 0) + 1;

    if (hashable(rel) && size <= 2_000_000) {
      try {
        const h = await sha1(abs);
        (shaToPaths[h] ||= []).push(rel);
      } catch {}
    }
  }

  // find dir-name collisions (same leaf name appearing many times)
  for (const [leaf, count] of Object.entries(dirNameHistogram)) {
    if (count >= 3) {
      similarNameDirs[leaf] = Object.keys(dirNameHistogram)
        .filter(k => k === leaf)
        .slice(0, 10);
    }
  }

  // big duplicates (exact content)
  const dupClusters = Object.values(shaToPaths).filter(arr => arr.length >= 2)
                        .sort((a,b)=>b.length-a.length).slice(0, 50);

  // lockfiles & submodule clues
  const clues: Record<string, boolean> = {
    pnpm: false, yarn: false, npm: false, poetry: false, gitmodules: false
  };
  const maybeTrue = async (p: string) => { try { await fs.access(path.join(repoRoot, p)); return true; } catch { return false; } };
  clues.pnpm = await maybeTrue("pnpm-lock.yaml");
  clues.yarn = await maybeTrue("yarn.lock");
  clues.npm = await maybeTrue("package-lock.json");
  clues.poetry = await maybeTrue("poetry.lock");
  clues.gitmodules = await maybeTrue(".gitmodules");

  const ended = new Date().toISOString();
  const out = {
    stage: "provenance_audit",
    started, ended,
    files_scanned: filesClassified,
    categories: tally,
    sizes_bytes: bytes,
    package_total: (tally["pkg.node"]||0)+(tally["pkg.py"]||0)+(tally["pkg.godot"]||0),
    build_total: (tally["build"]||0),
    our_code_total: (tally["ours.systemdev"]||0)+(tally["ours.chatdev"]||0)+(tally["ours.gamedev"]||0)+(tally["ours.previewui"]||0)+(tally["ours.src"]||0),
    tools_total: (tally["tools"]||0),
    assets_total: (tally["assets"]||0),
    unknown_total: (tally["unknown"]||0),
    externals, // symlinks resolving outside root (critical!)
    lockfile_clues: clues,
    top_duplicate_clusters: dupClusters.slice(0, 20),
    hot_filenames: Object.entries(nameHistogram).filter(([_,n])=>n>=5).sort((a,b)=>b[1]-a[1]).slice(0,50),
    similar_dirnames: similarNameDirs,
    next_hints: [
      "Quarantine build artifacts (build/, dist/, out/, *.map) into attic/build_quarantine with pointers",
      "Adopt path_alias_map.json for moved modules (Artificer import rewrite)",
      "Collapse exact-duplicate clusters into canonical locations",
      "Investigate externals[] for any out-of-repo symlink leakage",
      "Decide default package manager from lockfile_clues"
    ]
  };

  await fs.mkdir(path.join(repoRoot, "SystemDev/reports"), { recursive: true });
  await fs.mkdir(path.join(repoRoot, "SystemDev/receipts"), { recursive: true });
  
  const stamp = new Date().toISOString().replace(/[:.]/g,"-");
  const reportPath = path.join(repoRoot, `SystemDev/reports/provenance_audit_${stamp}.json`);
  const receiptPath = path.join(repoRoot, `SystemDev/receipts/provenance_audit_${stamp}.json`);
  
  // Write detailed report
  await fs.writeFile(reportPath, JSON.stringify(out, null, 2));
  
  // Write receipt
  const receipt = {
    stage: 'provenance_audit',
    timestamp: ended,
    files_scanned: filesClassified,
    package_vs_our_code: `${out.package_total} packages vs ${out.our_code_total} our code`,
    externals_detected: externals.length,
    duplicates_detected: dupClusters.length,
    top_bloat_category: Object.entries(tally).sort(([,a], [,b]) => b - a)[0],
    next_hint: externals.length > 0 ? 'Investigate external symlinks' : 'Proceed with bloat quarantine'
  };
  
  await fs.writeFile(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`✅ Provenance audit complete: ${filesClassified} files classified`);
  console.log(`📊 Package files: ${out.package_total}, Our code: ${out.our_code_total}`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`📄 Receipt: ${receiptPath}`);
  
  if (externals.length > 0) {
    console.log(`⚠️  External symlinks detected: ${externals.length}`);
  }
}

// Run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}