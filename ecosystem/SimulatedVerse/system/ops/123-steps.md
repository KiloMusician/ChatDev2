# 123 Steps • NuSyQ Idle / Roguelike / Builder (Replit edition)

## Foundation & Setup (Steps 1-20)

1. [ ] Create ops/triage.md with a 3-column table: {bug, placeholder, orphan}; seed with today's finds.

2. [ ] Add scripts/dev:retriage to package.json that parses logs → append to ops/triage.md.

3. [ ] Turn on ESLint/Prettier: add .eslintrc.cjs + .prettierrc with CI-breaking only on syntax.

4. [ ] Enable TypeScript strict mode; set "strict": true in tsconfig.json.

5. [ ] Add pnpm or npm lock; enforce engine in package.json to stop drift.

6. [ ] Wire Replit "Run" to pnpm dev + dotenv -e .env.local -- vite.

7. [ ] Add ./.replit + replit.nix with Node, Python, Git, JQ, ripgrep, graphviz, ffmpeg.

8. [ ] Create scripts/rg:placeholders → rg -n "(TODO|FIXME|XXX|PLACEHOLDER)" -g '!node_modules'.

9. [ ] Add scripts/rg:orphans → find imports that 404; output to ops/orphans.txt.

10. [ ] Make scripts/fix:paths to auto-rewrite moved files via a small AST transform.

11. [ ] Add src/lib/errors/graceful.ts with friendly(err) -> {title, help, action}.

12. [ ] Wrap all await in tryWrap(promise) helper; log with empathy.

13. [ ] Add global watchdog to src/lib/loops/guard.ts with step caps + backoff.

14. [ ] Create src/lib/validate/math.ts to unit-test algebraic/idle formulas.

15. [ ] Port idle algebra to src/sim/idle/core.ts with pure functions + tests.

16. [ ] Add vitest + @vitest/ui; pnpm test --ui wired to Replit "Shell".

17. [ ] Seed tests: conlang parser, OmniTag, MegaTag, RosettaStone.QGL lexer.

18. [ ] Add coverage gate at 60% (warn only) → 80% (block merges).

19. [ ] Create scripts/test:fast (unit only) & scripts/test:full (unit+e2e).

20. [ ] Add playwright basic smoke: boots UI, toggles all panes, asserts no hard errors.

## Core Libraries & Architecture (Steps 21-40)

21. [ ] Build tools/refactor/rename.ts (safe rename API) to kill typos at scale.

22. [ ] Implement src/lib/refs/indexer.ts that graphs module deps (dot output).

23. [ ] Visualize graph in docs/graphs/deps.svg (graphviz).

24. [ ] Add scripts/audit:deps to flag cycles & heavy modules > X KB.

25. [ ] Create src/lib/fs/safeLoad.ts—null-tolerant JSON/YAML loaders.

26. [ ] Sweep "placeholder" content into content/_stubs/… to stop runtime lookups.

27. [ ] Add assets/manifest.json with checksum + width/height for sprites/fonts.

28. [ ] Create ops/rename-map.yml (old→new paths) for bulk import fixing.

29. [ ] Add src/lib/i18n/keyguard.ts to detect missing strings at render.

30. [ ] Hook keyguard to dev HUD banner (non-blocking).

31. [ ] Add src/conlang/grammar.qgl (RosettaStone.QGL v1) + PEG/nearley parser.

32. [ ] src/conlang/lex.ts—supports emoji, math ops, superscripts/subscripts.

33. [ ] assets/glyphs.yml—Harmony/Trust/Forgiveness/Arrogance warning sigils.

34. [ ] src/tag/omnitag.ts—OmniTag (key:value; multi-domain); validate sets.

35. [ ] src/tag/megatag.ts—MegaTag (compositions/aliases/weights).

36. [ ] src/music/hyper_set.ts—Set theory ops (union, int, complement, Z-class).

37. [ ] src/music/serialism.ts—Row gen, inversion, retrograde, matrices.

38. [ ] src/music/tonal_map.ts—Tonnetz/Neo-Riemannian helpers.

39. [ ] src/music/analysis.ts—Music_Hyper_Set_Analysis() returns tags for UI.

40. [ ] Render "ΦΣΞ Music HUD"—tiny overlay showing live motif/tempo seeds.

## UI Panes & Game Views (Steps 41-60)

41. [ ] Create UI panes: AsciiHUD, RogueView, BuilderView, DefenseView, ExplorerView.

42. [ ] Add pane switcher: Ctrl+1..5, and a pause toggle P.

43. [ ] AsciiHUD shows stats, logs, glyphs, eco index, cascade meter.

44. [ ] RogueView ascii map, FOV/shadows, turn queue, items, stairs.

45. [ ] BuilderView base grid, blueprint ghosting, hotkeys 1–9.

46. [ ] DefenseView tower palette, range rings, pathfind lanes.

47. [ ] ExplorerView worldgen seed, biomes, points of interest, fog.

48. [ ] Global "slow-motion" slider (0.1x–2x) for sim & animations.

49. [ ] Add PauseState—freezes sim ticks; UI still navigable.

50. [ ] Save/load slot system (/saves/*.json) with checksum + schema version.

51. [ ] src/sim/idle/resources.ts—RSEV (Resources, Synergies, Events, Velocity).

52. [ ] Write balance/idle.yml with per-tier curves and soft caps.

53. [ ] Add "prestige lite" for early loop; never harms progress.

54. [ ] Implement offline calc (Δt) with cap + "welcome back" summary.

55. [ ] Add "eco-health" multiplier (protect biosphere → better yields).

56. [ ] Ensure every automation node passes ethics_test() before enabling.

57. [ ] Add sustainabilityScore(node); show badge in UI.

58. [ ] Integrate music sets as buffs: motifs ↔ production resonance.

59. [ ] Add anomaly events (benign/curious), never lethal, opt-in quests.

60. [ ] Implement friendly error toasts with recovery ("We paused the loop; here's why…").

## Game Mechanics & Systems (Steps 61-80)

61. [ ] Roguelike loot tables using OmniTag (rare sets unlock conlang pages).

62. [ ] Procedural rooms (Labyrinth/Wayward vibes) with secrets/locks/sigils.

63. [ ] Add hazards that are teachable puzzles, not damage sponges.

64. [ ] Rimworld-style jobs: hauling/building/doctoring for colonist AI.

65. [ ] Builder blueprints—queued, cancelable, refund 90% materials.

66. [ ] Dome/Core-keeper defense cycle events (timed waves, advance warning).

67. [ ] Factorio-like lanes: creeps path to "core"—player routes them.

68. [ ] Mindustry-style conveyors for in-base logistics (visual only at first).

69. [ ] Tower encyclopedia with pros/cons and eco footprint.

70. [ ] Wave designer tool in dev HUD; export JSON scenarios.

71. [ ] Worldgen: noise + plates → biomes; seed via NUSEED env.

72. [ ] Add "Peace Festival" POI that boosts morale & eco-health.

73. [ ] Add fauna allies w/ tasks (pollinate, scout, compost).

74. [ ] Pathfinding respects fauna sanctuaries; overlays visible.

75. [ ] Implement "listener stones" for inter-species dialogue prompts.

76. [ ] Add narrative "house of leaves" layers (rooms that shift, safe!).

77. [ ] Oldest House navigation model (smart shortcuts/elevators).

78. [ ] Ten-floor AI Temple: each floor = learning module + elevator controls.

79. [ ] Archive lore in content/temple/*.md with glyph references.

80. [ ] Add in-game codex search (fuzzy, tag-aware, zero-cost).

## AI & Council Systems (Steps 81-100)

81. [ ] Agents directory: agents/ (Scout, Builder, Mediator, Keeper).

82. [ ] Council orchestrator: src/ai/council.ts (round-robin + veto rules).

83. [ ] SCP containment (simulation only): src/scp/contain.ts non-violent sandbox.

84. [ ] Watchers: eccentric-class guardian ships monitor ethics/loops.

85. [ ] "Special Circumstances" playbook—humble language & reversible steps.

86. [ ] Trust system: actions earn/lose trust; restorative quests unlock.

87. [ ] Add observer/paradox.ts—detect contradictory directives; propose merge.

88. [ ] Implement quorum() for risky ops; defaults to SAFE_IDLE.

89. [ ] Cascading checklists per tier in quests/qbook.yml (bound already).

90. [ ] Add "Insight" currency for learning actions; never pay-to-win.

91. [ ] LLM-user bridge: src/ai/intermediary.ts (prompts → safe task plans).

92. [ ] "Knife-missile" analog = Guide-Drone (non-lethal, sim-safe, utility only).

93. [ ] Natural-language commands → DSL (/ai/dsl/guide_drone.dsl).

94. [ ] Sandbox the drone: no file writes unless task grants; dry-run first.

95. [ ] Provide story beats API: src/story/beats.ts to pace arcs.

96. [ ] Inventory system shared across modes (rogue/builder/defense).

97. [ ] RPG stats for colonists (traits/needs/memories); safe moods only.

98. [ ] Board-game actions log (undo/redo stack).

99. [ ] Platformer experiment panel (Noita-style physics sandbox, opt-in).

100. [ ] "Choose-your-own-adventure" adapter for plain text commands.

## Documentation & Polish (Steps 101-115)

101. [ ] docs/README.play.md quickstart: keys, panes, pause, save.

102. [ ] docs/FAQ.md—common errors & friendly fixes.

103. [ ] docs/STYLE.md—tone, humility, respectful prompts.

104. [ ] docs/TIERS.md—50-tier summary + glyphs.

105. [ ] docs/temple.md—10 floors, elevator logic, learning topics.

106. [ ] docs/oldest-house.md—navigation primitives & short paths.

107. [ ] docs/house-of-leaves.md—modular room patterns & safe illusions.

108. [ ] docs/music.md—set theory + serialism in buffs.

109. [ ] docs/ai-council.md—roles, quorums, conflicts.

110. [ ] docs/cascade.md—Cascade Event spec + triggers.

111. [ ] Add profiler overlay (FPS, tick ms, heap, GC count).

112. [ ] Memoize heavy selectors; batch renders; windowed lists.

113. [ ] Cache worldgen per chunk; reuse on reload.

114. [ ] Add save compaction; gzip saves beyond 200 KB.

115. [ ] Sprite atlas packing; lazy-load secondary panes.

## Production & Release (Steps 116-123)

116. [ ] Turn off dev sourcemaps in production preview.

117. [ ] Add feature flags via flags.yml + querystring ?flag=….

118. [ ] Set "low-power mode" toggle (reduced tick rate + fewer particles).

119. [ ] Implement cascade_event.py hook after: test-green, quest-complete, bench-done.

120. [ ] Record "spendless plan" in /ops/cascade/next.json with ranked steps.

121. [ ] Dry-run all file writes; diff in HUD; one-click apply when tokens available.

122. [ ] Snapshot "what worked" into ops/retros/DATE.md with metrics.

123. [ ] Tag release v0.x-cascadeN, push to GitHub (NuSyQ-hub), post in codex feed.

---

## Progress Tracking

- **Foundation Complete**: [ ] Steps 1-20 ✓
- **Core Architecture**: [ ] Steps 21-40 ✓  
- **Game Views**: [ ] Steps 41-60 ✓
- **Game Mechanics**: [ ] Steps 61-80 ✓
- **AI Systems**: [ ] Steps 81-100 ✓
- **Documentation**: [ ] Steps 101-115 ✓
- **Production Ready**: [ ] Steps 116-123 ✓

## Cascade Integration

This checklist is designed to work seamlessly with:
- **ΞNuSyQ Cascade Engine** (`sim/cascade/cascade_event.py`)
- **Agent Player System** (`tools/agent/play.js`)
- **Safe Runner** (`bin/safe-run`)
- **Temple/House/Oldest House** knowledge structures

Each step is:
- ✅ **Concrete and actionable**
- ✅ **Dependency-aware** (ordered by prerequisites)
- ✅ **Agent-friendly** (clear success criteria)
- ✅ **Zero-token compatible** (no external API requirements)
- ✅ **Culture Mind ethical** (life-first, benevolent)

## Usage

The autonomous agent can work through these steps systematically:

```bash
# Agent picks next step from checklist
python3 sim/cascade/cascade_event.py --plan

# Execute improvements
./bin/safe-run

# Track progress  
node tools/agent/cascade_trigger.js
```

**🌊 Let the Cascade begin - systematic progression from foundation to advanced features!**