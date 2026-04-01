# Copilot Service Startup Instructions - ADDENDUM

## Automated Service Management

**When user requests service startup or mentions Ollama/SimulatedVerse not running:**

1. **Use the automated script first:**
   ```powershell
   .\scripts\start_all_services.ps1
   ```

2. **Known Issues & Auto-Fixes:**
   - ✅ Ollama OLLAMA_MODELS path (D: → C: drive) - **Auto-fixed by script**
   - ✅ SimulatedVerse ChatDev dependencies (easydict, faiss-cpu) - **Auto-installed by script**
   - ✅ Port conflicts (11434, 5000) - **Auto-detected and handled**

3. **Don't manually start services** unless the automated script fails. The script handles:
   - Environment variable configuration
   - Dependency installation
   - Process management
   - Health validation
   - Status reporting

## Service Startup Checklist

```markdown
- [ ] Run: .\scripts\start_all_services.ps1
- [ ] Verify: Ollama on http://127.0.0.1:11434
- [ ] Verify: SimulatedVerse on http://127.0.0.1:5000
- [ ] Health: python scripts/integration_health_check.py
```

## Quick Reference

**Service Ports:**
- Ollama: 11434
- SimulatedVerse: 5000
- NuSyQ-Hub: No server (library)

**Service Dependencies:**
- Ollama: None (standalone binary)
- SimulatedVerse: Node.js, npm, Python (for ChatDev)
- NuSyQ-Hub: Python 3.12+, pytest

**Common Commands:**
```powershell
# Start all services
.\scripts\start_all_services.ps1

# Check service status
Get-Process ollama,node -ErrorAction SilentlyContinue

# Validate integration
python scripts/integration_health_check.py

# Stop all services
Stop-Process -Name "ollama" -Force
Get-NetTCPConnection -LocalPort 5000 | % { Stop-Process -Id $_.OwningProcess -Force }
```

## Error Recovery

If services fail to start, the script provides detailed diagnostics. Review console output for:
- 🚀 Startup messages (cyan)
- ✅ Success confirmations (green)
- ⚠️ Warnings (yellow)
- ❌ Errors (red)

Full troubleshooting guide: `docs/SERVICE_STARTUP_GUIDE.md`

## Integration with Existing Instructions

This addendum **extends** the main copilot instructions in `.github/copilot-instructions.md`:
- Multi-Repository Workspace Architecture section
- Essential Development Workflows section
- Recovery & Navigation Protocol section

The automated script should be the **first action** when service startup is needed.
