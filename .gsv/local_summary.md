# ChatDev2 — GSV Sector Card

**Role:** Zero-code multi-agent orchestration platform  
**Stack:** Python, OpenBMB/ChatDev 2.0, CAMEL framework  
**Colony port:** `:7338` (health: `/health`)

## What it does
Multi-agent software development via role-playing agents (CEO, CTO, Programmer, Reviewer).
Submit a task → agents collaborate through phases → code artifact produced.

## Key directories
| Path | Purpose |
|------|---------|
| `chatdev/` | Core runtime (roles, phases, task execution) |
| `camel/` | CAMEL multi-agent framework |
| `ecl/` | Experiential Co-Learning module |
| `CompanyConfig/` | Agent company templates |
| `ecosystem/` | Colony integration hooks |

## Colony connections
- Tasks submitted via `Dev-Mentor/tasks/queue.json`
- `chatdev plan "..."` via kilo membrane → writes plan to queue
- `delegation_planner.py chatdev "title"` in Kilo_Core/scripts/agents/
- Use for: scaffold generation, boilerplate, multi-file features

## When to use
```
chatdev plan "add X command to Terminal Depths"
chatdev plan "scaffold new NuSyQ endpoint for Y"
```
