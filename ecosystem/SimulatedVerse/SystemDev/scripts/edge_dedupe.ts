#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Deduplication - Near-Duplicate Detection
 * Uses content-based signatures to find similar files for consolidation
 */
import Database from "better-sqlite3";
import fs from "fs";
import path from "path";
import { Command } from "commander";
import crypto from "crypto";
import chalk from "chalk";

const program = new Command()
  .option("--threshold <n>", "Similarity threshold (1-100)", "82")
  .option("--max <n>", "max candidates", "25000")
  .option("--min-size <n>", "minimum file size", "50")
  .option("--max-size <n>", "maximum file size", "300000")
  .parse();
const opts = program.opts();

function tokensOf(txt: string) {
  return txt.toLowerCase().split(/[^a-z0-9_]+/).filter(Boolean).slice(0, 1200);
}

function sigOf(tokens: string[]) {
  // Cheap 64-bit sim signature via hash slices
  const h = crypto.createHash("sha256").update(tokens.join("|")).digest("hex");
  return h.slice(0, 16); // group key
}

function jaccardSimilarity(a: string[], b: string[]): number {
  const setA = new Set(a);
  const setB = new Set(b);
  const intersection = new Set([...setA].filter(x => setB.has(x)));
  const union = new Set([...setA, ...setB]);
  return (intersection.size / union.size) * 100;
}

async function main() {
  console.log(chalk.cyan("🔍 ΞNuSyQ Edge Deduplication - Near-Duplicate Analysis"));
  
  const db = new Database("SystemDev/.edge/edge.db", { readonly: true });
  const rows = db.prepare(`
    SELECT path, size, bucket, kind FROM files
    WHERE bucket LIKE 'ours.%' 
    AND size BETWEEN ? AND ?
    AND kind LIKE 'text.%'
    ORDER BY size DESC
    LIMIT ?;
  `).all(parseInt(opts.minSize, 10), parseInt(opts.maxSize, 10), parseInt(opts.max, 10));

  console.log(chalk.yellow(`📊 Analyzing ${rows.length} files for near-duplicates`));

  const buckets = new Map<string, { path: string; size: number; tokens: string[] }[]>();
  const fileTokens = new Map<string, string[]>();
  
  // Group by signature and collect tokens
  for (const r of rows) {
    try {
      const buf = fs.readFileSync(r.path, "utf8");
      const tokens = tokensOf(buf);
      const sig = sigOf(tokens);
      
      if (!buckets.has(sig)) buckets.set(sig, []);
      buckets.get(sig)!.push({ path: r.path, size: r.size, tokens });
      fileTokens.set(r.path, tokens);
    } catch {
      // Skip files that can't be read
    }
  }

  // Find groups with exact signatures
  const exactGroups = [...buckets.values()].filter(g => g.length > 1);
  
  // Find near-duplicate groups using more detailed comparison
  const nearGroups: Array<{ similarity: number; files: string[] }> = [];
  const threshold = parseInt(opts.threshold, 10);
  
  const allFiles = Array.from(fileTokens.keys());
  for (let i = 0; i < allFiles.length - 1; i++) {
    for (let j = i + 1; j < allFiles.length; j++) {
      const file1 = allFiles[i];
      const file2 = allFiles[j];
      const tokens1 = fileTokens.get(file1)!;
      const tokens2 = fileTokens.get(file2)!;
      
      const similarity = jaccardSimilarity(tokens1, tokens2);
      if (similarity >= threshold) {
        // Check if these files are already in an exact group
        const inExactGroup = exactGroups.some(group => 
          group.some(f => f.path === file1) && group.some(f => f.path === file2)
        );
        
        if (!inExactGroup) {
          nearGroups.push({
            similarity: Math.round(similarity),
            files: [file1, file2]
          });
        }
      }
    }
  }

  // Consolidate near groups to avoid overlaps
  const consolidatedNearGroups = nearGroups
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, 50); // Top 50 near-duplicate pairs

  const groups = [
    ...exactGroups.map(g => ({
      type: 'exact',
      similarity: 100,
      files: g.map(f => ({ path: f.path, size: f.size }))
    })),
    ...consolidatedNearGroups.map(g => ({
      type: 'near',
      similarity: g.similarity,
      files: g.files.map(path => ({ 
        path, 
        size: rows.find(r => r.path === path)?.size || 0 
      }))
    }))
  ].sort((a, b) => b.similarity - a.similarity);

  const out = {
    breath: "ΞΘΛΔ_dedupe",
    timestamp: new Date().toISOString(),
    threshold,
    candidates_analyzed: rows.length,
    exact_groups: exactGroups.length,
    near_groups: consolidatedNearGroups.length,
    total_groups: groups.length,
    groups: groups.slice(0, 100), // Top 100 groups
    consolidation_potential: {
      exact_duplicates: exactGroups.reduce((sum, g) => sum + (g.length - 1), 0),
      near_duplicates: consolidatedNearGroups.length
    }
  };

  const receiptPath = `SystemDev/receipts/edge_dedupe_${Date.now()}.json`;
  fs.writeFileSync(receiptPath, JSON.stringify(out, null, 2));

  console.log(chalk.green("✅ Deduplication analysis complete!"));
  console.log(chalk.blue(`📊 Found ${out.exact_groups} exact groups, ${out.near_groups} near-duplicate pairs`));
  console.log(chalk.yellow(`💾 Consolidation potential: ${out.consolidation_potential.exact_duplicates} exact + ${out.consolidation_potential.near_duplicates} near`));
  console.log(chalk.magenta(`📄 Receipt: ${receiptPath}`));

  if (groups.length > 0) {
    console.log(chalk.cyan("\n🔗 Top duplicate groups:"));
    groups.slice(0, 5).forEach((group, i) => {
      console.log(chalk.gray(`   ${i + 1}. ${group.type} (${group.similarity}% similarity)`));
      group.files.forEach(f => {
        console.log(chalk.gray(`      ${f.path} (${f.size}b)`));
      });
    });
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}