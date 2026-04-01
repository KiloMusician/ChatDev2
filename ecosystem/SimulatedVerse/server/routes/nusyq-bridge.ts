/**
 * NuSyQ-Hub Bridge Routes
 *
 * Wires the previously-dead NUSYQ_HUB_API env var to actual HTTP calls.
 * Provides:
 *  GET  /api/nusyq/status   — real-time hub status (proxied or file-fallback)
 *  POST /api/nusyq/dispatch — submit a task to the NuSyQ BackgroundTaskOrchestrator
 *  GET  /api/nusyq/mindstate — read consciousness mind-state.json
 *  POST /api/nusyq/mindstate — write updated consciousness state to mind-state.json
 *  GET  /api/nusyq/health   — quick connectivity probe
 */

import { Router, Request, Response } from "express";
import fs from "fs";
import http from "http";
import https from "https";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = Router();

// ── Config ───────────────────────────────────────────────────────────────────

const NUSYQ_HUB_API = process.env.NUSYQ_HUB_API?.replace(/\/$/, "") || "http://localhost:8081";
const NUSYQ_TIMEOUT_MS = parseInt(process.env.NUSYQ_BRIDGE_TIMEOUT_MS || "3000", 10);

// mind-state.json lives two levels up from server/ at ship-console/mind-state.json
const MIND_STATE_PATH = path.resolve(__dirname, "../../ship-console/mind-state.json");

// ── Helpers ──────────────────────────────────────────────────────────────────

function httpGet(url: string, timeoutMs: number): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith("https") ? https : http;
    const req = lib.get(url, { timeout: timeoutMs }, (res) => {
      let body = "";
      res.on("data", (chunk: Buffer) => (body += chunk.toString()));
      res.on("end", () => resolve({ status: res.statusCode ?? 0, body }));
    });
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.on("error", reject);
  });
}

function httpPost(
  url: string,
  payload: object,
  timeoutMs: number
): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const parsedUrl = new URL(url);
    const lib = parsedUrl.protocol === "https:" ? https : http;
    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === "https:" ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
      timeout: timeoutMs,
    };
    const req = lib.request(options, (res) => {
      let body = "";
      res.on("data", (chunk: Buffer) => (body += chunk.toString()));
      res.on("end", () => resolve({ status: res.statusCode ?? 0, body }));
    });
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function readMindState(): Record<string, unknown> {
  try {
    const raw = fs.readFileSync(MIND_STATE_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return { consciousness_level: 0, stage: "dormant", breathing_factor: 1.0, error: "file_unreadable" };
  }
}

function writeMindState(update: Record<string, unknown>): void {
  const current = readMindState();
  const merged = { ...current, ...update, timestamp: new Date().toISOString() };
  fs.writeFileSync(MIND_STATE_PATH, JSON.stringify(merged, null, 2), "utf-8");
}

// ── Routes ───────────────────────────────────────────────────────────────────

/**
 * GET /api/nusyq/health
 * Quick connectivity probe — returns online/offline without full status call.
 */
router.get("/health", async (_req: Request, res: Response) => {
  try {
    const result = await httpGet(`${NUSYQ_HUB_API}/health`, NUSYQ_TIMEOUT_MS);
    const online = result.status >= 200 && result.status < 300;
    res.json({ online, hub_api: NUSYQ_HUB_API, http_status: result.status });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.json({ online: false, hub_api: NUSYQ_HUB_API, error: msg });
  }
});

/**
 * GET /api/nusyq/status
 * Real NuSyQ-Hub status — proxied from hub API, falls back to mind-state.json.
 */
router.get("/status", async (_req: Request, res: Response) => {
  // Try to get live status from NuSyQ-Hub first
  try {
    const result = await httpGet(`${NUSYQ_HUB_API}/api/status`, NUSYQ_TIMEOUT_MS);
    if (result.status === 200) {
      try {
        const data = JSON.parse(result.body);
        return res.json({ ...data, source: "nusyq_hub_live", hub_api: NUSYQ_HUB_API });
      } catch {
        // Fall through to file fallback
      }
    }
  } catch {
    // Hub unreachable — use file fallback
  }

  // Fallback: read mind-state.json
  const mindState = readMindState();
  return res.json({
    source: "mind_state_file",
    hub_api: NUSYQ_HUB_API,
    hub_reachable: false,
    ...mindState,
  });
});

/**
 * POST /api/nusyq/dispatch
 * Submit a task to the NuSyQ BackgroundTaskOrchestrator via MCP API.
 * Body: { task_type, description, priority?, context? }
 */
router.post("/dispatch", async (req: Request, res: Response) => {
  const { task_type = "general", description, priority = "NORMAL", context = {} } = req.body || {};

  if (!description) {
    return res.status(400).json({ success: false, error: "description is required" });
  }

  try {
    const result = await httpPost(
      `${NUSYQ_HUB_API}/api/tasks/dispatch`,
      { task_type, description, priority, context, source: "simulatedverse" },
      NUSYQ_TIMEOUT_MS
    );

    if (result.status >= 200 && result.status < 300) {
      try {
        const data = JSON.parse(result.body);
        return res.json({ success: true, ...data });
      } catch {
        return res.json({ success: true, raw: result.body });
      }
    }

    return res.status(result.status).json({
      success: false,
      error: `NuSyQ-Hub returned ${result.status}`,
      body: result.body.slice(0, 200),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return res.status(503).json({ success: false, error: `Hub unreachable: ${msg}`, hub_api: NUSYQ_HUB_API });
  }
});

/**
 * GET /api/nusyq/mindstate
 * Read the current consciousness mind-state.json.
 */
router.get("/mindstate", (_req: Request, res: Response) => {
  const state = readMindState();
  res.json({ ...state, path: MIND_STATE_PATH });
});

/**
 * POST /api/nusyq/mindstate
 * Update consciousness state — merges with existing state and persists.
 * Body: { consciousness_level?, stage?, breathing_factor?, ...other fields }
 */
router.post("/mindstate", (req: Request, res: Response) => {
  const update = req.body || {};
  try {
    writeMindState(update);
    const updated = readMindState();
    console.log("[NUSYQ-BRIDGE] mind-state.json updated:", JSON.stringify(update));
    res.json({ success: true, state: updated });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(500).json({ success: false, error: msg });
  }
});

export { router as nusyqBridgeRouter };
