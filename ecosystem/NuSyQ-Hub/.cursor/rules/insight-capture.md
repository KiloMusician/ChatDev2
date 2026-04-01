---
description: INVOKE when reasoning reveals sudden synthesis, reframing, non-obvious implications, when a prior assumption was wrong, or when catching sloppy AI habits. Captures structural insights before they're lost. Multi-agent aware.
alwaysApply: false
agents: [claude, copilot, codex]
---

# Insight Capture - ΞNuSyQ Multi-Agent Edition

**Trigger:** A response reveals sudden synthesis, reframing, or non-obvious implications. Your own reasoning derives a structural insight, reveals a prior assumption was wrong, or catches a sloppy habit worth preventing.

**Goal:** Capture the insight before it's lost to the session ether. Make it available to all agents (Claude, Copilot, Codex).

---

## When This Fires

You (the AI agent) should suggest invoking this when:
- 🎯 A response reveals a sudden synthesis or reframing
- 🎯 Reasoning derives a non-obvious structural insight
- 🎯 A prior assumption turns out to be wrong
- 🎯 A non-obvious implication emerges from the work
- 🎯 A pattern clicks that wasn't explicit before
- 🎯 You catch yourself about to make a common AI mistake
- 🎯 You notice a sloppy habit that could become a rule to prevent it
- 🎯 **Cross-agent learning**: Another agent made this mistake, prevent it system-wide
- 🎯 **Architecture discovery**: You learned how ΞNuSyQ actually works

---

## Capture Flow

### Step 1: Acknowledge
Pause. Say: "That's interesting - should I capture this insight?"

### Step 2: Quick Classification
- **Synthesis** → Connected dots that weren't obvious
- **Reframe** → Shifted how to think about the problem
- **Correction** → Prior assumption was wrong
- **Pattern** → Could become a rule
- **System insight** → Reveals how things actually work
- **Sloppy habit** → AI tendency that causes problems (prime rule candidate!)
- **Agent-specific gotcha** → One agent type struggles with this
- **Architecture revelation** → Discovered how orchestration/routing works

### Step 3: Capture Location

| Size | Where | Format | Multi-Agent |
|------|-------|--------|-------------|
| One-liner | `src/Rosetta_Quest_System/insights.jsonl` | JSON event | ✅ All agents read |
| Paragraph | Quest log + insights.jsonl | Both formats | ✅ Tracked in quests |
| Full write-up | `docs/discoveries/DISCOVERY-*.md` | Markdown doc | ✅ Referenced in system brief |
| Architecture | `docs/AGENT_COORDINATION_MAP.md` | Update map | ✅ Orientation reads it |

### Step 4: Agent Scope Check
Ask: "Which agents need to know this?"

| Scope | Who | Where |
|-------|-----|-------|
| All agents | Claude, Copilot, Codex | `insights.jsonl` + System Brief |
| Agent-specific | Just one agent type | `docs/agent-gotchas/[agent]-lessons.md` |
| Human-only | User reference | `docs/human-notes/` |
| System-wide | Architecture change | `docs/AGENT_COORDINATION_MAP.md` |

### Step 5: Rule Potential Check
Ask: "Could this become a rule?"
- If yes → Create rule in `.cursor/rules/` or `.vscode/`
- If system-wide → Update `docs/ΞNuSyQ_SYSTEM_BRIEF.md`
- If agent-specific → Add to agent orientation

---

## ΞNuSyQ-Specific Capture Formats

### 1. Insight Event (insights.jsonl)

```json
{
  "timestamp": "2026-01-16T12:34:56Z",
  "agent": "claude",
  "session_id": "session_20260116_123456",
  "type": "synthesis",
  "insight": "MultiAIOrchestrator is a redirect to UnifiedAIOrchestrator - imports work via compatibility layer",
  "impact": "high",
  "applies_to": ["claude", "copilot", "codex"],
  "reference": "docs/AGENT_COORDINATION_MAP.md:48-75",
  "tags": ["orchestration", "architecture", "imports"]
}
```

### 2. Quest Log Entry (quest_log.jsonl)

```json
{
  "quest_id": "INSIGHT-20260116-001",
  "title": "Discovered orchestrator redirect pattern",
  "type": "insight_capture",
  "agent": "claude",
  "status": "completed",
  "insight": "Full description...",
  "actionable": true,
  "proposed_rule": "Always import from multi_ai_orchestrator.py (redirects to canonical)",
  "created_at": "2026-01-16T12:34:56Z"
}
```

### 3. Discovery Document (docs/discoveries/)

```markdown
# DISCOVERY-orchestrator-redirect-pattern

**Date**: 2026-01-16
**Discovered By**: Claude (session_20260116_123456)
**Applies To**: All agents
**Impact**: High

## The Insight

MultiAIOrchestrator is a compatibility layer that redirects to UnifiedAIOrchestrator...

## Why This Matters

Agents were confused about which orchestrator to use...

## What Changed

Updated AGENT_COORDINATION_MAP.md to clarify...

## Proposed Rule

```python
# ALWAYS import from multi_ai_orchestrator (compatibility layer)
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
# NOT directly from unified_ai_orchestrator
```
```

---

## Example Captures

### Quick Insight (insights.jsonl only)

```json
{
  "agent": "copilot",
  "type": "sloppy_habit",
  "insight": "Stop using generic TODO comments - create quests instead",
  "actionable": true
}
```

### Architecture Discovery (Full write-up)

1. Log to `insights.jsonl`
2. Create `docs/discoveries/DISCOVERY-terminal-routing.md`
3. Update `docs/AGENT_COORDINATION_MAP.md`
4. Reference in next agent orientation

### Cross-Agent Learning (Prevent repetition)

```json
{
  "agent": "claude",
  "type": "agent_gotcha",
  "insight": "Codex kept deleting scaffolding - added to System Brief rule 2",
  "applies_to": ["claude", "copilot", "codex"],
  "prevention": "Updated docs/ΞNuSyQ_SYSTEM_BRIEF.md with stronger preservation language"
}
```

### Rule Proposal (New .cursor/rules file)

```markdown
# docs/proposed-rules/RULE-no-orchestrator-creation.md

**Proposed By**: Claude (2026-01-16)
**Reason**: Caught about to create 6th orchestrator when 5 already exist

## Rule
Never create new orchestrators. Use existing:
1. MultiAIOrchestrator (primary)
2. UnifiedAIOrchestrator (canonical)
3. agent_orchestration_hub.py (routing)

## Detection
If AI suggests creating file matching `*orchestrat*.py`, trigger warning.
```

---

## Multi-Agent Persistence Strategy

### Where Insights Live

```
NuSyQ-Hub/
├── src/
│   └── Rosetta_Quest_System/
│       ├── quest_log.jsonl          # Quest-based insights
│       └── insights.jsonl           # Rapid-fire insight capture
├── docs/
│   ├── ΞNuSyQ_SYSTEM_BRIEF.md      # System-wide rules (all agents read)
│   ├── AGENT_COORDINATION_MAP.md    # Architecture insights
│   ├── discoveries/                 # Deep dives
│   │   └── DISCOVERY-*.md
│   └── agent-gotchas/               # Agent-specific lessons
│       ├── claude-lessons.md
│       ├── copilot-lessons.md
│       └── codex-lessons.md
└── .cursor/rules/                   # Enforced patterns
    └── *.md
```

### How Agents Access Insights

**On Startup** (via agent_orientation.py):
1. Read `docs/ΞNuSyQ_SYSTEM_BRIEF.md` (contains high-impact rules)
2. Read `docs/AGENT_COORDINATION_MAP.md` (architecture insights)
3. Check `insights.jsonl` for recent learnings (last 50 entries)

**During Session**:
1. Quest system automatically logs insights
2. Agents can query: `grep "type.*insight" src/Rosetta_Quest_System/insights.jsonl`

**Cross-Session**:
1. Insights accumulate in `insights.jsonl`
2. Human periodically promotes important ones to System Brief
3. Rules get codified in `.cursor/rules/`

---

## Backup Triggers

If the AI doesn't catch it, user can say:
- "Capture this"
- "That's a gotcha"
- "We should remember this"
- "Future me needs to know this"
- "All agents need to know this"
- "Add this to the System Brief"
- "This should be a rule"
- "Log this insight"

Any of these should trigger this workflow.

---

## Integration with ΞNuSyQ Workflow

### Automatic Captures (No Confirmation Needed)

The system automatically captures when:
- ✅ Quest completes with unexpected solution
- ✅ Error resolved in non-obvious way
- ✅ Agent discovers new capability
- ✅ Routing path clarified
- ✅ Configuration wired differently than expected

### Manual Captures (Require Acknowledgment)

Agent should ask before capturing:
- ❓ Subjective architectural opinions
- ❓ Experimental approaches
- ❓ Patterns seen only once
- ❓ User-specific preferences

### Promotion Path

```
insights.jsonl
  ↓ (if high-impact)
docs/discoveries/DISCOVERY-*.md
  ↓ (if system-wide)
docs/ΞNuSyQ_SYSTEM_BRIEF.md
  ↓ (if enforceable)
.cursor/rules/RULE-*.md
```

---

## Special Case: "Sloppy AI Habits"

When catching a common AI mistake, capture with urgency:

```json
{
  "agent": "claude",
  "type": "sloppy_habit",
  "urgency": "high",
  "habit": "Creating TODO comments instead of quests",
  "why_bad": "TODOs get lost, quests are tracked in quest_log.jsonl",
  "correct_behavior": "Use quest system: engine.add_quest(...)",
  "rule_candidate": true,
  "proposed_rule_path": ".cursor/rules/no-todo-comments.md"
}
```

This gets **immediate promotion** to prevent other agents from repeating it.

---

## Success Metrics

Track insight capture effectiveness:
- **Capture Rate**: Insights logged per session
- **Promotion Rate**: insights.jsonl → System Brief
- **Rule Creation**: Rules derived from insights
- **Agent Improvement**: Reduced repeat mistakes
- **Cross-Agent Learning**: Insights shared between Claude/Copilot/Codex

---

## Meta-Learning Loop

```
Agent encounters situation
  ↓
Derives insight
  ↓
Captures to insights.jsonl
  ↓
Human reviews and promotes
  ↓
System Brief updated
  ↓
All agents benefit in next session
  ↓
Fewer repeated mistakes
```

---

**Status**: Ready for use across Claude, Copilot, and Codex agents in ΞNuSyQ ecosystem.
