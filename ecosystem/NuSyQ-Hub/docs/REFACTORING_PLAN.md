# NuSyQ start_nusyq.py Refactoring Plan

## Current State

- **File**: `scripts/start_nusyq.py`
- **Size**: 5,166 lines (violates Pylint 1000-line convention)
- **Complexity**: Multi-subsystem orchestrator with snapshot classes, git
  operations, quest tracking, action handlers
- **Type Coverage**: ~60% of functions have partial type hints; many lack return
  type annotations

## Issues Addressed

✅ **Type Safety** (FIXED)

- Fixed 11 Pylance `reportOptionalMemberAccess` errors by converting
  `Optional[List[str]] = None` to `List[str] = field(default_factory=list)` in
  `RepoSnapshot` and `QuestSnapshot` dataclasses

✅ **Import Errors** (FIXED)

- Added `# type: ignore[import]` to 4 optional imports
  (`orchestration.suggestion_engine`, `pu_queue_runner`,
  `perpetual_action_generator`, `auto_fix_imports`)

✅ **Formatting** (COMPLETED)

- Ran `ruff --fix` to fix 2 formatting issues
- Ran `black --line-length=100` to ensure consistent formatting

## Proposed Modularization

### Phase 1: Extract Data Classes & Utilities (Low Risk, High Impact)

**File**: `scripts/nusyq_snapshots.py` (350 lines)

```
RepoSnapshot       - Git repository state snapshot
QuestSnapshot      - Quest log state snapshot
git_snapshot()     - Generate repo snapshot
read_quest_log()   - Read and parse quest log
Exports: All snapshot-related functionality
```

**File**: `scripts/nusyq_git_utils.py` (150 lines)

```
run()                      - Subprocess wrapper
is_git_repo()             - Git repo detection
_build_env()              - Environment builder
_append_resource_attributes() - OTEL attribute helper
Exports: Git and subprocess utilities
```

### Phase 2: Extract Health & Diagnostics (Medium Risk)

**File**: `scripts/nusyq_health.py` (400 lines)

```
lightweight_health()           - Health checks
check_spine_hygiene()         - Spine hygiene checks
_static_analysis_fallback()   - Code analysis fallback
read_action_contracts()       - Load action metadata
read_action_catalog()         - Load action catalog
Exports: Health and diagnostic operations
```

### Phase 3: Extract Action Handlers (Medium Risk)

**File**: `scripts/nusyq_action_handlers.py` (800 lines)

```
handle_snapshot()
handle_brief()
handle_suggest()
handle_selfcheck()
handle_analyze()
handle_review()
... (all action dispatcher logic)
Exports: All action handler dispatch logic
```

### Phase 4: Keep as Main Orchestrator (Low Risk)

**File**: `scripts/start_nusyq.py` (1,200 lines)

```
- Import and orchestrate all modules
- main() entry point
- Action routing via ACTION_TERMINAL_MAP
- Terminal emission logic
- Argument parsing and action dispatch
- Integration with external systems (spine, guild, etc.)
```

## Detailed Module Breakdown

### `scripts/nusyq_snapshots.py` (NEW)

**Purpose**: Centralize snapshot data models and snapshot generation

**Classes**:

```python
@dataclass
class RepoSnapshot:
    """Git repository state snapshot"""
    name: str
    path: Optional[Path]
    is_present: bool
    is_git: bool
    branch: str = "unknown"
    dirty: str = "unknown"
    head: str = "unknown"
    ahead_behind: str = "unknown"
    notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate markdown representation"""
```

**Functions**:

```python
def git_snapshot(name: str, path: Optional[Path]) -> RepoSnapshot:
    """Generate snapshot of git repository state"""

def read_quest_log(nusyq_hub_path: Optional[Path]) -> QuestSnapshot:
    """Read and parse NuSyQ-Hub quest log"""
```

**Benefits**:

- Isolated snapshot data models
- Easier to test snapshot generation
- Clearer separation of concerns
- Reduces main file by ~350 lines

---

### `scripts/nusyq_git_utils.py` (NEW)

**Purpose**: Centralize git and subprocess operations

**Functions**:

```python
def run(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_s: int = 10
) -> Tuple[int, str, str]:
    """Run subprocess command safely"""

def is_git_repo(path: Path) -> bool:
    """Check if path is a git repository"""

def _build_env() -> dict:
    """Build environment with tracing support"""

def _append_resource_attributes(
    current: Optional[str],
    additions: dict
) -> str:
    """Append OTEL resource attributes"""
```

**Benefits**:

- Reusable subprocess utilities
- Centralized git operations
- Easier to mock in tests
- Reduces main file by ~150 lines

---

### `scripts/nusyq_health.py` (NEW)

**Purpose**: Health checks, diagnostics, and status reporting

**Functions**:

```python
def lightweight_health(nusyq_hub_path: Optional[Path]) -> List[str]:
    """Generate lightweight health indicators"""

def check_spine_hygiene(
    hub_path: Optional[Path],
    fast: bool = False
) -> List[str]:
    """Check repository hygiene"""

def _static_analysis_fallback(
    file_path: Path,
    content: str,
    lines: int
) -> str:
    """Perform static code analysis"""

def read_action_contracts(hub_path: Optional[Path]) -> dict:
    """Load action contracts metadata"""

def read_action_catalog(hub_path: Optional[Path]) -> dict:
    """Load action catalog metadata"""
```

**Benefits**:

- Grouped diagnostic functions
- Easier to enhance health checks
- Clear API for status operations
- Reduces main file by ~400 lines

---

### `scripts/nusyq_action_handlers.py` (NEW)

**Purpose**: Centralize all action handler dispatch logic

**Functions** (representative subset):

```python
def handle_snapshot(
    hub_path: Optional[Path],
    nusyq_root_path: Optional[Path],
    simverse_path: Optional[Path],
    snapshot_path: Optional[Path]
) -> int:
    """Generate and display system snapshot"""

def handle_brief(
    hub_path: Optional[Path],
    nusyq_root_path: Optional[Path],
    simverse_path: Optional[Path]
) -> int:
    """Generate brief workspace intelligence summary"""

def handle_suggest(
    hub_path: Optional[Path],
    snapshot_path: Optional[Path]
) -> int:
    """Generate and display action suggestions"""

def handle_selfcheck(hub_path: Optional[Path]) -> int:
    """Quick 5-point diagnostic"""

def handle_analyze(
    hub_path: Optional[Path],
    file_path: str,
    system: str = "auto"
) -> int:
    """Analyze file with AI"""

def handle_review(
    hub_path: Optional[Path],
    file_path: str,
    system: str = "auto"
) -> int:
    """Review code quality"""

def handle_debug(
    hub_path: Optional[Path],
    error_desc: str,
    system: str = "auto"
) -> int:
    """Debug error with AI"""
```

**Benefits**:

- Each handler has clear signature
- Easier to test individual actions
- Reduces coupling in main orchestrator
- Reduces main file by ~800 lines

---

### `scripts/start_nusyq.py` (REFACTORED)

**Purpose**: Main orchestrator and entry point

**Responsibilities** (after refactoring):

- Import all action modules
- Parse command-line arguments
- Route actions to correct handlers
- Manage terminal output routing
- Orchestrate cross-system integration
- Error handling and recovery

**Structure** (estimated ~1,200 lines):

```python
# Imports
from scripts.nusyq_snapshots import RepoSnapshot, QuestSnapshot, git_snapshot, read_quest_log
from scripts.nusyq_git_utils import run, is_git_repo
from scripts.nusyq_health import lightweight_health, check_spine_hygiene
from scripts.nusyq_action_handlers import (
    handle_snapshot, handle_brief, handle_suggest,
    handle_selfcheck, handle_analyze, handle_review, handle_debug,
    # ... all other handlers
)

# Constants
ACTION_TERMINAL_MAP = { ... }
KNOWN_ACTIONS = { ... }

# Utilities
def emit_terminal_route(action: str) -> None: ...
def _get_paths() -> RepoPaths: ...
def _run_fast_test_suite(...) -> Tuple[int, str, str]: ...

# Main Entry Point
def main() -> int:
    # Spine initialization
    # Argument parsing
    # Action routing
    # Error handling
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
```

---

## Type Hints Improvement Plan

### Current Coverage

- Dataclasses: ✅ 100% (RepoSnapshot, QuestSnapshot)
- Key functions: ~50% (some missing return types)
- Handler functions: ~30% (many missing arg/return types)
- Internal utilities: ~40%

### Recommended Additions

#### Priority 1: Public API (High Impact)

```python
def main() -> int:
    """Main entry point"""

def emit_terminal_route(action: str) -> None:
    """Emit terminal routing hint"""

def handle_snapshot(
    hub_path: Optional[Path],
    nusyq_root_path: Optional[Path],
    simverse_path: Optional[Path],
    snapshot_path: Optional[Path]
) -> int:
    """Generate system snapshot"""

def handle_brief(
    hub_path: Optional[Path],
    nusyq_root_path: Optional[Path],
    simverse_path: Optional[Path]
) -> int:
    """Generate brief summary"""
```

#### Priority 2: Git Operations

```python
def git_snapshot(name: str, path: Optional[Path]) -> RepoSnapshot:
    """Generate git repository snapshot"""

def run(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_s: int = 10
) -> Tuple[int, str, str]:
    """Run subprocess command"""

def is_git_repo(path: Path) -> bool:
    """Check if path is git repository"""
```

#### Priority 3: Health & Diagnostics

```python
def lightweight_health(nusyq_hub_path: Optional[Path]) -> List[str]:
    """Generate health indicators"""

def check_spine_hygiene(
    hub_path: Optional[Path],
    fast: bool = False
) -> List[str]:
    """Check repository hygiene"""

def read_action_contracts(hub_path: Optional[Path]) -> dict[str, Any]:
    """Load action contracts"""

def read_action_catalog(hub_path: Optional[Path]) -> dict[str, Any]:
    """Load action catalog"""
```

---

## Implementation Timeline

### Week 1: Preparation

- [ ] Finalize type hints for all functions
- [ ] Create module stubs with imports
- [ ] Add docstrings to all functions
- [ ] Update mypy/pylint configuration

### Week 2: Phase 1 - Snapshots

- [ ] Create `scripts/nusyq_snapshots.py`
- [ ] Move snapshot classes and generators
- [ ] Update imports in `start_nusyq.py`
- [ ] Run tests and verify behavior

### Week 3: Phase 2 - Utilities & Health

- [ ] Create `scripts/nusyq_git_utils.py`
- [ ] Create `scripts/nusyq_health.py`
- [ ] Move functions and update imports
- [ ] Run tests and verify behavior

### Week 4: Phase 3 - Action Handlers

- [ ] Create `scripts/nusyq_action_handlers.py`
- [ ] Move all handler functions
- [ ] Update main() dispatcher logic
- [ ] Comprehensive testing

### Week 5: Cleanup & Optimization

- [ ] Run type checker (mypy) against all modules
- [ ] Add missing docstrings
- [ ] Optimize imports
- [ ] Final testing and validation

---

## Benefits of Modularization

| Metric                | Before                | After                        |
| --------------------- | --------------------- | ---------------------------- |
| **Lines per file**    | 5,166                 | ~1,200 (main) + modular libs |
| **Pylint compliance** | ❌ Exceeds 1000 lines | ✅ All modules < 1000 lines  |
| **Type coverage**     | ~50%                  | ~95%                         |
| **Testability**       | Monolithic            | Isolated units               |
| **Reusability**       | Coupled to main       | Importable modules           |
| **Maintenance**       | Difficult             | Clear separation of concerns |

---

## Risk Mitigation

### Testing Strategy

1. **Unit tests**: Test each extracted function independently
2. **Integration tests**: Verify action handlers work with main orchestrator
3. **Regression tests**: Ensure all commands work exactly as before
4. **Type checking**: Run mypy on all modules

### Rollback Plan

- Keep original `start_nusyq.py` as backup
- All refactoring changes pushed to feature branch
- Full test suite runs before merging

### Gradual Migration

- Can extract modules one at a time
- Each phase can be tested independently
- No need to refactor all at once

---

## Maintenance Notes

### Adding New Handlers

1. Add handler function to `scripts/nusyq_action_handlers.py`
2. Import in `scripts/start_nusyq.py`
3. Add to `ACTION_TERMINAL_MAP` and `KNOWN_ACTIONS`
4. Add to main() dispatcher switch/case logic

### Adding New Snapshots

1. Extend dataclass in `scripts/nusyq_snapshots.py`
2. Create generator function
3. Import in main file if needed
4. Add to relevant handlers

### Adding New Health Checks

1. Add function to `scripts/nusyq_health.py`
2. Call from `lightweight_health()` or `check_spine_hygiene()`
3. Test independently before integration

---

## Questions & Future Improvements

### Question 1: Async Support

Should action handlers be async-ready for parallel execution?

- **Current**: Mostly sync with limited async (guild operations)
- **Future**: Consider async refactoring for concurrent actions

### Question 2: Configuration Injection

Should handlers receive a config object instead of individual paths?

- **Current**: Pass individual OptionalPath parameters
- **Future**: Consider config object pattern for cleaner signatures

### Question 3: Error Handling

Should errors return exit codes or raise exceptions?

- **Current**: Mostly return exit codes
- **Future**: Consistent error handling strategy

---

## Related Documentation

- [AGENTS.md](./AGENTS.md) - Agent navigation and self-healing protocol
- [copilot-instructions.md](./.github/copilot-instructions.md) - Copilot
  behavioral doctrine
- [README.md](./README.md) - Project structure and setup

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-08  
**Status**: Ready for implementation phase
