import type { Agent } from "./types";

/**
 * Intermediary — Human ↔ AI Translator
 * Converts vague user input into structured ChatDev tasks.
 * Responsible for items 111-120, 57, 60, 47, 23, 118, 101, 104
 */
export const Intermediary: Agent = {
  name: "Intermediary",

  scan(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    // Scan for user interaction opportunities
    const interactionFiles = [
      "client/",
      "src/",
      "*.tsx",
      "*.jsx"
    ];
    
    let uiComponents = 0;
    for (const pattern of interactionFiles) {
      const found = ctx.shell(`find . -path "./node_modules" -prune -o -name "${pattern}" -print 2>/dev/null | wc -l`).trim();
      const count = parseInt(found) || 0;
      uiComponents += count;
    }
    
    // Check for user prompts in recent commits/logs
    const recentActivity = ctx.shell("git log --oneline -10 2>/dev/null | grep -i 'add\\|fix\\|update\\|create' | wc -l").trim();
    const activityLevel = parseInt(recentActivity) || 0;
    
    // Scan for Big Red Button integration opportunities
    const hasHUD = ctx.readText("client/src/components/HUD.tsx") || ctx.readText("src/components/HUD.tsx");
    const hasCascadeButton = hasHUD && hasHUD.includes("cascade");
    
    if (uiComponents > 0) {
      actions.push(`Found ${uiComponents} UI components for user interaction`);
    } else {
      warnings.push("No UI components found - limited user interaction capability");
    }
    
    if (!hasCascadeButton) {
      warnings.push("No cascade button found in UI - missing Big Red Button integration");
    }
    
    ctx.appendJournal("Intermediary", `scan: uiComponents=${uiComponents} activity=${activityLevel} hasCascadeButton=${hasCascadeButton}`);
    
    return {
      agent: "Intermediary",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Intermediary scanned ${uiComponents} UI components, activity level ${activityLevel}, cascade button: ${hasCascadeButton}`,
      actions,
      warnings,
      metrics: { uiComponents, activityLevel, hasCascadeButton: hasCascadeButton ? 1 : 0 }
    };
  },

  plan(ctx) {
    const actions: string[] = [];
    
    // Queue user interface enhancements
    ctx.queue({
      id: `ui-enhancement-${Date.now()}`,
      title: "Enhance user interfaces for ChatDev integration",
      source: "Intermediary",
      priority: "normal",
      tags: ["ui", "chatdev", "integration"],
      payload: { addCascadeButton: true, addAgentStatus: true, addTokenDisplay: true },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued UI enhancement for ChatDev integration");
    
    // Queue user prompt processing system
    ctx.queue({
      id: `prompt-processing-${Date.now()}`,
      title: "Create user prompt to ChatDev task translation system",
      source: "Intermediary",
      priority: "high",
      tags: ["prompts", "translation", "chatdev"],
      payload: { 
        supportedPrompts: [
          "Add roguelike dungeon",
          "Fix tower defense pathfinding", 
          "Balance economy",
          "Unlock Temple floor",
          "Evolve system"
        ]
      },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued prompt processing system");
    
    // Queue cost transparency features
    ctx.queue({
      id: `cost-transparency-${Date.now()}`,
      title: "Implement token cost transparency for user actions",
      source: "Intermediary",
      priority: "normal",
      tags: ["transparency", "costs", "tokens"],
      payload: { showBeforeAction: true, preferZeroToken: true, budgetWarnings: true },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued cost transparency features");
    
    ctx.appendJournal("Intermediary", `plan: ${actions.length} user interface tasks queued`);
    
    return {
      agent: "Intermediary",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Intermediary planned ${actions.length} user interface and translation tasks`,
      actions,
      warnings: []
    };
  },

  act(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    if (ctx.dryRun) {
      actions.push("DRY RUN: Would enhance UI with ChatDev integration and cost transparency");
      ctx.appendJournal("Intermediary", "act: dry-run mode, skipped UI operations");
      return {
        agent: "Intermediary",
        startedAt: new Date().toISOString(),
        finishedAt: new Date().toISOString(),
        summary: "Intermediary dry-run: UI enhancements ready for integration",
        actions,
        warnings: []
      };
    }
    
    // Create user prompt translation guide
    const promptGuide = {
      timestamp: new Date().toISOString(),
      agent: "Intermediary",
      supportedPrompts: {
        "Add roguelike dungeon": {
          chatdevTask: "Generate ASCII dungeon layout with rooms and corridors",
          estimatedTokens: 0,
          localFirst: true,
          agentsInvolved: ["Artificer", "Alchemist"]
        },
        "Fix tower defense pathfinding": {
          chatdevTask: "Analyze and optimize pathfinding algorithms",
          estimatedTokens: 0,
          localFirst: true,
          agentsInvolved: ["Artificer", "NeuroTide"]
        },
        "Balance economy": {
          chatdevTask: "Use Pandas analysis to adjust resource curves",
          estimatedTokens: 0,
          localFirst: true,
          agentsInvolved: ["Librarian", "Alchemist"]
        },
        "Unlock Temple floor": {
          chatdevTask: "Execute cascade cycle to unlock next progression tier",
          estimatedTokens: 0,
          localFirst: true,
          agentsInvolved: ["Pilot", "NeuroTide"]
        },
        "Evolve system": {
          chatdevTask: "Trigger consciousness evolution and meta-optimization",
          estimatedTokens: 0,
          localFirst: true,
          agentsInvolved: ["NeuroTide", "Council"]
        }
      },
      translationPrinciples: [
        "Always prefer zero-token local solutions",
        "Break complex requests into micro-tasks",
        "Show cost estimates before execution",
        "Route through appropriate specialist agents"
      ]
    };
    
    ctx.writeJSON("reports/intermediary_prompt_guide.json", promptGuide);
    actions.push("Created user prompt translation guide");
    
    // Create Big Red Button specification
    const bigRedButton = {
      timestamp: new Date().toISOString(),
      name: "Big Red Cascade Button",
      purpose: "One-click access to full ChatDev agent cascade cycle",
      implementation: {
        component: "CascadeButton",
        location: "HUD or main interface",
        styling: "Large, prominent, red background",
        onclick: "triggerAgentCascade()",
        confirmDialog: "Execute full agent cascade cycle?",
        costDisplay: "Estimated tokens: 0 (local-first)"
      },
      functionality: [
        "Trigger all agents in sequence",
        "Show real-time progress",
        "Display token usage",
        "Provide abort mechanism",
        "Log all agent reports"
      ]
    };
    
    ctx.writeJSON("reports/intermediary_big_red_button.json", bigRedButton);
    actions.push("Created Big Red Button specification");
    
    ctx.appendJournal("Intermediary", `act: created translation systems, actions=${actions.length} warnings=${warnings.length}`);
    
    return {
      agent: "Intermediary",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Intermediary created user interface translation systems: ${actions.length} actions, ${warnings.length} warnings`,
      actions,
      warnings,
      metrics: { translationGuideCreated: 1, bigRedButtonSpecified: 1 }
    };
  }
};