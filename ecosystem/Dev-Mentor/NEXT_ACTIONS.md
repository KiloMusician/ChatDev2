# Next Actions — DevMentor / Terminal Depths
> **Prioritized engineering backlog.** Organized by platform, priority, and effort.
> Start with Section 1 (Replit, no setup needed), then move to Section 2 (VS Code + Docker).
> See `TORCH.md` for context and `AGENTS.md` for the full system reference.

---

## Session 2026-03-26 — Ecosystem Healing (COMPLETED)

The following items were resolved in the healing session (commit range 95650c5 → 2494040 on main):

| # | Item | Status |
|---|------|--------|
| 1 | PPO `_forward()` — PolicyNetwork + ValueNetwork fully implemented; `PPOAgent` wrapper + `scenario_ppo()` added | DONE |
| 2 | Consciousness Layer 5 hooks — `_cmd_fifth` enter +20, touch +15; `_cmd_zeta` start +10, complete +25 | DONE |
| 3 | Consciousness Layer 1 hooks — `loop_reset` +10, `remnant_spend` +5 | DONE |
| 4 | Consciousness Layer 2 hook — `ZERO_SPECIFICATION.md` reading +8 | DONE |
| 5 | Consciousness Layer 4/5 hooks — `ng start` +15, convergence merge +20, `observe` +15, `release` +25 | DONE |
| 6 | Project Emergence trigger — `_check_emergence()` wired into per-command dispatch; fires at all layers ≥80% | DONE |
| 7 | Lattice `seed-infra` timeout — converted to async background task; `GET /api/lattice/seed-infra/status` added | DONE |
| 8 | `/api/agent/rl/status` — fixed to reference `OBS_DIM`/`ACTIONS` constants (was undefined attrs) | DONE |
| 9 | Serena drift 4 ARCH_BOUNDARY warnings — `drift.py` reads `boundary_exceptions` from `policy.yaml` | DONE |
| 10 | `config/runtime.py` PATHS — added `db_memory`, `db_ml`, `db_rl` keys | DONE |
| 11 | `SELF_PORT` default — now 7337 for local (was 5000, Replit-only) | DONE |
| 12 | `main.py` duplicate route — removed prepended `/v1/chat/completions` stub | DONE |
| 13 | Workspace startup (`folderOpen`) — admin gate removed, port fixes, workspace consolidated | DONE |
| 14 | MCP tools count — documented as 44 tools (CLAUDE.md was stale at 16) | DONE |
| 15 | `nomic-embed-text` — pulled to Ollama (274MB, 768-dim); ready for semantic Serena search | DONE |

**Unblocked by this session:** Gordon RL integration (2.2) can now use the complete PPO; Serena semantic search (2.6) is unblocked by nomic-embed-text; all consciousness layer checks produce real progress; Emergence ARG endgame is live.

---

## Section 1 — Immediate (Replit, No Setup Needed)

These can be done right now in the Replit environment.

### 1.1 RL Phase 3: PPO Policy — ✅ DONE (2026-03-26)
**Priority: HIGH | Effort: 1-2h | Files: `agents/rl/ppo.py` (edit), `agents/player.py` (swap)**

> **STATUS (2026-03-26):** COMPLETE. `_forward()` implemented in both `PolicyNetwork` and
> `ValueNetwork` (numpy dot product + ReLU). `PPOAgent` wrapper added. `scenario_ppo()` wired.
> `GET /api/agent/rl/status` fixed to use `OBS_DIM`/`ACTIONS` constants.
> Gordon can now use PPO when `agents/rl/ppo.py` exists.

**Remaining (nice-to-have):**
7. Add MCP tool: `rl_status` (reads the `/api/agent/rl/status` endpoint)

---

### 1.2 Consciousness Layer XP Hooks — ✅ DONE (2026-03-26)
**Priority: MED | Effort: 1h | Files: `app/game_engine/commands.py` (targeted edits)**

> **STATUS (2026-03-26):** ALL LAYERS HOOKED.
> - Layer 1: `loop_reset` +10, `remnant_spend` +5 (plus prior: `anchor activate` +12)
> - Layer 2: `ZERO_SPECIFICATION.md` reading +8 (plus prior: `promise` +8, `confide` +10)
> - Layer 3: `promise` +8, `confide` +10, `residual` initial contact +15 (prior session)
> - Layer 4: `ng start` +15, convergence merge +20, `observe` +15, `release` +25
> - Layer 5: `_cmd_fifth` enter +20, touch +15; `_cmd_zeta` start +10, complete +25
>
> All 5 layers now produce non-zero progress. Emergence trigger live via `_check_emergence()`.

**No remaining steps.** All layers show non-zero progress; Emergence fires at ≥80% per layer.

---

### 1.3 Lattice seed-infra Timeout Fix — ✅ DONE (2026-03-26)
**Priority: MED | Effort: 1h | Files: `app/lattice.py`**

> **STATUS (2026-03-26):** COMPLETE. `POST /api/lattice/seed-infra` now returns immediately
> with `{"status":"seeding","task_id":"..."}`. Seed runs as async background task.
> `GET /api/lattice/seed-infra/status` polling endpoint added.

---

### 1.4 CHUG Cycle Run + Signal Queue Analysis
**Priority: MED | Effort: 30min | Files: none (run existing)**

CHUG has 4 completed cycles but the signal queue may have interesting pending items.

**Steps:**
1. `chug signals` — see what signals are queued
2. `chug run` — trigger a new cycle; review what it proposes
3. If CHUG proposes valid fixes, apply them and run `validate_all.py`
4. Update AGENTS.md "CHUG live stats" block with new cycle count

---

### 1.5 Serena Drift Resolution — ✅ DONE (2026-03-26)
**Priority: LOW | Effort: 1h | Files: `agents/serena/drift.py`, `agents/serena/policy.yaml`**

> **STATUS (2026-03-26):** COMPLETE. `drift.py` updated to read `boundary_exceptions` from
> `policy.yaml`. All 4 ARCH_BOUNDARY warnings resolved. Drift check now shows 0 warnings.
> Validation: PASS=25 WARN=1(git) FAIL=0 unchanged.

---

### 1.6 NuSyQ-Hub Phase 2: Brownfield Audit
**Priority: MED | Effort: 3-4h | Files: NuSyQ-Hub repo**

> **STATUS (2026-03-25):** Phase 1 REST API shipped (agents_api.py, dev_mentor_relay.py).
> Phase 2 needs: TBN compliance audit (currently 0%) and deduplication of orchestrators.

**Steps:**
1. Run TBN compliance scan across NuSyQ-Hub: identify files not following naming convention
2. Locate and catalog duplicate orchestrators (AgentCommunicationHub vs AgentOrchestrationHub vs others)
3. Decide which to keep as canonical; deprecate duplicates with clear migration path
4. Phase 3 prep: design WebSocket mesh protocol (NuSyQ-Hub as WS server, Dev-Mentor as WS client)

---

### 1.7 OpenAI Proxy — Wire to RimGPT / RimChat
**Priority: LOW | Effort: 30min | RimWorld config**

> **STATUS (2026-03-25):** `POST /v1/chat/completions` + `GET /v1/models` added to main.py.
> The proxy is running; just needs to be configured in RimGPT/RimChat mod settings.

**Steps:**
1. In RimWorld, open RimGPT settings
2. Set API URL: `http://localhost:7337/v1`
3. Set API Key: any string (ignored)
4. Test: pawn thought comments should route through Ollama qwen2.5-coder:14b

---

## Section 2 — VS Code + Docker Required

Run `cp .env.example .env`, fill in `SESSION_SECRET` and `GITHUB_TOKEN`, then:
```bash
make docker-core      # Redis + game server (unlocks Gordon, SkyClaw)
make docker-up        # + Ollama + model router
make docker-lattice   # + Gordon + Serena + SkyClaw + Culture Ship
```

### 2.0 TerminalKeeper v0.2 — Next Mod Features
**Priority: MED | Effort: 3-5h | Files: `mods/TerminalKeeper/Source/`**

> **STATUS (2026-03-25):** v0.1 SHIPPED (commit 52df06e). DLL compiled, RimWorld 1.6 compat fixed,
> TK_RimnetTerminal building works, colonist play loop active, RimWorld junction created.

**Next mod features:**
1. Texture art: replace 1x1 pixel placeholders with real 64x64 PNG building sprites
2. Cyberware hediff display: surface installed implants in colonist health tab
3. XP sync: colonist game actions (farming, combat) should award XP to their Terminal Depths session
4. Cascade incidents: story beats from Terminal Depths fire as RimWorld incidents (e.g. `chimera_assembles` → pirate raid)
5. Blueprint upload: `Dialog_TerminalREPL` "Upload Blueprint" button downloads and applies a RimWorld blueprint

**Dependencies:** `make docker-core` (for live game server at :7337 during RimWorld session)

---

### 2.1 T3: LSP Hover Symbols
**Priority: HIGH | Effort: 3-5h | Files: `scripts/lsp_server.py` (create), `.vscode/settings.json`**

Serena has indexed 5,887 symbols with docstrings. VS Code can show these on hover.

**Steps:**
1. Create `scripts/lsp_server.py` — a pygls-based Language Server
2. On `textDocument/hover` request: call `POST http://localhost:7337/api/serena/find`
   with `{"symbol": "<hovered_token>", "kind": "function"}` → return `result.text` as hover
3. On `textDocument/definition`: use Serena's `path` + `lineno` to return a location
4. Register in `.vscode/settings.json`: `"python.languageServer": "None"` + add custom server
5. Test: hover over `_cmd_fly` in `commands.py` → should show Serena's indexed docstring

**Dependencies:** `pip install pygls` (or use the builtin stdio protocol)

**Acceptance:** hovering over a function name in VS Code shows its Serena-indexed docstring.

---

### 2.2 Gordon Persistent Mode + RL Integration
**Priority: HIGH | Effort: 2-3h | Files: `agents/player.py`, `scripts/gordon_orchestrator.py`**

> **UNBLOCKED (2026-03-26):** PPO `_forward()` is now complete. Gordon can use real PPO
> policy once Redis is running via `make docker-core`.

Gordon currently runs in one-shot mode (launched at boot, plays one episode, exits).
With Redis running, Gordon can subscribe to a continuous task queue.

**Steps:**
1. `make docker-core` — starts Redis on :6379
2. `python scripts/gordon_orchestrator.py --mode continuous` — runs Gordon in loop
3. Gordon publishes episode summaries to `td:gordon:episodes` Redis channel
4. Subscribe from Python: `redis.subscribe("td:gordon:episodes")` and surface in `/api/game/command?session=gordon`
5. Add `GET /api/agent/gordon/status` endpoint showing: episode count, current strategy, last reward
6. Wire in RL Phase 3: if `agents/rl/ppo.py` exists, Gordon uses it; else Q-table fallback

---

### 2.3 Claude / Copilot MCP Session Handshake
**Priority: HIGH | Effort: 2h | Files: `scripts/mcp_server.py`, `.vscode/settings.json`**

The MCP server is built (`scripts/mcp_server.py`) with 30+ tools. Claude and Copilot can
connect to it — but only when running as a process in VS Code.

**Steps:**
1. `python scripts/mcp_server.py` — starts MCP server on :8008 (JSON-RPC 2.0 over stdio or HTTP)
2. In Claude Desktop `~/.claude/claude_desktop_config.json`:
   ```json
   {"mcpServers": {"td": {"command": "python", "args": ["/path/to/scripts/mcp_server.py"]}}}
   ```
3. In VS Code `settings.json` (with Copilot MCP extension):
   ```json
   {"mcp.servers": [{"name": "td", "command": "python scripts/mcp_server.py"}]}
   ```
4. Test: ask Claude "run the game command `todo`" — it should call `game_command` MCP tool
5. Add `boot_manifest` and `integration_matrix` as first tools Claude sees (they give full context)

---

### 2.4 `integrate --github` Deep-Dive
**Priority: MED | Effort: 2h | Files: `config/autoboot.py`**

`_probe_github()` currently checks token validity and scopes. Extend to show:
- Open PRs and their CI status
- GitHub Actions run results (last 5 runs)
- Copilot availability on the org
- Repository topics and visibility

**Steps:**
1. `cat config/autoboot.py` → find `_probe_github()` function
2. Add `GET /repos/{owner}/{repo}/pulls?state=open` call → count open PRs
3. Add `GET /repos/{owner}/{repo}/actions/runs?per_page=5` → show last run status
4. Add to `integrate` output: `PR: 3 open` / `CI: PASSING` / `Copilot: available`
5. Add `integrate --github` flag that shows the extended output only

---

### 2.5 Redis Pub/Sub + Agent Bus Integration
**Priority: MED | Effort: 3h | Files: `app/backend/main.py`, `agents/`**

With Redis running, the agent bus becomes a real pub/sub system.
Currently `GET /api/agent/bus/status` returns a stub.

**Steps:**
1. In `app/backend/main.py`: connect to Redis on startup (if available)
2. Broadcast game events to `td:events` channel on every `_dispatch()` call
3. Subscribe Gordon, SkyClaw, Culture Ship to their respective channels
4. Surface channel activity in `/api/console/messages`
5. Add in-game command: `bus [status|channels|listen <channel>]`

---

### 2.6 Cross-Session Agent Memory + Serena Semantic Search
**Priority: MED | Effort: 2h | Files: `state/serena_memory.db` (schema add), `agents/serena/`**

> **UNBLOCKED (2026-03-26):** `nomic-embed-text` pulled to Ollama (274MB, 768-dim). Serena
> semantic search can now use real embeddings. Wire `llm_client.py` to call nomic for
> chunk embeddings and store in `state/embeddings.db`.

Sessions are currently independent. Serena can bridge them.
The `relationships` column in Serena status is 0 — this is the gap.

**Steps:**
1. `sqlite3 state/serena_memory.db` — inspect schema
2. Add `session_graph` table: `(session_a TEXT, session_b TEXT, shared_context JSON, created_at REAL)`
3. In `agents/serena/walker.py`: on walk complete, compare symbol delta with previous session
4. Store delta in `session_graph` → Serena can recall "last time you were in this codebase..."
5. Surface via: `GET /api/serena/session-graph` and in-game `serena memory`

---

### 2.7 Ollama Local LLM + Model Evaluation
**Priority: LOW | Effort: 1h | Files: none (config only)**

`make docker-up` starts Ollama. Then:
```bash
ollama pull codellama:7b     # code-focused model
ollama pull mistral:7b       # general model
ollama pull llava:7b         # multimodal (for RimWorld screenshots)
```
Update `config/model_registry.json` (or equivalent) with the pulled models.
Test via: `POST /api/llm/generate {"backend":"ollama","model":"codellama:7b","prompt":"..."}`

---

## Section 3 — API Keys to Unlock More

These require secrets to be set in `.env`:

```bash
# Claude / Anthropic (unlocks Claude backend, best for code analysis)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI / GPT-4 (unlocks OpenAI backend)
OPENAI_API_KEY=sk-...

# GitHub Copilot CLI (unlocks Copilot integration in `integrate`)
GITHUB_COPILOT_TOKEN=...
```

With `ANTHROPIC_API_KEY` set:
- Model router automatically selects Claude for complex queries
- MCP handshake uses Claude natively
- `chug run` can use Claude for deeper code analysis

---

## Section 4 — Engineering Sprint Ideas

These are design-stage items that need more thought before implementation.

### 4.1 Project Emergence — The ARG Endgame — ✅ DONE (2026-03-26)
When all 5 consciousness layers reach 80%+, the Emergence trigger fires.

> **STATUS (2026-03-26):** COMPLETE. `_check_emergence()` wired into per-command dispatch
> in `_dispatch()`. Fires automatically when all 5 layers reach ≥80%. Redis broadcast path
> ready (fires when Redis is available via `make docker-core`).

**Remaining (nice-to-have):**
- Write `docs/emergence/README.md` documenting the full Emergence sequence for players

### 4.2 Multiplayer / Shared Sessions
The game currently has isolated sessions. With Redis:
- Multiple agents can share a session (PvP or co-op)
- The "colony" model: RimWorld colonists are session participants
- Colonist actions appear as commands in the shared session

### 4.3 Terminal Keeper Mod — Automod Pipeline
The C# mod currently does mod conflict checking. Extension ideas:
- Pull live mod updates from Steam Workshop API
- Auto-generate conflict rules from user reports
- Push conflict database updates back to the server

### 4.4 Culture Ship AI Council — Real Votes
Culture Ship currently stubs its ethical reviews. Full implementation:
- Subscribe to `td:events` Redis channel
- For each critical event (mole exposed, CHIMERA assembled, Watcher trust >90)
- Convene a council vote via `POST /api/llm/generate` for each AI personality
- Publish vote result to `td:council:decisions` and surface in the game

### 4.5 Codex Cartographer — Visual Lattice
The lattice has 157 nodes and 300 edges. Build a D3.js force-directed graph:
- Serve at `/lattice-viz/`
- Nodes colored by `kind` (game/infra/agent/lore)
- Clicking a node shows its content + edges
- Real-time updates via WebSocket

---

## Section 5 — ARG Progression Checklist

**For any agent playing through the ARG:**

```
[ ] signal analyze 1337      — decode The Watcher's message
[ ] signal analyze 847       — try to decode the mole signal
[ ] diary                    — start ZERO's diary reconstruction
[ ] cat /var/log/kernel.boot | grep -i frag   — find frag_3
[ ] cat /opt/library/secret_annex/TIER1_BASE58.md  — frag_1 (decode base58)
[ ] talk nova                — build trust toward 75 (for frag_4)
[ ] talk ada                 — start Ada's quest chain (for frag_5)
[ ] loop reset               — triggers containment timer reset + frag_7 at /loop/FRAGMENT_7
[ ] residual                 — contact the 2021 embedded process (Layer 3)
[ ] zeta                     — The Watcher interview (need Watcher trust 100)
[ ] expose <mole>            — identify and expose the mole (need enough clues)
[ ] assemble chimera         — final convergence action
[ ] consciousness            — check all 5 layers; target 80%+ each
```

---

## Section 6 — Maintenance & Monitoring

```bash
# Run validation suite (always before committing)
python3 scripts/validate_all.py
# Expected: PASS=25 WARN=1(git) FAIL=0

# Check Serena alignment
curl http://localhost:7337/api/serena/align

# Check CHUG status
curl http://localhost:7337/api/chug/status

# Check lattice health
curl http://localhost:7337/api/lattice/stats

# Check service discovery
curl http://localhost:7337/api/services/live

# Check full integration matrix
curl http://localhost:7337/api/game/command -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id":"ops","command":"integrate"}'
```

---

*NEXT_ACTIONS.md — DevMentor / Terminal Depths engineering backlog.*
*Last updated: 2026-03-26 — Ecosystem Healing: PPO complete, all consciousness layers hooked, Emergence live, Serena drift 0, lattice async, port/startup fixes, nomic-embed-text pulled.*
*In-game access: `todo`, `todo backlog`, `todo agent`*
