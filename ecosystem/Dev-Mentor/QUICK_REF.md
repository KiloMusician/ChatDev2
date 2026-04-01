# 🎮 Terminal Depths — Quick Reference Cheat Sheet

## 🚀 One-Liner Startup

### Windows (PowerShell)
```powershell
cd C:\Users\keath\Dev-Mentor; .\bootstrap.ps1 -Mode full -Profile balanced
```

### Linux/macOS/WSL (Bash)
```bash
cd ~/Dev-Mentor && bash bootstrap.sh full balanced
```

### Docker (Any OS)
```bash
docker compose -f docker-compose.yml up -d
```

### Makefile (Any OS)
```bash
make bootstrap
```

---

## 📍 Entry Points

| Entry | Command | Purpose |
|-------|---------|---------|
| **PowerShell** | `.\bootstrap.ps1 -Mode full` | Windows native |
| **Bash** | `bash bootstrap.sh full` | Linux/macOS/WSL |
| **Makefile** | `make bootstrap` | Any OS |
| **VS Code** | `Ctrl+Shift+P` → `Tasks: Run Task` → `DevMentor: Start/Resume` | Integrated IDE |
| **Docker** | `docker compose up -d` | Direct Docker |
| **Replit** | Run button (auto) | Web-based IDE |

---

## 🎯 Common Modes

```powershell
# Full: services + CLI
.\bootstrap.ps1 -Mode full

# Services only (attach debugger later)
.\bootstrap.ps1 -Mode dev

# CLI only (services already running)
.\bootstrap.ps1 -Mode cli

# Shutdown
.\bootstrap.ps1 -Mode stop
```

---

## 🧠 Profiles (Hardware Optimization)

```powershell
# Low-end laptops (8GB RAM)
.\bootstrap.ps1 -Mode full -Profile lite

# Standard (16GB RAM) — DEFAULT
.\bootstrap.ps1 -Mode full -Profile balanced

# Workstations (32GB+ RAM)
.\bootstrap.ps1 -Mode full -Profile architect

# Multi-modal reasoning (GPU)
.\bootstrap.ps1 -Mode full -Profile vision
```

---

## 🌐 Web Interfaces (After Startup)

| URL | Service | Use |
|-----|---------|-----|
| http://localhost:7337 | Dev-Mentor | API health |
| http://localhost:7337/docs | API Swagger | Try endpoints |
| http://localhost:5002 | SimulatedVerse | Current local minimal runtime |
| http://localhost:4466/chatdev/agents | ChatDev adapter | Agent roster |
| http://127.0.0.1:1234/v1/models | LM Studio | Windows-native model endpoint |
| http://localhost:11434 | Ollama | Model management |

Open from terminal:
```bash
make open-api    # Dev-Mentor docs
make open-ui     # SimulatedVerse UI
```

---

## 📊 Service Status

```bash
# All services
docker compose ps

# Logs (follow)
docker compose logs -f

# Specific service logs
docker compose logs -f dev-mentor
docker compose logs -f ollama
docker compose logs -f simulatedverse

# System diagnostics
make doctor
```

---

## 🧭 VS Code Operator Tasks

Use these before broad rediscovery:

- `DevMentor: Start/Resume`
- `DevMentor: Next Step`
- `DevMentor: Diagnose Environment`
- `DevMentor: Validate Current Challenge`
- `🔍 DevMentor: Boot Status`
- `🔗 DevMentor: Integration Matrix`

---

## 🧪 Testing & Quality

```bash
make test         # All tests
make test-python  # Python only
make test-node    # Node only
make lint         # Lint code
make format       # Auto-format
make lint:fix     # ESLint fix
```

---

## 🔧 Development

```powershell
# Edit code (auto-reloads)
code Dev-Mentor-Complete.code-workspace

# Debug Python backend
F5 → "📡 Dev-Mentor Backend (FastAPI)"

# Debug CLI client
F5 → "🎮 Terminal Depths CLI"

# Debug SimulatedVerse
F5 → "🌍 SimulatedVerse Dev Server"

# Run tests
F5 → "🧪 Python Tests" or "🧪 Node Tests"
```

---

## 🛑 Shutdown & Cleanup

```bash
# Stop services (volumes persist)
make stop

# Stop and remove everything
docker compose down

# Full cleanup (aggressive)
make prune
```

---

## 🐛 Quick Fixes

| Issue | Fix |
|-------|-----|
| "Docker not running" | Start Docker Desktop |
| "Port 7337 already in use" | `make stop` or restart Docker |
| "Python modules missing" | `pip install -e .` in Dev-Mentor |
| "Node modules missing" | `npm install` in SimulatedVerse |
| "Ollama models slow" | `docker compose exec ollama ollama list` |

---

## 📁 Repositories Included

```
Dev-Mentor/              ← Terminal Depths (Python/FastAPI)
SimulatedVerse/          ← Autonomous world (Node/TypeScript)
NuSyQ/                   ← MCP orchestration (Python)
NuSyQ-Hub/               ← Game assets & lore
```

All 4 repos visible in VS Code workspace:
```powershell
code Dev-Mentor-Complete.code-workspace
```

---

## 🎮 In-Game Commands

Once playing:

```
help                     # Show all commands
tutorial                 # Learn game basics
skills                   # View skill progress
inventory                # Show items
hack <target>           # Attempt hack
scan / exploit / exfil  # Network actions
talk <npc> / ask <npc>  # NPC interaction
fs-reset                # Reset filesystem
```

---

## 🚀 Makefile Targets (All)

```bash
make help               # Show all targets
make bootstrap          # Full system
make dev                # Services only
make cli                # CLI only
make stop               # Shutdown
make restart            # Restart
make status             # Service status
make logs               # Tail logs
make doctor             # Health check
make test               # All tests
make lint               # Lint code
make format             # Format code
make build              # Build images
make clean              # Remove artifacts
make rebuild            # Clean + build
make prune              # Docker prune
make open-api           # Open API docs
make open-ui            # Open UI
```

---

## 🎓 Workflow Example

### First Time (10 min)
```powershell
1. cd C:\Users\keath\Dev-Mentor
2. .\bootstrap.ps1 -Mode full -Profile balanced
3. Wait for: "✓ All services healthy"
4. Game launches automatically
5. Type: help
```

### Subsequent Times (5 sec)
```powershell
1. cd C:\Users\keath\Dev-Mentor
2. .\bootstrap.ps1 -Mode cli
3. Game resumes
```

### Development (VS Code)
```
1. code Dev-Mentor-Complete.code-workspace
2. Ctrl+Shift+P → Tasks → Bootstrap: Full
3. Wait for health checks
4. Make changes → Auto-reload
5. F5 to debug
```

---

## 💡 Pro Tips

- **Hot reload:** Edit Python/Node → Changes live (no restart)
- **Multiple clients:** `make cli` in different terminals
- **Attach debugger:** `make dev` → F5 in VS Code
- **Local LM Studio:** Set `LM_STUDIO_PORT=8000` env var
- **Check logs:** `docker compose logs -f dev-mentor`
- **Rebuild:** `docker compose build --no-cache`
- **Health check:** `make doctor`

---

## 📞 Help

- Full guide: `BOOTSTRAP.md`
- Implementation: `IMPLEMENTATION_COMPLETE.md`
- Docker help: `docker compose --help`
- Makefile help: `make help`

---

**Remember:** The system handles everything. Just run `bootstrap.ps1` or `make bootstrap` and play!

---

Last Updated: Feb 2025
