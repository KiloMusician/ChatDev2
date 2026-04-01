# Orphaned Symbols Modernization Plan
**Generated:** 2026-02-17  
**Status:** Strategic Planning Phase  
**Philosophy:** Rehabilitate, Don't Delete

## Executive Summary
Nogic analysis identified 50 "orphaned symbols" - functions/classes with zero call references. Rather than treating these as dead code for deletion, we recognize them as **dormant capabilities** awaiting integration into the active ecosystem.

## Orphaned Symbol Categories & Rehabilitation Paths

### 1. High-Value Factory Functions (4 symbols) ⭐⭐⭐
**Symbols:**
- `get_integrator` (ai/ollama_chatdev_integrator.py:21)
- `get_orchestrator` (ai/claude_copilot_orchestrator.py:22)
- `create_quantum_resolver` (archive/quantum_problem_resolver_evolution/quantum_problem_resolver_v4.2.0_ARCHIVE.py:1172)
- `create_server` (docs/Core/context_server.py:30)

**Modernization Strategy:**
- [ ] Wire `get_integrator()` and `get_orchestrator()` into `src/orchestration/multi_ai_orchestrator.py`
- [ ] Add CLI flags: `--use-ollama-chatdev`, `--use-claude-orchestrator`
- [ ] Create `scripts/factory_migration.py` to promote v4.2.0 resolver patterns
- [ ] Expose `create_server()` in main.py as `--mode=context_server`

**Value Proposition:** These are API entry points that make subsystems accessible. Missing connective tissue, not value.

---

### 2. Documentation & Example Functions (18 symbols) ⭐⭐⭐
**Symbols:**
- `example_1_basic_ollama` through `example_10_error_handling` (examples/claude_orchestrator_usage.py)
- `example_health_check_with_rate_limiting` (examples/observability/structured_logging_integration.py:189)
- Various dual_write_node_example.js functions

**Current Problem:** Beautiful documentation code that demonstrates system capabilities, but no one discovers it because it's not invoked anywhere.

**Modernization Strategy:**
- [ ] Create `scripts/run_examples.py` - Interactive CLI menu for all examples
- [ ] Add `--mode=tutorial` to main.py that runs example carousel
- [ ] Wire examples into Culture Ship as "showcase projects"
- [ ] Generate quest: "Try Example: Batch Processing" with auto-completion tracking
- [ ] Add VS Code task: "🎓 Learn: Run System Examples"

**Integration Points:**
```python
# Add to scripts/start_nusyq.py action menu
if action == "examples":
    from examples.claude_orchestrator_usage import (
        example_1_basic_ollama,
        example_2_code_review,
        # ... all 10 examples
    )
    # Interactive menu: "Which example? [1-10]"
```

**Value Proposition:** These are tutorials-as-code. Should be first-class learning resources.

---

### 3. Mock Infrastructure (6 symbols) ⭐⭐
**Symbols:**
- `health`, `generate` (deploy/ollama_mock/app.py)
- `health`, `generate`, `generate_stream`, `generate_sse` (deploy/ollama_mock/app_fastapi.py)

**Current Problem:** Offline-first Ollama mock for testing, but not wired to any test runner.

**Modernization Strategy:**
- [ ] Add pytest fixture: `@pytest.fixture def mock_ollama_server()` that spawns app.py
- [ ] Wire into `tests/llm_testing/ultimate_gas_test.py` with `--offline` flag
- [ ] Add `scripts/start_mock_ollama.py` for manual offline development
- [ ] Document in `docs/OFFLINE_DEVELOPMENT_MODE.md`
- [ ] Add environment variable: `NUSYQ_MOCK_OLLAMA=1` for CI/CD

**Integration Points:**
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def offline_ollama(request):
    if request.config.getoption("--offline"):
        proc = subprocess.Popen(["python", "deploy/ollama_mock/app_fastapi.py"])
        yield "http://localhost:11434"
        proc.terminate()
```

**Value Proposition:** Enable $0 CI/CD testing and airplane-mode development.

---

### 4. Dashboard UI Components (4 symbols) ⭐⭐
**Symbols:**
- `renderAgents`, `renderQuests`, `renderErrors` (extensions/agent-dashboard/media/main.js)
- `activate` (extensions/agent-dashboard/extension.js:263)

**Current Problem:** UI functions exist but VSCode WebView never calls them.

**Modernization Strategy:**
- [ ] Audit `extensions/agent-dashboard/extension.js` - find broken message handlers
- [ ] Wire `renderAgents()` to `webview.postMessage({command: 'renderAgents', data: agents})`
- [ ] Add IPC bridge: VSCode Extension ↔ Quest System ↔ Dashboard UI
- [ ] Test dashboard with: `code --extensionDevelopmentPath=./extensions/agent-dashboard`

**Integration Points:**
```javascript
// extension.js - Add event listener
panel.webview.onDidReceiveMessage(message => {
    switch (message.command) {
        case 'requestAgents':
            panel.webview.postMessage({command: 'renderAgents', data: getAgents()});
            break;
        case 'requestQuests':
            panel.webview.postMessage({command: 'renderQuests', data: getQuests()});
            break;
    }
});
```

**Value Proposition:** Dashboard exists, just needs plumbing. 2 hours = visual quest management.

---

### 5. Demo & Showcase Systems (2 symbols) ⭐
**Symbols:**
- `quick_demo` (examples/sns_orchestrator_demo.py:307)
- Various helper functions in examples/

**Modernization Strategy:**
- [ ] Add `--demo` flag to main.py that runs quick_demo()
- [ ] Create `scripts/smoke_tests/run_all_demos.py` for CI validation
- [ ] Wire into onboarding: New users run --demo on first launch

---

## Implementation Priority Matrix

| Priority | Category | Effort | Value | Quick Wins |
|----------|----------|--------|-------|------------|
| **P0** | Documentation Examples | 4 hours | 🔥🔥🔥 | CLI menu for examples |
| **P1** | Factory Functions | 2 hours | 🔥🔥 | Wire into orchestrator |
| **P2** | Mock Infrastructure | 6 hours | 🔥🔥 | Offline test fixture |
| **P3** | Dashboard UI | 3 hours | 🔥 | Fix message handlers |
| **P4** | Demo Systems | 2 hours | 🔥 | --demo flag |

---

## Proposed: "Capability Discovery" System

Create a self-healing mechanism that detects orphaned capabilities and auto-generates integration quests:

```python
# src/diagnostics/capability_discovery.py
class CapabilityDiscoveryEngine:
    """Identify dormant capabilities and suggest integrations."""
    
    def discover_orphaned_capabilities(self) -> List[Quest]:
        analysis = NogicQuestIntegration().analyze_architecture()
        quests = []
        
        for symbol in analysis.orphaned_symbols:
            if symbol.file_id.startswith("examples/"):
                quests.append(Quest(
                    title=f"Wire example: {symbol.name}",
                    type="integration",
                    action=f"Create CLI command for {symbol.name}",
                    value="Enable learning path"
                ))
            elif symbol.file_id.startswith("deploy/"):
                quests.append(Quest(
                    title=f"Integrate test mock: {symbol.name}",
                    type="infrastructure",
                    action=f"Add pytest fixture for {symbol.name}",
                    value="Enable offline testing"
                ))
        
        return quests
```

---

## Success Metrics

After modernization, measure:
- **Discovery Rate:** How many users find and use example functions?
- **Test Coverage:** Does mock infrastructure increase offline test percentage?
- **Dashboard Activation:** Are UI components rendering?
- **Factory Adoption:** Are orchestrator factory functions being called?

Target: **Reduce orphaned symbols from 50 → 10** through integration, not deletion.

---

## Next Steps

1. **Create integration quests** from this plan (auto-generate via Culture Ship)
2. **Document current orphan value** (this file serves as that)
3. **Prioritize P0 work** (examples CLI menu = 4 hours, huge value)
4. **Track resurrection metrics** (quest completion = symbol adoption)

## Related Systems
- Culture Ship Quest Bridge: Auto-generate quests from orphans
- Nogic Integration: Track symbol call graph evolution
- Three Before New Protocol: Check orphans before creating new code

## References
- Nogic Analysis: `Reports/nogic_analysis/latest_architecture_analysis.json`
- Orphan Detection: `src/integrations/nogic_quest_integration.py::_find_orphaned_symbols()`
- Quest System: `src/Rosetta_Quest_System/quest_log.jsonl`
