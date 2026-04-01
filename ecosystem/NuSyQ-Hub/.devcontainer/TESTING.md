# Dev Container Testing Guide

## Quick Start

### 1. Rebuild Dev Container

In VS Code:
1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run: `Dev Containers: Rebuild and Reopen in Container`
3. Wait for container to build and post-create script to complete

### 2. Verify Environment

Once inside the container, open a terminal and run:

```bash
# Run comprehensive validation
python scripts/validate_devcontainer.py
```

This will check:
- ✅ Container environment detection
- ✅ All three repository mounts
- ✅ Environment variables
- ✅ Path resolution system
- ✅ Python/npm dependencies
- ✅ Git hooks functionality
- ✅ Ecosystem entry point

### 3. Manual Verification

If you prefer manual checks:

```bash
# Check environment
echo "Hub: $NUSYQ_HUB_ROOT"
echo "NuSyQ: $NUSYQ_ROOT"
echo "SimulatedVerse: $SIMULATEDVERSE_ROOT"
echo "Container: $IN_DEVCONTAINER"

# Verify repositories
ls -la /workspaces/
ls -la /workspaces/NuSyQ-Hub
ls -la /workspaces/NuSyQ
ls -la /workspaces/SimulatedVerse

# Test ecosystem entry point
python scripts/ecosystem_entrypoint.py doctor

# Test path resolution
python -c "from src.system.ecosystem_paths import get_repo_roots; import json; print(json.dumps({k: str(v) for k, v in get_repo_roots().items()}, indent=2))"
```

### 4. Test Services

```bash
# Activate all ecosystem services
python scripts/ecosystem_entrypoint.py activate

# This should start:
# - Ollama (if available on host)
# - MCP Server
# - Culture Ship
# - SimulatedVerse dev server
```

## Expected Results

### ✅ Successful Container Setup

```
🏥 NuSyQ Ecosystem Health Check

📁 Repository Status:
   ✅ hub: /workspaces/NuSyQ-Hub
   ✅ nusyq: /workspaces/NuSyQ
   ✅ simverse: /workspaces/SimulatedVerse

🐍 Python: 3.13.x

🌍 Environment Variables:
   NUSYQ_HUB_ROOT: /workspaces/NuSyQ-Hub
   NUSYQ_ROOT: /workspaces/NuSyQ
   SIMULATEDVERSE_ROOT: /workspaces/SimulatedVerse
   IN_DEVCONTAINER: true
```

### Container vs Host Differences

| Feature | Host | Container |
|---------|------|-----------|
| Python Version | 3.12.x | 3.13.x |
| NuSyQ-Hub Path | `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub` | `/workspaces/NuSyQ-Hub` |
| NuSyQ Path | `C:\Users\keath\NuSyQ` | `/workspaces/NuSyQ` |
| SimulatedVerse Path | `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse` | `/workspaces/SimulatedVerse` |
| Ollama | Local service | Forwarded from host (port 11434) |

## Troubleshooting

### Repository Not Found

**Symptom:**
```
❌ nusyq: /workspaces/NuSyQ (missing)
```

**Cause:** Repository not mounted in container

**Fix:**
1. Check `devcontainer.json` mounts section
2. Verify paths in mounts match your host system:
   ```json
   "source=${localEnv:USERPROFILE}/NuSyQ,target=/workspaces/NuSyQ,..."
   ```
3. Update paths if needed for your system
4. Rebuild container

### Python Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'pydantic'
```

**Cause:** Dependencies not installed during post-create

**Fix:**
```bash
# Manually run dependency installation
cd /workspaces/NuSyQ-Hub
pip install -r requirements.txt
pip install -r dev-requirements.txt

cd /workspaces/NuSyQ
pip install -r requirements.txt

cd /workspaces/SimulatedVerse
npm install
```

### Git Hooks Failing

**Symptom:**
```
❌ Python >= 3.10 not found
```

**Cause:** Hook not detecting container environment

**Fix:**
```bash
# Verify Python version
python --version  # Should show 3.13.x

# Check container detection
echo $IN_DEVCONTAINER  # Should show "true"

# Test hook directly
python .githooks/pre-commit-impl.py
```

### Port Forwarding Issues

**Symptom:** Cannot access services at localhost:3000, localhost:8000, etc.

**Fix:**
1. Check VS Code "Ports" panel (usually at bottom)
2. Verify ports are forwarded:
   - 11434 (Ollama)
   - 3000 (SimulatedVerse)
   - 8000 (MCP Server)
3. Right-click port → "Forward Port" if not listed

## VS Code Workspace Configuration

The dev container uses a multi-root workspace. To leverage this:

1. **Open Multi-Root Workspace:**
   - File → Open Workspace from File
   - Select `NuSyQ-Ecosystem.code-workspace`

2. **Workspace Folders:**
   - 🏠 NuSyQ-Hub (Main)
   - ⚛️ NuSyQ-Root
   - 🌌 SimulatedVerse

3. **Tasks:**
   All VS Code tasks should now resolve workspace folder paths correctly:
   - `${workspaceFolder}` → NuSyQ-Hub
   - `${workspaceFolder:⚛️ NuSyQ-Root}` → NuSyQ
   - `${workspaceFolder:🌌 SimulatedVerse}` → SimulatedVerse

## Testing Checklist

- [ ] Container builds without errors
- [ ] All three repositories mounted at `/workspaces/*`
- [ ] Environment variables set correctly
- [ ] `validate_devcontainer.py` passes all checks
- [ ] `ecosystem_entrypoint.py doctor` succeeds
- [ ] Git hooks work (Python version detection)
- [ ] Python imports work (no ModuleNotFoundError)
- [ ] Node.js and npm available
- [ ] Port forwarding functional
- [ ] VS Code multi-root workspace recognized

## Next Steps After Successful Testing

1. **Enable Continuous Services:**
   ```bash
   # Keep orchestrator running in background
   python scripts/start_multi_ai_orchestrator.py &

   # Keep PU queue processing
   python scripts/pu_queue_runner.py &
   ```

2. **Start Development:**
   ```bash
   # SimulatedVerse frontend
   cd /workspaces/SimulatedVerse
   npm run dev

   # Access at http://localhost:3000
   ```

3. **Run Tests:**
   ```bash
   # Hub tests
   cd /workspaces/NuSyQ-Hub
   pytest

   # NuSyQ tests
   cd /workspaces/NuSyQ
   pytest
   ```

## Support

For issues or questions:
- Check `docs/SESSION_2026-01-23_TRIPARTITE_COMPLETE.md` for session details
- Review `.devcontainer/devcontainer.json` configuration
- Examine `.devcontainer/post-create.sh` logs
- Run `python scripts/ecosystem_entrypoint.py doctor` for diagnostics
