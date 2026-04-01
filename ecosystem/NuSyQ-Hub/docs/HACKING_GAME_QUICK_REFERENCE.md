# 🎮 Hacking Game Quick Reference Card

**For agents & operators integrating BitBurner/Hacknet mechanics into NuSyQ-Hub**

## Quick Commands

### Scan a Component
```bash
curl -X POST http://localhost:8000/api/games/scan \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python"}'
```
**Returns:** Ports, services, vulnerabilities, security level, trace risk

### Execute Exploit
```bash
curl -X POST http://localhost:8000/api/games/exploit \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python", "exploit_type": "ssh_crack", "xp_reward": 50}'
```
**Returns:** Success flag, access level gained, trace triggered

### Check Your Progress
```bash
curl http://localhost:8000/api/games/status
```
**Returns:** Hacking status, skill tree state, faction info

### View Available Quests
```bash
curl 'http://localhost:8000/api/games/quests?tier=2'
```
**Returns:** Quest chains, difficulty, time limits, XP rewards

### Complete a Quest
```bash
curl -X POST http://localhost:8000/api/games/quest/complete \
  -H "Content-Type: application/json" \
  -d '{"quest_id": "q_scan_python", "completion_time": 120.5}'
```
**Returns:** XP gained, skill unlocks, generated narrative

---

## Progression Tiers

| Tier | Name | Focus | XP Required | Key Skills |
|------|------|-------|-------------|------------|
| 1 | Survival | Basic scanning, repair, cracking | 0 | basic_scan, ssh_crack, component_heal |
| 2 | Automation | Script writing, multi-tasking | 500 | script_writing, multi_threading |
| 3 | AI Integration | AI co-pilots, consciousness | 2000 | ai_copilot, consciousness_bridge |
| 4 | Defense | Trace evasion, hardening | 5000 | trace_evasion, security_hardening |
| 5 | Synthesis | Multi-faction control | 10000 | emergent_strategy |

---

## Quest Chain Examples

### Beginner Chain (Tier 1)
```
q_scan_python (50 XP)
  └─> q_crack_python_ssh (75 XP)
       └─> q_patch_python (100 XP) [unlocks: component_heal]
```

### Intermediate Chain (Tier 2)
```
q_scan_network (150 XP)
  └─> q_infiltrate_ollama (125 XP)
       └─> q_write_background_scan (200 XP)
```

### Advanced Chain (Tier 3+)
```
q_ai_code_generation (250 XP) [requires: ai_copilot]
q_consciousness_query (300 XP) [requires: consciousness_bridge]
```

---

## Factions

**Built-in Factions:**
1. **SysAdmins United** — Security & infrastructure
2. **Data Collective** — Analysis & intelligence  
3. **Explorers Guild** — Discovery & mapping
4. **Architects Circle** — Design & systems
5. **Sentinels** — Protection & defense

**To Join a Faction:**
```bash
curl -X POST 'http://localhost:8000/api/games/faction/join?agent_id=my-agent' \
  -H "Content-Type: application/json" \
  -d '{"faction_id": "<faction_id>"}'
```

**To View Missions:**
```bash
curl 'http://localhost:8000/api/games/faction/<faction_id>/missions'
```

**To Complete a Mission:**
```bash
curl -X POST 'http://localhost:8000/api/games/faction/<faction_id>/mission/complete?agent_id=my-agent' \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "<mission_id>"}'
```

---

## Exploit Types (Hacknet-style)

- `ssh_crack` — SSH brute force
- `sql_inject` — SQL injection
- `buffer_overflow` — Memory exploit
- `config_leak` — Extract configuration
- `service_hijack` — Hijack running service
- `privilege_escalate` — Gain admin/root

**Example:**
```python
from src.games import ExploitType
exploit_type = ExploitType.SSH_CRACK
```

---

## Skill Tree Commands

### Check Current Skills
```python
from src.games import get_skill_tree
tree = get_skill_tree()
print(tree.get_state())
```

### Add XP
```python
tree.add_xp(100)  # Adds 100 XP, checks for tier advancement
```

### Unlock a Skill
```python
tree.unlock_skill("trace_evasion")  # Requires tier 4
```

---

## Python API Examples

### Complete Demo Script
```bash
python -m src.games.demo
```

### Direct Usage
```python
import asyncio
from src.games import get_hacking_controller, ExploitType, get_skill_tree, get_faction_system

async def example():
    controller = get_hacking_controller()
    skill_tree = get_skill_tree()

    # Scan
    scan = await controller.scan("python")

    # Exploit
    exploit = await controller.exploit("python", ExploitType.SSH_CRACK)

    # Award XP
    skill_tree.add_xp(50)

    # Check progress
    print(f"Tier: {skill_tree.state.tier.name}")

asyncio.run(example())
```

---

## Trace System

**What triggers a trace?**
- High-privilege operations (access level 3+)
- Multiple exploits on same component
- Security level >3

**Grace period:** 30-120 seconds before lockdown

**Check active traces:**
```bash
curl http://localhost:8000/api/games/traces
```

**Returns:**
```json
{
  "active_traces": 1,
  "traces": {
    "python": {
      "status": "critical",
      "countdown": 5
    }
  }
}
```

---

## Integration with Smart Search

**Smart-search for hacking resources:**
```bash
python -m src.search.smart_search keyword "exploitation" --limit 10
```

**Returns:** Relevant quests, skills, and documentation for current tier

---

## Culture Ship Narratives

**Generated on quest completion:**
```
✓ **MISSION COMPLETE**: Crack Python SSH
Successful operation against python.
Skills advanced and knowledge gained. Reputation +75.
```

**Difficulty 4+ narratives:**
```
⚡ **ELITE MISSION COMPLETE**: Master Trace Evasion
The operative executed git penetration with surgical precision,
completing the mission 80%+ under time constraints.
```

---

## Troubleshooting

**Q: "Component not scanned yet"**  
A: Must run `/api/games/scan` before other operations on that component

**Q: "Cannot unlock skill - insufficient tier"**  
A: Need to reach the required tier. Add more XP via quests.

**Q: "Exploit not available on this component"**  
A: Component doesn't have this vulnerability. Scan shows available exploits.

**Q: "Lock down triggered"**  
A: Trace completed before you finished. Retry or unlock trace_evasion skill.

---

## Learning Path

**If new to the system:**
1. Run `python -m src.games.demo` to see everything
2. Read [HACKING_GAME_INTEGRATION_GUIDE.md](./docs/HACKING_GAME_INTEGRATION_GUIDE.md)
3. Try `GET /api/games/quests?tier=1` for beginner quests
4. Complete `q_scan_python` → `q_crack_python_ssh` → `q_patch_python`
5. Join a faction and complete a mission
6. Get to Tier 2 and unlock automation skills

**If extending the system:**
1. Read [HACKING_GAME_IMPLEMENTATION_SUMMARY.md](./docs/HACKING_GAME_IMPLEMENTATION_SUMMARY.md) Phase 2-6
2. Add new exploits in `src/games/hacking_mechanics.py`
3. Add new skills in `src/games/skill_tree.py`
4. Create quests in `src/games/hacking_quests.py`
5. Run tests to verify

---

## Key Metrics

- **Skill Tree:** 15+ skills across 5 tiers
- **Quests:** 15+ templates with multiple chains
- **Factions:** 5 built-in + player-created
- **API Endpoints:** 25+ under `/api/games/`
- **Exploit Types:** 6 (extensible)
- **Components:** Maps to RPG Inventory
- **Traces:** Active countdown alarms
- **Memory Limit:** 32 MB (Hacknet-style)

---

## File Locations

| File | Purpose |
|------|---------|
| `src/games/hacking_mechanics.py` | Core scan/exploit/patch logic |
| `src/games/skill_tree.py` | Progression and tier system |
| `src/games/faction_system.py` | Community and missions |
| `src/games/hacking_quests.py` | Quests and narratives |
| `src/games/demo.py` | Example workflow |
| `src/api/hacking_api.py` | REST endpoints |
| `HACKING_GAME_INTEGRATION_GUIDE.md` | Comprehensive guide |

---

**Status:** ✅ Ready for Testing Chamber  
**Version:** 1.0 (Prototype)  
**Maintainer:** AI Integration Team  
**Last Updated:** 2026-02-04
