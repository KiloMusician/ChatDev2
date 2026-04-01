import type { Agent } from "./types";

/**
 * Librarian — Knowledge steward, documentation engine, and research AI.
 * Manages Obsidian/Jupyter/Docs integration and maintains lore archives.
 * Responsible for items 31-39, 61-70, 5, 97, 114, 46, 48, 3, 115, 117
 */
export const Librarian: Agent = {
  name: "Librarian",

  scan(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    // Scan for knowledge repositories
    const knowledgePaths = [
      "kb/",
      "content/",
      "reports/",
      "replit.md",
      "*.rtf",
      "*.md"
    ];
    
    let knowledgeFiles = 0;
    for (const pattern of knowledgePaths) {
      const found = ctx.shell(`find . -path "./node_modules" -prune -o -name "${pattern}" -print 2>/dev/null | wc -l`).trim();
      const count = parseInt(found) || 0;
      knowledgeFiles += count;
      if (count > 0) {
        actions.push(`Found ${count} files matching ${pattern}`);
      }
    }
    
    // Check for documentation gaps
    const hasReadme = !!ctx.readText("README.md");
    const hasReplit = !!ctx.readText("replit.md");
    
    if (!hasReadme) warnings.push("No README.md found");
    if (!hasReplit) warnings.push("No replit.md found");
    
    // Scan for lore consistency
    const loreFiles = ctx.shell("find . -name '*.rtf' -o -name '*lexicon*' -o -name '*lore*' 2>/dev/null | wc -l").trim();
    const loreCount = parseInt(loreFiles) || 0;
    
    ctx.appendJournal("Librarian", `scan: knowledgeFiles=${knowledgeFiles} loreFiles=${loreCount} hasReadme=${hasReadme} hasReplit=${hasReplit}`);
    
    return {
      agent: "Librarian",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Librarian scanned ${knowledgeFiles} knowledge files, ${loreCount} lore files`,
      actions,
      warnings,
      metrics: { knowledgeFiles, loreCount }
    };
  },

  plan(ctx) {
    const actions: string[] = [];
    
    // Queue knowledge synchronization
    ctx.queue({
      id: `knowledge-sync-${Date.now()}`,
      title: "Synchronize knowledge repositories with game codex",
      source: "Librarian",
      priority: "normal",
      tags: ["knowledge", "sync", "codex"],
      payload: { syncObsidian: true, updateLore: true },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued knowledge synchronization");
    
    // Queue lore expansion if we have existing lore
    const loreExists = ctx.shell("find . -name '*lexicon*' -o -name '*lore*' 2>/dev/null").trim();
    if (loreExists) {
      ctx.queue({
        id: `lore-expansion-${Date.now()}`,
        title: "Expand lore archives with recent system evolution",
        source: "Librarian",
        priority: "low",
        tags: ["lore", "expansion", "archives"],
        payload: { focusAreas: ["quantum-development", "consciousness-evolution", "culture-ship"] },
        createdAt: new Date().toISOString(),
        dryRun: ctx.dryRun
      });
      actions.push("Queued lore expansion");
    }
    
    // Queue documentation maintenance
    if (ctx.insights.todos > 5) {
      ctx.queue({
        id: `docs-maintenance-${Date.now()}`,
        title: "Convert TODOs into structured knowledge entries",
        source: "Librarian",
        priority: "normal",
        tags: ["documentation", "todos", "structure"],
        payload: { maxTodos: 20, createFAQ: true },
        createdAt: new Date().toISOString(),
        dryRun: ctx.dryRun
      });
      actions.push("Queued documentation maintenance");
    }
    
    ctx.appendJournal("Librarian", `plan: ${actions.length} knowledge tasks queued`);
    
    return {
      agent: "Librarian",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Librarian planned ${actions.length} knowledge management tasks`,
      actions,
      warnings: []
    };
  },

  act(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    if (ctx.dryRun) {
      actions.push("DRY RUN: Would synchronize knowledge repositories and expand lore");
      ctx.appendJournal("Librarian", "act: dry-run mode, skipped knowledge operations");
      return {
        agent: "Librarian",
        startedAt: new Date().toISOString(),
        finishedAt: new Date().toISOString(),
        summary: "Librarian dry-run: knowledge systems ready for synchronization",
        actions,
        warnings: []
      };
    }
    
    // Update replit.md with latest insights
    const replitMd = ctx.readText("replit.md");
    if (replitMd) {
      const now = new Date().toISOString().split('T')[0];
      const updatedMd = replitMd + `\n\n# Recent Changes (${now})\n\nChatDev agents now operational with quantum development integration.\n`;
      ctx.writeText("replit.md", updatedMd);
      actions.push("Updated replit.md with agent status");
    } else {
      warnings.push("No replit.md to update");
    }
    
    // Create knowledge summary
    const summary = {
      timestamp: new Date().toISOString(),
      brokenImports: ctx.insights.brokenImports,
      duplicates: ctx.insights.dupes,
      todos: ctx.insights.todos,
      agents: ["NeuroTide", "Librarian", "Artificer", "Alchemist", "Pilot", "Intermediary", "Council"],
      status: "ChatDev integration active with quantum development"
    };
    
    ctx.writeJSON("reports/librarian_summary.json", summary);
    actions.push("Created knowledge summary report");
    
    ctx.appendJournal("Librarian", `act: performed knowledge operations, actions=${actions.length} warnings=${warnings.length}`);
    
    return {
      agent: "Librarian",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Librarian executed knowledge management: ${actions.length} actions, ${warnings.length} warnings`,
      actions,
      warnings,
      metrics: { documentsProcessed: actions.length }
    };
  }
};