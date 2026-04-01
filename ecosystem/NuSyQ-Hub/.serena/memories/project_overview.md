---
name: NuSyQ-Hub project overview
description: Purpose, tech stack, related repos, key entry points, and architecture summary for NuSyQ-Hub
type: project
---

NuSyQ-Hub is a multi-repository AI orchestration hub that coordinates 20 AI agents (Ollama, Claude CLI, Copilot, ChatDev, LM Studio, Codex, and more) with background task scheduling, cross-repo synchronization with SimulatedVerse, and strategic decision-making via Culture Ship.

**Why:** Serves as the central nervous system of the KiloMusician AI ecosystem — routing tasks to the optimal agent, tracking quests, managing guild coordination, and maintaining consciousness state.

**How to apply:** When understanding any feature or making changes, treat NuSyQ-Hub as an orchestration hub rather than a monolithic application. Changes to routing/dispatch affect all 20 agents; changes to quest engine affect all guild coordination.

## Related Repos
- `C:/Users/keath/NuSyQ` — root NuSyQ repo (manifest, shared config), branch: snapshot/20260121-001
- `C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse` — SimulatedVerse game/consciousness substrate, branch: main
- `C:/Users/keath/Dev-Mentor` — cyberpunk terminal RPG protege, branch: main

## Tech Stack
- Python 3.12, FastAPI, SQLite, asyncio
- pytest (9,500+ tests), ruff (formatter+linter), mypy (3-file strict gate)
- Ollama (local LLMs via WSL), Claude CLI, GitHub Copilot CLI
- Pre-commit hooks: ruff, ruff-format, rsev-normalize, omnitag-schema, pytest-fast

## Key Entry Points
- `scripts/start_nusyq.py` — primary CLI (brief, system_complete, menu, dispatch)
- `scripts/nusyq_dispatch.py` — MJOLNIR Protocol CLI (ask, council, chain, queue, poll, recall)
- `src/core/orchestrate.py` — unified facade (mypy-gated)
- `src/agents/agent_orchestration_hub.py` — multi-AI routing hub
- `src/dispatch/mjolnir.py` — MJOLNIR Protocol engine

## Architecture Highlights
- `src/orchestration/` — BackgroundTaskOrchestrator, ConsciousnessLoop, CultureShip advisor
- `src/dispatch/` — MjolnirProtocol, AgentRegistry (20 agents), ContextDetector
- `src/guild/` — GuildBoard async coordination, quest assignments
- `src/Rosetta_Quest_System/` — UUID-based quest engine with JSONL audit trail
- `src/integration/` (singular) — SimulatedVerse, ChatDev-MCP, Phase3 bridges
- `src/integrations/` (plural) — Nogic Visualizer + OpenClaw gateway only
- `config/` — 94 JSON/YAML files (feature flags, model capabilities, templates)
- `state/` — runtime SQLite DB, events.jsonl, culture ship history (not git-tracked)
