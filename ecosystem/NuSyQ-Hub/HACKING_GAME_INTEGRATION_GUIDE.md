"""Hacking Game Integration Guide — How to wire Bitburner/Hacknet mechanics into NuSyQ-Hub.

This document explains:
1. Architecture overview
2. Integration points with existing systems
3. API endpoints and usage examples
4. Extending the system with new mechanics
5. Culture Ship narrative generation
6. Smart search integration

Date: 2026-02-04
"""

# Table of Contents
# =================
# 1. Architecture Overview
# 2. Core Systems
# 3. API Integration
# 4. Quest & Progression Integration
# 5. Culture Ship Narratives
# 6. Smart Search Integration
# 7. Faction System
# 8. Usage Examples
# 9. Extension Points
# 10. Testing the System

## 1. Architecture Overview

The Bitburner/Hacknet integration adds a gamified hacking system to NuSyQ-Hub,
built on top of the existing RPG Inventory system. Here's how it fits together:

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI App (main.py)                                  │
├─────────────────────────────────────────────────────────┤
│  Existing Routes: /api/health, /api/quests, /api/ops    │
│  NEW: /api/games/  ← Hacking game routes                │
└─────────────────────────────────────────────────────────┘
         │
         ├─ HackingController (scanning, exploiting, traces)
         ├─ SkillTree (progression, tier unlocks)
         ├─ FactionSystem (missions, reputation, community)
         └─ QuestTemplates (hacking mission templates)
         │
         ├─ RPG Inventory (components, skills, metrics)
         ├─ Smart Search (discovery, hints)
         ├─ Culture Ship (narrative generation)
         └─ Quest System (Rosetta Quest System)
```

### Core Design Principles

1. **Built on existing systems**: Extends RPGInventorySystem, doesn't replace it
2. **Token-efficient**: Game mechanics use lightweight operations
3. **Async-ready**: All core operations support async/await
4. **Progression-tied**: Skill unlocks gate access to advanced features
5. **Narrative-rich**: Culture Ship generates lore for major milestones
6. **Community-enabled**: Factions and shared missions promote collaboration

## 2. Core Systems

### 2.1 HackingController (`src/games/hacking_mechanics.py`)

Manages the core hacking gameplay loop:
- **scan(component)** → Discover ports, services, vulnerabilities
- **connect(component)** → Establish initial access
- **exploit(component, exploit_type)** → Execute exploits, gain privileges
- **patch(component)** → Harden security (requires admin access)
- **check_traces()** → Monitor active alerts/traces

**Key Features:**
- Port enumeration and vulnerability discovery
- Trace/alarm system (Hacknet-style timer)
- Access level tracking (guest, user, admin, root)
- Memory constraints (simulates Hacknet resource limits)

**Example:**
```python
from src.games import get_hacking_controller, ExploitType

controller = get_hacking_controller()

# Scan to discover vulnerabilities
scan_result = await controller.scan("python")
print(f"Found {len(scan_result.vulnerabilities)} vulnerabilities")

# Connect (requires open SSH port)
await controller.connect("python")

# Execute exploit to gain higher access
exploit_result = await controller.exploit("python", ExploitType.SSH_CRACK)
if exploit_result.success:
    print(f"Access level: {exploit_result.access_gained}")

# Patch if you have admin access
await controller.patch("python")
```

### 2.2 SkillTree (`src/games/skill_tree.py`)

Manages progression similar to BitBurner's augmentation tree, but integrated with
Rosetta Stone tiers:

**Tiers:**
- Tier 1: SURVIVAL — Basic scanning, repair, SSH cracking
- Tier 2: AUTOMATION — Script writing, resource optimization, multi-threading
- Tier 3: AI INTEGRATION — AI co-pilots, consciousness bridge, smart search+
- Tier 4: DEFENSE — Trace evasion, firewall bypass, hardening
- Tier 5: SYNTHESIS — Multi-faction control, emergent strategies

**Key Methods:**
- `add_xp(amount)` → Award XP and check for tier advancement
- `unlock_skill(skill_id)` → Unlock a new skill
- `is_skill_available(skill_id)` → Check if usable
- `get_next_milestone()` → Info on next tier/skill unlock

**Example:**
```python
from src.games import get_skill_tree

skill_tree = get_skill_tree()

# Add XP from quest completion
skill_tree.add_xp(50)

# Check next milestone
milestone = skill_tree.get_next_milestone()
print(f"Next tier in {milestone['xp_to_next_tier']} XP")

# Unlock a skill when ready
skill_tree.unlock_skill("trace_evasion")
```

### 2.3 FactionSystem (`src/games/faction_system.py`)

Implements Grey Hack-style persistent multiplayer with factions:

**Built-in Factions:**
- SysAdmins United — Security & infrastructure focus
- Data Collective — Analysis & intelligence
- Explorers Guild — Discovery & mapping
- Architects Circle — Design & systems
- Sentinels — Protection & defense

**Key Methods:**
- `join_faction(agent_id, faction_id)` → Join a faction
- `create_mission(...)` → Faction leader creates missions
- `complete_mission(agent_id, mission_id)` → Award reputation & XP
- `get_leaderboard()` → View faction reputation rankings

**Example:**
```python
from src.games import get_faction_system, MissionType

faction_sys = get_faction_system()

# Join a faction
faction_sys.join_faction("copilot-001", faction_id)

# Check available missions
missions = faction_sys.get_faction_missions(faction_id)

# Complete a mission
result = faction_sys.complete_mission("copilot-001", mission_id)
print(f"Reputation gained: {result['reputation_gained']}")

# View leaderboard
leaderboard = faction_sys.get_leaderboard()
```

### 2.4 Hacking Quests (`src/games/hacking_quests.py`)

Pre-authored quest templates with progression chains:

**Sample Quests:**
- q_scan_python → q_crack_python_ssh → q_patch_python
- q_scan_network → q_infiltrate_ollama
- q_write_background_scan → q_optimize_scripts
- q_ai_code_generation (requires AI copilot skill)
- q_multi_faction_operation (tier 5 synthesis)

**Key Functions:**
- `get_quest_by_id(quest_id)` → Retrieve quest details
- `get_quest_chain(starting_quest_id)` → Get full quest sequence
- `generate_culture_ship_narrative(quest, completion_time)` → Lore narrative
- `list_all_quests()` → Browse all available quests

## 3. API Integration

### 3.1 Register the Router

In your main FastAPI app (e.g., `src/main.py`):

```python
from fastapi import FastAPI
from src.api import hacking_api

app = FastAPI()

# Register the hacking game router
app.include_router(hacking_api.router)
```

This exposes all endpoints under `/api/games/`.

### 3.2 Available Endpoints

**Scanning & Reconnaissance:**
- `POST /api/games/scan` — Scan a component
- `GET /api/games/component/{component_name}` — Cached info

**Exploitation:**
- `POST /api/games/connect` — Connect to component
- `POST /api/games/exploit` — Execute exploit
- `POST /api/games/patch` — Patch vulnerabilities
- `GET /api/games/traces` — View active traces

**Progression:**
- `GET /api/games/skills` — Current skill tree state
- `POST /api/games/unlock-skill` — Unlock a skill
- `POST /api/games/gain-xp` — Award XP

**Factions:**
- `GET /api/games/factions` — List all factions
- `POST /api/games/faction/join` — Join a faction
- `GET /api/games/faction/{id}/missions` — View faction missions
- `POST /api/games/faction/{id}/mission/complete` — Complete mission
- `GET /api/games/leaderboard` — Reputation rankings

**Quests:**
- `GET /api/games/quests` — List quests (optionally filtered by difficulty/tier)
- `GET /api/games/quest/{quest_id}` — Get quest details
- `GET /api/games/quest/{quest_id}/chain` — Get quest sequence
- `POST /api/games/quest/complete` — Mark quest complete, generate narrative

**Status:**
- `GET /api/games/status` — Overall game status

### 3.3 Example API Calls

**Scan a component:**
```bash
curl -X POST http://localhost:8000/api/games/scan \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python"}'
```

**Execute an exploit:**
```bash
curl -X POST http://localhost:8000/api/games/exploit \
  -H "Content-Type: application/json" \
  -d '{
    "component_name": "python",
    "exploit_type": "ssh_crack",
    "xp_reward": 50
  }'
```

**Get current progress:**
```bash
curl http://localhost:8000/api/games/status
```

**List available missions:**
```bash
curl http://localhost:8000/api/games/faction/{faction_id}/missions
```

**Complete a quest:**
```bash
curl -X POST http://localhost:8000/api/games/quest/complete \
  -H "Content-Type: application/json" \
  -d '{
    "quest_id": "q_scan_python",
    "completion_time": 120.5
  }'
```

## 4. Quest & Progression Integration

### 4.1 Linking Quests to Skill Tree

Each quest can unlock a skill when completed:

```python
HackingQuestTemplate(
    id="q_patch_python",
    title="Patch the Python Component",
    ...
    xp_reward=100,
    skill_unlock="component_heal",  # ← Unlocks this skill on completion
)
```

When `/api/games/quest/complete` is called:
1. XP is awarded
2. Skill tree tier is checked for advancement
3. Skill is unlocked if specified
4. Narrative is generated

### 4.2 Rosetta Stone Integration

Quests are tagged with tier information:

```python
quest.narrative_tags = ["reconnaissance", "learning", "tier-1"]
```

This allows filtering quests by current progression tier:

```python
current_tier = 2
tier_2_quests = get_quests_by_tier(current_tier)
```

### 4.3 Linking to Existing Quest System

To integrate with `src/Rosetta_Quest_System/`:

```python
from src.Rosetta_Quest_System import quest_engine
from src.games import get_quest_by_id

# When a player completes a hacking quest
quest = get_quest_by_id("q_scan_python")
narrative = generate_culture_ship_narrative(quest, completion_time)

# Log to quest system
quest_engine.log_completion({
    "quest_id": quest.id,
    "title": quest.title,
    "xp_gained": quest.xp_reward,
    "narrative": narrative,
    "timestamp": datetime.now().isoformat()
})
```

## 5. Culture Ship Narratives

The Culture Ship agent generates lore for completed quests:

```python
from src.games import generate_culture_ship_narrative

quest = get_quest_by_id("q_crack_python_ssh")
narrative = generate_culture_ship_narrative(quest, completion_time=240)

print(narrative)
# Output: "⚡ **ELITE MISSION COMPLETE**: Crack Python SSH..."
```

### Narrative Tiers

- **Tier 1 quests** (difficulty 1): "Reconnaissance" narratives
- **Tier 2 quests** (difficulty 2-3): "Mission complete" narratives
- **Tier 4+ quests** (difficulty 4-5): Epic narratives with time-based bonuses

Integrate with Culture Ship by:

```python
from src.integration.consciousness_bridge import broadcast_narrative

broadcast_narrative({
    "type": "quest_completion",
    "quest_id": quest.id,
    "narrative": narrative,
    "xp": quest.xp_reward,
    "tier": tier,
})
```

## 6. Smart Search Integration

Link hacking mechanics to fl1ght.exe smart search:

```python
from src.search.smart_search import SmartSearch

smart_search = SmartSearch()

# Index hacking quests
smart_search.index_quests(list_all_quests())

# Search with context
results = smart_search.search_contextual(
    query="I want to automate exploitation",
    context={"current_tier": 2, "current_xp": 500}
)
# Returns: quests, skills, and documentation relevant to automation + tier 2
```

## 7. Faction System

### 7.1 Joining Factions

```python
faction_sys.join_faction(agent_id, faction_id)
```

### 7.2 Creating Missions

```python
faction_sys.create_mission(
    faction_id=faction_id,
    title="Scan the Network",
    description="Perform reconnaissance on all components",
    mission_type=MissionType.RECONNAISSANCE,
    target_component="all",
    difficulty=1,
    reputation_reward=100,
    xp_reward=50,
)
```

### 7.3 Completing Missions

```python
result = faction_sys.complete_mission(agent_id, mission_id)
# Returns: reputation gained, XP gained, current faction reputation
```

### 7.4 Leaderboard

```python
leaderboard = faction_sys.get_leaderboard(faction_id)
# Top 20 agents by faction reputation
```

## 8. Usage Examples

### Example 1: Complete a Basic Quest Chain

```python
# Quest: Scan → Crack → Patch
async def complete_quest_chain():
    controller = get_hacking_controller()
    skill_tree = get_skill_tree()

    # Step 1: Scan
    scan_result = await controller.scan("python")
    skill_tree.add_xp(50)

    # Step 2: Exploit
    exploit_result = await controller.exploit("python", ExploitType.SSH_CRACK)
    if exploit_result.success:
        skill_tree.add_xp(75)

    # Step 3: Patch
    success = await controller.patch("python")
    if success:
        skill_tree.unlock_skill("component_heal")
        skill_tree.add_xp(100)

    print(f"New tier: {skill_tree.state.tier.name}")
```

### Example 2: Faction Mission Workflow

```python
# Create and complete a faction mission
faction_sys = get_faction_system()
faction_id = list(faction_sys.factions.keys())[0]

# Create a mission
mission = faction_sys.create_mission(
    faction_id=faction_id,
    title="Security Audit",
    description="Scan and harden all components",
    mission_type=MissionType.DEFENSE,
    target_component="all",
    difficulty=2,
    reputation_reward=200,
    xp_reward=100,
)

# Join faction if not already
faction_sys.join_faction("agent-001", faction_id)

# Complete mission
result = faction_sys.complete_mission("agent-001", mission.id)
print(f"Reputation: {result['new_reputation']}")
```

### Example 3: AI Co-Pilot Quest

```python
# Unlock AI co-pilot and use it to generate exploit code
skill_tree = get_skill_tree()

# Advance to tier 3
while skill_tree.state.tier.value < 3:
    skill_tree.add_xp(1000)

# Unlock AI copilot
skill_tree.unlock_skill("ai_copilot")

# Now can access AI generation via quest
quest = get_quest_by_id("q_ai_code_generation")
print(f"This quest requires: {quest.required_skills}")
```

## 9. Extension Points

### 9.1 Add New Exploits

In `src/games/hacking_mechanics.py`:

```python
class ExploitType(Enum):
    # Add new exploit types
    XSS_INJECTION = "xss_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
```

### 9.2 Add New Skills

In `src/games/skill_tree.py`:

```python
self.skills["new_skill"] = UnlockableSkill(
    id="new_skill",
    name="New Skill Name",
    description="...",
    tier_required=RosettaTier.TIER_3_AI_INTEGRATION,
    xp_cost=200,
    category="new_category",
)
```

### 9.3 Add New Quests

In `src/games/hacking_quests.py`:

```python
HACKING_QUEST_TEMPLATES["q_new_quest"] = HackingQuestTemplate(
    id="q_new_quest",
    title="New Quest",
    ...
)
```

### 9.4 Add New Factions

In `src/games/faction_system.py`:

```python
faction_sys.create_faction(
    name="New Faction",
    alignment=FactionAlignment.NEW_ALIGNMENT,
    description="...",
    founder_agent_id="founder-001",
)
```

## 10. Testing the System

### Unit Tests

```bash
pytest tests/test_hacking_mechanics.py
pytest tests/test_skill_tree.py
pytest tests/test_faction_system.py
```

### Integration Tests

```bash
pytest tests/test_hacking_api.py -v
```

### Manual Testing

```bash
# Start the API server
python src/main.py

# Run example queries (see section 3.3)
curl -X POST http://localhost:8000/api/games/scan ...
```

## Summary

The Bitburner/Hacknet integration adds:
- **Playable hacking mechanics** (scan, exploit, patch)
- **Skill-based progression** (Rosetta Stone tiers)
- **Faction system** (community, missions, reputation)
- **Quest chains** (narrative progression)
- **API endpoints** (full REST integration)
- **Token efficiency** (lightweight operations, AI-assisted generation)

All layers tie into existing NuSyQ-Hub systems: RPG Inventory, Smart Search,
Culture Ship, and the Rosetta Quest System. This creates a self-contained gaming
ecosystem that helps agents learn, collaborate, and improve the underlying system.

---

**Author:** AI Integration Team
**Date:** 2026-02-04
**Status:** Prototype, Ready for Testing Chamber
"""
