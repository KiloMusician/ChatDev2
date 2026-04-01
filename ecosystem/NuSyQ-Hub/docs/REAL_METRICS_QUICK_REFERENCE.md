# Real Metrics & Continuous Optimization - Quick Reference

## TL;DR

Your system now has **real metrics** (no simulation) and **automatic self-optimization**.

## Quick Commands

### Check System Health
```bash
# Get real system metrics (NO SIMULATION)
python src/diagnostics/real_system_metrics.py

# Quiet mode (just save to file)
python src/diagnostics/real_system_metrics.py --quiet
```

### Run Optimization Cycle
```bash
# Run single optimization cycle
python -m src.orchestration.continuous_optimization_engine --once

# View optimization history
python -m src.orchestration.continuous_optimization_engine --history
```

### Broadcast Metrics to Terminal
```bash
# Broadcast once
python -m src.output.metrics_terminal_broadcaster --once

# Broadcast continuously (every 60 seconds)
python -m src.output.metrics_terminal_broadcaster --interval 60
```

### Update Search Index
```bash
# Incremental update (auto-detects changes)
python src/search/index_builder.py --incremental

# Update specific files
python src/search/index_builder.py --incremental --files file1.py file2.py

# Check index health
python src/search/index_builder.py --check-health
```

## What Runs Automatically

### On Every Commit
1. Quest-commit bridge (XP tracking)
2. Smart Search incremental index update

### Want Continuous Optimization?

Run this to start 30-minute optimization cycles:
```bash
python -m src.orchestration.continuous_optimization_engine --interval 30
```

Each cycle:
- Collects health metrics
- Updates search index
- Runs Culture Ship healing
- Broadcasts results to terminals
- Records history

## Real Metrics Explained

### 🏥 Codebase Health
- **Source**: `system_health_assessment_*.json`
- **Meaning**: Percentage of working files vs broken/incomplete
- **Current**: 81.4% (402/880 working)

### 🎯 Quest System
- **Source**: `src/Rosetta_Quest_System/quests.json`
- **Meaning**: Actual quest completion rate and XP
- **Current**: 58.6% (260/444 completed)

### 🔍 Smart Search
- **Source**: `state/search_index/*.json`
- **Meaning**: Index health and search performance
- **Current**: 28,269 files, <0.5ms queries

### 📊 Git Activity
- **Source**: `git log` commands
- **Meaning**: Real commit velocity
- **Current**: 2.0 commits/day

### 🚀 Culture Ship
- **Source**: Healing cycle results in `docs/*HEALING*.md`
- **Meaning**: Autonomous fixes applied
- **Current**: 4 cycles run, fixes logged

### ⚡ PU Queue
- **Source**: `data/unified_pu_queue.json`
- **Meaning**: Task completion rate
- **Current**: 100% success (252/252)

### 🌱 Evolution
- **Source**: Quest log, system manifest, capabilities
- **Meaning**: Real capabilities added
- **Current**: 0 new (7d), 99% token savings from Smart Search

## Where Data Is Stored

### Metrics
- `state/real_system_metrics_*.json` - Timestamped snapshots
- Updated on every collection

### Optimization History
- `state/optimization_history.jsonl` - All cycles
- One JSON object per line (JSONL format)

### Terminal Logs
- `data/terminal_logs/metrics.log` - Real-time metrics broadcasts
- Watchable by terminal watchers

## Integration with Existing Tools

### Smart Search
- Auto-updates on commits (via git hook)
- Agents use for <1ms searches instead of 30-60s grep
- See: `docs/SMART_SEARCH_AGENT_GUIDE.md`

### Culture Ship
- Runs during optimization cycles
- Applies real fixes (no simulation)
- See: `docs/CULTURE_SHIP_AGENT_GUIDE.md`

### Terminal Routing
- Metrics broadcast to metrics terminal
- 16-terminal intelligent routing
- See: `docs/LIVE_TERMINAL_ROUTING_GUIDE.md`

## Anti-Simulation Guarantee

**EVERY VALUE IS REAL**:
- ✅ Health scores from actual file analysis
- ✅ Quest data from quest database
- ✅ Git metrics from git history
- ✅ Search performance from index stats
- ✅ Healing results from Culture Ship logs

**NO FAKE DATA**:
- ❌ No "consciousness" percentages
- ❌ No "velocity" growth indicators
- ❌ No "intelligence" estimates
- ❌ No simulated progress bars

## Typical Workflow

### Daily Monitoring
```bash
# Morning: Check system health
python src/diagnostics/real_system_metrics.py

# View recent improvements
python -m src.orchestration.continuous_optimization_engine --history
```

### After Major Changes
```bash
# Run optimization cycle
python -m src.orchestration.continuous_optimization_engine --once

# Check metrics before/after
python src/diagnostics/real_system_metrics.py
```

### Long-Running Sessions
```bash
# Terminal 1: Continuous optimization (every 30 min)
python -m src.orchestration.continuous_optimization_engine --interval 30

# Terminal 2: Metrics broadcasting (every 60 sec)
python -m src.output.metrics_terminal_broadcaster --interval 60

# Terminal 3: Watch metrics terminal
pwsh data/terminal_watchers/watch_metrics_terminal.ps1
```

## Troubleshooting

### "No metrics found"
- Run: `python src/diagnostics/system_health_assessor.py`
- This generates the base health assessment

### "Index not found"
- Run: `python src/search/index_builder.py`
- Builds initial full index (~86 seconds)

### "Culture Ship fails"
- Check: `src/orchestration/culture_ship_strategic_advisor.py` exists
- Verify: AI orchestrator connections

## More Information

- **Full Session Report**: `docs/SESSION_2026-01-24_SYSTEM_HEALING_COMPLETE.md`
- **Smart Search Guide**: `docs/SMART_SEARCH_AGENT_GUIDE.md`
- **Culture Ship Guide**: `docs/CULTURE_SHIP_AGENT_GUIDE.md`
- **Terminal Routing**: `docs/LIVE_TERMINAL_ROUTING_GUIDE.md`

---

**Remember**: NO SIMULATED PROGRESS. Only real, measurable, useful data. ✅
