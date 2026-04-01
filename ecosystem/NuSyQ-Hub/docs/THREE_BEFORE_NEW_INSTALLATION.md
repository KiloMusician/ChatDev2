# Three Before New Protocol - Installation & Quick Reference

## 🎯 Purpose

Stop brownfield pollution by forcing agents to discover existing tools before
creating duplicates.

## 📦 Installation

### 1. Discovery Tool (Already Installed)

```bash
# Test discovery
python scripts/find_existing_tool.py --capability "error reporting" --max-results 5
```

### 2. Pre-Commit Hook (Optional but Recommended)

```bash
# Windows PowerShell
cd .git/hooks
New-Item -ItemType SymbolicLink -Path "pre-commit" -Target "..\..\scripts\three_before_new_precommit_hook.py"

# Linux/Mac
cd .git/hooks
ln -s ../../scripts/three_before_new_precommit_hook.py pre-commit
chmod +x pre-commit
```

**Warn-only mode** (during transition period):

```bash
# PowerShell
$env:TBN_WARN_ONLY = "1"
git commit -m "test"

# Bash
TBN_WARN_ONLY=1 git commit -m "test"
```

### 3. Metrics Dashboard (Already Installed)

```bash
# View current compliance metrics
python scripts/ecosystem_health_dashboard.py

# 30-day view
python scripts/ecosystem_health_dashboard.py --days 30

# JSON output for automation
python scripts/ecosystem_health_dashboard.py --json
```

## 🚀 Quick Reference

### For AI Agents (Copilot, Claude, etc.)

**Before creating ANY new script/tool/utility:**

```bash
python scripts/find_existing_tool.py --capability "your capability here" --max-results 3
```

**Required workflow:**

1. Run discovery → identify 3 candidates
2. Assess candidates → can you extend/combine/modernize?
3. If no fit → document why in quest log
4. Proceed with creation only after step 3

### For Humans

Check `.github/copilot-instructions.md` for the full protocol:

- See "Brownfield Guardrail: Three Before New" section
- Review `docs/THREE_BEFORE_NEW_PROTOCOL.md` for complete rules

### Command Examples

```bash
# Find existing error reporting tools
python scripts/find_existing_tool.py --capability "error reporting" --max-results 5

# Find test runners
python scripts/find_existing_tool.py --capability "test runner" --max-results 3

# Find import fixers
python scripts/find_existing_tool.py --capability "import fixing" --json

# Check compliance health
python scripts/ecosystem_health_dashboard.py --days 60
```

## 📊 Current Status

As of implementation (Dec 2025):

- **314 tools created in 60 days**
- **0% compliance rate** (pre-protocol baseline)
- **Target: 70%+ compliance within 30 days**

## 🔧 Troubleshooting

### Hook not running?

```bash
# Check symlink exists
ls -la .git/hooks/pre-commit

# Test manually
python scripts/three_before_new_audit.py --warn-only
```

### Discovery not finding tools?

```bash
# Check search directories in scripts/find_existing_tool.py
# Default: scripts/, src/tools/, src/utils/, src/diagnostics/, src/healing/, docs/, config/, deploy/, web/
```

### Quest log integration not working?

```python
from src.Rosetta_Quest_System.quest_engine import log_three_before_new

log_three_before_new(
    tool_name="my_new_tool.py",
    capability="my capability",
    candidates=["tool1.py", "tool2.py", "tool3.py"],
    justification="These tools didn't fit because..."
)
```

## 📚 Reference Files

- Protocol document:
  [docs/THREE_BEFORE_NEW_PROTOCOL.md](../docs/THREE_BEFORE_NEW_PROTOCOL.md)
- Discovery tool: [scripts/find_existing_tool.py](find_existing_tool.py)
- Pre-commit audit:
  [scripts/three_before_new_audit.py](three_before_new_audit.py)
- Pre-commit hook:
  [scripts/three_before_new_precommit_hook.py](three_before_new_precommit_hook.py)
- Metrics dashboard:
  [scripts/ecosystem_health_dashboard.py](ecosystem_health_dashboard.py)
- Quest log integration:
  [src/Rosetta_Quest_System/quest_engine.py](../src/Rosetta_Quest_System/quest_engine.py)

## 🎓 Philosophy

> "In a brownfield codebase, the highest-leverage action is often **not creating
> something new**, but rather **discovering and enhancing what already exists**.
> The Three Before New protocol enforces this discipline."

**Expected outcomes:**

- 70% reduction in duplicate tool creation
- Improved tool quality (focus on enhancement vs greenfield)
- Better codebase discoverability
- Reduced cognitive load for new contributors
