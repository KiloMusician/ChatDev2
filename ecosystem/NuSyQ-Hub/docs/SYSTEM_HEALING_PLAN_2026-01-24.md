# System Healing Plan - 2026-01-24

## Current Health Status

**System Check Run**: 2026-01-24 00:48:12
**Overall Status**: 🟡 YELLOW - Services scaffolded but not persistent

### What's Actually Working ✅

1. **MCP Server** - 4 Python processes active
   - PIDs: 12416, 31376, 38860, 39832
   - Running: `python -m src.integration.mcp_server`
   - Status: HEALTHY (multiple instances may be redundant)

2. **Repository Detection** - All 3 repos accessible
   - NuSyQ-Hub: `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub`
   - NuSyQ: `C:\Users\keath\NuSyQ`
   - SimulatedVerse: `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`

3. **Ollama** - LLM backend operational
   - Version: 0.13.5
   - Status: RUNNING

4. **Test Suite** - Passing
   - GitHub integration: 76.2/100
   - Core smoke tests: PASS

### What's Broken/Missing ❌

1. **Orchestrator** (Critical)
   - Expected: `start_orchestrator.py` or `MultiAIOrchestrator`
   - Actual: NOT RUNNING
   - Impact: No multi-AI coordination

2. **PU Queue Processor** (Critical)
   - Expected: Processing unit queue active
   - Actual: NOT RUNNING
   - Impact: 242/246 PUs stuck, no new task processing

3. **Quest Log Sync** (High Priority)
   - Expected: `cross_ecosystem_sync` running
   - Actual: NOT RUNNING
   - Impact: SimulatedVerse not getting quest updates

4. **SimulatedVerse Dev Server** (High Priority)
   - Expected: `npm run dev` or `tsx server/index.ts`
   - Actual: NOT RUNNING
   - Impact: No frontend visualization

5. **Trace Service** (Medium Priority)
   - Expected: OpenTelemetry instrumentation
   - Actual: NOT IMPLEMENTED
   - Impact: No distributed tracing

6. **Guild Board Renderer** (Medium Priority)
   - Expected: `guild_render` or `GUILD_BOARD.md` generation
   - Actual: NOT RUNNING
   - Impact: No agent coordination visualization

### Redundancies/Issues 🔧

1. **Multiple MCP Server Instances**
   - 4 identical Python processes running same module
   - Likely leftover from previous sessions
   - Action needed: Clean up duplicate processes

2. **Dev Container Failed to Mount**
   - User reported: "every time it said that the other repos were non-existent"
   - Likely cause: Overlapping mounts in devcontainer.json (lines 13-22)
   - Action needed: Fix or remove dev container config (not critical for solo dev)

---

## Healing Strategy

### Phase 1: Service Persistence (CRITICAL)

**Problem**: Services start but don't persist across sessions
**Root Cause**: Scripts are one-shot runners, not daemons

**Solutions**:

1. **Create Persistent Service Manager**
   ```python
   # scripts/service_manager.py
   # Manages background services with process monitoring
   # Commands: start, stop, restart, status
   ```

2. **Make Services Background-Ready**
   - Orchestrator: Add `--daemon` flag
   - PU Queue: Convert to continuous polling
   - Quest Sync: Add `--watch` mode

3. **Add Windows Service Wrappers** (if needed)
   - Use NSSM or Windows Task Scheduler
   - Auto-start critical services

### Phase 2: SimulatedVerse Integration (HIGH PRIORITY)

**Problem**: Frontend never tested, integration unverified
**Action**:

1. **Start SimulatedVerse Dev Server**
   ```bash
   cd C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse
   npm run dev
   # Expected: Server on http://localhost:3000
   ```

2. **Test Hub → SimulatedVerse Data Flow**
   - Create test quest in Hub
   - Verify quest appears in SimulatedVerse UI
   - Document API contract

3. **Fix Quest Log Sync**
   - Enable continuous sync mode
   - Verify 1,114 items visible in SimulatedVerse

### Phase 3: Clean Up Redundancies (MEDIUM PRIORITY)

**Actions**:

1. **Kill Duplicate MCP Server Processes**
   - Keep 1 instance, kill PIDs: 12416, 38860, 39832
   - OR: Implement proper process deduplication

2. **Dev Container Decision**
   - Option A: Fix mounts (if useful for workflow)
   - Option B: Remove/disable (not needed for solo dev)
   - Current recommendation: **Option B** - focus on real work

3. **ChatDev Directory Warning**
   - Test reports: "❌ ChatDev directory missing"
   - Action: Either implement or remove from test suite

### Phase 4: Implement Missing Features (LOW PRIORITY)

1. **Trace Service** - OpenTelemetry instrumentation
2. **Guild Board Renderer** - Agent coordination viz
3. **Autonomous Monitor** - Self-healing capabilities

---

## Healing Actions - Ordered by Impact

### Immediate (Do Now)

1. ✅ **Document actual system state** (this file)
2. 🔧 **Create service persistence script**
3. 🚀 **Start SimulatedVerse and verify**
4. 🧹 **Clean up duplicate MCP processes**

### Short-Term (This Week)

5. 🔄 **Enable persistent PU queue processing**
6. 📡 **Make quest log sync continuous**
7. 🧪 **Test end-to-end: Hub → NuSyQ → SimulatedVerse**
8. 📊 **Create service status dashboard**

### Long-Term (This Month)

9. 🔍 **Implement trace service (OpenTelemetry)**
10. 🎨 **Build guild board renderer**
11. 🤖 **Add autonomous monitor with self-healing**
12. 📈 **Optimize service resource usage**

---

## What NOT to Do (Anti-Goals)

❌ **Don't** rebuild dev container - not useful for solo development
❌ **Don't** add more infrastructure before fixing existing services
❌ **Don't** implement new features before healing core functionality
❌ **Don't** optimize for multi-developer workflows (you're solo)
❌ **Don't** chase perfect abstractions - pragmatic fixes win

---

## Success Metrics

### Healed System Will Have:

1. **Persistent Services** - Survive terminal/session restarts
2. **Working Frontend** - SimulatedVerse shows real data
3. **Clean Processes** - No duplicate/zombie processes
4. **Continuous Sync** - Quest log always up-to-date
5. **Simple Management** - One command to check/start all services

### How to Measure:

```bash
# After healing, this should show all green:
python scripts/ecosystem_entrypoint.py doctor

# Expected output:
# ✅ MCP Server: 1 process (not 4)
# ✅ Orchestrator: RUNNING
# ✅ PU Queue: RUNNING (242/246 → 246/246)
# ✅ Quest Sync: RUNNING
# ✅ SimulatedVerse: http://localhost:3000 (accessible)
# ✅ Guild Board: RENDERING
```

---

## Next Action

**User's stated priority**: "we absolutely need to heal the system"

**My recommendation**: Start with Phase 1, Action #2 - Create persistent service manager that actually keeps services running.

**Question for user**: Should I focus on:
- A) Service persistence (make things stay running)
- B) SimulatedVerse integration (get frontend working)
- C) Process cleanup (kill duplicates, reduce noise)
- D) All three in parallel

---

*Generated by Claude Sonnet 4.5 - System Diagnosis 2026-01-24*
