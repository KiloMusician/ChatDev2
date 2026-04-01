# Background Process & Task Hygiene Audit
**Generated:** 2025-12-26 02:52 UTC
**Session:** Phase 4 - Comprehensive Terminal & Background Process Fix

## Issue Identified
Terminal tasks completing but VSCode waiting for input - getting worse as autonomous systems grow.

## Root Causes
1. **Missing presentation settings** in tasks.json across repos
2. **No `isBackground` flags** for long-running services
3. **Processes orphaned** when tasks exit unexpectedly
4. **No central inventory** of background services

## Systems Audit

### NuSyQ-Hub Background Systems
#### Python Services
- [ ] Autonomous Monitor (`scripts/autonomous_monitor.py`)
- [ ] Auto Cycle (`scripts/start_nusyq.py auto_cycle`)
- [ ] Quest Replay Engine
- [ ] Cultivation Metrics Builder
- [ ] Quantum Problem Resolver
- [ ] Cross-Ecosystem Sync

#### Node Services
- [ ] Modular Window Server (Port 3001) - `web/modular-window-server`
- [ ] VSCode Extension Dev Host
- [ ] Express API servers (various)

#### Docker Services
- [ ] Observability Stack (Jaeger, OpenTelemetry Collector)
- [ ] Agent Services (`deploy/docker-compose.agents.yml`)
- [ ] Full Stack (`deploy/docker-compose.full-stack.yml`)
- [ ] AI Task Manager (`projects/ai_task_manager/docker-compose.yml`)

### SimulatedVerse Background Systems
#### Node Services
- [ ] Express API (Port 5002)
- [ ] React Dev Server (Port 3000)
- [ ] WebSocket Services (consciousness sync)

### NuSyQ Root Background Systems
#### PowerShell Services
- [ ] NuSyQ.Orchestrator.ps1
- [ ] Ecosystem Sentinel

#### AI Services
- [ ] Ollama (Port 11434) - 37.5GB models
- [ ] 14 AI Agents (ChatDev integration)
- [ ] MCP Server

## Fixed: NuSyQ-Hub Tasks
✅ `NuSyQ: Snapshot` - Added showReuseMessage: false
✅ `NuSyQ: Auto Cycle` - Added proper presentation settings

## To Fix: All Repos

### 1. Task Presentation Standards
All tasks should have:
```json
"presentation": {
  "echo": true,
  "reveal": "always",
  "focus": false,
  "panel": "shared",
  "showReuseMessage": false,
  "clear": false
}
```

### 2. Background Service Tasks
Long-running services need:
```json
"isBackground": true,
"problemMatcher": {
  "pattern": {
    "regexp": "^Server listening on (.*)$",
    "file": 1
  },
  "background": {
    "activeOnStart": true,
    "beginsPattern": "^Starting",
    "endsPattern": "^Server listening"
  }
}
```

### 3. Process Cleanup Wrapper
Created: `scripts/run_and_exit_clean.py`
- Ensures clean exits
- Handles KeyboardInterrupt
- Returns proper exit codes

## Recommended Actions

### Immediate (Phase 4)
1. Apply presentation settings to all Hub tasks.json entries
2. Mark Docker/Node services as `isBackground: true`
3. Create similar wrappers for SimulatedVerse and NuSyQ
4. Document all background services in central inventory

### Short-term
1. Add health check endpoints for all services
2. Create unified "status" command showing all background processes
3. Implement graceful shutdown handlers
4. Add auto-restart policies for critical services

### Long-term
1. Centralized service orchestration (systemd/PM2 equivalent)
2. Service dependency graph
3. Auto-discovery of orphaned processes
4. Unified logging aggregation

## Zeta Interview Answers (Partial)

**Q: Which subsystem feels most fragile?**
A: Terminal task management - no proper lifecycle management

**Q: Critical-path workflows?**
A: `snapshot` → `hygiene` → `auto_cycle` → continuous monitoring

**Q: Tools to invoke more aggressively?**
A: Auto-cycle should run on PU queue changes, not just manually

**Q: Never auto-run without confirmation?**
A: Git push, dependency updates, production deployments

**Q: Preferred autonomous cadence?**
A: On-demand for fixes, hourly for monitoring, daily for reports

**Q: Auto-resolve lint issues?**
A: Yes - ruff/black fixes are safe

## Next Steps
1. Complete tasks.json hygiene across all repos
2. Catalog all background services
3. Implement unified service manager
4. Add to auto_cycle: background process health check

---
*Status: In Progress - Phase 4*
*Agent: Claude Code (Claude Sonnet 4.5)*
