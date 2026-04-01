# NuSyQ-Hub Practical Usage Guide
## Themed Terminals & Action Routing System

---

## 🎯 Quick Start: Running Your First Actions

### 1. System Status Check (No AI Required)
```bash
# Terminal: 📊 Metrics
python scripts/start_nusyq.py brief

# Output: System status, dirty files, commits ahead, current quest
# Time: ~3 seconds
```

### 2. Health Diagnostics (No AI Required)
```bash
# Terminal: 📊 Metrics
python scripts/start_nusyq.py doctor

# Output: Full system health assessment
# Time: ~10 seconds
```

### 3. System Analysis (Uses Ollama)
```bash
# Terminal: 🤖 Agents (automatically routed)
python scripts/start_nusyq.py analyze

# Output: File inventory, working vs. broken, enhancement opportunities
# Time: ~8 seconds
# Note: If Ollama timeouts, increase NUSYQ_OLLAMA_TIMEOUT env var
```

---

## 🔧 Enhancement Actions (Now Fixed!)

### Action 1: **Patch** - Quick Targeted Fixes
**Automatically routes to**: 💡 SUGGESTIONS terminal

```bash
python scripts/start_nusyq.py patch "src/main.py" "Fix OpenClaw retry logic"
```

**What it does**:
- Analyze file for specific issues
- Suggest minimal, targeted fixes
- Maintain existing functionality
- Include inline fix explanation

**Best for**:
- Known issues you want to fix
- Specific error resolution
- Quick code improvements

---

### Action 2: **Fix** - Resolve Errors
**Automatically routes to**: 🔥 ERRORS terminal

```bash
python scripts/start_nusyq.py fix "ImportError: No module named 'chatdev'"
```

**What it does**:
- Use Quantum Problem Resolver
- Diagnose root causes
- Provide multi-modal healing
- Include prevention tips

**Best for**:
- Debugging runtime errors
- Import issues
- Configuration problems

---

### Action 3: **Improve** - Code Quality & Performance
**Automatically routes to**: 💡 SUGGESTIONS terminal

```bash
python scripts/start_nusyq.py improve "src/tools/agent_task_router.py"
```

**What it does**:
- Analyze code quality
- Identify performance optimizations
- Check error handling
- Suggest modern patterns

**Best for**:
- Refactoring large files
- Improving maintainability
- Discovering patterns
- Code optimization

---

### Action 4: **Update** - Dependency Management
**Automatically routes to**: ✅ TASKS terminal

```bash
python scripts/start_nusyq.py update --all
# Or: update --deps (just dependencies)
# Or: update --code (just code patterns)
```

**What it does**:
- Check for outdated packages
- Identify deprecated APIs
- Suggest modern replacements
- Show update commands

**Best for**:
- Dependency management
- API migration
- Version compatibility

---

### Action 5: **Modernize** - Update to Modern Python
**Automatically routes to**: 💡 SUGGESTIONS terminal

```bash
python scripts/start_nusyq.py modernize "src/legacy_module.py"
```

**What it does**:
- Replace pathlib.Path
- Use modern type hints
- Apply structural patterns
- Update exception handling

**Best for**:
- Legacy code
- Python 3.9+ upgrades
- Pattern modernization

---

### Action 6: **Enhance** - Interactive Full Enhancement
**Automatically routes to**: 🏠 MAIN terminal

```bash
python scripts/start_nusyq.py enhance "src/orchestration/"
```

**What it does**:
1. Analyze current state
2. Identify issues & opportunities
3. Suggest all improvements
4. Guide through enhancements

**Best for**:
- Comprehensive directory review
- Multi-step improvements
- Interactive enhancement planning

---

## 🎯 Terminal Routing Reference

### Terminal-to-Action Mapping

| Terminal | Color | Routes | Best For |
|----------|:-----:|--------|----------|
| 🔥 **ERRORS** | Red | fix, debug, heal | Error diagnosis & resolution |
| 💡 **SUGGESTIONS** | Yellow | patch, improve, modernize, enhance | Code quality improvements |
| ✅ **TASKS** | Green | update, patch, build | Build tasks & project work |
| 📊 **METRICS** | Blue | brief, doctor, analyze | System status & monitoring |
| 🤖 **AGENTS** | Purple | analyze, autonomous | AI agent operations |
| 🏠 **MAIN** | Default | General, help, menu | Main interactive mode |

### How Terminal Routing Works

```python
# In enhance_actions.py - each action specifies a terminal
ENHANCEMENT_TERMINAL_MAP = {
    "patch": "TASKS",
    "fix": "ERRORS",
    "improve": "SUGGESTIONS",
    "update": "TASKS",
    "modernize": "SUGGESTIONS",
    "enhance": "MAIN",
}

# When you run an action, it prints a hint:
# [ROUTE ERRORS] 🔥    ← Terminal hint

# Then check the 🔥 ERRORS terminal for results
```

### Terminal Tips

✅ **Keep terminals organized**:
- 📊 METRICS: Status & monitoring
- 🔥 ERRORS: Troubleshooting
- 💡 SUGGESTIONS: Code improvements
- ✅ TASKS: Build & deployment
- 🤖 AGENTS: Autonomous workflows

✅ **Color-coded output**:
- Green = Success
- Red = Error
- Yellow = Warning
- Blue = Info

✅ **Terminal persistence**:
- Output stays in terminal for review
- Can scroll back through history
- Supports copy/paste of commands

---

## 🚀 Practical Workflows

### Workflow 1: Quick Code Quality Check
```bash
# 1. Check system status
python scripts/start_nusyq.py brief
# [ROUTE METRICS] 📊

# 2. Identify issues
python scripts/start_nusyq.py analyze
# [ROUTE AGENTS] 🤖

# 3. Pick a file to improve
python scripts/start_nusyq.py improve "src/agents/agent_orchestration_hub.py"
# [ROUTE SUGGESTIONS] 💡

# Check 💡 SUGGESTIONS terminal for results
```

### Workflow 2: Fix an Error
```bash
# 1. You get an error in a script
# ImportError: No module named 'orchestration'

# 2. Use fix action
python scripts/start_nusyq.py fix "ImportError: No module named 'orchestration'"
# [ROUTE ERRORS] 🔥

# 3. Check 🔥 ERRORS terminal for diagnosis and solution
# 4. Apply recommended fixes
```

### Workflow 3: Prepare for Release
```bash
# 1. Check system health
python scripts/start_nusyq.py doctor
# [ROUTE METRICS] 📊

# 2. Update dependencies
python scripts/start_nusyq.py update --deps
# [ROUTE TASKS] ✅

# 3. Modernize code
python scripts/start_nusyq.py modernize "src/main.py"
# [ROUTE SUGGESTIONS] 💡

# 4. Full system analysis
python scripts/start_nusyq.py analyze
# [ROUTE AGENTS] 🤖

# 5. Review all improvements in respective terminals
```

### Workflow 4: Comprehensive Directory Enhancement
```bash
# 1. Interactive enhancement mode
python scripts/start_nusyq.py enhance "src/orchestration/"
# [ROUTE MAIN] 🏠

# Follow the interactive prompts:
# Step 1: Analyzing current state...
# Step 2: Reviewing issues and opportunities
# Step 3: Suggesting improvements (by impact & effort)
# Step 4: Guiding you through enhancements

# Then use specific actions on identified issues:
python scripts/start_nusyq.py improve "src/orchestration/multi_ai_orchestrator.py"
python scripts/start_nusyq.py patch "src/orchestration/unified_ai_orchestrator.py"
```

---

## 📊 Environment Variables for Customization

### Olllama Configuration
```bash
# Set timeout for Ollama requests (default: 120 seconds)
$env:NUSYQ_OLLAMA_TIMEOUT = "180"
python scripts/start_nusyq.py improve "large_file.py"

# In bash/zsh:
export NUSYQ_OLLAMA_TIMEOUT=180
```

### OpenAI Fallback
```bash
# Set timeout for OpenAI fallback (default: 60 seconds)
$env:NUSYQ_OPENAI_TIMEOUT = "90"
```

### Feature Flags
```bash
# Enable quantum resolver enhancements
$env:NUSYQ_ENABLE_QUANTUM = "true"

# Enable consciousness integration
$env:NUSYQ_CONSCIOUSNESS_ENABLED = "true"
```

---

## 🧪 Testing Enhancement Actions

### Test 1: Quick Patch
```bash
# File exists, task clear, fast feedback
python scripts/start_nusyq.py patch "src/main.py" "Add error logging"
# Expected: ✅ Patch applied
# Time: 5-10 seconds
```

### Test 2: Improve Analysis
```bash
# Comprehensive file analysis (tested & working)
python scripts/start_nusyq.py improve "src/tools/agent_task_router.py"
# Expected: Detailed analysis + recommendations
# Time: 10-15 seconds
# Note: May timeout on very large files, set NUSYQ_OLLAMA_TIMEOUT=180
```

### Test 3: Update Check
```bash
# Non-AI action, instant results
python scripts/start_nusyq.py update --all
# Expected: Dependency list + modernization suggestions
# Time: 1-2 seconds
```

### Test 4: Modernize Single File
```bash
# Small file modernization
python scripts/start_nusyq.py modernize "src/config/service_config.py"
# Expected: Suggestions for modern Python patterns
# Time: 10-15 seconds
```

---

## 🔍 Troubleshooting

### Issue: Action hangs/times out
```bash
# Solution 1: Increase Ollama timeout
$env:NUSYQ_OLLAMA_TIMEOUT = "300"
python scripts/start_nusyq.py improve "your_file.py"

# Solution 2: Use smaller files for testing
python scripts/start_nusyq.py improve "src/config"  # directory
```

### Issue: "No module named 'src'"
```bash
# This was a bug we fixed! Run:
python scripts/autonomous_status.py --verbose

# Should show: 7/7 components available ✅
```

### Issue: Ollama not responding
```bash
# Check if Ollama is running
openclaw gateway health
# Should return: Gateway Health OK (0ms)

# Check Ollama models
python scripts/start_nusyq.py capabilities
# Will show available models
```

### Issue: Terminal not showing output
```bash
# The action likely routed to a different terminal
# Check all theme templates:
# 🔥 ERRORS - for fix actions
# 💡 SUGGESTIONS - for improve/patch/modernize
# ✅ TASKS - for update/patch
# 📊 METRICS - for analyze/brief/doctor
# 🤖 AGENTS - for analyze/autonomous
```

---

## 💡 Pro Tips

1. **Batch operate on directories**
   ```bash
   python scripts/start_nusyq.py improve "src/orchestration/"
   # Analyzes entire directory tree
   ```

2. **Use before and after git commits**
   ```bash
   git status
   python scripts/start_nusyq.py patch "modified_file.py"
   git diff src/  # Review changes
   git add + git commit
   ```

3. **Chain multiple actions**
   ```bash
   python scripts/start_nusyq.py update --deps
   python scripts/start_nusyq.py analyze
   python scripts/start_nusyq.py modernize "src/main.py"
   ```

4. **Monitor system health regularly**
   ```bash
   # Weekly health check
   python scripts/start_nusyq.py doctor
   
   # Monthly trend analysis
   python scripts/start_nusyq.py analyze > health_report.txt
   ```

5. **Use Ollama models strategically**
   ```bash
   # For code: qwen2.5-coder, starcoder2, deepseek-coder
   # For general analysis: llama3.1, mistral
   # Model selection is automatic based on task
   ```

---

## 📚 Additional Resources

- **[SYSTEM_ACTIVATION_REPORT.md](SYSTEM_ACTIVATION_REPORT.md)** - Comprehensive system status
- **[AGENTS.md](AGENTS.md)** - Agent navigation & recovery protocols
- **[docs/CAPABILITY_DIRECTORY.md](docs/CAPABILITY_DIRECTORY.md)** - All 919 capabilities
- **[docs/AUTONOMOUS_QUICK_START.md](docs/AUTONOMOUS_QUICK_START.md)** - Autonomous loop guide
- **.github/copilot-instructions.md** - AI guidance for Copilot

---

**Last Updated**: February 16, 2026  
**Status**: ✅ All actions verified and operational
