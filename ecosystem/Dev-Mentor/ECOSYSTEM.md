# Ecosystem Map — NuSyQ-Hub + Dev-Mentor

> Quick-load context for agents and operators. When working in Dev-Mentor and
> you see references to other repos — this is intentional. See section 2 for
> the full topology. Last updated: 2026-03-31.

---

## 1. What Is This?

Three-plus years of iterative AI-assisted development has produced a **multi-repo
ecosystem** centered on `NuSyQ-Hub`. Dev-Mentor is the newest member — a
VS Code mentorship repo and cyberpunk hacking game (Terminal Depths) that plugs
into the orchestrator via `nusyq_bridge.py`.

This is **not** a monorepo. Each repo has its own git history, focus, and team
of AI agents. They communicate via filesystem state files, HTTP APIs (Ollama,
LM Studio), and GitHub.

---

## 2. Repo Map

### Primary Repos

| Repo | Location | Role |
|------|---------|------|
| **NuSyQ-Hub** | `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub` | Orchestrator brain. Smart search, task queue, consensus council, agent coordination, Nogic bridge, GitNexus matrix |
| **SimulatedVerse** | `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse` | UI / simulation layer. Culture Ship runtime owner, NEXUS, Phase 4 Drizzle stack, ChatDev integration |
| **NuSyQ** | `C:\Users\keath\NuSyQ` | Multi-agent generation core + Rosetta boot bundle |
| **Dev-Mentor** | `C:\Users\keath\Dev-Mentor` | ← **THIS REPO**. VS Code mentor + Terminal Depths hacking game |
| **CONCEPT / Keeper** | `C:\CONCEPT` | Machine-governance layer. Pressure score, advisor, optimize, maintenance, safe-start |

### Context Repos (in NuSyQ-Hub workspace)

| Repo | Role |
|------|------|
| `ChatDev` | Multi-agent Python framework embedded in NuSyQ-Hub. Modular models. |
| `_vibe` | Experimental / vibe-coding scratchpad |
| `nusyq_clean_clone` | Clean reference clone for diffs/bisect |
| `temp_sns_core` | Temporary SNS core extraction |
| `SkyClaw` | Additional tooling |

### Untracked Reference

| Location | Contents |
|---------|---------|
| `NuSyQ-Hub/.vscode/prime_anchor/` | Infrastructure config: devcontainer, Grafana dashboards, TimescaleDB schema, sync registry, MCP server YAML |
| `prime_anchor/docs/ROSETTA_STONE.md` | **Master agent reference** — ecosystem topology, commands, LM Studio/Ollama discovery, zero-token patterns |

---

## 3. Data Flows

```
Dev-Mentor (this repo)
  │
  ├─ nusyq_bridge.py ──────────────────────────────────────────────────────┐
  │   writes:                                                               │
  │   state/memory_chronicle.jsonl  ← MemoryPalace-compatible JSONL        │
  │   state/quest_log.jsonl         ← Rosetta Quest System format          │
  │   state/npc_memory/             ← per-NPC persistent memory files      │
  │   state/agent_manifest.json     ← discoverable by NuSyQ-Hub            │
  │                                                                         ▼
  │                                                              NuSyQ-Hub
  │                                                              (reads state/)
  ├─ scripts/content_scheduler.py (daemon, every 6h)
  │   auto-generates: challenges, lore, story beats, world nodes
  │   auto-pushes to GitHub every 6h
  │   syncs quests to NuSyQ every 24h
  │
  ├─ mcp/server.py (JSON-RPC 2.0, 12 tools)
  │   exposes: file system, memory, game commands, LLM generation,
  │            game_state, git_push, system_status, chronicle
  │
  └─ app/ (FastAPI, port 7337)
      Terminal Depths web console + API
      /api/nusyq/status, /manifest, /sync-quests, /chronicle, /schedule
```

```
NuSyQ-Hub
  ├─ src/orchestration/     ← task routing + consensus
  ├─ src/search/            ← smart_search (zero-token keyword lookup)
  ├─ scripts/start_nusyq.py ← state snapshot → state/reports/current_state.md
  └─ ChatDev/               ← multi-agent Python generation
       └─ modular models (independently loadable)

SimulatedVerse
  ├─ SimulatedVerse/NEXUS/  ← NEXUS orchestration layer
  ├─ SimulatedVerse/ChatDev/← ChatDev integration
  ├─ SimulatedVerse/GameDev/← Game development assets
  └─ Phase 4 Drizzle stack  ← Production DB/API layer
```

---

## 4. Agent Communication Matrix

| From | To | Method | Status |
|------|----|--------|--------|
| Dev-Mentor | Ollama | HTTP `localhost:11434` | ✅ Active |
| Dev-Mentor | LM Studio | HTTP `localhost:1234` | ✅ Active |
| Dev-Mentor | NuSyQ-Hub | Filesystem (`state/`) | ✅ Active |
| Dev-Mentor | GitHub | `gh_sync.py` + GITHUB_TOKEN | ✅ Active |
| Dev-Mentor | ChatDev | NuSyQ-Hub Python CLI | 🔍 Via NuSyQ-Hub |
| Dev-Mentor | GitNexus | `NuSyQ-Hub /api/gitnexus/*` | ✅ Active |
| Dev-Mentor | Nogic | NuSyQ-Hub bridge + VS Code bridge | ✅ Active |
| Dev-Mentor | Rosetta bundle | `NuSyQ/state/boot`, `NuSyQ/state/registry`, `NuSyQ/state/reports` | ✅ Canonical |
| Dev-Mentor | Copilot | VS Code extension only | 🔒 No API |
| Dev-Mentor | Codex | REST API (rate-limited ~48h) | ⏳ Recovering |
| Claude Code | Ollama | HTTP direct | ✅ Active |
| Claude Code | LM Studio | HTTP direct | ✅ Active |

### Ollama Models Available

| Model | Best For |
|-------|---------|
| `deepseek-coder-v2:16b` | Code analysis, refactoring |
| `qwen2.5-coder:14b` | Code generation |
| `starcoder2:15b` | Code completion |
| `codellama:7b` | Fast code tasks |
| `llama3.1:8b` | General reasoning |
| `phi3.5:latest` | Fast general tasks |
| `gemma2:9b` | Balanced general |
| `nomic-embed-text` | Embeddings / semantic search |

---

## 5. Cross-Repo Safety Rules

1. **Never `rm -rf` or force-push from Dev-Mentor** — `state/` files are read by NuSyQ-Hub.
2. **Run `sync_guard.py` before VS Code pushes** — prevents runtime files from polluting history.
3. **Auto-commits from `content_scheduler.py` are normal** — they appear in GitLens as `auto: N file(s) changed`. Not errors.
4. **`devlog.md` and `cost_log.csv` are gitignored** — if they appear in `git status`, the scheduler cached stale tracking. Fix: `git rm --cached <file>`.
5. **NuSyQ-Hub root safety**: `start_nusyq.py` and `smart_search` are read-only. Do not auto-run `dispatch_task` without a prompt.

---

## 6. Service Startup Order (local dev)

```
1. Ollama          — should already be running (service/daemon)
2. LM Studio       — start from system tray if needed
3. Dev-Mentor app  — python -m cli.devmentor serve --port 7337
4. NuSyQ-Hub       — python scripts/start_nusyq.py (snapshot only; no daemon needed)
5. Content Scheduler (optional) — python scripts/content_scheduler.py

## 6b. Control-Plane Read Order

Use this precedence before broad analysis:

1. `NuSyQ/state/boot/rosetta_bootstrap.json`
2. `NuSyQ/state/registry.json`
3. `NuSyQ/state/reports/control_plane_snapshot.json`
4. focused feed artifacts
5. docs fallback
```

---

## 7. Ports & Endpoints

| Service | Port | Notes |
|---------|------|-------|
| Dev-Mentor (local) | 7337 | Terminal Depths console |
| Dev-Mentor (Replit) | 5000 | Replit-hosted version |
| Ollama | 11434 | Local LLM API |
| LM Studio | 1234 | Local OpenAI-compatible API |
| NuSyQ-Hub (if served) | varies | Check `start_nusyq.py` |
| Grafana (prime_anchor) | 3000 | TimescaleDB dashboards (if running) |
| TimescaleDB (prime_anchor) | 5432 | PostgreSQL+TimescaleDB |
