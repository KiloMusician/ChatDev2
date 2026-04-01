# Culture-Ship Analysis Report
Generated: 2025-08-29T10:00:01.040Z
Files scanned: 275

## Summary
- **placeholders**: 109
- **duplicates**: 0
- **imports**: 90
- **unreachable**: 175
- **softlocks**: 1

## PLACEHOLDERS
- Count: 109

### Details
- **scripts/self-heal.mjs:115** // strategy: reexport stub
- **scripts/self-heal.mjs:117** const stub = `// Culture-Ship: Consolidated duplicate\nexport * from "${relTarget}";\nexport { default } from "${relTarget}";\n`;
- **scripts/self-heal.mjs:119** write(abs, stub);
- **scripts/self-heal.mjs:121** patchNote(`duplicate-merge: ${f} -> ${canonical} (reexport stub)`);
- **scripts/self-heal.mjs:127** // -------- Healer: Stub empty placeholders ----------
- **scripts/self-heal.mjs:137** if (item.snippet === "<EMPTY PLACEHOLDER FILE>") {
- **scripts/self-heal.mjs:145** let stub;
- **scripts/self-heal.mjs:147** stub = `/**
- **scripts/self-heal.mjs:148** * Culture-Ship Placeholder Stub
- **scripts/self-heal.mjs:150** * This stub prevents softlocks by exporting safe no-op symbols.
- **scripts/self-heal.mjs:156** stub = `// Culture-Ship placeholder stub for ${item.file}\nexport const ready = true;\n`;
- **scripts/self-heal.mjs:159** write(abs, stub);
- **scripts/self-heal.mjs:161** patchNote(`placeholder-stub: ${item.file}`);
- **scripts/self-heal.mjs:245** { name: "Placeholder Stubs", fn: healPlaceholders },
- **scripts/generate-docs.cjs:182** - Placeholder repair
- **scripts/collect-metrics.cjs:144** // Placeholder count
- **scripts/collect-metrics.cjs:146** const placeholders = execSync('grep -r -n -i "TODO\\|FIXME\\|STUB" --include="*.ts" --include="*.tsx" . | wc -l', { encoding: 'utf8', stdio: 'pipe' });
- **scripts/analyze.mjs:67** results.push({ file: rel(f), line: 0, snippet: "<EMPTY PLACEHOLDER FILE>" });
- **ship-console/quick-orchestrator.ts:95** // Execute the task (placeholder - would integrate with actual systems)
- **ship-console/culture-mind-interface.ts:227** // Placeholder for actual directive execution

## DUPLICATES
- Duplicate groups: 0

## IMPORTS
- Total edges: 203
- Broken imports: 90

### Broken Import Details
- **tests/smoke.mjs** → `../bootstrap/init.js` (suggest: bootstrap/init.ts)
- **src/main.ts** → `./guardian/core/boot.js` (suggest: none)
- **src/main.ts** → `./guardian/core/bus.js` (suggest: src/kpulse/bus.ts, application-services/engine/src/bus.ts, application-services/engine/scripts/bus.js)
- **src/main.ts** → `./guardian/policy/load.js` (suggest: none)
- **scripts/serialism_to_boolean.cjs** → `./src/ai-hub/chatdev_tasks/repair_placeholders` (suggest: ai-systems/chatdev-tasks/repair_placeholders.cjs)
- **registry/loader.ts** → `../core/types` (suggest: global/shared/sim/types.ts)
- **bootstrap/init.ts** → `../config/profiles` (suggest: global/config/profiles.ts)
- **bootstrap/init.ts** → `../config/guards` (suggest: global/config/guards.ts)
- **bootstrap/init.ts** → `../ui/ascii/splash` (suggest: interface-systems/component-libraries/ascii/splash.ts)
- **agent/main.ts** → `./idle_tick.js` (suggest: agent/idle_tick.ts)
- **agent/main.ts** → `./quest_runner.js` (suggest: agent/quest_runner.ts)
- **agent/main.ts** → `./codemods.js` (suggest: agent/codemods.ts)
- **agent/main.ts** → `./testharness.js` (suggest: agent/testharness.ts)
- **agent/main.ts** → `./green_commit.js` (suggest: agent/green_commit.ts)
- **agent/codemods.ts** → `../engine/state.mjs` (suggest: src/kpulse/state.ts, src/engine/state.mjs, application-services/web/src/engine/state.ts)
- **src/vscode-bridge/extension-coordinator.ts** → `../copilot-enhancement/workspace-enhancer.js` (suggest: src/copilot-enhancement/workspace-enhancer.ts)
- **src/vscode-bridge/extension-coordinator.ts** → `../ollama-orchestration/model-manager.js` (suggest: system/llm/ollama-orchestration/model-manager.ts, system/llm/ollama-orchestration/model-manager.js)
- **src/vscode-bridge/extension-coordinator.ts** → `../ai-hub/coordination-core.js` (suggest: ai-systems/orchestration/coordination-core.ts)
- **src/vscode-bridge/extension-coordinator.ts** → `../knowledge-integration/obsidian-bridge.js` (suggest: src/knowledge-integration/obsidian-bridge.ts)
- **src/scripts/trigger-evolution.ts** → `../nusyq-framework/scp-containment` (suggest: none)

### Circular Dependencies
- Found 9 cycles
  - src/nusyq-framework/index.ts → src/nusyq-framework/narrative-quantum-engine.ts → src/nusyq-framework/index.ts
  - src/nusyq-framework/self-coding-evolution.ts → src/nusyq-framework/index.ts → src/nusyq-framework/self-coding-evolution.ts
  - src/nusyq-framework/index.ts → src/nusyq-framework/quantum-feedback.ts → src/nusyq-framework/index.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.microbe.ts → application-services/web/src/views/viewManager.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.colony.ts → application-services/web/src/views/viewManager.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.city.ts → application-services/web/src/views/viewManager.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.planet.ts → application-services/web/src/views/viewManager.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.system.ts → application-services/web/src/views/viewManager.ts
  - application-services/web/src/views/viewManager.ts → application-services/web/src/views/view.space.ts → application-services/web/src/views/viewManager.ts

## UNREACHABLE
- Entry points: 98
- Unreachable files: 175

### Unreachable Files
- vite.config.ts
- test-dual-layer.js
- tailwind.config.ts
- tailwind.config.cjs
- static-server.js
- start-dev.js
- postcss.config.js
- postcss.config.cjs
- index.js
- drizzle.config.ts
- tools/taskOrganizer.mjs
- tools/simbot.mjs
- tools/run-gamification-demo.ts
- tools/repository-philosopher-stone.ts
- tools/living-repo-map.ts
- tools/gamification-cli.ts
- test/new_test.spec.ts
- tests/smoke.mjs
- scripts/ui-audit.js
- scripts/setup.mjs

## SOFTLOCKS
- Count: 1

### Details
- **system/llm/ollama-orchestration/model-manager.js** /\bwhile\s*\(\s*true\s*\)\s*\{/
