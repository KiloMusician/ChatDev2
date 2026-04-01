<![CDATA[# NuSyQ Front-End Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-13  
**Author:** NuSyQ Development Team

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Individual Server Management](#individual-server-management)
- [Orchestration Scripts](#orchestration-scripts)
- [Health Monitoring](#health-monitoring)
- [Troubleshooting](#troubleshooting)
- [Development Workflow](#development-workflow)
- [Access URLs](#access-urls)

---

## 🏗️ Architecture Overview

The NuSyQ front-end ecosystem consists of three independent but complementary systems:

### 1. **SimulatedVerse** (Port 5000)
- **Technology:** Express.js + TypeScript (tsx runtime)
- **Purpose:** Consciousness simulation engine and Colony Game backend
- **Features:**
  - Consciousness lattice API
  - Quantum enhancement system
  - WebSocket multiplayer
  - ChatDev integration
  - Memory-only mode (no database required)
- **Location:** `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`

### 2. **ChatDev Visualizers** (Port 8000)
- **Technology:** Python HTTP server (static files)
- **Purpose:** Multi-agent AI development visualization
- **Features:**
  - Agent activity dashboard
  - Chain visualization
  - Execution replay
  - Static HTML interface
- **Location:** `C:\Users\keath\NuSyQ\ChatDev\visualizer`

### 3. **NuSyQ-Hub Modular Window** (Port 8080)
- **Technology:** Express.js + vanilla JavaScript
- **Purpose:** Quantum module management interface
- **Features:**
  - 790-line modular window system
  - Dynamic module loading
  - Grid/stack layouts
  - Quantum-themed UI
  - REST API for module state
- **Location:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server`

---

## 💻 System Requirements

### Software Dependencies
- **Node.js:** v18+ (for SimulatedVerse and NuSyQ-Hub Modular Window)
- **Python:** 3.8+ (for ChatDev Visualizers)
- **PowerShell:** 7+ (for orchestration scripts)
- **npm:** Latest version

### Port Requirements
| Port | Service | Protocol |
|------|---------|----------|
| 5000 | SimulatedVerse | HTTP |
| 8000 | ChatDev Visualizers | HTTP |
| 8080 | NuSyQ-Hub Modular Window | HTTP |

**Note:** Ensure these ports are not in use by other applications.

### Disk Space
- SimulatedVerse: ~500MB (including node_modules)
- ChatDev Visualizers: ~50MB (static files)
- NuSyQ-Hub Modular Window: ~200MB (including node_modules)

---

## 🚀 Quick Start

### One-Command Startup

```powershell
# Start all three servers
.\start-all-servers.ps1

# Start in silent mode (background processes)
.\start-all-servers.ps1 -Silent

# Start with health checks
.\start-all-servers.ps1 -WaitForHealth
```

### One-Command Shutdown

```powershell
# Stop all servers (with confirmation)
.\stop-all-servers.ps1

# Force stop without confirmation
.\stop-all-servers.ps1 -Force
```

### Health Check

```powershell
# Check all servers
.\health-check.ps1

# CI mode (exit code indicates health)
.\health-check.ps1 -CI

# JSON output for automation
.\health-check.ps1 -JSON

# Verbose mode with detailed errors
.\health-check.ps1 -Verbose
```

---

## 🔧 Individual Server Management

### SimulatedVerse (Port 5000)

**Start:**
```powershell
cd C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
npm run dev
```

**Stop:**
```powershell
# Find and kill the process
Get-Process -Name "node" | Where-Object {$_.Path -like "*SimulatedVerse*"} | Stop-Process -Force
```

**Environment:**
- Uses `.env` file for configuration
- Runs in memory-only mode (no PostgreSQL required)
- TypeScript files compiled on-the-fly with tsx

**Key Endpoints:**
- `GET /api/health` - Health check
- `GET /api/consciousness` - Consciousness lattice state
- `GET /api/colony/game` - Colony game API

---

### ChatDev Visualizers (Port 8000)

**Start:**
```powershell
cd C:\Users\keath\NuSyQ\ChatDev\visualizer
python -m http.server 8000
```

**Stop:**
```powershell
# Find and kill the Python process
Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*http.server 8000*"} | Stop-Process -Force
```

**Files:**
- `static/index.html` - Main dashboard
- `static/chain_visualizer.html` - Agent chain visualization
- `static/replay.html` - Execution replay

**Key Endpoints:**
- `GET /static/index.html` - Dashboard
- `GET /static/chain_visualizer.html` - Chain viewer
- `GET /static/replay.html` - Replay interface

---

### NuSyQ-Hub Modular Window (Port 8080)

**Start:**
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server
node server.js
```

**Stop:**
```powershell
# Find and kill the process on port 8080
Get-NetTCPConnection -LocalPort 8080 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**Dependencies:**
```json
{
  "express": "^4.18.2",
  "cors": "^2.8.5",
  "body-parser": "^1.20.2"
}
```

**Install Dependencies:**
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server
npm install
```

**Key Endpoints:**
- `GET /` - Main interface
- `GET /api/modules` - Get module state
- `POST /api/modules` - Create/update module

---

## 🎯 Orchestration Scripts

### start-all-servers.ps1

**Purpose:** Launch all three front-end systems in parallel

**Features:**
- Pre-flight checks (directory existence, port availability)
- Parallel server startup
- Optional silent mode (background processes)
- Optional health check wait
- Clear status output

**Parameters:**
- `-Silent` - Run in background without new windows
- `-WaitForHealth` - Wait for health checks before exiting

**Example Usage:**
```powershell
# Interactive mode (default)
.\start-all-servers.ps1

# Background mode
.\start-all-servers.ps1 -Silent

# With health verification
.\start-all-servers.ps1 -WaitForHealth
```

---

### health-check.ps1

**Purpose:** Verify all servers are running and accessible

**Features:**
- Port listening verification
- Process identification
- HTTP endpoint testing
- Response time monitoring
- Overall health status
- JSON output for CI/CD

**Parameters:**
- `-CI` - CI mode (exit code 0=healthy, 1=unhealthy)
- `-JSON` - Output as JSON
- `-Verbose` - Show detailed error messages

**Example Usage:**
```powershell
# Standard health check
.\health-check.ps1

# CI/CD integration
.\health-check.ps1 -CI
if ($LASTEXITCODE -eq 0) { Write-Host "All healthy" }

# JSON for automation
.\health-check.ps1 -JSON | ConvertFrom-Json
```

**Sample Output:**
```
╔════════════════════════════════════════════════════════════════╗
║           🏥 NuSyQ Front-End Health Monitor                   ║
╚════════════════════════════════════════════════════════════════╝

[1/3] SimulatedVerse (Port 5000)
   ✅ Port: LISTENING (node)
   ✅ HTTP: 200 (45ms)

[2/3] ChatDev Visualizers (Port 8000)
   ✅ Port: LISTENING (python)
   ✅ HTTP: 200 (12ms, 3702 bytes)

[3/3] NuSyQ-Hub Modular Window (Port 8080)
   ✅ Port: LISTENING (node)
   ✅ HTTP: 200 (18ms, 6570 bytes)

╔════════════════════════════════════════════════════════════════╗
║                  Overall Status: HEALTHY                       ║
╚════════════════════════════════════════════════════════════════╝
```

---

### stop-all-servers.ps1

**Purpose:** Gracefully stop all front-end servers

**Features:**
- Detection of running servers
- Confirmation prompt (optional)
- Force stop capability
- Verification after shutdown
- Detailed summary

**Parameters:**
- `-Force` - Skip confirmation prompt

**Example Usage:**
```powershell
# With confirmation
.\stop-all-servers.ps1

# Force stop
.\stop-all-servers.ps1 -Force
```

**Sample Output:**
```
╔════════════════════════════════════════════════════════════════╗
║            🛑 NuSyQ Server Shutdown Sequence                  ║
╚════════════════════════════════════════════════════════════════╝

[🔍] Checking for running servers...
   🟢 SimulatedVerse (Port 5000): Running (PID: 12345)
   🟢 ChatDev Visualizers (Port 8000): Running (PID: 12346)
   🟢 NuSyQ-Hub Modular Window (Port 8080): Running (PID: 12347)

[🛑] Stopping servers...
   ✅ SimulatedVerse: Stopped
   ✅ ChatDev Visualizers: Stopped
   ✅ NuSyQ-Hub Modular Window: Stopped

╔════════════════════════════════════════════════════════════════╗
║              ✅ All Servers Stopped Successfully               ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🏥 Health Monitoring

### Manual Health Checks

**Check All Servers:**
```powershell
.\health-check.ps1
```

**Check Individual Ports:**
```powershell
# Check if port is listening
Get-NetTCPConnection -LocalPort 5000,8000,8080 -State Listen

# Check HTTP endpoint
Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing
```

### Automated Monitoring

**PowerShell Loop:**
```powershell
# Monitor every 30 seconds
while ($true) {
    Clear-Host
    .\health-check.ps1
    Start-Sleep -Seconds 30
}
```

**CI/CD Integration:**
```yaml
# GitHub Actions example
- name: Health Check
  run: |
    pwsh -File health-check.ps1 -CI
```

---

## 🔧 Troubleshooting

### Port Already in Use

**Problem:** `Port 5000/8000/8080 is already in use`

**Solution:**
```powershell
# Stop all servers
.\stop-all-servers.ps1 -Force

# Or manually find and kill process
Get-NetTCPConnection -LocalPort 5000 | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force
}
```

---

### Server Not Responding

**Problem:** Health check shows `HTTP: UNREACHABLE`

**Diagnosis:**
```powershell
# Check if port is listening
Get-NetTCPConnection -LocalPort 5000 -State Listen

# Check process is running
Get-Process -Name "node" | Where-Object {$_.Path -like "*SimulatedVerse*"}

# Check logs in server terminal window
```

**Solution:**
1. Stop and restart the specific server
2. Check for errors in the terminal window
3. For routed output, inspect `data/terminal_logs/*.log` or run `python scripts/activate_live_terminal_routing.py --validate`
3. Verify dependencies are installed (`npm install`)
4. Check for firewall blocking the port

---

### Dependencies Missing

**Problem:** `Cannot find module 'express'` or similar

**Solution:**
```powershell
# NuSyQ-Hub Modular Window
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server
npm install

# SimulatedVerse
cd C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
npm install
```

---

### Process Won't Stop

**Problem:** `stop-all-servers.ps1` shows servers still running

**Solution:**
```powershell
# Force kill all node processes
Stop-Process -Name "node" -Force

# Force kill all python processes
Stop-Process -Name "python" -Force

# Or kill by port
$ports = 5000,8000,8080
foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
}
```

---

### Permission Errors

**Problem:** `Access denied` when starting/stopping servers

**Solution:**
```powershell
# Run PowerShell as Administrator
Start-Process pwsh -Verb RunAs

# Or adjust execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 💼 Development Workflow

### Full Development Cycle

```powershell
# 1. Start all servers
.\start-all-servers.ps1 -WaitForHealth

# 2. Develop and test
# - SimulatedVerse: Edit TypeScript files (hot reload enabled)
# - ChatDev: Refresh browser (static files)
# - Modular Window: Refresh browser + restart server

# 3. Monitor health
.\health-check.ps1

# 4. Stop servers when done
.\stop-all-servers.ps1
```

### Focused Development

**Working on SimulatedVerse only:**
```powershell
cd C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
npm run dev
# Server auto-reloads on file changes
```

**Working on Modular Window:**
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server
node server.js
# Restart server after changes
```

**Viewing ChatDev Visualizers:**
```powershell
cd C:\Users\keath\NuSyQ\ChatDev\visualizer
python -m http.server 8000
# Refresh browser after ChatDev runs generate new data
```

---

## 🌐 Access URLs

### Production URLs
| Service | URL | Description |
|---------|-----|-------------|
| **SimulatedVerse** | http://localhost:5000 | Main API endpoint |
| **SimulatedVerse Health** | http://localhost:5000/api/health | Health check |
| **SimulatedVerse Consciousness** | http://localhost:5000/api/consciousness | Consciousness lattice |
| **ChatDev Dashboard** | http://localhost:8000/static/index.html | Main dashboard |
| **ChatDev Chain Visualizer** | http://localhost:8000/static/chain_visualizer.html | Agent chain view |
| **ChatDev Replay** | http://localhost:8000/static/replay.html | Execution replay |
| **Modular Window** | http://localhost:8080 | Main interface |
| **Modular Window API** | http://localhost:8080/api/modules | Module management |

### Testing Endpoints

**SimulatedVerse:**
```powershell
# Health check
curl http://localhost:5000/api/health

# Consciousness state
curl http://localhost:5000/api/consciousness
```

**ChatDev:**
```powershell
# Load dashboard
Start-Process http://localhost:8000/static/index.html
```

**Modular Window:**
```powershell
# Load interface
Start-Process http://localhost:8080

# Get modules (JSON)
curl http://localhost:8080/api/modules
```

---

## 📊 Performance Metrics

### Response Time Benchmarks
| Server | Endpoint | Expected Response Time |
|--------|----------|----------------------|
| SimulatedVerse | `/api/health` | < 50ms |
| SimulatedVerse | `/api/consciousness` | < 200ms |
| ChatDev | `/static/index.html` | < 30ms |
| Modular Window | `/` | < 30ms |
| Modular Window | `/api/modules` | < 20ms |

### Resource Usage (Typical)
| Server | CPU | Memory |
|--------|-----|--------|
| SimulatedVerse | 5-15% | 150-300MB |
| ChatDev | < 1% | 10-20MB |
| Modular Window | < 5% | 50-100MB |

---

## 🔐 Security Considerations

### Development Mode
- All servers run in **development mode** by default
- **CORS is enabled** for all origins in Modular Window
- **No authentication** on any endpoint
- **Not suitable for production** without hardening

### Production Checklist
- [ ] Add authentication middleware
- [ ] Restrict CORS to specific origins
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Implement request validation
- [ ] Enable production logging
- [ ] Remove debug endpoints
- [ ] Set `NODE_ENV=production`

---

## 🆘 Support & Troubleshooting

### Getting Help
1. Check this documentation first
2. Run `.\health-check.ps1 -Verbose` for detailed diagnostics
3. Check individual server terminal windows for errors
4. Review logs in respective server directories

### Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Port conflict | Run `.\stop-all-servers.ps1 -Force` |
| Server won't start | Check dependencies with `npm install` |
| Health check fails | Verify firewall settings |
| Slow response times | Check system resources (CPU, memory) |
| Module loading errors | Clear browser cache |

---

## 📝 Change Log

### Version 1.0.0 (2025-10-13)
- Initial deployment of three-server architecture
- SimulatedVerse Express backend (port 5000)
- ChatDev Python HTTP visualizers (port 8000)
- NuSyQ-Hub Modular Window system (port 8080)
- Complete orchestration script suite
- Health monitoring system
- Comprehensive documentation

---

## 📚 Related Documentation

- [SimulatedVerse README](C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\README.md)
- [ChatDev Integration Guide](C:\Users\keath\NuSyQ\ChatDev\README.md)
- [NuSyQ-Hub Architecture](C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\README.md)
- [Modular Window System Docs](C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular_window_system.js) (inline comments)

---

## 🎓 Training Resources

### For New Developers

1. **Read this guide** (15 minutes)
2. **Run quick start:** `.\start-all-servers.ps1` (5 minutes)
3. **Test each URL** in browser (10 minutes)
4. **Run health check:** `.\health-check.ps1` (2 minutes)
5. **Practice stop/start cycle** (5 minutes)

**Total onboarding time:** ~40 minutes

---

**Built with ΞNuSyQ Framework** | **Version 1.0.0** | **October 2025**
]]>
