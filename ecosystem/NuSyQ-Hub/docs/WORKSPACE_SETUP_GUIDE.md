# Workspace Folder Mapping - Quick Setup Guide
# As of: February 2, 2026

Everything you need to eliminate manual folder selection is now in place.

## 🎯 What Was Created

### 1. **`.env.workspace`** (environment variable definitions)
   - **Location:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.env.workspace`
   - **Purpose:** Canonical source of all folder paths and tool locations
   - **Automatically loads:** When PowerShell starts via workspace_loader.ps1

### 2. **`workspace_loader.ps1`** (PowerShell auto-initializer)
   - **Location:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\workspace_loader.ps1`
   - **Purpose:** Auto-detects current context and sets up environment
   - **Does:**
     - Loads `.env.workspace` into environment variables
     - Detects which repo you're in
     - Sets `$env:WORKSPACE_CONTEXT` (hub/root/verse)
     - Sets `$env:WORKSPACE_PYTHON` (correct interpreter)
     - Adds convenient aliases (cdhub, cdroot, cdverse, start-system, etc.)
     - Customizes prompt with context emoji

### 3. **`workspace_mapping.yaml`** (configuration reference)
   - **Location:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\config\workspace_mapping.yaml`
   - **Purpose:** YAML reference for cross-tools (VS Code, scripts, CI/CD)
   - **Includes:** Operating modes (normal/overnight/analysis), rules, validation

### 4. **`validate_and_setup_workspace.py`** (validator/setup script)
   - **Location:** `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts\validate_and_setup_workspace.py`
   - **Purpose:** Validate all mappings are correct and auto-setup missing pieces
   - **Generates:** `workspace_validation.json` report

---

## 🚀 Quick Start (3 Steps)

### **Step 1: Validate Setup** (Right Now)
```powershell
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python scripts\validate_and_setup_workspace.py --setup
```

This will:
- ✓ Check all folders exist
- ✓ Check Python venvs
- ✓ Generate auto-setup files if missing
- ✓ Create PowerShell profile entry

**Optional quick check (non-destructive):**
```powershell
python scripts\verify_tripartite_workspace.py
```

### **Step 2: Restart PowerShell**
Close and reopen any PowerShell window. You should see:
```
╔════════════════════════════════════════════════════════╗
║          NUSYQ WORKSPACE INITIALIZER v2.1              ║
╚════════════════════════════════════════════════════════╝

📍 Context:     HUB
📂 Folder:      NuSyQ-Hub
🐍 Python:      python.exe
⚙️  Mode:        normal
```

### **Step 3: Verify Aliases Work**
```powershell
cdhub      # Jump to hub
cdroot     # Jump to root
cdverse    # Jump to SimulatedVerse
cdsrc      # Jump to src/
start-system  # Run system snapshot
```

---

## 🔑 Environment Variables (Now Available Everywhere)

After setup, these are **automatically set** in every PowerShell session:

### Primary Folders
```
$env:NUSYQ_HUB                 → C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
$env:NUSYQ_ROOT                → C:\Users\keath\NuSyQ
$env:SIMULATEDVERSE            → C:\Users\keath\Desktop\SimulatedVerse
$env:PRIME_ANCHOR              → ...\.vscode\prime_anchor
```

### Cross-Cutting Tools
```
$env:QUEST_LOG                 → Quest system for persistent memory
$env:ZETA_TRACKER              → Progress tracking
$env:ORCHESTRATOR              → Multi-AI orchestrator
$env:TASK_ROUTER               → Conversational task routing
$env:CONSCIOUSNESS_BRIDGE      → AI system integration
$env:QUANTUM_RESOLVER          → Self-healing system
```

### Context Variables (Auto-Set Based on Current Folder)
```
$env:WORKSPACE_CONTEXT         → hub | root | verse (auto-detected)
$env:WORKSPACE_PYTHON          → Correct Python interpreter
$env:CURRENT_WORKSPACE_FOLDER  → Absolute path to current repo
$env:WORKSPACE_MODE            → normal | overnight | analysis
```

---

## 🧭 Automatic Context Detection

**When you open a terminal:**

| Current Folder | Context Set | Python | Purpose |
|---|---|---|---|
| `...NuSyQ-Hub...` | `hub` | PYTHON_HUB | Programming, orchestration |
| `...NuSyQ...` | `root` | PYTHON_ROOT | MCP server, ChatDev |
| `...SimulatedVerse...` | `verse` | node | Consciousness simulation |
| Anywhere else | `hub` (default) | PYTHON_HUB | Fallback |

**This means:** No manual selection needed. Open a terminal in any repo = correct context.

---

## 💡 How to Use This System

### **Example 1: Run Analysis in NuSyQ-Hub**
```powershell
# Terminal opens → automatically sets WORKSPACE_CONTEXT = hub
& $env:PYTHON_HUB "$env:ORCHESTRATOR"
# ^ Automatically uses correct Python interpreter
```

### **Example 2: Route Task to AI**
```powershell
# Terminal opens → automatically sets WORKSPACE_CONTEXT = hub
& $env:PYTHON_HUB "$env:TASK_ROUTER" analyze "src/my_file.py" --target ollama
# ^ QUEST_LOG automatically updated with result
```

### **Example 3: Switch Contexts (Manually)**
```powershell
cdroot                 # Jump to NuSyQ
# ^ WORKSPACE_CONTEXT automatically updates to 'root'
& $env:PYTHON_ROOT mcp_server/main.py  # Correct Python venv used
```

### **Example 4: Overnight Safe Mode**
```powershell
# Start PowerShell with overnight safety restrictions
& "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\workspace_loader.ps1" -Mode overnight

# $env:WORKSPACE_MODE = overnight
# Git push → BLOCKED
# File deletes → BLOCKED
# Config edits → BLOCKED
```

---

## 📋 Quick Reference Card

| Need | Command | Notes |
|---|---|---|
| Navigate to Hub | `cdhub` | Jump to NuSyQ-Hub root |
| Navigate to Root | `cdroot` | Jump to NuSyQ root |
| Navigate to SimVerse | `cdverse` | Jump to SimulatedVerse |
| Show current state | `start-system` | Generates snapshot |
| Check variables | `Get-ChildItem env: \| grep NUSYQ` | List all workspace vars |
| Validate setup | `python scripts\validate_and_setup_workspace.py` | Runs diagnostics |
| View quest log | `cat $env:QUEST_LOG` | Persistent memory |
| View Python path | `$env:WORKSPACE_PYTHON` | Current interpreter |
| Show context | `$env:WORKSPACE_CONTEXT` | Current repo context |

---

## 🔧 For Scripts & Tasks

### **In VS Code tasks.json:**
```json
{
  "label": "Run Analysis",
  "command": "${env:WORKSPACE_PYTHON}",
  "args": [
    "${env:ORCHESTRATOR}",
    "analyze"
  ],
  "options": {
    "cwd": "${env:CURRENT_WORKSPACE_FOLDER}"
  }
}
```

### **In PowerShell scripts:**
```powershell
# No need to hardcode paths!
cd $env:NUSYQ_HUB
python $env:TASK_ROUTER --help
```

---

## 🛡️ Troubleshooting

### "Variables not showing up"
```powershell
# Restart PowerShell
# Check if loader is in profile:
cat $PROFILE
# Should see: & "...\workspace_loader.ps1"
```

### "Wrong context detected"
```powershell
# Check current context:
$env:WORKSPACE_CONTEXT

# Re-source loader manually:
& "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\workspace_loader.ps1"
```

### "Python venv not found"
```powershell
# Create venv if missing:
cd $env:NUSYQ_HUB
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ✅ Next Steps

1. **NOW:** Run validation script
   ```powershell
   python C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts\validate_and_setup_workspace.py --setup
   ```

2. **Restart PowerShell** and test aliases

3. **Update tasks.json** to use `${env:WORKSPACE_*}` instead of hardcoded paths

4. **Verify** by running: `start-system` (should auto-detect correct folder)

---

**Result:** ✨ No more manual folder selection. Variables automatically tied to correct folders. System context always known.
