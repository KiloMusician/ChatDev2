# Common AI Agent Gotchas

**Updated**: 2026-01-16
**Applies To**: All agents (Claude, Copilot, Codex)

---

## 1. Deleting Scaffolding

**What Happens**: Agent sees commented imports or "placeholder" files and deletes them for "cleanup"

**Why It's Wrong**: Those are intentional architecture for future expansion
- `src/blockchain/__init__.py` - Awaiting blockchain features
- `src/cloud/__init__.py` - Awaiting cloud integrations
- Commented imports in `__init__.py` - Strategic placeholders

**Correct Behavior**: Preserve all scaffolding. Only delete if explicitly broken or confirmed obsolete.

**Prevention**: System Brief Rule #2 - "Preserve existing architecture"

**Status**: ✅ Added to System Brief

---

## 2. Creating Duplicate Systems

**What Happens**: Agent creates new orchestrator/manager/coordinator when 5 already exist

**Why It's Wrong**: Creates fragmentation, confusion, and maintenance burden

**Examples**:
- Already have: MultiAIOrchestrator, UnifiedAIOrchestrator, agent_orchestration_hub
- Don't create: NewBetterOrchestrator, ImprovedAICoordinator

**Correct Behavior**:
1. Use existing systems
2. If inadequate, extend them
3. If broken, fix them

**Prevention**: Read AGENT_COORDINATION_MAP.md before creating coordination code

**Status**: ✅ In AGENT_COORDINATION_MAP.md

---

## 3. Using TODO Comments

**What Happens**: Agent adds `# TODO: fix this later` comments

**Why It's Wrong**: TODOs get lost, never tracked, never completed

**Correct Behavior**: Use quest system instead
```python
# DON'T: # TODO: Implement error handling
# DO:
from src.Rosetta_Quest_System.quest_engine import QuestEngine
engine = QuestEngine()
engine.add_quest("Implement error handling", "Add try/except in parse_config()")
```

**Prevention**: Rule candidate - ban TODO comments, require quests

**Status**: ⚠️ Needs rule creation

---

## 4. Ignoring quest_log.jsonl

**What Happens**: Agent starts fresh without checking existing work

**Why It's Wrong**: Duplicates effort, ignores context, breaks continuity

**Correct Behavior**:
1. Read quest_log.jsonl on startup
2. Check for in_progress quests
3. Continue existing work before starting new

**Prevention**: Agent orientation should enforce this

**Status**: ✅ In agent orientation workflow

---

## 5. Not Routing to Terminals

**What Happens**: Agent uses print() or generic logging

**Why It's Wrong**: Output goes to wrong terminal, chaos ensues

**Correct Behavior**: Use TerminalManager
```python
from src.system.terminal_manager import TerminalManager
tm = TerminalManager()
tm.route_output("Claude", "Starting task...")
```

**Prevention**: Enforce in System Brief

**Status**: ✅ TerminalManager exists, needs enforcement

---

## 6. Bypassing Orchestrator

**What Happens**: Agent calls Ollama/ChatDev directly instead of using orchestrator

**Why It's Wrong**: Breaks routing, logging, coordination

**Correct Behavior**: Always route through MultiAIOrchestrator
```python
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
orchestrator = MultiAIOrchestrator()
orchestrator.orchestrate_task(...)
```

**Prevention**: In AGENT_COORDINATION_MAP.md

**Status**: ✅ Documented

---

## 7. Creating New Config Files

**What Happens**: Agent creates `my_config.yaml` when `settings.json` exists

**Why It's Wrong**: Fragments configuration, creates inconsistency

**Correct Behavior**: Use existing config system
- `config/settings.json` - Main settings
- `config/secrets.json` - Sensitive data
- `.env` - Environment variables

**Prevention**: Check existing configs first

**Status**: ⚠️ Needs documentation

---

## 8. Overwriting State Files

**What Happens**: Agent reinitializes `terminal_config.json` or `lifecycle_state.json`

**Why It's Wrong**: Loses persistent state, breaks tracking

**Correct Behavior**: Append/update, never overwrite entire file

**Prevention**: State managers handle this, use them

**Status**: ✅ Managers exist

---

## 9. Verbose Explanations in Code

**What Happens**: Agent adds essay-length docstrings explaining obvious code

**Why It's Wrong**: Bloats codebase, wastes time, hard to maintain

**Correct Behavior**: Concise docstrings for public APIs only

**Prevention**: Code review, style guide

**Status**: ⚠️ Agent-specific (Claude tends to do this)

---

## 10. Not Testing Changes

**What Happens**: Agent makes changes without running tests

**Why It's Wrong**: Breaks working code, creates regression

**Correct Behavior**:
```bash
# After any change
python -m pytest tests/
python -m ruff check .
```

**Prevention**: Make testing mandatory in workflow

**Status**: ✅ Test suite exists (99.7% passing)

---

## Adding New Gotchas

When you discover a new common mistake:
1. Log to `insights.jsonl` immediately
2. Add section here with full details
3. Propose prevention mechanism
4. Consider rule creation in `.cursor/rules/`

Format:
```markdown
## N. Gotcha Title

**What Happens**: Description
**Why It's Wrong**: Impact
**Correct Behavior**: Solution
**Prevention**: How to catch
**Status**: Implementation status
```

---

**Meta**: This file is living documentation. Update it whenever agents make repeatable mistakes.
