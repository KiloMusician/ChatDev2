# Culture-Ship Cycle Report
Generated: 2025-08-29T10:00:09.359Z
Analysis from: reports/analysis.json

## Health Summary
- **Files scanned**: 275
- **Total issues**: 375

- **placeholders**: 109
- **duplicates**: 0
- **imports**: 90
- **unreachable**: 175
- **softlocks**: 1

## Fix Summary
- **Total fixes applied**: 95
- **Dry run mode**: Yes

- **ImportFixes**: 77
- **DuplicateMerges**: 0
- **PlaceholderStubs**: 0
- **SoftlockGuards**: 1
- **BarrelFiles**: 17

## Critical Issues
### Broken Imports (90)
- **tests/smoke.mjs** → `../bootstrap/init.js`
  - Suggestion: bootstrap/init.ts
- **src/main.ts** → `./guardian/core/boot.js`
- **src/main.ts** → `./guardian/core/bus.js`
  - Suggestion: src/kpulse/bus.ts, application-services/engine/src/bus.ts, application-services/engine/scripts/bus.js
- **src/main.ts** → `./guardian/policy/load.js`
- **scripts/serialism_to_boolean.cjs** → `./src/ai-hub/chatdev_tasks/repair_placeholders`
  - Suggestion: ai-systems/chatdev-tasks/repair_placeholders.cjs
- **registry/loader.ts** → `../core/types`
  - Suggestion: global/shared/sim/types.ts
- **bootstrap/init.ts** → `../config/profiles`
  - Suggestion: global/config/profiles.ts
- **bootstrap/init.ts** → `../config/guards`
  - Suggestion: global/config/guards.ts
- **bootstrap/init.ts** → `../ui/ascii/splash`
  - Suggestion: interface-systems/component-libraries/ascii/splash.ts
- **agent/main.ts** → `./idle_tick.js`
  - Suggestion: agent/idle_tick.ts

### Potential Softlocks (1)
- **system/llm/ollama-orchestration/model-manager.js**: /\bwhile\s*\(\s*true\s*\)\s*\{/ (high)

### Placeholders (109)
- **scripts/self-heal.mjs:115**: // strategy: reexport stub
- **scripts/self-heal.mjs:117**: const stub = `// Culture-Ship: Consolidated duplicate\nexport * from "${relTarget}";\nexport { defau
- **scripts/self-heal.mjs:119**: write(abs, stub);
- **scripts/self-heal.mjs:121**: patchNote(`duplicate-merge: ${f} -> ${canonical} (reexport stub)`);
- **scripts/self-heal.mjs:127**: // -------- Healer: Stub empty placeholders ----------
- **scripts/self-heal.mjs:137**: if (item.snippet === "<EMPTY PLACEHOLDER FILE>") {
- **scripts/self-heal.mjs:145**: let stub;
- **scripts/self-heal.mjs:147**: stub = `/**
- **scripts/self-heal.mjs:148**: * Culture-Ship Placeholder Stub
- **scripts/self-heal.mjs:150**: * This stub prevents softlocks by exporting safe no-op symbols.

## System Status
- **Infrastructure-First**: ✅ Zero external tokens used
- **Culture-Ship Active**: ✅ Analysis and healing operational
- **Safety Protocol**: ✅ Dry-run default, backups created
- **Report Generated**: 2025-08-29T10:00:09.360Z