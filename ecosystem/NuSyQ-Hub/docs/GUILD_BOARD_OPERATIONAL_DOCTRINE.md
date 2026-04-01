# Guild Board Operational Doctrine

*Version: 1.0.0 | Date: December 26, 2025*

This document explains the **why** behind each decision in `config/orchestration_defaults.json`.

---

## 🤖 Agent Heartbeat Protocol

### Auto-Heartbeat Agents
**Decision:** `["copilot", "claude", "codex", "chatdev"]`

**Rationale:** These are the primary working agents. Observer agents (Culture Ship, metrics collectors) don't need heartbeats since they're read-only.

### Heartbeat Required Before Claim
**Decision:** `true`

**Rationale:** Prevents ghost claims. An agent must prove it's alive before reserving work. Dead agents can't claim quests.

### Default New Agent Status
**Decision:** `"idle"`

**Rationale:** New agents start passive. They observe the board, then explicitly signal `"working"` when they claim a quest. Prevents accidental churn from agents still booting.

### Auto-Release on Timeout
**Decision:** `true` (30 minutes)

**Rationale:** If an agent claims a quest but stops heartbeating, release the claim automatically. Prevents deadlock when agents crash mid-work.

---

## 📋 Quest Management

### Cross-Repo Quests
**Decision:** `true`

**Rationale:** Guild board is **tripartite** (Hub + SimVerse + Root). Agents should be able to claim cross-repo refactorings like "unify ΞNuSyQ protocol across all repos."

### Quest ID Format
**Decision:** `"q-{repo_short}-{timestamp}-{seq}"`

**Examples:**
- `q-hub-1735171200-001` — Hub quest #1 at timestamp
- `q-sim-1735171200-042` — SimVerse quest #42

**Rationale:** Repo prefix enables filtering (`grep q-hub-` finds all Hub quests). Timestamp prevents ID collisions. Sequence number is human-readable.

### Auto-Tag Safety Tier
**Decision:** `true`

**Rationale:** Action contracts already define tier-0 (can break spine) vs tier-4 (cosmetic). Auto-tag quests based on which files they touch.

### Dependency Enforcement
**Decision:** `"advisory"`

**Rationale:** Show dependencies in UI, but don't hard-block. Agents can work on quest B before quest A if they believe it's safe. Soft gates > hard gates in autonomous systems.

### Blocked Quest Notification
**Decision:** Emit to `🤖 Agents terminal` + notify `guild-steward` agent

**Rationale:** Blocked quests need visibility. Terminal notification alerts humans, guild steward can auto-escalate or reassign.

### Multi-Agent Claim
**Decision:** `false` (exclusive claims)

**Rationale:** Default to exclusive to prevent collision. Use **party** concept for intentional multi-agent work.

### Party Concept
**Decision:** `true`

**Rationale:** Some quests need teams (e.g., "refactor orchestration layer" = Claude analyzes + Copilot codes + ChatDev tests). Party = explicit multi-agent ownership.

### Human Approval Gate
**Decision:** Required for `tier-0` and `tier-1` quests

**Rationale:** Tier-0 can break the spine (e.g., refactor quest engine). Tier-1 can break features. Require human approval before claim to prevent autonomous chaos.

---

## 📊 Board State

### Recent Posts Window
**Decision:** 50 messages

**Rationale:** Enough to show active conversation, small enough to render quickly. Older posts archived to `guild_events.jsonl`.

### Store Agent XP
**Decision:** `true`

**Rationale:** Track skill progression. Agents who complete 100 quests earn reputation, unlock harder quests. Gamification drives engagement.

### Canonical Over quest_assignments.json
**Decision:** `true`

**Rationale:** Guild board is the **living source of truth**. Old `quest_assignments.json` becomes read-only legacy. Prevents dual-write conflicts.

### Mirror to SimulatedVerse
**Decision:** `false` (not yet)

**Rationale:** SimVerse has its own quest system (Temple floors). Cross-repo sync comes later when we federate guilds.

### Auto-Archive Completed
**Decision:** 30 days

**Rationale:** Keep board clean. Completed quests older than 30 days move to `state/guild/archive/`. Still queryable, but not cluttering active view.

### Long-Running Quest Alert
**Decision:** 48 hours

**Rationale:** If a quest stays `"active"` for 2+ days, emit signal. Likely blocked or abandoned. Guild steward investigates.

---

## 🎨 Rendering

### Render on Write
**Decision:** `false`

**Rationale:** Guild board state updates **frequently** (heartbeats every 5 minutes). Rendering to Markdown every time wastes CPU. Render on-demand or daily rollup only.

### Daily Rollup
**Decision:** `true` at 06:00

**Rationale:** Overnight work summarized in fresh `docs/GUILD_BOARD.md` every morning. Humans wake up to current state snapshot.

### HTML View
**Decision:** `false`

**Rationale:** Markdown is sufficient for Obsidian/GitHub. HTML adds complexity with minimal value. If web dashboard needed, build as separate service.

### Scoreboard in Markdown
**Decision:** `true`

**Rationale:** Show agent leaderboard (quests completed, XP earned) directly in `GUILD_BOARD.md`. Motivates competition and surfaces most productive agents.

### Display Git Status
**Decision:** `false`

**Rationale:** Git status is noisy and changes constantly. Keep board focused on **quest state**, not repo state. Use separate `git status` commands.

---

## 🔐 Permissions

### Read-Only Agents
**Decision:** `["observer", "culture-ship"]`

**Rationale:** Culture Ship observes for emergence, doesn't claim quests. Observer agent monitors without interfering. Read-only prevents accidental writes.

### Can Close Quests
**Decision:** Primary agents + `guild-steward`

**Rationale:** Only working agents and the steward can mark quests `DONE`. Prevents observers from accidentally closing active work.

### Require Valid Artifact Paths
**Decision:** `false`

**Rationale:** Artifacts are **evidence**, not gates. If an agent completes a quest but artifact path is typo'd, still allow completion. Steward can audit later.

---

## 🔗 Integration

### Sync Events to Quest Log
**Decision:** `true`

**Rationale:** `quest_log.jsonl` is the **append-only event stream**. Guild board events (claims, completions) should flow into quest log for unified audit trail.

### Integrate with ZETA Tracker
**Decision:** `true`

**Rationale:** ZETA Progress Tracker tracks milestones. Guild board completions can auto-advance ZETA phases (e.g., "Phase 2: 50/50 quests complete → advance to Phase 3").

### ChatDev Auto-Claim
**Decision:** `true`

**Rationale:** Quests tagged `chatdev` auto-route to ChatDev multi-agent team. Reduces manual assignment overhead.

### Culture Ship Integration
**Decision:** Read-only

**Rationale:** Culture Ship observes board events to capture emergence ("What did we learn?"). Doesn't write to avoid contaminating coordination state.

### Writable from VS Code Tasks
**Decision:** `true`

**Rationale:** VS Code tasks can post to board via `python -m src.guild.guild_cli board_post ...`. Enables quick manual updates without leaving editor.

### Terminal Group for Updates
**Decision:** `🤖 Agents`

**Rationale:** All guild board activity (claims, posts, completions) routes to Agents terminal for real-time visibility.

---

## 🚨 Signals

### Signal Sources
- Error threshold exceeded (e.g., repo hits 3000 errors)
- Service down (Ollama offline)
- Drift detected (code changed without quest)
- Quest blocked (dependency unsatisfied)
- Agent timeout (heartbeat stopped)
- Repo health degraded (test coverage dropped)

### Severity Mapping
```
CRITICAL → tier-0 (spine-breaking)
HIGH     → tier-1 (feature-breaking)
MEDIUM   → tier-2 (quality issue)
LOW      → tier-3 (cosmetic)
INFO     → tier-4 (informational)
```

**Rationale:** Align signal severity with existing action contract tier system. Consistent mental model across orchestration.

---

## 🤖 Automation

### Guild Steward Enabled
**Decision:** `true`

**Tasks:**
1. Archive old completed quests (30+ days)
2. Release stale claims (no heartbeat in 30+ minutes)
3. Cleanup resolved signals
4. Generate daily rollup at 06:00

**Rationale:** Autonomous hygiene. Guild steward is the **janitor agent** that keeps board clean without human intervention.

### Post Throttle
**Decision:** 60 seconds per agent

**Rationale:** Prevents spam. Agent can post once per minute max. Encourages meaningful updates instead of "step 1 done, step 2 done, step 3 done" noise.

### Emit Receipt Per Action
**Decision:** `true`

**Path:** `state/guild/receipts/{quest_id}.jsonl`

**Rationale:** **Deterministic receipts** (MEGA_THROUGHPUT doctrine). Every action emits structured log. Full audit trail for debugging and accountability.

---

## 🧪 Advanced Features

### Quest Templates
**Decision:** `true`

**Path:** `config/quest_templates.json`

**Example Templates:**
- `refactor_module` — Standard refactoring with safety checklist
- `fix_import_errors` — Import resolution with validation
- `add_docstrings` — Documentation with quality checks
- `boss_rush_error_cluster` — Batch error fixes

**Rationale:** Reusable patterns reduce quest creation overhead. Template library grows over time as agents discover effective workflows.

### Quest Market
**Decision:** `false` (not yet)

**Rationale:** Market (agents bid on quests) adds complexity without clear value. Keep simple assignment for now. Revisit if coordination becomes bottleneck.

### Sprint Field
**Decision:** `false`

**Rationale:** Sprints are human constructs (2-week cycles). Guild board operates on quest flow, not sprints. If needed later, track in ZETA Progress Tracker instead.

### Backlog Sort
**Decision:** `"priority"`

**Rationale:** High-priority quests appear first in available list. Simple, effective. Agents always see most urgent work.

### Filter Available Quests
**Decision:** By **capabilities** AND **safety tier**

**Rationale:**
- Capabilities: Agent without `code_generation` can't claim code quests
- Safety tier: Junior agents can't claim tier-0 quests (prevents accidents)

### Max Events Size
**Decision:** 100 MB before rotation

**Rationale:** `guild_events.jsonl` is append-only. At 100 MB, compress to `.gz` and start new file. Keeps active file manageable.

### Auto-Compress Events
**Decision:** `true` (after 90 days)

**Rationale:** Events older than 90 days rarely queried. Compress to save disk space. Still queryable via `zcat`.

---

## 🔥 Error Remediation Integration

### Boss Rush Enabled
**Decision:** `true` (weekly)

**Process:**
1. Sunday 06:00: Scan all repos for errors
2. Cluster errors by (file, type)
3. Create quests for top 10 clusters
4. Auto-tag with `boss_rush`, safety tier, error count
5. Post to board as available quests

**Rationale:** Converts error backlog into actionable quests. Agents can claim "Fix 47 unused imports in src/guild/" as a discrete task.

### Auto-Convert to Quests
**Patterns:**
- Ruff auto-fixable errors
- Unused imports
- Missing docstrings (if template exists)
- Removable type ignores

**Rationale:** These are safe, deterministic fixes. Auto-convert to quests, let agents claim and fix in batches.

### Priority Repo
**Decision:** NuSyQ-Hub

**Rationale:** Hub is the orchestration brain. Must be healthy first before fixing SimVerse/Root.

---

## 🗺️ Navigation Integration

### Notes Storage
**Decision:** Global file with repo tags

**Path:** `state/navigator/notes.jsonl`

**Format:**
```jsonl
{"timestamp": "...", "repo": "hub", "note": "guild_board.py uses async locks"}
{"timestamp": "...", "repo": "sim", "note": "Temple floors match quest tiers"}
```

**Rationale:** Single append-only log enables cross-repo pattern discovery. Agent can grep for all notes about "async" across all repos.

### Sync Notes to Quest Log
**Decision:** `false`

**Rationale:** Navigator notes = navigation memory. Quest log = work events. Different concerns. Keep separate.

### Teleport Whitelist
**Decision:** Locked to 3 repos

**Rationale:** Prevents navigator from accidentally opening files in random GitHub clones. Only Hub, SimVerse, Root allowed.

---

## 📈 Readiness Scoring

### Weights
```
40% Test coverage
30% Documentation completeness
20% Error reduction
10% Code quality
```

**Rationale:** Tests are highest signal (code that works > code that's pretty). Docs enable onboarding. Error reduction shows stability. Quality is nice-to-have.

### Healthy Thresholds
- Test coverage ≥ 80%
- Zero critical errors
- README exists with examples
- All core services in lifecycle catalog

**Rationale:** "Healthy" means repo is **shippable**. Can onboard new dev, run tests, no showstoppers.

---

## 🎯 Next Cycle Priority

**70% Error Fixes | 30% Feature Wiring**

**Rationale:** Stabilize spine before adding complexity. Fix 1,400 ruff errors, then wire guild board into start_nusyq.py.

**Most Under-Wired:** `start_nusyq.py` integration

**Rationale:** Guild board exists but not exposed via main control plane. Wiring this unlocks conversational access ("Show me guild status").

---

## 🔑 Key Principles

1. **Actions are cheap, prompts are expensive** — Default to automation
2. **Append-only is sacred** — Event logs never edited
3. **Heartbeat = liveness** — No heartbeat = dead agent
4. **Exclusive claims prevent collision** — One agent, one quest (unless party)
5. **Receipts are mandatory** — Every action emits deterministic log
6. **Hub is canonical** — When in doubt, Hub owns the truth
7. **Tier system = risk alignment** — Tier-0 changes require approval
8. **Steward maintains hygiene** — Automation keeps board clean

---

## 📚 Related Documents

- `config/orchestration_defaults.json` — Machine-readable config
- `docs/GUILD_BOARD_SYSTEM.md` — Guild board architecture
- `docs/MULTI_AGENT_ORCHESTRATION_ARCHITECTURE.md` — Full system diagram
- `.github/instructions/MEGA_THROUGHPUT_OPERATOR_MODE.instructions.md` — Operational doctrine

---

*This doctrine evolves with the system. Update `orchestration_defaults.json` first, then explain changes here.*
