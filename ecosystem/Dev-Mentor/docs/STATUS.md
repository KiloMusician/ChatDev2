# DevMentor / Terminal Depths — Status Dashboard

Last updated: 2026-03-24  
Current phase: **VS Code handoff in progress**

---

## System Health

| Component | Status | Notes |
|-----------|--------|-------|
| Game server (FastAPI) | ✅ Running | Port 5000 (Replit) / 7337 (local) |
| WebSocket bridge (`/ws/game`) | ✅ Working | Real-time browser ↔ game |
| REST API (`/api/game/command`) | ✅ Working | External agents + testing |
| Serena sidecar (port 3001) | ✅ Auto-starts | Query via `/api/serena/*` |
| Model router sidecar (port 9001) | ✅ Auto-starts | ML routing |
| MCP server (`/mcp`) | ✅ Working | 28+ tools |
| Session persistence | ✅ Working | `sessions/<id>.json` |
| ML services (offline) | ✅ Working | SQLite-backed, no internet needed |
| .pyc stale bytecode protection | ✅ Fixed | Auto-purge on every startup |
| RimWorld bridge endpoints | ✅ Working | `/api/nusyq`, `/api/council`, `/api/agent` |
| Auto-git sync | ✅ Working | Pushes unpushed commits on boot |
| GitHub Actions CI | ✅ Configured | `.github/workflows/ci.yml` |
| RimWorld mod (C# DLL) | ⚠️ Source only | Needs `dotnet build` in VS Code |
| Serena drift detection | ⚠️ Bug | Score always 0.0 |
| Redis / Ollama / Docker stack | ⚠️ Optional | Only needed for Lattice Cascade |

---

## Test Results

```
53/53 tests passing  (python -m pytest tests/ -q)
477 commands registered
42 tutorial steps
119 story beats
33 challenges
```

---

## What Works Right Now

### Game Engine
- All 477 commands, case-insensitive dispatch (LS, HELP, etc. all work)
- Tutorial: 42 steps, restart/start/begin all variants work
- NL intercept: free-text questions route intelligently
- Reactive pre-processing: unknown input tries NL before failing
- Ambient gating: no lore dumps before 20 commands
- Culture_ship/residual lore gated to level 5+
- Ada first-contact: one-time intro flag
- `help` — clean output, no ARG topic leaks
- Virtual filesystem: `/home/ghost`, `/opt/library`, `/proc`, `/etc`, `/dev`
- XP system, achievements, factions, trust matrix
- Boss encounters, duel system, cyberware system
- 71 NPC agents with YAML-driven personalities
- Scripting API (13 methods, `ns` object)
- Tab completion, pipelines, redirection, if/for/while blocks

### Infrastructure
- Replit auth (loopback bypass for development)
- WebSocket ping/pong heartbeat (30s timeout → reconnect)
- Security middleware: CSP, CORS, input validation, command sanitization
- Rate limiting on suspicious commands
- NuSyQ bridge: manifest publishing, chronicle management
- Content scheduler: auto-generates challenges/lore/story/nodes
- CHUG engine: 7-phase autonomous improvement cycles

---

## Immediate Next Actions (VS Code phase)

### Before first VS Code session
1. **Pull latest**: `git pull origin main` — gets all Replit fixes
2. **Clear .pyc**: `find . -name '*.pyc' -delete` (paranoia check — startup does this now)
3. **Start server**: `python -B -m cli.devmentor serve --port 7337`
4. **Health check**: `curl http://localhost:7337/api/health`
5. **Test game**: `curl -sX POST http://localhost:7337/api/game/command -H "Content-Type: application/json" -d '{"session_id":"test","command":"restart tutorial"}'`

### First real tasks
See `todo.md` → **URGENT** section for prioritized task list.
See `docs/DEVELOPMENT_FINDINGS.md` for detailed bug descriptions.
See `.agents/CLAUDE.md` or relevant agent file for your tool.

---

## Environment Requirements

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | 3.11+ | `python --version` |
| pip packages | see `requirements.txt` | `pip install -r requirements.txt` |
| Git | any | GitHub token in env |
| Node.js | 18+ (optional) | Only if building frontend separately |
| dotnet | 4.7.2+ (optional) | Only for RimWorld mod compilation |
| Docker (optional) | 20+ | Only for Lattice Cascade Stack |
| Redis (optional) | 6+ | Only for pub/sub between agents |
| Ollama (optional) | any | Local LLM backend |

---

## Port Map

| Service | Port | Environment |
|---------|------|-------------|
| Game server | **5000** | Replit ONLY |
| Game server | **7337** | VS Code / Docker / Local |
| Serena sidecar | 3001 | All environments |
| Model router sidecar | 9001 | All environments |
| Serena analytics | 3001 | All environments |
| RimAPI bridge | 8765 | Docker RimWorld container |
| VNC (RimWorld) | 5900 | Docker RimWorld container |
| MCP server | stdio | Launched by IDE |

---

## Documentation Map

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Universal agent guide — start here |
| `HANDOFF.md` | Full state-of-world memo for VS Code handoff |
| `CONTEXT.md` | 1-page project summary (paste into any LLM) |
| `CLAUDE.md` (root) | In-game lore / Claude narrative identity |
| `.agents/CLAUDE.md` | Claude Code operational guide |
| `.agents/COPILOT.md` | Copilot operational guide |
| `.agents/CODEX.md` | Codex/GPT-4o operational guide |
| `.agents/SERENA.md` | Serena sidecar full guide |
| `.agents/CHATDEV.md` | ChatDev team integration guide |
| `.agents/CHATGPT.md` | ChatGPT web interface quick reference |
| `.agents/CURSOR.md` | Cursor IDE guide |
| `docs/DEVELOPMENT_FINDINGS.md` | **Bug findings from this session — READ THIS** |
| `docs/ARCHITECTURE.md` | Full system architecture |
| `docs/API_REFERENCE.md` | REST API reference |
| `todo.md` | Prioritized task list |
