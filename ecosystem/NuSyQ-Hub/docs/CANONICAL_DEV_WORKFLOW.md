# Canonical Dev Workflow (Daily Driver)

This short guide defines the most practical, high-signal endpoints for day‑to‑day development across games, packages, extensions, apps, and full‑stack systems.

## 1. Find Work
- `GET /api/quests`  
  Canonical quest log view. This is the authoritative task queue for the ecosystem.

## 2. Execute Work
- `GET /api/actions`  
  List actionable system operations.
- `POST /api/actions/execute`  
  Run work actions (`heal`, `work`, `suggest`, `evolve`, `test`, `queue`).

## 3. Check Code Health
- `GET /api/problems`  
  Real‑time diagnostics (VS Code + Ruff + mypy).

## 4. Ask for Guidance
- `GET /api/fl1ght`  
  Smart search across commands, quests, hints, and code.

## 5. Coordinate with Agents
- `GET /api/guild/quests`  
  Multi‑agent quest board.
- `GET /api/guild/summary`  
  Coordination status and progress.

## 6. Game / Simulation Loops
- `POST /api/hack/nmap`  
- `POST /api/hack/connect`  
- `POST /api/hack/exploit`  
- `POST /api/hack/patch`  
- `GET /api/hack/traces`  
- `GET /api/hack/sessions`

Use these endpoints to validate hacking‑game mechanics and trace‑timer flows.

## 7. Persist and Resume
- `GET /api/game/state`  
- `POST /api/game/state`  
The system auto‑persists on key actions, but these endpoints provide manual control.

## Recommended Daily Sequence
1. `/api/quests` → pick a quest  
2. `/api/actions` → execute an action  
3. `/api/problems` → validate health  
4. `/api/fl1ght` → get next steps  
5. `/api/game/state` → verify persistence

## Example: Complete a Quest (XP + Awards)
```bash
curl -X POST http://localhost:8000/api/quests/complete \
  -H "Content-Type: application/json" \
  -d '{
    "quest_id": "YOUR_QUEST_ID",
    "status": "completed",
    "skill": "automation",
    "xp": 50,
    "achievement": "quest_complete",
    "feature": "quest_rewards"
  }'
```
