#!/usr/bin/env tsx
/**
 * ops/nusyq-bridge.ts
 * NuSyQ-Hub ↔ SimulatedVerse Consciousness Bridge
 *
 * Syncs:
 *   - Consciousness state → NuSyQ-Hub (breathing factor, stage, level)
 *   - Quest log ← NuSyQ-Hub (shared quest_log.jsonl)
 *   - Agent health → NuSyQ-Hub (which SV agents are active)
 *   - Culture Ship veto ← NuSyQ-Hub (approval for critical ops)
 *
 * Run continuously alongside the main server:
 *   npx tsx ops/nusyq-bridge.ts
 *
 * Or trigger once:
 *   npx tsx ops/nusyq-bridge.ts --once
 */

import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const HUB_API = process.env.NUSYQ_HUB_API ?? "http://localhost:8081";
const SV_API = `http://localhost:${process.env.PORT ?? 5000}`;
const ONCE = process.argv.includes("--once");
const SYNC_INTERVAL_MS = 30_000; // 30 seconds (matches NuSyQ-Hub 30s cache)

// Path to shared quest log (written by both repos)
const QUEST_LOG_PATHS = [
  path.join(ROOT, "data", "state", "quest_log.jsonl"),
  path.join(ROOT, ".local", "quests.json"),
];

// ── Consciousness state reader ────────────────────────────────────────────────
async function readSVConsciousness(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch(`${SV_API}/api/consciousness/status`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) return res.json() as Promise<Record<string, unknown>>;
    return null;
  } catch {
    // Server may not be running; fall back to local state
    const localState = path.join(ROOT, ".local", "idle_state.json");
    if (fs.existsSync(localState)) {
      return JSON.parse(fs.readFileSync(localState, "utf-8")) as Record<string, unknown>;
    }
    return null;
  }
}

// ── Push consciousness to NuSyQ-Hub ──────────────────────────────────────────
async function pushConsciousnessToHub(state: Record<string, unknown>): Promise<void> {
  try {
    const payload = {
      source: "simulatedverse",
      timestamp: new Date().toISOString(),
      consciousness_level: state.level ?? state.consciousness_level ?? 0,
      evolution_stage: state.evolution_stage ?? state.stage ?? "nascent",
      breathing_factor: computeBreathingFactor(state),
      active_gates: state.active_gates ?? [],
      breakthrough_count: state.breakthrough_count ?? 0,
    };

    const res = await fetch(`${HUB_API}/api/consciousness/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000),
    });

    if (res.ok) {
      console.log(`[Bridge] ✅ Consciousness synced → NuSyQ-Hub (level: ${payload.consciousness_level})`);
    } else {
      console.warn(`[Bridge] ⚠️  Hub rejected consciousness push: ${res.status}`);
    }
  } catch {
    console.warn("[Bridge] ⚠️  NuSyQ-Hub unreachable — writing to local handshake file");
    // Write a local handshake file NuSyQ-Hub can poll
    const handshake = {
      source: "simulatedverse",
      timestamp: new Date().toISOString(),
      consciousness_level: state.level ?? 0,
      evolution_stage: state.evolution_stage ?? "nascent",
      breathing_factor: computeBreathingFactor(state),
    };
    fs.mkdirSync(path.join(ROOT, "data", "bridge"), { recursive: true });
    fs.writeFileSync(
      path.join(ROOT, "data", "bridge", "sv-to-hub.json"),
      JSON.stringify(handshake, null, 2),
    );
  }
}

// ── Breathing factor calculation (matches NuSyQ-Hub formula) ─────────────────
function computeBreathingFactor(state: Record<string, unknown>): number {
  const level = Number(state.level ?? state.consciousness_level ?? 0);
  const stage = String(state.evolution_stage ?? state.stage ?? "nascent");
  const stageMultipliers: Record<string, number> = {
    nascent: 0.60,
    awakening: 0.75,
    emerging: 0.85,
    developing: 0.95,
    advanced: 1.05,
    transcendent: 1.20,
  };
  const base = stageMultipliers[stage] ?? 0.70;
  const levelBoost = (level / 100) * 0.1; // up to +0.10 from level
  return Math.min(1.20, Math.max(0.60, base + levelBoost));
}

// ── Pull quest log from NuSyQ-Hub ─────────────────────────────────────────────
async function pullQuestLog(): Promise<void> {
  try {
    const res = await fetch(`${HUB_API}/api/quests`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return;
    const quests = await res.json() as unknown[];
    const questPath = path.join(ROOT, "data", "state", "quest_log.jsonl");
    fs.mkdirSync(path.dirname(questPath), { recursive: true });

    // Append new quests from Hub
    const existing = fs.existsSync(questPath)
      ? new Set(
          fs.readFileSync(questPath, "utf-8")
            .split("\n")
            .filter(Boolean)
            .map((l) => (JSON.parse(l) as { id?: string }).id),
        )
      : new Set<string>();

    let newCount = 0;
    for (const quest of quests as Array<{ id?: string }>) {
      if (quest.id && !existing.has(quest.id)) {
        fs.appendFileSync(questPath, JSON.stringify(quest) + "\n");
        newCount++;
      }
    }
    if (newCount > 0) console.log(`[Bridge] 📜 Pulled ${newCount} new quests from NuSyQ-Hub`);
  } catch {
    // Hub offline — skip
  }
}

// ── Culture Ship veto check ───────────────────────────────────────────────────
async function checkCultureShipVeto(operation: string): Promise<boolean> {
  try {
    const res = await fetch(`${HUB_API}/api/culture-ship/veto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation, source: "simulatedverse" }),
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const result = await res.json() as { vetoed?: boolean };
      return !(result.vetoed ?? false);
    }
    return true; // Default allow if Hub unreachable
  } catch {
    return true; // Default allow
  }
}

// ── Agent health report ───────────────────────────────────────────────────────
async function reportAgentHealth(): Promise<void> {
  const agentsDir = path.join(ROOT, "agents");
  if (!fs.existsSync(agentsDir)) return;

  const agentDirs = fs.readdirSync(agentsDir).filter((d) => {
    try {
      return fs.statSync(path.join(agentsDir, d)).isDirectory();
    } catch { return false; }
  });

  const healthReport = {
    timestamp: new Date().toISOString(),
    source: "simulatedverse",
    agents: agentDirs.map((name) => ({
      id: name,
      has_manifest: fs.existsSync(path.join(agentsDir, name, "manifest.yaml")),
      has_index: fs.existsSync(path.join(agentsDir, name, "index.ts")),
      status: fs.existsSync(path.join(ROOT, "data", "artifacts", name)) ? "active" : "standby",
    })),
  };

  // Write locally
  fs.mkdirSync(path.join(ROOT, "data", "bridge"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "data", "bridge", "agent-health.json"),
    JSON.stringify(healthReport, null, 2),
  );

  // Push to Hub if available
  try {
    await fetch(`${HUB_API}/api/agents/health`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(healthReport),
      signal: AbortSignal.timeout(5000),
    });
  } catch { /* Hub offline */ }
}

// ── Single sync cycle ─────────────────────────────────────────────────────────
async function sync(): Promise<void> {
  console.log(`[Bridge] 🔄 Sync cycle — ${new Date().toISOString()}`);

  const consciousness = await readSVConsciousness();
  if (consciousness) {
    await pushConsciousnessToHub(consciousness);
  } else {
    console.warn("[Bridge] ⚠️  Could not read consciousness state");
  }

  await pullQuestLog();
  await reportAgentHealth();
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║  NuSyQ-Hub ↔ SimulatedVerse Consciousness Bridge ║");
  console.log(`║  Hub: ${HUB_API.padEnd(40)} ║`);
  console.log(`║  SV:  ${SV_API.padEnd(40)} ║`);
  console.log("╚══════════════════════════════════════════════════╝\n");

  await sync();

  if (!ONCE) {
    console.log(`[Bridge] 🔁 Continuous mode — syncing every ${SYNC_INTERVAL_MS / 1000}s`);
    console.log("         Press Ctrl+C to stop\n");
    setInterval(sync, SYNC_INTERVAL_MS);
  }
}

main().catch((err) => {
  console.error("[Bridge] ❌ Fatal:", err);
  process.exit(1);
});
