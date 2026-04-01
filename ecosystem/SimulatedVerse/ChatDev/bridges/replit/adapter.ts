// ChatDev/bridges/replit/adapter.ts  
// Prompt Adapter - Codify the "continue compelling" magic that worked

import type { RLCIEnvelope } from '../../../SystemDev/interfaces/rlci';
import { createRLCIEnvelope } from '../../../SystemDev/interfaces/rlci';
import fs from 'fs';
import path from 'path';

export interface UserPromptAnalysis {
  must_do: boolean;
  task_type: string;
  urgency_level: "low" | "medium" | "high" | "critical";
  keywords: string[];
  quadrant_hints: Array<"SystemDev" | "ChatDev" | "GameDev" | "PreviewUI">;
}

export class ReplitPromptAdapter {
  private compellingKeywords = [
    'todo', 'error', 'warning', 'conflict', 'issue', 'fix', 
    'broken', 'failing', 'crash', 'bug', 'problem'
  ];

  private urgentKeywords = [
    'critical', 'urgent', 'blocking', 'broken', 'crash', 'failed'
  ];

  private taskPatterns = [
    { pattern: /continue.*todo|todo.*continue/i, task: 'continue_todos_errors_conflicts_warnings' },
    { pattern: /fix.*error|error.*fix/i, task: 'fix_errors' },
    { pattern: /debug|investigate/i, task: 'debug_investigation' },
    { pattern: /optimize|improve|enhance/i, task: 'optimization' },
    { pattern: /refactor|restructure/i, task: 'refactoring' },
    { pattern: /test|verify|check/i, task: 'verification' },
    { pattern: /deploy|build|release/i, task: 'deployment' },
    { pattern: /preview.*mobile|mobile.*preview/i, task: 'mobile_preview_hardening' }
  ];

  analyzeUserPrompt(userText: string): UserPromptAnalysis {
    const lowerText = userText.toLowerCase();
    
    // Check for compelling indicators
    const must_do = this.compellingKeywords.some(keyword => 
      lowerText.includes(keyword)
    );

    // Determine urgency
    let urgency_level: UserPromptAnalysis['urgency_level'] = "medium";
    if (this.urgentKeywords.some(keyword => lowerText.includes(keyword))) {
      urgency_level = "critical";
    } else if (must_do) {
      urgency_level = "high";
    } else if (lowerText.includes('quick') || lowerText.includes('simple')) {
      urgency_level = "low";
    }

    // Extract task type
    let task_type = 'assist';
    for (const { pattern, task } of this.taskPatterns) {
      if (pattern.test(userText)) {
        task_type = task;
        break;
      }
    }

    // Extract keywords
    const keywords = this.compellingKeywords.filter(keyword => 
      lowerText.includes(keyword)
    );

    // Determine quadrant hints
    const quadrant_hints: UserPromptAnalysis['quadrant_hints'] = [];
    if (lowerText.includes('system') || lowerText.includes('script') || lowerText.includes('infra')) {
      quadrant_hints.push('SystemDev');
    }
    if (lowerText.includes('agent') || lowerText.includes('chat') || lowerText.includes('ai')) {
      quadrant_hints.push('ChatDev');
    }
    if (lowerText.includes('game') || lowerText.includes('godot') || lowerText.includes('engine')) {
      quadrant_hints.push('GameDev');
    }
    if (lowerText.includes('preview') || lowerText.includes('ui') || lowerText.includes('mobile')) {
      quadrant_hints.push('PreviewUI');
    }

    // Default to all quadrants if none specified
    if (quadrant_hints.length === 0) {
      quadrant_hints.push('SystemDev', 'ChatDev', 'GameDev', 'PreviewUI');
    }

    return {
      must_do,
      task_type,
      urgency_level,
      keywords,
      quadrant_hints
    };
  }

  toRLCI(userText: string): RLCIEnvelope {
    const analysis = this.analyzeUserPrompt(userText);
    const currentFocus = this.getCurrentFocus();
    
    const priority = {
      'low': 'LOW' as const,
      'medium': 'MEDIUM' as const, 
      'high': 'HIGH' as const,
      'critical': 'CRITICAL' as const
    }[analysis.urgency_level];

    return createRLCIEnvelope('chat', analysis.task_type, {
      quad: analysis.quadrant_hints,
      loc: {
        cwd: process.cwd(),
        focus: currentFocus.focus,
        selection: currentFocus.selection
      },
      omnitag: {
        mode: analysis.must_do ? "breath_cycle" : "micro_cycle",
        law: "receipts",
        colony: "ΞNuSyQ", 
        anneal: true,
        zeta_checks: true,
        anti_theater: true,
        temple: analysis.quadrant_hints
      },
      intent: {
        task: analysis.task_type,
        priority,
        limits: {
          edits_max: analysis.urgency_level === 'critical' ? 12 : 8,
          lines_max: analysis.urgency_level === 'critical' ? 600 : 400
        },
        safety: ["path_safe_moves", "idempotent", "receipt_required"]
      },
      hints: [
        "Use capability registry before invoking tools",
        "Observe micro-cycle limits",
        analysis.must_do ? "Continue until compelling items resolved" : "Single focused improvement",
        ...(analysis.keywords.length > 0 ? [`Keywords: ${analysis.keywords.join(', ')}`] : [])
      ]
    });
  }

  private getCurrentFocus(): { focus: string[]; selection?: string[] } {
    // Try to detect current working context
    const focus = ["src/", "SystemDev/scripts"];
    
    // Check for recent git activity
    try {
      const gitStatus = require('child_process').execSync('git status --porcelain', { 
        encoding: 'utf-8', 
        stdio: 'pipe' 
      });
      
      if (gitStatus) {
        const modifiedFiles = gitStatus
          .split('\n')
          .filter(line => line.trim())
          .map(line => line.substring(3))
          .filter(file => !file.includes('node_modules'));
        
        if (modifiedFiles.length > 0) {
          focus.push(...modifiedFiles.slice(0, 3));
        }
      }
    } catch (error) {
      // Git not available or error
    }

    // Check for recent receipts to understand last activity
    try {
      const receiptsDir = 'SystemDev/receipts';
      if (fs.existsSync(receiptsDir)) {
        const receipts = fs.readdirSync(receiptsDir)
          .filter(file => file.endsWith('.json'))
          .sort()
          .slice(-3);
        
        for (const receiptFile of receipts) {
          try {
            const receipt = JSON.parse(
              fs.readFileSync(path.join(receiptsDir, receiptFile), 'utf-8')
            );
            
            if (receipt.focus || receipt.file) {
              focus.push(receipt.focus || receipt.file);
            }
          } catch (error) {
            // Invalid receipt file
          }
        }
      }
    } catch (error) {
      // Receipts not available
    }

    return { focus: [...new Set(focus)] };
  }

  // Generate the magic "continue compelling" prompt
  generateCompellingPrompt(): string {
    return `ΞNuSyQ::RLCI v1 — Quadpartite Continuation

ENV:
  device: Samsung S23 • Replit App (Preview)
  micro_cycle: true (≤8 edits / ≤400 lines)
  receipts: required
  anti_theater: true • zeta_checks: true • anneal: true

INTENT:
  continue_todos_errors_conflicts_warnings

SCOPE:
  prefer_roots: [ "src", "ChatDev", "GameDev", "SystemDev/scripts" ]
  ignore: [ "**/node_modules/**", "**/dist/**", "**/*.map", "**/.godot/**" ]
  selection_priority:
    - last_open_file
    - files with failing diagnostics
    - receipts where "needs_action": true

CAPABILITIES:
  load: "SystemDev/reports/capabilities.json"
  if_missing: run "tsx SystemDev/scripts/capability_registry.ts"

BEHAVIOR:
  1) Query receipts & diagnostics → pick the single most compelling fix.
  2) Execute the smallest viable change (≤8 edits).
  3) If search overload: run "tsx SystemDev/scripts/targeted_provenance.ts --roots src ChatDev GameDev".
  4) If path changes needed: call Artificer (import_rewriter + godot scene map).
  5) Write a receipt:
     SystemDev/receipts/cycle_\${timestamp}.json
     { file, edits, lines_changed, tests, next_hint }
  6) Trigger Culture-Ship cascade if ≥6 clean edits across cycles.

TIPS:
  - If git blocked: use Git-Steward (shell-first).
  - If "Cannot find module": run import_rewriter with path_alias_map.json.
  - If "repo too large": switch to targeted_provenance with --roots.

OUTPUT:
  concise log of what you fixed, the diff summary, and the receipt path.
  DO NOT stop after one pass if compelling items remain; enqueue next pass.`;
  }
}

// Factory function for easy usage
export function toRLCI(userText: string): RLCIEnvelope {
  const adapter = new ReplitPromptAdapter();
  return adapter.toRLCI(userText);
}

export default ReplitPromptAdapter;