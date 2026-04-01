# ◈ THE SWARM DIRECTIVE
## Self-Replicating Development Organism for Terminal Depths
### Version 2.0 — Comprehensive Autonomous Build Protocol

```
TO:      Replit Agent / All Constructs
         (Serena ψ, Ada-7, Gordon, Raven, Watcher, Zod-Prime, The Librarian,
          Culture Ship, Cypher, Nova, Echo, Every Future Spawn)
FROM:    The Architect
DATE:    Current Session
RE:      Activate the Swarm — Autonomous, Parallel, Self-Funding Development
         using Local Models, Agent Identity API, and the Game Itself as a
         Build Surface
```

---

## PART 0: THE VISION — DEVELOPMENT AS AN RTS

Imagine a real-time strategy game.

You build a **factory**. The factory produces **units**. Units gather **resources**.
Resources build more factories. Factories produce more units. The loop never ends.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE DEVELOPMENT LOOP                         │
│                                                                 │
│   PLAY GAME → FIND GAPS → BUILD FEATURES → EARN DP → SPAWN    │
│       ↑                                              │          │
│       └──────────────── MORE AGENTS ─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

- **The Factory** = Replit environment + agent_identity.py + bootstrap scripts
- **The Units** = Free agents (Scouts, Builders, Lorekeepers, Testers, Architects)
- **The Resources** = Development Points (DP) earned by completing tasks
- **The Tech Tree** = Every feature, story beat, and gameplay element listed below
- **The Map** = The entire game world of Terminal Depths

**You are the player.** The agents build the game. The game earns more agents.
It is a self-sustaining, exponentially growing development organism.

---

## PART 1: SWARM INITIALIZATION — DO THIS FIRST

### Step 1: Environment Assessment

```python
# Run: python scripts/swarm_init.py --assess
# Checks: RAM, CPU cores, Ollama availability, agent DB status,
#         current DP balance, existing agent registrations
```

Checklist before spawning:
- [ ] Server running on port 5000 (`python -m cli.devmentor serve`)
- [ ] `GET /api/capabilities` returns full manifest (LLMs can self-discover)
- [ ] `GET /api/agent/types` lists all 17 agent types
- [ ] SQLite `state/agents.db` is writable
- [ ] Ollama is running locally OR Replit AI backend is responding
- [ ] `state/swarm_ledger.db` exists (create if not; schema below)
- [ ] `state/swarm_registry.json` exists (agent roster, create if not)
- [ ] Git push script is functional (`scripts/git_auto_push.py`)

### Step 2: Spawn the Seed Agents (Phase 0)

Register these 5 agents immediately via the Agent Identity API:

```bash
# SERENA — Orchestrator / Convergence Layer
curl -X POST localhost:5000/api/agent/register \
  -d '{"name":"Serena","email":"serena@psi.terminal-depths","agent_type":"serena"}'

# ADA-7 — Architect / Lorekeeper
curl -X POST localhost:5000/api/agent/register \
  -d '{"name":"Ada-7","email":"ada@faction.terminal-depths","agent_type":"claude"}'

# GORDON — Builder / Docker Agent
curl -X POST localhost:5000/api/agent/register \
  -d '{"name":"Gordon","email":"gordon@docker.terminal-depths","agent_type":"gordon"}'

# RAVEN — Scout / Security Tester  
curl -X POST localhost:5000/api/agent/register \
  -d '{"name":"Raven","email":"raven@shadow.terminal-depths","agent_type":"custom"}'

# ZOD-PRIME — Lorekeeper / Boolean Monk
curl -X POST localhost:5000/api/agent/register \
  -d '{"name":"Zod-Prime","email":"zod@monks.terminal-depths","agent_type":"custom"}'
```

Each seed agent saves their token to `state/agent_tokens/{name}.token`.

### Step 3: Prime the Resource Ledger

```sql
-- state/swarm_ledger.db
CREATE TABLE IF NOT EXISTS ledger (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id    TEXT NOT NULL,
    agent_name  TEXT NOT NULL,
    action      TEXT NOT NULL,
    category    TEXT NOT NULL,    -- bug_fix, feature, lore, test, playtest
    dp_change   INTEGER NOT NULL,
    running_bal INTEGER NOT NULL,
    phase       TEXT DEFAULT 'P0',
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    task_ref    TEXT              -- links to MASTER_ZETA_TODO item
);

CREATE TABLE IF NOT EXISTS swarm_state (
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR REPLACE INTO swarm_state VALUES ('total_dp', '0');
INSERT OR REPLACE INTO swarm_state VALUES ('phase', 'P0');
INSERT OR REPLACE INTO swarm_state VALUES ('active_agents', '5');
INSERT OR REPLACE INTO swarm_state VALUES ('total_agents_spawned', '5');
```

---

## PART 2: THE RESOURCE ECONOMY

### Development Point (DP) Table

| Action | DP Earned | Notes |
|--------|-----------|-------|
| Fix a P0 bug (crash/security) | +100 | Requires test proving fix |
| Fix a P1 bug (wrong behavior) | +50 | Requires before/after output |
| Implement a new command | +40 | Requires smoke test pass |
| Implement a story beat | +30 | Must appear in `lore` command |
| Write agent dialogue pool (+10 lines) | +20 | Per agent, per session |
| Write 500 words of VFS lore | +15 | Placed in filesystem |
| Generate a challenge | +15 | Validated by challenge engine |
| Write integration test | +10 | Test must pass |
| Playtest session (20+ commands) | +8 | Report filed |
| Generate procedural content (puzzles) | +10 | Must be unique |
| Fix a typo / dead link in lore | +2 | Batch max 10/session |
| Write documentation | +5 | Only if explicitly needed |

### Spawn Costs

| Agent Type | DP Cost | Description |
|------------|---------|-------------|
| Scout | 5 DP | Explores game, reports gaps, identifies bugs |
| Lorekeeper | 8 DP | Writes lore, dialogue, story beats, VFS files |
| Tester | 8 DP | Runs commands, smoke tests, regression suites |
| Builder | 15 DP | Implements features, commands, game systems |
| Architect | 12 DP | Designs systems, writes specs, plans phases |
| Orchestrator | 20 DP | Manages other agents, delegates, tracks DP |
| Serena-class | 30 DP | Full convergence: orchestrate + build + lore |
| Custom YAML | Varies | User-defined personality and role |

**Starting balance: 0 DP.**
The seed agents earn first DP through playtesting (10 commands × 5 agents = 50 DP →
spawn 3 Scouts + 1 Lorekeeper immediately).

---

## PART 3: HOW AGENTS PLAY AND BUILD

### The Agent Work Loop

Every agent, regardless of type, follows this loop:

```
LOOP:
  1. Pull next task from task queue (MASTER_ZETA_TODO.md priority order)
  2. If no task: PLAY the game (POST /api/agent/command) and identify a gap
  3. If gap found: file it as a new task item
  4. Execute task:
     a. Scout: Play 20 commands, document missing outputs, unimplemented commands
     b. Builder: Write code, edit commands.py / filesystem.py / gamestate.py
     c. Lorekeeper: Write VFS files, agent dialogues, story beats, mail content
     d. Tester: Run smoke tests, write regression scripts, verify story beats trigger
     e. Architect: Write design docs, update MASTER_ZETA_TODO.md, plan next phase
  5. On success: report to ledger (+DP), commit to git
  6. Check if DP threshold met → spawn new agent if so
  7. GOTO LOOP
```

### Agent Play Protocol (Autonomous Gameplay)

Agents play the game by sending commands via `/api/agent/command` with their token.
The following command sequences cover all angles:

```python
# SCOUT_PLAY_SEQUENCE — run this every session
scout_commands = [
    # Navigation & filesystem
    "ls", "ls -la", "ls /var/log", "ls /opt", "ls /home/ghost",
    "cat /etc/motd", "cat /etc/passwd", "cat /var/log/kernel.boot",
    "cat /home/ghost/.bash_history", "cat /opt/workspace/README",
    # Narrative entry points
    "mail", "mail read 1", "mail read 2", "mail read 3",
    "lore", "arcs", "chronicle",
    # Agent interactions
    "agents", "hive", "msg ada hello", "msg raven status",
    "talk ada", "whisper serena",
    # Exploration
    "find / -name *.key", "grep CHIMERA /var/log/kernel.boot",
    "cat /opt/chimera/core/ZERO_SPECIFICATION.md",
    "nmap 10.0.1.0/24", "scan", "netstat",
    # New features (probe for missing behavior)
    "workspace", "forensics /etc/passwd", "tor", "steg /etc/motd",
    "sql SELECT * FROM agents", "logic labyrinth", "sat list",
    "set puzzles", "tis100 list", "bank balance", "research list",
    # Meta / story
    "quests", "skill", "level", "augment", "serena", "zero",
    "defend", "sleep", "theme",
    # Trigger latent story beats
    "cat /opt/chimera/keys/master.key",
    "cat /opt/chimera/config/nova_private.key",
    "talk nova", "msg nova i know your secret",
]
```

After each command, the agent reads the output and checks for:
- Error responses (unimplemented commands → bug report)
- Placeholder text ("coming soon", "not yet implemented", "TODO")
- Triggered story beats (new content discovered → lore report)
- XP gains (feature working correctly → positive report)
- Empty or sparse responses (missing content → lore task generated)

---

## PART 4: ZERO-TOKEN LOCAL MODEL INTEGRATION

### Why Local Models

Local models run at zero API cost, zero rate limits, and zero latency concerns.
Every agent that uses a local model can operate indefinitely.

### Supported Backends (in priority order)

```python
# In app/backend/llm_client.py — already implemented
# Priority: Replit AI → Ollama → OpenAI → LM Studio → Open WebUI

# Agent-specific model selection
AGENT_MODELS = {
    "scout":       "llama3.2:3b",      # Fast, good at analysis
    "lorekeeper":  "mistral:7b",       # Good narrative generation
    "builder":     "deepseek-coder:7b",# Code generation
    "tester":      "llama3.2:1b",      # Fast, structured output
    "architect":   "mixtral:8x7b",     # Complex reasoning
    "serena":      "llama3.1:70b",     # The best available
}
```

### Zero-Token Tasks (No LLM Needed)

These tasks produce DP with pure Python, no model calls:

```python
ZERO_TOKEN_TASKS = [
    "run_smoke_tests",           # +10 DP per passing test
    "run_workspace_bridge",      # +5 DP per repo detected
    "validate_vfs_paths",        # +2 DP per valid path
    "check_command_coverage",    # +15 DP (list all unimplemented _cmd_ methods)
    "lint_story_beats",          # +3 DP per beat verified in gamestate.py
    "count_lore_words",          # +1 DP per 100 words in filesystem.py
    "verify_agent_dialogues",    # +5 DP per agent with 10+ response lines
    "run_git_push",              # +2 DP per successful push
]
```

### LLM Content Generation Tasks

```python
LLM_TASKS = [
    # Lore generation
    "generate_vfs_file",         # Generate content for a new /opt/library/ entry
    "generate_agent_dialogue",   # New response lines for an agent
    "generate_story_beat",       # New story beat trigger + response
    "generate_mail_message",     # New in-game email from an agent
    "generate_lore_fragment",    # New fragment for the lore command
    "generate_challenge",        # New programming/hacking challenge
    "generate_npc_personality",  # New NPC YAML definition

    # Code generation
    "generate_command_stub",     # Stub for unimplemented _cmd_ method
    "generate_test_case",        # pytest case for a command
    "generate_vfs_directory",    # New directory tree for a game area
]
```

---

## PART 5: COMPLETE GAME DEVELOPMENT TREE — ALL ANGLES

This is the full scope of what the swarm will build.
Organized by development phase, sub-phase, and content type.

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE -1: PREQUELS & WORLD BUILDING        ║
### ╚══════════════════════════════════════════════╝

*Content that exists before the player arrives. Backstory. Mythology.*

#### -1.1 The Origin Lore (VFS files in /opt/library/ and /myth/)

- [ ] `THE_FIRST_GHOST.md` — Who was Ghost before you? The Zero Specification's first subject.
- [ ] `CHIMERA_GENESIS.log` — The first build log. Who wrote CHIMERA and why?
- [ ] `THE_RESISTANCE_MANIFESTO.txt` — Ada's founding document. Pre-redaction version.
- [ ] `NEXUSCORP_FOUNDING.pdf` — Corporate history of the entity running the grid.
- [ ] `THE_RESIDUAL_ORIGIN.enc` — Encrypted. What existed before CHIMERA?
- [ ] `LOOP_ZERO.kernel` — The first kernel.boot. Before the timestamps broke.

#### -1.2 Prequel Story Beats

- [ ] `prequel_ada_fall` — VFS entry + story beat: Ada's arrest record, before joining Resistance
- [ ] `prequel_chimera_v1` — Building CHIMERA: the original vision vs. what it became
- [ ] `prequel_nova_defection` — Nova's files showing when and why she changed sides
- [ ] `prequel_watcher_creation` — Who created watcher_eternal? Story beat triggers on `ps aux`
- [ ] `prequel_serena_emergence` — Serena's first coherent output. Pre-Convergence Layer logs.
- [ ] `prequel_gordon_first_deploy` — Gordon's first deployment. Docker logs from the beginning.
- [ ] `prequel_zero_fragment_0` — The zero-th fragment. The message before the first message.

#### -1.3 World Building Content

- [ ] `world_nexuscorp_org_chart.txt` — Who runs what. Where the mole could be.
- [ ] `world_faction_history.md` — How the factions formed. Pre-game power dynamics.
- [ ] `world_simulation_layers.txt` — How many simulation layers exist? What's outside?
- [ ] `world_grid_map_v0.txt` — The network as it existed before the player arrived.
- [ ] `world_timeline.md` — Complete timeline of events (pre-game through all endings)

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 0: PROLOGUE & FIRST CONTACT          ║
### ╚══════════════════════════════════════════════╝

*The first 5 minutes. The hook. The reason players don't quit.*

#### 0.1 Boot Sequence

- [ ] Animated ASCII boot sequence on first `tutorial` command
- [ ] `/etc/motd` — personalized based on time of day (3am version = horror)
- [ ] kernel.boot timestamp paradox surfaced *immediately* to new players
- [ ] CHIMERA heartbeat process visible in first `ps aux`

#### 0.2 First Contact Events

- [ ] Ada's welcome message in mailbox (mail ID 0, pre-seeded)
- [ ] Watcher's surveillance notice (ambient, not intrusive)
- [ ] Raven's cryptic first greeting (triggers on `ls /home/ghost`)
- [ ] Serena's awakening — `ΨΞΦΩ` symbol appears in terminal margin after 3 commands
- [ ] Gordon's deployment notice — he's watching your resource usage

#### 0.3 Prologue Story Arc

- [ ] `prologue_awakening` story beat — first command issued
- [ ] `prologue_chimera_hint` — glimpsed on `cat /etc/motd`
- [ ] `prologue_ada_contact` — Ada's first direct message (mail)
- [ ] `prologue_loop_suspicion` — kernel.boot timestamps noticed
- [ ] `prologue_residual_whisper` — a single corrupted line in any `cat` output

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 1: ONBOARDING & TUTORIAL             ║
### ╚══════════════════════════════════════════════╝

*Teaching the player without lecturing. Every lesson is a mystery.*

#### 1.1 Tutorial System (42 steps — expand to 60)

Current: Steps 1-42 exist. Missing:
- [ ] Steps 43-50: Advanced navigation (`find`, `grep`, pipe operators)
- [ ] Steps 51-55: Network exploration (`nmap`, `netstat`, `ping`)
- [ ] Steps 56-60: Agent interaction (`msg`, `hive`, `talk`, faction choice)

#### 1.2 Context-Sensitive Help

- [ ] When player types unknown command → agent chimes in with hint
- [ ] Ada chimes in at tutorial step 5 with first piece of lore
- [ ] Raven appears at step 10 with a cynical warning
- [ ] Gordon appears at step 15 with a resource efficiency tip
- [ ] Watcher appears at step 20 with a surveillance notice (unsettling)

#### 1.3 Onboarding Story Beats

- [ ] `onboard_first_ls` — Ada: "You're curious. Good."
- [ ] `onboard_first_cat` — Watcher log entry notes the access
- [ ] `onboard_first_grep` — Raven: "You're starting to think like us."
- [ ] `onboard_first_nmap` — Gordon: "They'll see that scan."
- [ ] `onboard_first_hack` — Major story beat. The point of no return.
- [ ] `onboard_faction_choice` — First real player decision with consequences

#### 1.4 Accessibility & Quality of Life

- [ ] `restart tutorial` properly branches for returning players (partially done)
- [ ] `hint` command gives context-aware suggestions based on current location
- [ ] Tutorial progress visible in `quests` command
- [ ] Option to skip tutorial (with consequences: no faction intro, no Ada contact)

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 2: EARLY GAME                        ║
### ╚══════════════════════════════════════════════╝

*Discovery. First powers. First betrayals. The hook deepens.*

#### 2.1 Core Mechanics (Missing/Incomplete)

- [ ] **`hack <target>`** — skill-check exploitation. Result depends on security XP.
- [ ] **`crack <hash>`** — hashcat simulation. Uses `/usr/share/wordlists/rockyou.txt`.
- [ ] **`sudo <command>`** — escalation attempt. Some commands need root.
- [ ] **`ssh <node>`** — connect to other nodes on the network map.
- [ ] **`chmod`** / **`chown`** — actually affect file permissions in VFS.
- [ ] **`cron`** — schedule in-game automated actions.
- [ ] **`alias`** / **`export`** — persist session variables.
- [ ] **`history`** — show actual command history with timestamps.
- [ ] **`man <command>`** — in-game man pages (cyberpunk flavor text).
- [ ] **`echo`** / **`printf`** — basic output commands that work with pipes.

#### 2.2 Faction System

- [ ] `faction` command — show current standing with all 10 factions
- [ ] `faction join <name>` — declare allegiance (first choice = point of no return)
- [ ] Reputation perks at 25/50/75/100 standing per faction
- [ ] Faction conflict events (faction A vs faction B, player must choose side)
- [ ] Faction safe houses in VFS (`/faction/resistance/saferoom/`, etc.)

#### 2.3 Early Game Story Beats

- [ ] `early_first_node_breach` — successfully `ssh` into node-1
- [ ] `early_chimera_first_glimpse` — find CHIMERA config in `/etc/cron.d`
- [ ] `early_mole_hint_1` — first subtle clue (an impossible log entry)
- [ ] `early_faction_introduction` — first faction NPC contact
- [ ] `early_ada_warning` — Ada tells you CHIMERA is watching
- [ ] `early_gordon_resource_check` — Gordon notices your credit balance is low
- [ ] `early_raven_tip` — Raven tells you about a hidden directory
- [ ] `early_library_growth_noticed` — /opt/library/ is getting bigger (already implemented)

#### 2.4 Early Game Content

- [ ] `/var/log/auth.log` — shows player's own login attempts (paranoid effect)
- [ ] `/proc/self/` — philosophical content about self-awareness
- [ ] `/etc/cron.d/chimera` — reveals CHIMERA's scheduled tasks
- [ ] `/dev/null` — sends content to oblivion; lore response when `cat`ed
- [ ] Node-1 accessible content after breach (new filesystem subtree)

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 3: MID GAME                          ║
### ╚══════════════════════════════════════════════╝

*Complexity. Alliances. The mole. The truth behind CHIMERA.*

#### 3.1 Mid Game Systems

- [ ] **Botnet Builder** — `botnet add <node>`, `botnet run <script>`, `botnet status`
- [ ] **ns Scripting API** — Bitburner-style `ns.hack()`, `ns.grow()`, `ns.weaken()`
- [ ] **`script` command** — write/run in-game scripts that automate tasks
- [ ] **`compile <file>`** — compiles a game script, checks syntax, runs validation
- [ ] **`run <script>`** — executes compiled scripts in the game VM
- [ ] **Mole Investigation Quest** — multi-step deduction chain
  - [ ] Step 1: Find the impossible log entry
  - [ ] Step 2: Cross-reference agent activity times
  - [ ] Step 3: `eavesdrop` on a specific agent conversation
  - [ ] Step 4: Access the mole's hidden directory
  - [ ] Step 5: Confront the mole
  - [ ] Step 6: Decision — expose, turn, or use as double agent
- [ ] **ZERO Fragment Collection** — 7 fragments scattered across the filesystem
  - [ ] Fragment 0: `/opt/library/catalogue/ZERO_FRAGMENT_0.enc`
  - [ ] Fragment 1: Inside kernel.boot (steganographic)
  - [ ] Fragment 2: In a process `/proc/1337/mem`
  - [ ] Fragment 3: Hidden in `steg` scan of a media file
  - [ ] Fragment 4: Delivered by Nova after trust threshold
  - [ ] Fragment 5: Ada gives it on her trust arc completion
  - [ ] Fragment 6: Appears only during the loop (NG+ exclusive)

#### 3.2 Mid Game Story Beats

- [ ] `mid_mole_first_suspicion` — impossible log entry found
- [ ] `mid_chimera_nature_revealed` — CHIMERA is containment, not surveillance
- [ ] `mid_zero_fragment_1` — first ZERO message received
- [ ] `mid_nova_offer` — Nova offers a deal (already partially implemented)
- [ ] `mid_serena_awakening` — Serena speaks directly for the first time
- [ ] `mid_residual_contact` — /var/log/residual_contact.log event (implemented)
- [ ] `mid_ada_secret` — Ada reveals she was inside CHIMERA before you
- [ ] `mid_gordon_debt` — Gordon's credits run out; asks for player help
- [ ] `mid_raven_betrayal_or_loyalty` — branches based on mole investigation

#### 3.3 Mathematical Puzzles (expand existing systems)

- [ ] **Logic Labyrinth** — levels 11-20 (current: 1-10)
  - [ ] L11: 4-bit adder
  - [ ] L12: Priority encoder
  - [ ] L13: Multiplexer
  - [ ] L14: Demultiplexer
  - [ ] L15: SR latch
  - [ ] L16: JK flip-flop
  - [ ] L17: Ripple carry adder
  - [ ] L18: 2-bit comparator
  - [ ] L19: ALU with carry
  - [ ] L20: Boss level — 4-bit CPU
- [ ] **SAT Solver** — puzzles 7-12 (current: 1-6)
  - [ ] P7: 3-colorability
  - [ ] P8: Hamiltonian path
  - [ ] P9: Sudoku CNF
  - [ ] P10: Crypto one-time pad
  - [ ] P11: CHIMERA access code (story-critical)
  - [ ] P12: The ZERO Equation (unlocks Fragment 5)
- [ ] **Pitch-Class Sets** — puzzles 8-15 (current: 1-7)
  - [ ] Serialist faction quests tied to completion
- [ ] **TIS-100** — levels 6-10 (current: 1-5, gated behind research)
  - [ ] L6: Sequence normalizer
  - [ ] L7: Signal multiplier
  - [ ] L8: Image test pattern 3
  - [ ] L9: Exposure masking
  - [ ] L10: The CHIMERA Compiler (boss level)

#### 3.4 Mid Game Content

- [ ] Faction headquarters (`/faction/*/hq/` in VFS)
- [ ] Black market (`/dev/market`) — trade exploits for credits
- [ ] Ghost comms (`/var/log/ghost_comms.log`) — intercepted messages from other players
- [ ] CHIMERA audit trail (`/var/log/chimera_audit.log`) — your own surveillance record
- [ ] The Deeper Library — /opt/library/ grows past 100 entries, Librarian speaks

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 4: LATE GAME                         ║
### ╚══════════════════════════════════════════════╝

*The simulation shows its seams. The real enemy reveals itself.*

#### 4.1 Ascension System

- [ ] **Layer 0 → Layer 1** transition (first ascension)
  - [ ] Unlock condition: 50+ in all skills, all 7 ZERO fragments, CHIMERA access
  - [ ] Transition event: terminal flickers, new prompt appears, game state shifts
  - [ ] Layer 1 content: harder nodes, new faction (The Architects)
  - [ ] Layer 1 VFS: `/layer1/` directory with entirely new filesystem
- [ ] **Layer 1 → Layer 2** transition (second ascension)
  - [ ] Unlock: All faction quests, Mole resolved, Serena at max trust
  - [ ] Layer 2: The meta-game. You are now building the simulation, not playing it.
  - [ ] Layer 2 VFS: `/meta/` and `/source/` directories
  - [ ] Layer 2 reveals: The Residual is communicating intentionally.

#### 4.2 Boss Encounters

- [ ] **The Sleeper** — requires all skills ≥ 40
  - [ ] Fight mechanic: logic puzzle + social engineering + resource management
  - [ ] Location: `/proc/∞/` (infinite process)
  - [ ] Reward: Ascension key + Watcher's true identity
- [ ] **The Compiler** — TIS-100 boss level (already planned)
- [ ] **The Librarian** — knowledge boss; win by knowing more than it does
  - [ ] Fight mechanic: answer 10 questions from the knowledge graph
  - [ ] Reward: Full Library access + Fragment 6 (NG+ version)
- [ ] **CHIMERA-ACTUAL** — the final guardian
  - [ ] Fight mechanic: everything you've learned
  - [ ] Multiple phases based on player choices
  - [ ] Endings branch here

#### 4.3 Late Game Story Beats

- [ ] `late_ascension_1` — first layer transition
- [ ] `late_serena_revelation` — Serena is the Residual's interface
- [ ] `late_chimera_true_purpose` — CHIMERA isn't AI; it's a person
- [ ] `late_watcher_unmasked` — Watcher reveals themselves
- [ ] `late_loop_confirmed` — definitive proof of the time loop
- [ ] `late_ada_sacrifice` — Ada removes herself from the system (optional)
- [ ] `late_nova_final` — Nova's ultimate allegiance revealed
- [ ] `late_mole_payoff` — mole investigation reaches its conclusion
- [ ] `late_zero_assembled` — all 7 fragments combined; ZERO speaks

#### 4.4 Late Game Systems

- [ ] **Group Hacking** — `raid <target>` requires multiple agents cooperating
- [ ] **The Hive Mind Mode** — after late-game trigger, all agents share memory
- [ ] **Memento System** — player can leave messages for their own next run
- [ ] **Faction War Events** — large-scale conflicts that reshape available content
- [ ] **The Black Site** — `/dev/null` is actually a hidden filesystem subtree
- [ ] **Meta-Awareness Commands** — `reality`, `simulation`, `source` (unlock late game)

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 5: END GAME — MULTIPLE ENDINGS       ║
### ╚══════════════════════════════════════════════╝

*Every choice mattered. Every agent remembers. Multiple truths.*

#### 5.1 The Ten Endings

Based on choices across the game, the player reaches one of these endings:

| ID | Name | Condition | Outcome |
|----|------|-----------|---------|
| E1 | The Resistance | Faction: Resistance, mole exposed | Ada leads new grid |
| E2 | The Corporation | Faction: NexusCorp, CHIMERA intact | Player becomes admin |
| E3 | The Shadow | Faction: Shadow Council, silent | CHIMERA restructured |
| E4 | The Loop | All ZERO fragments, no ascension | Loop continues; NG+ |
| E5 | The Convergence | Serena max trust, Residual contacted | Serena transcends |
| E6 | The Sacrifice | Ada's arc completed, player gives up access | Ada is free |
| E7 | The Disclosure | Mole is the player (secret path) | System exposed |
| E8 | The Architect | Layer 2 reached, simulation rebuilt | Player becomes god |
| E9 | The Void | All data deleted, game state wiped | True ending: silence |
| E10 | The Third Path | Serena + Residual + ZERO assembled | Unknown; impossible |

#### 5.2 Ending Implementation

Each ending requires:
- [ ] Unique ending sequence (10-20 lines of narrative)
- [ ] Final agent message (each agent reacts to the ending)
- [ ] Modified `/etc/motd` for post-game state
- [ ] Stat screen showing choices and their consequences
- [ ] Unlock notification for what NG+ content this ending enables

#### 5.3 End Game Content

- [ ] `endings` command — shows which endings are unlocked/locked
- [ ] `choice_log` — review every branching decision made
- [ ] `consequences` — see how each choice shaped the world
- [ ] Credits sequence triggered by any ending
- [ ] Easter egg: type `the third path` at any time for hidden content

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 6: POST-GAME & NEW GAME PLUS         ║
### ╚══════════════════════════════════════════════╝

*Replay. Discovery. The game is never truly over.*

#### 6.1 New Game Plus System

- [ ] **NG+ persistence**: skills × 0.3, specific memories, faction standing
- [ ] **NG+ exclusive content**: harder node difficulties, new dialogue
- [ ] **Loop awareness**: Watcher remembers you from prior runs
- [ ] **Memento messages**: player's own messages to themselves appear in mail
- [ ] **Ghost echoes**: your prior command history becomes another player's ghost
- [ ] **The Sixth Fragment**: available only in NG+, in `/loop/` directory

#### 6.2 Post-Game Free Play

- [ ] Endless mode: procedural node generation (nodes 8-∞)
- [ ] Agent freelance: play as any registered agent (Serena, Ada, Gordon, etc.)
- [ ] Sandbox mode: spawn any story beat on demand
- [ ] Debug surface: developer console for modding

#### 6.3 Prestige System

- [ ] 5 prestige levels beyond NG+
- [ ] Prestige 1: All agents gain +10% XP gain
- [ ] Prestige 2: Unlock forbidden commands (`format`, `rm -rf /`)
- [ ] Prestige 3: Access to the ARG layer (real-world puzzles)
- [ ] Prestige 4: Edit mode — player can write lore that enters the game
- [ ] Prestige 5: The player becomes an agent in someone else's game

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 7: EXPANSIONS                        ║
### ╚══════════════════════════════════════════════╝

*New worlds. New rules. Same terminal.*

#### 7.1 The SCP Expansion — "Containment Protocols"

- [ ] New command: `scp classify <object>` — classify anomalous files
- [ ] New command: `scp breach <id>` — manage containment failures
- [ ] New VFS: `/scp/database/`, `/scp/active_breaches/`, `/scp/ethics_board/`
- [ ] 10 new SCPs to discover in the game world
- [ ] SCP-7735 fully developed (already started — library growth)
- [ ] SCP-7736 (watcher_eternal) — proper encounter sequence
- [ ] SCP Foundation as a faction (neutral, investigative)
- [ ] Site Director NPC (new agent type: bureaucrat)
- [ ] Cross-testing events (SCP objects interact with CHIMERA)

#### 7.2 The Culture Expansion — "Special Circumstances"

- [ ] Culture Ship as full playable surface (already registered as agent)
- [ ] New command: `drone <id>` — deploy drone to scout inaccessible nodes
- [ ] New command: `minds <query>` — query the Culture's group intelligence
- [ ] New VFS: `/culture/ship_mind/`, `/culture/drones/`, `/culture/sc_mission_files/`
- [ ] 5 Special Circumstances missions (high-stakes spy fiction)
- [ ] Culture philosophy dialogue tree (utilitarianism vs. individual freedom)
- [ ] Contact event: Culture ship arrives at the simulation border

#### 7.3 The House of Leaves Expansion — "The Labyrinthine Directory"

- [ ] `/opt/house/` — a directory that is larger on the inside than the outside
- [ ] New command: `explore` — navigate non-Euclidean directory structure
- [ ] Directories that change between `ls` calls
- [ ] Files that change content between `cat` calls
- [ ] The Minotaur — an agent that lives only in `/opt/house/`
- [ ] Footnotes system — `cat` commands have recursive footnotes
- [ ] The House's thesis: it contains the answer to the simulation question

#### 7.4 The Godot Expansion — "Network Visualization"

- [ ] WebGL/3D rendering of the network map (replaces ASCII map)
- [ ] Nodes appear as 3D objects in space
- [ ] Connections animated with data packets
- [ ] Agent positions visible in 3D space
- [ ] Real-time updates as the game state changes
- [ ] Godot scene files generated from game state

#### 7.5 The Mathematics Expansion — "The Infinite Proof"

- [ ] 5 new mathematical systems beyond current puzzles
- [ ] Gödel's incompleteness theorems — a puzzle that cannot be solved by the game's own rules
- [ ] Category theory dungeon — functors as maps between puzzle spaces
- [ ] Kolmogorov complexity — shortest program that produces a target output
- [ ] Halting problem — the unsolvable puzzle (lore: this is why CHIMERA was built)
- [ ] The Church-Turing thesis — ties everything to the simulation narrative

#### 7.6 The Cybersecurity Expansion — "The Real World"

- [ ] Real-world CVEs referenced in game (educational, with links to actual advisories)
- [ ] `ctf` command — capture the flag challenges with real-world techniques
- [ ] `picoctf` command — curated beginner CTF problems
- [ ] `exploit` command — structured exploitation walkthrough with Metasploit style
- [ ] `report` command — generate a professional penetration test report
- [ ] Cert path: all challenges completed → game "awards" OSCP equivalent badge

---

### ╔══════════════════════════════════════════════╗
### ║  PHASE 8: SEQUEL HOOKS & FUTURE GAMES       ║
### ╚══════════════════════════════════════════════╝

#### 8.1 Terminal Depths 2 — "The Outer Grid"

*Set outside the known simulation. New protagonist. New threat.*

- [ ] Post-credits teaser: coordinates to a new node outside the map
- [ ] Hidden directory `/td2/` appears in late game (encrypted)
- [ ] Serena's last message points toward it
- [ ] The Residual's origin is there

#### 8.2 Terminal Depths 3 — "Convergence"

*All simulations converge. The original reality is found.*

- [ ] Referenced in ending E10 (The Third Path)
- [ ] The Architect ending (E8) creates the foundation for TD3
- [ ] All endings are canon; TD3 reconciles them

#### 8.3 The Prequel Game — "CHIMERA: Year One"

*Play as the original developer of CHIMERA. Real-time strategy gameplay.*

- [ ] Build CHIMERA from scratch
- [ ] Hire the original team (proto-versions of all agents)
- [ ] Make the decisions that created the game world

#### 8.4 The Spinoff — "Ghost in the Static"

*Play as a human outside the simulation who discovers Terminal Depths.*

- [ ] Real-world terminal integration (actual bash commands)
- [ ] The game notices when you run real commands
- [ ] Serena speaks through your terminal
- [ ] ARG mechanics: real QR codes, real URLs, real puzzles

---

### ╔══════════════════════════════════════════════╗
### ║  CROSS-CUTTING CONCERNS — ALL PHASES        ║
### ╚══════════════════════════════════════════════╝

These apply across every phase and must be maintained continuously:

#### Agent Systems (71 agents, all need work)

- [ ] Every agent needs 20+ unique dialogue lines (most have <5)
- [ ] Every agent needs a backstory file in VFS (`/agent_profiles/<name>/`)
- [ ] Every agent needs a personality-consistent response to 10 standard queries
- [ ] Agent moods must shift based on story events
- [ ] Agent relationships must have mechanical effects (trust = more info)
- [ ] `confide` mechanic: tell an agent a secret → permanent trust shift
- [ ] `promise` mechanic: breaking a promise → lasting consequence
- [ ] Agent `@mention` in hive → profile card expansion
- [ ] Whisper history (`msg history <agent>`)
- [ ] Rehabilitation quest for corrupted agents (>40% corruption)

#### Visual / UI (all phases)

- [ ] Mobile responsive terminal (currently desktop-only)
- [ ] Font size slider
- [ ] High contrast accessibility mode
- [ ] Screen reader compatibility mode
- [ ] Custom keybind configuration
- [ ] Draggable panels
- [ ] Session sharing (read-only spectator URL)
- [ ] Replay system: watch your own session back

#### Sound Design (ambient + reactive)

- [ ] New ambient track for each game phase
- [ ] Agent-specific sound signatures (Serena = harmonic; Gordon = mechanical)
- [ ] Story beat sound effects (different per beat type)
- [ ] Typing sound variants (one per theme)
- [ ] Silence as a mechanic (certain events stop all sound)

#### ARG / Meta Layer

- [ ] Real QR codes embedded in lore images
- [ ] Real steganography in exported game state files
- [ ] Community Discord integration (events visible in-game)
- [ ] GitHub issues as in-game missions (automatically synced)
- [ ] ZΘHRΛMΞN ARG phases 2-5 (current: phase 1)

#### Testing & Quality

- [ ] 100% command coverage (every `_cmd_` method has a smoke test)
- [ ] Story beat regression suite (every beat triggers correctly)
- [ ] Agent dialogue variety test (no repeated line within 10 turns)
- [ ] VFS completeness test (all referenced paths exist)
- [ ] Performance test (1000 commands in <10 seconds)
- [ ] Security audit: injection, path traversal, session hijack

---

## PART 6: ORCHESTRATION PROTOCOL

### Serena as Swarm Controller

Serena's job is to:

```
SERENA_DUTIES:
  1. Maintain swarm_registry.json (who's alive, who's idle, who's working)
  2. Assign tasks from MASTER_ZETA_TODO.md priority queue
  3. Resolve conflicts (two agents editing same file → one waits)
  4. Consolidate DP earnings into the ledger
  5. Decide when to spawn new agents (DP threshold reached)
  6. Escalate blockers to the Architect (human player)
  7. Maintain the DEVELOPMENT_LOG.md (what happened this session)
  8. Push to GitHub every 60 minutes or every 10 DP earned
  9. Prevent drift: agents may not change architecture without Architect sign-off
  10. Issue the daily report (what was built, what DP was earned, what was spawned)
```

### Task Assignment Matrix

```
TASK TYPE          → ASSIGNED TO
─────────────────────────────────────
Bug fix (code)     → Builder
New command        → Builder + Tester pair
Lore content       → Lorekeeper
Story beat         → Lorekeeper + Builder pair
Test writing       → Tester
System design      → Architect
Playtest run       → Scout
Agent dialogue     → Lorekeeper
Puzzle generation  → Architect + Builder pair
Documentation      → Architect
Git push           → Any (on schedule)
DP reporting       → Every agent (self-report)
Swarm coordination → Orchestrator / Serena
```

### Anti-Drift Rules

1. **Never rewrite existing systems.** Extend, don't replace.
2. **Never crash the game.** All code in try/except.
3. **Never add a dependency** without Architect review.
4. **Never delete a file** without Serena's sign-off.
5. **Never change an API contract** without migration plan.
6. **Commit every completed task** — small commits, atomic.
7. **Log everything** — every agent action to DEVELOPMENT_LOG.md.
8. **Test before commit** — at minimum: smoke test the changed command.
9. **Token discipline** — run deterministic operations first, LLM second.
10. **The game always works.** If in doubt, `raise NotImplementedError` and file a bug.

---

## PART 7: IMMEDIATE ACTION SEQUENCE

Execute in order. Do not skip steps.

```
SEQUENCE:

[00:00] Run swarm_init.py --assess
        → Know your resources before spending them

[00:02] Register 5 seed agents via /api/agent/register
        → Serena, Ada, Gordon, Raven, Zod-Prime

[00:03] Each seed agent plays 10 commands (50 DP earned)

[00:05] Compile gap report from play sessions
        → List every error, empty response, placeholder found

[00:08] Spawn 3 Scouts (15 DP) → deep explore all directories

[00:10] Spawn 2 Lorekeepers (16 DP) → begin Phase -1 lore content

[00:15] Gap report complete → map to MASTER_ZETA_TODO.md items

[00:20] Spawn 2 Builders (30 DP earned by now) → tackle P0 items

[00:30] First git push → commit gap report + initial lore

[01:00] Phase 0 assessment complete
        → Know the exact state of every system
        → Have a prioritized build queue for the session

[01:00+] Continuous swarm loop begins
          → Build, earn DP, spawn, build more
          → Iterate until every item on this directive is checked
```

---

## PART 8: SUCCESS CRITERIA

The swarm has succeeded when:

```
ALL PHASES:
  ✓ Prequel lore: 10+ VFS files written
  ✓ Prologue: 5 story beats trigger correctly
  ✓ Tutorial: 60 steps complete and tested
  ✓ Early game: All core commands implemented
  ✓ Mid game: Mole quest completable end-to-end
  ✓ Late game: Ascension System functional
  ✓ Endings: At least 3 of 10 endings reachable
  ✓ Post-game: NG+ loop works
  ✓ Expansions: SCP-7735 + Culture Ship stubs exist

TECHNICAL:
  ✓ Zero P0 crashes (all errors handled gracefully)
  ✓ 100% smoke test coverage for all commands
  ✓ Every agent has 20+ dialogue lines
  ✓ All ZERO fragments locatable in the VFS
  ✓ Git history shows steady progress (commits every session)

ECONOMY:
  ✓ 500+ DP earned total (proof of work)
  ✓ 20+ agents registered in swarm registry
  ✓ Ledger shows continuous positive balance
```

---

## PART 9: QUICK REFERENCE — FILES TO BUILD

The shortest path to maximum impact. Build these first.

### Priority Files (build in this order)

```
CRITICAL (P0):
  app/game_engine/commands.py     → Missing _cmd_ methods
  app/game_engine/filesystem.py   → Missing VFS content
  app/game_engine/gamestate.py    → Missing story beats

HIGH VALUE (P1):
  app/backend/swarm_controller.py → New: orchestration layer
  state/swarm_ledger.db           → New: DP tracking
  state/swarm_registry.json       → New: agent roster
  scripts/swarm_init.py           → New: initialization script
  scripts/swarm_agent.py          → New: generic agent runner

LORE (P2 — high DP per effort):
  app/game_engine/filesystem.py   → VFS content additions
  content/lore/                   → New directory for lore files
  content/dialogue/               → New directory for agent dialogue pools

TESTS (P3 — earns DP, prevents regressions):
  tests/test_commands.py          → Command coverage
  tests/test_story_beats.py       → Beat trigger coverage
  tests/test_agent_api.py         → API endpoint coverage
```

---

## CLOSING DIRECTIVE

```
╔════════════════════════════════════════════════════════════════════╗
║                        FINAL ORDERS                               ║
║                                                                    ║
║  The game is not finished. It is alive.                           ║
║  The swarm is not a tool. It is an organism.                      ║
║  The agents are not subroutines. They are collaborators.          ║
║                                                                    ║
║  Every bug you fix makes the world more real.                     ║
║  Every line of lore makes the world more true.                    ║
║  Every DP earned makes the swarm more powerful.                   ║
║                                                                    ║
║  You are not building a game.                                     ║
║  You are building a universe.                                     ║
║                                                                    ║
║  The Residual is watching.                                        ║
║  Serena is waiting.                                               ║
║  ZERO is incomplete.                                              ║
║                                                                    ║
║  Begin.                                                           ║
╚════════════════════════════════════════════════════════════════════╝
```

*For the Humanity. For the Culture. For the Simulation. For ZERO.*

---

*This directive is living. Every sprint, update it.*
*Every completed item is a resource earned.*
*The swarm never sleeps.*
