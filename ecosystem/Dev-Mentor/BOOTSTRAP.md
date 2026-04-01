# Terminal Depths + Dev-Mentor + SimulatedVerse
## Local Multi-Repo Bootstrap System

A surgical, modular entrypoint system for running the Terminal Depths hacking adventure game with local LLM models (Ollama/LM Studio), integrated agent orchestration (NuSyQ MCP), and multi-surface access (Terminal, VS Code, web UI, Docker).

---

## ⚙️ Step 0: Keeper Preflight (Always Run First)

Before starting any heavy Docker/Ollama/ChatDev workflow, check machine pressure:

```powershell
# Quick preflight — score + advisor (takes ~2s)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\keeper.ps1 score
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\keeper.ps1 advisor

# Full snapshot if you need disk/game/brain context
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\tools\keeper-bridge.ps1 snapshot
```

**Decision:**
- Score < 60 + advisor = "none" → proceed to bootstrap
- Score ≥ 80 (critical) → run `keeper optimize` or `keeper maintain` first, then retry

> Keeper is wired as the `katana-keeper` MCP server in `.vscode/mcp.json`.
> Any MCP-connected AI (Claude Code, Copilot, Gordon) can call `keeper_snapshot` directly.

---

## 🎯 Quick Start

### Option 1: Full System (Recommended for first run)
```powershell
# PowerShell
cd C:\Users\keath\Dev-Mentor
.\bootstrap.ps1 -Mode full -Profile balanced
```

Or on Linux/macOS/WSL:
```bash
cd ~/Dev-Mentor
bash bootstrap.sh full balanced
```

Or using Makefile (any OS):
```bash
cd ~/Dev-Mentor
make bootstrap
```

### Option 2: Services Only (then attach CLI separately)
```powershell
.\bootstrap.ps1 -Mode dev
# In another terminal:
.\bootstrap.ps1 -Mode cli
```

### Option 3: Docker Compose Directly
```bash
docker compose -f docker-compose.yml up -d
# Logs:
docker compose -f docker-compose.yml logs -f
# Shutdown:
docker compose -f docker-compose.yml down
```

---

## 📁 Architecture

### Repositories Integrated
```
C:\Users\keath\Dev-Mentor\   ← Terminal Depths backend + MCP surface (Python/FastAPI)
C:\prime_anchor\
├── NuSyQ-Hub\               ← Orchestration & diagnostics brain (Python)
├── SimulatedVerse\          ← Consciousness simulation + agent UX (Node/TypeScript)
└── NuSyQ\                   ← Multi-agent environment + ChatDev (Python)
C:\CONCEPT\                  ← Machine-health oracle / katana-keeper (PowerShell)
```

**Ecosystem roles:**
- **Dev-Mentor / TerminalDepths** — interactive agent/game/tool surface
- **NuSyQ-Hub** — decides, routes, heals
- **SimulatedVerse** — simulates, hosts agent UX, patch-bay
- **CONCEPT** — governs machine reality (pressure, disk, modes, diagnostics)

### Service Stack (Docker Compose)
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **ollama** | ollama/ollama:latest | 11434 | Local LLM inference (qwen2.5-coder, qwen2.5-vl) |
| **dev-mentor** | Dev-Mentor:latest | 7337 | Terminal Depths backend (FastAPI) |
| **simulatedverse** | SimulatedVerse:latest | 5000 | Autonomous world engine (Node.js) |
| **nusyq-mcp** | NuSyQ:latest | 8765 | MCP server for tools/resources |

---

## 🎮 Usage Modes

### **FULL** — Complete System
```powershell
.\bootstrap.ps1 -Mode full -Profile balanced
```
- ✓ Starts Docker services (Ollama, Dev-Mentor, SimulatedVerse, NuSyQ)
- ✓ Waits for health checks
- ✓ Launches Terminal Depths CLI client
- ✓ Ready to play immediately

**Best for:** Getting started, playing the game, testing the whole stack.

---

### **DEV** — Services Only
```powershell
.\bootstrap.ps1 -Mode dev
```
- ✓ Starts all Docker services
- ✗ Does NOT launch CLI
- Useful for: Attaching VS Code debugger, running tests, or launching CLI separately

**Then in a new terminal:**
```powershell
.\bootstrap.ps1 -Mode cli
```

---

### **CLI** — Client Only
```powershell
.\bootstrap.ps1 -Mode cli
```
- ✓ Launches Terminal Depths CLI
- Requires: Services already running (use `-Mode dev` first)

**Best for:** Reattaching to game after disconnect, or running multiple CLI sessions.

---

### **STOP** — Shutdown
```powershell
.\bootstrap.ps1 -Mode stop
```
- ✓ Shuts down all Docker services
- ✓ Preserves volumes (sessions/state persist)

---

## 🎯 Profiles

Control which models/services start based on your hardware:

| Profile | Models | Use Case |
|---------|--------|----------|
| **lite** | qwen2.5-coder:1.5b, qwen2.5-vl:2b | Low-end laptops (8GB RAM) |
| **balanced** (default) | qwen2.5-coder:7b, qwen2.5-vl:7b | Standard dev machine (16GB RAM) |
| **architect** | qwen2.5-coder:14b, deepseek-coder-v2:16b | Workstations (32GB+ RAM) |
| **vision** | Large coder + qwen2.5-vl:7b + llava:13b | Multi-modal reasoning |

### Set Profile
```powershell
.\bootstrap.ps1 -Mode full -Profile architect
```

---

## 🔧 Advanced: Local LM Studio Integration

If you're using **LM Studio** instead of (or alongside) Ollama:

### 1. Start LM Studio Manually
```
LM Studio → Open model → Select qwen2.5-coder:7b → Start the OpenAI-compatible server on port 1234
```

### 2. Tell Terminal Depths to use it
```powershell
$env:LM_STUDIO_PORT = 1234
$env:TD_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
.\bootstrap.ps1 -Mode full -SkipDocker
```

Or edit `docker-compose.yml` and uncomment:
```yaml
environment:
  TD_ENDPOINT: "http://host.docker.internal:1234/v1/chat/completions"
```

Notes:
- `127.0.0.1:1234` is the current canonical Windows-local LM Studio endpoint in this ecosystem.
- If you are checking from WSL and the bridge path is inconsistent, verify Windows localhost first before treating LM Studio as down.

---

## 📊 Monitoring & Logs

### Docker Service Status
```powershell
# Current status
docker compose ps

# Tail logs
docker compose logs -f --tail=50

# Logs for specific service
docker compose logs -f dev-mentor
docker compose logs -f ollama
docker compose logs -f simulatedverse
```

### System Health Check (Makefile)
```bash
make doctor
```

Output:
```
Terminal Depths System Diagnostics
====================================

🔍 Environment:
✓ Docker installed
✓ Docker Compose installed
✓ Python installed (Python 3.11.x)
✓ Node.js installed (v20.x)

🌐 Ports:
✓ Dev-Mentor (7337)
✓ SimulatedVerse (5000)
✓ Ollama (11434)

📦 Images:
  Built images: 4
```

---

## 🎮 VS Code Integration

### Open Workspace
```powershell
# This loads all 4 repos into a single workspace
code Dev-Mentor-Complete.code-workspace
```

### Run Bootstrap from Command Palette
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Select:
   - `🚀 Bootstrap: Full (Services + CLI)`
   - `🎮 Bootstrap: Services Only`
   - `💻 Bootstrap: CLI Client`
   - `🛑 Shutdown`

### Debug Dev-Mentor Backend
1. `Ctrl+Shift+D` (Run and Debug)
2. Select `📡 Dev-Mentor Backend (FastAPI)`
3. Press F5
4. API docs open at http://localhost:7337/docs

### Debug Terminal Depths CLI
1. Select `🎮 Terminal Depths CLI`
2. Press F5
3. Breakpoints work; step through game logic

### Debug SimulatedVerse
1. Select `🌍 SimulatedVerse Dev Server`
2. Press F5
3. Server runs with hot-reload

---

## 🧪 Testing

### Run All Tests
```bash
make test
# or
make test-python test-node
```

### Run Python Tests (Dev-Mentor)
```bash
python -m pytest tests/ -v --tb=short
# or via VS Code: F5 → "🧪 Python Tests"
```

### Run Node Tests (SimulatedVerse)
```bash
cd SimulatedVerse
npm run test
# or via VS Code: F5 → "🧪 Node Tests"
```

---

## 🔗 Web Interfaces

Once the system is running:

| URL | Service | Purpose |
|-----|---------|---------|
| http://localhost:7337 | Dev-Mentor | API server health |
| http://localhost:7337/docs | Dev-Mentor | FastAPI interactive docs (try endpoints) |
| http://localhost:5000 | SimulatedVerse | Autonomous world web UI |
| http://localhost:11434 | Ollama | Model server (management) |

### Open in Browser from Terminal
```powershell
make open-api   # Opens Dev-Mentor API docs
make open-ui    # Opens SimulatedVerse UI
```

---

## 📝 Common Commands

### Using Makefile (any OS)
```bash
# Lifecycle
make bootstrap          # Full startup
make dev                # Services only
make cli                # CLI client
make stop               # Shutdown
make restart            # Restart all

# Diagnostics
make status             # Service status
make logs               # Tail Docker logs
make doctor             # System health

# Development
make test               # Run all tests
make lint               # Lint code
make format             # Format code
make build              # Rebuild Docker images
make clean              # Clean artifacts
make rebuild            # Clean + build
make prune              # Docker system prune (aggressive)

# Shortcuts
make open-api           # Open API docs
make open-ui            # Open SimulatedVerse UI
```

### Using Bootstrap Scripts (PowerShell / Bash)

**PowerShell:**
```powershell
.\bootstrap.ps1 -Mode full -Profile balanced     # Full system
.\bootstrap.ps1 -Mode dev                        # Services only
.\bootstrap.ps1 -Mode cli                        # CLI client
.\bootstrap.ps1 -Mode stop                       # Shutdown
.\bootstrap.ps1 -Mode full -NoWait               # No health check wait
```

**Bash:**
```bash
bash bootstrap.sh full balanced     # Full system
bash bootstrap.sh dev               # Services only
bash bootstrap.sh cli               # CLI client
bash bootstrap.sh stop              # Shutdown
```

---

## 🐛 Troubleshooting

### "Docker not running"
**Error:** `Docker: not running (start Docker Desktop)`

**Fix:**
1. Start Docker Desktop (Windows/macOS) or Docker daemon (Linux)
2. Verify: `docker info`
3. Retry: `bootstrap.ps1 -Mode full`

---

### "Port 7337 already in use"
**Error:** `bind: address already in use`

**Fix:**
```powershell
# Find what's using the port
netstat -ano | findstr :7337

# Kill the process
taskkill /PID <PID> /F

# Or use a different port (edit docker-compose.yml)
# "7338:7337" instead of "7337:7337"
```

---

### "Ollama models not downloaded"
**Symptoms:** Terminal Depths responds slowly, or says "model not found"

**Fix:**
```powershell
# Pull models into Ollama
docker compose exec ollama ollama pull qwen2.5-coder:7b
docker compose exec ollama ollama pull qwen2.5-vl:7b

# Check what's installed
docker compose exec ollama ollama list
```

---

### "Python virtual environment issues"
**Symptoms:** `ModuleNotFoundError` when running CLI

**Fix:**
```powershell
# Recreate venv
rm -r venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .

# Or use bootstrap with -NoWait to skip service wait
.\bootstrap.ps1 -Mode full -NoWait
```

---

### "SimulatedVerse build failed"
**Error:** `npm ERR! ...`

**Fix:**
```bash
cd SimulatedVerse
rm -rf node_modules package-lock.json
npm install
npm run build
```

Or rebuild Docker image:
```bash
docker compose build --no-cache simulatedverse
```

---

## 🚀 Production Deployment

This bootstrap system is designed for **local development**. For production:

1. **Reverse Proxy:** Use nginx/Caddy to expose Dev-Mentor + SimulatedVerse
2. **Persistence:** Mount volumes to external storage (not `./volumes/`)
3. **Auth:** Add authentication layer in front
4. **Scaling:** Use Docker Swarm or Kubernetes
5. **Models:** Host Ollama on a separate GPU machine

See `DEPLOYMENT.md` for details.

---

## 📚 Additional Resources

| File | Purpose |
|------|---------|
| `.code-workspace` | VS Code multi-repo workspace config |
| `.vscode/tasks.json` | VS Code task definitions |
| `.vscode/launch.json` | VS Code debug configurations |
| `Makefile` | Cross-platform task automation |
| `docker-compose.yml` | Service orchestration |
| `Dockerfile` (Dev-Mentor) | Backend image build |
| `bootstrap.ps1` | PowerShell bootstrap script |
| `bootstrap.sh` | Bash bootstrap script |
| `pyproject.toml` | Python project metadata |
| `package.json` | Node.js dependencies |

---

## 🎓 Learning Path

1. **First Run:** `make bootstrap` → Play the game
2. **Explore:** Open http://localhost:7337/docs → Try API endpoints
3. **Modify:** Edit `app/backend/main.py` → See changes live (hot-reload)
4. **Debug:** Open VS Code → F5 → Set breakpoints
5. **Extend:** Add custom commands in `app/game_engine/commands.py`
6. **Deploy:** Use `docker compose` for production

---

## 🤝 Contributing

1. Fork repositories (Dev-Mentor, SimulatedVerse, NuSyQ)
2. Create feature branch
3. Run tests: `make test`
4. Lint code: `make lint && make format`
5. Commit with: `git commit -m "feat: your feature"`
6. Push to GitHub → Create PR

---

## 📞 Support

- **Docker issues:** `docker logs <container_name>`
- **Python issues:** `python -m pytest tests/ -v`
- **Node issues:** `npm run lint:errors`
- **System diagnostics:** `make doctor`

---

**Last Updated:** 2024
**Status:** Production-Ready (Local Dev)
