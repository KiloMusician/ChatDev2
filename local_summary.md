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
