# 🚀 NuSyQ-Hub Quick Command Reference

## System Status (30 seconds)
```bash
python scripts/start_nusyq.py brief
```
Shows: Repository status, commits, current quest

---

## Code Quality Actions

### Quick File Analysis
```bash
python scripts/start_nusyq.py analyze
```
Identifies 496 working files, 177 enhancement candidates

### Improve Specific File
```bash
python scripts/start_nusyq.py improve "src/main.py"
```
Returns detailed improvement suggestions

### Quick Patch for Issue
```bash
python scripts/start_nusyq.py patch "src/file.py" "specific issue to fix"
```
Targeted fix suggestions

### Modernize Legacy Code
```bash
python scripts/start_nusyq.py modernize "src/old_code.py"
```
Python pattern improvements

### Full Enhancement (Interactive)
```bash
python scripts/start_nusyq.py enhance "src/directory/"
```
Multi-step interactive enhancement

### Dependency Check
```bash
python scripts/start_nusyq.py update
```
Check for outdated dependencies

---

## ChatDev Multi-Agent Generation

### Generate Simple Project (2-3 minutes)
```bash
cd C:\Users\keath\NuSyQ\ChatDev

python run_ollama.py --task "Create a simple Python calculator" --name "SimpleCalc" --model "qwen2.5-coder:7b"
```

### Generate Complex Project (8-15 minutes)
```bash
python run_ollama.py --task "Create a REST API with SQLAlchemy and JWT auth" --name "RestAPI" --model "qwen2.5-coder:14b"
```

### View Existing Projects
```bash
ls WareHouse/
```
Shows 40+ existing projects for reference

### Access Generated Code
```bash
cd WareHouse/ProjectName_<timestamp>/
# Contains: source code, tests, requirements.txt, README.md
```

---

## System Health & Diagnostics

### Full Health Check
```bash
python scripts/start_nusyq.py doctor
```
Comprehensive system diagnostics

### Autonomous Components Status
```bash
python scripts/autonomous_status.py --verbose
```
Shows 7/7 components health

### Ollama Models Status
```bash
ollama list
```
Lists all available models

### Error Summary
```bash
python scripts/start_nusyq.py error_report
```
Complete diagnostics report

---

## Action Menu & Help

### See All Available Actions
```bash
python scripts/start_nusyq.py menu
```
Shows 11 categories, 65+ actions

### Get Help on Specific Action
```bash
python scripts/start_nusyq.py help improve
python scripts/start_nusyq.py help patch
python scripts/start_nusyq.py help modernize
```

### Show Capabilities Directory
```bash
python scripts/start_nusyq.py capabilities
```
Lists all 919 system capabilities

---

## Autonomous System

### Check Autonomous Status
```bash
python scripts/autonomous_status.py --verbose
```

### Verify Components (7/7)
```bash
# Should show:
# ✅ Autonomous Loop
# ✅ Autonomous Monitor
# ✅ Autonomous Quest Orchestrator
# ✅ Quantum Problem Resolver
# ✅ Multi-AI Orchestrator
# ✅ PU Queue
# ✅ Quest Engine
# 7/7 Components Available ✅
```

---

## Git Integration

### Quick Status
```bash
python scripts/start_nusyq.py brief
```
Shows commits ahead, dirty files

### File History
```bash
git log --oneline src/file.py | head -10
```

### Review Changes
```bash
git diff src/file.py
```

---

## Common Workflows

### Daily Code Quality
```bash
# 1. Check status
python scripts/start_nusyq.py brief

# 2. Identify improvements needed
python scripts/start_nusyq.py analyze

# 3. Pick a file and improve
python scripts/start_nusyq.py improve "src/agents/agent_orchestration_hub.py"

# 4. Review in terminal (look for [ROUTE] hints)
# 5. Commit when ready
git add src/agents/agent_orchestration_hub.py
git commit -m "Improve agent orchestration quality"
```

### ChatDev Feature Development
```bash
# 1. Generate project with ChatDev
cd C:\Users\keath\NuSyQ\ChatDev
python run_ollama.py --task "Your feature description" --name "FeatureName" --model "qwen2.5-coder:7b"

# 2. Find in WareHouse
cd WareHouse/FeatureName_<timestamp>

# 3. Test the generated code
python main.py
pytest

# 4. Integrate into NuSyQ-Hub
cp -r src/* /path/to/NuSyQ-Hub/src/
```

### Quick Error Diagnosis
```bash
# See error
python scripts/start_nusyq.py doctor

# Fix with patch
python scripts/start_nusyq.py patch "affected_file.py" "error message or description"

# Review and apply fix
# Look for 💡 SUGGESTIONS terminal

# Test
python -m pytest
```

---

## Terminal Routing

The system automatically routes outputs to specialized terminals:

| Output Type | Terminal | How to Access |
|---|---|---|
| Fixes & Suggestions | 💡 **SUGGESTIONS** | Look for [ROUTE SUGGESTIONS] 💡 |
| Errors | 🔥 **ERRORS** | Look for [ROUTE ERRORS] 🔥 |
| Tasks | ✅ **TASKS** | Look for [ROUTE TASKS] ✅ |
| Metrics | 📊 **METRICS** | Look for [ROUTE METRICS] 📊 |
| Agents | 🤖 **AGENTS** | Look for [ROUTE AGENTS] 🤖 |

---

## Environment Variables

### Configure Ollama Timeout (default 120s)
```bash
# Increase for very large files
$env:NUSYQ_OLLAMA_TIMEOUT = "180"

# Decrease for quick tasks
$env:NUSYQ_OLLAMA_TIMEOUT = "30"
```

### Set ChatDev Path (usually auto-detected)
```bash
$env:CHATDEV_PATH = "C:\Users\keath\NuSyQ\ChatDev"
```

---

## Useful Aliases (Add to PowerShell Profile)

```powershell
# Add to your PowerShell profile ($PROFILE)

function status { python scripts/start_nusyq.py brief }
function analyze-code { python scripts/start_nusyq.py analyze }
function improve { python scripts/start_nusyq.py improve @args }
function patch { python scripts/start_nusyq.py patch @args }
function health { python scripts/start_nusyq.py doctor }
function menu { python scripts/start_nusyq.py menu }
function chatdev { cd C:\Users\keath\NuSyQ\ChatDev }
function generate-code { python .\run_ollama.py @args }
```

**Usage**:
```bash
status              # Quick status
analyze-code        # Analyze files
improve src/file.py # Improve specific file
patch src/file.py   # Patch file
health              # Full diagnostics
menu                # Show action menu
chatdev             # Jump to ChatDev
```

---

## Troubleshooting

### "No module named src" Error
```bash
# Fix: Regenerate autonomous status
python scripts/autonomous_status.py --verbose

# Or manually:
python -c "import sys; print(sys.path)"
```

### Ollama Timeout on Large Files
```bash
# Increase timeout:
$env:NUSYQ_OLLAMA_TIMEOUT = "180"
python scripts/start_nusyq.py improve "large_file.py"
```

### ChatDev Not Found
```bash
# Verify installation
ls C:\Users\keath\NuSyQ\ChatDev\

# Check status
python scripts/autonomous_status.py --verbose

# Should see: ✅ ChatDev: Found at C:\Users\keath\NuSyQ\ChatDev
```

### Import Errors
```bash
# Run quick fix
python src/utils/quick_import_fix.py

# Or check:
python -c "from src.tools import *; print('✅ Imports OK')"
```

---

## Quick Links

- **System Status**: `python scripts/start_nusyq.py brief`
- **All Actions**: `python scripts/start_nusyq.py menu`
- **Documentation**: [COMPLETE_ACTIVATION_SUMMARY.md](COMPLETE_ACTIVATION_SUMMARY.md)
- **Practical Guide**: [PRACTICAL_USAGE_GUIDE.md](PRACTICAL_USAGE_GUIDE.md)
- **ChatDev Integration**: [C:\Users\keath\NuSyQ\ChatDev\README.md](C:\Users\keath\NuSyQ\ChatDev\README.md)
- **Agent Navigation**: [AGENTS.md](AGENTS.md)

---

## Most Common Commands

**Just Getting Started?**
```bash
python scripts/start_nusyq.py brief      # See system status
python scripts/start_nusyq.py doctor     # Full health check
python scripts/autonomous_status.py --verbose  # Verify all systems
```

**Ready to Improve Code?**
```bash
python scripts/start_nusyq.py analyze                # Find files to improve
python scripts/start_nusyq.py improve "src/file.py" # Improve specific file
```

**Want to Generate Code?**
```bash
cd C:\Users\keath\NuSyQ\ChatDev
python run_ollama.py --task "Your idea" --name "ProjectName" --model "qwen2.5-coder:7b"
```

---

**Status**: 🟢 System Fully Operational | All 919 Capabilities Available | Ready to Use
