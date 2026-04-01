# Stages 7-10: Detailed Execution Plan
**Phase 2 - Steps 29-30**
**Target:** Reduce 1,640 → 1,460 mypy errors (-180, -11%)
**Timeline:** 4 stages × 30-45 min = 2-3 hours
**XP Potential:** 80 XP

---

## Stage 7: Return Value & Function Signature Fixes
**Target:** 4 files, ~40 errors
**Priority:** 🔴 High
**Estimated Time:** 30 minutes
**XP Reward:** 20 XP

### File 1: [src/tools/safe_consolidator.py](src/tools/safe_consolidator.py)
**Errors:** 10 (lines 33, 34, 35, 91, 163, 170, 176)

#### Issues:
1. **Lines 33-35:** Missing type annotations
   ```python
   # Current
   empty_files_found = []
   functional_files_preserved = []
   consolidation_actions = []

   # Fix
   empty_files_found: list[str] = []
   functional_files_preserved: list[str] = []
   consolidation_actions: list[dict[str, str]] = []
   ```

2. **Line 91, 163:** Function declared `-> None` but returns dict
   ```python
   # Current
   def identify_safe_consolidations(self) -> None:
       # ... code ...
       return {"empty": [], "actions": []}

   # Fix
   def identify_safe_consolidations(self) -> dict[str, list[Any]]:
       # ... code ...
       return {"empty": [], "actions": []}
   ```

3. **Lines 170, 176:** Functions called but don't return values
   ```python
   # Fix return type or add return statement
   def generate_consolidation_report(self) -> dict[str, Any]:
       # ... add return statement
   ```

**Command to verify:**
```bash
mypy src/tools/safe_consolidator.py --show-error-codes
```

---

### File 2: [src/utils/config_validator.py](src/utils/config_validator.py)
**Errors:** 5 (lines 94, 100, 105)

#### Issues:
1. **Line 100:** Variable `optional_fields` redefined
   ```python
   # Current
   optional_fields = ["a", "b"]  # Line 94
   # ... later ...
   optional_fields = ["c", "d"]  # Line 100 - ERROR

   # Fix: Rename or merge
   optional_fields_part2 = ["c", "d"]
   all_optional_fields = optional_fields + optional_fields_part2
   ```

2. **Line 105:** Unsupported operator for Union type
   ```python
   # Current
   if field in config_dict:  # config_dict: dict[str, Any] | None

   # Fix
   if config_dict is not None and field in config_dict:
   ```

**Command:**
```bash
mypy src/utils/config_validator.py --show-error-codes
```

---

### File 3: [src/tools/ChatDev-Party-System.py](src/tools/ChatDev-Party-System.py)
**Errors:** 3 (line 46)

#### Issue:
```python
# Current
def main() -> None:
    # ... code ...
    return result  # ERROR: returns value

# Fix Option 1: Change signature
def main() -> dict[str, Any]:
    return result

# Fix Option 2: Remove return
def main() -> None:
    result = ...
    # Don't return, just execute
```

**Command:**
```bash
mypy src/tools/ChatDev-Party-System.py --show-error-codes
```

---

### File 4: [src/consciousness/house_of_leaves/doors/__init__.py](src/consciousness/house_of_leaves/doors/__init__.py)
**Errors:** 2 (line 36)

#### Issue:
```python
# Current
def validate_door() -> None:
    if not valid:
        return False  # ERROR

# Fix
def validate_door() -> bool:
    if not valid:
        return False
    return True
```

**Command:**
```bash
mypy src/consciousness/house_of_leaves/doors/__init__.py --show-error-codes
```

---

### Stage 7 Execution Checklist:
- [ ] Fix `safe_consolidator.py` (10 errors)
- [ ] Fix `config_validator.py` (5 errors)
- [ ] Fix `ChatDev-Party-System.py` (3 errors)
- [ ] Fix `house_of_leaves/doors/__init__.py` (2 errors)
- [ ] Run `black src/tools src/utils src/consciousness`
- [ ] Verify with `mypy` on each file
- [ ] Commit: `git commit -m "Stage 7: Fix return types and annotations - 20 XP"`

---

## Stage 8: High-Density Utility File Fixes
**Target:** 5 files, ~50 errors
**Priority:** ⚠️ Medium-High
**Estimated Time:** 45 minutes
**XP Reward:** 25 XP

### File 1: [src/utils/github_instructions_enhancer.py](src/utils/github_instructions_enhancer.py)
**Errors:** 15 (lines 318, 320, 321, 350, 355, 377, 379, 386, 388, 414, 424, 430)

#### Root Cause:
Type inference fails, resulting in `object` type instead of specific types.

#### Issues:
1. **Lines 318, 321, 355, 377, 379:** `"object" has no attribute "append"`
   ```python
   # Current (inferred as object)
   sections = some_function()  # Returns object
   sections.append(item)  # ERROR

   # Fix: Add explicit type
   sections: list[str] = some_function()
   sections.append(item)  # OK
   ```

2. **Lines 320, 350, 388, 414, 424, 430:** Unsupported operators with `object`
   ```python
   # Fix: Type narrowing
   if isinstance(count, int):
       total = count + 1  # OK
   ```

**Strategy:**
- Add type annotations to function return values
- Use `cast()` if necessary: `sections = cast(list[str], some_function())`

**Command:**
```bash
mypy src/utils/github_instructions_enhancer.py --show-error-codes | head -20
```

---

### File 2: [src/utils/enhanced_directory_context_generator.py](src/utils/enhanced_directory_context_generator.py)
**Errors:** 12 (lines 324, 327, 419-421, 450, 452, 453, 648, 655)

#### Issues:
1. **Lines 324, 327:** `Sequence[str]` vs `list[str]` mismatch
   ```python
   # Current
   def format_dependencies(self, deps: list[str]) -> str:
       pass

   def caller(self, items: Sequence[str]) -> None:
       self.format_dependencies(items)  # ERROR: Sequence ≠ list

   # Fix Option 1: Accept Sequence
   def format_dependencies(self, deps: Sequence[str]) -> str:
       deps_list = list(deps)  # Convert if needed
       pass

   # Fix Option 2: Convert at call site
   self.format_dependencies(list(items))
   ```

2. **Lines 419-421:** Missing method definitions
   ```python
   # Add stub methods or implementations
   def get_awareness_expansion_path(self) -> str:
       return "path/to/awareness"

   def get_decision_making_enhancements(self) -> str:
       return "enhancements"

   def get_creative_problem_solving_approach(self) -> str:
       return "approach"
   ```

3. **Lines 450, 452, 453:** `Sequence[str]` has no `.split()` method
   ```python
   # Current
   items: Sequence[str] = ...
   parts = items.split(",")  # ERROR: Sequence doesn't have split

   # Fix: items is probably a string, not Sequence
   items: str = ...
   parts = items.split(",")  # OK
   ```

4. **Lines 648, 655:** Returning `Sequence[str]` instead of `str`
   ```python
   # Current
   def get_description(self) -> str:
       return some_list  # ERROR: returns Sequence

   # Fix
   def get_description(self) -> str:
       return "\n".join(some_list)  # Convert to string
   ```

---

### File 3: [src/memory/memory_palace.py](src/memory/memory_palace.py)
**Errors:** 5 (lines 20, 23, 29, 44)

#### Issues:
1. **Line 23:** Variable `tags` redefined
   ```python
   # Line 20
   tags = ["tag1", "tag2"]
   # Line 23
   tags = process_tags(tags)  # Redefining

   # Fix: Use different name or augment
   processed_tags = process_tags(tags)
   ```

2. **Line 29:** Argument type mismatch
   ```python
   # Current
   def _organize_into_clusters(self, items: list[str]) -> None:
       pass

   # Caller
   tags: list[str] | None = get_tags()
   self._organize_into_clusters(tags)  # ERROR: might be None

   # Fix
   if tags is not None:
       self._organize_into_clusters(tags)
   ```

3. **Line 44:** Returning `Any`
   ```python
   # Add type annotation
   def get_related_memories(self) -> list[str]:
       return result  # type: ignore[no-any-return] if needed
   ```

---

### File 4: [src/integration/cross_repo_sync.py](src/integration/cross_repo_sync.py)
**Errors:** 7 (lines 138, 146, 157, 180, 182, 187, 189)

#### Issue: All errors are `Sequence[str].append()` - immutable type

```python
# Current
def process_items(self, items: Sequence[str]) -> None:
    items.append("new")  # ERROR: Sequence is immutable

# Fix: Change signature to list
def process_items(self, items: list[str]) -> None:
    items.append("new")  # OK
```

---

### File 5: [src/system/system_snapshot_generator.py](src/system/system_snapshot_generator.py)
**Errors:** 10 (lines 36, 49, 50, 59×2, 172, 178, 179, 198, 294)

#### Issues are complex Union types - defer to Stage 9 for thoroughness

---

### Stage 8 Execution Checklist:
- [ ] Fix `github_instructions_enhancer.py` (15 errors)
- [ ] Fix `enhanced_directory_context_generator.py` (12 errors)
- [ ] Fix `memory_palace.py` (5 errors)
- [ ] Fix `cross_repo_sync.py` (7 errors)
- [ ] Run `black src/utils src/memory src/integration`
- [ ] Verify with mypy
- [ ] Commit: `git commit -m "Stage 8: Fix utility & integration type errors - 25 XP"`

---

## Stage 9: Security & Integration Module Fixes
**Target:** 5 files, ~40 errors
**Priority:** ⚠️ Medium
**Estimated Time:** 35 minutes
**XP Reward:** 20 XP

### File 1: [src/security/secure_api_manager.py](src/security/secure_api_manager.py)
**Errors:** 6 (lines 59, 72, 95, 96, 111)

#### Issues: None checks for encryption
```python
# Line 59
api_key.encode()  # ERROR: api_key might be None

# Fix
if api_key is not None:
    encoded = api_key.encode()

# Line 72, 95, 111: self.cipher is None
def __init__(self):
    self.cipher: Fernet | None = self._initialize_cipher()

def encrypt_value(self, value: str) -> str:
    if self.cipher is None:
        raise ValueError("Cipher not initialized")
    return self.cipher.encrypt(value.encode()).decode()
```

---

### Files 2-5: Quick fixes following similar patterns
- `zero_token_bridge.py` - 3 errors (assignment type fixes)
- `quest_executor.py` - 2 errors (optional dict indexing)
- `contextual_memory.py` - 2 errors (optional datetime return)
- `health_restorer.py` - 5 errors (return type fixes)

---

## Stage 10: Cleanup & Quick Wins
**Target:** Batch fixes across 30+ files
**Priority:** 🟡 Low (High impact/effort ratio)
**Estimated Time:** 30 minutes
**XP Reward:** 15 XP

### Quick Win 1: Remove Unused Type Ignores (32 files)
```bash
# Find all unused ignores
ruff check src --select=UP --fix

# Or manually:
grep -r "# type: ignore" src/ | grep -E "unused-ignore"
# Remove those comments
```

### Quick Win 2: Add Missing Variable Annotations (50 top cases)
```bash
# Pattern to find
operations = {}
results = []

# Fix to
operations: dict[str, Any] = {}
results: list[str] = []
```

### Quick Win 3: Remove Unreachable Code (20 files)
```python
# Pattern
def validate() -> bool:
    if not valid:
        return False

    # This code is unreachable if above always returns
    return True  # Sometimes mypy thinks this is unreachable

# Fix: Ensure logic is correct or remove dead code
```

---

## Execution Summary

### Stage 7-10 Total Impact:
| Metric | Value |
|--------|-------|
| **Files Modified** | ~20 core files + 30 cleanup |
| **Errors Fixed** | ~180-200 (11-12%) |
| **Time Required** | 2-3 hours |
| **XP Earned** | 80 XP |
| **Commit Count** | 4 (one per stage) |

### Success Criteria:
- ✅ All Stage 7-10 files pass mypy
- ✅ No new errors introduced
- ✅ Code formatted with Black
- ✅ Test suite still passes (1,154 tests)
- ✅ 80 XP earned and logged

### Post-Stages Metrics:
- **Before:** 1,640 mypy errors
- **After:** ~1,440 mypy errors
- **Reduction:** 200 errors (12%)
- **Remaining work:** Stages 11-30 for full type safety

---

## Next Steps After Stage 10:
1. Run full mypy scan to validate reduction
2. Update `PHASE_2_COMPLETION_REPORT.md`
3. Push to remote repository
4. Proceed to Phase 3 (Steps 31-40) - Integration testing focus

---

**Created:** 2026-01-01
**Phase:** 2 (Steps 28-30)
**Status:** Ready for execution ✅
