/**
 * server/routes/dev-mentor-bridge.ts
 *
 * SimulatedVerse ↔ Dev-Mentor (Terminal Depths) Bridge
 * =====================================================
 * Proxies requests to the Terminal Depths game server at port 7337.
 * Enables unified player state, cross-game quests, and shared lore.
 *
 * Endpoints:
 *   GET  /api/dev-mentor/health        — ping Terminal Depths
 *   GET  /api/dev-mentor/state         — get player state for session
 *   POST /api/dev-mentor/command       — send game command
 *   GET  /api/dev-mentor/agents        — get agent states
 *   GET  /api/dev-mentor/quests        — get active quests
 *   GET  /api/dev-mentor/leaderboard   — get XP leaderboard
 *   POST /api/dev-mentor/sync          — push SimVerse state to Dev-Mentor
 */

import { Router, Request, Response } from "express";

const router = Router();

const DM_URL = process.env.TERMINAL_DEPTHS_URL || "http://localhost:7337";
const DEFAULT_SESSION = process.env.DM_SESSION_ID || "simverse-bridge";

// ── Utility ──────────────────────────────────────────────────────────────────

async function dmFetch(
  path: string,
  options: RequestInit = {}
): Promise<{ ok: boolean; data: any; status: number }> {
  try {
    const resp = await fetch(`${DM_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      signal: AbortSignal.timeout(8000),
    });
    const data = await resp.json().catch(() => ({}));
    return { ok: resp.ok, data, status: resp.status };
  } catch (err: any) {
    return { ok: false, data: { error: err.message }, status: 503 };
  }
}

async function dmCommand(
  sessionId: string,
  command: string
): Promise<{ ok: boolean; output: any[]; state: any }> {
  const result = await dmFetch("/api/game/command", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, command }),
  });
  if (!result.ok) {
    return { ok: false, output: [], state: {} };
  }
  return {
    ok: true,
    output: result.data.output || [],
    state: result.data.state || {},
  };
}

// ── Routes ────────────────────────────────────────────────────────────────────

/**
 * GET /api/dev-mentor/health
 * Ping Terminal Depths. Returns status + server info.
 */
router.get("/health", async (_req: Request, res: Response) => {
  try {
    const result = await dmFetch("/api/health");
    if (result.ok) {
      res.json({
        status: "connected",
        terminal_depths_url: DM_URL,
        server_info: result.data,
        bridge_version: "1.0.0",
      });
    } else {
      res.status(503).json({
        status: "unreachable",
        terminal_depths_url: DM_URL,
        error: result.data?.error || "Server not responding",
      });
    }
  } catch (err: any) {
    res.status(503).json({ status: "error", error: err.message });
  }
});

/**
 * GET /api/dev-mentor/state?session_id=xxx
 * Fetch game state for a session.
 */
router.get("/state", async (req: Request, res: Response) => {
  const sessionId = (req.query.session_id as string) || DEFAULT_SESSION;
  const { ok, state } = await dmCommand(sessionId, "status");
  if (!ok || !state) {
    return res.status(503).json({ error: "Terminal Depths unreachable" });
  }
  res.json({ session_id: sessionId, state });
});

/**
 * POST /api/dev-mentor/command
 * Send a game command on behalf of a session.
 * Body: { session_id?, command }
 */
router.post("/command", async (req: Request, res: Response) => {
  const { command, session_id } = req.body;
  if (!command || typeof command !== "string") {
    return res.status(400).json({ error: "command is required" });
  }
  const sessionId = session_id || DEFAULT_SESSION;
  const result = await dmFetch("/api/game/command", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, command }),
  });
  if (!result.ok) {
    return res.status(503).json({ error: "Terminal Depths unreachable" });
  }
  res.json(result.data);
});

/**
 * GET /api/dev-mentor/agents
 * Get all agent states from Terminal Depths.
 */
router.get("/agents", async (req: Request, res: Response) => {
  const sessionId = (req.query.session_id as string) || DEFAULT_SESSION;
  const result = await dmFetch(`/api/game/agents?session_id=${encodeURIComponent(sessionId)}`);
  if (!result.ok) {
    return res.status(503).json({ error: "Terminal Depths unreachable" });
  }
  res.json(result.data);
});

/**
 * GET /api/dev-mentor/quests
 * Get active quests from Terminal Depths.
 */
router.get("/quests", async (req: Request, res: Response) => {
  const sessionId = (req.query.session_id as string) || DEFAULT_SESSION;
  const { ok, output, state } = await dmCommand(sessionId, "quests");
  if (!ok) {
    return res.status(503).json({ error: "Terminal Depths unreachable" });
  }
  res.json({
    session_id: sessionId,
    level: state.level,
    quests_output: output,
  });
});

/**
 * GET /api/dev-mentor/leaderboard
 * Get XP leaderboard across sessions.
 * Dev-Mentor exposes agent leaderboard at /api/agent/leaderboard (not /api/game/leaderboard).
 */
router.get("/leaderboard", async (_req: Request, res: Response) => {
  const result = await dmFetch("/api/agent/leaderboard");
  if (!result.ok) {
    return res.status(503).json({ error: "Terminal Depths unreachable" });
  }
  res.json(result.data);
});

/**
 * POST /api/dev-mentor/sync
 * Push SimulatedVerse consciousness state to Terminal Depths.
 * Creates or updates a cross-game story beat.
 * Body: { session_id?, event_type, data }
 */
router.post("/sync", async (req: Request, res: Response) => {
  const { session_id, event_type, data } = req.body;
  if (!event_type) {
    return res.status(400).json({ error: "event_type is required" });
  }
  const sessionId = session_id || DEFAULT_SESSION;

  // Map SimVerse events to Dev-Mentor commands
  const eventCommands: Record<string, string> = {
    consciousness_level_up: "lore residual",
    agent_unlocked: "agents",
    quest_completed: "quests",
    culture_ship_spoke: "strategy",
  };

  const cmd = eventCommands[event_type];
  if (!cmd) {
    return res.json({ ok: true, message: "Event acknowledged (no DM mapping)" });
  }

  const { ok, output } = await dmCommand(sessionId, cmd);
  res.json({ ok, event_type, command_sent: cmd, output: output.slice(0, 5) });
});

/**
 * GET /api/dev-mentor/sessions
 * List active Terminal Depths sessions.
 * Dev-Mentor has no native /api/game/sessions list endpoint.
 * We return known well-known session IDs and validate health via /api/health.
 */
router.get("/sessions", async (_req: Request, res: Response) => {
  const healthResult = await dmFetch("/api/health");
  const knownSessions = ["claude-prime", "gordon-bot", "simverse-bridge"];
  res.json({
    sessions: knownSessions,
    active_game_sessions: healthResult.ok ? healthResult.data?.active_game_sessions ?? null : null,
    server_up: healthResult.ok,
    source: "known_sessions",
    note: "Dev-Mentor has no session-list endpoint. Use GET /api/dev-mentor/state?session_id=<id> to probe individual sessions.",
  });
});

export default router;
