# Terminal Depths — TODO

Updated: 2026-03-24

## URGENT — VS Code Phase Prerequisites (do these first)

- [x] Fix .pyc epoch-zero stale bytecode bug (auto-purge added to _startup())
- [x] Fix `restart tutorial` / `start tutorial` / all case variants
- [x] Case-insensitive command dispatch
- [ ] Verify `python -B -m cli.devmentor serve --port 7337` works cleanly on fresh clone
- [ ] Add `PYTHONDONTWRITEBYTECODE=1` to devmentor.sh / devmentor.ps1 launchers
- [ ] Test bootstrap.ps1 on fresh Windows clone (VS Code)
- [ ] RimWorld mod dotnet build task in .vscode/tasks.json (needs Assembly-CSharp.dll path)

## HIGH — Gameplay Gaps

- [ ] `ascend` story conclusion — currently a stub; write actual ending cutscene
- [ ] Ada dialogue variety — post-intro `talk ada` responses are repetitive (need 10+)
- [ ] Nova dialogue tree — currently only 3 responses, needs expansion
- [ ] `duel surrender` subcommand + duel timeout after 10 commands
- [ ] Story beat `serena_awakened` — triggers Serena L4 trust (Convergence level)

## MEDIUM — Polish

- [ ] Fix Serena drift score — always returns 0.0 (bug in serena_analytics.py diff detector)
- [ ] Challenge validation too strict — normalize whitespace/case before comparing answers
- [ ] `leaderboard` command — placeholder text, needs real session data connection
- [ ] Command history persistence across browser refresh (localStorage)
- [ ] Sound effects — Web Audio ambient works, SFX missing (key-click, hack-success)
- [ ] Optimize startup .pyc purge — limit rglob scope to `app/` only

## LOW — Infrastructure / NuSyQ

- [ ] RimWorld HediffDefs Part Tags — add `<installedPartDef>` for surgery UI
- [ ] RimWorld Strings XML — `Languages/English/Strings/Strings_TK.xml`
- [ ] NuSyQ chronicle reader UI — `/api/chronicle` endpoint + browser panel
- [ ] Godot integration — populate `docs/godot/` with real tutorial content
- [ ] Mobile layout — media queries below 600px
- [ ] SimulatedVerse integration — `/api/nubridge/status` should reflect SimulatedVerse state

## Priority 1 — Core Gameplay (Critical Path)

- [x] Core terminal commands (ls, cat, grep, find, ps, etc.)
- [x] Virtual filesystem with realistic content
- [x] Privilege escalation path (ghost → root via sudo find)
- [x] Story beats (CHIMERA, Nexus Corp, ADA, The Watcher)
- [x] NPC system (Ada, Cypher)
- [x] CTF challenges
- [x] Tab completion
- [x] Pipelines and redirection
- [x] XP + skills system
- [x] Achievements

## Priority 2 — Self-Building System

- [x] Scripting API (ns object, 13 methods)
- [x] Bundled scripts (hello, recon, exploit, test_suite, generate, loot_collector)
- [x] Developer mode (devmode on / inspect / spawn / teleport / generate / test)
- [x] External agent REST API (/api/script/*, /api/agent/info)
- [x] 15/15 automated tests passing
- [x] Orchestrator agent
- [x] Player agent (autonomous game player)
- [x] Tester agent
- [x] Content generator agent
- [x] Implementer/analyzer agent
- [x] Documenter agent (agents/documenter.py — man pages, lore pages, dev docs)
- [x] Task dispatcher (scripts/dispatch_task.py — routes tasks to agents)
- [x] Validation suite (scripts/validate_all.py — CI-style: syntax, API, agents, LLM, memory)
- [x] Self-improvement scanner (scripts/self_improve.py — code analysis, TODO extraction, task generation)
- [x] Initial man pages: ls, cat, grep, find, ps, nmap, ssh, sudo, exploit, scan, hack, signal, faction, trust, man

## Priority 3 — Game Depth

- [ ] Tutorial: expand to 42 steps (currently ~10)
- [ ] Story: expand to 30+ beats (currently ~15)
- [ ] Challenge count: reach 100+ (currently ~35)
- [ ] ARG layer: hidden files, puzzle chain, meta-revelation
- [ ] The Watcher: `/dev/.watcher` interactive element
- [ ] LLM-powered NPC responses (Ada + Cypher) — OpenAI integration ready
- [ ] `ascend` command: full story conclusion
- [ ] Multiplayer hint system (nodes leave messages)

## Priority 4 — Polish and DX

- [x] CRT visual effects (vignette, scan lines, glitch)
- [x] Pulse-red root prompt
- [x] Toast notifications for challenge completions
- [ ] Sound effects (optional: terminal beep, hack success)
- [ ] Mobile-responsive terminal
- [ ] Dark/light theme toggle
- [ ] Command history persistence across sessions
- [ ] User accounts / leaderboard

## Priority 5 — Infrastructure

- [x] Session persistence (sessions/<uuid>.json)
- [x] Zero-token ops engine
- [x] CHUG engine for autonomous improvement
- [x] Playtest automation (playtest.py)
- [x] Agent framework (agents/)
- [x] Knowledge base (knowledge/)
- [x] dev.sh with uvicorn --reload
- [ ] pytest integration tests (test_*.py)
- [ ] GitHub Actions CI
- [ ] Docker container for portability
- [ ] Deployment to production

## Priority 6 — Educational Depth

- [ ] Man pages for all commands (man <cmd>)
- [ ] Interactive tutorials for each skill category
- [ ] Code challenges (write a script to solve X)
- [ ] Networking simulation (real traceroute, ping behavior)
- [ ] Assembly/reverse engineering challenges
- [ ] Binary exploitation (buffer overflow simulation)
- [ ] Web security (XSS, SQLi simulation in game)

## Known Bugs / Rough Edges

- [ ] `generate lore` test check uses wrong expect string (minor)
- [ ] `teleport` test check uses wrong type (minor — actual behavior correct)
- [ ] `curl` / `wget` could fetch from game-internal URLs
- [ ] `ssh` to game nodes doesn't persist filesystem state
- [ ] Very long outputs may overflow terminal scroll buffer

## Metrics

| Metric           | Current | Target |
|------------------|---------|--------|
| Commands         | 100+    | 150+   |
| Challenges       | 35      | 100+   |
| Tutorial steps   | ~10     | 42     |
| Story beats      | ~15     | 30+    |
| Tests passing    | 15/15   | 50/50  |
| Test coverage    | ~40%    | 80%+   |
| ns API methods   | 13      | 20+    |
