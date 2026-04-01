#!/usr/bin/env tsx
import fs from "node:fs";
import path from "node:path";

const SNAP = "reports/repo_snapshot.json";
const NOW = Date.now();

function ls(dir: string, bag: string[] = []): string[] {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if ([".git","node_modules",".attic",".recycle","dist","build",".cache",".next","coverage","reports"].includes(e.name)) continue;
      ls(p, bag);
    } else bag.push(p);
  }
  return bag;
}

const files = ls(".");
const cur = { ts: NOW, count: files.length };
fs.mkdirSync("reports",{recursive:true});
let prev = { ts: NOW, count: files.length };
if (fs.existsSync(SNAP)) try { prev = JSON.parse(fs.readFileSync(SNAP,"utf8")); } catch {}
fs.writeFileSync(SNAP, JSON.stringify(cur, null, 2));

const dtMin = Math.max(1, Math.round((NOW - prev.ts) / 60000));
const growth = files.length - prev.count;
const perMin = growth / dtMin;
const alert = perMin > 500 ? "🚨 excessive growth" : (perMin > 50 ? "⚠️ high growth" : "ok");

fs.writeFileSync("reports/repo_growth.json", JSON.stringify({ prev, cur, growth, perMin:+perMin.toFixed(2), alert }, null, 2));
console.log(`[growth] files=${files.length} Δ=${growth} (~${perMin.toFixed(2)}/min) status=${alert}`);