
# 🤖 AI Agent Coordination Instructions - NuSyQ-Hub
**Generated**: 2026-03-18T02:14:54.024015
**Project Root**: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub

## System Configuration

### AI Systems Available

#### Ollama (Local LLMs)
- **Status**: ✅ ENABLED
- **URL**: http://localhost:11434
- **Models Available**: 10
    - gpt-3.5-turbo-16k:latest
  - llama3.1:8b
  - nomic-embed-text:latest
  - phi3.5:latest
  - starcoder2:15b
  - deepseek-coder-v2:16b
  - codellama:7b
  - gemma2:9b
  - qwen2.5-coder:7b
  - qwen2.5-coder:14b

#### ChatDev (Multi-Agent Development)
- **Status**: ✅ ENABLED
- **Path**: C:\Users\keath\NuSyQ\ChatDev
- **Capabilities**: Multi-agent development, project generation, team coordination

#### Docker Deployment
- **Status**: ✅ ENABLED
- **Compose Files**: [WindowsPath('C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/deploy/docker-compose.agents.yml'), WindowsPath('C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/deploy/docker-compose.dev.yml'), WindowsPath('C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/deploy/docker-compose.full-stack.yml'), WindowsPath('C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/deploy/docker-compose.yml')]

## Development Capabilities

### Programming Languages
- Python (coding, testing, debugging, refactoring)
- JavaScript/TypeScript (web dev, React, Node.js)
- PowerShell (automation, scripting)
- GDScript (game development, Godot)

### AI-Powered Development
- **Ollama**: code_generation, code_review, documentation, analysis, chat
- **Chatdev**: multi_agent_development, project_generation, team_coordination, code_review
- **Copilot**: code_completion, chat, inline_suggestions, test_generation

### Quest-Based Development
- **Status**: ✅ ENABLED
- **Quest Log**: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\src\Rosetta_Quest_System\quest_log.jsonl
- **Features**: Task tracking, quest chains, ZETA integration

### Game Development
- Wizard Navigator (RPG system for repository exploration)
- Godot integration (scene generation, AI integration)

### Web Development
- SimulatedVerse: http://127.0.0.1:5002
- React UI: http://127.0.0.1:3000

## Usage Guide for AI Agents

### 1. Development Tasks
```python
from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster

master = AIAgentCoordinationMaster()
status = master.get_system_status()
print(json.dumps(status, indent=2))
```

### 2. Multi-Agent Orchestration
```python
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

orchestrator = UnifiedAIOrchestrator()
orchestrator.register_ai_system(name="ollama", system_type="ollama_local")
result = orchestrator.submit_task(task_type="code_generation", content="...")
```

### 3. Quest-Based Development
```python
from src.Rosetta_Quest_System.quest_manager import QuestManager

qm = QuestManager()
quests = qm.list_quests()
qm.update_quest_status(quest_id, "in_progress")
```

### 4. Docker Deployment
```bash
cd deploy
docker-compose up --build
```

### 5. ChatDev Multi-Agent Development
```bash
python -m src.orchestration.chatdev_development_orchestrator \
    --project "MyProject" \
    --description "Build a web app"
```

## Environment Variables Required

```dotenv
CHATDEV_PATH=C:\Users\keath\NuSyQ\ChatDev
OLLAMA_HOST=http://127.0.0.1
OLLAMA_PORT=11434
```

## Key Integration Points

1. **Unified Orchestrator**: `src/orchestration/unified_ai_orchestrator.py`
2. **ChatDev Development**: `src/orchestration/chatdev_development_orchestrator.py`
3. **Quest System**: `src/Rosetta_Quest_System/`
4. **Docker Deployment**: `deploy/docker-compose.yml`
5. **Service Config**: `src/config/service_config.py`

## Next Steps for Full System Utilization

1. ✅ Verify Ollama models: `ollama list`
2. ✅ Test ChatDev integration: Set CHATDEV_PATH
3. ✅ Run quest system: Check quest_log.jsonl
4. ✅ Deploy with Docker: `docker-compose up`
5. ✅ Coordinate multi-agent tasks via UnifiedAIOrchestrator

---
**System Ready**: All AI agents can now fully utilize NuSyQ-Hub capabilities.
