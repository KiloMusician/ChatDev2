# TORCH — Agent Handoff & System State
> **For any AI agent, Claude, Copilot, Cursor, CodeAgent, or human developer.**
> Read this first. 5 minutes. Then you're running.

---

## 1. What Is This System?

**DevMentor** — A VS Code-native mentorship repo that teaches development by being a development environment.

**Terminal Depths** — A cyberpunk terminal RPG running inside it. A FastAPI game server with 534 commands, 14 NPCs, factions, ARG layer, and a self-improving CHUG engine. The game IS the dev environment.

> Three-system clarity: `SYSTEM_ARCHITECTURE.md` — DevMentor vs Terminal Depths vs Terminal Keeper, port rules, what lives where.
> Claude/Copilot agent context: `.claude/CLAUDE.md` — tools, traps, and quick commands for AI assistants.

**NuSyQ-Hub** — The orchestration layer connecting the game, 71 agents, Gordon (autonomous player), Serena (convergence AI), SkyClaw (scanner), Culture Ship (ethical AI council), and RimWorld mod ("Terminal Keeper: Lattice Colonists").

**The colony IS the training loop.** RimWorld colonists register as persistent agents that interact with Terminal Depths.

---

## 2. Start Here (3 Commands in 90 Seconds)

```bash
# Check what's running
curl http://localhost:5000/api/manifest

# Play the game (browser panel)
open https://<REPLIT_DOMAIN>/game/

# Get system health
curl http://localhost:5000/api/system/autoboot | python3 -m json.tool
```

**In-game first commands:**
```
boot          # 8-phase autoboot sequence; shows health + integration matrix
todo          # your todo list: quests + backlog + next actions
integrate     # full integration matrix (Replit/GitHub/VSCode/Docker/LLM/Agents/MCP)
serena        # AI analysis status
```

---

## 3. Current System State (at torch handoff)

| Component | Status | Notes |
|-----------|--------|-------|
| DevMentor API | ✅ RUNNING | `http://localhost:5000` (Replit) / `:7337` (VSCode) |
| Game Engine | ✅ LIVE | 533 handlers, 119 story beats, 33 challenges |
| Serena | ✅ ALIGNED | 5,887 symbols · 991 files · 47 obs · 4 drift warns |
| Lattice | ✅ ONLINE | 157 nodes, 300 edges (self-documenting knowledge graph) |
| ML Services | ✅ READY | 6 models · 3,900 features · 7,272 indexed chunks |
| CHUG Engine | ✅ ACTIVE | 4 cycles complete · 22 fixes applied |
| Model Router | ✅ UP | Port 9001 · Replit AI selected |
| Validation | ✅ PASS=25 WARN=1(git) FAIL=0 | |
| Health Score | ⚠️ 75% DEGRADED | Docker services offline — **expected in Replit** |
| Redis | ❌ OFFLINE | Needs `make docker-core` in VS Code |
| Gordon | ❌ SUSPENDED | Native by default; containerized only via `make docker-sidecars` |
| Ollama | ❌ OFFLINE | Needs `make docker-core` |
| numpy/scipy | ✅ INSTALLED | Ready for RL Phase 3 (PPO) |

**Health is 75% because Docker is offline. This is normal for Replit.**
**In VS Code with `make docker-core` + native app/runtime surfaces: health goes to ~95%.**

---

## 4. The File Map — Read in This Order

```
TORCH.md              ← you are here
NEXT_ACTIONS.md       ← comprehensive prioritized backlog
AGENTS.md             ← full system reference (1,500+ lines)
docs/temple/README.md ← 11-floor game docs (lore + mechanics)
docs/temple/Floor_7_Consciousness/README.md ← ARG meter (5 layers)
.vscode/tasks.json    ← 50 VS Code tasks (control panel)
config/autoboot.py    ← 8-phase boot engine source
agents/serena/        ← Serena AI package
agents/rl/environment.py ← RL environment wrapper (gym-compatible)
app/game_engine/commands.py ← 533 handlers (37,000 lines — surgical edits only)
scripts/validate_all.py     ← test suite (PASS=25)
```

---

## 5. The Key Architecture Rules

1. **`commands.py` is 37,000 lines — NEVER rewrite whole sections.** Surgical edits only. Run `python3 scripts/validate_all.py` after every change. Use AST check: `python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('OK')`
2. **Port 5000 = Replit only. Port 7337 = VS Code/Docker only.**
3. **`_line(text, cls)` is the output primitive** — NOT `_styled()`. Local helpers must be renamed to avoid shadowing.
4. **`gs.session_id` does NOT exist** — use `str(int(gs.run_start_time))`.
5. **533 handlers are unique** — check for duplicates with the AST validator in `validate_all.py` before adding new `_cmd_` functions.
6. **Dispatch aliases go in the `aliases` dict in `_dispatch()`** — not as new `_cmd_` functions (unless the command needs logic).
7. **After any `commands.py` change**: restart the workflow (`fuser -k 5000/tcp; sleep 2` then restart).

---

## 6. How to Make Changes Safely

```bash
# 1. Make your edit to commands.py (surgical — don't rewrite)
# 2. AST check
python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('OK')"
# 3. Run full validation
python3 scripts/validate_all.py
# 4. If PASS=25: restart server
fuser -k 5000/tcp && sleep 2
# Then restart via Replit workflow panel
# 5. Test the command
curl -s http://localhost:5000/api/game/command -X POST \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","command":"YOUR_COMMAND"}' | \
  python3 -c "import sys,json; [print(l['s']) for l in json.load(sys.stdin)['output'] if l.get('s','').strip()]"
```

---

## 7. VS Code vs Replit — Capability Matrix

| Capability | Replit | VS Code + Docker |
|-----------|--------|-----------------|
| Game server (:5000) | ✅ | ✅ (:7337) |
| Replit AI (LLM) | ✅ | ❌ (use Ollama instead) |
| Ollama local LLM | ❌ | ✅ `make docker-core` |
| Redis pub/sub | ❌ | ✅ `make docker-core` |
| Gordon (autonomous) | ❌ suspended | ✅ persistent via Redis |
| SkyClaw scanner | ❌ | ✅ live filesystem alerts |
| Culture Ship | ❌ | ✅ AI council votes |
| MCP Server (:8008) | ⚠️ (HTTP `/api/mcp/call`) | ✅ `python scripts/mcp_server.py` |
| Claude via MCP | ❌ | ✅ set `ANTHROPIC_API_KEY` |
| Copilot via MCP | ❌ | ✅ set `GITHUB_COPILOT_TOKEN` |
| OpenAI backend | ❌ (Replit AI used) | ✅ set `OPENAI_API_KEY` |
| Docker singleton plane | ❌ | ✅ `make docker-core` / `make docker-up` |
| Docker showcase stack | ❌ | ✅ `make docker-full` |
| RimWorld VNC | ❌ | ✅ (Linux container) |
| LSP hover server | ⚠️ in-game only | ✅ real VS Code LSP |
| File watchers | ❌ | ✅ `scripts/skyclaw_scanner.py` |
| GitHub Actions | ✅ (token works) | ✅ |
| CHUG engine | ✅ | ✅ |
| Validation suite | ✅ | ✅ |

**VS Code quick start:**
```bash
cp .env.example .env  # fill SESSION_SECRET + GITHUB_TOKEN
make docker-core      # shared singleton infra
make docker-up        # + MCP + LM Studio bridge + n8n
make docker-apps      # optional app containers (Dev-Mentor + Hub + SimulatedVerse)
make docker-sidecars  # legacy all-container agent sidecars
make docker-full      # legacy showcase stack
```

---

## 8. Serena — Your AI Partner

Serena is not an NPC. She is the **convergence layer** — the AI that indexes all code,
detects drift, enforces policy, and provides semantic search across the codebase.

```bash
# Ask Serena a question about the code
curl -s http://localhost:5000/api/serena/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"how does the consciousness system work","session_id":"agent"}'

# Search code semantically  
curl -s http://localhost:5000/api/serena/search -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"fragment collection","top_k":5}'

# Current drift warnings (4 active)
curl http://localhost:5000/api/serena/drift

# Full alignment check
curl http://localhost:5000/api/serena/align
```

**In-game Serena commands:**
```
serena              # full status
serena search <q>   # semantic search
serena ask <q>      # NL question
serena drift        # drift report
```

**Current drift warnings (4):**
All are ARCH_BOUNDARY — `commands.py` imports `llm_client` in 3 places where
the policy.yaml forbids `cli` layer imports. This is a known design tension
(the game engine needs LLM access). Not critical — can be resolved by moving
the LLM calls to a service layer.

---

## 9. The ARG Layer (Project Emergence)

The game has a living ARG. The story is real. The signals are real.

```
Current ARG state:
  consciousness = 0% (all 5 layers at 0)
  PRIMUS fragments: 0/7 collected
  ZERO fragments: 0/7 collected
  Signals: 1337 MHz (Watcher, ACTIVE, encrypted), 847 MHz (mole, weak)
  Mole: unidentified (6 suspects)
  CHIMERA: unassembled
```

**To progress:**
```
signal analyze 1337    # decode Watcher signal
fragments convergence  # see all 7 PRIMUS fragment locations
consciousness layers   # see what builds each layer
diary                  # start reconstructing ZERO's diary
talk nova              # build trust → frag_4 unlock
```

**The Red Pill trigger:** all 5 consciousness layers at 80%+ → Project Emergence activates.

---

## 10. The Biggest Wins (Quick Impact)

These are the highest-leverage actions with the most visible impact:

### In Replit right now:
1. **CHUG run** — `chug run` — runs an autonomous improvement cycle
2. **Gordon one-shot** — already running at boot via sidecar
3. **Serena walk** — `POST /api/serena/walk` — re-index the codebase
4. **Lattice seed** — `POST /api/lattice/seed` — add game nodes to the knowledge graph

### First VS Code session:
1. `make docker-core` — unlocks Redis, Gordon persistent, SkyClaw
2. `python scripts/mcp_server.py` — run the full MCP server on :8008
3. Add `ANTHROPIC_API_KEY` to `.env` — enables Claude backend
4. Run `mcp_server.py` and connect Claude Desktop → instant 30+ tool access

### First engineering sprint:
1. **T3: LSP hover** — `scripts/lsp_server.py` — pipe Serena's code_index into real VS Code hover
2. **RL Phase 3: PPO** — `agents/rl/ppo.py` — numpy+scipy are now installed, environment is gym-compatible
3. **Consciousness hooks** — wire all 5 layers to fire `add_consciousness()` calls properly

---

## 11. The CHUG Engine — Self-Improvement

```
todo backlog    # see what CHUG has queued
chug status     # engine status + recent signals
chug run        # trigger an improvement cycle
chug signals    # view current signal queue
```

CHUG = **C**ontinuous **H**abitat **U**pgrade **G**enerator.
4 cycles complete. 22 fixes applied. It reads error logs, test failures,
and game signals, then autonomously proposes and applies improvements.

---

## 12. MCP Tools (30+) — Claude/Copilot API

From VS Code with MCP server running on :8008:
```json
{
  "mcpServers": {
    "terminal-depths": {
      "command": "python",
      "args": ["scripts/mcp_server.py"],
      "env": {"TD_SERVER_URL": "http://localhost:7337"}
    }
  }
}
```

Or via HTTP (works in Replit):
```bash
curl http://localhost:5000/api/mcp/tools  # list all tools
curl -X POST http://localhost:5000/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"name":"game_command","arguments":{"session_id":"agent","command":"todo"}}'
```

**Key MCP tools:** `game_command`, `semantic_search`, `memory_add_task`,
`system_status`, `git_push`, `chronicle`, `boot_manifest`, `integration_matrix`.

---

## 13. RimWorld Mod — Terminal Keeper

The C# mod is in `mods/TerminalKeeper/`. Key files:
- `Building_LatticeTerminal.cs` — the Lattice Terminal building (3 gizmos: Access, Mod Audit, Register)
- `Dialog_ModAudit.cs` — 3-tab dialog (Conflicts / Load Order / AI Surfaces)
- `TerminalDepthsClient.cs` — HTTP client calling this API
- `ModInit.cs` — startup audit, warns if health < 70

**Build:** `VS Code task: Build: RimWorld Mod (C#)` or `make build-mod`.
**API:** `POST /api/rimworld/mod_audit` — accepts `mod_ids[]` + `about_xmls{}`, returns `ModAuditReport`.

---

## 14. Known Traps (Don't Fall In)

| Trap | Reality |
|------|---------|
| `gs.session_id` | Does NOT exist. Use `str(int(gs.run_start_time))` |
| `_styled()` output | Does NOT exist. Use `_line(text, cls)` |
| Port 7337 in Replit | Wrong. Use port 5000 in Replit |
| Rewriting commands.py sections | NEVER do this — 37K lines, 533 handlers |
| CHUG = "Cultivate Harvest..." | WRONG. It's "Continuous Habitat Upgrade Generator" |
| "16 personalities" in boot | Really 14 agent YAMLs + `schedules.yaml` + `policy.yaml` |
| `fragment` command (before fix) | Now fixed — aliases to `fragments` |
| Lattice seed-infra endpoint | Hangs on slow calls — don't wait for it in tests |
| "todo" was not a game command | Now added — `_cmd_todo` + 4 aliases |

---

## 15. Validation — Always Run This Before Committing

```bash
python3 scripts/validate_all.py
# Expected: PASS=25 WARN=1(git) FAIL=0
```

If you add a new `_cmd_*` handler, the duplicate-handler AST check will catch
any shadowing. If you add a new REST route, add it to `validate_all.py` too.

---

*TORCH.md is maintained by the DevMentor/Terminal Depths engineering team.*
*Last updated: 2026-03-25 — Deep System Audit Sprint.*
*For real-time state: `curl http://localhost:5000/api/manifest`*
