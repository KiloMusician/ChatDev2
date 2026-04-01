# 🏥 NUSYQ HEALING QUICK REFERENCE

## Single-Command Entry Points

```bash
# Master orchestrator (all-in-one)
python scripts/healing_orchestrator.py status      # System health
python scripts/healing_orchestrator.py diagnose    # Full diagnostic
python scripts/healing_orchestrator.py heal        # Auto-healing cycle
python scripts/healing_orchestrator.py validate    # Test validation
python scripts/healing_orchestrator.py process-quests  # Quest management
python scripts/healing_orchestrator.py complete    # Completion check
python scripts/healing_orchestrator.py automate    # Set up scheduling
```

## Direct Tool Access

### 🔍 Diagnosis

```bash
python scripts/system_pain_points_finder.py    # Detailed diagnostic
python scripts/healing_dashboard.py            # Real-time status
python scripts/complete_healing.py             # Validation report
```

### 🏥 Healing

```bash
python scripts/daily_health_cycle.py           # Full automated cycle
python scripts/auto_heal_config.py             # Configuration repair
python scripts/aggressive_cleanup.py           # Deep cleanup
python scripts/improve_type_hints.py --auto-fix  # Type improvements
```

### 📋 Quest Management

```bash
python scripts/todos_to_quests.py --limit 20  # Convert TODOs
python -m src.Rosetta_Quest_System.quest_processor --process 10
```

## Common Workflows

### 📊 Health Check (2 seconds)

```bash
python scripts/healing_orchestrator.py status
```

### 🔧 Full Healing Cycle (2-3 minutes)

```bash
python scripts/healing_orchestrator.py heal
```

### ✅ Validation (1 minute)

```bash
python scripts/healing_orchestrator.py validate
```

### 📈 Complete System Review (5 minutes)

```bash
python scripts/healing_orchestrator.py diagnose
python scripts/healing_orchestrator.py process-quests
python scripts/healing_orchestrator.py complete
```

## Health Metrics at a Glance

```
View Dashboard:         python scripts/healing_orchestrator.py status
Recent History:         tail -10 state/reports/health_history.jsonl
Pain Points Report:     cat state/reports/pain_points.json | jq
Quest Items:            tail -20 src/Rosetta_Quest_System/quest_log.jsonl
```

## Automation Setup

### Windows (Task Scheduler)

```
1. Open Task Scheduler
2. Create Basic Task → "NuSyQ Daily Healing"
3. Trigger: Daily at 2:00 AM
4. Action: python scripts/daily_health_cycle.py
5. Start in: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
```

### Linux/Mac (Cron)

```bash
# Add to crontab -e
0 2 * * * cd /path/to/NuSyQ-Hub && python scripts/daily_health_cycle.py
```

## Key Files Location

```
Healing Tools:           scripts/
  ├─ healing_orchestrator.py     (Master command)
  ├─ daily_health_cycle.py       (Automated cycle)
  ├─ system_pain_points_finder.py (Diagnostics)
  ├─ healing_dashboard.py        (Dashboard)
  ├─ complete_healing.py         (Validation)
  └─ ...

Documentation:          ./ (root) + docs/
  ├─ HEALING_COMPLETE_FINAL_SYNTHESIS.md
  ├─ HEALING_SESSION_RESULTS.md
  ├─ HEALING_PROGRESS_REPORT.md
  ├─ QUICK_START_HEALING.md
  └─ docs/SYSTEM_HEALTH_RESTORATION_PLAN.md

Tracking:               src/Rosetta_Quest_System/
  └─ quest_log.jsonl  (Structured work items)

History:                state/reports/
  ├─ health_history.jsonl  (JSONL time-series)
  ├─ pain_points.json      (Latest snapshot)
  └─ current_state.md      (System overview)
```

## Healing System Health

| Component     | Status      | Command                                            |
| ------------- | ----------- | -------------------------------------------------- |
| Tools         | ✅ 8/8      | `ls -la scripts/healing_*.py scripts/*cleanup*.py` |
| Diagnostics   | ✅ Active   | `python scripts/system_pain_points_finder.py`      |
| Automation    | ✅ Running  | `tail state/reports/health_history.jsonl`          |
| Tests         | ✅ Passing  | `python -m pytest tests/test_minimal.py -q`        |
| Documentation | ✅ Complete | `ls -la *.md docs/`                                |

## Troubleshooting

### Tools not found?

```bash
cd /path/to/NuSyQ-Hub
python scripts/healing_orchestrator.py help
```

### Health history empty?

```bash
python scripts/daily_health_cycle.py  # Run cycle to generate history
```

### Tests failing?

```bash
python scripts/healing_orchestrator.py validate
python -m pytest tests/ -x --tb=short  # More detail
```

### Need manual healing?

```bash
python scripts/aggressive_cleanup.py --dry-run  # Preview changes
python scripts/improve_type_hints.py --interactive  # Step through
```

## Next Steps

1. **Today**

   ```bash
   python scripts/healing_orchestrator.py status
   ```

2. **This Week**

   ```bash
   python scripts/healing_orchestrator.py process-quests
   # Process top 10 quests
   ```

3. **This Month**

   ```bash
   python scripts/healing_orchestrator.py diagnose
   python scripts/aggressive_cleanup.py
   ```

4. **Continuous**
   ```bash
   # Set up automation (see above)
   # Runs daily at 2:00 AM automatically
   ```

---

**Quick Summary:**

- 🎯 Use `healing_orchestrator.py` for most operations
- 📊 Check status anytime: `status` command
- 🔧 Run healing cycle: `heal` command
- 📋 Manage work items: `process-quests` command
- ⏰ Automation: Use `automate` command to set up scheduling

**System Status:** ✅ **FULLY OPERATIONAL AND SUSTAINABLE**
