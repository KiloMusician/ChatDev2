#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Counts - Instant Repository Analysis
 * Answers: "How many files are packages vs our code?"
 */
import Database from "better-sqlite3";
import fs from "fs";
import chalk from "chalk";

async function main() {
  console.log(chalk.cyan("📊 ΞNuSyQ Edge Counts - Repository Analysis"));
  
  const db = new Database("SystemDev/.edge/edge.db", { readonly: true });
  const buckets = db.prepare(`SELECT bucket, COUNT(*) c, SUM(size) s FROM files GROUP BY bucket ORDER BY c DESC`).all();
  
  const ours = buckets.filter((b: any) => b.bucket.startsWith("ours."));
  const pkg = buckets.filter((b: any) => b.bucket.startsWith("pkg."));
  const build = buckets.filter((b: any) => b.bucket === "build").map((x: any) => x.c).reduce((a: number, b: number) => a + b, 0);
  const other = buckets.filter((b: any) => !b.bucket.startsWith("ours.") && !b.bucket.startsWith("pkg.") && b.bucket !== "build");

  const totals = {
    ours: ours.reduce((a, b) => a + b.c, 0),
    packages: pkg.reduce((a, b) => a + b.c, 0),
    build,
    other: other.reduce((a, b) => a + b.c, 0)
  };
  
  const totalFiles = totals.ours + totals.packages + totals.build + totals.other;
  
  const out = {
    breath: "ΞΘΛΔ_counts",
    timestamp: new Date().toISOString(),
    totals,
    percentages: {
      ours: Math.round((totals.ours / totalFiles) * 100),
      packages: Math.round((totals.packages / totalFiles) * 100),
      build: Math.round((totals.build / totalFiles) * 100),
      other: Math.round((totals.other / totalFiles) * 100)
    },
    breakdown: { ours, pkg, build, other }
  };
  
  const receiptPath = `SystemDev/receipts/edge_counts_${Date.now()}.json`;
  fs.writeFileSync(receiptPath, JSON.stringify(out, null, 2));
  
  console.log(chalk.green("✅ Repository analysis complete!"));
  console.log(chalk.yellow(`📁 Total files: ${totalFiles.toLocaleString()}`));
  console.log(chalk.blue("\n📊 File distribution:"));
  console.log(chalk.gray(`   Our code: ${totals.ours.toLocaleString()} (${out.percentages.ours}%)`));
  console.log(chalk.gray(`   Packages: ${totals.packages.toLocaleString()} (${out.percentages.packages}%)`));
  console.log(chalk.gray(`   Build artifacts: ${totals.build.toLocaleString()} (${out.percentages.build}%)`));
  console.log(chalk.gray(`   Other: ${totals.other.toLocaleString()} (${out.percentages.other}%)`));
  
  console.log(chalk.cyan("\n🗂️  Our code breakdown:"));
  ours.forEach((b: any) => {
    console.log(chalk.gray(`   ${b.bucket}: ${b.c.toLocaleString()} files`));
  });
  
  console.log(chalk.magenta(`📄 Receipt: ${receiptPath}`));
  
  // Also output JSON for programmatic use
  console.log(JSON.stringify(out, null, 2));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}