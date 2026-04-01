# Onboarding & API Documentation

Welcome to NuSyQ-Hub! This guide will help you get started, understand the architecture, and contribute effectively.

## Quickstart
1. Clone the repo and run `python scripts/setup_env.py` or `poetry install`.
2. Use `make lint` and `make test` to check code quality and run tests.
3. Start the system: `python scripts/start_nusyq.py` or use VS Code tasks.

## Architecture
- **Orchestration:** `src/orchestration/` (task routing, agent registry, background tasks)
- **Healing:** `src/healing/` (self-repair, quantum problem resolver)
- **Integration:** `src/integration/` (SimulatedVerse, ChatDev, MCP server)
- **Quest System:** `src/Rosetta_Quest_System/` (quest log, task tracking)
- **Agents:** `src/agents/` (agent roles, communication hub)

## API Docs
- All public modules and functions are documented with docstrings.
- See `docs/` for Sphinx/MkDocs-generated API documentation (run `make docs`).

## Tutorials
- See `docs/Agent-Tutorials/` for agent orchestration, tracing, and advanced usage.

## Contribution
- Follow the [Three Before New Protocol](docs/THREE_BEFORE_NEW_PROTOCOL.md).
- Use pre-commit hooks and ensure all tests pass before PRs.

For more, see `README.md`, `AGENTS.md`, and `docs/`.
