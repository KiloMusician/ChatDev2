// SystemDev/guards/tipsynth.ts
// TipSynth - Contextual, intelligent, non-spammy hints from failures

import type { TipSynthInput, TipSynthOutput, RLCIEnvelope } from '../interfaces/rlci';

interface TipRule {
  pattern: RegExp;
  condition?: (input: TipSynthInput) => boolean;
  tip: string;
  action?: string;
  priority: "low" | "medium" | "high";
  run_card?: string;
}

export class TipSynth {
  private rules: TipRule[] = [
    // Git issues
    {
      pattern: /index\.lock/i,
      tip: "Git index locked. Try: git gc && rm -f .git/index.lock, then re-run",
      action: "git gc && rm -f .git/index.lock",
      priority: "high"
    },
    
    // Search overload
    {
      pattern: /too many files|search.*timeout|repo.*large/i,
      tip: "Switch to targeted search with --roots to limit scope",
      action: "tsx SystemDev/scripts/targeted_provenance.ts --roots src ChatDev GameDev",
      priority: "high"
    },
    
    // Module resolution
    {
      pattern: /cannot find module|module.*not found/i,
      condition: (input) => input.capabilities?.custom_scripts?.some((s: any) => s.path.includes('import_rewriter')),
      tip: "Run import rewriter to fix path aliases",
      action: "tsx SystemDev/scripts/import_rewriter.ts",
      priority: "medium",
      run_card: "SystemDev/cards/import_resolution.md"
    },
    
    // TypeScript errors
    {
      pattern: /type.*error|typescript.*error/i,
      tip: "Check tsconfig paths or run type alignment",
      action: "npx tsc --noEmit",
      priority: "medium"
    },
    
    // Permission issues
    {
      pattern: /permission denied|eacces/i,
      tip: "File permission issue. Check file ownership or use sudo",
      priority: "high"
    },
    
    // Port conflicts
    {
      pattern: /port.*already.*use|eaddrinuse/i,
      tip: "Port conflict detected. Check running processes or use different port",
      action: "ps aux | grep node | head -10",
      priority: "medium"
    },
    
    // Godot-specific
    {
      pattern: /godot.*error|\.tscn.*not.*found|gd.*script.*error/i,
      condition: (input) => input.envelope.quad.includes('GameDev'),
      tip: "Godot asset issue. Check scene paths or reimport assets",
      action: "find GameDev -name '*.tscn' -o -name '*.gd'",
      priority: "medium"
    },
    
    // Mobile Preview issues
    {
      pattern: /webgl.*error|canvas.*failed|mobile.*preview/i,
      condition: (input) => input.context?.file_path?.includes('PreviewUI') || 
                           input.envelope.quad.includes('PreviewUI'),
      tip: "Mobile compatibility issue. Check WebGL1 fallback and threading",
      priority: "high",
      run_card: "PreviewUI/cards/mobile_debug.md"
    },
    
    // Network issues
    {
      pattern: /fetch.*failed|network.*error|connection.*refused/i,
      tip: "Network connectivity issue. Check server status and endpoints",
      action: "curl -I http://localhost:5000/healthz",
      priority: "medium"
    },
    
    // Cache issues
    {
      pattern: /cache.*error|stale.*content|service.*worker/i,
      tip: "Cache poisoning detected. Clear browser cache and service workers",
      action: "Check /unstick.json endpoint",
      priority: "medium"
    },
    
    // ESLint/Linting
    {
      pattern: /eslint.*error|linting.*failed/i,
      tip: "Code style issue. Run linter with --fix flag",
      action: "npm run lint --fix",
      priority: "low"
    }
  ];

  synthesize(input: TipSynthInput): TipSynthOutput {
    const matchedTips: TipSynthOutput['tips'] = [];
    const alternativeCommands: string[] = [];
    
    for (const rule of this.rules) {
      if (rule.pattern.test(input.error_text)) {
        // Check condition if exists
        if (rule.condition && !rule.condition(input)) {
          continue;
        }
        
        matchedTips.push({
          text: rule.tip,
          action: rule.action,
          priority: rule.priority,
          run_card: rule.run_card
        });
        
        if (rule.action) {
          alternativeCommands.push(rule.action);
        }
      }
    }
    
    // Sort by priority
    matchedTips.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
    
    // Add contextual tips based on envelope
    const contextualTips = this.getContextualTips(input);
    matchedTips.push(...contextualTips);
    
    // Determine escalation if needed
    const escalation = this.getEscalation(input, matchedTips);
    
    return {
      tips: matchedTips.slice(0, 3), // Limit to top 3 tips to avoid spam
      alternative_commands: alternativeCommands.slice(0, 2),
      escalation
    };
  }

  private getContextualTips(input: TipSynthInput): TipSynthOutput['tips'] {
    const tips: TipSynthOutput['tips'] = [];
    
    // Quadrant-specific tips
    if (input.envelope.quad.includes('SystemDev')) {
      tips.push({
        text: "SystemDev context: Check scripts directory and capability registry",
        priority: "low"
      });
    }
    
    if (input.envelope.quad.includes('ChatDev')) {
      tips.push({
        text: "ChatDev context: Verify agent registry and directives",
        priority: "low"
      });
    }
    
    if (input.envelope.quad.includes('GameDev')) {
      tips.push({
        text: "GameDev context: Check Godot project and asset paths",
        priority: "low"
      });
    }
    
    if (input.envelope.quad.includes('PreviewUI')) {
      tips.push({
        text: "PreviewUI context: Verify mobile compatibility and Preview serving",
        priority: "low"
      });
    }
    
    // Anti-theater checks
    if (input.envelope.omnitag.anti_theater) {
      tips.push({
        text: "Anti-theater mode: Focus on real, measurable progress only",
        priority: "medium"
      });
    }
    
    return tips;
  }

  private getEscalation(input: TipSynthInput, tips: TipSynthOutput['tips']): TipSynthOutput['escalation'] {
    // Escalate to specific agents based on error patterns
    if (input.error_text.match(/git.*error|repository.*error/i)) {
      return {
        agent: "janitor",
        directive: "git_steward_playbook"
      };
    }
    
    if (input.error_text.match(/import.*error|module.*not.*found/i)) {
      return {
        agent: "artificer", 
        directive: "import_rewriter_cascade"
      };
    }
    
    if (input.error_text.match(/mobile.*preview|webgl.*error/i)) {
      return {
        agent: "navigator",
        directive: "mobile_preview_hardening"
      };
    }
    
    // High-priority issues get escalated to Raven
    if (tips.some(tip => tip.priority === 'high')) {
      return {
        agent: "raven",
        directive: "anomaly_investigation"
      };
    }
    
    return undefined;
  }

  // Add custom rules at runtime
  addRule(rule: TipRule): void {
    this.rules.push(rule);
  }

  // Get rules matching a pattern for debugging
  getRulesFor(errorText: string): TipRule[] {
    return this.rules.filter(rule => rule.pattern.test(errorText));
  }
}

// Factory function for easy usage
export function synthesizeTips(
  errorText: string,
  lastCommand: string,
  envelope: RLCIEnvelope,
  capabilities: any,
  context?: TipSynthInput['context']
): TipSynthOutput {
  const tipsynth = new TipSynth();
  return tipsynth.synthesize({
    error_text: errorText,
    last_command: lastCommand,
    envelope,
    capabilities,
    context
  });
}

export default TipSynth;