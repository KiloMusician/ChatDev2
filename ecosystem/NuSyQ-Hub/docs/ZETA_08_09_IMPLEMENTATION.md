# ZETA08 & ZETA09: Error Recovery + Context Awareness Implementation

**Status**: PHASE 2 COMPLETE → ZETA PRIORITY BEGINS
**Date**: 2026-02-16
**Phase**: Phase 2 Quality Enhancement Completed, Transitioning to ZETA Work

---

## Overview

ZETA08 and ZETA09 form the error recovery + context awareness infrastructure for NuSyQ-Hub's autonomous systems. This document outlines the implementation plan and tracks progress.

### ZETA08: Error Recovery Plan
- **Goal**: Build comprehensive error recovery system with ruff JSON diagnostics
- **Status**: Foundation exists (systematic_error_fixer.py), needs expansion
- **Key Components**:
  1. Ruff JSON diagnostics → Recovery mapping
  2. Auto-fixable vs. manual review classification
  3. Recovery action execution engine

### ZETA09: Context Awareness  
- **Goal**: Enhance event history + snapshot persistence for AI agents
- **Status**: Health monitor daemon exists (health_monitor_daemon.py), needs integration
- **Key Components**:
  1. Event history tracking (error patterns, recoveries)
  2. System state snapshots (before/after recovery)
  3. Context restoration from snapshots

---

## ZETA08: Error Recovery System

### Current Infrastructure

**Existing Components**:
- `scripts/systematic_error_fixer.py` (323 lines)
  - `run_ruff_json()` - Ruff diagnostics JSON extraction
  - `classify_severity()` - Error classification
  - `suggest_action()` - Action suggestions
  - `build_recovery_plan()` - Recovery plan generation
  - `fix_trailing_whitespace()` - Whitespace fixes
  - `fix_multiple_blank_lines()` - Formatting fixes
  - `fix_import_spacing()` - Import arrangement

- `src/diagnostics/health_monitor_daemon.py` (370+ lines)
  - Health checking infrastructure
  - `trigger_auto_recovery()` - Recovery workflow
  - Checkpoint mechanisms

- `src/diagnostics/unified_error_reporter.py` (486+ lines)
  - Ground-truth error reporting
  - Multi-tool diagnostic aggregation (ruff, mypy, type checking)

### Phase 1: Ruff JSON Diagnostics Mapping (PRIORITY)

**Objective**: Create bidirectional mapping between ruff diagnostics and recovery actions

**Deliverables**:
1. `ErrorRecoveryMapper` class in `src/healing/error_recovery_mapper.py`
   - Maps ruff rule codes → recovery strategies
   - Classifies auto-fixable vs. manual
   - Generates recovery action queues

2. Enhanced rule classification in `config/error_recovery_rules.json`
   - Expand beyond current suggest_action() hardcoding
   - Support new ruff rules (>100 rules currently)
   - Include severity levels + fixable flags

3. Recovery action executor
   - Execute auto-fix actions (via ruff --fix or surgical edits)
   - Log manual review requirements
   - Track success/failure metrics

### Phase 2: Automated Recovery Workflow

**Objective**: Chain diagnostic → classification → execution → validation

**Components**:
1. `ErrorRecoveryOrchestrator` (async)
   ```python
   async def run_recovery_cycle(self):
       diagnostics = await self.get_diagnostics()
       plan = await self.build_recovery_plan(diagnostics)
       results = await self.execute_plan(plan)
       validation = await self.validate_recovery(results)
       return {plan, results, validation}
   ```

2. Integration with quest system
   - Auto-create quests for manual review items
   - Track recovery as quest completion
   - Update quest_log.jsonl with recovery metadata

### Phase 3: Metrics & Reporting

**Objective**: Track recovery success rates and patterns

**Metrics**:
- Auto-fixed issues (count, rate, time)
- Manual review conversions
- Recovery success rate by rule type
- System improvement trends

---

## ZETA09: Context Awareness System

### Current Infrastructure

**Existing Components**:
- `src/diagnostics/health_monitor_daemon.py`
  - `trigger_auto_recovery()` with checkpoint support
  - `auto_checkpoint()` mechanism
  - Health status tracking

### Phase 1: Event History Tracking

**Objective**: Build comprehensive event log of all system activities

**Components**:
1. `EventHistoryTracker` class
   - Track all error occurrences
   - Record recovery attempts
   - Log AI agent decisions
   - Persist to `state/event_history.jsonl`

2. Event schema:
   ```json
   {
     "timestamp": "2026-02-16T22:30:45Z",
     "event_type": "error|recovery|agent_decision|system_status",
     "severity": "critical|warning|info",
     "source": "system|agent|automation",
     "context": {
       "file": "path/to/file.py",
       "module": "system_module",
       "error_code": "E402",
       "ai_agent": "copilot|ollama|chatdev"
     },
     "outcome": "success|failure|partial",
     "metrics": {
       "duration_ms": 1234,
       "tokens_used": 500,
       "recovery_attempts": 2
     }
   }
   ```

3. Query interface
   - `get_recent_events(hours=24)`
   - `get_events_by_type(type)`
   - `get_error_patterns(window=7d)`

### Phase 2: Snapshot Persistence

**Objective**: Capture system state before/after recovery for context restoration

**Components**:
1. `SystemStateSnapshot` class
   - Capture working file count, broken files, error distribution
   - Record AI system status (5 systems)
   - Store git state (branch, commits, diffs)
   - Persist to `state/snapshots/{timestamp}.json`

2. Snapshot lifecycle:
   - **Pre-recovery**: Baseline snapshot
   - **Post-recovery**: Result snapshot
   - **Diff**: Changes made, improvements measured

3. Recovery restoration
   - If new recovery fails, revert to last good snapshot
   - Selective restoration (recover specific files only)
   - Rollback capability with git integration

### Phase 3: Context-Aware Decision Making

**Objective**: Enable AI agents to access rich contextual information

**Components**:
1. `ContextAwarenessAPI` for agents
   ```python
   async def get_context() -> ContextSnapshot:
       """Get current system context for agent decision-making."""
       return {
           "recent_events": get_recent_events(hours=1),
           "error_patterns": get_error_patterns(),
           "system_state": get_current_snapshot(),
           "recovery_history": get_recovery_history(count=10),
           "agent_coordination": get_multi_agent_state()
       }
   ```

2. Integration points
   - `agent_task_router.py`: Use context for routing decisions
   - `multi_ai_orchestrator.py`: Coordinate based on context
   - `consciousness_bridge.py`: Aware semantic decisions

---

## Implementation Timeline

### Week 1 (This Week): Foundation
- [ ] ZETA08 Phase 1: Ruff diagnostic mapping
- [ ] ZETA09 Phase 1: Event history tracker
- [ ] Create config/error_recovery_rules.json
- [ ] Add tests for both systems

### Week 2: Integration
- [ ] ZETA08 Phase 2: Recovery orchestrator
- [ ] ZETA09 Phase 2: Snapshot persistence
- [ ] Quest system integration
- [ ] Metrics collection

### Week 3: Advanced
- [ ] ZETA08 Phase 3: Reporting dashboard
- [ ] ZETA09 Phase 3: Context-aware APIs
- [ ] Multi-agent coordination tests
- [ ] Documentation + demos

---

## File Structure

### New Files
```
src/healing/
├── error_recovery_mapper.py        (ZETA08 Phase 1)
└── error_recovery_orchestrator.py  (ZETA08 Phase 2)

src/context/
├── event_history_tracker.py        (ZETA09 Phase 1)
├── system_state_snapshot.py        (ZETA09 Phase 2)
└── context_awareness_api.py        (ZETA09 Phase 3)

config/
├── error_recovery_rules.json       (ZETA08 foundation)
└── event_history_config.json       (ZETA09 configuration)

state/
├── event_history.jsonl             (Runtime: event logs)
└── snapshots/                      (Runtime: state snapshots)
```

### Modified Files
```
scripts/systematic_error_fixer.py      (enhance with new mapper)
src/diagnostics/health_monitor_daemon.py (integrate snapshots)
src/tools/agent_task_router.py         (consume context API)
src/orchestration/multi_ai_orchestrator.py (context-aware routing)
src/integration/consciousness_bridge.py (semantic awareness)
```

---

## Success Criteria

### ZETA08 (Error Recovery)
- ✅ 100% of ruff diagnostics mappable to recovery actions
- ✅ Auto-fix success rate >80% for safe rules
- ✅ Zero regressions from auto-fixes
- ✅ Manual review queue integrated with quest system

### ZETA09 (Context Awareness)
- ✅ Event history captures all system activities (100% coverage)
- ✅ Snapshots capture state pre/post recovery
- ✅ Context API used by ≥3 routing decision points
- ✅ Recovery success improves with context awareness

---

## Next Steps

1. Start ZETA08 Phase 1: Create `ErrorRecoveryMapper`
2. Create comprehensive error recovery rules config
3. Test with current diagnostic system
4. Integrate with quest system
5. Then proceed to ZETA09 work

---

**Prepared by**: GitHub Copilot (Agent)
**For**: NuSyQ-Hub Autonomous Systems
**Context**: Phase 2 Complete → ZETA Priority Initiation
