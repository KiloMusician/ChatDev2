# DevMentor - VS Code-Native Mentorship Repository

### Overview
DevMentor is a VS Code-native mentorship repository designed to teach developers VS Code, Git, GitHub, AI tools, and modern development practices, including Godot game development. It serves as a self-contained learning environment, automatically configuring the IDE and providing interactive tutorials and challenges. Its core purpose is to act as a "cognitive exoskeleton" to enhance developer effectiveness.

The project integrates a cyberpunk terminal RPG called "Terminal Depths," which functions as both a playable game and a development platform for AI agents. Terminal Depths synchronizes its progress and skills with the core DevMentor state and is part of the NuSyQ-Hub ecosystem. A RimWorld mod, "Terminal Keeper: Lattice Colonists," connects a RimWorld colony directly to the Terminal Depths AI ecosystem, allowing colonists to register as persistent agents.

### User Preferences
- Primary interface: VS Code (not chat bots)
- Focus: Teaching VS Code by using VS Code
- Design: Repository as mentor, files as lessons
- Philosophy: The repo teaches the environment as much as it teaches users
- Token Discipline: Always run deterministic ops before using LLM
- Multi-environment: actively developed in BOTH VS Code (local) and Replit simultaneously

### System Architecture

#### Core Structure and Features
DevMentor is organized with dedicated directories for VS Code configurations, Python runtime logic, learning content, state management, documentation, and an orchestration framework for 71 agents.

Key architectural decisions and features include:
- **VS Code Integration:** `tasks.json` serves as a control panel for operations and workspace improvements.
- **State Management:** Progress, skill XP, achievements, and onboarding status are tracked in `.devmentor/state.json`.
- **Portability:** Supports seamless transfer of project state between Replit and VS Code.
- **Zero-Token Intelligence:** Python scripts handle deterministic actions like status generation and challenge validation without LLM reliance.
- **Port Resolution Shim:** `core/port_resolver.py` is the canonical URL resolver for all NuSyQ ecosystem services. `TD_BASE` = port 5000 on Replit, port 7337 on Docker/VS Code. Never write inline `os.environ.get("TERMINAL_DEPTHS_URL", "http://localhost:5000")` — import from `core.port_resolver` instead.
- **Offline-First Health Infrastructure:** A port registry (`config/port_map.json`) and a `health_server.py` provide health, status, and metrics endpoints.
- **Meta-Awareness Layer:** Detects the execution environment and scans sibling repositories, providing fuzzy and deterministic command suggestions.
- **CHUG Engine:** A perpetual improvement engine that runs autonomous 7-phase cycles for continuous project enhancement.
- **ML Services Layer:** Includes a model registry, feature store (time-series game events), embedder (TF-IDF and Ollama), and inference wrapper, all operating offline-first with SQLite.
- **Universal Agent Integration:** `AGENTS.md` at the repo root is the universal agent entry point for various AI tools.
- **Command Palette:** Fuzzy-searches commands, lists them, and shows quest progress.
- **Terminal Depths Game Engine:** A Python-based game with a Bitburner-style scripting API for in-game automation and terminal environment education.
- **LLM Integration:** A multi-backend client (Replit AI, Ollama, OpenAI) for AI agents, reflection, error analysis, and content generation.
- **Persistent Memory:** SQLite stores agent interactions, errors, learnings, tasks, and an LLM cache.
- **71-Agent Orchestration Framework:** Manages agents using YAML-driven personalities.
- **Serena — The Convergence Layer:** A focal agent for Terminal Depths, providing commands for navigation, querying, drift detection, and policy enforcement via a Trust Level Matrix.
- **Gordon Autonomous Player Agent:** An autonomous agent that plays Terminal Depths via its REST API, following a 7-phase strategic loop.
- **Terminal Abstraction Module:** Detects running surfaces and shell types, providing context-aware command execution.
- **Plugin System:** A modular architecture for challenge generation, documentation, formatting, and testing.
- **Model Context Protocol (MCP):** A JSON-RPC 2.0 server providing tools for file system, memory, game commands, LLM generation, game state, and system status.
- **NuSyQ-Hub Integration:** Bridges Terminal Depths with the NuSyQ-Hub ecosystem for agent manifest publishing and chronicle management.
- **The Lattice Knowledge Store:** A SQLite knowledge graph with cosine-similarity search.
- **Lattice Cascade Stack:** A full Docker Compose ecosystem with 15 services, including Redis pub/sub, Ollama, and OpenWebUI.
- **Gordon Orchestrator:** Monitors all services, detects RimWorld crashes, delegates tasks to agents via Redis pub/sub, and triggers CHUG engine cycles.
- **Sidecar Service Launcher:** Launches `serena_analytics`, `model_router`, and a Gordon one-shot cycle as background subprocesses on server startup.
- **Culture Ship:** A meta-controller that subscribes to Redis channels, runs AI Council votes on critical events, and publishes ethical reviews and strategic advice.
- **SkyClaw Scanner:** Scans filesystem, colony state, and crash logs for anomalies, publishing alerts and discoveries.
- **RimAPI Bridge:** A FastAPI service relaying RimWorld pawn state, incidents, and crashes to the Lattice via Redis.
- **RimWorld VNC Container:** A Dockerized Linux RimWorld instance with VNC, auto-configured mods, and crash detection.
- **Simulation Bridge:** A real-time WebSocket bridge connecting the graphical UI to the Python simulation, forwarding commands and pushing state updates.
- **Universal Integration Layer:** Terminal Depths acts as a universal integration point for IDEs, CLIs, and LLMs, including an Agent Identity System and Agent API Endpoints.
- **Real Git Integration:** Real subprocess git calls using GITHUB_TOKEN for `status`, `log`, `diff`, `pull`, `fetch`, `clone`, `push`, `commit`, `branch`.
- **VirtualFS Real-Directory Mounts:** Overlays any real filesystem directory at a virtual path, making `ls`, `cat`, `cd` mount-aware.

#### UI/UX Decisions (Terminal Depths)
- **Cyberpunk Aesthetic:** Features CRT vignette, scan lines, pulse-red root prompt, skill gradients, and glitch animations.
- **Interactive Elements:** Filenames, NPC tags, map nodes, and command history entries are clickable.
- **Ambient Sound System:** Uses Web Audio API for ambient music and key click sound effects.

### External Dependencies
- **Replit AI:** LLM functionalities.
- **Ollama:** Optional local LLM backend.
- **OpenAI:** Optional external LLM service.
- **GitHub:** Version control.
- **FastAPI:** Replit interactive web console and API services.
- **Typer/Rich:** CLI wrapper.
- **xterm.js:** Thin client for Terminal Depths.
- **SQLite:** Persistent agent memory and data storage.
- **Web Audio API:** Ambient music and SFX.
- **PyYAML:** Agent personality loading.
- **requests:** Gordon player agent HTTP calls.
- **numpy / scipy:** RL Phase 3 (PPO) — installed 2026-03-25.

### Current Sprint
**Hardening Sprint + Port Shim Sprint — PASS=25 WARN=1(git) FAIL=0 | 534 handlers**

New files created:
- `SYSTEM_ARCHITECTURE.md` — Definitive three-system clarity (DevMentor vs Terminal Depths vs Terminal Keeper), port rules, naming conventions, what lives where
- `.claude/CLAUDE.md` — Claude Code / Copilot context file: 16 MCP tools, architectural rules, key files, database schema, quick commands, traps list
- `core/port_resolver.py` — Ecosystem-wide port/URL resolution shim; replaces 30 scattered inline `os.environ.get("TERMINAL_DEPTHS_URL", "http://localhost:5000")` in `mcp/server.py`

Key changes:
- `.vscode/mcp.json` — Cross-platform (removed `C:/Users/keath/` paths); auto-detects port via `core/port_resolver.py`; no hardcoded `TERMINAL_DEPTHS_URL` (auto-detect handles it correctly per environment)
- `.vscode/settings.json` — Added Linux and Mac terminal profiles; removed user-specific Python interpreter path; added Ruff formatter settings
- `.devcontainer/devcontainer.json` — Ruff replaces black/pylint; removed postStartCommand conflict with Dockerfile ENTRYPOINT; added Ruff, Pylance, Biome extensions
- `Dockerfile` — Copies `*.md` and `docs/` so Docker image has full documentation
- `agents/serena/policy.yaml` — `boundary_exceptions` section resolves 4 ARCH_BOUNDARY drift warnings for `llm_client` import
- `state/serena_memory.db` — Added `session_graph` table (14 cols, 3 indexes)
- `AGENTS.md` — MCP section updated: `mcp/server.py` canonical (16 tools), count 533→534
- `.vscode/continue/config.json` — 5 models, tabAutocomplete, 4 custom commands, nomic-embed-text embeddings
- `mcp/server.py` — 30 inline port lookups → single module-level `_TD_BASE` via `core.port_resolver`
- `SYSTEM_ARCHITECTURE.md` — Port shim section added with usage examples

Previous sprints: Agent Torch-Passing, Deep System Audit, RimWorld Mod Audit, Integration Matrix, Autonomous Boot Engine.

**Next:** T3 LSP hover server (`scripts/lsp_server.py`), RL Phase 3 PPO (`agents/rl/ppo.py`), consciousness XP hooks, `integrate --github` deep-dive, Serena `session_graph` writer, `llm_client` → `core/llm.py` refactor.