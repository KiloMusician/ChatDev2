# System Port Map

The NuSyQ-Hub culture ship exposes several long-lived ports that power the modular terminal, orchestration APIs, telemetry, and local LLM servers. The `service_watch.py` script refreshes this mapping automatically so the dashboard (both the terminal HUD and the modular window UI) can highlight which endpoints are healthy.

| Port | Semantic Label | Component / Script | Notes |
| ---- | -------------- | ------------------ | ----- |
| 8080 | Modular Window | `web/modular-window-server` (main UI) | Hosts the ξNuSyQ Modular Window/terminal interface and MCP client, referenced throughout `FRONTEND_DEPLOYMENT.md`, `MENU_NAVIGATION_GUIDE.md`, and `web/modular-window-server/public/js/widgets.js`. |
| 8081 | MCP Server | `src/integration/mcp_server` (AI tooling REST API) | Dedicated REST surface for tooling (`/health`, `/tools`, `/execute`), used by `Quick Start`, `AI_AGENT_INTEGRATION_STATUS.md`, and automated tests. |
| 8090 | Window Server | `web/modular-window-server/window-server` (window service) | Secondary window/renderer port consumed by the terminal HUD, mirrors “Window” indicator in `widgets.js`, and is captured by `service_watch` as `window:8090`. |
| 4318 | Trace Collector | OpenTelemetry OTLP (local collectors) | Default OTLP trace exporter port; when the tracer is stopped the `trace:4318` entry in `service_watch` toggles to ⚠️ so agents know telemetry is offline. |
| 11434 | Ollama | Local Ollama daemon | Local LLM host (used by `src/orchestration/unified_ai_orchestrator.py`, `src/tools/agent_task_router.py`, `src/utils/ollama_client.py`). When missing, the `ollama:11434` flag in `service_watch` flips and the UI surfaces “Ollama unavailable.” |

Add new rows to this table whenever a new long-lived service port is wired into the culture ship live dashboard. The `TERMINAL_CHANNELS.md` companion file describes where the terminal HUD reads these flags for human-friendly output.
