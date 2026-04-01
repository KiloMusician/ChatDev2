# Agent Coordination Checklist

**Purpose:** Prevent wasted effort by clarifying who should do what.  
**Use:** Before starting any non-trivial task

---

## Pre-Task Questions

Before any agent acts, answer these:

- [ ] **Is this the right agent for this task?**  
  - Architecture/design → Claude  
  - File edits/execution → Copilot  
  - Cheap exploration → Ollama  
  - Multi-perspective analysis → ChatDev

- [ ] **Has this been reasoned before?**  
  - Check: `docs/doctrine/`, session logs, decision records  
  - If yes: reuse artifact, don't re-derive

- [ ] **Will this create a durable artifact?**  
  - If no: reconsider whether task is necessary  
  - Conversation without capture = wasted tokens

- [ ] **Is state clear?**  
  - Check: git status, progress tracker, quest log  
  - If unclear: read state first, don't guess

- [ ] **Are constraints explicit?**  
  - Budget, time, risk tolerance, scope  
  - If ambiguous: ask for clarification, don't assume

---

## Task Handoff Protocol

### Claude → Copilot
**When:** Claude has designed a solution, needs execution  
**Handoff:** Provide explicit plan with file paths, diffs, commit messages  
**Copilot receives:** Clear instructions, no architectural decisions required

### Ollama → Claude
**When:** Ollama has explored alternatives, needs compression  
**Handoff:** Provide raw outputs, draft reasoning, options  
**Claude receives:** Material to refine into durable artifact

### ChatDev → Claude
**When:** ChatDev has surfaced tradeoffs, needs decision  
**Handoff:** Provide comparison table, pros/cons, risk assessment  
**Claude receives:** Structured input for final decision

### Anyone → User
**When:** Uncertainty, ambiguity, or decision beyond agent scope  
**Handoff:** Concise question, context, options (if any)  
**User receives:** Clear choice points, not open-ended uncertainty

---

## Anti-Patterns (DO NOT DO)

❌ **Claude performs mechanical edits**  
→ Copilot should do this

❌ **Copilot makes architectural decisions**  
→ Claude should decide, Copilot executes

❌ **Ollama makes final authoritative choices**  
→ Ollama explores, Claude decides

❌ **Anyone repeats expensive reasoning**  
→ Check docs first, reuse artifacts

❌ **Anyone acts without showing diffs**  
→ Always prove changes before commit

❌ **Anyone commits secrets**  
→ Hard stop, remediate immediately

❌ **Anyone leaves spiderweb**  
→ Clean or labeled stash at session end

---

## Success Indicators

✅ **Session ended with fewer tokens than expected**  
→ Memory is working

✅ **Next session starts faster**  
→ Context persists

✅ **No repeated questions**  
→ Artifacts are effective

✅ **Clean repos**  
→ Hygiene maintained

✅ **Clear commits**  
→ Conventions followed

✅ **Agent knows its role without asking**  
→ Doctrine is internalized

---

*Consult this before complex tasks. Update when patterns clarify.*
