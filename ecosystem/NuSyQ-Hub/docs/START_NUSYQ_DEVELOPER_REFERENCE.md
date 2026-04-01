# start_nusyq.py - Developer Quick Reference Card

## 🎯 Quick Status

| Metric | Value | Status |
|--------|-------|--------|
| **Mypy Errors** | ~30 | Baseline (brownfield) |
| **Production Impact** | None | ✅ Functionally sound |
| **Your Responsibility** | New code only | ⚠️ Don't inherit debt |

## 🚦 Patch Decision Tree

```
Are you adding/modifying code in start_nusyq.py?
│
├─ YES → Does your change introduce NEW mypy errors?
│   ├─ YES → ❌ Must fix before committing
│   └─ NO → ✅ Safe to commit
│       └─ Are you touching functions with EXISTING errors?
│           ├─ YES → 🎯 Opportunistic: Add type hints (30 sec)
│           └─ NO → ✅ Commit as-is
│
└─ NO → ✅ Not your concern
```

## 📋 Common Scenarios

### Scenario 1: Adding Factory Function Call
```python
# ✅ GOOD: Defensive against baseline errors
orchestrator = get_orchestrator()  # Returns Any (baseline)
if orchestrator is None:  # New code handles uncertainty
    return
orchestrator.run()  # Safe after None check

# ❌ BAD: Assumes type safety that doesn't exist
orchestrator = get_orchestrator()
orchestrator.run()  # Could crash if None
```

### Scenario 2: Wiring Orphaned Examples
```python
# ✅ GOOD: New code is fully typed
def run_example(example_id: int) -> bool:  # Type hints on new function
    """Run example by ID."""
    example = find_example(example_id)  # Baseline untyped, but we handle it
    if example is None:
        return False
    return execute_example(example)  # Defensive

# ❌ BAD: Propagating baseline issues
def run_example(example_id):  # No hints (adds to baseline)
    example = find_example(example_id)
    return execute_example(example)  # No safety checks
```

### Scenario 3: Adding Dashboard Integration
```python
# ✅ GOOD: Use type guards for dynamic attributes
if hasattr(dashboard, 'render_agents'):  # Guard against attr-defined
    dashboard.render_agents(agents)
else:
    print("Dashboard missing render_agents method")

# ❌ BAD: Assume attribute exists
dashboard.render_agents(agents)  # Baseline error propagates
```

## 🎓 When to Use `# type: ignore`

### ✅ Legitimate Uses
```python
# Baseline brownfield debt (documented)
config = json.load(f)  # type: ignore[no-any-return]  # Pre-existing, see MYPY_BASELINE.md

# Third-party library without stubs
import some_untyped_lib  # type: ignore[import]

# Dynamic runtime behavior
result = getattr(obj, method_name)()  # type: ignore[misc]  # Method name from user input
```

### ❌ Code Smells
```python
# Lazy type avoidance - should fix
def process_data(data): # type: ignore[no-untyped-def]  # Just add '-> None'!
    pass

# Hiding real bugs
user.email.send()  # type: ignore[attr-defined]  # Email might not exist!

# Daisy-chaining ignores
result = func()  # type: ignore[no-any-return]
processed = transform(result)  # type: ignore[arg-type]
final = save(processed)  # type: ignore[no-any-return]
# ^ This is a cry for help, add proper types
```

## 📊 Baseline Categories at a Glance

| Error Code | Count | Priority | Fix Time | Example |
|------------|-------|----------|----------|---------|
| `no-untyped-def` | ~10 | P3 | 10 sec | `def func(x):` → `def func(x: int) -> None:` |
| `no-any-return` | ~8 | P2 | 2 min | Add `TypedDict` for JSON |
| `attr-defined` | ~5 | P1 | 1 min | Add `hasattr()` check |
| `truthy-function` | ~3 | P1 | 5 sec | `if func:` → `if func():` |
| `unused-ignore` | ~3 | P3 | 2 sec | Delete the comment |
| `union-attr` | ~1 | P2 | 30 sec | Add type narrowing |

**Total:** ~30 errors, **0 blocking production**

## 🏗️ Contribution Guidelines

### Before Committing
1. Run `mypy scripts/start_nusyq.py --show-error-codes`
2. Check error count: Should still be ~30 (not increased)
3. Any new errors? → Must fix them
4. Touched function with baseline error? → Consider adding type hints (optional)

### Commit Message Template
```
feat: Wire get_orchestrator factory into action_menu

- Added defensive None check for orchestrator
- Preserves existing mypy baseline (~30 errors unchanged)
- New code fully typed with error handling

Baseline errors on line 145 (no-untyped-def) remain - 
tracked in docs/MYPY_BASELINE_START_NUSYQ.md
```

### Code Review Checklist
- [ ] No new mypy errors introduced
- [ ] New code has type hints
- [ ] Baseline errors documented if triggering them
- [ ] Used defensive programming for uncertain types

## 🎯 Opportunistic Wins (5 Minutes)

If you're already in the file, these quick fixes help future maintainers:

```python
# LOW-HANGING FRUIT (~2 seconds each)
if get_orchestrator:  # [truthy-function]
if get_orchestrator():  # ✅ Fixed

result = call_api()  # type: ignore[no-any-return]  # Actually fine now
result = call_api()  # ✅ Removed stale ignore

# EASY TYPING (~10 seconds)
def action_menu():  # [no-untyped-def]
def action_menu() -> None:  # ✅ Fixed

# REQUIRES THOUGHT (~2 minutes)
config = json.load(f)  # Returns Any
# Add TypedDict:
class Config(TypedDict):
    version: str
    features: dict[str, bool]
config: Config = json.load(f)  # ✅ Typed
```

## 📚 Reference Documentation

- **Full Baseline Analysis:** `docs/MYPY_BASELINE_START_NUSYQ.md`
- **Assessment Tool:** `scripts/mypy_baseline_assessment.py`
- **Modernization Plan:** Part of orphan symbol rehabilitation
- **Culture Ship Quest:** "Type Safety Campaign" (future)

## 🆘 When In Doubt

**Q:** My patch triggers 5 mypy errors, but on lines I didn't touch!  
**A:** Baseline debt inheritance. Document in commit, no action needed.

**Q:** Should I fix baseline errors while I'm here?  
**A:** Encouraged but optional. Don't let it block your PR.

**Q:** This baseline documentation seems wrong!  
**A:** Run `python scripts/mypy_baseline_assessment.py` to regenerate.

**Q:** CI fails on mypy but I didn't add errors!  
**A:** Check if baseline count increased. If unchanged, CI config issue.

---

**Last Updated:** 2026-02-17 (Pre-orphan modernization)  
**Baseline:** ~30 errors, stable and non-blocking  
**Your Safe Zone:** Add new typed code, ignore inherited baseline
