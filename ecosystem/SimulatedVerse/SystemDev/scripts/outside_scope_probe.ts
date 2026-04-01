#!/usr/bin/env tsx
/**
 * Outside-Scope Probe
 * Detects requires/imports resolving outside repo, and symlinks that point out.
 * Dry-run only; writes a receipt with suspicious paths.
 */
import { promises as fs } from "fs";
import path from "path";
import module from "module";

const repoRoot = process.cwd();
const isWithin = (p: string) => path.resolve(p).startsWith(repoRoot + path.sep);

const scanGlobs = [
  "src", "scripts", "SystemDev", "ChatDev", "GameDev", "PreviewUI"
];

const collectFiles = async (dir: string, bag: string[] = []) => {
  try {
    const ents = await fs.readdir(dir, { withFileTypes: true });
    for (const e of ents) {
      const abs = path.join(dir, e.name);
      const rel = path.relative(repoRoot, abs).replace(/\\/g,"/");
      if (e.isDirectory()) {
        await collectFiles(abs, bag);
      } else if (e.isFile()) {
        if (/\.(ts|tsx|js|jsx|mjs|cjs|gd|py|cs)$/i.test(rel)) bag.push(abs);
      } else if (e.isSymbolicLink()) {
        const real = await fs.realpath(abs).catch(()=>abs);
        if (!isWithin(real)) suspicious.symlinks.push({ rel, resolvesTo: real });
      }
    }
  } catch {}
  return bag;
};

const suspicious: {
  requires_outside: { from: string; spec: string; resolved: string }[];
  symlinks: { rel: string; resolvesTo: string }[];
} = { requires_outside: [], symlinks: [] };

async function main() {
  console.log('🔍 SAGE-PILOT Outside-Scope Probe Starting...');
  
  const resolver = module.createRequire(path.join(repoRoot, "package.json"));
  for (const g of scanGlobs) {
    const root = path.join(repoRoot, g);
    // Skip if directory doesn't exist
    try {
      await fs.access(root);
    } catch {
      continue;
    }
    
    const files = await collectFiles(root);
    for (const abs of files) {
      const rel = path.relative(repoRoot, abs).replace(/\\/g,"/");
      const content = await fs.readFile(abs, "utf8").catch(()=> "");
      const specs = Array.from(content.matchAll(/from\s+['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)/g))
        .map(m => (m[1] || m[2])).filter(Boolean);

      for (const spec of specs) {
        if (/^(https?:|file:)/.test(spec)) {
          // explicit url/file protocols: flag as outside
          suspicious.requires_outside.push({ from: rel, spec, resolved: spec });
          continue;
        }
        try {
          const resolved = resolver.resolve(spec, { paths: [path.dirname(abs)] });
          if (!isWithin(resolved)) {
            suspicious.requires_outside.push({ from: rel, spec, resolved });
          }
        } catch {
          // unresolved is interesting but not outside-of-repo proof; skip
        }
      }
    }
  }
  
  const stamp = new Date().toISOString().replace(/[:.]/g,"-");
  await fs.mkdir(path.join(repoRoot, "SystemDev/reports"), { recursive: true });
  await fs.mkdir(path.join(repoRoot, "SystemDev/receipts"), { recursive: true });
  
  const reportPath = path.join(repoRoot, `SystemDev/reports/outside_scope_probe_${stamp}.json`);
  const receiptPath = path.join(repoRoot, `SystemDev/receipts/outside_scope_probe_${stamp}.json`);
  
  // Write detailed report
  await fs.writeFile(reportPath, JSON.stringify(suspicious, null, 2));
  
  // Write receipt
  const receipt = {
    stage: 'outside_scope_probe',
    timestamp: new Date().toISOString(),
    external_requires: suspicious.requires_outside.length,
    external_symlinks: suspicious.symlinks.length,
    total_externals: suspicious.requires_outside.length + suspicious.symlinks.length,
    concern_level: suspicious.requires_outside.length + suspicious.symlinks.length > 0 ? 'HIGH' : 'CLEAN',
    next_hint: suspicious.requires_outside.length + suspicious.symlinks.length > 0 ? 'Review external dependencies in report' : 'No external scope detected'
  };
  
  await fs.writeFile(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`✅ Outside-scope probe complete`);
  console.log(`🔗 External requires: ${suspicious.requires_outside.length}`);
  console.log(`🔗 External symlinks: ${suspicious.symlinks.length}`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`📄 Receipt: ${receiptPath}`);
}

// Run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}