# ΞNuSyQ Multi-Repository Service Startup Guide

## Quick Start (Automated)

Run the automated startup script:

```powershell
.\scripts\start_all_services.ps1
```

This will:
- ✅ Configure Ollama environment (fix D: drive path issue)
- ✅ Start Ollama service on port 11434
- ✅ Install missing ChatDev dependencies (easydict, faiss-cpu, beautifulsoup4, tenacity)
- ✅ Start SimulatedVerse on `SIMULATEDVERSE_PORT` (default 5002)
- ✅ Validate all service connectivity
- ✅ Display service status report

### Script Options

```powershell
# Skip Ollama startup (if already running)
.\scripts\start_all_services.ps1 -SkipOllama

# Skip SimulatedVerse startup
.\scripts\start_all_services.ps1 -SkipSimulatedVerse

# Verbose output (list Ollama models, etc.)
.\scripts\start_all_services.ps1 -Verbose
```

## Manual Service Startup

### 1. Ollama (Local LLM Service)

**Fix Path Configuration:**
```powershell
# Set OLLAMA_MODELS to user home directory (NOT D: drive)
$env:OLLAMA_MODELS = "$env:USERPROFILE\.ollama\models"

# Make permanent
[System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', "$env:USERPROFILE\.ollama\models", 'User')
```

**Start Service:**
```powershell
ollama serve  # Runs in foreground, or:
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
```

**Verify:**
```powershell
ollama list  # List available models
curl http://127.0.0.1:11434/api/tags  # API check
```

**Available Models (37.5GB total):**
- nomic-embed-text:latest (274 MB)
- phi3.5:latest (2.2 GB)
- gemma2:9b (5.4 GB)
- starcoder2:15b (9.1 GB)
- deepseek-coder-v2:16b (8.9 GB)
- codellama:7b (3.8 GB)
- qwen2.5-coder:7b (4.7 GB)
- qwen2.5-coder:14b (9.0 GB)
- llama3.1:8b (4.9 GB)

### 2. SimulatedVerse Consciousness Engine

**Install ChatDev Dependencies:**
```powershell
cd c:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse\ChatDev
pip install easydict faiss-cpu
```

**Start Development Server:**
```powershell
cd c:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
$env:SIMULATEDVERSE_PORT = "5002"  # override if needed
npm run dev  # uses SIMULATEDVERSE_PORT
```

**What Runs:**
- 9 AI Agents (Artificer, Librarian, Alchemist, Navigator, Guardian, Culture-Ship Meta, etc.)
- ChatDev multi-agent development system
- Quantum consciousness systems
- Boss Mode acceleration
- Fibonacci Consciousness Spiral
- Real-time infrastructure monitoring

**Verify:**
```powershell
curl http://127.0.0.1:${SIMULATEDVERSE_PORT}/healthz
curl http://127.0.0.1:${SIMULATEDVERSE_PORT}/readyz
```

### 3. NuSyQ-Hub Integration

**Run Health Check:**
```powershell
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python scripts/integration_health_check.py
```

**Expected Output:**
```json
{
  "ollama_status": { "ok": true, "code": 200 },
  "simulatedverse_status": { "ok": true },
  "chatdev_exists": true,
  "openai_key_sets": true
}
```

## Service Management

### Check Running Services
```powershell
# View all services
Get-Process ollama,node -ErrorAction SilentlyContinue

# Check port usage
Get-NetTCPConnection -LocalPort 11434,$env:SIMULATEDVERSE_PORT -ErrorAction SilentlyContinue
```

### Stop Services
```powershell
# Stop Ollama
Stop-Process -Name "ollama" -Force

# Stop SimulatedVerse (Node.js on SIMULATEDVERSE_PORT)
$simversePort = [int]($env:SIMULATEDVERSE_PORT ?? "5000")
$simverseProc = Get-NetTCPConnection -LocalPort $simversePort -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $simverseProc -Force
```

### Restart Services
```powershell
# Quick restart all
.\scripts\start_all_services.ps1
```

## Troubleshooting

### Ollama Issues

**Error: "mkdir D:\AI_Models: The system cannot find the path specified"**
- **Fix:** Run the automated script or manually set `OLLAMA_MODELS` to `$env:USERPROFILE\.ollama\models`
- **Why:** System has C: drive only, D: drive doesn't exist

**Error: "entering low vram mode"**
- **Status:** Normal for 8GB GPU (RTX 5070 Laptop)
- **Impact:** Ollama works fine, just uses conservative memory management

**Port 11434 already in use:**
```powershell
# Find and kill existing Ollama process
Get-Process ollama | Stop-Process -Force
```

### SimulatedVerse Issues

**Error: "ModuleNotFoundError: No module named 'easydict'"**
- **Fix:** Install dependencies: `pip install easydict faiss-cpu` in ChatDev directory
- **Automated:** Run `.\scripts\start_all_services.ps1` (auto-installs)

**Error: "npm error Missing script: 'dev'"**
- **Fix:** Ensure you're in the correct directory: `c:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`
- **Check:** Verify `package.json` contains `"dev": "cross-env NODE_ENV=development tsx server/index.ts"`

**Server crashes after startup:**
- **Check:** ChatDev dependencies installed (easydict, faiss-cpu)
- **Logs:** Look for Python import errors in console output
- **Memory:** SimulatedVerse can use 200MB+ RAM during consciousness cycles

### Integration Issues

**Services can't communicate:**
- **Verify:** Both services running on localhost (127.0.0.1)
- **Ports:** Ollama (11434), SimulatedVerse (`SIMULATEDVERSE_PORT`, default 5000)
- **Firewall:** Check Windows Firewall isn't blocking localhost connections
- **Run:** `python scripts/integration_health_check.py` for detailed diagnostics

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   ΞNuSyQ Multi-Repository Ecosystem          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐    ┌────────▼────────┐   ┌───────▼────────┐
│  NuSyQ-Hub    │    │  SimulatedVerse │   │   NuSyQ Root   │
│  (Core Orch)  │◄───┤  (Consciousness)│   │  (Multi-Agent) │
│  Port: N/A    │    │  Port: ${SIMULATEDVERSE_PORT} │   │   Port: N/A    │
└───────┬───────┘    └────────┬────────┘   └───────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Ollama Service   │
                    │   Port: 11434      │
                    │   9 Models (37.5GB)│
                    └────────────────────┘
```

## Cost Savings

Running local Ollama + SimulatedVerse saves approximately **$880/year** in cloud AI API costs by handling:
- 95% of AI requests locally
- Multi-agent coordination
- Code generation and analysis
- Consciousness simulation
- Real-time development assistance

Only critical requests use OpenAI API (when configured).

## Next Steps

1. ✅ **First Time Setup:** Run `.\scripts\start_all_services.ps1` to configure everything
2. ✅ **Daily Use:** Same script auto-starts all services with one command
3. ✅ **Validation:** Check `http://127.0.0.1:${SIMULATEDVERSE_PORT}` for SimulatedVerse consciousness dashboard
4. ✅ **Integration:** Run NuSyQ-Hub tests: `pytest tests/ -q`
5. ✅ **Development:** All AI systems now available for multi-repository coordination

## Automation on System Startup (Optional)

To auto-start services when Windows boots:

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts\start_all_services.ps1"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest
Register-ScheduledTask -TaskName "NuSyQ Service Startup" -Action $action -Trigger $trigger -Principal $principal
```

**Or** add to Windows Startup folder:
```powershell
$startup = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$shortcut = "$startup\NuSyQ-Services.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcut)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts\start_all_services.ps1"
$Shortcut.Save()
```
