# File Deduplication & Consolidation Plan

**Generated**: 2025-12-28  
**Status**: Analysis Complete, Awaiting Execution  
**Impact**: Resolves 23 duplicate file groups (excluding **init**.py)

---

## 🎯 Executive Summary

NuSyQ-Hub contains **23 groups of duplicate files** with identical names but
different implementations. The most critical duplicates involve core
infrastructure:

- **modular_logging_system.py** (4 copies): Core logging infrastructure with
  inconsistent filter implementations
- **quantum_problem_resolver.py** (2 copies): 62.92 KB vs 45.19 KB - Major
  system healing component
- **symbolic_cognition.py** (3 copies): 26.88 KB primary + 2 smaller variants
- **wizard_navigator.py** (3 copies): Navigation system with fragmented
  implementations
- **megatag_processor.py** (3 copies): Semantic tagging system split across
  modules

---

## 🚨 Priority 1: modular_logging_system.py (4 Copies)

### Current State

1. **`src/LOGGING/modular_logging_system.py`** - **CANONICAL** ✅
   - Size: 9.0 KB (273 lines)
   - Features: DuplicateMessageFilter, OTELNoiseSuppressor, get_logger(),
     configure_logging()
   - Tags: v1.1, recently updated with both filters
   - **Active imports**: 3 files (guild_board.py, demonstrate_capabilities.py,
     start_nusyq.py)
2. **`src/LOGGING/infrastructure/modular_logging_system.py`** - **SECONDARY**
   - Size: 5.19 KB (153 lines)
   - Features: Same filters, but LOG_FMT_SIMPLE constant, \_get_logger() variant
   - Tags: v1.1, infrastructure-specific
   - **Active imports**: 2 files (extract_commands.py,
     github_integration_auditor.py)
3. **`LOGGING/modular_logging_system.py`** - **LEGACY** ❌
   - Size: 1.21 KB (44 lines)
   - Features: Basic log_info/log_subprocess_event/log_tagged_event only
   - No filters, no modern functionality
   - **Active imports**: 3 files (health_verification.py,
     Interactive-Context-Browser.py, health_verifier.py)
4. **`LOGGING/infrastructure/modular_logging_system.py`** - **LEGACY** ❌
   - Size: 1.66 KB (58 lines)
   - Features: Same basic functions + log_debug/log_error
   - No filters, basic tagging only
   - **Active imports**: 1 file (ChatDev-Party-System.py) + 2 string references
     in legacy orchestrators

### Consolidation Decision

**✅ CANONICAL**: `src/LOGGING/modular_logging_system.py`

**Reasons**:

- Most complete implementation (both filters, full infrastructure)
- Actively maintained (v1.1, commit a852815, a6d2752)
- Modern pattern (get_logger factory, configure_logging)
- Under `src/` hierarchy (correct Python package structure)

**Migration Plan**:

1. Keep `src/LOGGING/infrastructure/modular_logging_system.py` for now
   (specialized use case)
2. Convert both `LOGGING/*` files to **import redirects**:
   ```python
   """Legacy import redirect - use src.LOGGING.modular_logging_system instead"""
   from src.LOGGING.modular_logging_system import *  # noqa: F403, F401
   ```
3. Update 4 active import locations:
   - `src/diagnostics/health_verification.py` line 154
   - `src/interface/Interactive-Context-Browser.py` line 20
   - `src/analysis/health_verifier.py` line 154
   - `src/ai/ChatDev-Party-System.py` line 13
   - `LOGGING/infrastructure/__init__.py` line 23

---

## 🚨 Priority 2: quantum_problem_resolver.py (2 Copies)

### Current State

1. **`src/healing/quantum_problem_resolver.py`** - **CANONICAL** ✅
   - Size: 62.92 KB
   - Location: Primary healing system directory
   - Features: Full quantum healing, multi-modal resolution, self-healing
     infrastructure
2. **`src/quantum/quantum_problem_resolver.py`** - **SPECIALIZED**
   - Size: 45.19 KB
   - Location: Dedicated quantum module directory
   - Likely older or specialized variant

### Consolidation Decision

**✅ CANONICAL**: `src/healing/quantum_problem_resolver.py`

**Reasons**:

- Larger (62.92 KB vs 45.19 KB) - likely more complete
- In `healing/` - correct semantic location for problem resolution
- Referenced in agent navigation protocol (AGENTS.md)

**Migration Plan**:

1. Compare both files line-by-line to identify unique features in `src/quantum/`
   variant
2. Merge unique features into canonical version
3. Convert `src/quantum/quantum_problem_resolver.py` to import redirect
4. Update all import references
5. Run full test suite to verify no breakage

---

## 🚨 Priority 3: symbolic_cognition.py (3 Copies)

### Current State

1. **`src/copilot/symbolic_cognition.py`** - **CANONICAL** ✅
   - Size: 26.88 KB
   - Largest and most complete implementation
   - Copilot-specific semantic processing
2. **`src/core/symbolic_cognition.py`**
   - Size: 4.92 KB
   - Core abstractions/interfaces?
3. **`src/ai/symbolic_cognition.py`**
   - Size: 2.98 KB
   - AI-specific variant

### Consolidation Decision

**✅ CANONICAL**: `src/copilot/symbolic_cognition.py`

**Migration Plan**:

1. Review smaller variants for unique interfaces/abstractions
2. Extract core interfaces to `src/core/` if needed
3. Redirect `src/ai/symbolic_cognition.py` to canonical
4. Update imports

---

## 🚨 Priority 4: wizard_navigator.py (3 Copies)

### Current State

1. **`src/tools/wizard_navigator.py`** - **CANONICAL** ✅
   - Size: 1.35 KB
   - Tools directory = operational utilities
2. **`src/navigation/wizard_navigator/wizard_navigator.py`**
   - Size: 0.54 KB
   - Nested in specialized directory
3. **`src/navigation/wizard_navigator.py`**
   - Size: 0.5 KB
   - Parent directory variant

### Consolidation Decision

**✅ CANONICAL**: `src/tools/wizard_navigator.py`

**Migration Plan**:

1. Merge functionality from all 3 variants
2. Convert navigation variants to redirects
3. Update module initialization files

---

## 🚨 Priority 5: megatag_processor.py (3 Copies)

### Current State

1. **`src/copilot/megatag_processor.py`** - **CANONICAL** ✅
   - Size: 20.14 KB
   - Most complete implementation
2. **`src/core/megatag_processor.py`**
   - Size: 3.68 KB
   - Core abstractions
3. **`src/tagging/megatag_processor.py`**
   - Size: 2.98 KB
   - Generic tagging variant

### Consolidation Decision

**✅ CANONICAL**: `src/copilot/megatag_processor.py`

**Migration Plan**: Similar to symbolic_cognition.py

---

## 📋 Priority 6-10: Other Duplicate Pairs

### 6. consciousness_bridge.py (2 copies)

- **CANONICAL**: `src/integration/consciousness_bridge.py` (1.71 KB)
- **LEGACY**: `src/system/dictionary/consciousness_bridge.py` (21.65 KB) ⚠️
  UNEXPECTED - Larger variant in dictionary?

**Action**: Investigate why dictionary variant is much larger - may contain
unique data structures

### 7. ollama_integration.py (2 copies)

- **CANONICAL**: `src/ai/ollama_integration.py` (7.51 KB)
- **DUPLICATE**: `src/integration/ollama_integration.py` (5.78 KB)

**Action**: Merge into `src/ai/` (AI-specific), redirect `src/integration/`

### 8. omnitag_system.py (2 copies)

- **CANONICAL**: `src/copilot/omnitag_system.py` (11.98 KB)
- **DUPLICATE**: `src/tagging/omnitag_system.py` (2.57 KB)

**Action**: Redirect `src/tagging/` to canonical

### 9. main.py (2 copies)

- **CANONICAL**: `src/main.py` (26.98 KB)
- **DUPLICATE**: `src/core/main.py` (3.52 KB)

**Action**: Investigate core variant - may be different entry point

### 10. chatdev_testing_chamber.py (2 copies)

- **CANONICAL**: `src/orchestration/chatdev_testing_chamber.py` (11.33 KB)
- **DUPLICATE**: `src/tools/chatdev_testing_chamber.py` (0.59 KB)

**Action**: Redirect tools variant to orchestration

---

## 📊 Other Notable Duplicates

- **ArchitectureWatcher.py** (src/core/ vs src/healing/) - 6.05 KB vs 2.63 KB
- **broken_paths_analyzer.py** (src/analysis/ vs src/diagnostics/) - 21.24 KB vs
  13.25 KB
- **doctrine_checker.py** (src/doctrine/ vs src/tools/) - 16.95 KB vs 13.65 KB
- **Enhanced-\***.py\*\* (src/interface/ vs src/interface/archived/) -
  Intentional archive
- **multi_ai_orchestrator.py** (src/legacy/ vs src/orchestration/) - Already
  marked legacy
- **quantum_problem_resolver_unified.py** (src/consciousness/ vs src/core/) -
  6.83 KB vs 33.5 KB
- **repository_analyzer.py** (src/analysis/ vs src/utils/) - 5.89 KB vs 4 KB
- **secrets.py** (src/core/ vs src/setup/) - 1.2 KB vs 19.09 KB

---

## 🎯 Execution Strategy

### Phase 1: Immediate Action (High Impact, Low Risk)

1. ✅ **modular_logging_system.py consolidation**
   - Convert 2 LOGGING/\* files to redirects
   - Update 4 import locations
   - Test guild board, health verification, context browser
2. ✅ **Simple pair consolidations**
   - chatdev_testing_chamber.py
   - omnitag_system.py
   - ollama_integration.py

### Phase 2: Analysis Required (Medium Impact, Higher Risk)

1. ⚠️ **consciousness_bridge.py** - Investigate 21.65 KB dictionary variant
2. ⚠️ **quantum_problem_resolver.py** - Line-by-line comparison needed
3. ⚠️ **main.py** - Verify if core variant is different entry point

### Phase 3: Complex Consolidations (High Impact, Complex)

1. 🔍 **symbolic_cognition.py** (3 copies) - Interface extraction needed
2. 🔍 **wizard_navigator.py** (3 copies) - Functionality merge required
3. 🔍 **megatag_processor.py** (3 copies) - Similar to symbolic_cognition

---

## 🧪 Testing Protocol

For each consolidation:

1. ✅ Run `pytest tests/ -q` to verify no import breakage
2. ✅ Run `python scripts/start_nusyq.py guild_status` to test logging
3. ✅ Run `python scripts/start_nusyq.py selfcheck` for system health
4. ✅ Check `python -m src.main --help` for entry point integrity
5. ✅ Verify no errors in VS Code Problems view

---

## 📝 Documentation Updates

After consolidation:

1. Update import reference guide in README.md
2. Document canonical file locations in CONTRIBUTING.md
3. Add import redirect pattern to development guide
4. Update AGENTS.md with corrected file references

---

## 🚀 Expected Benefits

- **Reduced confusion**: Single source of truth for each component
- **Easier maintenance**: Changes only need to happen once
- **Smaller codebase**: ~50 KB removed from active development
- **Better imports**: Clear, consistent import patterns
- **Type safety**: IDEs/linters can track references correctly

---

## ⚠️ Risks & Mitigations

**Risk**: Imports break in legacy/experimental code  
**Mitigation**: Use import redirects with `from canonical import *`

**Risk**: Different variants have unique features  
**Mitigation**: Line-by-line comparison before deletion, merge unique features

**Risk**: Third-party references to old paths  
**Mitigation**: Keep redirects indefinitely, add deprecation warnings

---

## 🎯 Next Steps

1. **Approve this plan** or request modifications
2. **Execute Phase 1** (modular_logging_system.py + simple pairs)
3. **Run full test suite** and verify no breakage
4. **Commit with detailed message** explaining consolidation
5. **Move to Phase 2** after validation

**Ready to proceed?** Start with modular_logging_system.py consolidation
(highest impact, well-understood).
