/**
 * 🐛➡️🎮 Error Quest Transformer
 * CoreLink Foundation - Transform Errors into Engaging Adventures
 * 
 * Converts LSP diagnostics, runtime errors, and system issues into rewarding quests
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { gamificationEngine } from './enhanced-gamification-system.ts';
import { cultivationSystem } from './cultivation-healing-system.ts';

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 ERROR TRANSFORMATION TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export interface ErrorContext {
  source: 'lsp' | 'runtime' | 'build' | 'test' | 'lint' | 'security' | 'performance';
  severity: 'info' | 'warning' | 'error' | 'critical';
  error_code?: string;
  message: string;
  file_path?: string;
  line_number?: number;
  column?: number;
  stack_trace?: string;
  suggested_fixes?: string[];
}

export interface ErrorQuest {
  id: string;
  title: string;
  error_context: ErrorContext;
  quest_category: 'debugging_labyrinth' | 'syntax_surgery' | 'runtime_rescue' | 'performance_pursuit' | 'security_sanctuary';
  difficulty_tier: 'novice' | 'apprentice' | 'adept' | 'master' | 'transcendent';
  narrative_frame: string;
  mechanics: {
    base_xp: number;
    diagnostic_bonus: number;
    prevention_multiplier: number;
    speed_bonus_threshold: number; // seconds
  };
  solution_paths: Array<{
    method: string;
    description: string;
    steps: string[];
    xp_multiplier: number;
    cultivation_effects: string[];
    mastery_gained: number;
  }>;
  healing_rituals: Array<{
    ritual: string;
    healing_power: number;
    cultivation_benefit: string;
  }>;
}

export interface QuestProgress {
  quest_id: string;
  start_time: number;
  diagnostic_time?: number;
  resolution_time?: number;
  solution_method?: string;
  xp_earned?: number;
  cultivation_gained?: number;
  status: 'active' | 'diagnostic' | 'solving' | 'completed' | 'abandoned';
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🔬 ERROR PATTERN ANALYZER
// ═══════════════════════════════════════════════════════════════════════════════

export class ErrorPatternAnalyzer {
  private error_patterns: Map<string, any> = new Map();
  private mastery_levels: Map<string, number> = new Map();
  
  constructor() {
    this.initializeErrorPatterns();
    this.loadMasteryData();
  }

  private initializeErrorPatterns(): void {
    // TypeScript/JavaScript Error Patterns
    this.error_patterns.set('TS2304', {
      pattern: /Cannot find name '(\w+)'/,
      category: 'syntax_surgery',
      difficulty: 'novice',
      common_causes: ['typo', 'missing_import', 'scope_issue'],
      solution_templates: [
        'Check spelling of variable/function name',
        'Add missing import statement',
        'Verify variable is in scope'
      ]
    });

    this.error_patterns.set('TS2339', {
      pattern: /Property '(\w+)' does not exist on type '(.+)'/,
      category: 'debugging_labyrinth',
      difficulty: 'apprentice',
      common_causes: ['incorrect_type', 'missing_property', 'interface_mismatch'],
      solution_templates: [
        'Check type definitions',
        'Add missing property to interface',
        'Use type assertion if necessary'
      ]
    });

    this.error_patterns.set('runtime_error', {
      pattern: /ReferenceError: (\w+) is not defined/,
      category: 'runtime_rescue',
      difficulty: 'adept',
      common_causes: ['undefined_variable', 'timing_issue', 'scope_problem'],
      solution_templates: [
        'Initialize variable before use',
        'Check execution order',
        'Verify variable scope and lifecycle'
      ]
    });

    this.error_patterns.set('performance_warning', {
      pattern: /Performance warning: (.+)/,
      category: 'performance_pursuit',
      difficulty: 'master',
      common_causes: ['inefficient_algorithm', 'memory_leak', 'blocking_operation'],
      solution_templates: [
        'Optimize algorithm complexity',
        'Implement caching strategy',
        'Use async patterns'
      ]
    });

    this.error_patterns.set('security_vulnerability', {
      pattern: /Security vulnerability: (.+)/,
      category: 'security_sanctuary',
      difficulty: 'transcendent',
      common_causes: ['input_validation', 'authentication_bypass', 'data_exposure'],
      solution_templates: [
        'Implement input sanitization',
        'Add authentication checks',
        'Encrypt sensitive data'
      ]
    });
  }

  analyzeError(error_context: ErrorContext): {
    pattern_match: any | null;
    difficulty_assessment: string;
    suggested_category: string;
    mastery_influence: number;
  } {
    // Try to match error patterns
    let pattern_match = null;
    
    for (const [pattern_id, pattern_data] of this.error_patterns) {
      if (pattern_data.pattern.test(error_context.message)) {
        pattern_match = { id: pattern_id, ...pattern_data };
        break;
      }
    }

    // Assess difficulty based on context and user mastery
    const base_difficulty = pattern_match?.difficulty || 'novice';
    const category = pattern_match?.category || 'debugging_labyrinth';
    const user_mastery = this.mastery_levels.get(category) || 0;
    
    // Adjust difficulty based on mastery
    let difficulty_assessment = base_difficulty;
    if (user_mastery > 50 && base_difficulty === 'novice') difficulty_assessment = 'apprentice';
    if (user_mastery > 100 && base_difficulty === 'apprentice') difficulty_assessment = 'adept';

    return {
      pattern_match,
      difficulty_assessment,
      suggested_category: category,
      mastery_influence: user_mastery
    };
  }

  updateMastery(category: string, points: number): void {
    const current = this.mastery_levels.get(category) || 0;
    this.mastery_levels.set(category, current + points);
    this.saveMasteryData();
  }

  private loadMasteryData(): void {
    try {
      if (existsSync('.local/error-mastery.json')) {
        const data = JSON.parse(readFileSync('.local/error-mastery.json', 'utf8'));
        this.mastery_levels = new Map(data.mastery || []);
      }
    } catch (error) {
      console.warn('Failed to load mastery data:', error);
    }
  }

  private saveMasteryData(): void {
    try {
      mkdirSync('.local', { recursive: true });
      writeFileSync('.local/error-mastery.json', JSON.stringify({
        mastery: Array.from(this.mastery_levels.entries()),
        timestamp: Date.now()
      }, null, 2));
    } catch (error) {
      console.warn('Failed to save mastery data:', error);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🎮 QUEST GENERATOR
// ═══════════════════════════════════════════════════════════════════════════════

export class ErrorQuestGenerator {
  private analyzer: ErrorPatternAnalyzer;
  private quest_templates: Map<string, any> = new Map();
  
  constructor() {
    this.analyzer = new ErrorPatternAnalyzer();
    this.initializeQuestTemplates();
  }

  private initializeQuestTemplates(): void {
    this.quest_templates.set('syntax_surgery', {
      title_templates: [
        'The Syntax Surgeon\'s Challenge',
        'Code Grammar Guardian',
        'Symbol Syntax Restoration',
        'Parsing Precision Master'
      ],
      narrative_templates: [
        '🔍 The code parser has stumbled upon a linguistic anomaly. Your syntax surgery skills are needed to restore grammatical harmony to the digital realm.',
        '📝 Ancient symbols have become misaligned, disrupting the flow of computational energy. Channel your inner grammarian to heal the syntax.',
        '⚡ A syntax disruption threatens the code\'s ability to communicate with the compiler. Your precision is required to mend this linguistic rift.'
      ],
      mechanics_base: {
        base_xp: 25,
        diagnostic_bonus: 10,
        prevention_multiplier: 1.5,
        speed_bonus_threshold: 120
      }
    });

    this.quest_templates.set('debugging_labyrinth', {
      title_templates: [
        'Labyrinth Navigator\'s Trial',
        'Logic Maze Master',
        'Recursive Reality Warden',
        'Semantic Sanctuary Seeker'
      ],
      narrative_templates: [
        '🌀 You stand at the entrance of the Debugging Labyrinth, where logic and meaning intertwine in complex patterns. Navigate the semantic maze to restore order.',
        '🗝️ Hidden within the code\'s logic lies a paradox that defies understanding. Your analytical prowess must pierce through the confusion.',
        '🔮 The very fabric of program logic has become entangled. Use your debugging divination to unravel the mystery.'
      ],
      mechanics_base: {
        base_xp: 40,
        diagnostic_bonus: 15,
        prevention_multiplier: 2.0,
        speed_bonus_threshold: 300
      }
    });

    this.quest_templates.set('runtime_rescue', {
      title_templates: [
        'Runtime Reality Guardian',
        'Execution Environment Savior',
        'Dynamic Disaster Response',
        'Temporal Execution Healer'
      ],
      narrative_templates: [
        '⚡ The runtime realm trembles as execution flows encounter unexpected obstacles. Your emergency response skills are critical.',
        '🌊 A cascade of runtime events threatens to crash the digital ecosystem. Stabilize the execution environment before chaos ensues.',
        '🚨 Runtime anomalies have been detected! Your swift intervention could mean the difference between graceful recovery and system failure.'
      ],
      mechanics_base: {
        base_xp: 60,
        diagnostic_bonus: 20,
        prevention_multiplier: 2.5,
        speed_bonus_threshold: 180
      }
    });

    this.quest_templates.set('performance_pursuit', {
      title_templates: [
        'Performance Optimization Sage',
        'Efficiency Enlightenment Seeker',
        'Computational Speed Ascension',
        'Algorithmic Transcendence'
      ],
      narrative_templates: [
        '🚀 The code yearns to transcend its current limitations and achieve computational nirvana. Guide it toward performance enlightenment.',
        '⚡ Inefficiencies drag down the system\'s true potential. Your optimization mastery can unlock hidden performance dimensions.',
        '🌟 The path to algorithmic perfection reveals itself through careful analysis and inspired optimization.'
      ],
      mechanics_base: {
        base_xp: 80,
        diagnostic_bonus: 25,
        prevention_multiplier: 3.0,
        speed_bonus_threshold: 600
      }
    });

    this.quest_templates.set('security_sanctuary', {
      title_templates: [
        'Guardian Protocol Defender',
        'Security Sanctuary Sentinel',
        'Digital Fortress Architect',
        'Ethical Cyber Guardian'
      ],
      narrative_templates: [
        '🛡️ Dark forces threaten the integrity of the digital realm. Your guardian training activates to establish impenetrable defenses.',
        '🏰 The security sanctuary requires fortification against malevolent intrusions. Channel your ethical guardian protocols.',
        '⚔️ A vulnerability has been detected in the protective barriers. Your security mastery is needed to seal the breach.'
      ],
      mechanics_base: {
        base_xp: 100,
        diagnostic_bonus: 30,
        prevention_multiplier: 4.0,
        speed_bonus_threshold: 900
      }
    });
  }

  generateQuest(error_context: ErrorContext): ErrorQuest {
    const analysis = this.analyzer.analyzeError(error_context);
    const category = analysis.suggested_category;
    const template = this.quest_templates.get(category) || this.quest_templates.get('debugging_labyrinth');
    
    // Generate unique quest ID
    const quest_id = `${category}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    
    // Select random title and narrative
    const title = template.title_templates[Math.floor(Math.random() * template.title_templates.length)];
    const narrative = template.narrative_templates[Math.floor(Math.random() * template.narrative_templates.length)];
    
    // Generate solution paths based on error pattern
    const solution_paths = this.generateSolutionPaths(error_context, analysis.pattern_match);
    
    // Generate healing rituals
    const healing_rituals = this.generateHealingRituals(category);
    
    // Adjust mechanics based on difficulty
    const difficulty_multiplier = this.getDifficultyMultiplier(analysis.difficulty_assessment);
    const mechanics = {
      base_xp: Math.round(template.mechanics_base.base_xp * difficulty_multiplier),
      diagnostic_bonus: Math.round(template.mechanics_base.diagnostic_bonus * difficulty_multiplier),
      prevention_multiplier: template.mechanics_base.prevention_multiplier,
      speed_bonus_threshold: template.mechanics_base.speed_bonus_threshold
    };

    return {
      id: quest_id,
      title,
      error_context,
      quest_category: category as any,
      difficulty_tier: analysis.difficulty_assessment as any,
      narrative_frame: this.enhanceNarrativeWithContext(narrative, error_context),
      mechanics,
      solution_paths,
      healing_rituals
    };
  }

  private generateSolutionPaths(error_context: ErrorContext, pattern_match: any): Array<{
    method: string;
    description: string;
    steps: string[];
    xp_multiplier: number;
    cultivation_effects: string[];
    mastery_gained: number;
  }> {
    const base_paths = [
      {
        method: 'systematic_debugging',
        description: 'Use systematic debugging approach with careful analysis',
        steps: [
          'Read error message carefully and understand the context',
          'Locate the problematic code section',
          'Analyze surrounding code for clues',
          'Test potential solutions incrementally',
          'Verify the fix and add preventive measures'
        ],
        xp_multiplier: 1.5,
        cultivation_effects: ['debugging_mastery', 'systematic_thinking'],
        mastery_gained: 15
      },
      {
        method: 'collaborative_investigation',
        description: 'Seek wisdom from documentation, community, or AI assistance',
        steps: [
          'Research the error in official documentation',
          'Search for similar issues in community forums',
          'Consult AI assistance for insights',
          'Apply the most appropriate solution',
          'Document the solution for future reference'
        ],
        xp_multiplier: 1.2,
        cultivation_effects: ['knowledge_cultivation', 'wisdom_seeking'],
        mastery_gained: 10
      },
      {
        method: 'experimental_exploration',
        description: 'Learn through experimentation and trial-and-error',
        steps: [
          'Create a minimal reproduction of the error',
          'Try different approaches systematically',
          'Observe the effects of each change',
          'Build understanding through experimentation',
          'Apply the working solution with confidence'
        ],
        xp_multiplier: 1.8,
        cultivation_effects: ['creative_problem_solving', 'experiential_learning'],
        mastery_gained: 20
      }
    ];

    // Add pattern-specific solution if available
    if (pattern_match?.solution_templates) {
      base_paths.push({
        method: 'pattern_recognition',
        description: 'Apply known pattern-based solution',
        steps: pattern_match.solution_templates.concat([
          'Verify the solution addresses the root cause',
          'Test thoroughly to ensure no side effects'
        ]),
        xp_multiplier: 1.0,
        cultivation_effects: ['pattern_mastery', 'efficiency'],
        mastery_gained: 8
      });
    }

    return base_paths;
  }

  private generateHealingRituals(category: string): Array<{
    ritual: string;
    healing_power: number;
    cultivation_benefit: string;
  }> {
    const ritual_map = {
      syntax_surgery: [
        { ritual: 'lint_configuration_enhancement', healing_power: 5, cultivation_benefit: 'code_quality_improvement' },
        { ritual: 'style_guide_adherence', healing_power: 3, cultivation_benefit: 'consistency_cultivation' }
      ],
      debugging_labyrinth: [
        { ritual: 'unit_test_expansion', healing_power: 8, cultivation_benefit: 'confidence_building' },
        { ritual: 'logging_enhancement', healing_power: 6, cultivation_benefit: 'observability_improvement' }
      ],
      runtime_rescue: [
        { ritual: 'error_handling_fortification', healing_power: 10, cultivation_benefit: 'resilience_building' },
        { ritual: 'defensive_programming', healing_power: 7, cultivation_benefit: 'robustness_cultivation' }
      ],
      performance_pursuit: [
        { ritual: 'profiling_analysis', healing_power: 12, cultivation_benefit: 'performance_awareness' },
        { ritual: 'optimization_documentation', healing_power: 8, cultivation_benefit: 'knowledge_preservation' }
      ],
      security_sanctuary: [
        { ritual: 'security_audit_ceremony', healing_power: 15, cultivation_benefit: 'guardian_strengthening' },
        { ritual: 'vulnerability_assessment', healing_power: 12, cultivation_benefit: 'threat_awareness' }
      ]
    };

    return ritual_map[category as keyof typeof ritual_map] || ritual_map.debugging_labyrinth;
  }

  private getDifficultyMultiplier(difficulty: string): number {
    const multipliers = {
      novice: 1.0,
      apprentice: 1.3,
      adept: 1.6,
      master: 2.0,
      transcendent: 2.5
    };
    return multipliers[difficulty as keyof typeof multipliers] || 1.0;
  }

  private enhanceNarrativeWithContext(narrative: string, error_context: ErrorContext): string {
    const location = error_context.file_path 
      ? ` in ${error_context.file_path}${error_context.line_number ? `:${error_context.line_number}` : ''}`
      : ' in the digital realm';
    
    const severity_descriptor = {
      info: 'A gentle disturbance',
      warning: 'An ominous warning signal',
      error: 'A critical disruption',
      critical: 'A catastrophic anomaly'
    }[error_context.severity] || 'An unknown disturbance';

    return `${narrative}\n\n🎯 QUEST DETAILS:\n${severity_descriptor} has been detected${location}.\n\nError Message: "${error_context.message}"\n\nPrepare your debugging tools and channel your inner code warrior! 🗡️`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🎮 QUEST PROGRESSION MANAGER
// ═══════════════════════════════════════════════════════════════════════════════

export class ErrorQuestManager {
  private generator: ErrorQuestGenerator;
  private active_quests: Map<string, QuestProgress> = new Map();
  private completed_quests: Array<{ quest: ErrorQuest; progress: QuestProgress }> = [];
  
  constructor() {
    this.generator = new ErrorQuestGenerator();
    this.loadQuestData();
  }

  async transformErrorToQuest(error_context: ErrorContext): Promise<{
    quest: ErrorQuest;
    narrative: string;
    suggested_actions: string[];
  }> {
    const quest = this.generator.generateQuest(error_context);
    
    // Start quest progression tracking
    const progress: QuestProgress = {
      quest_id: quest.id,
      start_time: Date.now(),
      status: 'active'
    };
    
    this.active_quests.set(quest.id, progress);
    
    const narrative = `🎮 ERROR TRANSFORMED INTO QUEST!

${quest.narrative_frame}

🏆 POTENTIAL REWARDS:
• Base XP: ${quest.mechanics.base_xp}
• Diagnostic Bonus: +${quest.mechanics.diagnostic_bonus} XP
• Speed Bonus: Available if resolved within ${quest.mechanics.speed_bonus_threshold}s
• Prevention Multiplier: ${quest.mechanics.prevention_multiplier}x for implementing safeguards

🛠️ SOLUTION PATHS AVAILABLE:
${quest.solution_paths.map((path, index) => 
  `${index + 1}. ${path.method.replace('_', ' ').toUpperCase()}: ${path.description} (${path.xp_multiplier}x XP)`
).join('\n')}`;

    const suggested_actions = [
      'Begin diagnostic phase',
      'Choose your solution path',
      'Document your approach',
      'Implement the fix',
      'Perform healing rituals'
    ];

    this.saveQuestData();
    
    return { quest, narrative, suggested_actions };
  }

  async completeQuestDiagnostic(quest_id: string): Promise<{
    success: boolean;
    diagnostic_xp: number;
    next_phase: string;
  }> {
    const progress = this.active_quests.get(quest_id);
    if (!progress || progress.status !== 'active') {
      return { success: false, diagnostic_xp: 0, next_phase: '' };
    }

    progress.diagnostic_time = Date.now();
    progress.status = 'diagnostic';
    
    // Calculate diagnostic XP (base on the quest mechanics)
    // For now, we'll use a simple calculation
    const diagnostic_xp = 15; // This would be calculated based on quest mechanics
    
    this.saveQuestData();
    
    return {
      success: true,
      diagnostic_xp,
      next_phase: 'Begin implementing your chosen solution path'
    };
  }

  async completeQuest(quest_id: string, solution_method: string): Promise<{
    success: boolean;
    total_xp: number;
    cultivation_effects: string[];
    mastery_gained: number;
    completion_narrative: string;
    healing_recommendations: string[];
  }> {
    const progress = this.active_quests.get(quest_id);
    if (!progress) {
      return {
        success: false,
        total_xp: 0,
        cultivation_effects: [],
        mastery_gained: 0,
        completion_narrative: 'Quest not found',
        healing_recommendations: []
      };
    }

    // Mark quest as completed
    progress.resolution_time = Date.now();
    progress.solution_method = solution_method;
    progress.status = 'completed';

    // Calculate rewards (this would use the actual quest data)
    const base_xp = 50; // This would come from the quest
    const speed_bonus = this.calculateSpeedBonus(progress);
    const total_xp = Math.round(base_xp * (1 + speed_bonus));
    
    progress.xp_earned = total_xp;
    progress.cultivation_gained = Math.round(total_xp * 0.2);

    // Update mastery
    const category = 'debugging_labyrinth'; // This would come from the quest
    this.generator.analyzer.updateMastery(category, 10);

    const completion_narrative = `🎉 QUEST COMPLETED: ERROR VANQUISHED!

✨ Solution Method: ${solution_method.replace('_', ' ').toUpperCase()}
💫 XP Gained: ${total_xp} (including ${Math.round(base_xp * speed_bonus)} speed bonus)
🌱 Cultivation Gained: ${progress.cultivation_gained}
🎯 Mastery Improved: +10 ${category.replace('_', ' ')}

🏆 Your error-slaying prowess grows stronger with each challenge conquered!`;

    const healing_recommendations = [
      'Perform code quality healing ritual',
      'Add protective test coverage',
      'Document the solution for future reference'
    ];

    // Move to completed quests
    this.active_quests.delete(quest_id);
    // We would store the completed quest here
    
    this.saveQuestData();

    // Integrate with cultivation system
    await this.integrateWithCultivationSystem(solution_method, total_xp);

    return {
      success: true,
      total_xp,
      cultivation_effects: ['debugging_mastery', 'problem_solving'],
      mastery_gained: 10,
      completion_narrative,
      healing_recommendations
    };
  }

  private calculateSpeedBonus(progress: QuestProgress): number {
    if (!progress.diagnostic_time || !progress.resolution_time) return 0;
    
    const total_time = (progress.resolution_time - progress.start_time) / 1000; // seconds
    const speed_threshold = 300; // This would come from quest mechanics
    
    if (total_time <= speed_threshold) {
      return Math.max(0.5, 1 - (total_time / speed_threshold)) * 0.5; // Up to 50% bonus
    }
    
    return 0;
  }

  private async integrateWithCultivationSystem(solution_method: string, xp_gained: number): Promise<void> {
    try {
      // Integrate with the cultivation system
      if (solution_method.includes('systematic')) {
        await cultivationSystem.cultivation_fields.cultivateField('wisdom_garden', 'knowledge_synthesis', 10);
      }
      
      // Trigger healing based on the solution type
      if (solution_method.includes('test')) {
        await cultivationSystem.system_health.performHealing('test_cultivation');
      }
    } catch (error) {
      console.warn('Failed to integrate with cultivation system:', error);
    }
  }

  getActiveQuestsSummary(): string {
    const active_count = this.active_quests.size;
    const completed_count = this.completed_quests.length;
    
    return `🎮 ERROR QUEST DASHBOARD

📊 Quest Statistics:
• Active Quests: ${active_count}
• Completed Quests: ${completed_count}
• Success Rate: ${completed_count > 0 ? ((completed_count / (completed_count + active_count)) * 100).toFixed(1) : 0}%

🔥 Active Adventures:
${Array.from(this.active_quests.entries()).map(([id, progress]) => {
  const elapsed = ((Date.now() - progress.start_time) / 1000 / 60).toFixed(1);
  return `• ${id.slice(0, 20)}... (${progress.status}, ${elapsed}m ago)`;
}).join('\n') || 'No active quests - ready for new challenges!'}`;
  }

  private loadQuestData(): void {
    try {
      if (existsSync('.local/error-quests.json')) {
        const data = JSON.parse(readFileSync('.local/error-quests.json', 'utf8'));
        this.active_quests = new Map(data.active || []);
        this.completed_quests = data.completed || [];
      }
    } catch (error) {
      console.warn('Failed to load quest data:', error);
    }
  }

  private saveQuestData(): void {
    try {
      mkdirSync('.local', { recursive: true });
      writeFileSync('.local/error-quests.json', JSON.stringify({
        active: Array.from(this.active_quests.entries()),
        completed: this.completed_quests.slice(-50), // Keep last 50
        timestamp: Date.now()
      }, null, 2));
    } catch (error) {
      console.warn('Failed to save quest data:', error);
    }
  }
}

// Export the quest manager
export const errorQuestManager = new ErrorQuestManager();