# 🤖 Agent Instructions & Breadcrumbs System

## How to Use This System

### For Current Agent (Immediate Session)
```python
# Import the helper
from scripts.agent_git_helper import agent_commit

# Make changes, then commit with context
agent_commit(
    changes=["Your changes here"],
    todo_completed=["Items completed from 50-item list"],
    next_priorities=["Next items to work on"],
    technical_notes="Any important technical context",
    agent_instructions="Instructions for next agent session"
)
```

### For Next Agent (Future Session)
1. **Check latest session log**: `docs/Agent-Sessions/SESSION_YYYY-MM-DD.md`
2. **Review breadcrumbs**: Look for "Next Agent" sections in recent commits
3. **Continue from last state**: Use the priorities and context provided
4. **Update session log**: Create new session file for your work

### Commit Message Template
All agent commits should include:
- ✅ **Changes Made**: What was actually done
- 📋 **To-Do Progress**: Items completed from the 50-item list
- 🎯 **Next Priorities**: What should be done next
- 🔧 **Technical Context**: Important implementation details
- 🧭 **Breadcrumbs**: Instructions for future agents

### Session Management
- Each agent session gets its own log file
- Session logs track progress on the 50-item to-do list
- Git commits reference session logs for traceability
- Future agents can pick up exactly where previous agents left off

### Best Practices
1. **Always use agent_git_helper.py** for commits
2. **Update session logs** before major work
3. **Leave clear breadcrumbs** for complex work
4. **Reference to-do item numbers** consistently
5. **Include technical context** for implementation decisions
