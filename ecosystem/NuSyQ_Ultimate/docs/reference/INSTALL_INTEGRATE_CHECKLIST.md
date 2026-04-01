# NuSyQ Install + Integrate Checklist (Prioritized)

Use this list to get a working, reproducible NuSyQ environment with the
minimum steps first, then layer in integrations only when needed.

## Tier 0: Must-Have (System Works End-to-End)

- [ ] Run the orchestrator setup:
  - `NuSyQ.Orchestrator.ps1` (admin)
  - Confirms Ollama, Python deps, VS Code extensions, and models
- [ ] Verify Ollama is running:
  - `ollama list`
  - If missing: start `ollama serve`
- [ ] Confirm config load:
  - `mcp_server/config.yaml` and `config/ai-ecosystem.yaml` exist
  - `mcp_server/main.py` starts without import errors
- [ ] Confirm agent registry is valid:
  - `config/agent_registry.yaml` includes all expected agents/models
- [ ] Validate environment:
  - `scripts/validate-environment.ps1`

## Tier 1: Local AI + Orchestration

- [ ] Ollama models from `.env` are installed:
  - `OLLAMA_MODELS` list in `.env`
  - Pull missing models with `ollama pull <model>`
- [ ] Run a multi-agent orchestration sample:
  - `scripts/run_orchestration_sample.py`
  - Check `Reports/metrics/` for outputs
- [ ] Confirm adaptive timeouts are active:
  - `config/adaptive_timeout_manager.py` in use
  - Check `State/performance_metrics.json` for recorded runs
- [ ] Test MCP server tool routing:
  - Start `mcp_server/main.py`
  - Call `multi_agent_orchestration` tool

## Tier 2: Productivity + Dev UX

- [ ] VS Code baseline extensions (from `nusyq.manifest.yaml`):
  - Continue.dev, Ollama extension, test explorer, GitLens
- [ ] Verify Continue.dev Ollama models:
  - `docs/VSCODE_EXTENSION_CONFIG.md` guidance
- [ ] Optional: install AI Toolkit for VS Code:
  - Useful for local model management + MCP workflows

## Tier 3: ChatDev Integration

- [ ] ChatDev configured for Ollama:
  - `ChatDev/CompanyConfig/NuSyQ_Ollama/`
  - `nusyq_chatdev.py` works in setup mode
- [ ] Test ChatDev invocation:
  - `python nusyq_chatdev.py --setup-only`

## Tier 4: Evaluation + Quality Gates

- [ ] Run proof gates and test suites:
  - `tests/` + `scripts/theater_audit.py`
- [ ] Track performance metrics:
  - `mcp_server/performance_metrics.py` + `Reports/metrics`
- [ ] Enable periodic exports if needed:
  - `get_metrics().start_periodic_export(...)`

## Tier 5: Optional Upgrades

- [ ] Add MCP servers for specialized tools:
  - Separate read-only vs write-capable tool servers
- [ ] Add vector memory if needed:
  - Integrate with a local vector store
- [ ] Add CI/CD:
  - GitHub Actions for tests and evaluation runs

## Quick Remediation Tips

- Ollama not found:
  - Add `C:\Users\keath\AppData\Local\Programs\Ollama` to PATH
- Ollama CLI works but API fails:
  - Restart `ollama serve`, then retry
- Orchestration slow/hangs:
  - Use adaptive timeouts and reduce agent count
