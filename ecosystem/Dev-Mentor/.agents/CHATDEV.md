# ChatDev — DevMentor / Terminal Depths Integration Guide
> Updated: 2026-03-24 | Port: 7337 (local/VS Code) | 5000 (Replit)

---

## Project Structure for ChatDev

ChatDev simulates a software team. Map project roles:

### ChatDev Role → DevMentor Area
| ChatDev Role | Files to Own | Focus |
|---|---|---|
| **CTO / Architect** | `docs/ARCHITECTURE.md`, `app/backend/main.py` | System design, API contracts |
| **Chief Programmer** | `app/game_engine/commands.py` | Game command implementation |
| **Programmer** | `app/game_engine/filesystem.py`, `app/game_engine/story.py` | VFS and story content |
| **Art Designer** | Terminal UI helpers (`_sys`, `_lore`, ASCII art in commands.py) | Output formatting, ASCII art |
| **QA Engineer** | `tests/`, REST API testing | Command validation, regression |
| **CEO / PM** | `docs/FEATURE_BACKLOG.md`, `AGENTS.md` | Scope, agent coordination, backlog |
| **DevOps** | `app/backend/main.py` `_startup()`, `.github/workflows/` | CI, server lifecycle |

---

## ChatDev Task: Add a Feature

```
Phase 1 — Demand Analysis:
  Input: Feature description from docs/FEATURE_BACKLOG.md
  Output: Technical spec (method name, args, return format, man page filename)
  Check: Does a _cmd_<name> already exist? (grep -n "def _cmd_" commands.py)

Phase 2 — Language Choice: Python 3.11 (FastAPI + game engine pattern)

Phase 3 — Coding:
  CTO:        Define method signature + docstring
  Programmer: Implement _cmd_<name>() method in CommandRegistry class
  Programmer: Register in dispatch aliases dict (~line 1450 in _dispatch)
  Art Designer: Design output format (which helpers, ASCII layout, colors)
  Programmer: Create docs/commands/<name>.md man page

Phase 4 — Code Review:
  Mandatory syntax check:
    python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"
  Mandatory .pyc purge (prevents stale bytecode bug):
    find app -name '*.pyc' -delete
  Live test (port 7337 local, 5000 Replit):
    curl -sX POST http://localhost:7337/api/game/command \
      -H "Content-Type: application/json" \
      -d '{"session_id":"chatdev","command":"<name>"}'

Phase 5 — Test:
  QA: Run pytest: python -m pytest tests/ -q
  QA: Verify output format (all lines have 's' key, types are valid)
  QA: Check XP awards fire correctly
  QA: Check story beats persist across commands

Phase 6 — Environment Doc:
  Create: docs/commands/<name>.md (see CODEX.md for template)
  Update: docs/FEATURE_BACKLOG.md (mark [x])
  Update: AGENTS.md command count if it changed
```

---

## ChatDev Config Template

```json
{
  "project_name": "Terminal Depths Feature Sprint",
  "language": "Python",
  "target": "app/game_engine/commands.py",
  "background_docs": ["CONTEXT.md", "AGENTS.md", "docs/ARCHITECTURE.md"],
  "test_command": "python -m pytest tests/ -q && curl -sX POST http://localhost:7337/api/game/command -H 'Content-Type: application/json' -d '{\"session_id\":\"chatdev\",\"command\":\"help\"}'",
  "rules": [
    "Never use _info() — use _line(text, type) instead",
    "Always syntax-check commands.py after editing",
    "Always delete .pyc files after editing (find app -name '*.pyc' -delete)",
    "Always create a man page in docs/commands/<name>.md",
    "Always register new commands in the aliases dict if needed",
    "Port 7337 for local, 5000 for Replit — never mix them"
  ],
  "anti_patterns": [
    "_info('text')               ← NameError crash",
    "gs.xp += 50                ← use gs.award_xp('skill', 50)",
    "import commands             ← circular; methods are already in CommandRegistry",
    "rewriting large sections    ← surgical edits only in 32k-line file"
  ]
}
```

---

## ChatDev Suggested Sprint Tasks (prioritized backlog)

### Sprint: Dialogue Depth
| Task | File | Complexity |
|------|------|-----------|
| Expand Ada dialogue variety (10+ new responses for `talk ada` post-intro) | commands.py | Medium |
| Write Nova dialogue tree (currently thin — just 3 responses) | commands.py | Medium |
| Add `duel surrender` subcommand + duel timeout after 10 commands | duels.py | Medium |
| Write `serena_awakened` story beat (unlocks L4 trust) | commands.py + story.py | Low |

### Sprint: Polish
| Task | File | Complexity |
|------|------|-----------|
| Fix `ascend` — write actual story conclusion (currently a stub) | commands.py | High |
| Fix challenge validation — normalize whitespace/case before comparing | challenge_engine.py | Low |
| Add `leaderboard` real data (currently placeholder text) | commands.py + main.py | Medium |
| Fix Serena drift score — always returns 0.0 | serena_analytics.py | Medium |

### Sprint: Infrastructure
| Task | File | Complexity |
|------|------|-----------|
| Optimize startup .pyc purge — limit rglob to `app/` only | main.py | Low |
| Add `duel` exit via timeout (no player input for N commands) | session.py + duels.py | Medium |
| RimWorld mod compilation setup (VS Code + dotnet build task) | .vscode/tasks.json | Medium |

---

## Critical Engineering Rules (paste into ChatDev system prompt)

```
You are working on a 32,700-line Python game engine (commands.py).
Rules:
1. SURGICAL EDITS ONLY — never rewrite a function without reading it first
2. Output helpers: _sys, _ok, _err, _dim, _lore, _warn, _line(text, type) 
   — _info() does NOT exist, using it crashes the server
3. After EVERY edit: python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read())"
4. After EVERY edit: find app -name '*.pyc' -delete
5. Port 7337 = local/VS Code. Port 5000 = Replit ONLY.
6. Do not commit .devmentor/ or state/ directories — they are gitignored runtime state
7. The read tool only shows ~18,600 lines — use sed -n 'N,Mp' for deeper sections
```
