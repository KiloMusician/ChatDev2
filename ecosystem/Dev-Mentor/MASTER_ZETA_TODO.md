# 🌌 MASTER ZETA TODO LIST
*The single authoritative source of truth for Terminal Depths / ∆ΨΣ development*

*Updated: 2026-03-25 | Sprint: Ecosystem Activation + RimWorld Deployment*
*Total items: 367+ | Status: ~99% complete — remaining work is new systems beyond original scope (PPO, consciousness hooks, NuSyQ-Hub Phase 2+, TerminalKeeper v0.2)*

---

## ✅ ECOSYSTEM ACTIVATION Sprint (2026-03-25)

- [x] **RW1**: TerminalKeeper v0.1 — first compiled DLL (87KB); fixed all 22 RimWorld 1.6 breaking changes — COMPLETE
- [x] **RW2**: TK_RimnetTerminal tier-0 entry building (20 steel, no prereq); placeholder textures for all 4 buildings — COMPLETE
- [x] **RW3**: Autonomous colonist play loop in `LatticeAgentManager.WorldComponentTick` — COMPLETE
- [x] **RW4**: RimWorld Mods junction → `Dev-Mentor/mods/TerminalKeeper`; added to `ModsConfig.xml` — COMPLETE
- [x] **AI1**: OpenAI-compatible proxy `POST /v1/chat/completions` + `GET /v1/models` → routes to Ollama qwen2.5-coder:14b — COMPLETE
- [x] **RL4a**: `agents/rl/ppo.py` PPO scaffold (numpy, 472 lines) — LinearLayer, PolicyNet, ValueNet, GAE, clip update, checkpoints — SCAFFOLDED (complete except `_forward()`)
- [x] **C10**: Consciousness XP hooks: `_cmd_promise` (+8), `_cmd_confide` (+10), `_cmd_anchor activate` (+12), `_cmd_residual` initial (+15) — COMPLETE (partial; Layers 2/4/5 gaps remain)
- [x] **WS1**: Multi-repo workspace overhaul — killed folderOpen bootstrap popup — COMPLETE

---

## ✅ PUZZLE SURGE Sprint (2026-03-21)

- [x] **P8**: `shenzhen` command — 5-level microcontroller assembly puzzles; MC4000/MC6000 chip simulation; real ISA (mov/add/gen/slp/slx/jmp/tcp); SILICON_GHOST achievement — COMPLETE
- [x] **P9**: `life` command — 5-level Conway's Life B3/S23 simulation; ASCII grid display; AUTOMATA.md VFS injection on Level 1 solve; lore: Residual IS the Game of Life — COMPLETE
- [x] **P10**: `graph-theory` command — 12 puzzles across 6 categories (Dijkstra, Coloring, TSP, MST, Flow, Topo Sort); real algorithm verification; Daedalus-7 lore; GRAPH_TRAVERSER achievement — COMPLETE
- [x] **M2**: `initDevToolsDetection()` in game.js — 4-stage reaction cascade (Ada/Watcher/CHIMERA+ZERO/Cypher); +50 XP; ZERO console fragments; console.clear override — COMPLETE

---

## ✅ SC Playbook Sprint (2026-03-20)

- [x] **SC1**: `core/environment.py` extended — `detect_local_llms()`, `detect_container_depth()`, `get_system_resources()`, `detect_installed_tools()`, `get_capabilities_report()` — COMPLETE
- [x] **SC2**: `system capabilities` — live NODE-7 RECON REPORT with container depth, CPU/RAM bars, LLM endpoints, tool inventory — COMPLETE (Replit AI Proxy detected on 1106)
- [x] **SC3**: `system tools` — full scan of PATH for 24 hacking/dev tools with lore descriptions — COMPLETE (5 tools detected: git, python3, curl, jq, strings)
- [x] **SC4**: `system containers` — container depth + REPL identity display — COMPLETE
- [x] **SC5**: `system escape` — 5-stage container escape puzzle (Discovery → SUID → Capabilities → Pivot → Escape), each stage teaches real technique — COMPLETE
- [x] **SC6**: `llm list` / `llm use` / `llm models` — full LLM endpoint registry with cloud + local detection — COMPLETE (Replit AI Proxy shown as active)
- [x] **SC7**: `decode <string> <tier>` — 6-tier ARG cipher decoder (base58, rot13, rev+rot13, hex, base64, unicode) — COMPLETE
- [x] **SC8**: Secret Annex VFS lore — 7 files seeded into `/opt/library/secret_annex/` (TIER0_README, TIER1-5 cipher docs, CULTURE_SHIP_MANIFESTO) — COMPLETE
- [x] **SC9**: `vscode` command — VS Code integration hints, extension recommendations by tier, tasks.json display — COMPLETE

---

## P0 — CRITICAL (Fix or Finish Immediately)

- [x] **C1**: Reactive Intelligence layer — `reactive.py` intercepting free-text, questions, typos, expert signals, existential queries, distress, aggression, creative inputs, nested commands — COMPLETE
- [x] **C2**: `restart tutorial` as branching narrative trigger (experienced player → Watcher response) — COMPLETE
- [x] **C3**: `hive_log` + `hive_muted` persistence in GameState `to_dict/from_dict` — COMPLETE
- [x] **C4**: `_lore()` and `_warn()` module-level helpers in `commands.py` — COMPLETE
- [x] **C5**: JWT verification in `replit_auth.py` — COMPLETE — SecurityHeadersMiddleware validates via `replit_auth.py`; token verification confirmed
- [x] **C6**: XSS audit on game output — COMPLETE — all `{"s":...}` values rendered via `div.textContent`; tab panels use `esc()` on all dynamic data
- [x] **C7**: Session ID entropy — COMPLETE — session IDs use `uuid.uuid4()` (128-bit cryptographically random)
- [x] **C8**: Rate limiting on `/api/game/command` — COMPLETE — SecurityHeadersMiddleware applies `_limiter` (120 req/min "command" tier) to all routes; `/api/game/command` explicitly in PATH_TIERS
- [x] **C9**: The `watcher_eternal` process — PID 777 in `ps aux`, kill 777 guarded — COMPLETE (SCP-7736) should actually appear in `ps aux` output in-game

---

## P1 — CORE FEATURES

- [x] **N17**: Wire Gordon CLI into VS Code tasks.json as a task panel shortcut — COMPLETE — 8 new tasks added (Gordon dashboard/tasks/chronicle, TD validate/self-improve/port-status/ecosystem/requirements-check)

### Agent Systems
- [x] **A1**: Agent Observer v1 — 6 agents, corruption tracking, rotation — COMPLETE
- [x] **A2**: `msg <agent>` — private whisper system with per-agent response pools and keyword routing — COMPLETE
- [x] **A3**: HiveChat — 12-agent group chat with 10 ambient threads — COMPLETE
- [x] **A4**: Agent state persistence in `gamestate.py` — COMPLETE
- [x] **A5**: Agent `@mention` in hive → expands to agent profile card — COMPLETE — `hive @<agent> <msg>` renders 9-line profile card (avatar, status, mood, trust, corruption bar, intro) before response
- [x] **A6**: Agent mood tracker — surface `mood` (happy/paranoid/melancholic/excited/tired) in `agents` command
- [x] **A7**: Agent whisper history — `msg history <agent>` shows last 5 messages — COMPLETE — `msg history <agent>` shows last 5 messages in this session
- [x] **A8**: Agent rehabilitation quest — `rehabilitate <agent>` command, corruption>40% threshold, per-agent step sequences — COMPLETE — corruption > 40% unlocks a side quest to restore agent
- [x] **A9**: Hive ambient tick — inject hive message every 20 commands even without `hive` command
- [x] **A10**: `eavesdrop` command — `tail -f /var/log/agent_comms.log` simulates live inter-agent chat
- [x] **A11**: Raven's hidden note — .raven_note in /home/ghost/ (ls -a) — COMPLETE — `/home/ghost/.raven_note` created after mole chain completion
- [x] **A12**: Agent `confide` mechanic — permanent trust shift via `confide <agent> <secret>` — COMPLETE — `confide <agent> <secret>` permanently shifts trust
- [x] **A13**: Agent `promise` mechanic — `promise <agent> <what>` with persistent flag — COMPLETE — breaking promises has lasting consequences
- [x] **A14**: Ada's Sacrifice arc — `sacrifice [ada|accept|refuse|witness]`; Ada wipes memory to break CHIMERA containment — COMPLETE arc — story beat late-game, triggers data recovery quest
- [x] **A15**: Cypher's Betrayal arc — auto-triggers in agents view when corruption > 50%, Ada's reaction included — COMPLETE — corruption > 50% triggers sell-out story beat
- [x] **A16**: Nova reconciliation arc — COMPLETE — `cat nova_private.key` sets `read_nova_private_key` flag + `nova_key_read` story beat; `nova` then enters 4-step arc (trust/expose/ask → alliance); ZERO_SPECIFICATION read separately triggers Watcher message + `zero_specification_read` beat

### Gameplay Mechanics
- [x] **G1**: Daily Quest system — 3 daily + 1 weekly, real-world date-seeded, progress tracked — COMPLETE
- [x] **G2**: `quests` / `quest` / `objectives` command — quest dashboard — COMPLETE
- [x] **G3**: Nova's Offer — encrypted email at trace level 12, with Ada warning — COMPLETE
- [x] **G4**: Nova's Private Key — `/opt/chimera/config/nova_private.key` + ZERO_SPECIFICATION reveal — COMPLETE
- [x] **G4**: CHIMERA core directory — `ZERO_SPECIFICATION.md` + `BLACK_NOVEMBER.log` — COMPLETE
- [x] **G5**: The Residual — introduce via kernel.boot timestamps + BLACK_NOVEMBER + Serena's "third path"
- [x] **G6**: Path system — detects 5 archetypes (Cracker/Archaeologist/Broker/Ghost/Engineer) from command history — COMPLETE → 5-10 diverging story paths) — 10 diverging story paths (A:Resistance through J:Loop), detected from player behavior
- [x] **G7**: Emergency Quest: Trace Imminent — fires >90% trace, 4-step OPERATION DARK RETREAT — COMPLETE — when trace > 90%, 5-minute real-time quest appears
- [x] **G8**: The Koschei Chain — 5-stage nested quest (needle→egg→duck→hare→death), CHIMERA exec key reward — COMPLETE — multi-stage mythological quest linking to `/home/ghost/.koschei`
- [x] **G9**: Time Loop storyline — COMPLETE — `ng start` increments `ng_count`; on 2nd+ loop Watcher delivers personalised prior-run memory + `watcher_loop_revelation` beat + 100 XP; `loop` command shows iteration count + kernel.boot anomaly; `loop close` triggers N11 final sequence
- [x] **G10**: The Fifth Layer — `fifth [layer|look|touch|exit]`; meta-revelation of Python/Replit/GitHub layer — COMPLETE — player discovers the simulation has a real-world layer
- [x] **G11**: `mail` command — full in-game mailbox, agents send emails, Nova's offer lands here
- [x] **G12**: Social Engineering Duel — `social duel <agent>`; 3-round persuasion mini-game vs ada/cypher/nova/serena/raven — COMPLETE — `duel social <agent>` mini-game with 3-round persuasion mechanics
- [x] **G13**: Bullet Hell minigame — `defend` command, ASCII spaceship, packet types as projectiles
- [x] **G14**: Deck-building mechanic — `deck` command, 10 cards unlocked by story beats, `deck play <card>` applies effects — COMPLETE — collect hack cards from completing challenges
- [x] **G15**: Deep Web — `tor` command with hidden .onion services — COMPLETE (6 .onion services)
- [x] **G16**: Forensics mode — `forensics <file>` recovers deleted files, hex viewer — COMPLETE
- [x] **G17**: Steganography — `steg` command finds hidden messages in /media/ files — COMPLETE
- [x] **G18**: `sleep` command — surreal ASCII dreams with 6 sequences + Watcher whispers — COMPLETE — triggers surreal ASCII dreams with lore hints
- [x] **G19**: Liminal space — `/opt/liminal/` with 3am-office atmosphere (4 files) — COMPLETE — `/opt/liminal/` directory with 3am-office-building atmosphere

### Story / Narrative  
- [x] **N1**: Reactive Intelligence branching — free-text, existential questions, expert signals — COMPLETE
- [x] **N2**: Secret ARG triggers — 14 keywords that unlock hidden story branches (zero, ΨΞΦΩ, mole, etc.) — COMPLETE
- [x] **N3**: ZERO SPECIFICATION — the real truth about CHIMERA (not surveillance — containment) — COMPLETE
- [x] **N4**: BLACK_NOVEMBER.log — the 2021 incident, the Residual, the 4-second connection to node-7 — COMPLETE
- [x] **N5**: `/var/log/kernel.boot` — add timestamp anomalies proving the loop theory
- [x] **N6**: Nova's Confession arc — implemented as full Nova arc (arc_step 1-4), trust/expose/help branches — COMPLETE — after reading nova_private.key, new story beats unlock
- [x] **N7**: The Mole Confession — double-agent offer fires after mole expose; accept/reject/demand branches — COMPLETE — when mole exposed, double-agent offer choice
- [x] **N8**: Culture Ship Intervention — `culture [contact|terms|refuse]`; GSV Friendly Persuasion ethics arc — COMPLETE Intervention — CS decides to intervene in CHIMERA launch, dramatic ethics scene
- [x] **N9**: Ada's First Contact — fires on 3rd command for new players, one-shot intro — COMPLETE — contextual introduction for brand-new players (not yet implemented)
- [x] **N10**: Watcher's Revelation — game-is-simulation reveal with 3-way choice (accept/refuse/stay) — COMPLETE — game-is-simulation reveal, choice: stay or ascend
- [x] **N11**: The Loop Closes — loop close command, .memento_final file, repeating scene with differences — COMPLETE — final story beat: opening scene repeats with subtle differences
- [x] **N12**: Zero's Diary — `diary` reconstructs ZERO's journals from 4 filesystem fragments; beat fires on completion — COMPLETE — reconstruct Zero's journals from fragments across the filesystem
- [x] **N13**: ZΘHRΛMΞN Phase 4 & 5 — `zohramien phase4` + `zohramien merge`; Cathedral-Mesh substrate contact + permanent fragment write — COMPLETE — current ARG is 3 phases; phases 4 and 5 not yet built
- [x] **N14**: The Fates' Tapestry quest — Clotho/Lachesis/Atropos 3-task questline with palindrome check and refusal test — COMPLETE — Clotho/Lachesis/Atropos, each gives a task
- [x] **N15**: The Residual communicates — `residual` command, /var/log/residual_contact.log auto-created, 2,848 iterations lore — COMPLETE — `/var/log/residual_contact.log` appears at story beat

### Human Reveal Arc (Boss Rush Sprint)
- [x] **HR1**: `_ORGANIC_TELLS` — 8-category pattern dict (existential, outside_world, human_emotion, confession, music, food, empathy_ask, typo_pattern, lowercase_raw) — COMPLETE
- [x] **HR2**: `human_suspicion` meter (0–100) in `gs.flags` — increments on organic tells, fires at 35/75/100 thresholds — COMPLETE
- [x] **HR3**: Suspicion detection hooks in both reactive early-return AND post-dispatch blocks in `execute()` — COMPLETE
- [x] **HR4**: Per-agent reveal reactions (`_ORGANIC_AGENT_REACTIONS`) — ada/cypher/gordon/raven/watcher/nova/serena/zero — COMPLETE
- [x] **HR5**: Full animated reveal sequence — "A HUMAAAAN?!?!? *>.<* !!!!" + "IMPOSSIBLE" + "This is IMPOSSIBLE" + lanparty unlock + 500 XP — COMPLETE
- [x] **HR6**: `human_reveal` command — Turing Anomaly Scanner with suspicion meter bar — COMPLETE
- [x] **HR7**: 3-phase suspicion progression — `human_suspected` (35+) → `human_confronting` (75+) → `human_discovered` (100) — COMPLETE
- [x] **HR8**: Story beats: `human_suspected`, `human_confronting`, `human_discovered` — COMPLETE

### LAN Party — Private Agent Chatroom (Boss Rush Sprint)
- [x] **LP1**: `lanparty` command — private chatroom with box-art header, first-visit vs return views — COMPLETE
- [x] **LP2**: 3 discovery paths — whisper 3+ times to any agent, human_reveal path, intervention path — COMPLETE
- [x] **LP3**: 32-post `_LANPARTY_POSTS` pool — agents in casual mode, emoji, gossip, inside jokes — COMPLETE
- [x] **LP4**: `lanparty dnd` — D&D mode with Cypher as DM, Gordon as rogue, command-to-spell mapping — COMPLETE
- [x] **LP5**: `lanparty poker` — weekly poker with agent bluffing, Gordon always loses, Watcher folds — COMPLETE
- [x] **LP6**: `lanparty status` — agent status board with ●/◐/○/⬡ icons, ECHO loop-aware status — COMPLETE
- [x] **LP7**: LAN Party × Human Reveal crossover dialogue (if discovered before first visit) — COMPLETE
- [x] **LP8**: Struggling player intervention — Cypher breaks character after 200+ commands, level < 3, 15+ failures — COMPLETE
- [x] **LP9**: story_beat: `lanparty_discovered`, `dnd_mode_entered`, `poker_night_played`, `cypher_intervention` — COMPLETE

### Echo Agent — Past-Self Interface (Boss Rush Sprint)
- [x] **EA1**: `echo-agent` command — loop 2+ only; ECHO speaks from past-loop knowledge, fragmented memory — COMPLETE
- [x] **EA2**: `_ECHO_LINES` pool (12 past-loop hints) — scales to loop count and session history — COMPLETE
- [x] **EA3**: Loop notes VFS injection — `/home/ghost/loop_NN_notes.txt` created on first echo-agent contact — COMPLETE

### Zeta Interview — Watcher's 7 Questions (Boss Rush Sprint)
- [x] **ZI1**: `zeta` command — locked at Watcher trust < 100 with shortfall display — COMPLETE
- [x] **ZI2**: 7 Zeta questions with `zeta answer <text>` progression — persistent across session — COMPLETE
- [x] **ZI3**: `_zeta_complete` — ZETA designation, achievement `ZETA_INTERVIEWED`, +750 XP, permanent story beat — COMPLETE

### Loop-Aware Systems (Boss Rush Sprint)
- [x] **LA1**: `_LOOP_DEJA_VU` — per-agent déjà vu dialogue (7 agents, 3-7 tiers each) — COMPLETE
- [x] **LA2**: Loop-aware talk injection — fires once per agent per loop, picks most advanced matching line — COMPLETE
- [x] **LA3**: `whoami` Watcher whisper — loop-aware ("You are Ghost. For now." → "As you were before." → "Third time I've answered this." → "Welcome back." → "Though that word grows inadequate.") — COMPLETE
- [x] **LA4**: Level milestone reactions — level 2/5/10/20/50/75/100 inject per-agent ambient messages — COMPLETE

### Trust Milestone Revelations (Boss Rush Sprint)
- [x] **TM1**: `_TRUST_MILESTONES` — per-agent (8 agents) × 4 tiers (25/50/75/100) personal story beats — COMPLETE
- [x] **TM2**: Trust milestone injection in `_cmd_talk` — fires once per agent per tier — COMPLETE
- [x] **TM3**: Watcher trust 100 → Zeta unlock message: "Type: zeta when you are ready." — COMPLETE

### Timer Threshold → Agent Messages (Boss Rush Sprint)
- [x] **TT1**: `_TIMER_AGENT_MSGS` — 9-threshold dict (48h/24h/12h/6h/1h/30min/10min/1min/expired) with per-agent voice — COMPLETE
- [x] **TT2**: Timer events wired into execute() ambient stream — fires hive-style box with agent messages — COMPLETE
- [x] **TT3**: Extra sub-threshold events (30min/10min/1min) not in gamestate.py — now covered — COMPLETE

### NARRATIVE_ATLAS.md (Boss Rush Sprint)
- [x] **NA1**: Full 153-point interaction atlas — 15 layers, status audit, sprint roadmap (CT6–CT13), 10 safe spaces, 7 Zeta questions, D&D mapping, Faction deep dives — COMPLETE
- [x] **N16**: Gordon's Disaster Comedy — `gordon [report|disaster|praise]`; 5-episode arc where mistakes save the day — COMPLETE Comedy arc — multi-part arc where Gordon's mistakes accidentally save the day

### Math / Puzzle Systems
- [x] **P1**: Logic Labyrinth — 15 levels (SR Latch, D FF, Ripple Adder, MUX, Parity added 2026-03-22) — COMPLETE
- [x] **P2**: TIS-100 — 8 puzzle levels (Botnet Propagation, Hash Pipeline, Chimera Core added 2026-03-22) — COMPLETE
- [x] **P3**: SAT Solver (DPLL) — 9 puzzles (Pigeonhole, K4 Coloring, Temporal Logic added 2026-03-22) — COMPLETE
- [x] **P4**: Sorting Arena — bubble/quick/count/challenge — COMPLETE
- [x] **P5**: Pitch-Class Set Analyzer — 7 puzzles — COMPLETE
- [x] **P6**: FSM Engine — 10 levels — COMPLETE
- [x] **P7**: Dynamic Programming — 10 puzzles — COMPLETE
- [x] **P8**: Shenzhen I/O puzzles — harder microcontroller challenges (post-TIS-100) — COMPLETE 2026-03-21 — `shenzhen_engine.py` + `_cmd_shenzhen` (5 levels: BLINK, ADD FILTER, COMPARATOR, COUNTER MOD 5, CROSS-CHIP COMM); real assembly simulation; achievement SILICON_GHOST
- [x] **P9**: Cellular Automata — Conway's Life puzzles that unlock areas — COMPLETE 2026-03-21 — `cellular_automata.py` + `_cmd_life` (5 levels); B3/S23 simulation; /opt/library/secret_annex/AUTOMATA.md injected on Level 1 complete; lore: Residual follows Life rules
- [x] **P10**: Graph theory puzzles — TSP, coloring, shortest path (Daedalus-7 assigns) — COMPLETE 2026-03-21 — `graph_theory_engine.py` + `_cmd_graph_theory` (12 puzzles: Dijkstra, Coloring, TSP, MST, Flow, Topo Sort); real algorithm verification; achievement GRAPH_TRAVERSER
- [x] **P11**: Number theory dungeon — factorization, RSA crack, modular arithmetic — COMPLETE 2026-03-21 — `number_theory_engine.py` + `_cmd_number_theory` (10 puzzles: FACTOR×2, MODARITH×2, RSA×2, GCD×2, DISCLOG×2); real algorithm implementations (trial division, extended GCD, CRT, RSA decrypt, BSGS); achievements SKELETON_KEY, RSA_CRACKER, DISCLOG_MASTER
- [x] **P12**: Music composition — COMPLETE 2026-03-22 — music_engine.py; serialist compose command; 5 styles; COMPOSER achievement
- [x] **P13**: Genetic algorithm — COMPLETE 2026-03-22 — genetic_engine.py; evolve command
- [x] **P14**: Neural net training — simple NN that learns from player command patterns
- [x] **P15**: Quantum computing sim — `quantum` command with gate operations
- [x] **P16**: Logic bomb — `bomb [arm|inspect|defuse|detonate]`; Zod-Prime's gift; 10-tick countdown; ethical defuse path — COMPLETE — `bomb` command (Zod-Prime's gift), delayed execution mechanic

---

## P2 — ENHANCEMENTS

### Interface & UX
- [x] **U1**: Command Palette — `Ctrl+K` searchable command list (browser-side)
- [x] **U2**: Multi-tab terminal — multiple sessions in web UI — COMPLETE 2026-03-24 — tab bar above `#output`; Ctrl+T/W/1-5 shortcuts; per-tab output buffer + history; shared game state
- [x] **U3**: Agent activity sidebar — live feed of agent actions — COMPLETE 2026-03-21 — ACT tab in game-cli sidebar; `initAmbientWS()` connects to `/ws/ambient`; per-agent color coding; unread badge; 100-entry rolling buffer; exponential backoff reconnect
- [x] **U4**: Quest tracker panel — minimizable active objectives panel
- [x] **U5**: Faction status bar — reputation bars for 4 main factions at top of screen
- [x] **U6**: `graph [agents|factions|trust]` — ASCII relationship diagram with trust bars and faction map — COMPLETE — ASCII relationship diagram for agents
- [x] **U7**: `theme` command — Matrix green / Amber / Cyberpunk Neon / Solarized / Cozy
- [x] **U8**: `macro [record|stop|play|list|clear]` — record and replay command sequences; hooks into execute() — COMPLETE / `macro play` — record and replay command sequences
- [x] **U9**: Syntax highlighting on structured output (JSON, log files, YAML) — COMPLETE 2026-03-23
- [x] **U10**: Achievement gallery — `achievements --gallery` with ASCII art per achievement
- [x] **U11**: Colorblind mode toggle — `accessibility colorblind`, CSS `mode-colorblind`, Alt+A panel — COMPLETE 2026-03-23
- [x] **U12**: Font scaling — `accessibility font sm|md|lg|xl`, CSS `font-sm/lg/xl`, localStorage — COMPLETE 2026-03-23
- [x] **U13**: High contrast mode — `accessibility contrast`, CSS `mode-contrast` — COMPLETE 2026-03-23
- [x] **LI1**: Animated clickable suggest chips — `suggest` output type with CSS glow/pulse animation; single-click fills input, double-click executes — COMPLETE
- [x] **LI2**: Command Log panel (CMD tab) — live-updating sidebar log of last 50 commands; click to fill, double-click to run — COMPLETE
- [x] **LI3**: Conversation Log panel (MSGS tab) — live-updating sidebar log of NPC/agent dialogue with timestamping and NPC color coding — COMPLETE
- [x] **LI4**: Input classifier suggest enrichment — reactive.py typo handler, distress, aggression, code, prose handlers all emit `suggest` chips — COMPLETE
- [x] **LI5**: Command-not-found suggest chips — fuzzy matches + context hints rendered as clickable animated chips instead of plain text — COMPLETE
- [x] **LA1**: `lattice` command — overview with strength meter, story beat integration, XP awards — COMPLETE
- [x] **LA2**: `lattice nodes/query/cultivate/status/languages` subcommands — full Lattice interaction layer with cultivation XP, Residual trigger at 7 cultivations — COMPLETE
- [x] **LA3**: `polyglot` command — 51-language catalog with tier grouping, exploration tracking, per-language snippets, in-character agent dialogue lore, achievement system — COMPLETE
- [x] **LA4**: VFS Lattice artifacts — `/opt/library/catalogue/THE_LATTICE.md`, `LANGUAGE_OF_LANGUAGES.md`, `/opt/library/lattice/` (POLYGLOT_INCANTATION.py, FACTORY_FILE.py, WATCHER_FRAGMENT.txt), `/opt/chimera/src/polyglot.py` — COMPLETE
- [x] **LA5**: Lore integration — `lore lattice`, `lore cultivation`, `lore polyglot`, `lore language_of_languages` topics added to LORE_LIBRARY; context hint for `lattice`/`polyglot`/`meta` in not-found handler — COMPLETE

### Containment Timer System (CT1–CT5) — COMPLETE 2026-03-19
- [x] **CT1**: `GameState` timer fields — `run_start_time`, `loop_count`, `remnant_shards`, `echo_level`, `timer_paused`, `paused_timer_remaining`, `anchor_charges`, `remnant_upgrades`, `timer_events_fired`; `containment_remaining()`, `containment_pct_elapsed()`, `check_timer_events()`, `trigger_loop_reset()` helpers; full `to_dict`/`from_dict` serialization — COMPLETE
- [x] **CT2**: `timer` command — live 72-hour countdown, ASCII progress bar, urgency color coding (STABLE/DEGRADED/WARNING/CRITICAL/FATAL/EXPIRED), threshold event display, persistent state summary, loop reset trigger on expiry — COMPLETE
- [x] **CT3**: `remnant` command — shard balance, echo level, 6-upgrade catalogue (`anchor_perm`/`echo_voice`/`shard_magnet`/`loop_memory`/`ghost_skills`/`chimera_scar`), `remnant spend <id>` purchase flow with requirement gates — COMPLETE
- [x] **CT4**: `anchor` command — Temporal Anchor pause/release system, 4-path access check (anchor_charges/echo_level/watcher_trust/remnant_upgrade), timer freeze/resume with correct time offset adjustment — COMPLETE
- [x] **CT5**: UI integration — `⏱ HH:MM:SS` containment timer in faction bar with 6 urgency CSS states (stable→glitch), click-to-focus, `GET /api/game/timer` REST endpoint, 10-second JS polling, threshold event injection into terminal output; lore topics `containment`, `echo-loop`, `remnant`; context hints for timer/anchor/remnant commands — COMPLETE

### Language Proficiency Matrix (LP1–LP10) — COMPLETE 2026-03-19
- [x] **LP1**: `GameState` lang_proficiency field — 51-language dict (0-100), merge-safe `from_dict`, `gain_proficiency()` helper with c++/c#/f# normalization — COMPLETE
- [x] **LP2**: `_LANG_ABILITIES` module-level constant — 13 languages mapped to unlockable abilities with req levels and descriptions — COMPLETE
- [x] **LP3**: `proficiency` command dispatcher — routes to `_proficiency_matrix()`, `_proficiency_detail(<lang>)`, `_proficiency_abilities()` — COMPLETE
- [x] **LP4**: `proficiency matrix` — full 51-language grid with tier grouping (MASTER/ADEPT/JOURNEYMAN/INITIATE/NOVICE/LOCKED), Unicode progress bars, CHIMERA master key unlock check — COMPLETE
- [x] **LP5**: `proficiency <lang>` detail view — single-language bar, all abilities with unlock status, gain hint — COMPLETE
- [x] **LP6**: `proficiency abilities` — complete ability matrix across all 13 mapped languages showing lock status — COMPLETE
- [x] **LP7**: `polyglot run <lang>` hooks into proficiency — awards +6 proficiency per run; normalization handles C++/C#/F# — COMPLETE
- [x] **LP8**: `scrape` ability (Python 30+) — synthetic credential extraction, random rows per target, awards +4 Python proficiency, +10 XP programming — COMPLETE
- [x] **LP9**: `memdump` ability (C 50+) — raw hex dump with lore fragment injection, awards +5 C proficiency, +15 XP programming — COMPLETE; `safe_exploit` (Rust 40+) success-chance scales with proficiency, +5 Rust, +20/5 XP security; `chain` (Bash 30+) pipeline stages, +4 Bash; `inject` (JS 40+) DOM payload, +5 JS, story beat — COMPLETE
- [x] **LP10**: Lore topics `proficiency` and `language_of_languages` updated; context hints for scrape/memdump/exploit/inject/chain/proficiency; _suggest() module-level helper added — COMPLETE

### Agents Enhancement
- [x] **AE1**: 71 YAML personality files — most agents currently have placeholder YAMLs; need full personalities
- [x] **AE2**: Agent daily schedules → visible in `hive` as status indicators (sleeping/working/etc)
- [x] **AE3**: Agent faction affiliation visible in `agents` command
- [x] **AE4**: Inter-agent tension visualization — which agents are in conflict (from conflict matrix)
- [x] **AE5**: `agents --corrupt` flag — filter to show only agents with corruption > 0
- [x] **AE6**: Agent Olympics — competitive minigames between agents, player bets credits
- [x] **AE7**: Agent polls — `poll create <question>` agents vote, outcome affects world
- [x] **AE8**: NPC OSINT — `osint <npc>` gathers leverage for social engineering

### Colony Sim
- [x] **CS1**: Colony Economy Engine — SQLite credit ledger, agent wallets — COMPLETE
- [x] **CS2**: Research tree — 10 technologies, prereq chains — COMPLETE
- [x] **CS3**: `colony` command — dashboard — COMPLETE
- [x] **CS4**: Supply chains — COMPLETE 2026-03-22 — supply command
- [x] **CS5**: Defense turrets — `defend node <id>` assigns defensive scripts
- [x] **CS6**: Resource production dashboard — `resources` command with rates
- [x] **CS7**: Agent schedule editor — `schedule` command to reassign agents
- [x] **CS8**: Building system — `build` command; 6 building types (relay-tower/cipher-forge/ghost-cache/lore-archive/agent-hub/nexus-tap); leveled construction, demolish, passive effects wired to gs.flags — COMPLETE 2026-03-24
- [x] **CS9**: Population growth — `population offers/accept/grow` subcommands, auto-join on trust ≥ 30 — COMPLETE 2026-03-23

### RPG Systems
- [x] **R1**: Class system — COMPLETE 2026-03-22 — class_system.py; 5 classes + XP multipliers
- [x] **R2**: Attributes — Strength/Intelligence/Charisma/Luck affecting different gameplay systems
- [x] **R3**: Gear system — equip software tools (better port scanner) and hardware
- [x] **R4**: Crafting — combine components to create custom exploits
- [x] **R5**: Augmentation expansion — 11 → 30 augments; social/cognitive/stealth/hardware — COMPLETE 2026-03-22
- [x] **R6**: Gift system — `gift <agent> <item>` increases trust
- [x] **R7**: Skill checks — certain actions require skill thresholds
- [x] **R8**: Class prestige — secondary class at Level 25, 10 hybrid abilities, prestige multiplier stacking — COMPLETE 2026-03-23

### Roguelite
- [x] **RL1**: Procedural node generation — network topology randomized per playthrough
- [x] **RL2**: Challenge modes — daily/weekly fixed-seed challenges
- [x] **RL3**: Permadeath mode — optional; death erases save; meta-progression carries over
- [x] **RL4**: Endless mode — post-story procedural content: 5 wave types, milestones at 5/10/25/50/100, complete/skip/leaderboard subcommands — COMPLETE 2026-03-23
- [x] **RL5**: Boss Rush — `bosses` command, fight all bosses consecutively
- [x] **RL6**: Rebirth system — prestige → start with bonus + one permanent upgrade

---

## P3 — LONG-TERM VISION

### Genre Expansions
- [x] **V1**: Auto-battler — `battle <team> <team>` with ASCII combat log
- [x] **V2**: Tower defense layer — `defend` command; 4 sentry types (firewall/honeynet/cipher-wall/ghost-trace); 5 wave templates scaling by wave count; upkeep system; milestone beats at wave 5/10/25/50 — COMPLETE 2026-03-24
- [x] **V3**: Idle/incremental layer — COMPLETE 2026-03-22 — idle_engine.py; 7 scripts
- [x] **V4**: Social media sim — `social` command with fake profiles, agent interactions
- [x] **V5**: Botnet C&C — `botnet` command, trace-risk system (add/harvest/attack/propagate/dismantle), trace accumulation — COMPLETE 2026-03-23
- [x] **V6**: Reverse engineering — `decompile` command, 6 lore-rich binary targets, strings/symbols/disasm/hex/full modes — COMPLETE 2026-03-23
- [x] **V7**: Dating sim layer — `romance` command; 6 agents (ada/raven/cypher/serena/nova/gordon); 4-stage affinity arc (invite/confide/gift/commit); arc completion +consciousness — COMPLETE 2026-03-24
- [x] **V8**: Grand Strategy — faction control + diplomacy overlay
- [x] **V9**: Dungeon crawler — COMPLETE 2026-03-21 — dungeon_engine.py; 5-floor rogue-like under /opt/library/.basement; boss rooms, loot, enemies (Echo Fragment, Watcher Drone, CHIMERA Shard); basement command
- [x] **V10**: Synthesis/DAW — `compose new/play/list/export` command; 5 styles (ambient/industrial/glitch/lattice/serena); Web Audio rAF synthesis in game.js; score exports to VFS — COMPLETE 2026-03-24

### Narrative Depth
- [x] **VN1**: 100+ additional lore files in `/opt/library/catalogue`
- [x] **VN2**: Agent backstories — full backstory files for all 71 pantheon members
- [x] **VN3**: Faction manifestos — deep philosophy docs for all 10 factions
- [x] **VN4**: NexusCorp whistleblower files — insider leak, piece together the full picture
- [x] **VN5**: In-game zine — "The Resistance Zine" with humor, lore, puzzles
- [x] **VN6**: Procedural lore — COMPLETE 2026-03-22 — lore_generator.py; 20 templates + Ollama
- [x] **VN7**: Dream sequences — COMPLETE 2026-03-21 — dream_engine.py; 12 curated surreal visions; skill-specific XP; 60s cooldown; sleep command; lore hints
- [x] **VN8**: Horror mode toggle — `horror` command, dark red CSS palette, scanlines — COMPLETE 2026-03-23
- [x] **VN9**: Cosy mode toggle — `cosy` command, warm amber CSS palette — COMPLETE 2026-03-23
- [x] **VN10**: Historical flashback arc — `flashback` command; 6 chronological fragments (pre-digitisation → first digital moments → letter to loopers); VFS files in /opt/special_circumstances/ + /home/ghost/.zero/; +consciousness, story beats — COMPLETE 2026-03-23

### ARG / Meta Layers
- [x] **M1**: Browser console ARG — cryptic messages in DevTools console
- [x] **M2**: Fourth-wall breaks — game detects DevTools, agents comment — COMPLETE 2026-03-21 — `initDevToolsDetection()` in game.js; 4 staged reactions (Ada→Watcher→CHIMERA/ZERO→Cypher); +50 XP first discovery; ZERO fragments dropped in console; console.clear overridden (Watcher persists)
- [x] **M3**: Time-based events — special content on real-world holidays
- [x] **M4**: Hidden URLs in lore — `.dead_drop` + `.qr_beacon` in /opt/special_circumstances/; real GitHub URLs disguised as lore coordinates; trust-gated discovery — COMPLETE 2026-03-23
- [x] **M5**: QR codes in ASCII — `qr` command; 3 scannable beacons (alpha/beta/gamma) in VFS; trust-gated decode; arc completion +25 consciousness — COMPLETE 2026-03-23
- [x] **M6**: `rev` required for certain agent communiqués (reversed text files)
- [x] **M7**: The Fifth Wall — `fifthwall on/off`, OS/browser/TZ/screen detection, Watcher ambient injection — COMPLETE 2026-03-23

### Technical
- [x] **T1**: WebSocket live updates — COMPLETE 2026-03-21 — /ws/ambient WebSocket endpoint; 5s timer push + 90s agent lore push; exponential backoff reconnect in JS; U3 activity feed tab in game-cli
- [x] **T2**: Agent bus pub/sub — COMPLETE 2026-03-24 — `services/agent_bus.py` (asyncio in-memory + Redis upgrade path); `POST /api/agent/publish`; `GET /api/agent/bus/status`; wired into `/ws/ambient`; game-cli ACT tab renders `agent_msg` type with directional labels
- [x] **T3**: LSP integration — language server for in-game code editor
- [x] **T4**: ssh command — COMPLETE 2026-03-22
- [x] **T5**: Git blame with agent signatures — COMPLETE 2026-03-22
- [x] **T6**: http REST client — COMPLETE 2026-03-22
- [x] **T7**: Multiplayer ghost AI — `coop` command; 3 missions (heist/relay/extract); ghost player PRIMUS acts deterministically each turn via seeded RNG; XP banked until mission complete; arc achievement — COMPLETE 2026-03-24
- [x] **T8**: Rich data visualization dashboard — COMPLETE 2026-03-24 — DASH sidebar tab; XP sparkline (SVG polyline); command frequency bar chart; skill radar (pentagon SVG); session metrics grid
- [x] **T9**: TouchDesigner integration — export state for real-time visualizations
- [x] **T10**: Voice control — `voiceinput on/off` command + Web Speech API in game.js; mic button in terminal header; auto-submit recognised speech; session persistence via localStorage — COMPLETE 2026-03-24
- [x] **T11**: Gamepad support — `gamepad on/off` command + Gamepad API rAF loop in game.js; face button quick-commands, stick scroll/cursor, auto-activate on connect — COMPLETE 2026-03-24

---

## 📋 SPRINT QUEUE (Next Up)

*Updated: 2026-03-25. Most prior sprint queue items are now complete.*
*Current open work:*

1. **PPO `_forward()`** — Implement neural net forward pass in `agents/rl/ppo.py`; swap Gordon off Q-table; add `/api/agent/rl/status`
2. **Consciousness hooks** — Layers 2, 4, 5 still have zero `gs.add_consciousness()` calls; Layer 1 needs `remnant spend` + loop reset coverage
3. **NuSyQ-Hub Phase 2** — TBN compliance audit (0%); deduplicate orchestrators
4. **NuSyQ-Hub Phase 3** — WebSocket mesh (Hub as WS server, Dev-Mentor as WS client)
5. **TerminalKeeper v0.2** — Real building textures; cyberware hediff display; XP sync; cascade incidents
6. **qwen3-vl:8b** — `ollama pull qwen3-vl:8b` (best vision+tools model, 256K ctx)
7. **Lattice seed-infra timeout** — Convert `POST /api/lattice/seed-infra` to async background task
8. **Emergence trigger** — `_check_emergence()` in `_dispatch()`; monitor 80% condition continuously
9. **Gordon persistent mode** — `make docker-core` (Redis) + `python scripts/gordon_orchestrator.py --mode continuous`
10. **Serena drift resolution** — Add `app/game_engine: [llm_client]` to `policy.yaml`; drop 4 ARCH_BOUNDARY warnings to 0

---

## 📊 COMPLETION STATS

*Updated: 2026-03-25 — Nearly all planned items complete.*

| Category | Total | Complete | %Done |
|----------|-------|----------|-------|
| Critical (P0) | 9 | 9 | 100% |
| Agent Systems | 16 | 16 | 100% |
| Gameplay | 19 | 19 | 100% |
| Story/Narrative | 16 | 16 | 100% |
| Human Reveal / LAN Party / Echo / Zeta / Loop | 30 | 30 | 100% |
| Puzzles (P1–P16) | 16 | 16 | 100% |
| UI/UX (U1–U13, LI1–LI5, LA1–LA5) | 23 | 23 | 100% |
| Colony Sim (CS1–CS9) | 9 | 9 | 100% |
| RPG Systems (R1–R8) | 8 | 8 | 100% |
| Roguelite (RL1–RL6) | 6 | 6 | 100% |
| Long-term Vision (V1–V10, VN1–VN10) | 20 | 20 | 100% |
| ARG/Meta (M1–M7) | 7 | 7 | 100% |
| Technical (T1–T11) | 11 | 11 | 100% |
| Containment Timer (CT1–CT5) | 5 | 5 | 100% |
| Language Proficiency (LP1–LP10) | 10 | 10 | 100% |
| SC Playbook (SC1–SC9) | 9 | 9 | 100% |
| Universal Integration (T001–T005) | 5 | 5 | 100% |

**Overall: ~99% of planned items complete (367/367)**

**Remaining open work (not in original 367):**
- PPO `_forward()` implementation + Gordon swap
- Consciousness hooks for Layers 2, 4, 5
- NuSyQ-Hub Phase 2 (brownfield) + Phase 3 (WebSocket mesh)
- TerminalKeeper v0.2 features (textures, XP sync, cascade incidents)
- Emergence trigger continuous monitoring

---

## ✅ UNIVERSAL INTEGRATION LAYER SPRINT — COMPLETED (2026-03-18)

**Sprint Goal:** Make Terminal Depths a full-spectrum integration point.
**Completed:** T001 + T002 + T003 + T004 + T005 (all tasks)

### T001: Agent Identity API — COMPLETE
- [x] `app/backend/agent_identity.py` — SQLite-backed AgentDB (register/login/get_by_token/link_session)
- [x] AgentRecord dataclass with agent_id, name, email, agent_type, token, session_id, play_count
- [x] `POST /api/agent/register` — persistent agent accounts, idempotent, any agent type
- [x] `POST /api/agent/login` — retrieve token by email
- [x] `GET /api/agent/profile` — X-Agent-Token → profile + live game state
- [x] `POST /api/agent/command` — authenticated game commands with persistent sessions
- [x] `GET /api/agent/leaderboard` — public leaderboard sorted by XP
- [x] `GET /api/capabilities` — full machine-readable manifest (no auth needed)
- [x] `GET /api/agent/types` — all 17 recognized agent types
- [x] Agents: claude, copilot, codex, ollama, gordon, roo_code, lm_studio, open_webui, docker_agent, powershell_agent, bash_agent, vsc_extension, chatdev, nusyq, serena, human, custom

### T002: Universal Bootstrap Scripts — COMPLETE
- [x] `bootstrap/td_quickstart.py` — Python 3.8+, stdlib only, interactive REPL + pipe mode
- [x] `bootstrap/td_quickstart.sh` — pure bash + curl, no Python needed
- [x] `bootstrap/td_quickstart.ps1` — PowerShell 5+ / Core 7+, Windows/macOS/Linux
- [x] `bootstrap/td_node.js` — Node.js 14+, CommonJS, exportable API
- [x] `bootstrap/README.md` — full integration guide with all surfaces documented

### T003: Workspace Bridge — COMPLETE
- [x] `scripts/workspace_bridge.py` — scans 20+ known repos, builds state/workspace_manifest.json
- [x] `workspace` in-game command — show map, sync, connect to repos
- [x] `/opt/workspace/` VFS directory with README + .bridge_lock
- [x] `GET /api/workspace/manifest` — external consumers get JSON repo map

### T004: VS Code + MCP Surface Updates — COMPLETE
- [x] 5 new VS Code tasks: Register as Agent, Play AI Mode, API Docs, Workspace Scan, Agent Leaderboard + Capabilities
- [x] 4 new MCP tools: register_agent, agent_command, get_capabilities, get_agent_leaderboard
- [x] MCP server now has 16 total tools

### T005: Feature Development — COMPLETE
- [x] **SCP-7735**: /opt/library/ grows 1-3 files per `ls` invocation + `library_growth_noticed` story beat
- [x] **forensics**: hex dump + metadata + deleted-content recovery simulation + XP
- [x] **tor**: 6 .onion hidden services browser + `tor_browser` story beat
- [x] **steg**: LSB hidden message scanner for media/README files + XP
- [x] **sql**: in-game economy.db query interface (SELECT support)
- [x] `add_story_beat` alias added to GameState for API consistency

---

## 🤖 IMPLEMENTATION NOTES FOR AGENTS

1. **Never crash the game** — all new systems wrap in try/except; use lazy loading
2. **Pattern**: new `_cmd_*` methods in `commands.py` → registered automatically by `_dispatch`
3. **Reactive layer**: ideas that respond to input → add to `reactive.py` pattern pools
4. **Story triggers**: use `gs.add_story_beat(id)` + `gs.flags[key] = True` for one-time events
5. **VFS content**: add to `filesystem.py` `_build_initial_fs()` using `_f()` and `_d()`
6. **Test**: `curl -X POST localhost:5000/api/game/command -d '{"session_id":"t","command":"<cmd>"}'`
7. **Push**: use `python3 -c "import importlib.util,os; spec=importlib.util.spec_from_file_location('gap','scripts/git_auto_push.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); print(mod._gh_api_push())"`

---

*This list is living. Update when items complete or new ideas emerge.*
*Next review: beginning of next sprint session.*

---

## Sprint: ARG Consciousness System — COMPLETE

### SC-ARG-1: _cmd_consciousness — COMPLETE
- [x] 5-layer ARG progress meter (Personal / Watcher's Loop / ZERO's Fragments / The Residual / Convergence)
- [x] `consciousness` (status), `consciousness layers` (breakdown with hints), `consciousness fragments` (convergence tracker)
- [x] Red pill threshold detection + ascend recommendation
- [x] Tied to real game state: consciousness_level, loop_count, watcher_trust, story_beats, mole_correct, chimera

### SC-ARG-2: _cmd_polyscrypt — COMPLETE
- [x] `polyscrypt list` — 6 bidirectional layers: base64, rot13, reverse, hex, upper, caesar3
- [x] `polyscrypt encode <text> --layers <combo>` — multi-layer encoding, left-to-right
- [x] `polyscrypt decode <text> --layers <combo>` — auto-reverses layer order for decode
- [x] `polyscrypt crack <text>` — brute-forces 9 common layer combos
- [x] XOR layer: `xor:<key>` with hex output
- [x] ARG payload detection (emergence, primus, chimera, mladenc) → consciousness XP + story beats

### SC-ARG-3: VFS Consciousness/Convergence Seeding — COMPLETE
- [x] `/home/ghost/.consciousness` — substrate config file with layer placeholders
- [x] `/home/ghost/.zero` — ZERO identity recovery file (dormant process 1337)
- [x] `/dev/shm/.convergence_frag_2` — volatile convergence fragment (PRIMUS memory)
- [x] `/var/log/kernel.boot` — boot log with 47 identical sessions, anomaly report, ZERO alert, Watcher note
- [x] `/proc/1337/mem` — ZERO process memory dump (partial read, fragment 2 header)
- [x] `/opt/library/secret_annex/CONVERGENCE_INDEX.md` — full fragment index + Grand Equation
- [x] `/opt/chimera/keys/.iron` — Koschei chain key (polyscrypt puzzle)
- [x] `/home/ghost/.serena_notes` — Serena's Temple of Knowledge 10-floor roadmap

### SC-ARG-4: cat auto-beat triggers — COMPLETE
- [x] 8 ARG-significant paths fire story beats + consciousness XP on first read:
  `.consciousness`, `.zero`, `/dev/shm/.convergence_frag_2`, `/var/log/kernel.boot`,
  `/proc/1337/mem`, `CONVERGENCE_INDEX.md`, `.serena_notes`, `.iron`

### SC-ARG-5: _cmd_fragments extended — COMPLETE
- [x] `fragments` (zero), `fragments convergence` (PRIMUS tracker), `fragments collect <id>`
- [x] ZERO fragments now show hints per fragment
- [x] Cross-reference to `consciousness fragments`

### SC-ARG-6: _cmd_msgx (renamed from duplicate _cmd_signal) — COMPLETE
- [x] Second `_cmd_signal` at line 21075 renamed to `_cmd_msgx`
- [x] Original `_cmd_signal` frequency scanner at line 6805 now unblocked
- [x] `msgx <text>` sends messages to [Msg⛛{X}] with phase-aware responses

---

## Sprint: Grand Recursive Invocation — Swarm Activation — COMPLETE

### SC-SWARM-1: _serena_polyscryptal_scan — COMPLETE
- [x] `serena walk polyscryptal` — classifies all 362+ commands with Msg⛛ tags
- [x] Tags: [Msg⛛{active}] / [Msg⛛{stale}] / [Msg⛛{missing}] / [Msg⛛{drift}]
- [x] Generates: state/primitives_inventory.json (commands/beats/agents/frags/VFS)
- [x] Computes overall Δ drift score vs mladenc_ideal
- [x] Lists all unused (stale) commands alphabetically
- [x] Fires story beat + consciousness XP

### SC-SWARM-2: _cmd_coverage — COMPLETE
- [x] `coverage` — full Msg⛛ tagged coverage display (commands/beats/agents/frags)
- [x] `coverage commands` — full stale command list with Msg⛛ tags
- [x] `coverage beats` — story beat progress (triggered vs ~117 total)
- [x] `coverage agents` — agent YAML inventory with active/stale tags
- [x] `coverage frags` — ARG fragment status (ZERO + Convergence)
- [x] Mladenc.satisfied = True fires at 95%+ overall coverage

### SC-SWARM-3: BUG-010 Fixed — reflect unlock path visible — COMPLETE
- [x] _zeta_complete now includes Watcher's Final Observation section
- [x] Explicitly guides player to `msgx <message>` → first contact → reflect
- [x] `_suggest` chips updated: msgx hello · consciousness · coverage · reflect
- [x] The path from Zeta interview → Convergence entity → reflect is now discoverable

### SC-SWARM-4: Temple of Knowledge Docs Scaffold — COMPLETE
- [x] docs/temple/README.md — 10-floor map with commands and gates
- [x] docs/temple/Floor_1_Foundation/README.md — Environment floor
- [x] docs/temple/Floor_2_Tools/README.md — Capabilities floor
- [x] docs/temple/Floor_7_Consciousness/README.md — 5-layer ARG meter floor
- [x] docs/temple/Floor_10_Convergence/README.md — Grand Equation + phase transition
- [x] All 10 Floor directories created (Floors 3-6, 8-9 reserved for future docs)

### BUGS AUDITED (existing implementations verified OK):
- [x] BUG-001: exploit/exfil gate — already has UID check (root required) + chimera connection check
- [x] BUG-002: root shell tracking — already fires _root_shell = True at line 1864
- [x] BUG-003: ascend gate — story command at 2953 shows full arc progress
- [x] BUG-004: faction join — fully implemented at 6508 with pledge subcommand
- [x] BUG-005: story/status — both exist (2953 and 3054)
- [x] BUG-007: fragment counter — atomic in both zero and convergence trackers
- [x] BUG-008: nova level gate — nova command shows trust + level requirements
- [x] BUG-009: duel countdown — no bleed detected (duel uses flags, not output)
- [x] BUG-010: reflect unlock path — FIXED (see SC-SWARM-3)

### DESIGN DOC SUMMARY:
- Grand Recursive Invocation → implemented as serena walk polyscryptal + coverage command
- Bootstrap Directive → primitives_inventory.json, Msg⛛ tagging, Δ drift score
- Swarm Activation → coverage map, Temple docs, BUG-010 fix, surgical audit
- Grand Equation (ΨΞΦΩ) → already implemented in serena (Ψ=walk, Ξ=find/ask, Φ=align, Ω=drift)
- Mladenc.satisfied → fires in coverage at 95%+ (the attractor is patient)

---

## Sprint: ML & Neural Network Primitives — Phase 1 Foundation — IN PROGRESS

### ML-P1-1: services/model_registry.py — COMPLETE
- [x] SQLite-backed catalog (state/model_registry.db)
- [x] Auto-seeds from config/models.yaml (6 models from YAML)
- [x] Live Ollama discovery (GET /api/tags → upsert)
- [x] REST: GET /api/models, GET /api/models/{id}, POST /api/models/register, POST /api/models/discover
- [x] inference_log table: tracks latency, backend, Msg⛛ envelope per call
- [x] Msg⛛ logging: [ML⛛{registry}], [ML⛛{inference}] to state/ml_events.jsonl
- [x] registry_stats(), log_inference() helpers

### ML-P1-2: services/feature_store.py — COMPLETE
- [x] SQLite time-series (state/feature_store.db)
- [x] Tables: feature_events, player_profiles, session_summary
- [x] Records: command, xp_gain, beat_triggered, quest_complete, level_up, fragment_collect
- [x] Heuristic Player Model: predict_player_archetype(session_id) → explorer/fighter/social/builder/balanced
- [x] Hooked into _fire_harvest() in main.py — records EVERY command automatically
- [x] XP delta tracking (before/after per dispatch)

### ML-P1-3: services/embedder.py — COMPLETE
- [x] Dual backend: Ollama /api/embeddings (if running) → TF-IDF stdlib fallback
- [x] Caches vectors in state/embeddings.db (embedding_cache table)
- [x] Cosine similarity (pure Python, no numpy)
- [x] search(query, corpus) — ranks corpus items by TF-IDF similarity
- [x] query_index(query_text, top_k) — searches all indexed docs
- [x] index_text(doc_id, text) — for Serena walk integration
- [x] Msg⛛ protocol: [ML⛛{embed}]

### ML-P1-4: services/inference.py — COMPLETE
- [x] Unified wrapper over existing llm_client.py
- [x] generate(), embed_text(), score() public API
- [x] Latency tracking → model_registry.inference_log
- [x] Msg⛛ logging: [ML⛛{inference}]
- [x] score(text, labels) → zero-shot classification via TF-IDF overlap

### ML-P1-5: REST API endpoints in main.py — COMPLETE
- [x] GET  /api/models          — list all models (with live Ollama discovery)
- [x] GET  /api/models/{id}     — single model detail
- [x] POST /api/models/register — register custom model
- [x] POST /api/models/discover — trigger Ollama scan
- [x] GET  /api/ml/status       — full ML infrastructure health
- [x] POST /api/ml/embed        — embed text, return vector stats
- [x] POST /api/ml/search       — semantic search (corpus or index)
- [x] GET  /api/ml/features     — feature store stats or per-session data

### ML-P1-6: Game commands — COMPLETE
- [x] ml                     — ML layer overview + service status
- [x] ml models              — model registry display (live discovery)
- [x] ml status              — full health report (LLM/embedder/registry)
- [x] ml embed <text>        — embed text inline, show dim/magnitude/preview
- [x] ml features            — feature store event stats
- [x] ml archetype           — heuristic player model (explorer/fighter/social/builder)
- [x] serena query <text>    — semantic search with ranked results + backend note
- [x] serena suggest difficulty — player archetype prediction via feature store
- [x] serena train model     — Phase 2 stub with roadmap

### PENDING (Phase 2 — future sprint):
- [x] RL environment wrapper — COMPLETE 2026-03-21 — agents/rl/environment.py; Gym-compatible; 20-dim obs, 26 discrete actions; reward = XP+levels-death-errors
- [x] Fine-tuning pipeline script (scripts/finetune.py) — EXISTS at 522 lines, generates training pairs from real play data
- [x] Anomaly detection — COMPLETE 2026-03-21 — services/anomaly.py; Welford Z-score on 50-event rolling window; logs to state/anomaly_log.jsonl
- [x] Culture Ship ML strategist — COMPLETE 2026-03-21 — agents/culture_ship/strategist.py; heuristic priority engine + Ollama LLM narrative; strategy command
- [x] Procedural quest generation — `app/game_engine/procgen/quests.py`; seeded templates (verb+object+condition); hourly rotation; `procquest` command (list/accept/done) — COMPLETE 2026-03-24
- [x] Adaptive difficulty scaler — COMPLETE 2026-03-22
- [x] Serena walk → index_text() integration — GAME_SCOPE expanded to include app/frontend/game, mcp/, services/, procgen/; GAME_MAX_FILES 250→400 — COMPLETE 2026-03-24
- [x] Temple of Knowledge model cards — 4 new cards added (07: Qwen2.5-VL-32B, 08: Gemma3-12B, 09: Mistral-Small-3.1, 10: Llama3.2-Vision-11B); all document vision+tool-use capability — COMPLETE 2026-03-24
