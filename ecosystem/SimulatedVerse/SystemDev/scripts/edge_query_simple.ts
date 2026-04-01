#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Query - Simple Database Query Tool
 * Replaces symlink overlay with direct database queries
 * 
 * Usage:
 *   tsx SystemDev/scripts/edge_query_simple.ts --bucket=ours.src --kind=typescript
 *   tsx SystemDev/scripts/edge_query_simple.ts --search="drizzle" --limit=20
 *   tsx SystemDev/scripts/edge_query_simple.ts --stats
 */
import Database from "better-sqlite3";
import { Command } from "commander";
import chalk from "chalk";
import path from "path";

const program = new Command()
  .option("--bucket <name>", "filter by bucket (e.g., ours.src, ours.systemdev)")
  .option("--kind <type>", "filter by kind (e.g., typescript, javascript, python)")
  .option("--search <term>", "full-text search term")
  .option("--limit <n>", "max results", "50")
  .option("--stats", "show database statistics")
  .option("--export <path>", "export results to JSON file")
  .parse();

const opts = program.opts();

async function main() {
  const dbPath = process.env.EDGE_DB_PATH || "SystemDev/.edge/edge.db";
  
  if (!require("fs").existsSync(dbPath)) {
    console.error(chalk.red(`❌ Database not found: ${dbPath}`));
    console.log(chalk.yellow("Run: tsx SystemDev/scripts/edge_index.ts --fts"));
    process.exit(1);
  }

  const db = new Database(dbPath, { readonly: true });
  
  console.log(chalk.cyan("🔍 ΞNuSyQ Edge Query\n"));
  
  // Show statistics
  if (opts.stats) {
    const stats = db.prepare(`
      SELECT 
        COUNT(*) as total_files,
        COUNT(DISTINCT bucket) as buckets,
        SUM(size) as total_bytes
      FROM files
    `).get() as any;
    
    const bucketBreakdown = db.prepare(`
      SELECT bucket, COUNT(*) as count, SUM(size) as bytes
      FROM files
      GROUP BY bucket
      ORDER BY count DESC
    `).all();
    
    console.log(chalk.bold("📊 Database Statistics:"));
    console.log(`   Total Files: ${chalk.green(stats.total_files.toLocaleString())}`);
    console.log(`   Total Size: ${chalk.green((stats.total_bytes / 1024 / 1024).toFixed(2))} MB`);
    console.log(`   Buckets: ${chalk.green(stats.buckets)}\n`);
    
    console.log(chalk.bold("📦 Bucket Breakdown:"));
    for (const b of bucketBreakdown) {
      const pct = ((b.count / stats.total_files) * 100).toFixed(1);
      console.log(`   ${chalk.yellow(b.bucket.padEnd(20))} ${String(b.count).padStart(7)} files (${pct}%)`);
    }
    
    db.close();
    return;
  }
  
  // Build query
  let query = "SELECT path, size, bucket, kind FROM files WHERE 1=1";
  const params: any[] = [];
  
  if (opts.bucket) {
    query += " AND bucket = ?";
    params.push(opts.bucket);
  }
  
  if (opts.kind) {
    query += " AND kind = ?";
    params.push(opts.kind);
  }
  
  if (opts.search) {
    // Use FTS5 if available
    const hasFts = db.prepare(`
      SELECT name FROM sqlite_master 
      WHERE type='table' AND name='files_fts'
    `).get();
    
    if (hasFts) {
      query = `
        SELECT f.path, f.size, f.bucket, f.kind
        FROM files f
        JOIN files_fts fts ON f.path = fts.path
        WHERE fts.path MATCH ?
      `;
      params.length = 0; // Clear previous params
      params.push(opts.search);
    } else {
      query += " AND path LIKE ?";
      params.push(`%${opts.search}%`);
    }
  }
  
  query += ` ORDER BY size ASC LIMIT ?`;
  params.push(parseInt(opts.limit, 10));
  
  // Execute query
  const results = db.prepare(query).all(...params);
  
  console.log(chalk.bold(`📄 Results: ${results.length} files\n`));
  
  if (results.length === 0) {
    console.log(chalk.gray("No files found matching criteria."));
    db.close();
    return;
  }
  
  // Display results
  for (const r of results as any[]) {
    const sizeKb = (r.size / 1024).toFixed(1);
    console.log(`${chalk.green(r.path.padEnd(60))} ${chalk.gray(sizeKb.padStart(8))} KB ${chalk.yellow(r.bucket)}`);
  }
  
  console.log(chalk.gray(`\n(showing ${results.length} of max ${opts.limit})`));
  
  // Export if requested
  if (opts.export) {
    const exportData = {
      timestamp: new Date().toISOString(),
      query: { bucket: opts.bucket, kind: opts.kind, search: opts.search, limit: opts.limit },
      count: results.length,
      files: results
    };
    
    require("fs").writeFileSync(opts.export, JSON.stringify(exportData, null, 2));
    console.log(chalk.blue(`\n💾 Exported to: ${opts.export}`));
  }
  
  db.close();
}

main().catch(console.error);
