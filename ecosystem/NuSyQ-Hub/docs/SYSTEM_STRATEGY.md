# System Strategy: Self-Healing, Model Flexibility, and Orchestration

This living document captures the design goals and runbook for NuSyQ's
multi-repo ecosystem (NuSyQ-Hub, NuSyQ/ChatDev, SimulatedVerse). It focuses on
three pillars:

- Dynamic model discovery and mapping
- Lightweight runtime observability (busy flags, availability)
- Self-healing and graceful model swapping

Goals

- Keep no hard-coded model names or paths; prefer discovery via HTTP endpoints
  (Ollama `/api/tags`, LM Studio `/v1/models`).
- Provide an authoritative `state/llm_inventory.json` that orchestrators consult
  at startup and periodically refresh.
- Make providers expose availability and busy state; orchestrators should prefer
  `available_nonbusy()` providers for task routing.

Runbook (Bring-up)

1. Start local runtimes (Ollama, LM Studio) and ensure they are reachable.
2. Run `python scripts/discover_llms.py` to create `state/llm_inventory.json`.
3. Start orchestrator (MCP / NuSyQ-Hub). The coordinator will load inventory and
   register core providers in the `LLMRegistry`.
4. Use `scripts/check_coordinator_status.py` and MCP `/health` endpoints to
   verify provider availability and busy state.

Model swapping and evolution

- Add new models locally (pull into Ollama or LM Studio). Re-run discovery.
- Orchestrator should support hot-reload of `state/llm_inventory.json`.
- Provide unit tests & CI to simulate model removal/addition and ensure fallback
  paths (Ollama → OpenAI → Copilot) still function.

Self-healing

- Health checker periodically verifies each provider; on failure:
  - mark provider unavailable and busy=false
  - if provider was in-use, escalate task to fallback chain
  - attempt a restart/hook (script) for local runtime (e.g., `ollama serve`)
  - log incident to `state/reports/` and notify operator via configured channels

Observability & telemetry

- Record per-provider metrics in coordinator.performance_metrics
- Expose `LLMRegistry.busy_snapshot()` in MCP `/health` response
- Persist periodic snapshots to `state/` for offline analysis

Next steps

- Implement hot-reload of inventory and a simple UI to tag models with roles
  (code-focused, reasoning, embeddings).
- Add automated restart hooks for common runtimes and sandboxed testing to
  validate new models before they are used in production tasks.
