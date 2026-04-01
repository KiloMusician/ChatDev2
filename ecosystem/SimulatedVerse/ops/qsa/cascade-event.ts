#!/usr/bin/env tsx
import { request } from "undici";
import { promises as fs } from "node:fs";

async function main() {
  // 1) Run scan → propose
  await sh("tsx ops/qsa/scan-repo.ts");
  await sh("tsx ops/qsa/propose-pus.ts");

  // 2) Nudge Culture-Ship (if your bridge API exists)
  const pus = (await fs.readFile("reports/qsa/pus.ndjson","utf8")).trim();
  try {
    const r = await request(process.env.CULTURE_SHIP_URL || "http://127.0.0.1:5000/api/culture/cascade", {
      method: "POST",
      headers: { "content-type":"application/json" },
      body: JSON.stringify({ source:"QSA", pus })
    });
    console.log("[qsa:cascade] status", r.statusCode);
  } catch {
    console.log("[qsa:cascade] culture-ship endpoint not found; skipping");
  }
}

async function sh(cmd: string) {
  const { exec } = await import("node:child_process");
  await new Promise<void>(res => exec(cmd, { stdio: "inherit" } as any, ()=>res()));
}

main().catch(e=>{ console.error(e); process.exit(1); });