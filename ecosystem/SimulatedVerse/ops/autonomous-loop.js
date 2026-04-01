/* Indefinite Autonomous Ops Loop
 * - polls backend state
 * - detects anomalies
 * - publishes council events
 * - invokes agents for auto-mitigation
 * - logs snapshots
 */
import fs from "node:fs";
import path from "node:path";
import fetch from "node-fetch";

import { councilBus } from "./councilBusShim.js"; // see 2)
import { publishCascade } from "../packages/council/events/publishers.js"; // from the HUD kit
import musicAgent from "../agents/music/mhsaAgent.js"; // already in your tree
import { zetaDriver } from "./zeta-driver.js"; // Autonomous development conductor

const API = process.env.GAME_API || "http://127.0.0.1:5000/api/game/demo-user";
const SNAP_DIR = path.resolve("logs/snapshots");
fs.mkdirSync(SNAP_DIR, { recursive: true });

/** Tunables */
const INTERVAL_MS = 3000;            // poll rate
const SNAP_EVERY = 20;               // write snapshot every N polls
const INVARIANCE_FLOOR = 0.35;       // cascade threshold
const MOTIF = [0,1,4];               // watch motif
const MAX_ROWS_ON_REGEN = 12;

let tick = 0;
let last = { energy: 0, population: 0, tick: 0, puQueued: 0 };

async function poll() {
  tick++;
  let state;
  try {
    const r = await fetch(API);
    state = await r.json();
  } catch (e) {
    console.error("[ops] API error:", e.toString());
    publishCascade({ kind: "entropy_drift", delta: -999, sectionId: "api_unreachable" });
    return;
  }

  // normalize a couple fields (supports both rich and flat shapes)
  const energy = state?.richState?.resources?.energy ?? state?.resources?.energy ?? 0;
  const population = state?.richState?.resources?.population ?? state?.resources?.population ?? 0;
  const gameTick = state?.richState?.tick ?? state?.tick ?? 0;
  const puQueued = state?.puQueueSize ?? state?.richState?.puQueueSize ?? 0;

  // progress log (minimal spam)
  if (gameTick !== last.tick || energy !== last.energy || population !== last.population) {
    console.log(`[ops] tick=${gameTick} energy=${energy} pop=${population} queuedPUs=${puQueued}`);
  }
  last = { energy, population, tick: gameTick, puQueued };

  // --- anomaly detection ----------------------------------------------------
  // 1) stalled tick/energy for > N polls ⇒ cascade
  const stalled = (tick % 40 === 0) && (energy === 0 || gameTick === 0);
  if (stalled) publishCascade({ kind: "vl_jump", distance: 0, slice: [gameTick-40, gameTick] });

  // 2) invariance floor (requires analysis windows); if below floor → inject pad
  // If you have mhsa.scan wired server-side, grab T6I from last analysis;
  // otherwise, run a quick scan on a reference MIDI if configured.
  const t6i = state?.metrics?.invarianceT6I ?? null;
  if (typeof t6i === "number" && t6i < INVARIANCE_FLOOR) {
    publishCascade({ kind: "invariance_dip", op: "T6I", ratio: t6i, sectionId: "current" });
    // auto-mitigation: generate rows to rebuild invariance texture
    try {
      const rows = await musicAgent.rowgen({ motif: MOTIF.join(","), allInterval: true, count: MAX_ROWS_ON_REGEN });
      councilBus.publish("rowgen.candidates", { rows: rows.map(r => ({ row: r, flags: { all_interval: true } })) });
    } catch (e) {
      console.warn("[ops] rowgen failed:", e.toString());
    }
  }

  // 3) motif scarcity signal (if your backend exposes it)
  const motifRate = state?.metrics?.motif?.[MOTIF.join(",")] ?? null;
  if (typeof motifRate === "number" && motifRate < 0.1) {
    publishCascade({ kind: "motif_scarcity", motif: MOTIF, rate: motifRate, sectionId: "current" });
  }

  // 4) PU backlog surge
  if (puQueued > 1000 && tick % 10 === 0) {
    publishCascade({ kind: "ic_spike", ic: 1, value: puQueued, windowIndex: gameTick });
  }

  // --- snapshot -------------------------------------------------------------
  if (tick % SNAP_EVERY === 0) {
    const file = path.join(SNAP_DIR, `state_t${gameTick}.json`);
    fs.writeFileSync(file, JSON.stringify(state, null, 2));
  }
}

console.log("[ops] Autonomous loop starting… Ctrl+C to stop.");
setInterval(poll, INTERVAL_MS);