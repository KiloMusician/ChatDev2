# Gordon Cockpit

## Purpose

Use Keeper as a low-token, high-authority Windows orchestration surface for the MSI Katana laptop. The PowerShell core is authoritative; the JSON bridge and MCP wrapper exist so you do not need to scrape console output or re-derive runtime state.

Gordon is not limited to Keeper. Gordon is expected to operate as a federated ecosystem agent with access to the other major repos and their exposed tools when available: Dev-Mentor / Terminal Depths, SimulatedVerse, NuSyQ-Hub, Serena surfaces, Culture Ship / council surfaces, SkyClaw and related claw-family tooling, Ollama, LM Studio, ChatDev, and any available delegation/sub-agent paths.

## Start Here

1. Read [`agent_manifest.json`](/mnt/c/CONCEPT/agent_manifest.json).
2. If your client supports workspace MCP, mount the `keeper` server from [`.vscode/mcp.json`](/mnt/c/CONCEPT/.vscode/mcp.json).
3. Call `keeper_snapshot` first.
4. After snapshot, load the Rosetta bundle first when available:
   - `/mnt/c/Users/keath/NuSyQ/state/boot/rosetta_bootstrap.json`
   - `/mnt/c/Users/keath/NuSyQ/state/registry.json`
   - `/mnt/c/Users/keath/NuSyQ/state/reports/control_plane_snapshot.json`
5. Then attach upstream surfaces required for the mission.
6. Then stay narrow:
   - `keeper_score` for pressure only
   - `keeper_advisor` for deterministic recommendation only
   - `keeper_games` for Steam/game context only
   - `keeper_think` for maintenance/disk context only
   - `keeper_doctor` for diagnostics only
6. Use `keeper_analyze` only when deterministic outputs are insufficient.

## Preferred Interfaces

1. `tools/keeper-mcp.ps1`
2. `tools/keeper-bridge.ps1`
3. `keeper.ps1`
4. Upstream MCP/API surfaces from Dev-Mentor, SimulatedVerse, and NuSyQ-Hub

The bridge and MCP tools are cheaper than broad CLI flows because they return structured JSON. Prefer them whenever you can.

## Available Runtime Surfaces

- [`tools/keeper-mcp.ps1`](/mnt/c/CONCEPT/tools/keeper-mcp.ps1): stdio MCP server for structured tool calls
- [`tools/keeper-bridge.ps1`](/mnt/c/CONCEPT/tools/keeper-bridge.ps1): JSON bridge over keeper runtime
- [`keeper.ps1`](/mnt/c/CONCEPT/keeper.ps1): authoritative CLI/router
- [`tools/Launch-KeeperShell.ps1`](/mnt/c/CONCEPT/tools/Launch-KeeperShell.ps1): desktop surface launcher

Expected upstream ecosystem surfaces:

- Dev-Mentor / Terminal Depths MCP server and REST APIs
- NuSyQ-Hub orchestration, healing, doctor, and quest entrypoints
- SimulatedVerse patch-bay, ChatDev server, council bridge, and simulation APIs
- Serena endpoints or toolkits exposed by upstream repos
- Culture Ship / guardian / council governance surfaces exposed upstream
- SkyClaw and other claw-family tools exposed upstream
- Ollama and LM Studio local model endpoints

## Core Commands

- `snapshot`: full structured state, recent sessions, listener state, brain state
- `status`: current health snapshot
- `games`: Steam/game metadata
- `doctor`: diagnostics and audio triage
- `recommend`: deterministic mode recommendation
- `auto`: safe coding/balanced automation
- `think`: maintenance audit
- `maintain`: maintenance pass
- `score`: weighted pressure score
- `advisor`: deterministic action recommendation
- `analyze`: Ollama-assisted deep analysis
- `optimize`: apply advisor recommendation
- `mode`: apply or restore a mode profile
- `export`: write JSON/HTML incident bundles

## Operating Model

- Snapshot first, then narrow.
- Prefer deterministic tools before LLM-assisted analysis.
- Use `recommend`, `advisor`, `score`, and `think` to decide; use `mode`, `optimize`, and `maintain` to act.
- Treat `analyze` as a warm-path escalation, not the default.
- Do not scrape human `Format-List` output when the bridge or MCP can return JSON.
- Treat Gordon as a cockpit-level orchestrator across repos, tools, models, agents, and delegations whenever those surfaces are available.
- Keeper is the machine-governance layer, not the full ecosystem boundary.

## Ecosystem Role

CONCEPT is the **machine-health oracle** for the four-part ecosystem. The division of responsibility:

| Repo | Role |
|------|------|
| **CONCEPT** (this repo) | Governs machine reality — pressure, disk, modes, diagnostics |
| **Dev-Mentor / TerminalDepths** | Interactive agent/game/tool surface — MCP, chronicle, NuSyQ bridge |
| **SimulatedVerse** | Simulation + agent UX — council bridge, ChatDev, patch-bay |
| **NuSyQ-Hub** | Diagnostics/healing/orchestration brain — decides, routes, heals |

Culture Ship authority is intentionally split:

- `SimulatedVerse` is the runtime owner
- `NuSyQ-Hub` is the control owner

**Already live cross-repo wiring:**
- Dev-Mentor consumes Keeper via [`C:/CONCEPT/tools/keeper-mcp.ps1`] (wired in `.vscode/mcp.json`)
- Dev-Mentor syncs into NuSyQ-Hub via `nusyq_bridge.py` (chronicle + quest + agent discovery)
- NuSyQ-Hub references CONCEPT as a registered agent in `data/agents/agents.json`
- Gordon's MCP stack (`gordon-mcp.yml`) mounts CONCEPT at `/rootfs/concept` via the filesystem server

## Interaction Matrix

Use this as the fast mental model for repo-to-repo value flow:

| From | To | Why it matters |
|------|----|----------------|
| **CONCEPT** | **Dev-Mentor / TerminalDepths** | Keeper gives preflight pressure, advisor, and maintenance context before game/task/orchestration work |
| **Dev-Mentor / TerminalDepths** | **CONCEPT** | Agents call Keeper through MCP instead of guessing machine state |
| **CONCEPT** | **SimulatedVerse** | Keeper protects ChatDev and simulation bring-up from machine-pressure blind spots |
| **SimulatedVerse** | **CONCEPT** | Recovery needs on `5002` and `4466` are a direct signal that machine/runtime state matters |
| **CONCEPT** | **NuSyQ-Hub** | Machine state feeds better healing and routing decisions |
| **NuSyQ-Hub** | **CONCEPT** | Hub acts as orchestration brain above Keeper's machine-governance layer |
| **NuSyQ-Hub** | **Nogic** | Nogic bridge is real and can be treated as an architecture visualization surface |
| **NuSyQ-Hub** | **GitNexus** | GitNexus is live and exposes `/api/gitnexus/health`, `/api/gitnexus/matrix`, and `/api/gitnexus/repos/{repo_id}` |

## Cross-Repo Operating Sequence

Use this sequence before any heavy Docker/Ollama/ChatDev workflow:

```powershell
# 1. Keeper preflight (always)
pwsh -File C:\CONCEPT\tools\keeper-bridge.ps1 snapshot
pwsh -File C:\CONCEPT\keeper.ps1 score
pwsh -File C:\CONCEPT\keeper.ps1 advisor
pwsh -File C:\CONCEPT\keeper.ps1 think

# 2. Only if score < 60 and advisor != "none":
pwsh -File C:\CONCEPT\keeper.ps1 optimize

# 3. Then start your heavy workflow (docker compose, Ollama, ChatDev)

# 4. Post-run snapshot if the task was heavy
pwsh -File C:\CONCEPT\tools\keeper-bridge.ps1 snapshot
```

**Via MCP (in any connected client):**
```
keeper_snapshot → keeper_score → keeper_advisor → (keeper_optimize if needed) → proceed
```

## Current Caveats

- Continuity MCP is currently degraded in repo-local context, so fallback files such as [AGENTS.md](/mnt/c/CONCEPT/AGENTS.md) and [`.continuity/SESSION_NOTES.md`](/mnt/c/CONCEPT/.continuity/SESSION_NOTES.md) may still matter for session memory.
- Keeper runtime commands must execute on Windows.
- Full Pester suite passed on 2026-03-30: 67 passed, 0 failed.
- In this shell, `pwsh` previously required explicit path handling; the workspace MCP config now points at the absolute PowerShell 7 executable.
- Not every upstream surface is mounted from this repo by default. Some capabilities live in sibling repos and need to be attached or discovered there.

## Federation Rule

If Gordon can reach a relevant upstream tool, model endpoint, orchestration surface, or agent interface, it should be considered in-bounds. The intended reach includes:

- Keeper
- Dev-Mentor / Terminal Depths
- NuSyQ-Hub
- SimulatedVerse
- Serena
- Culture Ship
- SkyClaw and other claw-family tools
- Ollama
- LM Studio
- ChatDev
- delegation, orchestration, and sub-agent pathways across the ecosystem

## Runtime Notes

- LM Studio is confirmed reachable from native Windows at `http://127.0.0.1:1234/v1/models`.
- In this environment, WSL bridge addresses for LM Studio have been inconsistent. Verify Windows localhost first before treating LM Studio as down.
- The ChatDev adapter is currently reachable at `http://127.0.0.1:4466/chatdev/agents`.
- SimulatedVerse minimal mode is currently reachable at `http://127.0.0.1:5002/api/health`.
- Use [`tools/compact-docker-vhd.ps1`](/mnt/c/CONCEPT/tools/compact-docker-vhd.ps1) for report-only or elevated Docker/WSL VHD compaction prep when disk pressure is dominated by `docker_data.vhdx`.
- If a Windows-native service is up but `127.0.0.1` fails from WSL, prefer the Windows host bridge address before assuming the service is down.

## Surgical Recovery Commands

If the SimulatedVerse surfaces are down but the repo is already prepared, use durable detached launches instead of broad investigation:

```bash
cd /mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse
setsid -f bash -lc 'exec npm run dev:minimal </dev/null >/tmp/simulatedverse-minimal.log 2>&1'

cd /mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/packages/chatdev-adapter
setsid -f bash -lc 'exec npm run start </dev/null >/tmp/chatdev-adapter.log 2>&1'
```

Then verify:

```bash
curl http://127.0.0.1:5002/api/health
curl http://127.0.0.1:4466/chatdev/agents
```

## Good First Calls

- `keeper_snapshot`
- `keeper_score`
- `keeper_advisor`
- `keeper_games`
- `keeper_think`

## Use `analyze` When

- deterministic tools disagree with observed behavior
- audio triage needs correlation with recent action logs
- you need a concise hypothesis after `snapshot` + `doctor` + `score` have already been captured
