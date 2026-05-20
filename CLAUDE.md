# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Role in Colony

`ChatDev2` is the **zero-code multi-agent orchestration platform** in the colony stack. It runs as `kilocore-chatdev` on host port `:7338` (health: `/health`). It is the upstream `OpenBMB/ChatDev` project, customized for colony integration.

Colony integration point: tasks can be submitted via `Dev-Mentor/tasks/queue.json` or using `delegation_planner.py chatdev "title"` in `Kilo_Core/scripts/agents/`.

## Key Directories

| Path | Purpose |
|------|---------|
| `chatdev/` | Core ChatDev 2.0 runtime (agent roles, phase logic, task execution) |
| `camel/` | CAMEL multi-agent framework used by ChatDev |
| `ecl/` | Experiential Co-Learning module |
| `entity/` | Agent entity definitions |
| `ecosystem/` | Colony ecosystem integration hooks |
| `CompanyConfig/` | Configurable agent company templates |
| `frontend/` | Web UI (DevAll platform) |

## Running

```bash
# Container (preferred — starts with colony stack)
docker compose up -d kilocore-chatdev

# Check health
curl http://localhost:7338/health
```

## Colony Integration

- ChatDev tasks are submitted through `Dev-Mentor` — do not call the container API directly for colony tasks
- The container reads `OLLAMA_HOST` from the environment (set to `http://host.docker.internal:11435` via `docker-compose.override.yml`)
- Colony task flow: `dispatch.py :9002` → DevMentor queue → `kilocore-chatdev :7338`

## Agent Rules

- Do not modify `camel/` or `chatdev/` core unless patching a specific colony-facing bug
- `ecosystem/` is the correct seam for colony integration changes
- After any change, run `docker compose restart kilocore-chatdev` and verify `/health` returns 200
