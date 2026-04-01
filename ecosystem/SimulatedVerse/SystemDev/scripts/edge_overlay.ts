#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Overlay - VFS WorkingSet for Agent Performance
 * Creates a filtered view of the repository for fast agent operations
 */
import Database from "better-sqlite3";
import fs from "fs";
import path from "path";
import { Command } from "commander";
import chalk from "chalk";

const program = new Command()
  .option("--include-buckets <csv>", "comma list", "ours.systemdev,ours.chatdev,ours.gamedev,ours.previewui,ours.src")
  .option("--max <n>", "max files", "20000")
  .option("--symlinks", "materialize symlinks", false)
  .option("--clean", "clean existing overlay", false)
  .parse();
const opts = program.opts();

async function main() {
  console.log(chalk.cyan("🔗 ΞNuSyQ Edge Overlay - Creating WorkingSet"));
  
  const db = new Database("SystemDev/.edge/edge.db", { readonly: true });
  const BUCKETS = (opts.includeBuckets as string).split(",").map((s) => s.trim());
  
  console.log(chalk.yellow(`📦 Including buckets: ${BUCKETS.join(", ")}`));
  
  const rows = db.prepare(`
    SELECT path,size,bucket,kind FROM files WHERE bucket IN (${BUCKETS.map(() => "?").join(",")})
    ORDER BY size ASC LIMIT ?;
  `).all(...BUCKETS, parseInt(opts.max, 10));

  const root = "SystemDev/.edge/overlay";
  
  if (opts.clean) {
    console.log(chalk.gray("🧹 Cleaning existing overlay..."));
    fs.rmSync(root, { recursive: true, force: true });
  }
  
  fs.mkdirSync(root, { recursive: true });
  
  const roster = {
    timestamp: Date.now(),
    count: rows.length,
    buckets: BUCKETS,
    max_files: parseInt(opts.max, 10),
    files: rows
  };
  
  const rosterPath = path.join(root, "roster.json");
  fs.writeFileSync(rosterPath, JSON.stringify(roster, null, 2));
  
  console.log(chalk.green(`📋 Roster created: ${rows.length} files`));

  if (opts.symlinks) {
    const ws = path.join(root, "WorkingSet");
    fs.rmSync(ws, { recursive: true, force: true });
    fs.mkdirSync(ws, { recursive: true });
    
    console.log(chalk.yellow("🔗 Creating symlinks..."));
    let linked = 0;
    
    for (const r of rows) {
      const dst = path.join(ws, r.path.replace(/\//g, "__"));
      try {
        const srcPath = path.resolve(r.path);
        if (fs.existsSync(srcPath)) {
          fs.symlinkSync(srcPath, dst);
          linked++;
        }
      } catch (e) {
        // Ignore symlink failures
      }
    }
    
    console.log(chalk.green(`🔗 Created ${linked} symlinks in WorkingSet/`));
  }

  // Generate receipt
  const receipt = {
    breath: "ΞΘΛΔ_overlay",
    timestamp: new Date().toISOString(),
    working_set_files: rows.length,
    buckets_included: BUCKETS,
    symlinks_created: opts.symlinks,
    max_limit: parseInt(opts.max, 10),
    overlay_path: root
  };
  
  const receiptPath = `SystemDev/receipts/edge_overlay_${Date.now()}.json`;
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(chalk.blue(`📄 Receipt: ${receiptPath}`));
  console.log(chalk.magenta(`✅ WorkingSet ready → ${rows.length} files in ${root}`));
  
  // Show bucket breakdown
  const bucketCounts = rows.reduce((acc: Record<string, number>, row: any) => {
    acc[row.bucket] = (acc[row.bucket] || 0) + 1;
    return acc;
  }, {});
  
  console.log(chalk.cyan("\n📊 WorkingSet breakdown:"));
  Object.entries(bucketCounts).forEach(([bucket, count]) => {
    console.log(chalk.gray(`   ${bucket}: ${count} files`));
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}