# 🏛️ AI Council - Quick Start Guide

**TL;DR**: The AI Council is your persistent AI board of directors. Use it to track progress, flag warnings, capture insights, and ensure systematic evolution.

---

## ⚡ Quick Commands

```bash
# Daily progress tracking
python config/ai_council.py standup

# Emergency issue response
python config/ai_council.py emergency "Description of critical issue"

# Record subtle insight
python config/ai_council.py wink "Pattern or observation"

# Check current status
python config/ai_council.py progress
```

---

## 🎯 When to Use What

### Use STANDUP when...
- ✅ Starting/ending your day
- ✅ Completing a major milestone
- ✅ Need to remember "what was I working on?"
- ✅ Want to verify roadmap adherence

**Example**:
```python
from config.ai_council import daily_standup

daily_standup(
    completed=["Fixed Unicode bug", "Created AI Council"],
    in_progress=["Documentation", "Testing"],
    next_up=["Week 4 integration tests"]
)
```

---

### Use EMERGENCY when...
- 🚨 Critical errors detected
- 🚨 Security vulnerabilities found
- 🚨 System breaking changes
- 🚨 Urgent architectural concerns

**Example**:
```python
from config.ai_council import emergency_session

emergency_session(
    issue="457 errors after recent merge",
    severity="high"  # critical/high/medium
)
```

---

### Use QUANTUM_WINK when...
- 💡 Notice a subtle pattern
- 💡 See code duplication
- 💡 Spot potential optimization
- 💡 Have architectural insight

**Example**:
```python
from config.ai_council import quantum_wink

quantum_wink(
    insight="All agent_*.py files share structure - consider base class",
    agent="claude_code"
)
```

---

### Use ADVISORY when...
- 🤔 Exploring new approaches
- 🤔 Need architectural guidance
- 🤔 Brainstorming ideas
- 🤔 Requesting best practices

**Example**:
```python
from config.ai_council import AICouncil

council = AICouncil()
minutes = council.convene_advisory(
    topic="Add GraphQL API?",
    context="REST works, but GraphQL might improve efficiency",
    seeking="Pros/cons analysis"
)
```

---

## 📊 Understanding Council Tiers

### Executive Council (3 agents) - Strategic
- **claude_code**: Master orchestrator
- **chatdev_ceo**: Software strategy
- **ollama_qwen_14b**: Technical architecture

**Use for**: High-level decisions, daily standups, critical issues

---

### Technical Council (5 agents) - Implementation
- **ollama_gemma_9b**: Security & best practices
- **chatdev_cto**: System design
- **chatdev_programmer**: Code quality
- **ollama_codellama_13b**: Code generation
- **chatdev_reviewer**: QA

**Use for**: Emergency responses, technical guidance

---

### Advisory Panel (3 agents) - Insights
- **ollama_llama_8b**: General reasoning
- **chatdev_tester**: Reliability
- **ollama_phi_3**: Quick triage

**Use for**: Advisory sessions, reflection, brainstorming

---

## 💰 Cost Breakdown

- **Standup**: ~$0.02 (Executive Council, Claude participates)
- **Emergency**: $0.00 (Technical Council, all Ollama)
- **Advisory**: ~$0.01 (Advisory Panel + Claude)
- **Quantum Wink**: $0.00 (just file write)

**Monthly** (daily standups + weekly advisory): ~$0.64

**vs. All-Claude**: $18/month
**Savings**: 96% 💰

---

## 📁 Where Council Data Lives

```
Logs/ai_council/
  council_state.json              # Persistent state
  council_standup_*.json          # Standup minutes
  council_emergency_*.json        # Emergency minutes
  council_advisory_*.json         # Advisory minutes
  quantum_winks.jsonl             # Insights log
```

---

## 🔍 Typical Workflows

### Morning Workflow
```bash
# Check yesterday's progress
python config/ai_council.py progress

# Plan today's work (optional - can skip on quiet days)
# python config/ai_council.py standup
```

---

### Issue Detection Workflow
```bash
# Found 457 errors!
python config/ai_council.py emergency "457 errors after merge"

# Council provides:
# - Root cause analysis
# - Immediate mitigation
# - Long-term fix
# - Related warnings
```

---

### Insight Capture Workflow
```python
# During code review, notice pattern
quantum_wink(
    "Repeated subprocess.run() - extract to utility function",
    "claude_code"
)

# Later, review all winks
council = AICouncil()
winks = council.state["quantum_winks"]
# Use for refactoring planning
```

---

### End of Week Workflow
```python
# Reflect on week's progress
council = AICouncil()
minutes = council.convene_advisory(
    topic="Week 3 Retrospective",
    context="Completed multi-agent orchestration + AI Council",
    seeking="What went well, what to improve?"
)

# Use insights for Week 4 planning
```

---

## 🎓 Pro Tips

### 1. Quantum Winks Are Gold
- Don't overthink - if you notice something, record it
- Winks are lightweight (no AI calls, just file writes)
- Review winks weekly to find patterns

### 2. Standup Isn't Always Needed
- Skip on quiet days (reviewing code, reading docs)
- Use when completing milestones or starting new phases
- Daily is ideal, but 2-3x/week works too

### 3. Emergency Sessions Are Powerful
- All Technical Council (5 free agents) in parallel
- Get multiple perspectives instantly
- Use severity to prioritize: critical > high > medium

### 4. Progress Summary is Your Friend
```bash
python config/ai_council.py progress

# Shows:
# - Recent sessions count
# - Tasks completed
# - Active work
# - Next steps
# - Active warnings
# - Quantum winks collected
```

### 5. Council State Persists Forever
- All progress history saved
- Warnings tracked until resolved
- Quantum winks archived
- **Result**: Institutional memory across sessions

---

## 🚀 Advanced Usage

### Custom Advisory Session
```python
council = AICouncil()

# Custom participants (mix tiers)
from config.multi_agent_session import MultiAgentSession, ConversationMode

session = MultiAgentSession(
    agents=["claude_code", "ollama_qwen_14b", "ollama_gemma_9b"],
    task_prompt="Should we add caching to multi-agent sessions?",
    mode=ConversationMode.PARALLEL_CONSENSUS
)

result = session.execute()
# Get 3 perspectives instantly, vote on consensus
```

---

### Resolve Active Warnings
```python
council = AICouncil()

# Check warnings
warnings = council.state["active_warnings"]
print(f"Active warnings: {len(warnings)}")

# After fixing
council.state["active_warnings"] = [
    w for w in warnings if w["issue"] != "Fixed issue description"
]
council._save_state()
```

---

### Analyze Quantum Wink Patterns
```python
council = AICouncil()
winks = council.state["quantum_winks"]

# Group by topic
subprocess_winks = [w for w in winks if "subprocess" in w["insight"].lower()]
print(f"Subprocess insights: {len(subprocess_winks)}")
# Result: 3 winks suggest creating utility function
```

---

## 📖 Full Documentation

- **Complete Guide**: `docs/reference/AI_COUNCIL_GUIDE.md` (500+ lines)
- **Progress Report**: `docs/reference/WEEK3_EXTENSION_AI_COUNCIL.md`
- **Source Code**: `config/ai_council.py` (640 lines)

---

## ❓ FAQ

**Q: Do I need to run standups every day?**
A: No! Use when completing milestones or starting new phases. 2-3x/week works great.

**Q: What's the difference between emergency and advisory?**
A: Emergency = urgent issue needing rapid response. Advisory = exploring ideas/guidance.

**Q: How many quantum winks should I record?**
A: No limit! Winks are free (no AI calls). Record any pattern you notice.

**Q: Can I use council without Ollama?**
A: Technically yes (falls back to Claude), but costs 25× more. Ollama strongly recommended.

**Q: Where's the council history?**
A: `Logs/ai_council/council_state.json` + individual session JSON files.

---

## 🎉 Summary

The AI Council gives ΞNuSyQ a **persistent memory** and **collective intelligence**:

- **STANDUP**: Track what we did/doing/next
- **EMERGENCY**: Rapid response to critical issues
- **QUANTUM_WINK**: Capture subtle insights
- **ADVISORY**: Explore ideas and guidance
- **PROGRESS**: Always know project status

**Cost**: ~$0.64/month (96% savings)
**Benefit**: 11-agent oversight with institutional memory

**Start now**:
```bash
python config/ai_council.py standup
```

---

**Created**: 2025-10-07
**Version**: 1.0.0
**Status**: ✅ Production Ready
