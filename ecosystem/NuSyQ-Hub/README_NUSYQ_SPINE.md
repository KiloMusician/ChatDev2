NuSyQ Spine (opt-in)
=====================

This repository includes a lightweight, opt-in NuSyQ "spine" that emits small, best-effort events for higher-level orchestration and observability. The spine is disabled by default.

Enable
------
- Edit `config/nusyq_spine.yaml` and set `enabled: true`.

Quick smoke test
----------------
1. Ensure MCP server is running (the project commonly exposes a health endpoint on port 8001):

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

2. Run a unit/functional test that exercises `src/tools/agent_task_router.py` routing (filtered tests recommended):

```powershell
python -m pytest -q -k 'not e2e and not llm_testing'
```

Notes
-----
- Spine event emission is best-effort and non-blocking. If the spine is disabled the code paths remain dormant.
- Use the smoke tests and `scripts/probe_endpoints.py` to verify local LLM endpoints before running orchestration experiments.
NuSyQ Spine
===============

Opt-in, small orchestration spine for NuSyQ-Hub. Place under `src/nusyq_spine`.

Quick start (from repo root):

```bash
python -m src.nusyq_spine.cli status
python -m src.nusyq_spine.cli snapshot
python -m src.nusyq_spine.cli find lint
python -m src.nusyq_spine.cli run "python -m pytest -q -k 'not e2e and not llm_testing'"
```

Enable by editing `config/nusyq_spine.yaml` and setting `enable: true`.
