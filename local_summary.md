# ChatDev2 — Sector Card

**Role:** Autonomous multi-agent software development system (ChatDev v2 fork).
Operates as a colony worker — receives tasks from `Dev-Mentor/tasks/queue.json`
and produces code autonomously via its agent pipeline.

**Colony integration:**
- Tasks submitted via `delegation_planner.py chatdev "title"` or direct queue write
- Docker container: `kilocore-chatdev` on port :7338
- Uses `lattice` profile; adapts to LiteLLM :4000 for all model calls

**Key directories:**
- `camel/` — Core CAMEL agent framework
- `assets/`, `attached_assets/` — Task and output assets
- Agent roles: Programmer, Reviewer, Tester, Documenter

**Status:** Live as Docker container. Routes through LiteLLM ecosystem aliases.
Safe-mode tasks only (safe_mode: true in task envelope).

**Fast truth probe:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\chatdev_colony_doctor.ps1
```

Current verified shape on 2026-06-25:
- Live colony ChatDev `:7338` health is up.
- Dev-Mentor `:7337`, LiteLLM `:4000`, and Ollama `:11434` are reachable.
- Local checkout app imports after `fastmcp` is installed.
- Local checkout exposes bridge/ecosystem routes, but the live `:7338` service does not expose `/api/bridge/status` or `/api/ecosystem/status`; treat that as container/image drift until rebuilt or re-routed.
- Avoid broad `rg` over this repo without excluding `ecosystem/`, `logs/`, `WareHouse/`, and generated reports.

**Task envelope format:**
```json
{
  "assigned_to": "chatdev",
  "category": "hardening",
  "issue": "<task description>",
  "repo": "<repo name>",
  "safe_mode": true
}
```
