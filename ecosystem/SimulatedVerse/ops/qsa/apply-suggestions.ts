#!/usr/bin/env tsx
import { promises as fs } from "node:fs";
import { dirname } from "node:path";

const DRY = process.env.DRY_RUN !== "0";

async function safeMove(from: string, to: string) {
  await fs.mkdir(dirname(to), { recursive: true });
  if (DRY) { console.log(`[dry] mv ${from} -> ${to}`); return; }
  await fs.rename(from, to).catch(async () => {
    const data = await fs.readFile(from);
    await fs.writeFile(to, data);
    await fs.unlink(from);
  });
}

// Example: move giant logs/spam to /attic/
async function main() {
  const spam = JSON.parse(await fs.readFile("reports/qsa/spam.json","utf8"));
  for (const s of spam.spam.filter((x:any)=>x.size>2_000_000)) {
    const target = `attic/${s.path}`.replace(/^\.?\//,"");
    await safeMove(s.path, target);
  }
  console.log("[qsa] apply-suggestions done (dry? " + DRY + ")");
}

main().catch(e=>{ console.error(e); process.exit(1); });