# NuSyQ Front-End Quick Start Guide

## 🚀 Start Everything (One Command)

```powershell
.\start-all-servers.ps1
```

## 🏥 Check Health

```powershell
.\health-check.ps1
```

## 🛑 Stop Everything

```powershell
.\stop-all-servers.ps1
```

---

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| **SimulatedVerse** | http://localhost:5000 |
| **ChatDev Visualizers** | http://localhost:8000/static/index.html |
| **Modular Window** | http://localhost:8080 |

---

## 📊 What's Running?

### SimulatedVerse (Port 5000)
- Consciousness API & Colony Game
- Express + TypeScript backend
- No database required

### ChatDev Visualizers (Port 8000)
- Agent monitoring dashboard
- Python HTTP server (static files)
- View agent chains and replay

### NuSyQ-Hub Modular Window (Port 8080)
- Quantum module interface
- Express + JavaScript
- 790-line modular system

---

## 🔧 Common Tasks

### Start in Background
```powershell
.\start-all-servers.ps1 -Silent
```

### Health Check (CI Mode)
```powershell
.\health-check.ps1 -CI
```

### Force Stop (No Confirmation)
```powershell
.\stop-all-servers.ps1 -Force
```

### JSON Health Output
```powershell
.\health-check.ps1 -JSON
```

---

## ❌ Troubleshooting

### Port Already in Use
```powershell
.\stop-all-servers.ps1 -Force
```

### Server Not Responding
Check individual terminal windows for errors, then restart that specific server.

### Terminal Logs
Terminal routing writes JSON logs to `data/terminal_logs/*.log`. Use
`python scripts/activate_live_terminal_routing.py --validate` to verify that
watcher scripts and VS Code tasks are aligned.

### Dependencies Missing
```powershell
# Modular Window
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\web\modular-window-server
npm install

# SimulatedVerse
cd C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
npm install
```

---

## 📚 Full Documentation

See **[FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)** for complete guide.

---

**Quick Reference v1.0.0** | Built with ΞNuSyQ Framework
