# Rosetta Quest System — Interactive AI "Quest" Engine

Φ.3.0 — Task-Driven Recursive Development Platform

## Overview
- Each task = a quest (with status, metadata, dependencies)
- Each module = a questline (group of related quests)
- Tracks development state in JSON (and optionally CSV)
- CLI and API for quest/questline management
- Integrates with Copilot/context for suggestions and automation
- Designed for AI + User joint planning, long-term projects
- Full logging, tagging, and context propagation

## Features
- Add, update, and complete quests
- Organize quests into questlines (modules)
- Track dependencies, status, and history
- Export/import quests as CSV
- Suggest next quest (AI/heuristic-driven)
- Designed for recursive, modular, and quantum workflows

## Usage
```sh
# Add a new questline
python quest_engine.py add_questline "Core Engine" "Main system engine development" core,engine

# Add a new quest
python quest_engine.py add_quest "Implement PID Guard" "Create idempotent process lock" "Core Engine" "" "startup,guard"

# List all questlines
python quest_engine.py list_questlines

# List all quests in a questline
python quest_engine.py list_quests "Core Engine"

# Update quest status
python quest_engine.py update_quest_status <quest_id> complete

# Export quests to CSV
python quest_engine.py export_csv

# Import quests from CSV
python quest_engine.py import_csv

# Suggest next quest
python quest_engine.py suggest_next_quest
```

## Data Model
- **Quest**: id, title, description, questline, status, created_at, updated_at, dependencies, tags, history
- **Questline**: name, description, tags, quests, created_at, updated_at

## Integration
- Designed for future Copilot/context bridge integration
- All actions logged to `quest_log.jsonl`

## Philosophy
- Recursive, modular, and quantum-inspired task management
- Enables AI + user joint planning and long-term project cultivation


---

## 🔄 Workflow Integration

### **Infrastructure Integration Status**
- **Chatdev Launcher**: ❌ Not Available
- **Testing Chamber**: ❌ Not Available
- **Quantum Automator**: ❌ Not Available
- **Ollama Integrator**: ❌ Not Available
- **Kilo Secrets**: ❌ Not Available

### **Workflow Capabilities**
Rosetta_Quest_System system integration

### **Subprocess Management**
Rosetta_Quest_System process management


### Subprocess Integration Guide

**Standard Rosetta_Quest_System Integration:**
```python
# Import relevant modules
from rosetta_quest_system.rosetta_quest_system_coordinator import Rosetta_Quest_SystemCoordinator

# Initialize coordinator
coordinator = Rosetta_Quest_SystemCoordinator()

# Execute rosetta_quest_system operations
coordinator.execute_operations(parameters)
```


### **Rube Goldbergian Integration**
This directory integrates seamlessly with the modular KILO-FOOLISH workflow:
1. **ChatDev Integration**: Automated development task orchestration
2. **Ollama Bridge**: Local AI model integration with API fallback
3. **Testing Chamber**: Isolated development and testing environments
4. **Quantum Workflows**: Advanced workflow automation and optimization
5. **Consciousness Sync**: Repository awareness and memory integration

---
OmniTag: [quest, task, recursive, planning, context, copilot]
MegaTag: [QUEST_ENGINE, RECURSIVE_DEVELOPMENT, CONTEXT_INTEGRATION]
