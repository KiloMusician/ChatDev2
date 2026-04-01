import type { Agent } from "./types";

/**
 * Artificer — Surgical Editor / Fixer
 * Executes precise, minimal-risk code edits and optimizations.
 * Responsible for items 2, 4, 52-54, 109, 13-14, 19, 83, 7-9, 93, 58, 108-109
 */
export const Artificer: Agent = {
  name: "Artificer",

  scan(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    // Scan for surgical editing opportunities
    const codeFiles = ctx.shell("find . -name '*.ts' -o -name '*.js' -o -name '*.mjs' -o -name '*.tsx' -o -name '*.jsx' 2>/dev/null | grep -v node_modules | wc -l").trim();
    const codeFileCount = parseInt(codeFiles) || 0;
    
    // Check for common issues that need surgical fixes
    const importIssues = ctx.shell("find . -name '*.ts' -o -name '*.js' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | xargs grep -l 'import.*undefined' 2>/dev/null | wc -l").trim();
    const importIssueCount = parseInt(importIssues) || 0;
    
    // Check for duplicate function names
    const duplicates = ctx.shell("find . -name '*.ts' -o -name '*.js' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | xargs grep -h '^export.*function\\|^function' 2>/dev/null | sort | uniq -d | wc -l").trim();
    const duplicateCount = parseInt(duplicates) || 0;
    
    if (importIssueCount > 0) {
      warnings.push(`Found ${importIssueCount} files with import issues`);
    }
    
    if (duplicateCount > 0) {
      warnings.push(`Found ${duplicateCount} duplicate function signatures`);  
    }
    
    actions.push(`Scanned ${codeFileCount} code files for surgical opportunities`);
    
    ctx.appendJournal("Artificer", `scan: codeFiles=${codeFileCount} importIssues=${importIssueCount} duplicates=${duplicateCount}`);
    
    return {
      agent: "Artificer", 
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Artificer scanned ${codeFileCount} code files, found ${importIssueCount} import issues, ${duplicateCount} duplicates`,
      actions,
      warnings,
      metrics: { codeFiles: codeFileCount, importIssues: importIssueCount, duplicates: duplicateCount }
    };
  },

  plan(ctx) {
    const actions: string[] = [];
    
    // Queue import fixes if needed
    if (ctx.insights.brokenImports > 0) {
      ctx.queue({
        id: `import-surgery-${Date.now()}`,
        title: "Perform surgical import fixes",
        source: "Artificer",
        priority: "high", 
        tags: ["surgery", "imports", "precision"],
        payload: { maxFixes: 25, verifyAfterEach: true },
        createdAt: new Date().toISOString(),
        dryRun: ctx.dryRun
      });
      actions.push("Queued surgical import fixes");
    }
    
    // Queue duplicate resolution
    if (ctx.insights.dupes > 0) {
      ctx.queue({
        id: `dupe-surgery-${Date.now()}`,
        title: "Perform surgical duplicate removal",
        source: "Artificer",
        priority: "normal",
        tags: ["surgery", "duplicates", "cleanup"],
        payload: { maxDupes: 10, preserveNewest: true },
        createdAt: new Date().toISOString(), 
        dryRun: ctx.dryRun
      });
      actions.push("Queued surgical duplicate removal");
    }
    
    // Queue code quality improvements
    ctx.queue({
      id: `quality-surgery-${Date.now()}`,
      title: "Apply surgical code quality improvements", 
      source: "Artificer",
      priority: "low",
      tags: ["surgery", "quality", "optimization"],
      payload: { focusAreas: ["unused-imports", "formatting", "comments"] },
      createdAt: new Date().toISOString(),
      dryRun: ctx.dryRun
    });
    actions.push("Queued quality improvements");
    
    ctx.appendJournal("Artificer", `plan: ${actions.length} surgical tasks queued`);
    
    return {
      agent: "Artificer",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Artificer planned ${actions.length} surgical editing tasks`,
      actions,
      warnings: []
    };
  },

  act(ctx) {
    const actions: string[] = [];
    const warnings: string[] = [];
    
    if (ctx.dryRun) {
      actions.push("DRY RUN: Would perform surgical code edits on imports, duplicates, and quality");
      ctx.appendJournal("Artificer", "act: dry-run mode, skipped surgical operations");
      return {
        agent: "Artificer",
        startedAt: new Date().toISOString(),
        finishedAt: new Date().toISOString(),
        summary: "Artificer dry-run: surgical tools ready for precise editing",
        actions,
        warnings: []
      };
    }
    
    // Perform minimal, safe surgical edits
    let editsPerformed = 0;
    
    // Fix obvious import typos (very conservative)
    try {
      const importFixes = ctx.shell("find . -name '*.ts' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | head -5");
      if (importFixes) {
        // Only log what we would fix, don't actually edit yet
        actions.push("Identified files for surgical import fixes");
        editsPerformed = 1;
      }
    } catch (e) {
      warnings.push(`Import surgery scan failed: ${e}`);
    }
    
    // Clean up unused variables in a very targeted way
    try {
      const unusedVars = ctx.shell("find . -name '*.ts' -o -name '*.mjs' 2>/dev/null | grep -v node_modules | xargs grep -n 'const.*=.*//.*unused' 2>/dev/null | head -3");
      if (unusedVars) {
        actions.push("Identified unused variables for cleanup");
        editsPerformed++;
      }
    } catch (e) {
      warnings.push(`Variable cleanup scan failed: ${e}`);
    }
    
    // Create surgical edit report
    const editReport = {
      timestamp: new Date().toISOString(),
      agent: "Artificer",
      editsIdentified: editsPerformed,
      safetyMode: "conservative",
      nextSteps: ["Review identified fixes", "Apply with verification", "Test after each edit"]
    };
    
    ctx.writeJSON("reports/artificer_surgery.json", editReport);
    actions.push("Created surgical edit report");
    
    ctx.appendJournal("Artificer", `act: performed surgical analysis, edits=${editsPerformed} actions=${actions.length} warnings=${warnings.length}`);
    
    return {
      agent: "Artificer",
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      summary: `Artificer performed surgical analysis: ${editsPerformed} edits identified, ${actions.length} actions, ${warnings.length} warnings`,
      actions,
      warnings,
      metrics: { editsIdentified: editsPerformed, safetyMode: 1 }
    };
  }
};