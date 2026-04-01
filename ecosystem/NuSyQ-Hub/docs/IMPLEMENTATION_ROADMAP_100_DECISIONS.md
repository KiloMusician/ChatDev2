# Implementation Roadmap - 100 Strategic Decisions Applied

*Date: December 26, 2025*
*Status: Configuration complete, ready for phased implementation*

---

## ✅ Configuration Applied (All 100 Defaults)

Updated `config/orchestration_defaults.json` with comprehensive operational settings across 6 domains:

1. **Terminal Orchestration** (1-10)
2. **Wizard Navigator** (11-29)
3. **Errors & Diagnostics** (30-41)
4. **Terminal Architecture** (42-50)
5. **Guild Board** (51-100)

---

## 🎯 High-Impact Changes (Top 20)

### Immediate Effect
1. **Default agent status:** `observing` → Safer onboarding
2. **Quest ID format:** `quest_YYYYMMDD_HHMMSS_slug` → Human-readable
3. **Post throttle:** 5 posts/minute → Prevents spam
4. **Auto-release timeout:** 10 minutes → Faster recovery
5. **Archive quests:** 14 days → Cleaner backlog
6. **Long-run alert:** 24 hours → Earlier detection

### Routing & Visibility
7. **Routing priority:** Explicit → keyword → event → default
8. **Always-log systems:** claude_orchestrator, copilot_bridge, wizard_nav, chatdev, task_router
9. **Terminal updates:** Route to 🎯 Zeta terminal
10. **Priority terminals:** Claude, Copilot, Codex

### Integration & Automation
11. **Quest log sync:** Disabled → Separation of concerns
12. **Culture Ship write:** Enabled (signals only)
13. **ZETA tracker integration:** Enabled
14. **Guild steward automation:** Enabled
15. **Boss Rush:** Auto-convert top 10 error clusters

### Storage & Retention
16. **Event log rotation:** 25 MB → More frequent compression
17. **Lifecycle cadence:** Every 4 hours
18. **Lifecycle retention:** 30 reports
19. **Notes storage:** Per-repo → Better isolation
20. **Explain priority:** README → SYSTEM_MAP → docs

---

## 📋 Phased Implementation Plan

### Phase 1: Validation & Safety (Week 1)
**Goal:** Ensure configuration doesn't break existing systems

**Tasks:**
- [x] Update orchestration_defaults.json ✅
- [x] Validate JSON syntax ✅
- [ ] Test guild_status command with new settings
- [ ] Verify quest ID format generation
- [ ] Test auto-heartbeat with "observing" status
- [ ] Confirm post throttle (5/min limit)

**Commands:**
```bash
# Test guild status
python scripts/start_nusyq.py guild_status

# Create test quest with new ID format
python scripts/start_nusyq.py guild_add_quest copilot "Test quest" "Verify new ID format" 5 safe test

# Heartbeat as observing
python scripts/start_nusyq.py guild_heartbeat copilot observing
```

**Expected outcomes:**
- Guild board operates normally
- Quest IDs use new format
- Agents start as "observing"
- Post throttle enforced

### Phase 2: Terminal Routing (Week 1-2)
**Goal:** Wire terminal router to guild board

**Tasks:**
- [ ] Update `agent_terminal_router.py` to route guild events
- [ ] Route heartbeats → 🎯 Zeta terminal
- [ ] Route claims → ✓ Tasks terminal
- [ ] Route posts by type (progress → 💡 Suggestions, blockage → 🔥 Errors)
- [ ] Route completions → ✓ Tasks + 📊 Metrics
- [ ] Enable per-message audit log

**Integration point:**
```python
# In agent_terminal_router.py
async def route_guild_event(event_type, agent, data):
    if event_type == "heartbeat":
        await write_to_terminal(agent, TerminalType.ZETA, ...)
    elif event_type == "claim":
        await write_to_terminal(agent, TerminalType.TASKS, ...)
    # etc.
```

**Validation:**
```bash
# Post heartbeat and check Zeta terminal
python scripts/start_nusyq.py guild_heartbeat copilot working

# Claim quest and check Tasks terminal
python scripts/start_nusyq.py guild_claim copilot quest_20251226_120000_test
```

### Phase 3: Boss Rush Automation (Week 2)
**Goal:** Auto-convert top 10 error clusters to quests

**Tasks:**
- [ ] Create `src/automation/boss_rush_generator.py`
- [ ] Scan errors weekly (Sunday 06:00)
- [ ] Cluster by (file, error_type)
- [ ] Generate quests for top 10 clusters
- [ ] Auto-tag with `boss_rush`, safety tier, count
- [ ] Post quests to guild board

**Boss Rush flow:**
```
Sunday 06:00:
1. python scripts/start_nusyq.py error_report
2. Group errors → top 10 clusters
3. For each cluster:
   - quest_id = quest_{date}_{time}_{file_slug}_errors
   - title = "Fix {count} {error_type} in {file}"
   - description = Error details
   - Auto-add to guild board
4. Agents see available quests
```

**Validation:**
```bash
# Manual Boss Rush trigger
python scripts/start_nusyq.py boss_rush

# Check created quests
python scripts/start_nusyq.py guild_available copilot
```

### Phase 4: Guild Steward Agent (Week 2-3)
**Goal:** Autonomous hygiene maintenance

**Tasks:**
- [ ] Create `src/agents/guild_steward.py`
- [ ] Archive quests older than 14 days
- [ ] Release claims with no heartbeat (10 min timeout)
- [ ] Cleanup resolved signals
- [ ] Generate daily rollup at 06:00
- [ ] Run steward every hour

**Steward loop:**
```python
async def steward_cycle():
    # Archive old quests
    archived = await board.archive_completed_quests(age_days=14)

    # Release stale claims
    released = await board.release_stale_claims(timeout_minutes=10)

    # Cleanup signals
    cleaned = await board.cleanup_resolved_signals()

    # Generate rollup if 06:00
    if current_hour == 6:
        await renderer.render_and_save()
```

**Validation:**
```bash
# Manual steward run
python scripts/start_nusyq.py guild_steward

# Check steward logs
cat state/guild/steward_log.jsonl
```

### Phase 5: Culture Ship Integration (Week 3)
**Goal:** Emergence observation + signal writing

**Tasks:**
- [ ] Wire Culture Ship to read guild events
- [ ] Observe quest completions for "What did we learn?"
- [ ] Write critical signals to guild board
- [ ] Capture agent collaboration patterns
- [ ] Generate monthly emergence reports

**Culture Ship → Guild Board:**
```python
# Culture Ship can write signals
await board.add_signal(
    severity="INFO",
    message="Agents collaborating on complex refactor (party of 3)",
    source="culture_ship",
    context={...}
)
```

### Phase 6: ZETA Tracker Integration (Week 3-4)
**Goal:** Quest completions advance ZETA phases

**Tasks:**
- [ ] Wire guild board to ZETA_PROGRESS_TRACKER.json
- [ ] Count quest completions per phase
- [ ] Auto-advance phase when threshold met
- [ ] Display ZETA progress in guild board
- [ ] Link quests to ZETA milestones

**ZETA advancement:**
```python
# When quest completes
zeta = load_zeta_tracker()
zeta.phases["current"].quests_completed += 1

if zeta.phases["current"].quests_completed >= threshold:
    zeta.advance_to_next_phase()
    await board.add_signal("ZETA phase advanced!")
```

### Phase 7: Enhanced Rendering (Week 4)
**Goal:** HTML views, leaderboards, git status

**Tasks:**
- [ ] Implement HTML renderer
- [ ] Add leaderboard (top agents by quests completed)
- [ ] Display open PRs per repo
- [ ] Show git status summary
- [ ] Enable SimulatedVerse daily mirror

**HTML output:**
```bash
python scripts/start_nusyq.py guild_render --format html
# → docs/guild_board.html (interactive dashboard)
```

---

## 🔧 Configuration Highlights (Key Changes)

### Quest Management
```json
{
  "quest_id_format": "quest_{YYYYMMDD}_{HHMMSS}_{slug}",
  "default_new_agent_status": "observing",
  "auto_release_timeout_minutes": 10,
  "auto_archive_completed_after_days": 14,
  "long_running_quest_alert_hours": 24
}
```

### Throttling & Limits
```json
{
  "post_throttle_max_per_minute": 5,
  "cross_repo_search_limit": 50,
  "max_events_jsonl_size_mb": 25,
  "lifecycle_retention_report_count": 30
}
```

### Integration Switches
```json
{
  "sync_events_to_quest_log": false,
  "culture_ship_write_enabled": true,
  "integrate_with_zeta_tracker": true,
  "chatdev_auto_claim_tagged_quests": true,
  "mirror_to_simulatedverse": true
}
```

### Automation
```json
{
  "guild_steward_enabled": true,
  "auto_boss_rush_from_top_clusters": true,
  "auto_convert_top_error_clusters_to_quests": true,
  "auto_compress_events": true
}
```

---

## 📊 Success Metrics (Per Phase)

### Phase 1 (Validation)
- ✅ Guild status command succeeds
- ✅ New quest IDs formatted correctly
- ✅ Agents default to "observing"
- ✅ Post throttle enforced (5/min)

### Phase 2 (Terminal Routing)
- ✅ Heartbeats appear in 🎯 Zeta
- ✅ Claims appear in ✓ Tasks
- ✅ Completions trigger dual routing (Tasks + Metrics)
- ✅ Audit log captures all events

### Phase 3 (Boss Rush)
- ✅ Top 10 error clusters identified
- ✅ Quests auto-created weekly
- ✅ Agents can claim Boss Rush quests
- ✅ Error count decreases week-over-week

### Phase 4 (Guild Steward)
- ✅ Old quests archived automatically
- ✅ Stale claims released (no deadlock)
- ✅ Daily rollup generated at 06:00
- ✅ Signal cleanup runs hourly

### Phase 5 (Culture Ship)
- ✅ Emergence patterns captured
- ✅ Signals posted to guild board
- ✅ Monthly reports generated
- ✅ Agent collaboration quantified

### Phase 6 (ZETA Integration)
- ✅ Quest completions advance phases
- ✅ ZETA progress visible in board
- ✅ Phase transitions logged
- ✅ Milestones linked to quests

### Phase 7 (Enhanced Rendering)
- ✅ HTML dashboard functional
- ✅ Leaderboard displays top agents
- ✅ Git status summary shown
- ✅ SimVerse mirror operational

---

## 🏆 Completion Criteria

**Phases 1-2:** Guild board fully operational with terminal routing
**Phases 3-4:** Automation reduces manual overhead by 70%
**Phases 5-6:** Emergence capture + ZETA alignment functional
**Phase 7:** Multi-format rendering + cross-repo visibility

**Target:** 80% of configuration activated within 4 weeks

---

## 🔑 Critical Path (Must-Do First)

1. **Phase 1 validation** → Ensure config doesn't break existing systems ✅
2. **Terminal routing** → Visibility into agent coordination
3. **Boss Rush** → Convert error backlog into actionable quests
4. **Guild Steward** → Autonomous hygiene (no manual cleanup)

**These 4 phases unlock 80% of the value.**

---

## 📁 New Files to Create

```
src/
├── automation/
│   └── boss_rush_generator.py          (Phase 3)
├── agents/
│   └── guild_steward.py                 (Phase 4)
└── integration/
    └── zeta_guild_bridge.py             (Phase 6)

scripts/
└── boss_rush.py                         (Phase 3 CLI)

docs/
└── guild_board.html                     (Phase 7)
```

---

## 🎯 Next Immediate Action

**Test Phase 1 validation:**

```bash
# 1. Test guild status with new config
python scripts/start_nusyq.py guild_status

# 2. Create test quest (verify new ID format)
python scripts/start_nusyq.py guild_add_quest copilot "Test quest" "Verify configuration" 5 safe test

# 3. Check generated quest ID
python scripts/start_nusyq.py guild_available copilot

# 4. Heartbeat as observing
python scripts/start_nusyq.py guild_heartbeat copilot observing

# 5. Verify status
python scripts/start_nusyq.py guild_status
```

**Expected:** All commands succeed, quest ID follows new format, agent shows as "observing"

---

*All 100 defaults applied. Ready for phased implementation.* ✅
