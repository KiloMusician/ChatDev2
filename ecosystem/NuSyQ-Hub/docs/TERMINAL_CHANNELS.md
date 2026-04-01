# Terminal Channels

The NPC-grade terminal HUD is powered by structured “channels” — curated log streams under `data/terminal_logs/` that the modular UI, the culture ship console, and `service_watch.py` read for telemetry, ChatDev receipts, and agent-level hints.

## service_watch
- **Path**: `data/terminal_logs/service_watch.log`
- **Source**: `scripts/service_watch.py` (also writes to `state/reports/ship_status.json` and triggers the HUD widgets in `web/modular-window-server/public/js/widgets.js`).  
- **Format**: one JSON object per line with `timestamp`, `ports` (mcp/critical/window/trace/ollama), `duplicates`, `chatdev_receipt`, and `warehouse_artifact`.  
- **Purpose**: gives real-time status of the five monitored ports, duplicate launcher counts, and the latest ChatDev/WareHouse artifacts; the printable summary is shown directly in the terminal when you run `python scripts/service_watch.py`.

## ImportCheck
- **Path**: `data/terminal_logs/importcheck.log.*`
- **Source**: the `ImportCheck` logging channel (`src.tools.agent_task_router`, `src.integration.mcp_server`, orchestration helpers).  
- **Use**: contains `[RECEIPT]` entries from agent task routing, Multi-AI orchestrator initialization, and reconciliations. Scan its most recent file to confirm which agent (ChatDev, Claude, Copilot, Ollama) finished work.

## ChatGPT-Bridge
- **Path**: `data/terminal_logs/chatgpt_bridge.log.*`
- **Source**: `src.orchestration.unified_ai_orchestrator` and bridging helpers between NuSyQ-Hub and GPT-reliant agents.  
- **Use**: surfaces general AI orchestration events, pipeline registration, and error reports when telemetry/OTLP (4318) is unavailable.

## Other terminal helpers
- **`data/terminal_logs/*.log`**: any log prefixed by a channel name (e.g., `culture_ship`, `mcp_server`, `modular_window`) can feed into the HUD.  
- **Widget integration**: the UI loads `service_watch.py --json` to show port health, while the terminal prints receipts from ImportCheck and ChatGPT-Bridge by tailing those files.

Treat this doc as the schema for the terminal HUD: whenever a new channel is introduced (new `.log` stream or JSON emitter), update `TERMINAL_CHANNELS.md` so future agents know which log to monitor for status, receipts, hints, or mission grading.

## Interactive helpers
- `scripts/interactive/service_watch_interactive.py` – runs `interactive_status_dump()`, the CLI `service_watch` in `--json` mode, and tails the latest `service_watch.log` entry so the VS Code interactive window shows the freshest ports and receipts before you reconnect the widget HUD.
- `scripts/interactive/service_manager_interactive.py` – loads `ServiceManager`, dumps the cached state file, and inspects the pid locks for the critical launchers (`cross_sync`, `guild_renderer`, `pu_queue_runner`). Use these cells as a lightweight sanity check before spawning new services.
