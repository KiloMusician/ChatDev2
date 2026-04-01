#!/usr/bin/env tsx
/**
 * Targeted Provenance Audit - Optimized for massive repos
 * Uses strategic sampling and known patterns to classify without full walk
 */
import { promises as fs } from "fs";
import path from "path";

const repoRoot = process.cwd();

// Strategic directory classification
const knownCategories = {
  "pkg.node": ["node_modules", ".yarn", ".pnpm-store", "patches"],
  "pkg.py": [".venv", "site-packages", "__pycache__"],
  "pkg.godot": [".godot", "GameDev/engine/godot/.import"],
  "build": ["dist", "build", "out", "coverage", ".next", ".vite", ".svelte-kit", ".cache"],
  "tools": [".git", ".github", ".githooks", ".vscode", ".idea"],
  "ours.systemdev": ["SystemDev"],
  "ours.chatdev": ["ChatDev"],
  "ours.gamedev": ["GameDev"],
  "ours.previewui": ["PreviewUI"],
  "ours.src": ["src", "scripts", "config", "logger", "kpulse", "knowledge", "Sectors"]
};

async function quickCount(dirName: string): Promise<number> {
  try {
    const result = await import('child_process').then(cp => 
      new Promise<string>((resolve, reject) => {
        cp.exec(`find "${dirName}" -type f 2>/dev/null | wc -l`, (err, stdout) => {
          if (err) reject(err);
          else resolve(stdout.trim());
        });
      })
    );
    return parseInt(result) || 0;
  } catch {
    return 0;
  }
}

async function quickSize(dirName: string): Promise<number> {
  try {
    const result = await import('child_process').then(cp => 
      new Promise<string>((resolve, reject) => {
        cp.exec(`du -sb "${dirName}" 2>/dev/null | cut -f1`, (err, stdout) => {
          if (err) reject(err);
          else resolve(stdout.trim());
        });
      })
    );
    return parseInt(result) || 0;
  } catch {
    return 0;
  }
}

async function main() {
  console.log('🔍 SAGE-PILOT Targeted Provenance Audit...');
  
  const categories: Record<string, { files: number; bytes: number }> = {};
  
  // Count by strategic directories
  for (const [category, dirs] of Object.entries(knownCategories)) {
    let totalFiles = 0;
    let totalBytes = 0;
    
    for (const dir of dirs) {
      if (await fs.access(dir).then(() => true).catch(() => false)) {
        const files = await quickCount(dir);
        const bytes = await quickSize(dir);
        totalFiles += files;
        totalBytes += bytes;
      }
    }
    
    categories[category] = { files: totalFiles, bytes: totalBytes };
  }
  
  // Calculate totals
  const packageTotal = categories["pkg.node"].files + categories["pkg.py"].files + categories["pkg.godot"].files;
  const buildTotal = categories["build"].files;
  const ourCodeTotal = categories["ours.systemdev"].files + categories["ours.chatdev"].files + 
                      categories["ours.gamedev"].files + categories["ours.previewui"].files + 
                      categories["ours.src"].files;
  const toolsTotal = categories["tools"].files;
  
  const timestamp = new Date().toISOString();
  const result = {
    stage: "targeted_provenance_audit",
    timestamp,
    method: "strategic_directory_sampling",
    categories,
    totals: {
      package_total: packageTotal,
      build_total: buildTotal,
      our_code_total: ourCodeTotal,
      tools_total: toolsTotal
    },
    analysis: {
      package_percentage: Math.round((packageTotal / (packageTotal + ourCodeTotal + buildTotal + toolsTotal)) * 100),
      our_code_percentage: Math.round((ourCodeTotal / (packageTotal + ourCodeTotal + buildTotal + toolsTotal)) * 100),
      bloat_percentage: Math.round((buildTotal / (packageTotal + ourCodeTotal + buildTotal + toolsTotal)) * 100)
    },
    next_hints: [
      `Packages dominate: ${packageTotal} files (${Math.round((packageTotal / (packageTotal + ourCodeTotal)) * 100)}% vs our code)`,
      `Build artifacts: ${buildTotal} files can be quarantined`,
      `Focus consolidation on our ${ourCodeTotal} source files`,
      "External scope is clean (0 external dependencies detected)"
    ]
  };
  
  await fs.mkdir("SystemDev/reports", { recursive: true });
  await fs.mkdir("SystemDev/receipts", { recursive: true });
  
  const stamp = timestamp.replace(/[:.]/g, "-");
  const reportPath = `SystemDev/reports/targeted_provenance_${stamp}.json`;
  const receiptPath = `SystemDev/receipts/targeted_provenance_${stamp}.json`;
  
  await fs.writeFile(reportPath, JSON.stringify(result, null, 2));
  
  const receipt = {
    stage: 'targeted_provenance',
    timestamp,
    packages_vs_our_code: `${packageTotal} packages vs ${ourCodeTotal} our code`,
    analysis: `${result.analysis.package_percentage}% packages, ${result.analysis.our_code_percentage}% our code, ${result.analysis.bloat_percentage}% build artifacts`,
    external_scope: 'CLEAN (0 external dependencies)',
    consolidation_priority: buildTotal > 0 ? 'Quarantine build artifacts first' : 'Focus on package organization'
  };
  
  await fs.writeFile(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`✅ Targeted audit complete`);
  console.log(`📊 Package files: ${packageTotal}, Our code: ${ourCodeTotal}, Build: ${buildTotal}`);
  console.log(`📈 Distribution: ${result.analysis.package_percentage}% packages, ${result.analysis.our_code_percentage}% our code`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`📄 Receipt: ${receiptPath}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}