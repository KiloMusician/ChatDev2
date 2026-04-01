#!/usr/bin/env tsx
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";

function sh(cmd: string) {
  console.log("[ollama:preload]", cmd);
  try {
    execSync(cmd, { stdio: "inherit" });
  } catch (e) {
    console.error(String(e));
  }
}

const list = readFileSync("ops/ollama/models.txt", "utf8")
  .split(/\r?\n/).map(s => s.trim()).filter(Boolean);

for (const model of list) {
  sh(`ollama pull ${model}`); // idempotent
}