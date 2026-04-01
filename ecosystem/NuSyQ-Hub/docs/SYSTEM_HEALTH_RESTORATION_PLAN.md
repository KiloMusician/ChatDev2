# System Health Restoration Plan

## Generated: 2025-12-30 by GitHub Copilot Deep Analysis

### 🚨 **CRITICAL: DO THESE FIRST** (30 minutes)

#### 1. Fix Configuration Gaps (10 min)

```powershell
# Check what's actually missing
python -c "from src.setup.secrets import config; import json; secrets = config._secrets; missing = [];
for service in ['openai', 'anthropic', 'github']:
    for key in ['api_key', 'token']:
        val = secrets.get(service, {}).get(key if key == 'token' else 'api_key');
        if val and 'REDACTED' in str(val):
            missing.append(f'{service}.{key}');
print('Missing credentials:', missing if missing else 'None - all configured!')"

# If missing, see docs/CONFIGURATION_GUIDE.md for setup
```

#### 2. Verify Ollama Port (5 min)

```powershell
# Test if Ollama is actually running
curl http://localhost:11434/api/version

# If fails, start Ollama or fix port in config
$env:OLLAMA_HOST = "http://localhost:11434"
```

#### 3. Run Full Test Suite (10 min)

```powershell
# Ensure nothing broke
python -m pytest tests/ -v --tb=short -x

# If failures, prioritize fixing those before continuing
```

#### 4. Clean Lint Errors (5 min)

```powershell
# Auto-fix what can be fixed
ruff check src/ --fix
black src/ --line-length=100

# Re-check
ruff check src/ | Select-Object -First 20
```

---

### ⚠️ **HIGH PRIORITY: DO THESE TODAY** (1-2 hours)

#### 5. Implement Critical TODOs (30 min)

Target the 6 integration TODOs in `multi_ai_orchestrator.py`:

```powershell
# Create a quest for each TODO
python scripts/start_nusyq.py generate_quests_from_todos src/orchestration/multi_ai_orchestrator.py
```

**Or manually implement top 3:**

1. Ollama API integration (already have URL/port, just wire it up)
2. Copilot API integration (VS Code extension installed, need protocol)
3. ChatDev API integration (path configured in secrets.json)

#### 6. Resolve File Duplicates (20 min)

Follow `docs/FILE_DEDUPLICATION_PLAN.md`:

```powershell
# Start with highest priority: modular_logging_system.py (4 copies)
python scripts/deduplicate_files.py --file modular_logging_system.py --dry-run

# Review plan, then execute
python scripts/deduplicate_files.py --file modular_logging_system.py --execute
```

#### 7. Commit Working Tree (20 min)

```powershell
# Create meaningful commits
git status | Select-Object -First 30  # Review changes
git add config/ docs/ scripts/  # Add documentation/tooling first
git commit -m "docs: add configuration guide and system health restoration plan"

git add src/tools/agent_task_router.py src/ai/ai_intermediary.py  # Core fixes
git commit -m "fix: resolve type errors in agent routing and AI intermediary"

git add tests/  # Test updates
git commit -m "test: increase timeouts and add integration coverage"

# Continue for other logical groups
```

#### 8. Add Missing Type Hints (30 min)

Focus on the 30 mypy warnings:

```powershell
# Get list of files with most warnings
mypy src/ --no-error-summary 2>&1 | Select-String "\.py:" | Group-Object {$_ -replace ':.*', ''} | Sort-Object Count -Descending | Select-Object -First 10

# Add type hints to top 3 files
# Example pattern:
# def my_function(arg1, arg2):  # Before
# def my_function(arg1: str, arg2: int) -> dict[str, Any]:  # After
```

---

### 📋 **MEDIUM PRIORITY: DO THIS WEEK** (2-4 hours)

#### 9. Test Performance Optimization (30 min)

```powershell
# Profile slow tests
python -m pytest tests/ --durations=10

# Optimize slowest tests (likely test_help_output timeout increase was a symptom)
```

#### 10. Documentation Currency Check (1 hour)

```powershell
# Find docs referencing old patterns
grep -r "REDACTED" docs/
grep -r "TODO" docs/ | wc -l

# Update or archive outdated docs
```

#### 11. Dependency Audit (30 min)

```powershell
# Check for outdated packages
pip list --outdated

# Security vulnerabilities
pip-audit

# Update critical ones
pip install --upgrade <package>
```

#### 12. SimulatedVerse Branch Cleanup (30 min)

```powershell
cd C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse

# Check what codex/prefer-simverse-python-bin has
git log --oneline origin/main..HEAD

# If mergeable, push or create PR
git push --set-upstream origin codex/prefer-simverse-python-bin
```

---

### 🔄 **CONTINUOUS: BUILD THESE HABITS**

#### 13. Pre-Commit Checks

```powershell
# Add to .git/hooks/pre-commit
black src/ --check
ruff check src/
mypy src/ --no-error-summary
pytest tests/test_*.py -x -q
```

#### 14. Daily Health Check

```powershell
# Run every morning
python scripts/quick_status.py
python scripts/start_nusyq.py brief
```

#### 15. Weekly TODO Review

```powershell
# Every Monday
python -c "from pathlib import Path; todos = [];
for f in Path('src').rglob('*.py'):
    with open(f, encoding='utf-8') as fp:
        for i, line in enumerate(fp, 1):
            if 'TODO' in line.upper():
                todos.append(f'{f}:{i}');
print(f'Total TODOs: {len(todos)}'); [print(t) for t in todos[:20]]"

# Convert top 5 to quests
```

---

### 🎯 **SUCCESS METRICS**

**After 1 day:**

- [ ] All tests passing
- [ ] Lint errors < 25 (down from 38)
- [ ] API keys configured (or documented why not needed)
- [ ] Working tree < 10 uncommitted files

**After 1 week:**

- [ ] Lint errors < 15
- [ ] All critical TODOs resolved or in quest system
- [ ] File duplicates down to 0-1
- [ ] All 3 repos synced with remote

**After 1 month:**

- [ ] Lint errors < 5
- [ ] 90%+ test coverage
- [ ] Zero REDACTED placeholders
- [ ] Automated pre-commit hooks active

---

## 🧭 **NAVIGATION AIDS**

**If stuck, run:**

```powershell
python scripts/start_nusyq.py doctor  # Full diagnostics
python src/diagnostics/system_health_assessor.py  # Health roadmap
python src/healing/quantum_problem_resolver.py  # Advanced healing
```

**For context restoration:**

- Check `docs/Agent-Sessions/SESSION_*.md` for breadcrumbs
- Review `config/ZETA_PROGRESS_TRACKER.json` for phase state
- Read `src/Rosetta_Quest_System/quest_log.jsonl` for quest history
