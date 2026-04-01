# 🎯 NuSyQ-Hub Complete Automation - OPERATOR QUICK REFERENCE

**Last Updated:** 2025-12-27  
**System Status:** ✅ OPERATIONAL  
**Tests:** 7/7 PASSING

---

## Quick Commands

### 📋 View System State
```bash
python scripts/start_nusyq.py
```
Shows: Current state snapshot, active quests, system health, next actions

### 🔍 Scan Errors & Generate Quests
```bash
python scripts/start_nusyq.py scan
```
Runs: Error scanner → Signal generation → Quest creation

### 🎬 Show Action Menu
```bash
python scripts/start_nusyq.py menu
```
Browse 60+ actions organized by category (heal, analyze, develop, etc.)

### ⚡ Quick Actions
```bash
python scripts/start_nusyq.py heal           # Healing system
python scripts/start_nusyq.py analyze        # Full analysis
python scripts/start_nusyq.py doctor         # Health check
python scripts/start_nusyq.py review <file> # Code review
python scripts/start_nusyq.py debug "<err>"  # Debug error
```

### 🧪 Validate System
```bash
python scripts/test_full_automation.py
```
7 integration tests, all critical paths validated

---

## 📊 Data Flow At a Glance

```
ERROR                SIGNAL              QUEST              ACTION
Errors found    →   Categorized by   →  Actionable      →  Execute
(1,228 total)       severity           development        via AI or
                    (23 types)         tasks              menu
                                       (23 quests)
```

---

## 🎛️ Key Components

| Component | What It Does | When to Use |
|---|---|---|
| **Error Scanner** | Finds all errors (mypy, ruff, pytest) | On demand or scheduled |
| **Error→Signal Bridge** | Classifies errors by severity | Automatic after scan |
| **Signal→Quest Mapper** | Converts signals to tasks | Automatic after signals |
| **MQTT Broker** | Distributes signals real-time | For agent coordination |
| **Quest Logger** | Records all quests (JSONL) | Always on (append-only) |
| **Ecosystem Orchestrator** | Routes quests to AI | When action needed |
| **Bootstrap System** | Snapshots system state | For debugging/monitoring |

---

## 🤖 AI Routing

Quests automatically route to the best AI system:

- **Ollama** (local LLM) - Type errors, style fixes, simple analysis
- **ChatDev** - Complex development, multi-agent coding
- **Consciousness** - Semantic analysis, pattern recognition
- **Quantum Resolver** - Advanced debugging, self-healing

---

## 📦 Files to Know

| File | Purpose |
|---|---|
| `docs/COMPLETE_AUTOMATION_SYSTEM.md` | Full technical guide |
| `DELIVERY_MANIFEST.md` | Completion summary |
| `scripts/test_full_automation.py` | Integration tests |
| `scripts/start_nusyq.py` | Main entry point |
| `config/automation_config.json` | Customization |
| `src/Rosetta_Quest_System/quest_log.jsonl` | Quest history |
| `state/reports/error_ground_truth.json` | Canonical errors |

---

## 💡 Common Patterns

### Find and fix type errors
```bash
python scripts/start_nusyq.py scan
python scripts/start_nusyq.py menu heal
# Pick "Fix mypy errors" action
```

### Review code quality
```bash
python scripts/start_nusyq.py review src/main.py
# AI analyzes and suggests improvements
```

### Debug specific error
```bash
python scripts/start_nusyq.py debug "TypeError: Expected str, got int"
# Quantum resolver investigates and suggests fix
```

### Check system health
```bash
python scripts/start_nusyq.py doctor
# Full health assessment with recommendations
```

---

## 🔍 Viewing Quests

### Last created quests
```bash
cat src/Rosetta_Quest_System/quest_log.jsonl | tail -5
```

### Quests by priority
```bash
python -c "
import json
with open('src/Rosetta_Quest_System/quest_log.jsonl') as f:
    quests = [json.loads(l) for l in f if 'quest' in l]
for q in sorted(quests, key=lambda x: x.get('priority', 0), reverse=True)[:10]:
    print(f'{q.get(\"priority\", 0)} | {q.get(\"title\", \"N/A\")}')
"
```

### Error trends
```bash
python scripts/generate_quest_metrics.py
cat state/reports/quest_metrics.json
```

---

## ⚙️ Configuration

Edit `config/automation_config.json` to customize:

```json
{
  "error_scanner": {
    "scan_repositories": ["NuSyQ-Hub", "NuSyQ", "SimulatedVerse"],
    "tools": ["mypy", "ruff", "pytest"]
  },
  "orchestrator": {
    "timeout_seconds": 60,
    "ai_preferences": {
      "mypy": "ollama",
      "pytest": "chatdev"
    }
  }
}
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---|---|
| No errors found | Verify tools installed: `mypy --version`, `ruff --version` |
| MQTT fails | Start broker: `docker run -d -p 1883:1883 eclipse-mosquitto` |
| Orchestrator timeout | Increase timeout in config: `"timeout_seconds": 120` |
| Tests fail | Run: `python scripts/test_full_automation.py --verbose` |
| Quests not created | Check quest_log.jsonl: `tail -20 src/Rosetta_Quest_System/quest_log.jsonl` |

---

## 📈 What Each Test Validates

1. **Bootstrap System** - State snapshot works
2. **Capability Registry** - UIs/APIs discoverable
3. **Error→Signal Bridge** - Error conversion accurate
4. **Signal→Quest Mapper** - Quest generation valid
5. **Ecosystem Orchestrator** - AI routing functional
6. **Bridge + Data** - End-to-end error→signal works
7. **Signal→Quest** - Real quest creation verified

**Result:** ✅ 7/7 PASSING

---

## 🚀 Production Setup

```bash
# 1. Configure system
cp config/automation_config.json.template config/automation_config.json
# Edit as needed

# 2. Start MQTT broker (if using real-time distribution)
docker run -d -p 1883:1883 eclipse-mosquitto

# 3. Validate everything works
python scripts/test_full_automation.py

# 4. Enable continuous scanning (optional)
# Add to cron: */30 * * * * cd /path && python scripts/start_nusyq.py scan

# 5. Monitor via quest log
# tail -f src/Rosetta_Quest_System/quest_log.jsonl
```

---

## 📞 When You're Stuck

1. **View full state:** `python scripts/start_nusyq.py`
2. **Check health:** `python scripts/start_nusyq.py doctor`
3. **Read errors:** `python scripts/start_nusyq.py error_report`
4. **Run tests:** `python scripts/test_full_automation.py --verbose`
5. **Read guide:** `docs/COMPLETE_AUTOMATION_SYSTEM.md`

---

**Remember:** This system transforms errors into quests. Run scan → view menu → pick action. That's it! 🎯
