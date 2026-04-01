description: File preservation mandate for Copilot and NuSyQ-Hub
applyTo: '**/*'

# File Preservation Mandate

This file mandates preservation of critical files for Copilot and NuSyQ-Hub integration.

## Core Principle: Edit-First, Create-Last

**Tell the agent: "Fix [issue]" or "Add [feature]"**

Agent MUST follow this hierarchy:
1. **Search for existing implementation** - Use `grep_search`, `semantic_search`, `file_search` to find related code
2. **Enhance existing files** - Modify existing modules instead of creating new ones
3. **Create only when necessary** - New files ONLY if no suitable existing location exists
4. **Consolidate duplicates** - If similar files exist, merge instead of creating third variant

**Evidence Required:**
- Agent must cite ≥6 specific file paths from repository showing search attempt before new file creation
- Reference `docs/SYSTEM_MAP.md` canonical directory structure
- Check `src/Rosetta_Quest_System/quest_log.jsonl` for related past work

## Anti-Bloat Rules

### Forbidden Patterns
**Tell the agent to AVOID:**
- Creating `new_[thing].py` when `[thing].py` exists
- Duplicating functionality across multiple files
- Abstract base classes with single implementation
- Wrapper modules that only import and re-export
- "Utils" or "helpers" proliferation (use existing `src/utils/`)
- Abandoned prototypes in canonical locations (use Testing Chamber)

### Mandatory Cleanup
**Tell the agent: "Clean up abandoned code"**

Agent identifies and removes:
- Files with `TODO`, `FIXME`, `DEPRECATED` older than 90 days
- Duplicate files (same name, different directory)
- Unused imports (via ruff)
- Dead code (no references via `grep_search`)

**Process:**
1. Run `python scripts/lint_test_check.py` to find violations
2. Use `src/healing/repository_health_restorer.py` for path repairs
3. Log cleanup to `src/Rosetta_Quest_System/quest_log.jsonl`
4. Commit with conventional commit message: `chore: remove abandoned [files]`

## Runtime Exhaust vs. Curated Knowledge

### Runtime Exhaust (Ephemeral - OK to delete)
**Locations:** `state/reports/`, `logs/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.log`

**Purpose:** Debugging, troubleshooting, transient state

**Retention:** 30 days maximum, auto-purge OK

**Examples:**
- `state/reports/snapshot_TIMESTAMP.md` - System state snapshots
- `logs/system_health_status.json` - Health check results
- `logs/orchestration_TIMESTAMP.log` - Runtime logs

### Curated Knowledge (Persistent - NEVER delete without review)
**Locations:** `docs/`, `config/`, `src/Rosetta_Quest_System/`, `.github/instructions/`

**Purpose:** Persistent intelligence, system memory, doctrine

**Retention:** Permanent until explicitly deprecated

**Examples:**
- `src/Rosetta_Quest_System/quest_log.jsonl` - Quest history and decisions
- `config/ZETA_PROGRESS_TRACKER.json` - Development milestones
- `docs/SYSTEM_MAP.md`, `docs/ROUTING_RULES.md`, `docs/OPERATIONS.md` - Canonical doctrine
- `.github/instructions/*.instructions.md` - Copilot behavioral instructions
- `AGENTS.md` - Agent navigation and recovery protocol

## Critical Files (NEVER delete or move)

**Tell the agent: "These files are sacred infrastructure"**

**NuSyQ-Hub (Oldest House/Spine/Brain):**
- `scripts/start_nusyq.py` - System orchestrator entrypoint
- `scripts/start_system.ps1` - Health check script
- `src/tools/agent_task_router.py` - Conversational task routing
- `src/orchestration/multi_ai_orchestrator.py` - Multi-AI coordination
- `src/healing/quantum_problem_resolver.py` - Self-healing system
- `AGENTS.md` - Agent navigation protocol
- `.github/copilot-instructions.md` - High-level Copilot contract
- All `.github/instructions/*.instructions.md` files

**Quest/Progress System:**
- `src/Rosetta_Quest_System/quest_log.jsonl`
- `config/ZETA_PROGRESS_TRACKER.json`
- `docs/Checklists/PROJECT_STATUS_CHECKLIST.md`

**Foundation Docs:**
- `docs/SYSTEM_MAP.md`
- `docs/ROUTING_RULES.md`
- `docs/OPERATIONS.md`
- `README.md`

**Configuration:**
- `config/secrets.json` (template, not actual secrets)
- `config/feature_flags.json`
- `.vscode/tasks.json`

## Modification Protocol

**Before editing critical files:**
1. Read full file (not just snippets)
2. Understand purpose and dependencies
3. Make surgical edits (not rewrites)
4. Preserve existing comments and docstrings
5. Run `python scripts/lint_test_check.py`
6. Commit with detailed conventional commit message

**Before deleting ANY file:**
1. Search for references: `grep_search` for filename
2. Check import dependencies
3. Verify not in critical files list above
4. Log deletion reason to quest_log.jsonl
5. Use `git rm` (not manual delete) for audit trail

**Reference:** [ROUTING_RULES.md](../../docs/ROUTING_RULES.md) for commit boundaries and verification defaults.
