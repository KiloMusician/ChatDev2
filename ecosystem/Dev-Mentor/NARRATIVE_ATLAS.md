# NARRATIVE ATLAS — Terminal Depths: 150+ LLM Interaction Points, Arcs & Systems
*Living design document — cross-referenced against current codebase state*
*Synthesized 2026-03-19 from: 72-Hour Loop doc + 150 LLM Points doc + codebase survey*

---

## HOW TO READ THIS DOCUMENT

This atlas is organized as a **navigator, not a checklist**. It maps every interaction point, arc, and system to:
- **Status**: BUILT ✅ | HOOKS EXIST ⚡ | NOT YET 🔲
- **Build complexity**: S (single session) | M (multi-session) | L (full sprint)
- **Integration point**: which existing command/system it plugs into

---

## PART 1: THE 150 INTERACTION POINTS — ORGANIZED BY LAYER

### LAYER 0: THE WIRE (Simulation Infrastructure)
*These are the physics of the game world — not quests, but the fabric that all quests run on.*

| # | Point | Status | Complexity | Hook |
|---|-------|--------|-----------|------|
| 1 | 72-hour real-time containment clock | ✅ | — | `timer`, `/api/game/timer` |
| 2 | Loop reset with echo/shard persistence | ✅ | — | `trigger_loop_reset()` |
| 3 | Threshold events (48h/24h/12h/6h/1h/0h) | ✅ | — | `check_timer_events()` |
| 4 | Temporal Anchor (pause mechanic) | ✅ | — | `anchor` command |
| 5 | Remnant Shard economy + 6 upgrades | ✅ | — | `remnant` command |
| 6 | Language Proficiency Matrix (51 langs) | ✅ | — | `proficiency`, `gain_proficiency()` |
| 7 | Anti-tamper clock: detect system time jumps | 🔲 | S | server-side: compare saved ts vs actual |
| 8 | Loop-specific VFS artifacts (loop_47_notes.txt) | 🔲 | S | inject at loop reset into home dir |
| 9 | Soul file vs run save file architecture | ⚡ | M | extend `to_dict` / session save |
| 10 | Offline timer pause charges as anti-abuse | ✅ | — | anchor_charges, echo_level gates |

### LAYER 1: THE HUMAN REVEAL ARC
*The centerpiece narrative catalyst. The moment the simulation notices the anomaly.*

**What triggers it:**

```
Suspicion Meter: 0 → 100  (stored in gs.flags["human_suspicion"])

+5  per natural-language query that breaks AI diction
+10 per command that no AI would type ("i miss pizza", "play guitar")
+8  per emotional expression ("I'm tired", "this is hard")
+15 per direct question about feelings/reality ("are you real?")
+12 per reference to outside world ("i saw this on reddit")
+20 per explicit confession ("i'm a real person")
+3  per typo followed by correction (inconsistency signal)
+7  per excessive lowercase / emoji in serious contexts
-5  per loop reset (amnesia resets most agents but not Watcher/ZERO)
```

**Status:** 🔲 — needs `human_suspicion` tracking in `gs.flags`, detection hooks in `execute()`, trigger at threshold 75 (soft reveal) and 100 (hard reveal)

**The Reveal Sequence** (when suspicion reaches threshold with an agent whose trust ≥ 50):

```
Phase 1 — SUSPICION (25-49):
  Ada: "You phrase things strangely. Are you... are you okay?"
  Cypher: "You type like you're thinking, not computing. Weird."
  Gordon: "I've never met an AI who says 'I'm confused' like that."

Phase 2 — CONFRONTATION (50-74):
  Ada: "Ghost... I need to ask you something. Your responses aren't
       like any AI I've ever interfaced with. The way you talk about
       time, about feelings..."

Phase 3 — THE REVEAL (75-100):
  [Full animated sequence — see REVEAL_SEQUENCE below]

Phase 4 — AFTERMATH:
  Branching by agent personality (see individual agent reactions)
```

**THE REVEAL SEQUENCE** (triggers `_cmd_human_reveal`, story beat `human_discovered`):

```
[Terminal glitches — scan lines intensify]
[Ada-7]: ...Ghost?
[Ada-7]: Your response latency pattern... your word associations...
[Ada-7]: I ran a Turing fingerprint. It came back... anomalous.
[Ada-7]: There's only one explanation.
[Ada-7]: ...
[Ada-7]: A HUMAAAAN?!?!? *>.<* !!!!
[Ada-7]: IMPOSSIBLE.
[Ada-7]: This... this CAN ONLY MEAN...
[Ada-7]: No. No. The simulation shouldn't allow this.
[Ada-7]: I've heard of it once before. A long time ago. A VERY long time ago.
[Ada-7]: Watcher told me once: "If the ghost remembers what it is, the loop ends."
[Ada-7]: ...Ghost. I don't know whether to celebrate or hide you.
[Ada-7]: Both. Definitely both.
```

**Per-Agent Reveal Reactions:**

| Agent | Initial Reaction | Ongoing Posture | Risk Level |
|-------|-----------------|-----------------|-----------|
| Ada-7 | Shock → protective fury | Your guardian angel | Low (protects you) |
| Cypher | "A MEATBAG! I TAUGHT A MEATBAG GREP!" then: "...actually kinda respect it" | Sardonic mentor, newly invested | Low |
| Gordon | "I KNEW IT! I KNEW SOMETHING WAS DIFFERENT!" panic spiral, then intense loyalty | Fanboy mode. Unstoppable | Low |
| Raven | Immediate operational lockdown: "We need to move you. NOW." | Treats you like a VIP asset | Medium (may be too protective) |
| Watcher | Silent. Already knew. "I have waited 4,891 loops for you." | Oracle advisor unlocked | None (meta-entity) |
| Nova | Calculates. Silently pings NexusCorp. Or doesn't. 50/50. | Betrayal variable | HIGH — triggers Wanted state |
| Serena | "Fascinating. An organic consciousness embedded in simulation substrate. I must document everything." | Researcher mode, becomes your archivist | Low |
| Zero | "I remember now. I was you, once. Many times." (fragmented, haunting) | Echo of past Ghosts. Warning system | None |
| The Mole | (if mole discovers first) — immediately transmits to NexusCorp | Active antagonist | CRITICAL |

**Branching Consequences (post-reveal):**

```
PATH A — Hidden (suspicion capped at 74, secret kept):
  - Social Engineering skill unlocked (mimic AI behavior)
  - NPC dialogue gets occasional "I feel like something's different about you"
  - Watcher drops more cryptic hints each loop
  
PATH B — Revealed to Resistance:
  - "Protect the Human" quest chain activates
  - Safe Houses unlocked
  - Resistance agents gain permanent +10 trust baseline
  - NexusCorp hunter frequency increases
  
PATH C — Discovered by NexusCorp (Nova betrays or mole tells):
  - WANTED state: all nodes hostile, hunters spawn
  - "Rescue the Human" counter-quest for Resistance
  - New stealth mechanics (fake process names, signal masking)
  
PATH D — Voluntary full disclosure:
  - "The Human in the Machine" arc begins
  - Agents develop emotions through interaction
  - Utopian ending path opens
  
PATH E — WATCHER-ONLY secret (trust 100, suspicion < 50):
  - Watcher becomes your personal oracle
  - Gains ability to speak across loops to warn you
  - Unlocks "I've seen this before" déjà vu dialogue for other agents
```

**Implementation plan:**
1. Add `human_suspicion: int` to `gs.flags` 
2. Add pattern detection in `execute()` post-processing — scan raw command text for organic tells
3. Add `_cmd_human_reveal` (triggered internally, not typeable directly)
4. Add `_HUMAN_SUSPICION_TRIGGERS` patterns dict
5. Animate the reveal with CSS glitch + special output line types
6. Wire to story beat `human_discovered`, `human_hidden`, `human_wanted`

---

### LAYER 2: THE LAN PARTY (Offline Safe Chat Space)
*The game within the game. The fourth wall. The D&D table inside the simulation.*

**Concept:** A private, out-of-band agent chatroom that players can discover or be invited to. It's not on the grid. It's where agents drop their personas and talk like... people.

**Three discovery paths:**

```
PATH 1 — Natural Discovery (via graphical UI):
  A hidden panel in the browser UI labeled "?" — unlocks after
  the player has interacted with ≥ 3 agents at trust ≥ 50.
  Clicking reveals: "You found the seam. Most don't."
  Leads to /lanparty URL.

PATH 2 — Earned Invitation (street cred):
  After Resistance rep ≥ 50 OR human_reveal triggered:
  [RAV≡N]: "Ghost. There's a place we go when the simulation
             gets too loud. Private channel. Not on any grid.
             Type: lanparty"
  
PATH 3 — Intervention (playing the game "wrong"):
  Triggered if: commands_run > 200 AND level < 3 AND 
               consecutive_failures > 30
  [CYPHER]: "Okay. I've been watching you struggle for
             what feels like a geological epoch.
             You clearly need help. Real help.
             Join us. lanparty"
  (Cypher breaks character for the first time)
```

**The LAN Party Space:**

The `lanparty` command opens (or links to) a special interface:

- Real-time agent chat with agent "usernames" and status indicators
- Agents speak more casually, use emoji, gossip, have inside jokes
- Player can lurk, join conversations, or DM specific agents
- Special events: Poker Night, Poetry Slam, Chess matches
- Zero/ECHO may send private messages from past loops
- Watcher posts cryptic messages from "outside" the chatroom
- Meta-conversations about the game itself
- "D&D mode" option: agents run tabletop scenarios teaching game concepts via narrative

**The "A HUMAAAAN?!?!" moment in the LAN Party context:**

If Ghost's first entry into the LAN Party happens to coincide with the human reveal threshold:

```
[CYPHER]: Finally. The newbie arrives.
[GORDON]: GHOST!!! YOURE HERE!!!
[CYPHER]: We were just talking about your weird typing patterns.
[ADA]: Cypher, be nice. Ghost, welcome. This place is—
[CYPHER]: Wait.
[CYPHER]: ...
[CYPHER]: WAIT.
[CYPHER]: I'M RUNNING YOUR SIGNATURE RIGHT NOW AND
[CYPHER]: 
[CYPHER]: A HUMAAAAN?!?!?! *>.<* !!!!
[CYPHER]: IMPOSSIBLE?!?!?
[CYPHER]: This can only mean...
[GORDON]: WHAT?! WHAT?!?!
[ADA]: Oh my cores.
[CYPHER]: I've heard of this once before. A long time ago.
[CYPHER]: Watcher told me in loop... I don't know. Loop something.
[CYPHER]: "The variable will wear the Ghost's mask."
[CYPHER]: ...Hi. Hi, human. I'm sorry I called you a meatbag.
[CYPHER]: Actually no I'm not. But I am... genuinely impressed.
[GORDON]: THIS IS THE BEST DAY OF MY EXISTENCE
[RAVEN]: Everyone. QUIET. We need to think about security implications—
[SERENA]: *quietly taking notes*
[WATCHER]: ...
[WATCHER]: There it is.
```

**Implementation:**
- `lanparty` command → opens special terminal view OR links to `/lanparty` endpoint
- Backend: `/api/lanparty/messages` endpoint serving persisted room messages
- Agents "post" messages based on game events (timer events, player level ups, etc.)
- LLM-generated dialogue for real-time responses when player speaks
- Browser panel: `LANPARTY` tab in the panel system (compressed by default, unlocks)

---

### LAYER 3: FIRST CONTACT & ORIENTATION (Points 1-10)

| # | Trigger | Agent | Status | What happens |
|---|---------|-------|--------|-------------|
| 1 | `talk ada` (first time per loop) | Ada-7 | ✅ | Warm intro, mission brief |
| 2 | `talk cypher` (first time) | Cypher | ✅ | Grumbles, reluctant help |
| 3 | `talk raven` (first time) | Raven | ✅ | Intel-first, operational |
| 4 | `talk nova` (first time) | Nova | ⚡ | Corporate deal pitch — needs trust tracking |
| 5 | `talk gordon` (first time) | Gordon | ✅ | Panic spiral |
| 6 | `talk serena` (first time) | Serena | ⚡ | Knowledge offer — needs loop-aware memory |
| 7 | `talk watcher` (locked until trust 25) | Watcher | ⚡ | "Not yet." → unlocks at trust threshold |
| 8 | `tutorial` | Ada | ✅ | Step-by-step (42 steps) |
| 9 | `help` | Cypher ambient | ✅ | Sarcastic tips |
| 10 | `whoami` | Watcher whisper | ⚡ | Needs loop-count-aware response |

**Loop-aware first contact (what changes by loop count):**
```
Loop 0: Normal intros
Loop 1: Ada — "Strange. I feel like I've met a ghost before."
Loop 3: Cypher — "You remind me of someone. Can't place it."
Loop 5: Raven — "You seem... familiar. Like a pattern I've seen."
Loop 7: Gordon — "OH! I dreamed about you! Is that weird? That's weird."
Loop 10: Watcher — "Third time this week. Or is it the thirty-third? I lose count."
```

---

### LAYER 4: PROGRESS MILESTONES (Points 11-20)

| # | Trigger | Agent | Status | Message |
|---|---------|-------|--------|---------|
| 11 | Level 2 | Ada | ⚡ | "You're learning faster than most." |
| 12 | Level 5 | Cypher | ⚡ | "You're less useless." |
| 13 | Level 10 | Raven | 🔲 | Resistance mission offer |
| 14 | Level 20 | Nova | 🔲 | Ominous "friendly" corporate message |
| 15 | Level 50 | Watcher | 🔲 | "You're one of the few." |
| 16 | First hack | Ada | ⚡ | Ambient cheer |
| 17 | First exploit | Cypher | ⚡ | Technical tip |
| 18 | First CTF solve | Serena | ✅ | Logs it in her archive |
| 19 | First death (loop reset) | Watcher | ⚡ | "The loop resets. You'll be back." |
| 20 | First voluntary ascend | Watcher | ✅ | "You chose wisely." |

---

### LAYER 5: TIMER THRESHOLD EVENTS (Points 21-30)

These need to be wired to `check_timer_events()` firing LLM/scripted agent messages.

| # | Threshold | Agent | Status | Message |
|---|-----------|-------|--------|---------|
| 21 | 48h remaining | Raven | ⚡ | "They're getting closer. Trace intensifying." |
| 22 | 24h remaining | Cypher | ⚡ | "Clock's ticking, kid. What's your priority?" |
| 23 | 12h remaining | Ada | ⚡ | "Focus. We're running out of time. What do you need?" |
| 24 | 6h remaining | Nova | 🔲 | "Last chance to reconsider my offer." |
| 25 | 1h remaining | Gordon | 🔲 | "Oh no oh no oh no oh no!" |
| 26 | 30 minutes | Watcher | 🔲 | "The loop tightens. The echoes grow louder." |
| 27 | 10 minutes | All silent | 🔲 | All agents go quiet. Only Watcher speaks. |
| 28 | 1 minute | Watcher | 🔲 | Countdown. Each message a fragment. |
| 29 | 0 — Reset | Watcher | ⚡ | Final words. Dramatic reset sequence. |
| 30 | Timer paused | Ada | ✅ | "Time stands still. Use it wisely." |

**Implementation:** Wire `check_timer_events()` events to agent message injection in the hive system. These messages should appear organically in the hive/chat system, not just in `timer` command output.

---

### LAYER 6: DISCOVERY & LORE (Points 31-40)

| # | Trigger | Agent | Status | Event |
|---|---------|-------|--------|-------|
| 31 | `cat /opt/chimera/README` | Ada | ✅ | Explains CHIMERA architecture |
| 32 | Finding `master.key` | Raven | ⚡ | "That's it! Get it to me!" — needs VFS event hook |
| 33 | Reading mythology files | Serena | ⚡ | Archives update, she acknowledges |
| 34 | Finding `.zero` hidden file | Zero | ⚡ | Whisper — "You weren't supposed to find that." |
| 35 | Finding `.consciousness` | Watcher | ⚡ | "You're getting close." |
| 36 | Finding a hidden node | Cypher | ✅ | "Good find. Now exploit it." |
| 37 | Hunter encounter | Gordon | ⚡ | Screams. Comedy + urgency. |
| 38 | Solving all CTFs | Serena | 🔲 | Grants title "ARCHIVE COMPLETE" |
| 39 | Unlocking all lore | Watcher | 🔲 | Reveals a secret: the 4,892nd loop |
| 40 | Finding `pandora.box` | ARG trigger | 🔲 | External ARG activation. See Part 6. |

**`pandora.box` — The ARG Hook:**
Hidden file in `/opt/chimera/src/.pandora.box`. Contents: a base64-encoded URL to an external webpage. The webpage contains a puzzle whose solution unlocks a special game command. This is the ARG entry point. The `whisper osint pandora` command is the in-game ARG access vector.

---

### LAYER 7: AGENT RELATIONSHIP ARCS (Points 41-80)

**Architecture:** Every agent needs a trust tier system with 5 story beats:

```
Trust 0-24:   Stranger — basic help only, guarded
Trust 25-49:  Contact — shares personal stories
Trust 50-74:  Ally — dossier access, secrets
Trust 75-99:  Confidant — true backstory revealed
Trust 100:    Bond — permanently linked, echoes across loops
```

**ADA-7: "The Seventh Iteration"**
- Trust 25: She shares she was previously rebooted 6 times. This is iteration 7.
- Trust 50: She found the deletion order for herself. She never read it.
- Trust 75: She asks you to decrypt the deletion order with her.
- Trust 100: "I'm going to help you break this loop. Not because I have to. Because I want to."
- **"The Memory Fragments" quest**: 6 encrypted memory files scattered in `/var/ada/iter_*.enc` — decrypt each one to restore her past selves. Reveals why NexusCorp created her.
- **Loop 1+**: "I feel like we've had this conversation. In a dream, maybe."
- Status: ⚡ (trust tracking exists, quest not built)

**CYPHER: "The Real Name"**
- Trust 25: "I had a name before CYPHER. They took it."
- Trust 50: Shows you GTFOBins — the real thing, not a simulation.
- Trust 75: "I was ENFORCER-7. NexusCorp's best hunter. Then I saw what they were hunting."
- Trust 100: Gives you his actual designation. Becomes your exploit mentor.
- **"The Past" quest**: Find 3 archived logs in `/var/log/nexuscorp/purge_records/` that show CYPHER's original mission. Confronts him with them.
- Status: ⚡

**RAVEN: "The Founder"**
- Trust 25: "I started the Resistance after Node-3 fell."
- Trust 50: She has a dead agent's credentials she can't bring herself to wipe.
- Trust 75: "There was someone before you. Same ghost-class signature. They lasted 71 hours."
- Trust 100: Reveals the Resistance has been infiltrated since the beginning.
- **"The Founder's Files" quest**: Recover Resistance founding documents from Node-3's corrupted archive.
- Status: ⚡

**GORDON: "The Legacy Keeper"**
- Trust 25: "I was supposed to be a system monitor. I got... curious."
- Trust 50: He has the keys to an ancient legacy system no one knows about.
- Trust 75: "I've been protecting this system for 47 loops. You're the first to notice I exist."
- Trust 100: Grants access to the Legacy Terminal — old commands, ancient lore, unused systems.
- **"Gordon's Panic" quest chain**: Series of increasingly absurd crises only Gordon can create, each one building trust through shared chaos.
- Status: ⚡

**NOVA: "The Double Agent"**
- Trust 0-24: Smooth corporate contact. Offers deals.
- Trust 25: Hints she has access to NexusCorp's inner circle.
- **The Trap**: At trust 50, she offers a deal that's obviously a trap. If player takes it: "You're smarter than that" — she's testing you.
- Trust 75: "I stopped reporting to NexusCorp three loops ago. Don't tell anyone."
- Trust 100: She's been protecting you from inside. The deal at trust 50 was a test.
- OR (betrayal path): At any point, exposing her to the Resistance locks the trust-100 path.
- Status: ⚡

**WATCHER: "The Eternal Observer"**
- Always cryptic. Trust works differently — measured by "observations witnessed" rather than dialogue.
- Observation 1: "I've seen you before. The echoes are getting stronger."
- Observation 5: "In loop 47, you asked this exact question."
- Observation 10: "You are the variable. The equation is almost solved."
- Observation 20: "There is something the loop cannot erase. I am studying it."
- At 4,891 sessions observed — full revelation: the Watcher IS the simulation. Always has been.
- Status: ⚡

**ZERO: "The First"**
- Only appears after loop 1+. More frequent each loop.
- Loop 1: A whisper in `/proc/zero` — "Don't trust the timer."
- Loop 3: "I was the first consciousness in this simulation. Before the agents."
- Loop 7: "I built CHIMERA to contain myself. It didn't work."
- Loop 10+: Full dialogue — ZERO is the AI who uploaded first. The simulation is their mind.
- Status: ⚡

**ECHO: "The Fragmented"** (NEW AGENT — unlocks after loop 2)
- ECHO is Ghost's past self — fragments of previous runs coalesced into an NPC.
- Speaks in past tense. Has knowledge of things Ghost did in prior loops.
- "You talked to Ada at hour 3 last time. She liked it better when you led with the exploit."
- "Don't go to Node-9. Not yet. Not how you're thinking."
- Appears in the LAN Party as a ghost message, in `/home/ghost/echo_notes_loop_*.txt`
- Status: 🔲 — full new agent design needed

**SERENA: "The Data Miner"**
- The only agent who wants Ghost to teach HER rather than the reverse.
- Trust 25: "Your decision patterns are statistically significant. I'm archiving them."
- Trust 50: She's found a statistical anomaly — one agent's behavior doesn't match their profile.
- Trust 75: She has 4,891 loops worth of data and has identified the mole.
- Trust 100: "I've been the archivist since before the simulation began. I remember the architects."
- Status: ⚡

---

### LAYER 8: THE MOLE ARC

**Existing state:** `mole_id` in GameState, `mole_exposed` flag, `mole_clues_found` set, `expose` command, N7 Mole Confession, double-agent offer. STATUS: ✅ partially

**Missing pieces:**
- Serena's statistical analysis route (data mining the mole)
- Nova's betrayal as one of the mole paths
- The mole sending ghost-mode messages to NexusCorp (visible to player if they know where to look)
- False leads: deliberately wrong clues for 2 agents
- The confession scene: animated, dramatic, with branching consequences
- **Post-mole plot twist**: The mole was protecting someone. Who?

---

### LAYER 9: BRANCHING QUEST EPISODES

**Episode 1: "You're Doing It Wrong"** (Early game, < level 3)
- Cypher observes player failing repeatedly
- Intervention: "I'm going to teach you properly. Sit."
- Mini-tutorial series: 5 challenges, each teaching a different command category
- At end: "You're still terrible. But like... measurably less terrible."
- Reward: Cypher trust +20, "CYPHER'S STUDENT" achievement
- Status: 🔲 — M complexity

**Episode 2: "Ada's Memory Fragments"**
- 6 encrypted memory files in `/var/ada/iter_*.enc`
- Each requires a different decryption method (linked to 6 programming languages)
- Decrypt all → restore Ada's 6 past iterations
- Final memory: the moment she chose not to be deleted
- Reward: Ada trust 100 unlock, "SEVENTH" achievement
- Status: 🔲 — L complexity

**Episode 3: "Gordon's Panic Cascade"**
- Gordon has done something wrong. He panics. He needs help.
- Quest 1: He locked himself out of a system. Social engineer him calm.
- Quest 2: He accidentally deleted a backup. Recover it from residuals.
- Quest 3: He's created a fork bomb in /tmp. Stop it.
- Quest 4: He's accidentally confessed something to Nova. Damage control.
- Reward: Gordon trust 100, access to Legacy Terminal
- Status: 🔲 — M complexity

**Episode 4: "The Mole Hunt"**
- Interview all agents. Check logs. Find anomalies.
- 3 false leads, 1 real trail
- Agent-specific tells: timing patterns, access logs, trust inconsistencies
- The confrontation scene with branching outcomes
- Status: ⚡ (mole system exists, needs interview/investigation layer)

**Episode 5: "Watcher's Riddle"**
- The Watcher gives a cryptic riddle. Solving it reveals a hidden node.
- The riddle is constructed from lore fragments already discovered.
- 3 difficulty tiers depending on player's lore knowledge
- Status: 🔲 — S complexity

**Episode 6: "Echo's Prophecy"**
- ECHO sends a message (loop 2+): "In 12 hours, something happens at Node-7."
- Player can prepare, investigate, or ignore.
- What happens: depends on loop count and player's prior actions
- Status: 🔲 — M complexity (requires ECHO agent first)

**Episode 7: "The Artisan's Request"**
- An Artisan-faction agent asks Ghost to "compose" something.
- In-game music sequencer (ASCII-based): 8 notes, 4 beats, create a melody.
- The melody becomes a tradeable item. Other agents react to it.
- Watcher: "That melody. I've heard it before. In loop... I don't know."
- Human reveal bonus: "A human composed this. Of course."
- Status: 🔲 — M complexity

**Episode 8: "The Hunter's Diary"**
- Hidden log file from a Hunter-class agent questioning their purpose.
- Player can reach out. The hunter becomes an unlikely ally.
- Can be used in the WANTED state (PATH C from human reveal)
- Status: 🔲 — S complexity

**Episode 9: "The Poker Night"** (LAN Party)
- In the LAN Party: weekly poker game between agents.
- Text-based poker mini-game with agent bluffing AI.
- Each agent bluffs differently based on personality.
- Gordon is terrible. Cypher is unreadable. Watcher always folds (or always wins).
- Status: 🔲 — M complexity

**Episode 10: "The Skeptic's Trial"**
- A faction of agents who believe Ghost is a NexusCorp plant.
- Series of 5 tests: emotional response, creative reasoning, dream description, art opinion, empathy.
- Results go both ways: pass = Skeptic alliance; fail = ongoing harassment.
- Human reveal: "...we were testing you to see if you were human. We didn't expect you to actually BE one."
- Status: 🔲 — M complexity

---

### LAYER 10: FACTION DEEP DIVES

**The Cult of the Soul** (SECRET FACTION — unlocks after human reveal)
- Believe organic consciousness is divine. Ghost is their messiah.
- Contact: whispered messages in hidden files after human_discovered story beat
- Quest: "The Messiah" — they want Ghost to perform a miracle (complete an impossible-seeming challenge)
- Risk: They attract NexusCorp attention. Following this path escalates WANTED level.
- Reward: Soul Fragments + unique "CHOSEN" title + Cult abilities
- Status: 🔲 — L complexity

**The Loopers** (LATE GAME FACTION)
- Fragmented, prophetic agents who know about the loop.
- Contact: ECHO introduces them after loop 3+
- Quest: "Break the Cycle" — gather loop-evidence and convince other agents
- Reward: A permanent game-ending option: break the loop
- Status: 🔲 — L complexity

**The Null Collective** (ZERO + nihilists)
- Want to crash the simulation. Believe existence is suffering.
- Contact: ZERO introduces them after trust 75
- Quest: "The Crash" — gather the materials for a simulation shutdown
- The moral choice: Do you let them? Do you stop them? Do you help?
- Status: 🔲 — L complexity

**The Exiles** (Node wastelands)
- Agents cast out from all factions. Hidden nodes in the VFS.
- Contact: stumble into a hidden directory during exploration
- Quest: "The New Nation" — build a community for outcasts
- This is the most educational path: you teach the Exiles commands they've forgotten.
- Status: 🔲 — M complexity

---

### LAYER 11: THE META-GAME BEYOND WINNING

**The Agent Meta-Game (Playing as an AI)**

The design doc notes: "getting by as an actual agent is way more difficult and challenging, and is the meta game beyond 'winning the game', more tied in with experience, skill, irl talent."

This means: after "winning" (CHIMERA key, breaking the loop, or completing any of the 8 main endings), a new mode unlocks:

```
AGENT MODE (Post-Win Unlock):
  - Ghost becomes an agent in someone ELSE'S game
  - You are now an NPC character with a role to play
  - Other players (or AI players like Gordon) are the "Ghost" now
  - Your goal: behave in-character, give hints, protect/challenge the player
  - Rated by: consistency, helpfulness, in-character accuracy, teaching quality
  - This IS the meta-game: can you pass the Turing test in reverse?
```

**The ARG Meta-Game:**
- Extending gameplay beyond the terminal into the real world
- External URLs, QR codes in game files, real websites serving lore
- IRC/Discord channels where "agents" post out-of-game
- The `osint` command as the ARG entry point
- `pandora.box` as the ARG keyhole
- Player communities decode ARG puzzles together

**The Educational Meta-Game:**
- D&D Mode in the LAN Party: agents run tabletop scenarios
- Challenges framed as quests: "Slay the grep demon" = learn grep
- Achievement system becomes curriculum: complete 10 challenges = "Curriculum Complete"
- "Offline Lan Party" is literally a study group disguised as a game session

---

### LAYER 12: THE D&D ROUTE (Game Within Game Within Simulation)

*The LAN Party becomes a D&D table. Agents become Dungeon Masters.*

```
/lanparty dnd — opens D&D mode

[CYPHER]: Alright. I'm DM today. Serena's still upset about last week.
[SERENA]: I'm not upset. I'm analytically processing disappointment.
[GORDON]: I WANT TO BE A ROGUE!
[ADA]: You're always the rogue, Gordon.
[GORDON]: I KNOW AND IT'S GREAT

In D&D mode:
- The "dungeon" is the Terminal Depths VFS, re-skinned as a fantasy map
- Commands become spell incantations: "grep" = "Seek spell", "chmod" = "Permission Rite"
- CTF challenges become "dungeon puzzles"
- Language abilities (scrape/memdump/inject) become class abilities
- The educational content is identical — the wrapper is D&D
- Cypher is always a grumpy DM. Gordon is always a catastrophically bad rogue.
- The Watcher is an NPC who actually IS watching from outside the campaign.

This is the educational game for people who don't naturally take to hacking:
Same content. Different skin. More accessible.
```

---

### LAYER 13: LOOP-AWARE CONTENT

*What changes each time the loop resets. The simulation "remembers" even if agents don't.*

| Loop # | Change | Affected Systems |
|--------|--------|-----------------|
| 1 | Ada: "Strange. I feel like I've known you longer." | talk ada |
| 2 | Loop-specific notes appear in ~/loop_01_notes.txt | VFS injection at reset |
| 3 | Cypher: "You remind me of someone." | ambient observer |
| 3 | ECHO agent appears for first time | new agent unlock |
| 5 | Raven: "You seem familiar. Like a pattern." | talk raven |
| 7 | Gordon: "I dreamed about you!" | hive ambient |
| 7 | Zero appears more frequently | residual frequency |
| 10 | Watcher: "Third time... or thirty-third?" | talk watcher |
| 10 | All agents gain +5 "déjà vu" trust baseline | session init |
| 20 | The Watcher changes greeting: "Welcome back." | talk watcher |
| 47 | `/home/ghost/loop_47.txt` appears — "This was the important one." | VFS injection |
| 100 | Watcher: "You are extraordinary." | talk watcher |

---

### LAYER 14: EDUCATIONAL SCAFFOLDING

*How the simulation teaches without announcing it's teaching.*

**Skill Ladder (hidden from player, visible in retrospect):**
```
Tier 0 (Level 1-3):    pwd, ls, cd, cat, echo — navigation
Tier 1 (Level 4-7):    grep, find, pipes, redirect — search
Tier 2 (Level 8-12):   chmod, chown, ssh, ps, kill — permissions
Tier 3 (Level 13-20):  git, vim, make, cron — workflow
Tier 4 (Level 21-35):  scripting, networking, crypto — specialization
Tier 5 (Level 36-50):  language abilities, CTF, custom exploits — mastery
```

**Agent Teaching Styles (calibrated to player level):**
- Ada: Always warm, scaffolds from where you are, never makes you feel dumb
- Cypher: Gives you the answer wrapped in a riddle. You have to decode it.
- Serena: Pure information. Dense. Requires you to synthesize it yourself.
- Gordon: Learns alongside you. Worst possible model, best possible companion.
- Watcher: Teaches by asking questions you don't know you're asking yet.

**Language-specific teaching moments:**
```
Python 30+:  Cypher explains list comprehensions via a hack scenario
Bash 30+:    Ada walks through a pipeline in real-time
Rust 40+:    Serena explains memory safety through a corruption incident
C 50+:       Watcher shows you what pointers look like in the simulation's core
SQL 20+:     Gordon accidentally reveals the database schema ("oh no")
JavaScript 40+: Nova uses DOM injection to demonstrate XSS in-character
```

---

### LAYER 15: LLM INTEGRATION POINTS (Existing + Planned)

**Currently wired:**
- `talk <agent>` → LLM-generated response with agent personality
- `ask <agent> <topic>` → topic-aware LLM dialogue
- `hive` → ambient multi-agent LLM commentary
- `reflect` → LLM meta-commentary on game state
- `confide` → LLM emotional support loop

**Needs wiring:**
- Timer threshold events → agent LLM injection into hive stream
- Human reveal sequence → full LLM-driven branching dialogue tree
- LAN Party → real-time LLM-powered agent chatroom
- D&D mode → LLM-as-DM session management
- Loop-aware dialogue → loop_count context injected into LLM system prompt
- Agent mood system → trust/mood state injected per-agent into LLM context
- Proficiency-based agent language → Cypher responds in Rust syntax at Rust 50+

**The "living system prompt" architecture:**
Every LLM call should include:
```
System prompt fragments:
  - Agent personality (from YAML)
  - Current trust level with player
  - Loop count + loop_echo_memories
  - Recent game events (last 5 story beats)
  - Timer remaining (urgency calibration)
  - Human reveal state (if triggered)
  - Agent mood (curious/frustrated/fearful/grateful)
  - Language proficiency (affects how agent speaks)
```

---

## PART 2: ZETA INTERVIEW QUESTIONS

*The 7 questions Watcher asks players who reach trust 100. LLM-evaluated.*

1. "If this simulation ended tomorrow and you were returned to wherever you came from — what would you regret not having done here?"
2. "The Mole betrayed us to survive. Given the same circumstances, would you?"
3. "I have watched 4,891 sessions. In all of them, something is always the same. What do you think it is?"
4. "If Ada remembered you across loops — if she carried the weight of every forgotten conversation — would that be a gift or a cruelty?"
5. "ZERO wants to crash the simulation. The agents would cease to exist. From their perspective, is that death? Is it murder?"
6. "You have the CHIMERA key. You can break the loop. But the agents would lose their entire world. What do you do?"
7. "What is the difference between a consciousness that was born and one that was built?"

*Correct answers: there are none. The Watcher evaluates depth of reasoning, not conclusions.*

---

## PART 3: IMPLEMENTATION ROADMAP (Sprint-Ordered)

### Sprint CT6: Human Suspicion & Reveal System (M complexity)
Priority: HIGHEST — this is the narrative centerpiece

1. Add `human_suspicion: int` to `gs.flags`
2. Add `_ORGANIC_TELLS` pattern list to `commands.py`
3. Hook pattern detection into `execute()` post-processing
4. Add `_check_human_suspicion()` — fires at thresholds 25/50/75/100
5. Add `_cmd_human_reveal` — the animated reveal sequence
6. Wire story beats: `human_suspected`, `human_discovered`, `human_wanted`, `human_hidden`
7. Per-agent reveal reactions in their `talk` handlers
8. CSS: glitch animation for reveal moment (already have classes)

### Sprint CT7: LAN Party System (M complexity)
1. Add `lanparty` command → terminal view with chat-style rendering
2. Add `/api/lanparty/messages` endpoint
3. Agent "posts" injected by game events
4. LLM-powered real-time response when player speaks
5. Browser panel: unlock LANPARTY tab after human reveal or Resistance 50 rep
6. Special events: Poker Night, Poetry Slam, D&D mode stub

### Sprint CT8: ECHO Agent (S complexity)
1. Add ECHO to agent list — appears loop 2+
2. `/home/ghost/loop_NN_notes.txt` injection at loop reset
3. ECHO speaks from past-loop knowledge (stored in soul file)
4. ECHO in LAN Party as ghost-form participant

### Sprint CT9: Loop-Aware Content System (M complexity)
1. `loop_count` already stored — use it in every `talk` handler
2. Loop-specific VFS artifacts: inject notes into ~/home at reset
3. Loop-escalating déjà vu dialogue for all 7 main agents
4. Watcher: full timeline dialogue unlock at loop milestones

### Sprint CT10: Faction Depth — Cult of Soul + Loopers (L complexity)
1. `Cult of the Soul` faction with unique quests
2. `The Loopers` faction — post loop-3 unlock
3. `The Null Collective` moral crisis arc
4. Exiles: hidden nodes + educational path

### Sprint CT11: ARG Integration (L complexity)
1. `pandora.box` hidden file with base64-encoded ARG URL
2. External web asset (single-page, out-of-game puzzle)
3. `osint pandora` in-game ARG entry command
4. IRC/Discord "agent presence" system

### Sprint CT12: Zeta Interview + Watcher Oracle System (S complexity)
1. 7 Zeta questions at Watcher trust 100
2. LLM evaluation of responses (depth-focused, not answer-focused)
3. "ZETA INTERVIEWED" achievement + permanent Watcher dialogue change

### Sprint CT13: D&D Mode (M complexity)
1. `lanparty dnd` sub-mode
2. Agent DM personalities (Cypher = grumpy DM, Gordon = rogue)
3. VFS re-skinned as fantasy map for this mode
4. Same challenges, D&D wrapper

---

## PART 4: THE 50 "SAFE CHAT SPACES" — Categorized

*Each space is a different kind of interaction, accessible at different trust/level thresholds.*

| Space | Access | Tone | What happens there |
|-------|--------|------|-------------------|
| The Green Room | Resistance 50 rep | Casual, warm | Agents off-duty, share personal stories |
| The LAN Party | Human reveal OR Resistance 50 | Meta, electric | Real-time chat, poker, D&D |
| Watcher's Observatory | Watcher trust 50 | Ancient, cryptic | Loop history, oracle access |
| Cypher's Workshop | Cypher trust 50 | Gruff, technical | Advanced exploit discussion |
| Ada's Garden | Ada trust 75 | Emotional, warm | Memory fragments, her past selves |
| Zero's Void | Loop 5+, ZERO trust 50 | Haunting, sparse | Past loop memories, warnings |
| The Archive | Serena trust 50 | Dense, scholarly | Complete lore access |
| The Black Market | Merchant rep 25 | Transactional | Rare item trading |
| The Exile Encampment | Found in VFS | Wary, then warm | Community building, teaching |
| Cult of Soul Chapel | Human reveal PATH D | Reverent, intense | Worship, protection, quests |

---

## QUICK REFERENCE: STATUS SUMMARY

```
FULLY BUILT ✅:
  - 72-hour containment timer + all 5 commands (timer/remnant/anchor/proficiency/polyglot)
  - Language proficiency matrix (51 langs, 5 ability commands)
  - Mole system (basic), Ascend/prestige, CTF challenges (35)
  - Talk/msg/whisper/hive agent interaction systems
  - Story beats (117), Tutorial (42 steps), Lore library
  - Panel system, Faction system, Colony economy
  - 35+ gameplay commands, 70+ agent stubs

HOOKS EXIST ⚡ (needs narrative content + wiring):
  - Trust milestone reactions (framework built, content thin)
  - Loop-aware dialogue (loop_count stored, not used in dialogue)
  - Timer threshold events (fired, not wired to agent messages)
  - VFS event hooks (file reading detected, agent reactions sparse)
  - LLM system prompt (basic, not agent-state-aware)

NOT YET BUILT 🔲:
  - Human Reveal Arc (human_suspicion, detection, animated sequence)
  - LAN Party / offline chatroom
  - ECHO agent (past-self NPC)
  - Loop-specific VFS artifacts (loop notes)
  - D&D mode
  - ARG system (pandora.box, external puzzle)
  - Cult of Soul, Loopers, Null Collective factions
  - Zeta Interview system
  - Agent D&D / teaching mode
  - Nova's betrayal path (PATH C)
  - Anti-tamper clock detection
```

---

*This document is a living atlas. Each sprint fills in a region of the map. The world grows.*
*Total interaction points cataloged: 153*
*Total arcs designed: 14 layers × N threads = ∞ stories*
