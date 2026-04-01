# Phase 2: CI/CD Enforcement & Auto-Merge Architecture

## Overview

Phase 2 implements automated code quality gates and risk-based auto-merging to enable safe autonomous development. This system builds on the closed-loop autonomy created in Phase 1A.

**Key Goals:**
- ✅ Enforce code quality standards automatically (lint, type-check, test, security)
- ✅ Enable safe autonomous merging for low-risk changes (score < 0.3)
- ✅ Route medium-risk changes to human review
- ✅ Block critical-risk changes until approved
- ✅ Protect critical paths via CODEOWNERS
- ✅ Provide transparent governance with detailed PR comments

## Architecture

### 1. GitHub Actions Workflows

#### Flow Diagram
```
PR Created/Updated
    ↓
[autonomy-gates.yml] ← Run on every PR and push
    ├─ Lint (ruff, black)
    ├─ Type Check (mypy)
    ├─ Test Suite (pytest)
    └─ Security Scan (bandit)
    ↓
Success? YES ↓ NO → Comment: "❌ Check Failed"
    ↓
[autonomy-merge.yml] ← Triggered after gates pass
    ├─ Extract Risk Metadata (from PR body)
    ├─ Evaluate Auto-Merge Eligibility
    │  └─ Risk Score < 0.3? AND All Checks Pass? AND Created by Bot?
    ├─ LOW-RISK → Auto-Merge (squash)
    ├─ MEDIUM-RISK → Comment: "⏳ Requires Review"
    ├─ HIGH-RISK → Comment: "⚠️ REQUIRES REVIEW + Approval"
    └─ CRITICAL-RISK → Comment: "❌ BLOCKED - Manual Approval"
    ↓
Merged (or blocked for review)
```

### 2. Workflow Files

#### **autonomy-gates.yml** - Code Quality Enforcement
**Trigger:** Every PR and push to master

**Checks:**
1. **Ruff Linting** - E, W, F rules (errors, warnings, fixes)
2. **Black Format Check** - Code style consistency
3. **MyPy Type Checking** - Static type validation
4. **Pytest Tests** - Full test suite with coverage reporting
5. **Bandit Security Scan** - Security vulnerability detection

**Output:**
- Individual check status (✓ or ✗)
- Summary comment on PR with all results
- GitHub Actions check status for branch protection
- Coverage report (if tests pass)

**Failure Behavior:**
- If any check fails, subsequent checks still run (for visibility)
- PR is marked as "Checks Failed"
- Autonomy-merge workflow doesn't trigger merging

#### **autonomy-merge.yml** - Risk-Based Auto-Merge
**Trigger:** After autonomy-gates completes

**Steps:**
1. Extract risk metadata from PR body
   - Risk Score (float: 0.0-1.0)
   - Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
   - Approval Policy (AUTO, REVIEW, PROPOSAL, BLOCKED)

2. Check all status checks
   - Verify autonomy-gates completed successfully
   - Verify all required checks passed

3. Evaluate merge eligibility
   ```
   Auto-Merge if:
   - Risk Score < 0.3 (LOW)
   - AND all checks pass
   - AND PR created by autonomy bot (github-actions[bot] or agent/*)
   ```

4. Apply merge method
   - **AUTO**: Squash merge immediately
   - **REVIEW**: Create comment requesting human review
   - **PROPOSAL**: Create proposal package (future: GitHub Discussions)
   - **BLOCKED**: Block merge, require explicit approval

**Output:**
- PR comment with governance decision
- Auto-merge applied (if eligible)
- Status tracked for metrics

### 3. Risk Scoring System

Risk scoring is performed by the autonomy system (src/autonomy/risk_scorer.py) during PR creation. The score determines governance policy.

#### Risk Factors
```
Base Score: 0.0

File Count:
  - +0.05 per file (capped at 0.4)

Critical Path Files (+0.3 each):
  - src/orchestration/
  - src/autonomy/
  - src/healing/
  - src/main.py
  - config/

Deletions (+0.2 per deletion)

Test Results:
  - Test Failures: ×1.3 multiplier
  - Test Passes: ×0.7 reduction

Code Metrics:
  - Cyclomatic complexity > 10: +0.1
  - Functions > 50 lines: +0.05 per function
  - Missing type hints: +0.05

Final Score: Sum of factors (capped at 1.0)
```

#### Risk Levels
```
Risk Score Range    | Level      | Approval Policy | Action
-------------------|------------|-----------------|----------
0.0 - 0.3          | LOW        | AUTO            | Auto-merge
0.3 - 0.6          | MEDIUM     | REVIEW          | Wait for review
0.6 - 0.8          | HIGH       | PROPOSAL        | Create discussion
0.8 - 1.0          | CRITICAL   | BLOCKED         | Manual approval
```

### 4. CODEOWNERS - Critical Path Protection

The `.github/CODEOWNERS` file defines which paths require additional review scrutiny.

**Critical Paths:**
```
/src/autonomy/                  - Closed-loop autonomy (highest protection)
/src/orchestration/             - Multi-AI orchestration
/src/healing/                   - Self-healing systems
/src/main.py                    - Main entry point
/scripts/start_nusyq.py         - System startup
/config/                        - Configuration
/.github/workflows/             - CI/CD pipelines
```

**Protection Rules:**
- Changes to critical paths automatically increase risk score
- Critical paths are marked as "must review" in governance
- Future: Require CODEOWNERS approval before merge

## Risk-Based Governance Policies

### AUTO → Auto-Merge
**Criteria:** Risk Score < 0.3 + All Checks Pass

**Examples:**
- Adding utility functions (non-critical path)
- Fixing typos/documentation
- Adding unit tests
- Updating dependencies (if tests pass)

**Process:**
```
1. All CI checks pass
2. Risk score calculated < 0.3
3. PR created by autonomy bot
4. Merge applied automatically (squash)
5. Commit message preserved with autonomy metadata
```

### REVIEW → Human Review Required
**Criteria:** 0.3 ≤ Risk Score < 0.6

**Examples:**
- Modifying orchestration logic
- Changing utility functions
- Adding new features to non-critical paths
- Touching 5-10 files

**Process:**
```
1. All CI checks pass
2. Risk score 0.3-0.6
3. PR comment requests review
4. Human must approve before merge
5. If approved, can be merged manually or by bot
```

### PROPOSAL → Discussion Required
**Criteria:** 0.6 ≤ Risk Score < 0.8

**Examples:**
- Major refactoring
- Adding to critical paths
- Touching 20+ files
- Adding new dependencies

**Process:**
```
1. All CI checks pass
2. Risk score 0.6-0.8
3. Create GitHub Discussion/Issue
4. Link PR to discussion
5. Require explicit team decision before proceed
```

### BLOCKED → Manual Approval Only
**Criteria:** Risk Score ≥ 0.8

**Examples:**
- Modifying autonomy system itself
- Changes to main.py or orchestration
- Touching both critical paths and tests
- Large deletions from critical code

**Process:**
```
1. All CI checks pass (but merge is blocked)
2. Risk score ≥ 0.8
3. Merge blocked at GitHub level
4. Requires explicit user approval (@KiloMusician or specified CODEOWNERS)
5. Can force merge manually if necessary
```

## Implementation Details

### PR Body Metadata Format

The autonomy system embeds risk information in the PR description for GitHub Actions to parse:

```markdown
## Autonomy System Generated

Risk Score: 0.25
Risk Level: LOW
Approval Policy: AUTO
Files Changed: 3
Critical Paths: 0

[Patch Details]
- Added src/utilities/new_feature.py (75 lines)
- Modified tests/test_new_feature.py (added 40 lines)

[Autonomy Rationale]
Patch extracted from task #12345 (Add performance analyzer)
All tests pass, no critical paths affected, low complexity.
```

### GitHub Actions Environment Variables

```yaml
# Available in workflows
RISK_SCORE: 0.25                    # Float 0.0-1.0
RISK_LEVEL: LOW                     # LOW, MEDIUM, HIGH, CRITICAL
APPROVAL_POLICY: AUTO               # AUTO, REVIEW, PROPOSAL, BLOCKED
AUTONOMY_BOT: true                  # Is this from autonomy bot?
```

### Branch Protection Rules (Recommended Configuration)

In GitHub repo settings → Branches → Branch protection rules for `master`:

```
✓ Require a pull request before merging
✓ Require status checks to pass before merging
  ✓ autonomy-gates
  ✓ autonomy-merge
✓ Require branches to be up to date before merging
✓ Allow auto-merge (with squash selected)
✗ Dismiss stale pull request approvals (for autonomy PRs)
✗ Require approval from code owners (override for AUTO policy)
```

## Workflow Examples

### Example 1: Low-Risk Auto-Merge
```
Developer says: "Add performance logging to utilities"

↓ GitDev generates patch:
  - Added src/utilities/performance_logger.py (100 lines)
  - Added tests/test_perf_logger.py (80 lines)
  - Not touching critical paths

↓ Risk Score Calculation:
  - Base: 0.0
  - File count (2 files): +0.1
  - Critical path: 0
  - Test added: -0.05 (reduction for tests)
  - Final: 0.05 → LOW

↓ GitHub Actions:
  - autonomy-gates: ✓ All checks pass
  - autonomy-merge: Risk 0.05 < 0.3 → AUTO

↓ Result:
  - PR automatically merged
  - Commit: "feat: Add performance logging [autonomy-auto]"
  - Log entry in quest_log.jsonl
```

### Example 2: Medium-Risk Human Review
```
Developer says: "Refactor task queue efficiency"

↓ GitDev generates patch:
  - Modified src/orchestration/background_task_orchestrator.py (80-line change)
  - Added tests (pass)
  - Touches critical path

↓ Risk Score Calculation:
  - Base: 0.0
  - File count: +0.05
  - Critical path (orchestration): +0.3
  - Test added: -0.05
  - Final: 0.3 → MEDIUM

↓ GitHub Actions:
  - autonomy-gates: ✓ All checks pass
  - autonomy-merge: Risk 0.3-0.6 → REVIEW

↓ Result:
  - PR comment: "⏳ Medium-risk change. Awaiting review from @KiloMusician"
  - PR stays open, requires human approval
  - Human reviews, approves, and merges manually
  - Log entry in quest_log.jsonl (marked REVIEW status)
```

### Example 3: Critical-Risk Blocked
```
Developer says: "Rewrite autonomy system"

↓ GitDev generates patch:
  - Modified src/autonomy/patch_builder.py (200-line rewrite)
  - Modified src/autonomy/risk_scorer.py (100-line change)
  - All tests pass
  - Affects multiple critical paths

↓ Risk Score Calculation:
  - Base: 0.0
  - File count: +0.1
  - Critical paths (2 files × 0.3): +0.6
  - Large deletions: +0.2
  - Final: 0.9 → CRITICAL

↓ GitHub Actions:
  - autonomy-gates: ✓ All checks pass (but high risk)
  - autonomy-merge: Risk 0.9 > 0.8 → BLOCKED

↓ Result:
  - PR comment: "❌ CRITICAL RISK - Merge blocked. Requires explicit approval."
  - Merge is blocked at branch protection level
  - @KiloMusician must explicitly approve and merge manually
  - Log entry with escalation flag
```

## Metrics & Monitoring

### Key Metrics Tracked

1. **Auto-Merge Success Rate**
   - % of PRs that auto-merge without human intervention
   - Target: 40-60% of all PRs

2. **Risk Distribution**
   - % LOW / MEDIUM / HIGH / CRITICAL by week
   - Track if autonomy is generating safe code

3. **Check Failure Rate**
   - % PRs that fail gates (lint, test, security)
   - Monitor code quality drift

4. **Review Turnaround Time**
   - Average time from REVIEW policy → human approval
   - Track if bottleneck exists

5. **False Positives/Negatives**
   - Merges that should have been blocked
   - Blocks that were too restrictive

## Debugging & Manual Overrides

### When Auto-Merge Doesn't Trigger

```bash
# Check PR labels
gh pr view <PR_NUMBER> --json labels

# Check workflow runs
gh run list --branch master --status completed

# Check PR comments (look for governance decision)
gh pr view <PR_NUMBER> --json comments

# Manually trigger workflow (if needed)
gh workflow run autonomy-merge.yml -f pr_number=<PR_NUMBER>
```

### Force Merge (Emergency)

```bash
# If PR is incorrectly blocked:
gh pr merge <PR_NUMBER> --squash --delete-branch

# Required: Document reason in quest log
```

### Update Risk Score

If autonomy bot calculated risk incorrectly:

1. Edit PR body to update `Risk Score: X.XX`
2. Add comment explaining adjustment
3. Trigger autonomy-merge workflow manually

## Future Enhancements (Phase 3+)

1. **Approval Shortcuts**
   - Reviewers can comment `/approve` to fast-track REVIEW tier
   - Comment `/merge` to override BLOCKED (audit logged)

2. **Risk Scoring ML**
   - Machine learning model to refine risk factors
   - Learn from past merges (success/failure)

3. **Enhanced ProposalPackage**
   - GitHub Discussions integration
   - Side-by-side risk/benefit analysis
   - Automated cost-benefit scoring

4. **Autonomy Dashboard**
   - Real-time merge decision visibility
   - Risk distribution charts
   - Success/failure rate tracking
   - Model utilization metrics

5. **CODEOWNERS Enforcement**
   - Auto-request review from code owners for critical paths
   - Escalation if owner unavailable

## Troubleshooting

### "Merge blocked - checks failed"
→ Check workflow logs: `gh run list | grep autonomy-gates`
→ Common issues: test failure, lint error, type mismatch
→ Fix and push new commit to re-trigger

### "Auto-merge not happening for low-risk PR"
→ Verify PR metadata embedded in body (Risk Score: < 0.3)
→ Check if PR creator is autonomy bot
→ Verify all checks actually passed (cache issues?)
→ Manually trigger: `gh workflow run autonomy-merge.yml`

### "Risk score seems wrong"
→ Check RiskScorer logic: `src/autonomy/risk_scorer.py`
→ Verify critical_paths list is correct
→ Review risk_factors calculation
→ Consider if new file type should be excluded

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [RiskScorer Implementation](../src/autonomy/risk_scorer.py)
- [Autonomy System](../src/autonomy/)
- [Phase 1A: Closed Loop](../docs/PHASE_1A_CLOSED_LOOP.md) (if exists)
