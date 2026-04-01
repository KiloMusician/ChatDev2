# NuSyQ-Hub Learning System Guide

**Purpose**: Document how the system learns from fixes and prevents repeat mistakes

## Overview

The NuSyQ-Hub ecosystem has a built-in learning system that automatically extracts patterns from every commit, stores them in a knowledge base, and makes them available to strategic decision-making systems like Culture Ship. This creates a **continuous learning loop** where past solutions inform future decisions.

## How It Works

### 1. Learning Flow

```
Developer/Agent makes fix
  ↓
Writes commit with "Pattern:" or "Impact:" markers
  ↓
Git post-commit hook extracts patterns automatically
  ↓
Patterns saved to data/knowledge_bases/evolution_patterns.jsonl
  ↓
XP awarded based on tags (15-90 XP per commit)
  ↓
Culture Ship reads patterns during strategic analysis
  ↓
Future decisions informed by learned patterns
  ↓
Rosetta Stone updated with key learnings
```

### 2. Components

**Evolution Patterns Database**:
- Location: `data/knowledge_bases/evolution_patterns.jsonl`
- Format: One JSON object per line (JSONL)
- Fields:
  ```json
  {
    "timestamp": "2026-01-25T09:47:13.344452+00:00",
    "commit": "806b8337",
    "patterns": [
      "Pattern: Autonomous systems must update their own generated tasks",
      "Impact: Self-improvement loop now tracks PU lifecycle end-to-end"
    ],
    "tags": ["TYPE_SAFETY", "RESILIENCE", "AUTOMATION", "FEATURE"],
    "xp": 90
  }
  ```

**Git Post-Commit Hook**:
- Location: `.git/hooks/post-commit`
- Parses commit messages for learning markers
- Extracts evolution tags from commit body
- Awards XP based on tag combination
- Appends to evolution_patterns.jsonl

**Culture Ship Strategic Advisor**:
- Location: `src/orchestration/culture_ship_strategic_advisor.py`
- Reads evolution patterns to identify recurring issues
- Makes strategic decisions informed by past learnings
- Can detect when same mistakes are being repeated

**Rosetta Stone**:
- Location: `docs/ROSETTA_STONE.md`
- Human-readable reference updated with key learnings
- Line 7: "refresh when the system learns something new"
- Consolidates most important patterns for quick agent reference

## Writing Learning-Extractable Commits

### Basic Syntax

Include one or more of these markers in your commit message body:

1. **Pattern:** - Describes a reusable solution pattern
2. **Impact:** - Describes the measurable effect of the change
3. **Tags** - Automatically extracted from commit message context

### Example Commit Messages

**Good Example** (90 XP):
```
feat: implement autonomous loop PU tracking

- Added PU status update logic in _process_execution_results()
- Marks autonomous_loop_audit PUs as completed when fixes applied
- Fixed service health check to use actual orchestrator data

Pattern: Autonomous systems must update their own generated tasks
Pattern: Use getattr() for platform-specific subprocess flags
Impact: Self-improvement loop now tracks PU lifecycle end-to-end
Impact: Code now runs on non-Windows platforms without AttributeError

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Minimal Example** (45-50 XP):
```
fix: add None checks before list operations

Pattern: Always check list|None unions before using list methods
Impact: Prevents AttributeError when optional lists are None
```

**Anti-Pattern** (15-20 XP - generic):
```
fix: various improvements
```

### Recognized Tags

Tags are extracted automatically based on commit content and markers:

- **TYPE_SAFETY** - Type annotation fixes, mypy error elimination
- **BUGFIX** - Bug fixes, error corrections
- **FEATURE** - New functionality added
- **RESILIENCE** - Error handling, robustness improvements
- **AUTOMATION** - Workflow automation, CI/CD improvements
- **INTEGRATION** - System integration, component wiring
- **ARCHITECTURE** - Structural changes, design patterns
- **DESIGN_PATTERN** - Reusable solution patterns
- **OBSERVABILITY** - Logging, metrics, debugging aids
- **CONFIGURATION** - Config management, environment setup
- **INITIALIZATION** - Startup, bootstrap improvements
- **DOCUMENTATION** - Docs, comments, guides

### XP Award Scale

- **15-35 XP**: Simple fixes, single tag
- **45-65 XP**: Good fix with patterns, 2-3 tags
- **85-90 XP**: Excellent learning capture, 4+ tags with clear patterns

## Querying Learned Patterns

### Command Line

**See latest patterns**:
```bash
tail -5 data/knowledge_bases/evolution_patterns.jsonl
```

**Count total learnings**:
```bash
wc -l < data/knowledge_bases/evolution_patterns.jsonl
```

**Find patterns by topic**:
```bash
grep -i "type" data/knowledge_bases/evolution_patterns.jsonl | python -m json.tool
```

### Python

**Load all patterns**:
```python
from pathlib import Path
import json

patterns_file = Path("data/knowledge_bases/evolution_patterns.jsonl")
patterns = [
    json.loads(line)
    for line in patterns_file.read_text().strip().split('\n')
]

print(f"Total patterns learned: {len(patterns)}")
```

**Find patterns by tag**:
```python
type_safety_patterns = [
    p for p in patterns
    if "TYPE_SAFETY" in p["tags"]
]

for p in type_safety_patterns[-5:]:  # Last 5
    print(f"{p['commit']}: {p['patterns'][0]}")
```

**Get XP statistics**:
```python
total_xp = sum(p["xp"] for p in patterns)
avg_xp = total_xp / len(patterns)
print(f"Total XP earned: {total_xp}")
print(f"Average XP per commit: {avg_xp:.1f}")
```

## How Culture Ship Uses Patterns

Culture Ship reads evolution_patterns.jsonl during strategic analysis to:

1. **Identify Recurring Issues**: Detect when the same type of error keeps appearing
2. **Suggest Proven Solutions**: Recommend patterns that worked before
3. **Prioritize High-Impact Fixes**: Focus on areas with high XP patterns
4. **Avoid Past Mistakes**: Check if a proposed solution was tried and failed before

Example from `culture_ship_strategic_advisor.py`:
```python
def identify_strategic_issues(self) -> list[StrategicIssue]:
    """Identify issues, informed by learned patterns."""
    # Read evolution patterns
    patterns = self._load_evolution_patterns()

    # Check for recurring issues
    recurring = self._find_recurring_issues(patterns)

    # Prioritize based on past impact
    prioritized = self._prioritize_by_learned_impact(recurring)

    return prioritized
```

## Best Practices

### ✅ DO

1. **Be Specific**: "Pattern: Use getattr() for platform-specific flags" > "Pattern: Better code"
2. **Include Impact**: Quantify the improvement where possible
3. **Multiple Patterns**: One commit can capture multiple learnings
4. **Tag Appropriately**: Helps categorization and retrieval
5. **Update Rosetta**: Add major learnings to docs/ROSETTA_STONE.md

### ❌ DON'T

1. **Don't be vague**: "Pattern: Fixed stuff" provides no learning value
2. **Don't omit context**: Pattern should be understandable without seeing the code
3. **Don't duplicate**: Check recent patterns before adding similar ones
4. **Don't over-tag**: Use only tags that truly apply
5. **Don't skip attribution**: Co-Authored-By helps track agent contributions

## Integration with Rosetta Stone

The Rosetta Stone (docs/ROSETTA_STONE.md) serves as a curated, human-readable reference. When a pattern is particularly important:

1. Extract the key learning from evolution_patterns.jsonl
2. Add a concise summary to the relevant Rosetta section
3. Link to the commit for full context
4. Update Rosetta's "last updated" timestamp

Example Rosetta entry:
```markdown
### Pattern: Platform-Specific Subprocess Flags

Use `getattr(subprocess, 'FLAG_NAME', default)` instead of direct attribute
access for platform-specific flags like CREATE_NEW_CONSOLE (Windows-only).

**Learned from**: commit 806b8337 (2026-01-25)
**Impact**: Cross-platform compatibility, prevents AttributeError on Linux/Mac
```

## Monitoring Learning Health

### Weekly Review

Run this to see learning trends:
```bash
python -c "
from pathlib import Path
import json
from collections import Counter
from datetime import datetime, timedelta

patterns_file = Path('data/knowledge_bases/evolution_patterns.jsonl')
patterns = [json.loads(line) for line in patterns_file.read_text().strip().split('\n')]

# Last 7 days
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
recent = [p for p in patterns if p['timestamp'] > week_ago]

print(f'Patterns this week: {len(recent)}')
print(f'XP earned: {sum(p[\"xp\"] for p in recent)}')

# Top tags
all_tags = [tag for p in recent for tag in p['tags']]
top_tags = Counter(all_tags).most_common(5)
print(f'Top tags: {top_tags}')
"
```

### Health Indicators

**Good**:
- Steady pattern accumulation (2-5 per day during active development)
- Diverse tags (not all TYPE_SAFETY or BUGFIX)
- High average XP (50+)
- Specific, actionable patterns

**Needs Attention**:
- No new patterns in days (knowledge not being captured)
- All patterns are generic (low XP < 30)
- Same tags every time (narrow focus)
- Vague impact statements

## Troubleshooting

**Problem**: Patterns not being extracted from commits

**Solutions**:
1. Check git hook exists and is executable: `ls -la .git/hooks/post-commit`
2. Verify pattern markers in commit message (Pattern:, Impact:)
3. Check evolution_patterns.jsonl permissions
4. Look for hook errors in git output

**Problem**: Culture Ship not using learned patterns

**Solutions**:
1. Verify patterns file exists: `cat data/knowledge_bases/evolution_patterns.jsonl`
2. Check Culture Ship can read file (permissions)
3. Verify pattern format is valid JSON
4. Check Culture Ship logs for parsing errors

**Problem**: Low XP awards

**Solutions**:
1. Add more specific patterns to commit messages
2. Include measurable impact statements
3. Use multiple relevant tags
4. Document the "why" not just the "what"

## Examples from Real System History

### Error Reduction Progress

```json
{
  "commit": "10ed8eb4",
  "patterns": ["Total impact: 51+ errors eliminated, codebase health significantly improved."],
  "tags": ["TYPE_SAFETY", "BUGFIX", "OBSERVABILITY", "AUTOMATION", "INITIALIZATION"],
  "xp": 50
}
```

### Meta-Learning

```json
{
  "commit": "8edd10b7",
  "patterns": ["Meta-insight: Culture Ship was analyzing itself and incorrectly reporting non-integration"],
  "tags": ["TYPE_SAFETY", "ARCHITECTURE", "INTEGRATION", "FEATURE"],
  "xp": 50
}
```

### Design Pattern Discovery

```json
{
  "commit": "91d482a0",
  "patterns": [
    "11 overlapping type-fixing tools -> 1 unified entrypoint",
    "1,500+ lines of type-fixing logic -> ~800 lines (47% reduction)",
    "100% backward compatible via shim pattern"
  ],
  "tags": ["DESIGN_PATTERN", "TYPE_SAFETY", "AUTOMATION"],
  "xp": 90
}
```

## Summary

The learning system ensures that **every fix becomes institutional knowledge**. By writing learning-extractable commits, you contribute to a knowledge base that:

- Prevents repeating the same mistakes
- Captures proven solutions for reuse
- Informs strategic decision-making
- Tracks system evolution over time
- Awards XP for knowledge contributions

**Remember**: The system is only as smart as the patterns we feed it. Write thoughtful commit messages, and the system learns from every change.

---

**Last Updated**: 2026-01-25
**Related**: `docs/ROSETTA_STONE.md`, `src/orchestration/culture_ship_strategic_advisor.py`
