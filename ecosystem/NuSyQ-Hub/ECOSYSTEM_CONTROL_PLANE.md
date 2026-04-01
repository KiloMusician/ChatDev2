# Ecosystem Control Plane

Last updated: 2026-03-31

This is the canonical operator-facing map for the current multi-repo stack.

Use this document to avoid rediscovering:

- what each repo is for
- which surfaces are live
- which systems are low-token or zero-token
- which agent/tool should be used first

## Repo Roles

| Repo | Role | Primary Value |
|------|------|---------------|
| `CONCEPT / Keeper` | machine-governance layer | pressure score, advisor, optimize, maintenance, safe-start |
| `Dev-Mentor / TerminalDepths` | interactive task plane | MCP/game/API workflow surface for operators and agents |
| `SimulatedVerse` | simulation + patch-bay runtime | live Culture Ship runtime owner, ChatDev UX/runtime, experimentation |
| `NuSyQ` | Rosetta + proof-gate layer | normalization, routing, artifact persistence, proof enforcement |
| `NuSyQ-Hub` | orchestration brain | healing, diagnostics, routing, Nogic visualization, GitNexus matrix, Culture Ship control owner |

## Live Cross-Repo Surfaces

### Deterministic / low-token first

- Keeper bridge / MCP
  - PowerShell-first machine-state preflight
- GitNexus
  - `/api/gitnexus/health`
  - `/api/gitnexus/matrix`
  - `/api/gitnexus/repos/{repo_id}`
- Nogic
  - `src/integrations/nogic_bridge.py`
  - `src/integrations/nogic_vscode_bridge.py`
- RosettaStone
  - `NuSyQ/scripts/run_rosetta_pipeline.py`
  - `NuSyQ/Reports/rosetta/`

### Runtime / service surfaces

- Dev-Mentor
  - `http://127.0.0.1:7337/api/health`
- SimulatedVerse minimal
  - `http://127.0.0.1:5002/api/health`
- ChatDev adapter
  - `http://127.0.0.1:4466/chatdev/agents`
- NuSyQ MCP
  - `http://127.0.0.1:8765/health`
- Ollama
  - `http://127.0.0.1:11434/api/tags`
- LM Studio
  - canonical Windows localhost: `http://127.0.0.1:1234/v1/models`

## Agent / Tool Use Order

Start with the cheapest reliable surface first:

1. `Keeper`
   - machine pressure, mode, maintenance, disk/WSL/docker safety
2. `GitNexus`
   - cross-repo git truth and branch state
3. `Nogic`
   - architecture/topology understanding
4. `RosettaStone`
   - normalized artifacts and repeatable proof output
5. local model backends
   - `Ollama`, `LM Studio`
6. specialized/runtime agents
   - `Gordon`, `Serena`, `Culture Ship`, `SkyClaw`, `ChatDev`, `Copilot CLI`, `Claude` when available

## Agent Roles

| Surface | Best Use |
|---------|----------|
| `Gordon` | execution, orchestration, operating the local stack |
| `Serena` | code generation, refactoring, bounded implementation work |
| `Culture Ship` | strategic and ethical coordination across systems |
| `SkyClaw / claw-family` | scanning, retrieval, command-oriented assistance |
| `ChatDev` | multi-agent generation or review tasks |
| `Ollama` | local reasoning and code assistance |
| `LM Studio` | local OpenAI-compatible model endpoint and backend comparison |
| `Copilot / Copilot CLI` | inline and terminal coding assistance |
| `Claude` | deep reasoning when available and not rate-limited |

## Token-Saving Patterns

- snapshot first, then narrow
- prefer `GitNexus` and `Keeper` before broad repo exploration
- reuse `Reports/rosetta/` artifacts instead of regenerating the same context
- use `Nogic` when topology matters instead of reconstructing it from source trees
- prefer local inference before costly external paths when the task allows it

## Zero-Token / Near-Zero-Token Capabilities

- Keeper scoring, advisor, maintenance plans
- GitNexus matrix and per-repo snapshots
- Nogic bridge-backed architecture inspection
- Rosetta artifact reuse
- local grep, rg, and cached receipts

## VS Code Extension Strategy

Treat the extension story as one control plane, not three unrelated products.

Canonical spine:

- `src/vscode_mediator_extension/`
  - primary IDE control plane

Supporting/legacy:

- `extensions/agent-dashboard/`
  - dashboard proof-of-concept
- `src/integration/vscode_extension/`
  - narrow ChatDev command surface
- `src/vscode_integration/`
  - command-palette and generated command wiring

## Known Graphical / UI Surfaces

Current IDE/UI surfaces that actually exist:

- `src/vscode_mediator_extension`
  - `NuSyQ Capability Cockpit`
  - `NuSyQ Diagnostics`
  - status-bar diagnostics and terminal topology indicators
- `extensions/agent-dashboard`
  - legacy agent/quest/error dashboard
  - now treated as a feeder/reference surface rather than the preferred entry point
- `src/integration/vscode_extension`
  - lightweight ChatDev log console and launcher
- hidden/local bridge commands already exposed through the mediator surface
  - control center
  - guild board
  - service status
  - tripartite status

Modernization direction:

- keep the mediator cockpit as the main visual shell
- absorb useful legacy dashboard behavior instead of duplicating panels
- leave narrow, single-purpose panels like ChatDev logs as supporting utilities
- document UI ownership so future work extends the control plane instead of spawning another parallel dashboard

Desired direction:

- keep `PowerShell Mediator` as the spine
- surface GitNexus, Nogic, Culture Ship, Keeper, local model health, and diagnostics there
- migrate useful dashboard behaviors into that extension instead of proliferating more packages

## Current Cross-Repo Operating Sequence

1. Keeper preflight
2. GitNexus repo truth
3. Nogic topology check when needed
4. attach runtime surfaces
5. use Rosetta artifacts or produce new ones
6. run specialized agents only after the deterministic surfaces agree

## Structured Control-Plane Read Order

All agents, scripts, and cockpits should prefer:

1. `state/boot/rosetta_bootstrap.json`
2. `state/registry.json`
3. `state/reports/control_plane_snapshot.json`
4. focused feed artifacts
5. docs fallback
