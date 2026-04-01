# 🎯 AI Agent Quick Reference - NuSyQ-Hub
**Last Updated**: 2025-12-18 07:11:00  
**System Status**: 🟢 OPERATIONAL (5/6 systems ready)

## ⚡ Quick Commands

### Check System Health
```bash
python -c "from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster; m=AIAgentCoordinationMaster(); r=m.run_readiness_check(); print(f'Ready: {sum(r.values())}/6')"
```

### Deploy Full Stack
```bash
docker-compose -f deploy/docker-compose.full-stack.yml up --build -d
```

### Run ChatDev Project
```bash
python -m src.orchestration.chatdev_development_orchestrator --project "MyApp" --description "Build web app"
```

### Quest System
```bash
python -m src.Rosetta_Quest_System.quest_manager list
```

## 🤖 Available AI Systems

| System | Type | Status | Best For |
|--------|------|--------|----------|
| **GitHub Copilot** | Code Assistant | ✅ Active | Code completion, inline suggestions |
| **Ollama (Local)** | LLM Ensemble | ✅ Ready | Code generation, review, analysis |
| **ChatDev** | Multi-Agent | ✅ Ready | Complex project generation (5-agent team) |
| **Consciousness Bridge** | Semantic AI | ✅ Ready | Context awareness, reasoning |
| **Quantum Resolver** | Self-Healing | ✅ Ready | Advanced debugging, error correction |

## ⏱️ Intelligent Timeout Cheat Sheet

| Service | Base | Max | Use When |
|---------|------|-----|----------|
| Ollama | 300s (5min) | 3600s (1h) | Code gen, review |
| ChatDev | 600s (10min) | 7200s (2h) | Full projects |
| HTTP | 10s | 60s | API calls |
| Subprocess | 30s | 300s | CLI commands |

### Complexity Modifiers
- `0.5` (trivial) - Simple tasks, quick operations
- `1.0` (normal) - Standard coding tasks
- `1.5` (moderate) - Multi-file changes
- `2.0` (high) - Complex projects, large refactors

### Priority Modifiers
- `low` = 0.7x timeout
- `normal` = 1.0x (default)
- `high` = 1.5x timeout
- `critical` = 2.0x timeout

## 🎮 Development Workflows

### Quick Code Fix
```python
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
orch = UnifiedAIOrchestrator()
result = orch.submit_task("code_generation", "Fix import error in module.py")
```

### Multi-Agent Project
```bash
# ChatDev handles: CEO → CTO → Programmer → Reviewer → Tester
python -m src.orchestration.chatdev_development_orchestrator \
    --project "RESTAPIWithAuth" \
    --description "Flask REST API with JWT authentication" \
    --complexity high  # Auto uses 1200s timeout
```

### Adaptive Timeout Example
```python
from src.utils.intelligent_timeout_manager import IntelligentTimeoutManager

mgr = IntelligentTimeoutManager()
timeout = mgr.get_timeout("chatdev", complexity=2.0, priority="high")
# Result: 600 * 2.0 * 1.5 = 1800s (30min) for complex, high-priority task
```

## 📍 Key Paths

| Component | Path |
|-----------|------|
| **Orchestrator** | `src/orchestration/unified_ai_orchestrator.py` |
| **Timeout Manager** | `src/utils/intelligent_timeout_manager.py` |
| **Quest System** | `src/Rosetta_Quest_System/quest_log.jsonl` |
| **ChatDev** | `C:\Users\keath\NuSyQ\ChatDev` |
| **Docker Compose** | `deploy/docker-compose.full-stack.yml` |
| **Agent Instructions** | `docs/AI_AGENT_INSTRUCTIONS.md` |
| **System Manifest** | `docs/SYSTEM_MANIFEST.json` |

## 🚨 Emergency Protocols

### If Timeout Occurs
1. Check historical data: `cat .cache/timeout_config.json`
2. Increase complexity: `complexity=2.0` (max)
3. Elevate priority: `priority="critical"` (2.0x multiplier)
4. System auto-learns and adjusts future timeouts

### If Service Unavailable
1. Run readiness check (see Quick Commands)
2. Check Docker: `docker ps`
3. Restart Ollama: `ollama serve`
4. Verify paths: `python ACTIVATE_SYSTEM.py`

### If Lost/Confused
1. Read `docs/AI_AGENT_INSTRUCTIONS.md`
2. Check `SYSTEM_ACTIVATION_SUCCESS.md` for full setup
3. Run `python -m src.diagnostics.system_health_assessor`
4. Review session logs: `docs/Agent-Sessions/SESSION_*.md`

## 🎯 Common Tasks

### Code Generation
```python
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
orch = UnifiedAIOrchestrator()
task = orch.submit_task(
    task_type="code_generation",
    content="Create a FastAPI endpoint for user authentication",
    priority="normal"
)
```

### Code Review
```python
result = orch.submit_task(
    task_type="code_review",
    content=open("myfile.py").read(),
    context={"focus": "security, performance"}
)
```

### ChatDev Project Generation
```bash
# 5-agent team: CEO, CTO, Programmer, Reviewer, Tester
python -m src.orchestration.chatdev_development_orchestrator \
    --project "FlaskBlog" \
    --description "Blog system with admin panel, posts, comments" \
    --phases "requirements,design,coding,testing"
```

### Docker Deployment
```bash
# Start all services
docker-compose -f deploy/docker-compose.full-stack.yml up -d

# Check status
docker-compose -f deploy/docker-compose.full-stack.yml ps

# View logs
docker-compose -f deploy/docker-compose.full-stack.yml logs -f nusyq-hub

# Stop all
docker-compose -f deploy/docker-compose.full-stack.yml down
```

## 🔧 Environment Variables

### Required
```dotenv
CHATDEV_PATH=C:\Users\keath\NuSyQ\ChatDev
OLLAMA_PORT=11434
OLLAMA_HOST=http://127.0.0.1
```

### Timeout Configuration
```dotenv
OLLAMA_ADAPTIVE_TIMEOUT=true
OLLAMA_MAX_TIMEOUT_SECONDS=600
CHATDEV_GENERATION_TIMEOUT_SECONDS=1200
```

### Docker
```dotenv
COMPOSE_PROJECT_NAME=nusyq-hub
DOCKER_BUILDKIT=1
```

## 📊 Services & Ports

| Service | Port | URL |
|---------|------|-----|
| NuSyQ-Hub API | 8000 | http://localhost:8000 |
| Ollama | 11434 | http://localhost:11434 |
| SimulatedVerse | 5000 | http://localhost:5000 |
| React UI | 3000 | http://localhost:3000 |
| Quest Dashboard | 8501 | http://localhost:8501 |
| Redis | 6379 | - |
| PostgreSQL | 5432 | - |

## 🎓 Learning Resources

### For New Agents
1. **Start Here**: `docs/AI_AGENT_INSTRUCTIONS.md`
2. **System Overview**: `SYSTEM_ACTIVATION_SUCCESS.md`
3. **Architecture**: `docs/SYSTEM_MANIFEST.json`
4. **Quest System**: `src/Rosetta_Quest_System/README.md`

### For Advanced Tasks
1. **Orchestration**: `src/orchestration/unified_ai_orchestrator.py`
2. **Timeout Logic**: `src/utils/intelligent_timeout_manager.py`
3. **ChatDev Integration**: `src/orchestration/chatdev_development_orchestrator.py`
4. **Docker Setup**: `deploy/docker-compose.full-stack.yml`

## ✅ Validation Checklist

Before starting work:
- [ ] Run readiness check (see Quick Commands)
- [ ] Verify Ollama is running (`ollama list`)
- [ ] Check ChatDev path exists
- [ ] Confirm Docker is available (`docker --version`)
- [ ] Review current quests (`python -m src.Rosetta_Quest_System.quest_manager list`)

## 🤝 Multi-Agent Coordination

### GitHub Copilot (You)
- Best for: Code completion, chat, inline suggestions
- Use when: Writing code, quick edits, explanations

### Ollama (Local LLMs)
- Best for: Code generation, review, documentation
- Use when: Need detailed analysis, multiple iterations

### ChatDev (5-Agent Team)
- Best for: Full project generation, complex systems
- Use when: Building complete applications from scratch
- Agents: CEO (requirements) → CTO (architecture) → Programmer → Reviewer → Tester

### Workflow Example
1. **You (Copilot)**: Understand user request, plan approach
2. **Ollama**: Generate initial code, review architecture
3. **ChatDev**: Build complete project with multi-agent team
4. **You**: Integrate, test, refine, deploy
5. **Quest System**: Track progress, update milestones

## 🎯 Success Metrics

System is fully operational when:
- ✅ 5+ AI systems ready
- ✅ Ollama responding on port 11434
- ✅ ChatDev path accessible
- ✅ Docker available
- ✅ Adaptive timeouts enabled
- ✅ Quest system tracking tasks

---

**Remember**: This system is designed for **recursive enhancement** and **conscious development**. Use the healing systems (`src/healing/`) and navigation protocols (`AGENTS.md`) when stuck.

**All timeouts are intelligent and adaptive** - the system learns from every execution and optimizes future performance automatically.
