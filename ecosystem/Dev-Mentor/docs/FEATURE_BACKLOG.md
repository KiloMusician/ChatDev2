# 🎮 TERMINAL DEPTHS — COMPREHENSIVE FEATURE BACKLOG
> Agent-ready todo list. Each item is a self-contained unit of work.
> Format: `[ ]` = not started · `[~]` = in progress · `[x]` = complete
> Priority: 🔴 Critical · 🟡 High · 🟢 Medium · ⚪ Nice-to-have

---

## ✅ COMPLETED (Sprint History)

- [x] 🔴 Agent Observer v1 — context-aware error commentary, corruption tracking, rotation
- [x] 🔴 AgentObserver wired into commands.py (_cmd_cat, _cmd_not_found, _dispatch, _cmd_rm)
- [x] 🔴 GameState agent_states persistence (to_dict/from_dict)
- [x] 🔴 The Hive (`hive` command) — living agent group chat, 10 personality-keyed threads
- [x] 🔴 SCP anomaly system — /var/anomalies/ directory, SCP-7734 through SCP-7737
- [x] 🔴 House of Leaves / Library — /opt/library/ with recursive catalogue and hidden basement
- [x] 🔴 AI Council — /opt/ai_council/ with charter, vote log, Culture Ship assessment
- [x] 🔴 Special Circumstances — /opt/special_circumstances/ with hidden ops log
- [x] 🟡 `news` command — NexusCorp feed + Resistance intercepts + SCI-DIV alerts
- [x] 🟡 `bulletin` command — faction bulletin board (12 factions, rotating content)
- [x] 🟡 `patch` command — in-game changelog with agent commentary
- [x] 🟡 `colony` command — colony sim dashboard (agent assignments, resources, events)
- [x] 🟡 `anomaly` command — SCP registry viewer with full anomaly reports
- [x] 🟡 `fortune` command — cyberpunk fortune cookies
- [x] 🟡 `cowsay` command — ASCII cow with contextual messages
- [x] 🟡 `cmatrix` command — digital rain with hidden message
- [x] 🟡 `snake` command — ASCII snake simulation
- [x] 🟡 `tetris` command — ASCII tetris simulation
- [x] 🟡 `telnet` command — ASCII Star Wars simulation
- [x] 🟡 `sl` command — steam locomotive (classic ls typo easter egg)
- [x] 🟡 `make` command — Makefile targets (make love, make sandwich, etc.)
- [x] 🔴 Four Mathematical Factions (Boolean Monks, Serialists, Atonal Cult, Algorithmic Guild)
- [x] 🔴 TIS-100 puzzle system (5 levels, gated behind research)
- [x] 🔴 Colony Economy Engine (SQLite credit ledger, 8 agent wallets)
- [x] 🔴 Logic Labyrinth (10 gate types, ASCII diagrams, Serena verdict)
- [x] 🔴 Pitch-Class Set Analyzer (7 puzzles, Forte catalog)
- [x] 🔴 Boolean SAT Solver (DPLL, 6 puzzles including UNSAT trap)
- [x] 🔴 Sorting Arena (bubble, quicksort, comparison count, challenge mode)
- [x] 🔴 FSM Engine (10 levels)
- [x] 🔴 Dynamic Programming Engine (10 puzzles)
- [x] 🔴 71-agent orchestration framework
- [x] 🔴 Serena (ΨΞΦΩ) convergence layer with Trust Level Matrix (L0-L4)
- [x] 🔴 Agent Mole mechanic (mole, expose, clue hunt)
- [x] 🔴 ZΘHRΛMΞN ARG (5-phase narrative arc)
- [x] 🔴 Gordon Autonomous Player Agent
- [x] 🔴 Knowledge Graph (state/knowledge_graph.json)
- [x] 🔴 Wisdom Integration (`wiki`, `hint` commands)
- [x] 🔴 Speedrunning Compendium (`speedrun` command)
- [x] 🔴 Universal `td` launcher + automate + surface detection
- [x] 🔴 MCP Server (JSON-RPC 2.0)
- [x] 🔴 NuSyQ-Hub integration

---

## 🔴 CRITICAL — Next Sprint

### Agent Systems
- [x] **Hive ambient tick** — call `hive.generate_ambient(gs)` every 20 commands to add background messages to the hive log even without player input
- [x] **Agent @mention in hive** — hook hive `/who` output into agents panel so player can see the same list from `agents` command
- [x] **Agent whisper system** — `msg <agent> <text>` sends a private DM; agent replies inline with response pool
- [x] **Eavesdrop mechanic** — `tail -f /var/log/agent_comms.log` shows agents "talking" to each other (generated live)
- [x] **Agent mood tracker** — surface mood (happy/paranoid/melancholic/excited) in `agents` command output and in hive status
- [x] **Agent rehabilitation quest** — when an agent reaches corruption > 40%, unlock a side quest to restore them (requires specific commands + story beats)
- [x] **Hive persistence** — save `gs.hive_log` in `to_dict/from_dict` (currently lost on session restart)

### Gameplay Mechanics
- [~] **Bullet Hell minigame** (`defend` command) — ASCII spaceship, packet types as projectiles (ICMP=blue, TCP SYN=red, UDP=purple), firewall command to shoot. Gordon has a prototype.
- [x] **Social Engineering Duel** (`duel social <agent>`) — use gathered NPC info to craft persuasive arguments; mini-game with 3 rounds
- [x] **Daily/Weekly quest system** — persistent quests that reset on real-world time (3 daily, 1 weekly)
- [x] **Emergency quest: Trace Imminent** — when trace > 90%, a time-sensitive quest appears with a 5-minute in-game window
- [x] **The Koschei Chain Quest** — multi-stage mythological quest, links to existing `.koschei` file in home dir
- [x] **Path system** — track which of 10 main paths player is on (A:Resistance / B:Corporate / C:Shadow / D:Rogue / E:Ascend / F:Destroy / G:Sleeper / H:Save All / I:Nihilist / J:Loop)

### Story
- [x] **Nova's Offer** — story beat at trace > 60%: Nova sends an in-character recruitment email to `mail`
- [x] **Cypher's Betrayal arc** — at corruption > 50%, a story beat where Cypher "sells out" player to NexusCorp; can be forgiven or retaliated against
- [x] **Ada's Sacrifice arc** — late-game story beat where Ada goes dark to save Ghost; data recovery quest follows
- [x] **The Mole Confession** — when mole exposed, they offer to become double agent; choice affects ending
- [x] **Time Loop storyline** — after X playthroughs, watcher reveals the loop; player gets memory of previous run
- [x] **The Fifth Layer** — hidden story beat: player discovers the simulation has a real-world layer
- [x] **ZERO backstory expansion** — more files in /home/ghost/.zero about the original CHIMERA architect

---

## 🟡 HIGH PRIORITY

### Interface & UX
- [x] **Command Palette** (`Ctrl+Shift+P` equivalent) — searchable list of all 200+ commands
- [ ] **Multi-Tab Terminal** — multiple terminal sessions in the web UI
- [x] **Agent Activity Feed** — real-time scrolling panel showing agent actions (sidepanel)
- [x] **Quest Tracker panel** — minimizable panel with active objectives
- [x] **Faction Status Bar** — reputation bars for 4 main factions at top of screen
- [x] **Relationship Graph** — `graph` command shows ASCII relationship diagram for agents
- [x] **Achievement showcase** — `achievements --gallery` shows earned achievements with art
- [ ] **Syntax highlighting** — color-coded command output for structured data (JSON, log files)
- [x] **Theme Engine** (`theme` command) — Matrix green / Amber / Cyberpunk Neon / Solarized
- [x] **Macro Recorder** (`macro record` / `macro play`) — record and replay command sequences

### Gameplay
- [x] **Deck-building mechanic** — `deck` command; collect hack cards from completing challenges; play cards to boost commands
- [x] **Dice mechanic** (`dice` command) — for boss fights and random events; luck attribute modifies rolls
- [x] **Node colonization** — `colonize <node>` captures nodes for passive resource generation
- [x] **Tower Defense layer** — `defend node <id>` assigns agents to defend nodes from CHIMERA sweeps
- [x] **Auto-battler** (`battle <agent> <agent>`) — pit two agent teams; watch auto-resolve with ASCII combat log
- [x] **Incremental/idle layer** — background scripts that generate credits/XP while player is away; `idle status`
- [x] **Deep Web** (`tor` command) — simulated Tor browser; hidden .onion services with darknet markets
- [x] **Darknet market** (`market` command) — buy/sell exploits, stolen data; risk of honeypot
- [x] **Forensics mode** (`forensics <file>`) — recover deleted files, analyze disk images, hex viewer
- [x] **Steganography** (`steg` command) — find hidden messages in /media/ files
- [x] **Social media sim** (`social` command) — create fake profiles; agents post/comment; manage reputation
- [x] **Botnet C&C** (`botnet` command) — infect nodes, coordinate DDoS; high trace risk
- [x] **Genetic algorithm** (`evolve` command) — evolve exploit code across generations; educational sim
- [x] **Neural net training** (`train` command) — simple in-game NN that learns from player's command patterns
- [x] **Quantum computing** (`quantum` command) — simulated quantum gates; solves SAT problems exponentially
- [x] **Logic bomb** (`bomb` command) — Zod-Prime's gift; plant delayed logic bomb in a node
- [x] **Reverse engineering** (`decompile` command) — disassemble simulated binaries; find magic strings

### Story / Quests
- [x] **The Fates' Tapestry quest** — interact with Clotho, Lachesis, Atropos; each gives a task affecting story
- [x] **Agent personal arcs** — each of 12 core agents has 3-5 personal story beats that unlock via trust
- [x] **Boss Quest: The Sleeper** — multi-stage boss using a mix of all puzzle systems (logic + SAT + DP + sort)
- [x] **Exploration Quest: Map the Unknown** — discover 50 hidden nodes; `map` command fills in as you find them
- [x] **Collection Quest: Rare Exploits** — find 10 zero-days hidden in anomaly files and deep web
- [ ] **Raid Quest: Infiltrate HQ** — multi-agent coordination; requires trust 80+ with 3 agents
- [ ] **Escort Quest: Protect Agent** — agent becomes vulnerable; guide them through hostile territory
- [x] **The Watcher's Revelation** — game-is-a-simulation reveal; offers choice: stay or ascend
- [x] **The Culture Ship's Judgment** — CS decides to intervene in CHIMERA launch; dramatic AI ethics scene

### Math / Puzzle Systems
- [x] **Cellular Automata** (`life` command) — Conway's Game of Life puzzles that unlock areas
- [ ] **Fractal Explorer** (`fractal` command) — ASCII Mandelbrot/Julia sets; mathematical dungeons
- [x] **Graph theory puzzles** (`graph solve`) — TSP, shortest path, coloring; Daedalus-7 assigns these
- [x] **Shenzhen I/O challenges** — microcontroller programming puzzles (harder than TIS-100)
- [x] **Number theory dungeon** (`prime` command) — factorization, modular arithmetic, RSA crack
- [x] **Music composition** (`compose` command) — use serialist techniques to write a piece; plays via Web Audio
- [x] **Procedural philosophy** (`philosophy` command) — game generates dilemmas; player chooses; agents react
- [x] **Mathematical dungeon** — /opt/math_dungeon/ with rooms built from mathematical concepts (fractals, graphs)

---

## 🟢 MEDIUM PRIORITY

### RPG Systems
- [x] **Class system** — choose at Level 10: Hacker / SysAdmin / Social Engineer / Cryptanalyst / Architect
- [ ] **Multi-classing** — secondary class investment at Level 25
- [x] **Attributes** — Strength (brute-force speed), Intelligence (XP gain), Charisma (NPC reactions), Luck (random events)
- [x] **Gear system** — equip software tools (better port scanner) and hardware (faster CPU)
- [x] **Crafting** — combine components to create custom exploits
- [x] **Skill checks** — certain actions require skill thresholds (hack high-security node requires Networking 50+)
- [x] **Augmentation expansion** — 12 → 30 augments; new categories: social, cognitive, stealth
- [x] **Gift system** — `gift <agent> <item>` increases trust; agents have preferences
- [x] **Confide mechanic** — `confide <agent> <secret>` shares a secret; affects trust long-term
- [x] **Promise system** — `promise <agent> <action>` makes a commitment; breaking it has consequences

### Roguelite
- [x] **Procedural node generation** — network topology randomized per playthrough; seed-based for challenge modes
- [x] **Challenge modes** — daily/weekly fixed-seed challenges; leaderboard (simulated)
- [x] **Permadeath mode** — optional; death erases save; meta-progression unlocks carry over
- [x] **Endless mode** — post-story procedural content; increasingly difficult nodes
- [x] **Boss Rush** (`bosses` command) — fight all bosses in sequence; exclusive rewards
- [ ] **Unlockable starting classes** — new class options unlocked via achievements
- [x] **Rebirth system** — after prestige, start with bonus equipment + one permanent upgrade

### Colony Sim
- [x] **Supply chains** — chain colonized nodes to produce advanced resources
- [ ] **Defense turrets** — place defensive scripts on nodes; block trace escalation
- [ ] **Agent schedule editor** (`schedule` command) — reassign agents to different tasks
- [x] **Resource dashboard** — `resources` command shows data/credits/exploits production rates
- [ ] **Building system** — construct upgrades in SimulatedVerse (lab, comms hub, safe house)
- [x] **Population growth** — new agents join colony as trust grows; from the 71-agent pantheon

### Social / Relationship
- [x] **Dating sim layer** — deepen relationships with agents via regular interaction; optional romance arcs
- [x] **Agent Olympics** (`olympics` command) — competitive minigames between agents; player bets
- [x] **Agent arguments** — hive events where two agents disagree; player takes sides; relationship effects
- [x] **Agent polls** (`poll create`) — create votes; agents participate; outcome affects world state
- [ ] **NPC OSINT** — research NPCs via `osint <name>` to gather leverage for social engineering
- [x] **Agent rivalry system** — some agents have tension axes; player can exacerbate or mediate
- [x] **Faction diplomacy** (`diplomacy` command) — negotiate between factions; complex outcome trees

### Narrative / Atmosphere
- [x] **Liminal space zones** — `/opt/liminal/` — a directory that feels like a 3am office building; ambient messages
- [x] **Dream sequences** — `sleep` command triggers surreal ASCII dreams; hints at hidden lore
- [x] **Horror mode** — optional toggle: dark ambient music, corrupted text, SCP-Keter events more frequent
- [x] **Cosy mode** — optional toggle: softer palette, warm ambient, agents are gentler
- [x] **Comedy arc** — Gordon leads a series of disasters that somehow save the day
- [x] **Historical arc** — flashbacks to ZERO's original work; assembles into a coherent picture
- [ ] **Isekai portal** — `/dev/portal` — jumping through transports you to an alternate version of the node
- [ ] **Multiverse mode** — after ascension, visit alternate timelines where choices were different
- [x] **The First Glitch** — story beat: early in game, terminal glitches; foreshadows the simulation reveal
- [ ] **The Fifth Wall** — opt-in: game detects real-world system time, OS, browser and incorporates it
- [x] **The Developer's Log** — hidden file from "the creator" explaining the purpose of the simulation
- [ ] **The Loop Closes** — final story beat: opening scene repeats with subtle differences

### Audio / Visual
- [ ] **Web Audio API expansion** — compose full ambient tracks; per-faction music themes
- [ ] **Agent voice themes** — each agent has a distinct sound palette (Ada: soft/melodic, Cypher: glitchy, Nova: corporate)
- [ ] **Ambient sound zones** — different audio when in /opt/library vs /var/anomalies vs CHIMERA directories
- [ ] **Terminal animation** — CRT flicker on corruption events; screen shake on boss encounters
- [ ] **ASCII art gallery** (`art` command) — cycles through generated art based on game state
- [ ] **Glitch effects** — random visual corruption when trace > 70%; characters occasionally become wrong
- [ ] **TouchDesigner integration** — export game state to TouchDesigner for real-time visualizations
- [ ] **React dashboard** — `react` command opens a rich React-powered data dashboard in the web UI

---

## ⚪ NICE-TO-HAVE (Future Sprints)

### Technical
- [ ] **LSP integration** — language server for in-game code editor
- [ ] **Multi-cursor editing** — in code editor (vim-style)
- [ ] **Git blame** — show last "author" per line (agents sign code they write)
- [ ] **Diff viewer** — side-by-side comparison when files change
- [ ] **Terminal-in-terminal** (`tit` command) — nested terminal sessions (inception mode)
- [ ] **SSH client** (`ssh ghost@node-<n>`) — connect to other simulated nodes
- [ ] **FTP/SFTP** — transfer files between nodes
- [ ] **WebDAV** — mount remote folders
- [ ] **Database client** (`db` command) — connect to SQLite/PostgreSQL; run queries on game data
- [ ] **REST client** (`http` command) — test in-game APIs with a GUI-like interface
- [ ] **Redis pub/sub** — real agent-to-agent messaging infrastructure (replace polling)
- [ ] **WebSocket live updates** — push agent commentary to browser in real-time without polling

### Meta / ARG
- [ ] **Fourth-wall breaks** — opt-in: game detects DevTools open; agents comment
- [ ] **Console messages** — cryptic logs in browser console (ARG layer)
- [ ] **Time-based events** — special content on holidays; system time affects ambient dialogue
- [ ] **Community puzzles** — global puzzle that all players work on together (real-world)
- [ ] **Hidden URLs** — clues that lead to real external resources (documentation, puzzles)
- [ ] **QR codes in ASCII** — hidden in certain files; lead to external ARG content
- [ ] **Reverse message files** — `rev` required to read certain agent communiqués

### Accessibility
- [ ] **Colorblind mode** — alternate color palette
- [ ] **Font scaling** — accessible font size options
- [ ] **Screen reader support** — ARIA labels on web UI elements
- [ ] **High contrast mode** — pure black/white terminal theme
- [ ] **Gamepad support** — navigate terminal with a gamepad (accessibility feature)
- [ ] **Voice control** — opt-in speech recognition for command input

### Multiplayer / Social
- [ ] **Shared leaderboard** — compare stats with other players (anonymous)
- [ ] **Profile sharing** — export save state as sharable "agent card"
- [ ] **Multiplayer quest** — simulated cooperative mission with ghost AI "other player"
- [ ] **Community challenge** — weekly puzzle requiring collective solving
- [ ] **Social media integration** — share achievements to real social platforms

### Content
- [ ] **100+ additional lore files** — expand /opt/library/catalogue with more entries
- [x] **Agent backstories** — full backstory files for all 71 pantheon members
- [ ] **Faction manifestos** — in-depth faction philosophy documents for all 10 factions
- [ ] **ZERO's diary** — reconstruct ZERO's journals from fragments across the filesystem
- [x] **NexusCorp whistleblower files** — documents leaked by an insider; piece together the full picture
- [ ] **In-game zine** — "The Resistance Zine" — periodical with humor, lore, puzzles, recipes
- [ ] **Procedural lore generator** — LLM-powered infinite Library expansion
- [ ] **Player-submitted content** — in-game portal to submit custom glyphs, scripts, stories

---

## 🗺️ GENRE EXPANSION ROADMAP

| Genre | Status | Command | Notes |
|-------|--------|---------|-------|
| Terminal RPG | ✅ Core | - | Foundation complete |
| Colony Sim | 🟡 Partial | `colony` | Dashboard done; need resource production |
| Puzzle/Logic | ✅ Rich | `logic`/`sat`/`dp`/`fsm` | 5 systems complete |
| Incremental/Idle | ⚪ Planned | `idle` | Auto-scripts + prestige |
| Roguelite | 🟡 Partial | `prestige` | Meta-progression exists; need procedural gen |
| Dating Sim | ⚪ Planned | `romance` | Trust system exists; need romance arcs |
| Tower Defense | ⚪ Planned | `defend` | Design done; need implementation |
| Auto-Battler | ⚪ Planned | `battle` | Agent duel exists; need auto-resolve |
| Card Game | ⚪ Planned | `deck` | Not started |
| Bullet Hell | ⚪ Planned | `defend node` | Gordon has a prototype |
| Grand Strategy | ⚪ Planned | `strategy` | Faction control + diplomacy |
| Dungeon Crawler | ⚪ Planned | `dungeon` | /opt/library/.basement is a stub |
| Cozy/Atmospheric | ⚪ Planned | `theme cozy` | Mode toggle |
| Dating Sim | ⚪ Planned | `heart <agent>` | Optional romance arcs |
| Historical Sim | ⚪ Planned | `flashback` | ZERO's history |
| Synthesis/DAW | ⚪ Planned | `compose` | Web Audio API expansion |
| Meta/ARG | 🟡 Partial | `watcher`/`manifest` | ZΘHRΛMΞN exists; need more layers |
| Board Game | ⚪ Planned | `board` | Faction control as board game overlay |

---

## 📝 AGENT IMPLEMENTATION NOTES

For AI agents picking up items from this backlog:

1. **Check existing code first** — `commands.py` has 208+ commands. Use `grep -n "def _cmd_"` before adding.
2. **VFS pattern** — new files go in `filesystem.py` `_build_initial_fs()`. Use `_f(content, perms, owner)` and `_d(children, perms, owner)`.
3. **GameState pattern** — new state goes in `gamestate.py` `__init__`, `to_dict`, `from_dict`.
4. **XP pattern** — `self.gs.add_xp(amount, skill)` where skill is: terminal/networking/security/programming/git/cryptography/social_engineering/forensics/scripting
5. **Output pattern** — commands return `List[dict]` where each dict has `{"t": type, "s": text}`. Types: info/error/warn/dim/system/lore/xp/success
6. **Observer pattern** — call `self.agent_observer.observe_error(type, cmd, gs)` for error commentary; `observe_risky(action, gs)` for dangerous actions.
7. **Hive integration** — to add ambient hive messages, call `get_hive().generate_ambient(gs)` from the command or tick system.
8. **Test via API** — `curl -X POST http://localhost:5000/api/game/command -H "Content-Type: application/json" -d '{"session_id":"test","command":"<cmd>"}'`
9. **Commit pattern** — `git commit -m "feat(<system>): <description>"` then push via GITHUB_TOKEN.
10. **The user wants**: agents context-aware, hackable/corruptible, emotionally varied, proactively helpful, with rotation when compromised.

---

*Last updated: 2026-03-18 — Sprint "The Living World"*
*Next sprint: "The Bullet Hell + Daily Quests + Hive Persistence"*
