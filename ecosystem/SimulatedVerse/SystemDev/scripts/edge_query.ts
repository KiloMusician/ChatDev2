#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Query System
 * Fast searches with FTS5 and ripgrep fallback
 */
import Database from "better-sqlite3";
import { Command } from "commander";
import { spawnSync } from "child_process";
import path from "path";
import chalk from "chalk";

const program = new Command()
  .option("-t, --text <q>", "full-text search (fts)")
  .option("-g, --glob <pattern>", "glob-ish via LIKE: e.g. %.ts")
  .option("-b, --bucket <bucket>", "bucket filter (ours.src, ours.gamedev, pkg.node, ...)")
  .option("-l, --limit <n>", "limit", "100")
  .option("-s, --stats", "show statistics", false)
  .parse();

const { text, glob, bucket, limit, stats } = program.opts();

function likeify(glob: string) {
  return glob.replace(/\*/g, "%").replace(/\?/g, "_");
}

async function main() {
  const db = new Database("SystemDev/.edge/edge.db", { readonly: true });
  
  if (stats) {
    const total = db.prepare("SELECT COUNT(*) as count FROM files").get() as any;
    const buckets = db.prepare("SELECT bucket, COUNT(*) c FROM files GROUP BY bucket ORDER BY c DESC").all();
    console.log(chalk.cyan("📊 Edge Database Statistics"));
    console.log(chalk.yellow(`Total files indexed: ${total.count}`));
    console.log(chalk.blue("\nBucket breakdown:"));
    buckets.forEach((b: any) => {
      console.log(chalk.gray(`  ${b.bucket}: ${b.c} files`));
    });
    return;
  }

  if (text) {
    console.log(chalk.cyan(`🔍 Full-text search: "${text}"`));
    
    // Prefer SQLite FTS. If index lacks content (old shard), fallback to ripgrep if available.
    const has = db.prepare("SELECT count(*) c FROM sqlite_master WHERE name='content_fts'").get() as any;
    if (has.c > 0) {
      const rows = db.prepare(`
        SELECT path FROM content_fts WHERE content_fts MATCH ? LIMIT ?;
      `).all(text, parseInt(limit, 10));
      
      console.log(chalk.green(`📄 Found ${rows.length} matches via FTS5`));
      rows.forEach((r: any) => console.log(chalk.gray(`  ${r.path}`)));
      
      const result = { mode: "fts", count: rows.length, paths: rows.map((r: any) => r.path) };
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(chalk.yellow("⚠️  FTS5 index not available, falling back to ripgrep"));
      const rg = spawnSync("rg", ["-n", "--no-heading", text, "."], { encoding: "utf8" });
      
      if (rg.status === 0) {
        const lines = rg.stdout.split('\n').filter(Boolean).slice(0, parseInt(limit, 10));
        console.log(chalk.green(`📄 Found ${lines.length} matches via ripgrep`));
        lines.forEach(line => console.log(chalk.gray(`  ${line}`)));
      } else {
        console.log(chalk.red("❌ Ripgrep search failed"));
      }
      
      console.log(JSON.stringify({ mode: "ripgrep", status: rg.status, stdout: rg.stdout }, null, 2));
    }
  } else {
    // Metadata query
    const conditions: string[] = [];
    const params: any[] = [];
    if (glob) { conditions.push("path LIKE ?"); params.push(likeify(glob)); }
    if (bucket) { conditions.push("bucket = ?"); params.push(bucket); }
    const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
    const q = `SELECT path,size,bucket,kind FROM files ${where} ORDER BY size DESC LIMIT ?;`;
    params.push(parseInt(limit, 10));
    
    const rows = db.prepare(q).all(...params);
    console.log(chalk.cyan(`📊 Metadata query results: ${rows.length} files`));
    
    rows.forEach((r: any) => {
      console.log(chalk.gray(`  ${r.path} (${r.size}b, ${r.bucket}, ${r.kind})`));
    });
    
    console.log(JSON.stringify({ mode: "meta", count: rows.length, rows }, null, 2));
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}