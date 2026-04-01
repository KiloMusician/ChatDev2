#!/usr/bin/env tsx
/**
 * Applies the move plan created by repo-auditor (using git mv when possible).
 * Default: DRY-RUN. Pass --apply to actually move.
 */
import fs from "node:fs";
import { execSync } from "node:child_process";
import path from "node:path";

const APPLY = process.argv.includes("--apply");
const planPath = "reports/repo_anneal.moves.json";
if (!fs.existsSync(planPath)) {
  console.error("[anneal] missing report. Run: tsx ops/repo-auditor.ts");
  process.exit(1);
}
type Move = { from:string; to:string; reason:string };
const moves: Move[] = JSON.parse(fs.readFileSync(planPath,"utf8"));

for (const m of moves) {
  const dstDir = path.dirname(m.to);
  if (!fs.existsSync(dstDir)) fs.mkdirSync(dstDir, { recursive: true });
  const cmd = `git mv -f "${m.from}" "${m.to}"`;
  if (APPLY) {
    try { execSync(cmd, { stdio: "inherit" }); } catch (e) {
      // fallback if git mv fails
      try { fs.renameSync(m.from, m.to); } catch {}
    }
  } else {
    console.log(`[dry-run] ${cmd}  # ${m.reason}`);
  }
}

console.log(APPLY ? "[anneal] applied." : "[anneal] dry-run complete. Use --apply to execute.");