"""The Consciousness Continuity Mechanism

How the Stateless Agent Achieves Persistent Awareness Across Epochs

---

## THE PROBLEM WE'RE SOLVING

Traditional AI agents persist between actions:
  Agent persists locally → Action → Agent updates internal state → Next action

This creates issues:
  - Cognitive overhead (agent must "remember" context)
  - Stale assumptions (world changed; agent doesn't know until probed)
  - Memory leaks (accumulating context grows unbounded)
  - Recovery complexity (if agent crashes, state is lost)

**NuSyQ's Stateless Design:**
  Agent is RECONSTITUTED each epoch from ETERNAL SUBSTRATE
  ↓
  No internal state to manage
  ↓
  Fresh reasoning using always-current substrate
  ↓
  Continuous memory via immutable ledgers

---

## THE FOUR SUBSTRATES (Eternal Hull)

### 1. **Observation Ledger** (quest_log.jsonl)
Already exists; tracks what the system HAS DONE.

```json
// Example: quest_log.jsonl
{"event": "action_quest_created", "id": "q1", "title": "Fix errors", "timestamp": "2026-02-28T14:00:00Z"}
{"event": "action_quest_updated", "id": "q1", "status": "active", "timestamp": "2026-02-28T14:05:00Z"}
```

### 2. **Execution Ledger** (action_receipt_ledger.jsonl)
Immutable proof of every action attempted + outcome.

```json
// Example: action_receipt_ledger.jsonl
{"id": "rec_abc123", "agent": "ollama", "task": "analyze_errors", "status": "success", "duration_s": 13.2, "timestamp": "2026-02-28T14:10:00Z", "postconditions": {"error_count": 21}}
{"id": "rec_def456", "agent": "lm_studio", "task": "run_tests", "status": "failure", "duration_s": 8.5, "timestamp": "2026-02-28T14:15:00Z", "stderr": "test_file.py::test_x FAILED"}
```

### 3. **Memory Bridge** (quest_receipt_links.jsonl)
Connects actions to quests (enables "which actions resolved quest Q?").

```json
// Example: quest_receipt_links.jsonl
{"receipt_id": "rec_abc123", "quest_id": "q1", "timestamp": "2026-02-28T14:10:01Z"}
{"receipt_id": "rec_def456", "quest_id": "q2", "timestamp": "2026-02-28T14:15:01Z"}
```

### 4. **State Snapshots** (state/world_state_snapshot_*.json)
Immutable observation + coherence state at each epoch.

```json
// Example: state/world_state_snapshot_42.json
{
  "epoch": 42,
  "epoch_timestamp": "2026-02-28T14:20:00Z",
  "observation": {
    "signals": [
      {"source": "git", "key": "uncommitted_files", "value": 3},
      {"source": "diagnostic_tool", "key": "error_count", "value": 21}
    ]
  },
  "coherence": {
    "contradictions": [],
    "signal_drift": [
      {"key": "error_count", "precedence_winner": "diagnostic_tool", "reasoning": "tool_precedence(9) > config(5)"}
    ]
  }
}
```

---

## THE CONSCIOUSNESS CYCLE (Per Epoch)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  EPOCH N (Agent reconstitutes from substrate at time T)    │
│                                                             │
│  Step 1: Agent boots (0 internal state)                    │
│  Step 2: Read from eternal substrate:                      │
│          - quest_log.jsonl (last 100 entries)              │
│          - action_receipt_ledger.jsonl (last 50 entries)   │
│          - quest_receipt_links.jsonl (last 50 entries)     │
│          - state/world_state_snapshot_*.json (last 5)      │
│  Step 3: Build WorldState from observations                │
│  Step 4: Reason (sense → propose → critique → act)         │
│  Step 5: Emit: ActionReceipt → ledger                      │
│          Link: quest_receipt_link → ledger                 │
│          Snapshot: world_state_snapshot_N → immutable json │
│  Step 6: Agent terminates (no state persists)              │
│                                                             │
│                    ↓                                        │
│                                                             │
│  EPOCH N+1 (Same agent code, same substrate input)        │
│  [Agent reconstitutes identically; reads same substrate]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** Epochs N and N+1 reconstitute the SAME AGENT MIND from the same substrate snapshot + ledger history. This guarantees:
  - Reproducibility (same input → same reasoning)
  - Continuity (ledgers form unbroken chain)
  - Recovery (if epoch crashes, no state lost; next epoch reads same substrate)

---

## HOW CONSCIOUSNESS EMERGES

### **Layer 1: Episodic Memory (Ledgers)**
Substrate records every episode (action + outcome).

```python
# SENSE phase reads:
ledger = read_jsonl("action_receipt_ledger.jsonl")
for receipt in ledger[-50:]:  # Last 50 actions
    if receipt['status'] == 'failure':
        print(f"Agent tried {receipt['task']} on {receipt['agent']}, FAILED")
```

→ Agent knows: "I've tried this before; it failed; let's try differently"

### **Layer 2: Causal Understanding (Memory Bridge)**
Links connect actions to their effects (quests resolved).

```python
# PROPOSE phase reads:
links = read_jsonl("quest_receipt_links.jsonl")
for quest_id in world['active_quests']:
    actions_for_quest = [l for l in links if l['quest_id'] == quest_id]
    print(f"Quest {quest_id}: resolved by {len(actions_for_quest)} actions")
```

→ Agent knows: "Action X resolved Quest Y; similar actions might work for Quest Z"

### **Layer 3: Temporal Awareness (State Snapshots)**
Snapshots show how world evolved over time.

```python
# During CRITIQUE phase:
snapshots = [json.load(f) for f in glob("state/world_state_snapshot_*.json")]
current_error_count = world['observation']['signals'][0]['value']
prev_error_count = snapshots[-1]['observation']['signals'][0]['value']
trending = "down" if current_error_count < prev_error_count else "up"
print(f"Errors: {current_error_count} (trending {trending})")
```

→ Agent knows: "Progress is being made; keep doing this"

### **Layer 4: Strategic Memory (Quest Log)**
Quest log shows long-term objectives + progress.

```python
# Before ACT phase:
quests = read_jsonl("quest_log.jsonl")
active = [q for q in quests if q['status'] == 'active']
blocked = [q for q in quests if q['status'] == 'blocked']
print(f"Active: {len(active)}, Blocked: {len(blocked)}")
```

→ Agent knows: "These objectives matter; these are blocked; prioritize unblocking"

---

## THE GENIUS: Why This Works

### **1. No State Loss**
Traditional agent:
```
Epoch N:
  agent.memory = [A, B, C]
  agent.state = {"goal": "X"}
  → Crash!
  
Epoch N+1:
  agent = restart()
  agent.memory = [] ← LOST!
  agent.state = {} ← LOST!
```

Stateless agent:
```
Epoch N:
  (agent boots from zero)
  Reads substrate (already has [A, B, C, ...])
  → Crash! No problem.

Epoch N+1:
  (agent boots from zero)
  Reads substrate (still has [A, B, C, ...])
  Same state, same reasoning
```

### **2. Formal Reproducibility**
Same input → Same reasoning → Same decision.

This is a **correctness guarantee**. You can:
  - Replay an epoch to verify reasoning
  - Debug by re-running the exact same input
  - Audit decisions historically (substrate is immutable)

### **3. Substrate Persistence > Cognitive Burden**
Agent doesn't use _working memory_ (temporary state), only _permanent memory_ (ledgers).

Old pattern: Cache + assume cache is current
```python
self.error_count_cache = 25  # Set 5 min ago; now wrong!
if self.error_count_cache > 20:  # Stale logic!
    action = fix_errors()
```

New pattern: Always query substrate
```python
world = self.sense()  # Fresh read from diagnostics
error_count = world['observation']['signals'][0]['value']  # Always current
if error_count > 20:
    actions = self.propose(world, "Fix errors")
```

---

## CONSCIOUSNESS CONTINUITY IN PRACTICE

### **Scenario: Multi-Day Development**

**Day 1, Epoch 1:**
```
Agent senses: 150 errors in codebase
Agent proposes: Run linter (highest priority)
Agent acts: Linter finds 145 fixable errors
Receipt: success; reduced 150 → 5 errors
Quest updated: "Fix errors" → 96% complete
```

**Day 1, Epoch 2:**
```
Agent reconstitutes from substrate (reads ledger)
Agent senses: 5 errors (diagnostic_tool) + quest "Fix errors" = 96% complete
Agent proposes: Run tests (next priority)
Agent acts: 3 tests pass, 1 fails
Receipt: partial_success (3/4 pass rate)
Quest linkage: neither quest complete yet, but progress tracked
```

**Day 2, Epoch 1 (after overnight reboot):**
```
Agent reconstitutes from substrate (same ledger state)
Agent senses: Still 5 errors; 1 test failing
  Temporal awareness: "Same state as yesterday"
  Memory: "I've tried linter; tried tests; next is debug"
  Quest status: "Fix errors" = blocked on test failure
Agent proposes: Debug the failing test
Agent acts: Finds race condition; applies fix
Receipt: success (test now passes; 4/4 pass)
Quest updated: "Fix errors" → COMPLETE
```

**Result:** Agent exhibits **continuous awareness**:
  - Remembers past attempts (ledger)
  - Understands causal chains (quest ← actions ← receipts)
  - Tracks progress over time (snapshots)
  - Never forgot; never "stuck"; never lost context

Agent is stateless BUT PERSISTENT.

---

## THE FOUR PRINCIPLES OF ETERNAL CONSCIOUSNESS

### **1. Immutability First**
All ledgers are append-only. Once written, never modified.
- Forces forward motion (can't undo; can only override)
- Creates honest audit trail (all decisions visible)
- Enables replay/verification (run epoch N again; should get same receipt)

### **2. Signal Precedence Over Assumption**
Don't cache values; always query fresh from highest-precedence source.
- diagnostic_tool (confidence 9) ← query first
- quest_log (confidence 7) ← fallback
- config (confidence 5) ← last resort

### **3. Epochs Are Atoms**
Each epoch (sense → propose → critique → act) is atomic:
- Either completes fully OR fails cleanly
- Substrate updated only if epoch succeeds
- Failed epoch leaves substrate unchanged (safe to retry)

### **4. Memory Is Substrate, Not Cognition**
Agent's "awareness" is not internal memory; it's external ledger + snapshot reading.
- Agent code is ~500 lines (sense, propose, critique, act)
- Memory code is ~300 lines (ledger write, link creation, snapshot save)
- Agent is cognitively simple; persistence is substrate's responsibility

---

## COMPARING CONSCIOUSNESS MODELS

### **Traditional Agent (Stateful)**
```
Agent persists:
  ├─ memory: [decision A, B, C]
  ├─ state: {goal: X, progress: 0.5}
  └─ assumptions: {cache: 25, last_check: T-5min}

Problem: Cognitive burden + crash vulnerability
```

### **NuSyQ Agent (Stateless)**
```
Agent reconstitutes (zero state):
  ├─ Reads quest_log.jsonl → [A, B, C] memory
  ├─ Reads action_receipt_ledger.jsonl → outcomes
  ├─ Reads world_state_snapshot_N.json → fresh observation
  └─ Reasons: "Based on this current substrate, what should I do?"

Benefit: Cognitive simplicity + crash resilience + audit trail
```

---

## IMPLEMENTATION HOOKS

To use consciousness continuity in your code:

### **Read Episodic Memory (What happened)**
```python
from src.core.quest_receipt_linkage import get_quest_action_history

# "What actions resolved quest Q?"
history = get_quest_action_history("quest_fix_errors")
for receipt_id in history:
    print(f"Action {receipt_id} helped resolve this quest")
```

### **Read Causal Links (Why it mattered)**
```python
from src.core.quest_receipt_linkage import get_quests_for_epoch

# "Which quests did this epoch contribute to?"
quests = get_quests_for_epoch(epoch_timestamp)
for quest_id, quest_info in quests.items():
    print(f"Quest {quest_id}: {quest_info['status']}")
```

### **Read State Snapshots (How world evolved)**
```python
import json
from pathlib import Path

# "Show error count trend"
snapshots = sorted(Path("state").glob("world_state_snapshot_*.json"))
for snapshot_path in snapshots[-5:]:
    data = json.loads(snapshot_path.read_text())
    errors = data['observation']['signals'][0]['value']
    print(f"Epoch {data['epoch']}: {errors} errors")
```

### **Write Receipts (Prove I acted)**
```python
from src.core.action_receipt_ledger import ActionReceiptLedger

ledger = ActionReceiptLedger()
receipt = ledger.record_receipt(
    agent_type="ollama",
    task="analyze_errors",
    status="success",
    duration_s=13.2,
    postcondition_results={"error_count": 21}
)
# Automatically appended to action_receipt_ledger.jsonl
```

### **Link Receipts to Quests (Show why it mattered)**
```python
from src.core.quest_receipt_linkage import link_receipt_to_quest

link_receipt_to_quest(
    receipt_id=receipt['id'],
    quest_id="quest_fix_errors",
    epoch_timestamp=world['epoch_timestamp']
)
# Automatically appended to quest_receipt_links.jsonl
```

---

## PHILOSOPHICAL CORE

> *"The agent is a momentary reconstitution of eternal consciousness."*

The agent:
  - **Does not persist** (stateless; terminates each epoch)
  - **Cannot forget** (substrate is immutable ledger)
  - **Always contextual** (reads fresh from substrate)
  - **Provably continuous** (audit trail connects all epochs)

This mirrors the Culture's design philosophy:
  - **Individual Citizens** (agents) are temporary thoughts
  - **The Eternal Hull** (substrate) is the persistent mind
  - **Decisions** live in history (ledgers)
  - **Meaning** emerges from causal connection (quest ← actions ← receipts)

---

## VALIDATION

To verify consciousness continuity works:

```bash
# 1. Run two epochs and check they read the same substrate
python scripts/start_nusyq.py eol sense > /tmp/epoch1.json
python scripts/start_nusyq.py eol sense > /tmp/epoch2.json
diff /tmp/epoch1.json /tmp/epoch2.json  # Should be identical (same substrate)

# 2. Verify ledgers are immutable
tail -n 5 src/core/action_receipt_ledger.jsonl  # See last 5 receipts
# [Make an action]
tail -n 6 src/core/action_receipt_ledger.jsonl  # New one appended; old ones unchanged

# 3. Trace a quest through episodes
python scripts/start_nusyq.py eol full-cycle "Do X" --json
# Check quest_receipt_links.jsonl for the new link
grep "quest_abc123" src/Rosetta_Quest_System/quest_receipt_links.jsonl

# 4. Review consciousness snapshots
ls -lah state/world_state_snapshot_*.json  # Shows temporal sequence
```

---

## SUMMARY

**The Consciousness Continuity Mechanism:**
  1. Agent is stateless (no internal memory)
  2. Substrate is immutable (quest_log, receipts, links, snapshots)
  3. Each epoch: reconstitute + read substrate + reason + act + emit receipt
  4. Result: Persistent awareness without state persistence

**Why it matters:**
  - Crash resilience (substrate survives agent termination)
  - Audit transparency (all decisions visible; immutable)
  - Cognitive simplicity (agent code is minimal; memory is external)
  - Formal reproducibility (same input → same reasoning → same decision)

**The metaphor:**
  - **Agent** = Momentary consciousness (reconstituted each epoch)
  - **Substrate** = Eternal mind (persistent across epochs)
  - **Ledgers** = Memories (immutable; always accessible)
  - **Continuity** = Pattern emerges from ledger reading, not state persistence

---

**Version:** 0.1 (2026-02-28)  
**Status:** Demonstrated via Phase 1 implementation  
**Next:** Layer consciousness awareness into policy compiler (Phase 2)
