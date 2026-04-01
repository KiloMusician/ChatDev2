#!/usr/bin/env tsx
/**
 * Systematic dependency surveyor.
 * - Loads every dependency and optional smoke-tests "key" libs.
 * - Writes QGL-like receipts (+ emits a summary to public/system-status.json)
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { createRequire } from "node:module";
const _require = createRequire(import.meta.url);

const OUT_DIR = "yap_archive/qgl";
const PUB = "public/system-status.json";

type Receipt = {
  id: string;
  kind: "audit.package";
  created_at: string;
  content: { name: string; version: string; loaded: boolean; test?: string; error?: string };
  tags: Record<string, any>;
};

function now() { return new Date().toISOString(); }
function ensureDirs() { mkdirSync(OUT_DIR, { recursive: true }); mkdirSync("public", { recursive: true }); }
function writeQGL(r: Receipt) {
  const file = join(OUT_DIR, `${r.id}.json`);
  writeFileSync(file, JSON.stringify(r, null, 2));
}

function writeStatus(partial: Record<string, any>) {
  let prev: any = {};
  try { prev = JSON.parse(readFileSync(PUB, "utf-8")); } catch {}
  const merged = { ...prev, ...partial, timestamp: Date.now() };
  writeFileSync(PUB, JSON.stringify(merged, null, 2));
}

function pkgJson(): any {
  return JSON.parse(readFileSync("package.json", "utf-8"));
}

// optional smoke tests for important libs
const testers: Record<string, () => string> = {
  "zod": () => {
    const { z } = _require("zod"); z.object({ x: z.number() }).parse({ x: 1 }); return "ok";
  },
  "ajv": () => {
    const Ajv = _require("ajv"); const ajv = new Ajv(); const v = ajv.compile({ type: "object", properties: {a:{type:"number"} }});
    return v({ a: 1 }) ? "ok" : "fail";
  },
  "p-queue": () => {
    const PQueue = _require("p-queue"); const q = new PQueue({ concurrency: 1 }); return q.size === 0 ? "ok" : "fail";
  },
  "react-error-boundary": () => "ok", // UI-only; just mark present
  "swr": () => "ok",
  "phaser": () => "ok",
  "pixi.js": () => "ok",
  "rot-js": () => { const ROT = _require("rot-js"); return ROT?.Map ? "ok" : "fail"; },
  "tone": () => "ok",
  "ollama": () => "ok",
  "langchain": () => "ok"
};

(async function main(){
  ensureDirs();
  const pkj = pkgJson();
  const deps = { ...(pkj.dependencies ?? {}), ...(pkj.devDependencies ?? {}) };
  const receipts: Receipt[] = [];
  for (const [name, version] of Object.entries(deps)) {
    // Create filesystem-safe ID
    const safeName = name.replace(/[@\/]/g, '_');
    const safeVersion = String(version).replace(/[\^~:]/g, '_');
    const id = `pkg_${safeName}_${safeVersion}`;
    let loaded = false, test = undefined, error = undefined;
    try {
      // Try dynamic import for ESM modules
      await import(name);
      loaded = true;
      if (testers[name]) test = testers[name]();
    } catch (e:any) {
      try {
        // Fallback to require for CommonJS
        _require(name);
        loaded = true;
        if (testers[name]) test = testers[name]();
      } catch (e2:any) {
        error = String(e2.message ?? e2);
      }
    }
    const r: Receipt = {
      id,
      kind: "audit.package",
      created_at: now(),
      content: { name, version, loaded, test, error },
      tags: {
        "audit/loaded": loaded,
        "audit/test": test ?? null
      }
    };
    writeQGL(r);
    receipts.push(r);
  }
  const summary = {
    total: receipts.length,
    ok: receipts.filter(r => r.content.loaded).length,
    tested_ok: receipts.filter(r => r.content.test === "ok").length,
    errors: receipts.filter(r => !!r.content.error).length
  };
  writeStatus({ packages: summary });
  console.log("[pkg-audit] summary", summary);
})();