# 🚀 NuSyQ‑Hub Operations Runbook

This runbook provides day‑to‑day start/stop, health, and troubleshooting guidance for the multi‑agent NuSyQ‑Hub ecosystem with intelligent timeouts.

Generated: 2025‑12‑18

## Daily Start

1) Activate environment and run activation (verifies paths, env, quest, docs)

```powershell
# From repo root
python ACTIVATE_SYSTEM.py
```

2) Start local LLMs (if not already running)

```powershell
# Ollama is usually already running; if not, start it
ollama serve
```

3) Bring up full stack in Docker (GPU‑ready Ollama, SimulatedVerse, Redis, Postgres, Quest Dashboard)

```powershell
# Production-like full stack
docker-compose -f deploy/docker-compose.full-stack.yml up --build -d

# Minimal dev stack (if preferred)
docker-compose -f deploy/docker-compose.yml up -d
```

## Health Checks

- Docker status
```powershell
docker-compose -f deploy/docker-compose.full-stack.yml ps
```

- View logs
```powershell
docker-compose -f deploy/docker-compose.full-stack.yml logs -f nusyq-hub
```

- Orchestrator readiness snapshot
```powershell
python -c "from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster as M; import json; print(json.dumps(M().run_readiness_check(), indent=2))"
```

- Ollama models
```powershell
ollama list
```

## Core Endpoints

- NuSyQ‑Hub API: http://localhost:8000
- Ollama: http://localhost:11434
- SimulatedVerse (Express): http://localhost:5002
- React UI: http://localhost:3000
- Quest Dashboard (Streamlit): http://localhost:8501

## Intelligent Timeouts

Use the Intelligent Timeout Manager to prevent premature timeouts for long‑running tasks.

```python
from src.utils.intelligent_timeout_manager import IntelligentTimeoutManager
mgr = IntelligentTimeoutManager()

# Example: complex ChatDev task with high priority
adaptive = mgr.get_timeout("chatdev", complexity=2.0, priority="high")
print(adaptive)

# Record actual duration so the system learns over time
mgr.record_performance("chatdev", actual_seconds=1500)
```

Guidelines:
- Complexity: 0.5 (trivial), 1.0 (normal), 1.5 (moderate), 2.0 (high)
- Priority: low (0.7×), normal (1.0×), high (1.5×), critical (2.0×)
- Persistence: `.cache/timeout_config.json`

## Quest‑Based Development

```powershell
# Validate quest log and ZETA mapping
python -m src.tools.quest_log_validator

# Use quest manager (if available)
python -m src.Rosetta_Quest_System.quest_manager list
```

Artifacts:
- Log: `src/Rosetta_Quest_System/quest_log.jsonl`
- ZETA tracker: `config/ZETA_PROGRESS_TRACKER.json`

## Multi‑Agent Development (ChatDev)

```powershell
python -m src.orchestration.chatdev_development_orchestrator `
  --project "MyWebApp" `
  --description "Build a Flask REST API with JWT" `
  --complexity high
```

- Complexity engages adaptive timeouts (e.g., 600s base × 2.0 = 1200s+)
- Env: ensure `CHATDEV_PATH` is set to your ChatDev installation

## Game / Web Development

- SimulatedVerse dual stack (Express + React) is provided in Docker full‑stack
- Dev commands (non‑Docker) are in the SimulatedVerse repo (`npm run dev`), but prefer Docker here for uniformity

## Troubleshooting

1) Port in use (e.g., 11434 already in use)
- It usually means Ollama is already running → proceed
- To locate process: `Get-NetTCPConnection -LocalPort 11434 | Format-List`

2) Missing environment vars in shell
- The activation script reads `.env`; if a shell still warns, export or re‑run activation
- Required keys: `CHATDEV_PATH`, `OLLAMA_HOST`, `OLLAMA_PORT`

3) Quest System import error
- Activation now attempts multiple variants (`quest_manager`, `quest_engine`) and falls back to file presence
- Ensure `src/Rosetta_Quest_System/quest_engine.py` exists

4) ChatDev path invalid
- Update `.env`: `CHATDEV_PATH=C:\Users\<you>\NuSyQ\ChatDev`

5) Adaptive timeouts seem too short/long
- Increase `complexity` or `priority`
- Let the system learn by recording `actual_seconds`
- Inspect/update `.cache/timeout_config.json`

6) Full test suite
```powershell
python -m pytest -q
```

## Stop & Cleanup

```powershell
# Stop containers
docker-compose -f deploy/docker-compose.full-stack.yml down

# Optional: remove volumes (destructive!)
docker volume prune
```

## Reference Docs

- Agent Instructions: `docs/AI_AGENT_INSTRUCTIONS.md`
- Quick Reference: `AI_AGENT_QUICK_REFERENCE.md`
- System Manifest: `docs/SYSTEM_MANIFEST.json`
- Activation Report: `SYSTEM_ACTIVATION_SUCCESS.md`
