# NuSyQ-Hub Capability Discovery Report
**Generated**: 2025-12-24 02:57
**Purpose**: Map actual system capabilities vs what's wired in start_nusyq.py

## Current Wired Actions (start_nusyq.py)
- ✅ `snapshot` - System state across 3 repos
- ✅ `heal` - Health check via health.py
- ✅ `suggest` - Contextual suggestions
- ✅ `hygiene` - Spine health check

## Discovered Capabilities (Not Yet Wired)

### Entry Points Found

#### 1. src/main.py - Primary Orchestrator
**Modes supported**:
- `--mode=orchestration` - Multi-AI orchestration
- `--mode=quantum` - Quantum computing modules
- `--mode=analysis` - Repository analysis
- Interactive mode (default)

**Key systems**:
- MultiAIOrchestrator
- QuantumProblemResolver (import failing - needs fix)
- BrokenPathsAnalyzer
- QuickSystemAnalyzer
- CopilotWorkspaceEnhancer
- EnvironmentalAbsorptionEngine ("The Oldest House")

#### 2. src/cli/nusyq_cli.py - Full CLI Tool
**Systems integrated**:
- UnifiedAutonomousHealingPipeline
- HealingCycleScheduler
- ResolutionTracker
- PerformanceCache
- DashboardAPI
- SystemHealthAssessor

#### 3. src/tools/agent_task_router.py - Conversational Task Routing
**Task types**:
- `analyze` - Code analysis
- `generate` - Prototype generation
- `review` - Code review
- `debug` - Debugging assistance
- `plan` - Planning/architecture
- `test` - Test generation
- `document` - Documentation

**Target systems**:
- `auto` - Orchestrator decides
- `ollama` - Local LLM (qwen2.5-coder, deepseek-coder-v2, etc.)
- `chatdev` - Multi-agent team (CEO, CTO, Programmer, Tester)
- `copilot` - VS Code Copilot integration
- `consciousness` - Consciousness Bridge
- `quantum_resolver` - Quantum Problem Resolver

**Methods**:
- `route_task()` - Route task to appropriate system
- `health_check()` - Check system health

### Scripts Directory (120 scripts!)

**Categories observed**:
1. **Analysis**: analyze_consciousness_patterns.py, analyze_current_state.py, analyze_sonarqube_issues.py
2. **Fixing**: autonomous_error_fixer.py, batch_error_fixer.py, batch_type_fixer.py
3. **Type Systems**: add_type_annotations.py, add_type_hints.py, auto_fix_type_hints.py
4. **Git Helpers**: agent_git_helper.py
5. **Aggregation**: aggregate_insights.py
6. **Modernization**: autonomous_modernization_execution.py

### Orchestration Modules

Found in src/orchestration/:
- chatdev_autonomous_router.py
- snapshot_maintenance_system.py
- multi_ai_orchestrator.py
- unified_autonomous_healing_pipeline.py
- healing_cycle_scheduler.py
- auto_healing.py (newly added)
- emergence_protocol.py (newly added)
- semantic_cache.py (newly added)
- suggestion_engine.py (newly added)

## Capability Gaps (What's Not Wired)

### High Value, Not Wired:
1. **Agent Task Router** - Natural language task routing to Ollama/ChatDev
2. **NuSyQ CLI** - Full CLI with healing cycles, monitoring, dashboard
3. **Main Orchestrator** - Multi-mode entry point (orchestration/quantum/analysis)
4. **Autonomous Error Fixing** - 120 scripts for automated fixes
5. **Consciousness Bridge** - Environmental absorption engine
6. **Quantum Problem Resolver** - Advanced self-healing

### Medium Value, Needs Discovery:
1. **Dashboard API** - Web-based monitoring
2. **Healing Cycle Scheduler** - Automated healing workflows
3. **Resolution Tracker** - Track fixes over time
4. **Performance Cache** - Speed optimizations

## Recommended Next Actions

### Immediate (Steward Mode):
1. Wire `agent_task_router` as `analyze`, `generate`, `review` actions
2. Fix QuantumProblemResolver import in main.py
3. Add `cli` action that delegates to nusyq_cli.py

### Near-term (Explore Mode):
4. Test main.py orchestration modes
5. Map which of 120 scripts are actively useful
6. Document consciousness bridge capabilities

### Future (Cultivate Mode):
7. Integrate dashboard API
8. Enable healing cycle automation
9. Wire quantum problem resolver once fixed

## Questions for Living Usage

1. Which task type is most needed: analyze/generate/review/debug?
2. Should Ollama integration be direct or via orchestrator?
3. Is ChatDev stable enough for production use?
4. What's the intended relationship between health.py and SystemHealthAssessor?
5. Are 120 scripts signal or noise? (needs curation)

---

**Discovery Status**: Phase 1 complete
**Next**: Test one high-value capability, observe friction
