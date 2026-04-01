#!/usr/bin/env tsx
/**
 * ΞNuSyQ Edge Indexer (Shardable)
 * Breath: ΞΘΛΔ_index  | Colony: ΞNuSyQ | Law: receipts-first
 * Buckets: pkg.node, pkg.py, pkg.godot, build, tools, ours.systemdev, ours.chatdev, ours.gamedev, ours.previewui, ours.src
 */
import fg from "fast-glob";
import Database from "better-sqlite3";
import xxhash from "xxhash-wasm";
import fs from "fs";
import path from "path";
import { Command } from "commander";
import ignore from "ignore";
import { performance } from "perf_hooks";
import chalk from "chalk";

const IGNORES = ignore().add([
  "**/.git/**","**/.github/**","**/.cache/**","**/.venv/**",
  "**/node_modules/**","**/.godot/**","**/dist/**","**/build/**","**/coverage/**"
]);
const DB_DIR = "SystemDev/.edge";
const RECEIPTS = "SystemDev/receipts";
fs.mkdirSync(DB_DIR, { recursive: true });
fs.mkdirSync(RECEIPTS, { recursive: true });

const program = new Command()
  .option("--shard-size <n>", "files per shard", "4000")
  .option("--fts", "index content into FTS", false)
  .option("--hash <algo>", "hash algo", "xxh3")
  .option("--root <dir>", "root dir", ".")
  .parse();
const opts = program.opts();

const db = new Database(path.join(DB_DIR, "edge.db"));
db.pragma("journal_mode = WAL");
db.exec(`
CREATE TABLE IF NOT EXISTS files(
  path TEXT PRIMARY KEY, size INTEGER, mtime INTEGER, kind TEXT, bucket TEXT, hash_xxh3 TEXT, lang TEXT, shard INTEGER
);
CREATE TABLE IF NOT EXISTS symbols(path TEXT, name TEXT, kind TEXT, loc_start INTEGER, loc_end INTEGER);
CREATE TABLE IF NOT EXISTS edges(src TEXT, dst TEXT, kind TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
`);
if (opts.fts) {
  db.exec(`CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(path, text, tokenize='porter');`);
}

function bucketFor(p: string): string {
  if (p.includes("/node_modules/")) return "pkg.node";
  if (p.includes("/.venv/") || p.includes("/site-packages/")) return "pkg.py";
  if (p.includes("/.godot/")) return "pkg.godot";
  if (p.match(/\/(dist|build|coverage)\//) || p.endsWith(".map")) return "build";
  if (p.startsWith(".git/") || p.startsWith(".github/")) return "tools";
  if (p.startsWith("SystemDev/")) return "ours.systemdev";
  if (p.startsWith("ChatDev/")) return "ours.chatdev";
  if (p.startsWith("GameDev/")) return "ours.gamedev";
  if (p.startsWith("PreviewUI/")) return "ours.previewui";
  if (p.startsWith("src/") || p.startsWith("scripts/") || p.startsWith("config/") || p.startsWith("knowledge/") || p.startsWith("Sectors/"))
    return "ours.src";
  return "other";
}

function kindFor(p: string): string {
  const ext = p.split(".").pop() || "";
  if (["ts","tsx","js","jsx","mjs","cjs"].includes(ext)) return "code.tsjs";
  if (["gd","cs","py","json","yaml","yml","toml","ini","md","rtf","txt"].includes(ext)) return `text.${ext}`;
  return `bin.${ext}`;
}

function langFor(p: string): string {
  const ext = p.split(".").pop() || "";
  if (["ts","tsx"].includes(ext)) return "ts";
  if (["js","jsx","mjs","cjs"].includes(ext)) return "js";
  if (ext === "gd") return "gdscript";
  if (ext === "cs") return "csharp";
  if (ext === "py") return "python";
  return "other";
}

async function main() {
  console.log(chalk.cyan("🔍 ΞNuSyQ Edge Indexer - Sharded Repository Analysis"));
  
  const t0 = performance.now();
  const xxh = await xxhash();
  const all = await fg(["**/*"], { dot: false, onlyFiles: true, cwd: opts.root });
  const files = all.filter(p => !IGNORES.ignores(p));
  const shardSize = parseInt(opts.shardSize, 10);
  let shard = 0, inserted = 0, fts = 0;

  console.log(chalk.yellow(`📊 Scanning ${files.length} files in shards of ${shardSize}`));

  const insert = db.prepare(`
    INSERT OR REPLACE INTO files(path,size,mtime,kind,bucket,hash_xxh3,lang,shard)
    VALUES(@path,@size,@mtime,@kind,@bucket,@hash_xxh3,@lang,@shard)
  `);
  const ftsInsert = opts.fts ? db.prepare(`INSERT INTO content_fts(path,text) VALUES(?,?)`) : null;

  for (let i = 0; i < files.length; i += shardSize) {
    const batch = files.slice(i, i + shardSize);
    shard++;
    console.log(chalk.gray(`⚡ Processing shard ${shard} (${batch.length} files)`));
    
    const tx = db.transaction(() => {
      for (const p of batch) {
        try {
          const st = fs.statSync(p);
          const bucket = bucketFor(p);
          const kind = kindFor(p);
          const lang = langFor(p);
          const buf = (st.size <= 2_000_000 && (bucket.startsWith("ours") || kind.startsWith("text."))) ? fs.readFileSync(p) : null;
          const hash_xxh3 = buf ? xxh.h32Raw(buf).toString(16) : null;
          insert.run({ path: p, size: st.size, mtime: Math.floor(st.mtimeMs), kind, bucket, hash_xxh3, lang, shard });
          inserted++;
          if (opts.fts && buf && bucket.startsWith("ours")) {
            ftsInsert!.run(p, buf.toString("utf8"));
            fts++;
          }
        } catch { /* swallow */ }
      }
    });
    tx();
  }

  const t1 = performance.now();
  const bucketStats = db.prepare(`SELECT bucket, COUNT(*) c FROM files GROUP BY bucket ORDER BY c DESC`).all();
  
  const receipt = {
    breath: "ΞΘΛΔ_index",
    timestamp: new Date().toISOString(),
    files_seen: files.length,
    inserted,
    fts_docs: fts,
    shards: shard,
    ms: Math.round(t1 - t0),
    buckets: bucketStats
  };
  
  const receiptPath = `${RECEIPTS}/edge_index_${Date.now()}.json`;
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(chalk.green("✅ Edge index complete!"));
  console.log(chalk.blue(`📈 Files: ${inserted} • FTS: ${fts} • Shards: ${shard} • Time: ${receipt.ms}ms`));
  console.log(chalk.magenta(`📄 Receipt: ${receiptPath}`));
  
  // Show top buckets
  console.log(chalk.cyan("\n🗂️  Top buckets:"));
  bucketStats.slice(0, 8).forEach((b: any) => {
    console.log(chalk.gray(`   ${b.bucket}: ${b.c} files`));
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}