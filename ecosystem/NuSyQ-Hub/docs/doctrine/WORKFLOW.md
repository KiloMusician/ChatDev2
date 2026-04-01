# Workflow — Standard Operating Procedures

**Purpose:** Reduce hesitation by defining how common tasks are performed.  
**Principle:** Explicit > implicit, reversible > irreversible, safe > fast

---

## Session Startup

1. **Check state persistence**
   ```bash
   # NuSyQ-Hub
   cat config/ZETA_PROGRESS_TRACKER.json
   ls docs/Agent-Sessions/SESSION_*.md | tail -1

   # SimulatedVerse
   git status -sb
   git stash list

   # NuSyQ Root
   cat knowledge-base.yaml | head -20
   ```

2. **Review last session log**
   - Read most recent `SESSION_*.md`
   - Check for open todos or blockers

3. **Confirm working tree state**
   - Each repo should be: clean, or have exactly one labeled stash, or show intentional WIP

4. **Set context anchors**
   - What phase are we in? (from ZETA tracker)
   - What's the immediate goal?
   - What constraints apply? (budget, time, risk tolerance)

---

## Repo Cleanup (Anti-Spiderweb)

**When:** Working tree has uncommitted changes  
**Goal:** Classify and commit in coherent chunks OR stash with clear label

### Step 1: Evidence Gathering
```bash
cd /path/to/repo
git status --short
git diff --stat
git ls-files -o --exclude-standard  # untracked files
```

### Step 2: Classification
Group files into:
- **REAL SOURCE** (keep, commit intentionally)
- **CONFIG** (review carefully, may keep)
- **GENERATED** (delete or ignore)
- **SECRETS** (never commit, ensure ignored)

### Step 3: Action
```bash
# Option A: Selective commit
git add -p packages/ src/ server/  # by logical group
git commit -m "feat(core): <summary>"

# Option B: Safe stash
git stash push -m "wip-YYYY-MM-DD-<description>" --include-untracked

# Option C: Delete generated
rm -rf receipts/ tmp_*/ *.log
git status  # confirm clean or intentional
```

### Step 4: Validation
```bash
git status -sb  # should be clean or one labeled stash
git log -3 --oneline  # verify commit quality if committed
```

---

## Making Changes (Safe Iteration)

### Before Any Edit
1. **Read first, edit second**
   - Understand current state
   - Locate exact change site
   - Confirm no merge conflicts

2. **Prove the diff**
   ```bash
   git diff <file>
   # OR in VS Code: Source Control → view diff
   ```

3. **Commit with evidence**
   ```
   feat(scope): <summary>

   What: <what changed>
   Why: <rationale>
   Verification: <commands run or tests passed>
   Risk: <LOW|MEDIUM|HIGH + explanation>
   ```

### After Any Edit
1. **Validate immediately**
   ```bash
   # Python
   python -m pytest tests -q
   ruff check .

   # TypeScript/Node
   npm run check
   npm test

   # Repo-specific
   python src/diagnostics/system_health_assessor.py
   ```

2. **Check for side effects**
   ```bash
   git status  # should show only intended changes
   git diff --stat  # confirm scope
   ```

---

## Commit Hygiene

### Size
- **Small > large**
- One logical change per commit
- If change affects >10 files, consider splitting

### Message
- **Header:** `<type>(<scope>): <summary>`
  - type: feat, fix, chore, refactor, docs, test
  - scope: module/area affected (optional)
  - summary: imperative, lowercase, no period, <50 chars

- **Body:** What + Why + Verification + Risk
  - What: concrete changes made
  - Why: rationale or context
  - Verification: commands run or proof of correctness
  - Risk: impact assessment

### Before Committing
```bash
git diff --cached  # review staged changes
git status  # confirm only intended files staged
```

### After Committing
```bash
git log -1 --stat  # verify commit contents
git show HEAD  # review full diff
```

---

## Stash Management

### When to Stash
- Switching context mid-work
- Need clean tree for operation
- Want to save exploratory changes

### How to Stash
```bash
# Descriptive label required
git stash push -m "wip-2025-12-23-<description>" --include-untracked
```

### Stash Recovery
```bash
# List stashes
git stash list

# Inspect before applying
git stash show --stat stash@{0}
git stash show -p stash@{0} | head -100

# Selective restore (DO NOT BLINDLY POP)
git restore --source=stash@{0} -- path/to/keep

# Drop when done
git stash drop stash@{0}
```

---

## Secret & Env File Management

### Rules (ABSOLUTE)
1. `.env` files NEVER committed
2. `.env.example` or `.env.template` for structure
3. Secrets in `config/secrets.json` (NuSyQ-Hub) — gitignored
4. API keys as environment variables when possible

### Verification
```bash
# Check if .env tracked (should return nothing)
git ls-files | grep "^\.env$"

# Check ignore rules
git check-ignore -v .env .env.local

# If .env was committed, remediate immediately
git rm --cached .env
git commit -m "chore(security): remove env file from tracking"
```

---

## Testing & Validation

### Fast Checks (Run Frequently)
```bash
# NuSyQ-Hub
python -m pytest tests -q
python scripts/lint_test_check.py

# SimulatedVerse
npm run check  # TypeScript
npm test

# NuSyQ Root
python -m pytest  # if tests exist
```

### Comprehensive Checks (Before Push or Major Milestone)
```bash
# NuSyQ-Hub
python -m pytest tests --cov=src --cov-report=term-missing
python src/diagnostics/system_health_assessor.py

# SimulatedVerse
npm run build
npm run lint

# Cross-repo
./scripts/full_ecosystem_check.sh  # if exists
```

---

## Session Closure

### Required Checklist
- [ ] All repos: clean working tree OR one labeled stash
- [ ] No uncommitted secrets
- [ ] Recent commits follow conventions
- [ ] Progress tracker updated (if major work done)
- [ ] Session log created (if significant session)

### State Capture
```bash
# Update progress tracker
vim config/ZETA_PROGRESS_TRACKER.json

# Create session log (if needed)
cat > docs/Agent-Sessions/SESSION_$(date +%Y%m%d_%H%M).md << 'EOF'
# Session: <brief title>
**Date:** $(date -I)
**Agent:** <Copilot|Claude|etc>
**Duration:** ~X min
**Goal:** <what was attempted>
**Outcome:** <what was achieved>
**Next:** <what remains>
**Artifacts:** <files created/updated>
EOF
```

### Final Verification
```bash
# Each repo
git status -sb
git stash list
git log -5 --oneline

# Confirm clean or intentional state
```

---

## Emergency Recovery

### If Lost or Confused
1. **Read state first**
   ```bash
   cat config/ZETA_PROGRESS_TRACKER.json
   ls -lt docs/Agent-Sessions/ | head -5
   cat src/Rosetta_Quest_System/quest_log.jsonl | tail -10
   ```

2. **Run health check**
   ```bash
   python src/diagnostics/system_health_assessor.py
   ```

3. **Use healing tools**
   ```bash
   python src/healing/repository_health_restorer.py
   python src/utils/quick_import_fix.py
   ```

4. **Consult doctrine**
   - Read `docs/doctrine/SYSTEM_OVERVIEW.md`
   - Read `docs/doctrine/DECISIONS.md`
   - Read this file

### If Something Broke
1. **Stop immediately** (do not compound)
2. **Gather evidence**
   ```bash
   git status
   git diff
   git log -10 --oneline
   ```
3. **Rollback if possible**
   ```bash
   git reset --soft HEAD~1  # undo last commit, keep changes
   git reset --hard HEAD~1  # undo last commit, discard changes
   git stash  # if working tree dirty
   ```
4. **Document failure**
   - What was attempted
   - What failed
   - Error messages
   - Steps to reproduce

---

## Agent-Specific Workflows

### Claude
1. Be invoked for: decisions, compression, abstraction
2. Output artifacts to: `docs/doctrine/`, decision records, policy files
3. Hand off to: Copilot (for execution), Ollama (for cheap iteration)

### Copilot
1. Be invoked for: file edits, commits, mechanical tasks
2. Always: show diff, follow conventions, validate after
3. Refuse if: instructions ambiguous, secrets detected, rules violated

### Ollama
1. Be invoked for: prompt testing, draft generation, cheap exploration
2. Feed results to: Claude (for compression), Copilot (for execution)
3. Never: make final authoritative decisions alone

### ChatDev
1. Be invoked for: design alternatives, tradeoff analysis, multi-role reasoning
2. Output: comparison tables, risk assessments, recommended paths
3. Hand off to: Claude (for decision), Copilot (for execution)

---

*Update this file when new patterns emerge or workflows stabilize.*
