#!/usr/bin/env tsx
import { promises as fs } from "node:fs";
import * as path from "node:path";
import { spawn } from "node:child_process";

async function main() {
  const plan = path.join("reports/triage", "triage.move_plan.sh");
  try { await fs.access(plan); } catch { 
    console.error("Plan not found. Run: tsx ops/repo-triage.ts"); 
    process.exit(1);
  }
  const dry = process.argv.includes("--dry");
  if (dry) {
    const txt = await fs.readFile(plan, "utf8");
    console.log("=== DRY RUN: plan preview ===\n");
    console.log(txt.split("\n").slice(0, 60).join("\n"));
    process.exit(0);
  }
  console.log("Applying move plan...");
  await new Promise((res, rej) => {
    const p = spawn("bash", [plan], { stdio: "inherit" });
    p.on("exit", (c) => c === 0 ? res(null) : rej(new Error(`exit ${c}`)));
  });
  console.log("Done.");
}
main().catch(e => { console.error(e); process.exit(1); });