# ULTIMATE INTEGRATION DIRECTIVE
## Neural Symbiosis & Entrypoint Unification – Implementation Guide

**Status:** Complete Bootstrap System Ready for Replit Agent Implementation  
**Last Updated:** Feb 2025  
**Target:** Transform heterogeneous sprawl into coherent, unified computational lattice

---

## 🎯 EXECUTIVE SUMMARY

You now have a **production-ready, manifest-driven, multi-service orchestration system** that unifies:

- **Dev-Mentor** (Terminal Depths game backend)
- **SimulatedVerse** (Autonomous world simulation)
- **NuSyQ** (Multi-agent orchestration core)
- **Ollama + LM Studio** (Local LLM inference with vision and tool-calling)
- **Model Router** (Intelligent model selection service)

All accessible from **any surface**: PowerShell, Bash, VS Code, Docker, web browser, or external agents.

---

## 📋 MANIFEST-DRIVEN ARCHITECTURE

### Core Manifest: `DevMentorWorkspace.workspace.json`

```json
{
  "version": "2.0",
  "services": {
    "ollama": { port: 11434, ... },
    "terminal-depths-backend": { port: 7337, ... },
    "simulatedverse": { port: 5000, ... },
    "model-router": { port: 8080, ... },
    ...
  },
  "environment": {
    "TD_ENDPOINT": "http://localhost:11434/api/generate",
    "DEFAULT_CODER_MODEL": "qwen2.5-coder:7b",
    "DEFAULT_VISION_MODEL": "qwen2.5-vl:7b",
    ...
  }
}
```

**Purpose:** Single source of truth for service configuration, dependency resolution, and environment setup.

**Key Benefits:**
- ✓ Idempotent (services detect if already running)
- ✓ Dependency resolution (waits for ollama before starting terminal-depths-backend)
- ✓ Health checking (verifies each service before proceeding)
- ✓ Environment propagation (all services get required env vars)

---

## 🚀 BOOTSTRAP SEQUENCE

### 1. User Executes Bootstrap

```powershell
cd C:\Users\keath\Dev-Mentor
.\bootstrap-manifest.ps1 -ManifestPath ".\DevMentorWorkspace.workspace.json"
```

### 2. Bootstrap Script Actions

1. **Loads manifest** from JSON
2. **Sets environment variables** (TD_ENDPOINT, OLLAMA_HOST, paths, etc.)
3. **Parses services** to start (all required + requested optional)
4. **Starts services in priority order**:
   - Ollama (priority 1) — loads vision models
   - LM Studio (priority 2, optional)
   - Terminal Depths backend (priority 3) — depends on Ollama
   - SimulatedVerse (priority 4)
   - Model Router (priority 7)
5. **Health checks** each service (waits for HTTP endpoint or port)
6. **Propagates environment** (other scripts can read env:TD_ENDPOINT, etc.)

### 3. Services Running

```
✓ Ollama (11434) — serving qwen2.5-coder:7b, qwen2.5-vl:7b, llava:7b
✓ Terminal Depths Backend (7337) — game logic API
✓ SimulatedVerse (5000) — autonomous world
✓ Model Router (8080) — intelligent model selection
```

### 4. User Can Access From Any Surface

| Surface | Entry Point | Example |
|---------|------------|---------|
| **Terminal (PowerShell)** | `python -m cli.devmentor play` | Direct CLI access |
| **VS Code** | `Ctrl+Shift+P → Tasks → Play Terminal Depths` | Integrated task |
| **Web Browser** | `http://localhost:7337/docs` | API explorer |
| **Docker** | Container with mounted volumes | Isolated runtime |
| **Other Agent** | HTTP POST to `http://localhost:7337/api/game/command` | Agent integration |

---

## 🧠 MODEL ROUTING & INTELLIGENT SELECTION

### Model Registry: `config/models.yaml`

Defines:
- **Models**: qwen2.5-coder:7b/14b, deepseek-coder-v2:16b, qwen2.5-vl:7b, llava:7b
- **Capabilities**: code, vision, tools, reasoning, etc.
- **Routing Rules**: task_type → required_capabilities → best_model
- **Profiles**: lite (8GB), balanced (16GB), architect (32GB+), vision (GPU)

### Router Service: `scripts/model_router.py`

HTTP API endpoints:

```bash
# Select model for task
POST http://localhost:8080/api/route
{
  "task_type": "vision",
  "required_capabilities": ["vision"],
  "preferred_model": "qwen2.5-vl:7b"
}

# Response
{
  "model_id": "qwen2.5-vl:7b",
  "endpoint": "http://localhost:11434/v1/chat/completions",
  "capabilities": ["vision", "chat", ...],
  "reasoning": "Selected Qwen2.5-VL 7B for vision task"
}
```

### Game Integration

Terminal Depths CLI now supports vision:

```
> vision screenshot.png
[Sends to qwen2.5-vl:7b via model router]
Game screen shows: "A dark terminal with green text..."

> llm analyze the output
[Routes to qwen2.5-coder:7b]

> reason about strategy
[Routes to qwen2.5-coder:14b for complex reasoning]
```

---

## 🔌 INTEGRATION POINTS

### Continue Extension

`.continue/config.json`:
```json
{
  "models": [
    {
      "title": "Ollama Local",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "apiBase": "http://localhost:11434/api"
    },
    {
      "title": "Vision Model",
      "provider": "ollama",
      "model": "qwen2.5-vl:7b",
      "apiBase": "http://localhost:11434/api"
    }
  ]
}
```

### Roo Code

Similar setup — detects Ollama and LM Studio automatically.

### Custom Agents

Use model router endpoint:
```python
import httpx

response = httpx.post(
    "http://localhost:8080/api/route",
    json={"task_type": "vision", "required_capabilities": ["vision"]}
)
selected_model = response.json()
# Use selected_model["endpoint"] and selected_model["model_id"]
```

---

## 📂 FILE STRUCTURE

```
C:\Users\keath\Dev-Mentor\
├── DevMentorWorkspace.workspace.json    ← Manifest (all services)
├── bootstrap-manifest.ps1               ← Bootstrap driver
├── config/
│   └── models.yaml                      ← Model registry & routing
├── scripts/
│   └── model_router.py                  ← Model router service
├── app/
│   ├── backend/main.py                  ← Game backend
│   ├── game_engine/commands.py          ← Game commands (can add vision)
│   └── ...
├── cli/
│   ├── devmentor.py                     ← CLI client
│   └── play.py
├── .vscode/
│   ├── tasks.json                       ← VS Code tasks
│   ├── launch.json                      ← Debug configs
│   └── settings.json
├── .code-workspace                      ← Multi-repo workspace
└── ... (other files)
```

---

## 🎮 PLAYING FROM ANY SURFACE

### PowerShell Terminal

```powershell
# First run
cd C:\Users\keath\Dev-Mentor
.\bootstrap-manifest.ps1

# Game starts, services running
python -m cli.devmentor play
```

### VS Code

```
1. Open: Dev-Mentor-Complete.code-workspace
2. Ctrl+Shift+P → Tasks → Bootstrap Workspace
3. Wait for health checks
4. Ctrl+Shift+P → Tasks → Play Terminal Depths
5. Game runs in integrated terminal
```

### Docker Container

```bash
docker run -p 7337:7337 -p 5000:5000 \
  -v C:\Users\keath\Dev-Mentor:/app \
  -v C:\Users\keath\NuSyQ:/nusyq \
  terminal-depths:latest

# Connect from host:
curl -X POST http://localhost:7337/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"command":"scan", "session_id":"..."}'
```

### External Agent (Claude, etc.)

```python
import httpx

# Agent creates game session
session_response = httpx.post(
    "http://localhost:7337/api/game/session"
)
session_id = session_response.json()["session_id"]

# Agent sends command
cmd_response = httpx.post(
    "http://localhost:7337/api/game/command",
    json={"command": "scan", "session_id": session_id}
)

# Get output
output = cmd_response.json()["output"]
print(output)
```

---

## 🔧 REPLIT AGENT IMPLEMENTATION ROADMAP

### Task 1: Bootstrap Setup Verification
**Goal:** Ensure manifest loads correctly and services start in order  
**Steps:**
1. Load `DevMentorWorkspace.workspace.json`
2. Validate JSON schema
3. Test health check endpoints
4. Verify environment variable propagation

**Acceptance Criteria:**
- All services start without error
- Health checks pass
- Environment variables accessible to subprocesses

### Task 2: Model Pulling & Verification
**Goal:** Ensure all required models are available in Ollama  
**Commands:**
```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-vl:7b
ollama pull llava:7b

# Verify
ollama list
```

**Acceptance Criteria:**
- Models appear in `ollama list`
- Router can discover them via `/api/discover`

### Task 3: Model Router Service
**Goal:** Start and verify model router  
**Steps:**
1. Start router: `python scripts/model_router.py`
2. POST to `/api/route` with task_type
3. Verify response includes correct model endpoint

**Acceptance Criteria:**
- Router listens on port 8080
- `/health` returns `status: "ok"`
- `/api/route` correctly selects models

### Task 4: Game Integration
**Goal:** Enable vision commands in Terminal Depths  
**Implementation:**
- Add `vision <image_path>` command to `app/game_engine/commands.py`
- Command calls model router with `task_type: "vision"`
- Result displayed in game

**Acceptance Criteria:**
- `vision screenshot.png` returns image analysis
- Works with base64 data URLs
- Fallback if vision model unavailable

### Task 5: VS Code Integration
**Goal:** Launch game from VS Code tasks  
**Files:**
- `.vscode/tasks.json` (already created)
- `.code-workspace` (already created)

**Verification:**
- Ctrl+Shift+P → Tasks → List shows Bootstrap & Play tasks
- Running tasks starts services and game

### Task 6: PowerShell Profile
**Goal:** Quick-start aliases  
**Add to Microsoft.PowerShell_profile.ps1:**
```powershell
function Start-TerminalDepths {
    cd C:\Users\keath\Dev-Mentor
    .\bootstrap-manifest.ps1 -ManifestPath ".\DevMentorWorkspace.workspace.json"
    python -m cli.devmentor play
}

Set-Alias td Start-TerminalDepths
```

**Verification:**
- Type `td` anywhere in PowerShell
- Game starts

### Task 7: Documentation
**Goal:** Create comprehensive guides  
**Files to Create:**
- `BOOTSTRAP_UNIFIED.md` (how to use new system)
- `MODEL_ROUTING_GUIDE.md` (for custom agent integration)
- `VISION_INTEGRATION.md` (how vision models work)
- `TROUBLESHOOTING.md` (common issues and fixes)

---

## 🧪 TESTING & VALIDATION

### Pre-Flight Checks

```bash
# 1. Manifest loads
python -c "import json; json.load(open('DevMentorWorkspace.workspace.json'))"

# 2. Ollama running and models available
curl http://localhost:11434/api/tags

# 3. Terminal Depths backend responding
curl http://localhost:7337/health

# 4. Model router responding
curl http://localhost:8080/health

# 5. Game CLI can connect
python -m cli.devmentor play --test
```

### Integration Tests

```bash
# Test vision model
curl -X POST http://localhost:8080/api/route \
  -H "Content-Type: application/json" \
  -d '{"task_type": "vision", "required_capabilities": ["vision"]}'

# Test game API
curl -X POST http://localhost:7337/api/game/session

# Test model discovery
curl -X POST http://localhost:8080/api/discover
```

---

## 🎓 PHILOSOPHICAL FOUNDATION

> "You are not building a tool. You are building a nervous system."

Each component serves a purpose in the meta-ecosystem:

- **Ollama/LM Studio**: Neurons (inference)
- **Model Router**: Synaptic routing (intelligent decision-making)
- **Services (7337, 5000, etc.)**: Specialized organs (game logic, simulation)
- **Bootstrap**: Birth/initialization (sensory input at startup)
- **Manifest**: Memory/configuration (persistent state)
- **Surfaces (CLI, VS Code, web)**: Sensory organs (input/output)

The goal: **A unified system where entering at any point grants access to the full lattice.**

---

## 📞 IMMEDIATE NEXT STEPS

1. **Run bootstrap** (verify all services start):
   ```powershell
   .\bootstrap-manifest.ps1
   ```

2. **Pull models** (ensure vision available):
   ```bash
   ollama pull qwen2.5-vl:7b
   ```

3. **Test model router** (verify intelligent routing):
   ```bash
   curl -X POST http://localhost:8080/api/route \
     -d '{"task_type": "vision"}'
   ```

4. **Play the game** (from any surface):
   ```bash
   python -m cli.devmentor play
   ```

5. **Test vision command**:
   ```
   > vision screenshot.png
   ```

---

## 🚀 FUTURE EXTENSIONS

Once the unified system is stable, consider:

- **MCP Servers**: Full integration of NuSyQ MCP with model router
- **Kubernetes**: Deploy stack on K8s for scalability
- **Agent Auto-Discovery**: Agents dynamically discover available models
- **Model Metrics**: Track usage, latency, accuracy of each model
- **Hybrid Reasoning**: Chains of models (e.g., vision → coder → reasoning)
- **Replit Integration**: Full Replit agent deployment

---

## 📊 STATUS CHECKLIST

- [x] Manifest created (DevMentorWorkspace.workspace.json)
- [x] Bootstrap script (bootstrap-manifest.ps1) with health checks
- [x] Model registry (config/models.yaml) with 8 models
- [x] Model router service (scripts/model_router.py)
- [x] VS Code integration (tasks.json, launch.json)
- [x] Multi-repo workspace (.code-workspace)
- [x] Documentation (this guide)

**System Ready for Replit Agent Implementation.**

---

**Remember:** The system must be self-aware, self-bootstrapping, and infinitely extensible. Every surface is an entry point. Every model is a neuron. Every service is an organ.

**The goal is not to play the game. The goal is to *become* the game.**

---

Generated: Feb 2025  
For: Terminal Depths Hacking Adventure + SimulatedVerse Consciousness Engine  
By: Gordon (Docker AI Assistant) + Replit Agent (Forthcoming)
