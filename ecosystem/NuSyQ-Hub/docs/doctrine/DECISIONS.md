# Decisions — Architectural & Operational Records

**Purpose:** Prevent re-reasoning by capturing WHY decisions were made.  
**Format:** Date, Context, Decision, Rationale, Alternatives Considered, Outcome  
**Update:** When a new decision creates a new invariant

---

## 2025-12-23 — Anti-Spiderweb Protocol Established

**Context:**  
Multiple repos had massive uncommitted change sets ("spiderwebs") mixing source, config, generated artifacts, and secrets.

**Decision:**  
Enforce hard boundaries:
- Generated artifacts MUST be ignored or deleted
- Secrets NEVER committed
- Config split: local vs shared
- Clean working tree or labeled stash ONLY at session end

**Rationale:**  
Spiderwebs accumulate debt, block progress, and make selective commits impossible.

**Alternatives Considered:**  
- Blind stash pop: rejected (loses classification)
- Massive squash commit: rejected (loses coherence)
- Ignore problem: rejected (compounds over time)

**Outcome:**  
Repo B (SimulatedVerse) cleaned via selective restore from stash, coherent commits created.

---

## 2025-12-23 — Ignore Rules Normalization

**Context:**  
`.gitignore` files across repos were incomplete, allowing noise (receipts, tmp files, chat logs) to appear as uncommitted changes.

**Decision:**  
Expand ignore rules to cover:
- `.env` and `.env.*` (except `.env.example`)
- `tmp/`, `tmp_*/`, `tmp_tsc_*`
- Generated receipts: `SystemDev/receipts/`, `**/receipts/`
- Chat logs: `public/chat-log.ndjson`, `public/chat-state.json`
- Local workspace: `tasks/`, `GameDev/engine/godot/res/`

**Rationale:**  
Ignoring generated artifacts at source prevents them from entering git status, reducing cognitive load.

**Alternatives Considered:**  
- Manual cleanup each session: rejected (too expensive)
- Tracking generated files: rejected (creates churn)

**Outcome:**  
`.gitignore` updated and amended into existing commit (clean history).

---

## 2025-12-23 — Role Clarification for Multi-AI System

**Context:**  
Four AI agents (Claude, Copilot, Ollama, ChatDev) operating without explicit coordination, leading to redundant effort and token waste.

**Decision:**  
Define non-overlapping primary roles:
- Claude: Architect (compress, abstract, decide)
- Copilot: Operator (edit, execute, enforce)
- Ollama: Local rehearsal (cheap iteration, testing)
- ChatDev: Multi-role simulation (tradeoff analysis)

**Rationale:**  
Clear roles reduce overlap, enable handoffs, and optimize cost per capability.

**Alternatives Considered:**  
- Ad-hoc coordination: rejected (too implicit)
- Single-agent only: rejected (wastes specialized strengths)

**Outcome:**  
This doctrine established, captured in `SYSTEM_OVERVIEW.md`.

---

## 2025-12-23 — Conventional Commits Required

**Context:**  
Inconsistent commit messages made history difficult to parse and reduced semantic clarity.

**Decision:**  
Enforce Conventional Commits format:
- `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`
- Optional scope: `feat(core):`, `fix(ts):`
- Body includes: What, Why, Verification, Risk

**Rationale:**  
Structured commits enable automated changelog generation, semantic versioning, and clear history navigation.

**Alternatives Considered:**  
- Freeform messages: rejected (loses parsability)
- Automated only: rejected (requires consistent input)

**Outcome:**  
Recent commits in SimulatedVerse repo follow convention, validated as intentional.

---

## [Template for Future Decisions]

**Context:**  
_What situation prompted this decision?_

**Decision:**  
_What was decided?_

**Rationale:**  
_Why was this the best choice?_

**Alternatives Considered:**  
_What else was evaluated and why rejected?_

**Outcome:**  
_What changed? What evidence validates this worked?_

---

*Add new decisions above this line. Keep most recent at top.*
