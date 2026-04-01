# Duplicate Files Consolidation Plan

**Date**: 2025-12-28
**Based On**: Duplicate Files Audit
**Execution Time**: Estimated 12-15 hours total

---

## Import Analysis Results

### 1. modular_logging_system.py - CRITICAL INCONSISTENCY

**Import Patterns Found** (15 total imports):
```python
# Pattern 1: Root LOGGING directory (5 imports)
from LOGGING.infrastructure.modular_logging_system import ...
from LOGGING.modular_logging_system import ...

# Pattern 2: src.LOGGING directory (10 imports)
from src.LOGGING.modular_logging_system import ...
from src.LOGGING.infrastructure.modular_logging_system import ...

# Pattern 3: Lowercase variant (INCORRECT)
from src.logging.modular_logging_system import ...  # healing/quantum_problem_resolver.py
```

**Files Affected**:
1. `src/ai/ChatDev-Party-System.py` - `LOGGING.infrastructure`
2. `src/analysis/health_verifier.py` - `LOGGING.modular_logging_system`
3. `src/copilot/copilot_enhancement_bridge.py` - Dynamic importlib loading
4. `src/diagnostics/health_verification.py` - `LOGGING.modular_logging_system`
5. `src/guild/guild_board.py` - `src.LOGGING.modular_logging_system`
6. `src/healing/quantum_problem_resolver.py` - **BROKEN**: `src.logging` (lowercase)
7. `src/healing/quantum_problem_resolver_clean.py` - **BROKEN**: `src.logging`
8. `src/interface/Interactive-Context-Browser.py` - `LOGGING.modular_logging_system`
9. `src/legacy/consolidation_20251211/*` - `LOGGING.infrastructure`
10. `src/LOGGING/__init__.py` - Local import
11. `src/tools/extract_commands.py` - `src.LOGGING.infrastructure`
12. `src/utils/github_integration_auditor.py` - `src.LOGGING.infrastructure`

**CRITICAL DISCOVERY**: modular_logging_system.py ALREADY imports from structured_logging.py!
```python
# Line 23-27 of src/LOGGING/modular_logging_system.py
try:
    from src.observability.structured_logging import HumanReadableFormatter, StructuredFormatter
except ImportError:
    HumanReadableFormatter = None
    StructuredFormatter = None
```

**Consolidation Strategy**:
1. ✅ **Prime**: `src/LOGGING/modular_logging_system.py` (312 lines, most complete)
2. ❌ **Deprecate**: All other 3 instances
3. 🔄 **Migrate**: All imports to `src.observability.structured_logging` (new standard)
4. 🔗 **Shim**: Keep `src/LOGGING/modular_logging_system.py` as compatibility shim temporarily

---

### 2. wizard_navigator.py - CIRCULAR IMPORTS

**Import Patterns** (6 imports):
```python
# All import from src.tools.wizard_navigator
from src.tools.wizard_navigator import WizardNavigator, RepositoryWizard
```

**Files Affected**:
- `src/navigation/wizard_navigator/wizard_navigator.py` - **CIRCULAR**: imports from tools
- `src/navigation/wizard_navigator.py` - Re-exports from tools
- `src/navigation/wizard_navigator/__init__.py` - Package init

**CRITICAL DISCOVERY**: Navigation versions are WRAPPERS around tools version!

**Consolidation Strategy**:
1. ✅ **Prime**: `src/tools/wizard_navigator.py` (actual implementation)
2. 🔄 **Decision Needed**: Should this move to `src/navigation/wizard_navigator/`?
3. ❓ **Architecture Question**: Is navigation a tool, or are tools navigation aids?

**Recommended**:
- **Move** `src/tools/wizard_navigator.py` → `src/navigation/wizard_navigator/core.py`
- **Update** `src/navigation/wizard_navigator/__init__.py` to import from `.core`
- **Deprecate** `src/tools/wizard_navigator.py` with import shim
- **Rationale**: Navigation is conceptual domain, tools are utilities

---

### 3. symbolic_cognition.py - DOMAIN SPECIALIZATION

**Import Patterns** (3 imports):
```python
# Each domain imports from DIFFERENT locations
from src.copilot.symbolic_cognition import SymbolicCognition  # copilot/enhanced_bridge.py
from src.copilot.symbolic_cognition import SymbolicCognition  # enhancements/__init__.py
from src.core.symbolic_cognition import SymbolicCognition    # integration/consciousness_bridge.py
```

**Files Affected**:
- `src/copilot/enhanced_bridge.py` - Uses copilot version
- `src/enhancements/__init__.py` - Uses copilot version
- `src/integration/consciousness_bridge.py` - Uses **core version**

**CRITICAL DISCOVERY**: Imports are ALREADY SPLIT by domain!

**Consolidation Strategy**:
1. **Diff all 3 versions** to determine specialization
2. If identical:
   - ✅ **Prime**: `src/core/symbolic_cognition.py` (base implementation)
   - 🔄 **Migrate**: All imports to core
3. If specialized:
   - ✅ **Base**: `src/core/symbolic_cognition.py`
   - ✅ **Copilot Extension**: `src/copilot/symbolic_cognition.py` (extends base)
   - ✅ **AI Extension**: `src/ai/symbolic_cognition.py` (extends base)
4. **Document**: Why specialization exists

---

### 4. ollama_integration.py - MULTIPLE VARIANTS

**Import Patterns** (9 imports):
```python
# Pattern 1: src.ai.ollama_integration (3 imports)
from src.ai.ollama_integration import KILOOllamaIntegration, ollama, get_ollama_instance

# Pattern 2: src.integration.ollama_integration (6 imports)
from src.integration.ollama_integration import EnhancedOllamaHub, OllamaHub
```

**Files Affected**:
- `src/agents/code_generator.py` - `src.ai.ollama_integration`
- `src/ai/ai_coordinator.py` - `src.ai.ollama_integration`
- `src/ai/ollama_hub.py` - `src.ai.ollama_integration`
- `src/automation/unified_pu_queue.py` - `src.integration.ollama_integration`
- `src/diagnostics/*` - `src.integration.ollama_integration`
- `src/healing/repository_health_restorer.py` - Local `.ollama_integration`
- `src/tools/health_restorer.py` - Local `.ollama_integration`

**CRITICAL DISCOVERY**: TWO DIFFERENT IMPLEMENTATIONS!
- `src/ai/ollama_integration.py` - KILOOllamaIntegration
- `src/integration/ollama_integration.py` - OllamaHub, EnhancedOllamaHub
- `src/orchestration/ollama_integration.py` - Unknown variant

**Consolidation Strategy**:
1. **Diff all 3 versions** to map features
2. **Likely scenario**:
   - ai/ version: Original KILO implementation
   - integration/ version: Enhanced/unified implementation
   - orchestration/ version: Orchestrator-specific adapter
3. ✅ **Prime**: `src/integration/ollama_integration.py` (most imports, "Enhanced" suggests latest)
4. 🔄 **Consolidate**: Merge features from ai/ and orchestration/ into integration/
5. 🔗 **Shim**: Create `src/ai/ollama_integration.py` compatibility shim
6. **Cross-reference**: Extension audit found 5 Ollama integrations total

---

## Consolidation Execution Plan

### Phase 1: File Comparison (3 hours)

**Task 1.1**: Diff modular_logging_system.py variants
```bash
diff -u src/LOGGING/modular_logging_system.py src/LOGGING/infrastructure/modular_logging_system.py > /tmp/logging_diff_1.txt
diff -u LOGGING/modular_logging_system.py LOGGING/infrastructure/modular_logging_system.py > /tmp/logging_diff_2.txt
```

**Task 1.2**: Diff symbolic_cognition.py variants
```bash
diff -u src/core/symbolic_cognition.py src/copilot/symbolic_cognition.py > /tmp/symbolic_diff_1.txt
diff -u src/core/symbolic_cognition.py src/ai/symbolic_cognition.py > /tmp/symbolic_diff_2.txt
```

**Task 1.3**: Diff ollama_integration.py variants
```bash
diff -u src/ai/ollama_integration.py src/integration/ollama_integration.py > /tmp/ollama_diff_1.txt
diff -u src/integration/ollama_integration.py src/orchestration/ollama_integration.py > /tmp/ollama_diff_2.txt
```

**Task 1.4**: Analyze wizard_navigator.py structure
```bash
head -50 src/tools/wizard_navigator.py
head -50 src/navigation/wizard_navigator/wizard_navigator.py
```

**Deliverable**: Diff analysis report documenting:
- Which files are identical vs specialized
- Unique features in each variant
- Prime candidate selection rationale

---

### Phase 2: Import Path Migration (4 hours)

**Task 2.1**: Fix broken imports (IMMEDIATE)
```bash
# Fix lowercase 'logging' imports
sed -i 's/from src\.logging\./from src.LOGGING./g' src/healing/quantum_problem_resolver.py
sed -i 's/from src\.logging\./from src.LOGGING./g' src/healing/quantum_problem_resolver_clean.py
```

**Task 2.2**: Standardize modular_logging_system imports
```bash
# Create migration script
cat > scripts/migrate_logging_imports.py << 'SCRIPT'
import os
import re

MIGRATION_MAP = {
    r'from LOGGING\.infrastructure\.modular_logging_system import':
        'from src.LOGGING.modular_logging_system import',
    r'from LOGGING\.modular_logging_system import':
        'from src.LOGGING.modular_logging_system import',
}

for root, dirs, files in os.walk('./src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path) as f:
                content = f.read()

            modified = content
            for old_pattern, new_import in MIGRATION_MAP.items():
                modified = re.sub(old_pattern, new_import, modified)

            if modified != content:
                with open(path, 'w') as f:
                    f.write(modified)
                print(f"Migrated: {path}")
SCRIPT

python scripts/migrate_logging_imports.py
```

**Task 2.3**: Migrate to structured_logging.py (FUTURE)
```python
# Create deprecation shim in src/LOGGING/modular_logging_system.py
import warnings
warnings.warn(
    "modular_logging_system is deprecated. "
    "Use src.observability.structured_logging instead.",
    DeprecationWarning,
    stacklevel=2
)
from src.observability.structured_logging import *
```

**Deliverable**: All imports standardized to canonical paths

---

### Phase 3: File Consolidation (3 hours)

**Task 3.1**: Consolidate modular_logging_system.py
1. Verify `src/LOGGING/modular_logging_system.py` is most complete (312 lines)
2. Remove `src/LOGGING/infrastructure/modular_logging_system.py`
3. Remove `LOGGING/modular_logging_system.py`
4. Remove `LOGGING/infrastructure/modular_logging_system.py`
5. Update `src/LOGGING/__init__.py` imports

**Task 3.2**: Consolidate wizard_navigator.py
1. Move `src/tools/wizard_navigator.py` → `src/navigation/wizard_navigator/core.py`
2. Update `src/navigation/wizard_navigator/__init__.py`:
   ```python
   from .core import WizardNavigator, RepositoryWizard, main
   ```
3. Create deprecation shim at `src/tools/wizard_navigator.py`:
   ```python
   import warnings
   warnings.warn("Import from src.navigation.wizard_navigator instead", DeprecationWarning)
   from src.navigation.wizard_navigator import *
   ```
4. Remove `src/navigation/wizard_navigator.py` (redundant wrapper)

**Task 3.3**: Consolidate symbolic_cognition.py
1. Diff to determine if specialized or duplicated
2. If duplicated: Keep `src/core/symbolic_cognition.py`, remove ai/ and copilot/
3. If specialized: Document specialization in ADR

**Task 3.4**: Consolidate ollama_integration.py
1. Merge features from all 3 into `src/integration/ollama_integration.py`
2. Create compatibility shims in ai/ and orchestration/
3. Update 9 import statements

**Deliverable**: Single canonical file per module

---

### Phase 4: Testing & Validation (2 hours)

**Task 4.1**: Run import tests
```bash
python -m pytest tests/ -v
python -c "from src.LOGGING.modular_logging_system import get_logger; print('✅ Logging imports work')"
python -c "from src.navigation.wizard_navigator import WizardNavigator; print('✅ Navigator imports work')"
python -c "from src.core.symbolic_cognition import SymbolicCognition; print('✅ Cognition imports work')"
python -c "from src.integration.ollama_integration import EnhancedOllamaHub; print('✅ Ollama imports work')"
```

**Task 4.2**: Run integration tests
```bash
python -m src.diagnostics.unified_error_reporter  # Should work with new imports
python -m src.guild.guild_board --status           # Should work with logging imports
```

**Task 4.3**: Verify no broken imports
```bash
python -m py_compile src/**/*.py  # Compile all files to check syntax
```

**Deliverable**: All tests passing, no import errors

---

### Phase 5: Cleanup & Documentation (1 hour)

**Task 5.1**: Remove deprecated files
```bash
rm src/LOGGING/infrastructure/modular_logging_system.py
rm LOGGING/modular_logging_system.py
rm LOGGING/infrastructure/modular_logging_system.py
# Keep shims temporarily
```

**Task 5.2**: Update documentation
- Update `docs/architecture/MODULE_STRUCTURE.md` with canonical import paths
- Document deprecated import paths with migration guide
- Add section to `CONTRIBUTING.md` about avoiding duplicates

**Task 5.3**: Create Architecture Decision Record
```markdown
# ADR-001: Consolidate Duplicate Module Implementations

## Status
Accepted

## Context
19 duplicate filenames found across codebase, causing import confusion.

## Decision
- Canonical logging: `src.observability.structured_logging`
- Canonical navigation: `src.navigation.wizard_navigator`
- Canonical cognition: `src.core.symbolic_cognition`
- Canonical ollama: `src.integration.ollama_integration`

## Consequences
- Reduced codebase size by ~5-10%
- Eliminated import ambiguity
- Maintained backward compatibility via deprecation shims
```

**Deliverable**: Documentation updated, ADR created

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**: Use deprecation shims for 1-2 release cycles before removal

### Risk 2: Specialized Versions Loss
**Mitigation**: Diff analysis in Phase 1 captures all unique features

### Risk 3: Import Errors During Migration
**Mitigation**: Phase 4 testing catches all import failures

### Risk 4: Unknown Dependencies
**Mitigation**: Grep analysis finds all import statements before migration

---

## Success Criteria

1. ✅ All duplicate files consolidated to single canonical location
2. ✅ All imports standardized to canonical paths
3. ✅ No broken imports (all tests pass)
4. ✅ Deprecation warnings in place for old import paths
5. ✅ Documentation updated with new structure
6. ✅ ADR created documenting consolidation decisions

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Comparison | 3 hours | None |
| Phase 2: Migration | 4 hours | Phase 1 complete |
| Phase 3: Consolidation | 3 hours | Phase 2 complete |
| Phase 4: Testing | 2 hours | Phase 3 complete |
| Phase 5: Cleanup | 1 hour | Phase 4 complete |
| **Total** | **13 hours** | Sequential |

---

## Next Immediate Action

**Execute Phase 1, Task 1.1**: Diff modular_logging_system.py variants

```bash
# Compare prime candidate with infrastructure variant
diff -u src/LOGGING/modular_logging_system.py src/LOGGING/infrastructure/modular_logging_system.py

# Compare root LOGGING variants
diff -u LOGGING/modular_logging_system.py LOGGING/infrastructure/modular_logging_system.py
```

**Expected Outcome**: Identify if infrastructure/ adds any features, or if it's outdated copy

---

## Pattern for Future Prevention

### Pre-commit Hook Addition
```python
# .git/hooks/check-duplicates.py
import sys
from collections import defaultdict
from pathlib import Path

duplicates = defaultdict(list)
for path in Path('src').rglob('*.py'):
    if path.name != '__init__.py':
        duplicates[path.name].append(str(path))

errors = []
for filename, paths in duplicates.items():
    if len(paths) > 1:
        errors.append(f"Duplicate filename: {filename} in {paths}")

if errors:
    print("❌ Duplicate files detected:")
    for error in errors:
        print(f"  {error}")
    sys.exit(1)
```

### Import Guidelines in CONTRIBUTING.md
```markdown
## Import Path Standards

### Canonical Module Locations
- **Logging**: `from src.observability.structured_logging import ...`
- **Navigation**: `from src.navigation.wizard_navigator import ...`
- **Symbolic Cognition**: `from src.core.symbolic_cognition import ...`
- **Ollama Integration**: `from src.integration.ollama_integration import ...`

### Before Creating New Module
1. Search for existing similar modules: `find src/ -name "*keyword*.py"`
2. Check if functionality exists in related domain directories
3. If unsure, ask in PR review or create discussion issue
```

---

## Summary

This consolidation plan addresses 19 duplicate files through systematic diff analysis, import migration, and file consolidation. The 5-phase approach ensures no functionality is lost while establishing canonical module locations and preventing future duplication.

**Key Insight**: Some "duplicates" (wizard_navigator, modular_logging_system) are actually wrappers/shims around canonical implementations, revealing architectural patterns that should be documented.
