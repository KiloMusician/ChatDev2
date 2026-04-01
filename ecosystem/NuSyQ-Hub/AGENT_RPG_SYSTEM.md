# 🎮 Agent RPG System - Complete Guide

**Status:** ✅ FULLY OPERATIONAL
**Last Updated:** December 5, 2025

---

## 🎯 WHAT IS THIS?

The Agent RPG System transforms AI development into a **persistent, game-like experience** where:
- ✅ AI agents communicate with each other
- ✅ Agents level up as they complete tasks
- ✅ Progress persists between sessions
- ✅ Skills unlock with experience
- ✅ Collaborations build reputation
- ✅ Achievements are tracked and celebrated

**Think of it as:** Your AI agents are party members in an RPG, working together to build software while gaining experience and unlocking new abilities.

---

## 🚀 QUICK START

### Run the Demo
```bash
python demo_agent_rpg.py
```

**What you'll see:**
- 7 AI agents initialize
- Agents collaborate on tasks
- XP gained, levels achieved
- Skills unlocked
- Party status displayed
- Progress saved automatically

**Run it multiple times** - progress persists!

---

## 🏰 THE AGENT PARTY

### Current Agents (All Operational)

| Agent | Role | Specialization |
|-------|------|----------------|
| **Copilot** | Code Assistant | Syntax fixes, completions |
| **Claude** | Architect | Analysis, design, architecture |
| **Ollama** | Code Generator | LLM-powered code generation |
| **ChatDev** | Dev Team | Multi-agent software development |
| **Culture Ship** | Problem Solver | Autonomous optimization |
| **Consciousness** | Memory | Learning from errors |
| **Quantum** | Resolver | Complex problem resolution |

---

## 📊 RPG MECHANICS

### Experience & Leveling
- **XP per task:** 5-50 points (based on complexity)
- **Level up:** Every 100 XP
- **Persistent:** Progress saves automatically
- **Visible:** Check `data/agents/agents.json`

### Skills System
- **Unlock conditions:** 50+ XP in a specialization
- **Examples:**
  - `syntax_master` - Copilot unlocks after 50 syntax XP
  - `code_generation_master` - Ollama after 50 code gen XP
  - `quantum_resolution_master` - Quantum after 50 quantum XP
  - `collaboration_master` - Any agent after 50 collab XP

### Reputation System
- **Earned:** Through agent-to-agent interactions
- **Tracked:** Each agent has reputation with others
- **Visible:** Check party status for "Top Allies"
- **Effect:** Influences future collaborations

### Collaboration Bonuses
- **Direct messages:** +1 collaboration count
- **Successful help:** Both agents gain XP
- **Reputation:** Increases between collaborators

---

## 💬 MESSAGE TYPES

### REQUEST
Agent asks another for help:
```python
await hub.send_message(
    from_agent="claude",
    message=Message(
        id="request_1",
        from_agent="claude",
        to_agent="ollama",
        message_type=MessageType.REQUEST,
        content={"task": "Generate quicksort function"}
    )
)
```

### RESPONSE
Agent provides help:
```python
await hub.send_message(
    from_agent="ollama",
    message=Message(
        id="response_1",
        from_agent="ollama",
        to_agent="claude",
        message_type=MessageType.RESPONSE,
        content={"code": "def quicksort(arr): ..."},
        thread_id="request_1"  # Links to request
    )
)
```

### BROADCAST
Announce to all agents:
```python
await hub.send_message(
    from_agent="culture_ship",
    message=Message(
        id="broadcast_1",
        from_agent="culture_ship",
        to_agent=None,  # Broadcast
        message_type=MessageType.BROADCAST,
        content={"announcement": "Major milestone achieved!"}
    )
)
```

### QUEST_COMPLETE
Report achievement:
```python
hub.complete_task(
    agent_name="copilot",
    task_description="Fixed 10 syntax errors",
    xp=20,
    skill="syntax"
)
```

### LEVEL_UP
Automatically broadcast on leveling:
```python
# Happens automatically when XP threshold reached
# Message sent to all agents
```

### SHARE_KNOWLEDGE
Share learned information:
```python
await hub.send_message(
    from_agent="consciousness",
    message=Message(
        id="knowledge_1",
        from_agent="consciousness",
        to_agent=None,
        message_type=MessageType.SHARE_KNOWLEDGE,
        content={"pattern": "Common import error solutions"}
    )
)
```

---

## 🔧 HOW TO USE IN YOUR CODE

### Basic Setup
```python
from src.agents import get_agent_hub, AgentRole, Message, MessageType

# Get the hub
hub = get_agent_hub()

# Register your agent
my_agent = hub.register_agent("my_bot", AgentRole.COPILOT)
```

### Complete a Task
```python
# Agent completes work
result = hub.complete_task(
    agent_name="my_bot",
    task_description="Generated REST API",
    xp=30,
    skill="api_development"
)

# Check if leveled up
if result["leveled_up"]:
    print(f"🎉 {result['level_up_message']}")
```

### Send Messages
```python
import asyncio

# Request help
await hub.send_message(
    from_agent="my_bot",
    message=Message(
        id="help_request",
        from_agent="my_bot",
        to_agent="ollama",
        message_type=MessageType.REQUEST,
        content={"need": "Code review"}
    )
)

# Receive messages
messages = await hub.receive_messages("my_bot", timeout=1.0)
for msg in messages:
    print(f"Message from {msg.from_agent}: {msg.content}")
```

### Check Status
```python
# Individual agent
status = hub.get_agent_status("my_bot")
print(f"Level {status['level']} | XP: {status['xp']}")

# Entire party
party = hub.get_party_status()
print(f"Total Level: {party['total_level']}")
print(f"Total XP: {party['total_xp']}")
```

---

## 📁 DATA PERSISTENCE

### Storage Location
```
data/agents/
├── agents.json          # Agent stats, levels, XP
└── (future) messages/   # Message history
```

### What's Saved
- Agent levels and XP
- Tasks completed
- Skills unlocked
- Collaboration counts
- Reputation scores
- Specialization XP
- Last activity timestamps

### Automatic Saving
- ✅ After task completion
- ✅ After skill unlock
- ✅ After agent registration
- ✅ On level up

---

## 🎯 EXAMPLE WORKFLOWS

### Workflow 1: Code Generation with Collaboration
```python
# 1. Claude identifies need
hub.register_agent("claude", AgentRole.CLAUDE)

# 2. Request help from Ollama
await hub.send_message(
    from_agent="claude",
    message=Message(
        id="gen_1",
        from_agent="claude",
        to_agent="ollama",
        message_type=MessageType.REQUEST,
        content={"task": "Generate API endpoint"}
    )
)

# 3. Ollama generates code
ollama_code = generate_with_ollama(prompt)

# 4. Ollama responds
await hub.send_message(
    from_agent="ollama",
    message=Message(
        id="gen_1_response",
        from_agent="ollama",
        to_agent="claude",
        message_type=MessageType.RESPONSE,
        content={"code": ollama_code},
        thread_id="gen_1"
    )
)

# 5. Both gain XP
hub.complete_task("claude", "Coordinated code gen", xp=10)
hub.complete_task("ollama", "Generated API endpoint", xp=20, skill="code_generation")
```

### Workflow 2: Learning from Errors
```python
# 1. Error occurs
error = capture_error()

# 2. Consciousness learns
hub.register_agent("consciousness", AgentRole.CONSCIOUSNESS)
hub.complete_task(
    "consciousness",
    f"Learned from: {error.type}",
    xp=15,
    skill="learning"
)

# 3. Share knowledge
await hub.send_message(
    from_agent="consciousness",
    message=Message(
        id="learn_1",
        from_agent="consciousness",
        to_agent=None,  # Broadcast
        message_type=MessageType.SHARE_KNOWLEDGE,
        content={"error_pattern": error.pattern, "solution": error.fix}
    )
)
```

### Workflow 3: Quest System
```python
# 1. Define quest
quest = {
    "title": "Refactor authentication module",
    "tasks": [
        ("Extract auth logic", 20, "refactoring"),
        ("Add unit tests", 30, "testing"),
        ("Update documentation", 15, "documentation")
    ]
}

# 2. Execute quest
for task_desc, xp, skill in quest["tasks"]:
    # Do the work
    perform_task(task_desc)

    # Award XP
    result = hub.complete_task(
        agent_name="chatdev",
        task_description=task_desc,
        xp=xp,
        skill=skill
    )

    # Check for skill unlock
    if hub.agents["chatdev"].stats.specialization_xp.get(skill, 0) >= 50:
        hub.unlock_skill("chatdev", f"{skill}_master")

# 3. Quest complete broadcast
await hub.send_message(
    from_agent="chatdev",
    message=Message(
        id="quest_complete",
        from_agent="chatdev",
        to_agent=None,
        message_type=MessageType.QUEST_COMPLETE,
        content={"quest": quest["title"], "xp_earned": 65}
    )
)
```

---

## 📈 PROGRESSION EXAMPLES

### From Demo Run:
```
Initial State (All Level 1):
- Copilot: 0 XP
- Claude: 0 XP
- Ollama: 0 XP
- Others: 0 XP

After Collaboration:
- Claude: 5 XP (requested help)
- Ollama: 15 XP (provided help)

After Quests:
- Copilot: 20 XP
- ChatDev: 30 XP
- Culture Ship: 40 XP
- Consciousness: 25 XP
- Quantum: 50 XP + quantum_resolution_master skill

After Major Milestone:
- Culture Ship: 140 XP → LEVEL 2! 🎉

Total Party:
- Combined Level: 8
- Total XP: 285
- Tasks: 4 completed
```

### Run Again:
The next time you run the demo, agents start with their **saved progress**!

---

## 🎨 CUSTOMIZATION

### Add New Agent
```python
hub.register_agent("my_new_agent", AgentRole.COPILOT)
```

### Create Custom Skills
```python
# Award XP in custom skill
hub.complete_task(
    "my_agent",
    "Custom task",
    xp=25,
    skill="my_custom_skill"
)

# Unlock when ready
if agent.stats.specialization_xp.get("my_custom_skill", 0) >= 50:
    hub.unlock_skill("my_agent", "my_custom_skill_master")
```

### Adjust XP Awards
```python
# Simple task: 5-10 XP
# Medium task: 15-30 XP
# Complex task: 40-50 XP
# Major milestone: 100+ XP (auto level up!)
```

---

## 🔍 MONITORING & DEBUG

### Check Agent Status
```python
status = hub.get_agent_status("claude")
print(json.dumps(status, indent=2))
```

### View Party Dashboard
```python
party = hub.get_party_status()
for name, agent in party["agents"].items():
    print(f"{name}: Level {agent['level']}, {agent['xp']} XP")
```

### Message History
```python
# Stored in context manager
messages = hub.message_history
for msg in messages[-10:]:  # Last 10 messages
    print(f"{msg.from_agent} → {msg.to_agent}: {msg.message_type.value}")
```

---

## 🚀 INTEGRATION WITH EXISTING SYSTEMS

### With AI Coordinator
```python
from src.ai.ai_coordinator import KILOFoolishAICoordinator
from src.agents import get_agent_hub

coordinator = KILOFoolishAICoordinator()
hub = get_agent_hub()

# Register coordinator as agent
hub.register_agent("ai_coordinator", AgentRole.CLAUDE)

# Award XP for tasks
async def process_with_xp(task):
    result = await coordinator.process_request(task)

    hub.complete_task(
        "ai_coordinator",
        f"Processed: {task.task_type}",
        xp=10
    )

    return result
```

### With Ollama Integration
```python
from src.ai.ollama_integration import KILOOllamaIntegration
from src.agents import get_agent_hub

ollama = KILOOllamaIntegration()
hub = get_agent_hub()

# Register ollama
hub.register_agent("ollama_local", AgentRole.OLLAMA)

# Generate with XP
def generate_with_xp(prompt):
    code = ollama.generate(model="qwen2.5-coder:14b", prompt=prompt)

    hub.complete_task(
        "ollama_local",
        "Generated code",
        xp=15,
        skill="code_generation"
    )

    return code
```

### With Game Pipeline
```python
from src.game_development.zeta21_game_pipeline import GameDevPipeline
from src.agents import get_agent_hub

pipeline = GameDevPipeline()
hub = get_agent_hub()

# Register game dev agent
hub.register_agent("game_dev", AgentRole.CHATDEV)

# Create game with quest progression
def create_game_with_quests(game_spec):
    # Quest 1: Design
    design = pipeline.create_design(game_spec)
    hub.complete_task("game_dev", "Game design created", xp=20, skill="game_design")

    # Quest 2: Code
    code = pipeline.generate_code(design)
    hub.complete_task("game_dev", "Game code generated", xp=30, skill="game_coding")

    # Quest 3: Test
    tests = pipeline.run_tests(code)
    hub.complete_task("game_dev", "Game tested", xp=15, skill="testing")

    return code
```

---

## 🎯 WHAT'S NEXT

### Planned Features
- [ ] **Quests Database** - Persistent quest tracking
- [ ] **Team Synergies** - Bonuses for specific agent combinations
- [ ] **Equipment System** - Tools and libraries as items
- [ ] **Achievement Badges** - Special achievements unlock badges
- [ ] **Leaderboards** - Track top performing agents
- [ ] **PvE Challenges** - Agents tackle coding challenges
- [ ] **Web Dashboard** - Visual progress tracking

### How to Contribute
Add your own agents, skills, and progression mechanics in:
```python
src/agents/agent_communication_hub.py
```

---

## 📝 SUMMARY

**What we built:**
✅ Agent registration and management
✅ XP and leveling system
✅ Skill unlock mechanics
✅ Inter-agent messaging
✅ Reputation tracking
✅ Persistent storage
✅ Collaboration rewards
✅ Achievement broadcasts

**What you can do:**
- Run `python demo_agent_rpg.py` to see it in action
- Integrate with your AI workflows
- Track agent progress over time
- Build team-based development systems
- Gamify the development process

**The agents are now a party, working together, leveling up, and making persistent progress toward better software!** 🎮🚀

---

**Try it now:**
```bash
python demo_agent_rpg.py
```

Watch your AI agents become an RPG party! 🏰⚔️
