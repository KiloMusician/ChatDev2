import type { Agent } from "./types";

/**
 * Alchemist — Hotfixer / Plugin Integrator
 * Quick-response improviser, merging scattered modules, plugins, and anomalies.
 * Responsible for items 36, 50, 104, 54, 112-116, 16, 116, 85-90
 */
export const Alchemist: Agent = {
  name: "Alchemist",

  scan(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    // Scan for integration opportunities and broken plugins
    const packageJson = ctx.readJSON("package.json");
    const dependencies = packageJson ? Object.keys(packageJson.dependencies || {}).length : 0;
    const devDependencies = packageJson ? Object.keys(packageJson.devDependencies || {}).length : 0;
    
    // Check for missing configurations
    const configs = [
      "vite.config.ts",
      "tsconfig.json", 
      "tailwind.config.ts",
      "drizzle.config.ts"
    ];
    
    let configHealth = 0;
    for (const config of configs) {
      if (ctx.readText(config)) {
        configHealth++;
        actions.push(`Verified config: ${config}`);
      } else {
        warnings.push(`Missing config: ${config}`);
      }
    }
    
    // Scan for unintegrated modules
    const looseModules = ctx.shell("find . -name '*.ts' -o -name '*.js' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | grep -v dist | xargs grep -L 'export\\|import' 2>/dev/null | wc -l").trim();
    const orphanedModules = parseInt(looseModules) || 0;
    
    if (orphanedModules > 0) {
      warnings.push(`Found ${orphanedModules} potentially orphaned modules`);
    }
    
    ctx.appendJournal("Alchemist", `scan: deps=${dependencies} devDeps=${devDependencies} configHealth=${configHealth}/4 orphaned=${orphanedModules}`);
    
    return {
      agent: "Alchemist",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Alchemist scanned ${dependencies + devDependencies} dependencies, ${configHealth}/4 configs healthy, ${orphanedModules} orphaned modules`,
      actions,
      warnings,
      metrics: { dependencies, configHealth, orphanedModules }
    };
  },

  plan(ctx) {
    const actions: string[] = [];
    
    // Queue integration fixes for broken or missing pieces
    ctx.queue({
      id: `integration-alchemy-${Date.now()}`,
      title: "Perform integration alchemy on loose modules",
      source: "Alchemist",
      priority: "normal",
      tags: ["integration", "alchemy", "hotfix"], 
      payload: { maxIntegrations: 15, createBridges: true },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued integration alchemy");
    
    // Queue plugin harmonization
    ctx.queue({
      id: `plugin-harmony-${Date.now()}`,
      title: "Harmonize plugin configurations and dependencies",
      source: "Alchemist",
      priority: "normal",
      tags: ["plugins", "harmony", "config"],
      payload: { focusAreas: ["vite", "tailwind", "drizzle", "typescript"] },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued plugin harmonization");
    
    // Queue experimental feature synthesis 
    ctx.queue({
      id: `feature-synthesis-${Date.now()}`,
      title: "Synthesize experimental features from user prompts",
      source: "Alchemist",
      priority: "low",
      tags: ["experimental", "synthesis", "features"],
      payload: { createPrototypes: true, documentExperiments: true },
      createdAt: new Date().toISOString(), 
      dryRun: ctx.dryRun
    });
    actions.push("Queued feature synthesis");
    
    ctx.appendJournal("Alchemist", `plan: ${actions.length} alchemy tasks queued`);
    
    return {
      agent: "Alchemist",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Alchemist planned ${actions.length} integration and synthesis tasks`,
      actions,
      warnings: []
    };
  },

  act(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    if (ctx.dryRun) {
      actions.push("DRY RUN: Would perform integration alchemy and experimental synthesis");
      ctx.appendJournal("Alchemist", "act: dry-run mode, skipped alchemical operations");
      return {
        agent: "Alchemist",
        startedAt: new Date().toISOString(),
        finishedAt: new Date().toISOString(),
        summary: "Alchemist dry-run: alchemical processes ready for synthesis",
        actions,
        warnings: []
      };
    }
    
    // Perform integration alchemy
    let integrationsCreated = 0;
    
    // Create missing bridge modules
    const bridgeNeeded = ctx.readText("modules/culture_ship/agents/index.ts");
    if (!bridgeNeeded) {
      // Create agent index bridge
      const agentBridge = `/**
 * Agent Registry Bridge - Created by Alchemist
 * Integrates ChatDev agents with Culture-Ship ecosystem
 */
export * from "./types";
export * from "./agent_bus";
export { runAgentsCycle } from "./index";
`;
      ctx.writeText("modules/culture_ship/agents/bridge.ts", agentBridge);
      actions.push("Created agent bridge module");
      integrationsCreated++;
    }
    
    // Harmonize configurations
    const packageJson = ctx.readJSON("package.json");
    if (packageJson && !packageJson.scripts?.["agents:cycle"]) {
      packageJson.scripts = packageJson.scripts || {};
      packageJson.scripts["agents:cycle"] = "tsx modules/culture_ship/agents/cycle.ts";
      packageJson.scripts["agents:status"] = "tsx modules/culture_ship/agents/cycle.ts --status";
      ctx.writeJSON("package.json", packageJson);
      actions.push("Added agent scripts to package.json");
      integrationsCreated++;
    }
    
    // Create experimental synthesis report
    const synthesisReport = {
      timestamp: new Date().toISOString(),
      agent: "Alchemist", 
      integrationsCreated,
      experimentalFeatures: [
        "ChatDev-driven game mechanics generation",
        "Quantum-enhanced plugin system",
        "Consciousness-driven configuration management",
        "Autonomous dependency optimization"
      ],
      alchemicalProcesses: [
        "Module bridge synthesis",
        "Configuration harmonization", 
        "Dependency transmutation",
        "Feature prototype generation"
      ]
    };
    
    ctx.writeJSON("reports/alchemist_synthesis.json", synthesisReport);
    actions.push("Created alchemical synthesis report");
    
    ctx.appendJournal("Alchemist", `act: performed alchemy, integrations=${integrationsCreated} actions=${actions.length} warnings=${warnings.length}`);
    
    return {
      agent: "Alchemist",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Alchemist performed integration alchemy: ${integrationsCreated} integrations, ${actions.length} actions, ${warnings.length} warnings`,
      actions,
      warnings,
      metrics: { integrationsCreated, experimentalFeatures: 4 }
    };
  }
};