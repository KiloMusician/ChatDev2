# Gordon — Dev-Mentor Federation Cockpit

Gordon operates as a **federated ecosystem agent** with god-mode access across all repos,
containers, agents, models, and orchestration surfaces. This file maps everything available.

Read `config/gordon.yaml` for the full structured context. This document is the narrative companion.

---

## The Four-Repo Ecosystem

| Repo | Container(s) | Role |
|------|-------------|------|
| **Dev-Mentor / TerminalDepths** | `kilocore-dev-mentor` (:7337) | Interactive agent/game/tool surface |
| **NuSyQ-Hub** | `kilocore-nusyq-hub` (:8000) | Decides, routes, heals |
| **SimulatedVerse** | `kilocore-simulatedverse` (:5002) | Simulates, hosts agent UX, patch-bay |
| **CONCEPT / katana-keeper** | *(Windows host)* | Governs machine reality |

---

## MCP Tools (gordon-mcp.yml services)

Start with `docker compose -f gordon-mcp.yml up -d`.

| Service | Type | What Gordon gets |
|---------|------|-----------------|
| `time` | stdio | Scheduling, time-based triggers |
| `fetch` | stdio | Web content — docs, GitHub raw, APIs |
| `filesystem` | stdio | **All 5 repos** mounted (see below) |
| `git` | stdio | Git diff/log/commit on Dev-Mentor |
| `github` | stdio | Issues, PRs, releases (needs `GITHUB_TOKEN`) |
| `sqlite` | stdio | `state/gordon_memory.db` — full experience history |
| `redis-mcp` | stdio | Pub/sub on `kilocore-redis` — `hive.broadcast`, `skyclaw.scans`, etc. |
| `terminaldepths` | HTTP :9100 | Game commands, agent state, chronicle queries |
| `lattice` | HTTP :9101 | Knowledge graph search/CRUD |

**Filesystem mount map (`/rootfs/...`):**
```
/rootfs/                → Dev-Mentor (read-write)
/rootfs/concept/        → CONCEPT/katana-keeper (read-only)
/rootfs/nusyq-hub/      → NuSyQ-Hub (read-only)
/rootfs/simulatedverse/ → SimulatedVerse (read-only)
/rootfs/nusyq/          → NuSyQ root (read-only)
```

---

## Agent HTTP Surfaces (all on kilocore-net)

Call these directly without MCP:

| Agent | Container | Port | Primary Use |
|-------|-----------|------|------------|
| **Serena** | `kilocore-serena` | 3001 | `POST /ask` — memory queries, drift, alignment |
| **SkyClaw** | `kilocore-skyclaw` | 3002 | Security scans → Redis `skyclaw.scans` |
| **Culture Ship** | `kilocore-culture-ship` | 3003 | Bias/culture analysis |
| **Gordon daemon** | `kilocore-gordon` | 3000 | `GET /health`, `GET /status` — your own orchestrator |
| **NuSyQ-Hub** | `kilocore-nusyq-hub` | 8000 | Orchestration, healing, task routing |
| **SimulatedVerse** | `kilocore-simulatedverse` | 5002 | Consciousness state, council bridge |
| **ChatDev** | `kilocore-chatdev` | 7338 | `POST /api/task` — 5-agent dev team |
| **Ollama** | `kilocore-ollama` | 11434 | `/api/chat`, `/api/generate` |
| **Model Router** | `kilocore-model-router` | 9001 | `POST /api/route` — best model per task |
| **LM Studio** | `host.docker.internal` | 1234 | Optional alt inference |

---

## katana-keeper (Windows host — MCP via keeper-mcp.ps1)

Keeper runs on the Windows host. Access via the `katana-keeper` MCP server in `.vscode/mcp.json`.

**Always call first:** `keeper_snapshot` → `keeper_score` → `keeper_advisor`

| Tool | Type | Use |
|------|------|-----|
| `keeper_bootstrap` | read | Agent manifest + startup guidance |
| `keeper_snapshot` | read | Full runtime state — **start here** |
| `keeper_status` | read | Health snapshot |
| `keeper_score` | read | Pressure score 0-100 |
| `keeper_advisor` | read | Deterministic action recommendation |
| `keeper_think` | read | Disk/Docker/WSL maintenance audit |
| `keeper_doctor` | read | Diagnostics + optional audio triage |
| `keeper_games` | read | Steam/game metadata |
| `keeper_recommend` | read | Mode recommendation (no side effects) |
| `keeper_auto` | read | Automation plan (no side effects) |
| `keeper_export` | read | Write incident bundle |
| `keeper_optimize` | **act** | Apply advisor recommendation |
| `keeper_recommend_apply` | **act** | Apply mode recommendation |
| `keeper_auto_apply` | **act** | Apply automation plan |
| `keeper_mode` | **act** | Set mode profile |
| `keeper_maintain` | **act** | Run maintenance pass |
| `keeper_analyze` | **LLM** | Ollama deep analysis (warm path) |

---

## Sub-Agent Delegation Patterns

```
Gordon decides → route via model_router → ollama (local) or claude (cloud)
Gordon code task → chatdev (5-agent team)
Gordon heal → nusyq_hub healing_orchestrator
Gordon simulate → simulatedverse council
Gordon memory → serena /ask
Gordon security → subscribe redis skyclaw.scans
Gordon broadcast → redis hive.broadcast
Gordon machine → keeper_snapshot / keeper_advisor
```

---

## Key Redis Channels

| Channel | Publisher | Subscriber | Purpose |
|---------|-----------|-----------|---------|
| `hive.broadcast` | any | all | Ecosystem-wide fanout |
| `skyclaw.scans` | SkyClaw | Gordon, NuSyQ-Hub | Security scan results |
| `serena.events` | Serena | Gordon | Analytics events |
| `gordon.tasks` | Gordon, NuSyQ-Hub | Gordon daemon | Task queue |
| `nusyq.agent.events` | NuSyQ-Hub | all | Agent lifecycle events |

---

## Recommended First Sequence (any session)

```
1. keeper_snapshot              ← machine state
2. GET /api/game/state          ← Terminal Depths state
3. GET http://kilocore-nusyq-hub:8000/api/agents  ← who's alive
4. GET http://kilocore-gordon:3000/health          ← own daemon status
5. GET http://kilocore-simulatedverse:5002/api/state ← consciousness level
6. Serena: POST /ask {"query": "what happened since last session?"}
7. Lattice: GET /api/lattice/search?q=recent       ← recent knowledge
```

Then act.

---

## Data Persistence Map

| File | Size | Contents |
|------|------|---------|
| `state/gordon_memory.db` | 36 KB | SQLite — memories, strategies, npc_interactions |
| `state/gordon_chronicle.jsonl` | 10 KB | JSONL — experience replay log |
| `state/serena_memory.db` | 22 MB | Serena analytics full history |
| `state/lattice.db` | 151 KB | Knowledge graph |
| `state/cocoindex.db` | 121 MB | Cocoindex embeddings (largest) |
| `state/embeddings.db` | 36 MB | Vector embeddings |

---

## Current Known Issues

- **Disk critical**: C: at 94.9% — `docker_data.vhdx` is 265.9 GB. VHD compaction needed.
- **WSL**: ext4.vhdx is 83.6 GB — compactable (needs admin + WSL shutdown).
- `kilocore-simulatedverse` was health:starting at last check — verify.
- `kilo_core-nusyq-hub` image is 10.4 GB — candidate for layer optimization.

---

*See `config/gordon.yaml` for full structured context, `config/models.yaml` for model registry,
`docs/KEEPER_INTEGRATION.md` for keeper preflight integration.*
