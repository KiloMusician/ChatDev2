#!/usr/bin/env python3
"""Insert Agent Communication Protocol section into AGENT_TUTORIAL.md"""

# Read the file
with open(r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\docs\AGENT_TUTORIAL.md", encoding="utf-8") as f:
    lines = f.readlines()

# Find the Quick Reference Card line
insert_line = None
for i, line in enumerate(lines):
    if "Quick Reference Card" in line:
        insert_line = i
        break

if insert_line is None:
    print("ERROR: Could not find Quick Reference Card section")
else:
    print(f"Will insert before line {insert_line + 1}")

    # Create the new section
    new_section = """## 🤝 Agent Communication Protocol (NEW)

### Overview: How Agents Talk to Each Other

NuSyQ is a **multi-agent ecosystem**. When agents need to coordinate (Copilot → Ollama → ChatDev), they use these standardized communication patterns.

### Communication Channel 1: Quest Log Exchange

**Purpose:** Persistent, auditable task coordination across agents

**Pattern:**
```json
{
  "quest_id": "feature_xyz_implementation",
  "sender": "copilot",
  "receiver": "chatdev",
  "timestamp": "2025-01-20T14:32:15Z",
  "message_type": "hand_off",
  "payload": {
    "task": "Implement User authentication endpoint",
    "context": {
      "design_decision": "Use JWT tokens",
      "database": "PostgreSQL",
      "framework": "FastAPI"
    },
    "acceptance_criteria": [
      "POST /auth/login returns JWT",
      "Token valid for 1 hour",
      "Refresh endpoint exists"
    ],
    "estimated_duration_minutes": 45
  },
  "next_checkpoint": "code_review_ready"
}
```

**How to Send:**
```python
from src.Rosetta_Quest_System import quest_log

quest_log.add_entry({
    "quest_id": "feature_xyz_implementation",
    "sender": "copilot",
    "receiver": "chatdev",
    "message_type": "hand_off",
    "payload": {...}
})
```

**How to Receive:**
```python
# ChatDev agent polls for messages
messages = quest_log.query(
    receiver="chatdev",
    message_type="hand_off",
    status="pending"
)

for msg in messages:
    # Process the handoff
    implement_task(msg["payload"])

    # Acknowledge receipt
    quest_log.update_entry(msg["quest_id"], {
        "status": "acknowledged",
        "receiver_acknowledged_at": datetime.now().isoformat()
    })
```

---

### Communication Channel 2: Error Escalation

**Purpose:** Alert other agents to blocking issues; request help

**Pattern:**
```python
# When Ollama fails, escalate to fallback AI
from src.tools.agent_task_router import escalate_failure

try:
    result = ollama_agent.analyze(
        file="src/api/systems.py",
        timeout=60
    )
except TimeoutError as e:
    # Escalate: "I'm stuck, ask Claude for help"
    escalation = {
        "quest_id": "code_analysis_xyz",
        "escalated_by": "ollama:qwen2.5-coder",
        "escalate_to": "claude",
        "reason": "Timeout analyzing large file",
        "file": "src/api/systems.py",
        "lines": 5000,
        "context": str(e)
    }

    quest_log.add_entry({
        "message_type": "escalation",
        **escalation
    })

    # Claude receives escalation and switches approach
    result = claude_agent.analyze(
        file="src/api/systems.py",
        strategy="summarize_then_analyze"  # Different approach
    )
```

---

### Communication Channel 3: Result Handoff

**Purpose:** Pass completed work to next agent in pipeline

**Pattern:**
```python
# Copilot completes API design
design_result = {
    "api_endpoints": [
        {"method": "GET", "path": "/users", "params": ["skip", "limit"]},
        {"method": "POST", "path": "/users", "body": ["name", "email"]}
    ],
    "database_schema": {
        "users_table": ["id", "name", "email", "created_at"]
    },
    "authentication": "JWT"
}

# Hand off to ChatDev for implementation
handoff = {
    "message_type": "result_handoff",
    "sender": "copilot",
    "receiver": "chatdev:team_1",
    "phase": "design",
    "completed_at": datetime.now().isoformat(),
    "result": design_result,
    "next_phase": "implementation",
    "graduation_checkpoint": "code_ready_for_review"
}

quest_log.add_entry(handoff)

# ChatDev retrieves and starts implementation
pending_handoffs = quest_log.query(
    receiver="chatdev:team_1",
    message_type="result_handoff",
    status="pending"
)

for handoff in pending_handoffs:
    design = handoff["result"]
    chatdev_team.implement(design)
```

---

### Communication Channel 4: Consensus Request

**Purpose:** Get input from multiple agents before major decision

**Pattern:**
```python
# Before choosing architecture, ask multiple agents
consensus_request = {
    "message_type": "consensus_request",
    "sender": "copilot",
    "question": "Should we use async/await or sync+threads for background jobs?",
    "context": {
        "workload": "Process 10K emails per hour",
        "priority": "Latency critical",
        "team_size": 3
    },
    "deadline_hours": 1,
    "requested_from": ["ollama:qwen2.5-coder", "claude", "chatdev"],
    "voting_strategy": "ranked"
}

quest_log.add_entry(consensus_request)

# Agents receive and respond
agents = ["ollama:qwen2.5-coder", "claude"]
responses = []

for agent_name in agents:
    response = {
        "message_type": "consensus_response",
        "responder": agent_name,
        "request_id": consensus_request["message_type"],
        "recommendation": "async/await",
        "confidence": 0.85,
        "rationale": "asyncio better for I/O-bound email processing"
    }
    quest_log.add_entry(response)
    responses.append(response)

# Aggregate votes
votes = [r["recommendation"] for r in responses]
winner = max(set(votes), key=votes.count)
print(f"Consensus: {winner}")
```

---

### Communication Channel 5: Status Updates

**Purpose:** Keep other agents informed of progress without blocking

**Pattern:**
```python
# ChatDev updating Copilot on implementation progress
status_update = {
    "message_type": "status_update",
    "sender": "chatdev:team_1",
    "context_quest": "feature_xyz_implementation",
    "progress_percent": 45,
    "current_task": "Implementing database migrations",
    "completed_milestones": [
        "API design doc created",
        "FastAPI project scaffolded",
        "Database models defined"
    ],
    "next_milestone": "API endpoints implementation",
    "estimated_remaining_minutes": 30,
    "blockers": []
}

quest_log.add_entry(status_update)

# Copilot checks progress
progress = quest_log.query(
    context_quest="feature_xyz_implementation",
    message_type="status_update",
    sender="chatdev:team_1"
)

if progress:
    latest = progress[-1]
    print(f"ChatDev progress: {latest['progress_percent']}%")
    print(f"ETA: {latest['estimated_remaining_minutes']} minutes")
```

---

### Communication Channel 6: Review Requests

**Purpose:** Ask another agent to review work before graduation

**Pattern:**
```python
# ChatDev asking Copilot for code review before including in canonical
review_request = {
    "message_type": "review_request",
    "sender": "chatdev",
    "receiver": "copilot",
    "artifact": "src/api/auth.py",
    "lines_of_code": 342,
    "checklist": [
        {"item": "No hardcoded secrets", "weight": 1.0},
        {"item": "Proper error handling", "weight": 0.8},
        {"item": "Type hints on all functions", "weight": 0.9},
        {"item": "Unit tests for auth logic", "weight": 0.7},
        {"item": "Docstrings on public methods", "weight": 0.6}
    ],
    "graduation_candidate": True,
    "target_location": "src/api/auth.py"
}

quest_log.add_entry(review_request)

# Copilot reviews and responds
review_response = {
    "message_type": "review_response",
    "sender": "copilot",
    "reviewer": "copilot",
    "request_id": review_request["artifact"],
    "approved": False,
    "checklist_scores": {
        "No hardcoded secrets": 1.0,
        "Proper error handling": 0.6,  # Found missing try/except
        "Type hints on all functions": 0.9,
        "Unit tests for auth logic": 0.3,  # Only 1 test
        "Docstrings on public methods": 1.0
    },
    "overall_score": 0.74,
    "approval_threshold": 0.80,
    "feedback": [
        {"line": 45, "issue": "Missing try/except around database call"},
        {"line": 120, "issue": "Only 1 unit test; need 5 minimum"},
        {"line": 200, "issue": "Hardcoded timeout value"}
    ],
    "graduation_approved": False,
    "next_steps": "Address feedback, request re-review"
}

quest_log.add_entry(review_response)
```

---

### Routing Decision Tree: Which Channel to Use

```
Agent A → Agent B
    ↓
Is it a query that needs a reply?
    ├─ YES: Consensus Request (Channel 4)
    │   └─ Need multiple opinions? → Consensus voting
    │   └─ Need single expertise? → Direct escalation (Channel 2)
    │
    ├─ NO: Is work being handed off?
    │   ├─ YES: Result Handoff (Channel 3)
    │   │   └─ Work complete, ready for next phase
    │   │
    │   └─ NO: Is this an error/blocker?
    │       ├─ YES: Error Escalation (Channel 2)
    │       │   └─ I'm stuck, need help
    │       │
    │       └─ NO: Is it just an update?
    │           ├─ YES: Status Update (Channel 5)
    │           │   └─ Keeping you informed
    │           │
    │           └─ NO: Is it a review?
    │               ├─ YES: Review Request (Channel 6)
    │               │   └─ Before graduation, I need your approval
    │               │
    │               └─ NO: General coordination?
    │                   └─ Quest Log Exchange (Channel 1)
    │                       └─ Store for any agent to read
```

---

### Agent Communication Best Practices

**✅ DO:**
- ✅ Always include `timestamp` for causality tracking
- ✅ Use `quest_id` to link messages to parent task
- ✅ Set clear expectations (deadline, format, acceptance criteria)
- ✅ Provide context sufficient for receiver to act independently
- ✅ Log all communication for audit trail
- ✅ Acknowledge receipt of handoffs

**❌ DON'T:**
- ❌ Assume the other agent reads messages instantly (always poll)
- ❌ Send vague requests without context or acceptance criteria
- ❌ Skip the review step before graduating code
- ❌ Leave messages without status (mark as "pending", "acknowledged", "completed")
- ❌ Send circular requests (A asks B, B asks A) without breaking the cycle
- ❌ Block waiting for response; use async patterns (poll, check later)

---

### Common Multi-Agent Workflows

#### Workflow A: Design → Implementation → Review → Graduation

```
Copilot (design)
    ↓ [Result Handoff]
ChatDev (implement)
    ↓ [Review Request]
Claude (review)
    ↓ [Review Response + Approval]
ChatDev (fix feedback)
    ↓ [Result Handoff]
Copilot (graduate to canonical)
```

#### Workflow B: Fast Problem with Fallback

```
Ollama:qwen (primary)
    ↓ [Timeout after 60s]
[Error Escalation]
    ↓
Claude (fallback)
    ↓ [Result returned]
Copilot (integrate result)
```

#### Workflow C: Parallel Experiments + Consensus

```
Copilot (design 3 approaches)
    ↓ [Consensus Request]
┌─ Ollama:qwen (approach A)
├─ Claude (approach B)
└─ ChatDev (approach C)
    ↓ [All respond in parallel]
[Aggregate votes]
    ↓
Winner approach handed to implementation team
```

---

"""

    # Insert the new section before the Quick Reference Card
    lines.insert(insert_line, new_section)

    # Write the file back
    with open(r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\docs\AGENT_TUTORIAL.md", "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("✅ Successfully inserted Agent Communication Protocol section")
    print(f"   Now {len(lines)} total lines in file")
    print(f"   Inserted before line {insert_line + 1}")
