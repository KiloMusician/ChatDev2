# Zero-Token Ops Playbook

> **Principle**: Maximize deterministic operations before using any LLM tokens.

This playbook teaches DevMentor (and any agent IDE) how to extract maximum value from zero-cost operations before engaging expensive reasoning.

## The Efficiency Hierarchy

1. **Purely deterministic checks** (fast, no model): lint, format, syntax, tests, dependency graph, dead-code detection
2. **Cached / incremental computation**: only re-check changed files, reuse prior results
3. **Local computation**: small scripts for classification/summarization
4. **Remote LLM**: only when deterministic steps can't decide

DevMentor forces this order.

## The Ops Core Commands

Run everything through a single orchestrator:

```bash
python scripts/devmentor_ops.py <command>
```

### Available Commands

| Command | Purpose | Artifacts |
|---------|---------|-----------|
| `doctor` | Environment + dependency + config sanity | `reports/doctor.json` |
| `check` | Lint + syntax + health checks | `reports/check.json` |
| `fix` | Auto-fix what can be fixed | `reports/fix.json` |
| `prune` | Detect bloat, duplicates, large files | `reports/prune.json` |
| `graph` | Generate module/file map | `reports/module_map.json` |
| `export` | Build portable ZIP | `exports/devmentor-portable.zip` |
| `report` | Generate markdown status report | `reports/latest.md` |
| `all` | Run all operations in sequence | All artifacts |

## Artifacts-First Workflow

Instead of asking an LLM:
> "Please debug the repo"

Run:
```bash
python scripts/devmentor_ops.py doctor
python scripts/devmentor_ops.py check
python scripts/devmentor_ops.py report
```

Then the agent reads:
- `reports/doctor.json`
- `reports/check.json`
- `reports/latest.md`

Now the model only needs to:
1. Interpret results
2. Choose next patch
3. Apply minimal changes

That's "bang for buck".

## The Golden Pattern: Evidence Packets

Every operation outputs:
- What ran
- What failed
- Where
- How to reproduce
- Suggested next actions

Files:
- `reports/latest.json` (machine-readable)
- `reports/latest.md` (human-readable)
- `reports/module_map.json` (codebase structure)

## Token Discipline Rules

Teach agents these defaults:

1. **Never ask the model before running** `ops doctor` + `ops check`
2. **Never propose changes** without a failing test or error output
3. **Never refactor** without a `reports/module_map.json`
4. **Prefer autofixers** (`ops fix`) over LLM edits
5. **When LLM is used**, patch the smallest surface area possible
6. **After every patch**: re-run `ops check` to verify

## Before Any LLM Reasoning

- [ ] Run `ops doctor`
- [ ] Run `ops check`
- [ ] Read `reports/latest.md`

## Before Any Refactor

- [ ] Generate module map: `ops graph`
- [ ] Confirm invariant list exists
- [ ] Confirm tests exist or create minimal ones

## Before Adding Files

- [ ] Check if existing module can host it
- [ ] Confirm new file has an owner + purpose
- [ ] Confirm docs update path

## After Changes

- [ ] Run `ops check`
- [ ] Update report: `ops report`
- [ ] Export zip (if portability impacted): `ops export`

## The CHUG Engine v2.0 (7-Phase Cycle)

The CHUG Engine runs a complete 7-phase improvement cycle:

```bash
python chug_engine.py              # Run one full cycle
python chug_engine.py --loop       # Run continuously
python chug_engine.py --status     # Show current state
python chug_engine.py --phase N    # Run specific phase (1-7)
```

### The 7 Phases

| Phase | Name | Purpose | Output |
|-------|------|---------|--------|
| 1 | ASSESS | Zero-token health snapshot | `reports/health.json` |
| 2 | PLAN | Surgical improvement bullets (≤7) | `reports/plan.md` |
| 3 | EXECUTE | Apply changes with modularity | Fixes applied |
| 4 | VERIFY | Prove everything still works | `reports/verify.json` |
| 5 | CONSOLIDATE | Reduce bloat, clean caches | `reports/consolidate.json` |
| 6 | DOCUMENT | Update docs to match reality | `reports/tree.md`, `reports/chug_status.md` |
| 7 | EXPORT | Portability gate validation | `reports/export.json` |

### Phase Flow

```
ASSESS → PLAN → EXECUTE → VERIFY → CONSOLIDATE → DOCUMENT → EXPORT
   ↓        ↓       ↓         ↓          ↓           ↓         ↓
health  bullets  fixes    verify    cleanup      tree.md    ZIP ok?
```

### CHUG State

The engine maintains persistent state in `.devmentor/chug_state.json`:
- Cycles completed
- Total issues found/fixed
- Consecutive clean cycles
- History of recent cycles

## The CHUG-0 Micro-Prompt

Ultra low-token version for agents:

```
Run: python scripts/devmentor_ops.py all
Read: reports/latest.md
Apply the smallest patch that fixes the top failure.
Re-run: python scripts/devmentor_ops.py check
Repeat until clean.
Do not add new features while failures exist.
```

## Agent Compression Protocol

When the model must speak, use this structure:

```
Observed: (paste exact failing line / file / stack)
Cause guess: (1 sentence)
Patch: (exact file edits)
Verification: (ops check result)
Next: (1–3 bullets)
```

This keeps reasoning tight and reduces follow-up tokens.

## Integration with VS Code

All ops commands are available as VS Code tasks:

1. Open Command Palette (`Cmd/Ctrl+Shift+P`)
2. Type "Run Task"
3. Select any "DevMentor: Ops *" task

## Integration with Replit

On Replit boot:
1. `ops doctor` runs automatically (via status checks)
2. `reports/latest.md` + "next actions" are generated
3. The model never asks what to do until these exist
