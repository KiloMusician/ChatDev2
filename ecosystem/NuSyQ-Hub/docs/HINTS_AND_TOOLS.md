# Help, Hints & Evolve - Game-Like System Guide

This file documents the in-app Help & Hints features, game-like progression mechanics, and how to extend them.

Inspired by hacker games like **Bitburner**, **Hacknet**, **GreyHack**, **EmuDevz**, and **HackHub**.

---

## Core Endpoints

### Information & Guidance
| Endpoint | Description |
|----------|-------------|
| `GET /api/hints` | Contextual hints from quest engine |
| `GET /api/tutorials` | Step-by-step tutorials |
| `GET /api/faq` | Frequently asked questions |
| `GET /api/commands` | Command catalog |
| `GET /api/scripts` | Scripts inventory |
| `GET /api/inventory` | Game inventory items |
| `GET /api/ops` | Operations helpers |

### fl1ght.exe Smart Search
| Endpoint | Description |
|----------|-------------|
| `GET /api/fl1ght?q=<query>` | Smart search across all knowledge |
| `GET /api/fl1ght?q=<query>&include_code=true` | Include codebase in search |
| `GET /api/search?q=<query>` | Basic catalog search |

### RPG Progression
| Endpoint | Description |
|----------|-------------|
| `GET /api/progress` | Overall game progression stats |
| `GET /api/skills` | Skill XP and levels |
| `GET /api/rpg/status` | Full RPG inventory status |
| `POST /api/rpg/xp?skill=<name>&points=10` | Award XP to a skill |

### Tips & Contextual Help
| Endpoint | Description |
|----------|-------------|
| `GET /api/tips/random` | Random helpful tip |
| `GET /api/tips/contextual?context=error` | Context-aware tips |

### Guild Board (Multi-Agent Coordination)
| Endpoint | Description |
|----------|-------------|
| `GET /api/guild/quests` | List guild quests |
| `GET /api/guild/quests?state=open` | Filter by state |
| `GET /api/guild/summary` | Guild board summary |

### Actions/Ops (Scriptable Automation)
| Endpoint | Description |
|----------|-------------|
| `GET /api/actions` | List available actions with XP rewards |
| `GET /api/actions/<name>` | Get action details |
| `POST /api/actions/execute` | Execute an action |

### Evolve System
| Endpoint | Description |
|----------|-------------|
| `GET /api/evolve` | List persisted evolve suggestions |
| `POST /api/evolve` | Trigger evolve suggestion |

### System Info
| Endpoint | Description |
|----------|-------------|
| `GET /api/map` | System map of all endpoints |
| `GET /api/whoami` | Session/agent identity |

---

## Quick Examples

### fl1ght.exe Smart Search
```bash
# Search for quest-related info
curl "http://localhost:8000/api/fl1ght?q=quest"

# Search with code results
curl "http://localhost:8000/api/fl1ght?q=terminal&include_code=true"
```

Response:
```json
{
  "query": "quest",
  "total_results": 12,
  "categories": {"commands": 3, "hints": 5, "tutorials": 2, "faq": 2},
  "results": [...],
  "suggestions": ["Try running: start_nusyq.py queue", "Check hint: Quest Priority"]
}
```

### Game Progression
```bash
# Check progress
curl http://localhost:8000/api/progress
```

Response:
```json
{
  "evolution_level": 2,
  "consciousness_score": 35.5,
  "skills_unlocked": 4,
  "quests_completed": 12,
  "temple_floor": 3,
  "achievements": ["First Steps", "Awakening"]
}
```

### Execute Actions with XP
```bash
# List available actions
curl http://localhost:8000/api/actions

# Execute heal action
curl -X POST http://localhost:8000/api/actions/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "heal"}'
```

Response:
```json
{
  "action": "heal",
  "success": true,
  "message": "Action 'heal' queued for execution.",
  "xp_earned": 15
}
```

---

## Terminal Commands

The frontend terminal (command-registry.js) includes these game-like commands:

| Command | Evolution | Description |
|---------|-----------|-------------|
| `fl1ght <query>` | 2 | Smart search (fl1ght.exe) |
| `skills` | 3 | Show skill progression |
| `progress` | 2 | Show game progression |
| `tip` | 1 | Get random helpful tip |
| `house` | 4 | House of Leaves maze game |
| `quest` | 4 | Quest system operations |
| `guild` | 4 | Guild board operations |
| `evolve` | 5 | Evolve to next level |

Commands unlock as your evolution level increases (1-5).

---

## UI Integration

- **Menu**: Main -> Help & Hints
- The Help panel fetches hints/tutorials/faq/commands and provides a client-side search box
- Quick "Evolve" action creates evolve suggestion artifacts
- Progress and skills are displayed in the dashboard

---

## Extending the System

### Adding Hints
Add new entries in `src/api/systems.py`:
```python
# In _fallback_hints() or create dynamic hints
Hint(id="new_hint", title="Title", text="Description", tags=["tag1"])
```

### Adding Actions
Add to `ACTIONS_REGISTRY` in `src/api/systems.py`:
```python
"my_action": {
    "description": "What it does",
    "category": "category",
    "xp": 20,
    "command": "python my_script.py",
}
```

### Adding Terminal Commands
Add to `command-registry.js`:
```javascript
this.registerCommand({
    name: 'mycommand',
    evolution: 2,  // Unlock level
    category: 'mycategory',
    description: 'Description',
    usage: 'mycommand <args>',
    execute: async (args) => { /* implementation */ }
});
```

---

## Related Systems

- **Quest Engine**: `src/tools/hint_engine.py`
- **RPG Inventory**: `src/system/rpg_inventory.py`
- **Guild Board**: `src/guild/guild_board.py`
- **Smart Search**: `src/search/smart_search.py`
- **House of Leaves**: `src/games/house_of_leaves.py`
- **Temple of Knowledge**: `src/consciousness/temple_of_knowledge/`
- **Cultivation Idle**: `web/modular-window-server/public/js/cultivation-idle-engine.js`
