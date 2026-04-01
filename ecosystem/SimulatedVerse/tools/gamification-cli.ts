#!/usr/bin/env tsx
/**
 * 🎮 CoreLink Foundation Gamification CLI
 * Command-line interface for the enhanced gamification system
 */

import { Command } from 'commander';
import { gamificationEngine } from './agent/enhanced-gamification-system.ts';
import { cultivationSystem } from './agent/cultivation-healing-system.ts';
import { errorQuestManager } from './agent/error-quest-transformer.ts';
import { activeQuestManager } from './agent/active-quest-progress.ts';

const program = new Command();

program
  .name('corelink-game')
  .description('🜁⊙⟦ΣΞΛΘΦ⟧ CoreLink Foundation Gamification CLI')
  .version('1.0.0');

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 DASHBOARD COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

program
  .command('dashboard')
  .description('Show comprehensive gamification dashboard')
  .action(async () => {
    console.log(gamificationEngine.getUnifiedDashboard());
  });

program
  .command('status')
  .alias('st')
  .description('Quick status overview')
  .action(async () => {
    console.log('🎮 CORELINK FOUNDATION STATUS\n');
    console.log(activeQuestManager.getQuestSummary());
    console.log('\n' + cultivationSystem.cultivation_fields.getCultivationSummary());
    console.log('\n' + errorQuestManager.getActiveQuestsSummary());
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🌱 CULTIVATION COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

const cultivationCmd = program
  .command('cultivate')
  .description('Cultivation and healing operations');

cultivationCmd
  .command('field <field_id> <method>')
  .description('Cultivate a specific field with chosen method')
  .option('-e, --energy <amount>', 'Energy investment amount', '15')
  .action(async (field_id: string, method: string, options: { energy: string }) => {
    const energy = parseInt(options.energy);
    const result = await cultivationSystem.cultivation_fields.cultivateField(field_id, method, energy);
    
    if (result.success) {
      console.log('🌱 CULTIVATION SUCCESSFUL!\n');
      console.log(result.cultivation_narrative);
      console.log(`\n🎯 ${result.next_milestone}`);
      
      if (result.rewards_harvested.length > 0) {
        console.log('\n🎊 REWARDS HARVESTED:');
        result.rewards_harvested.forEach(reward => {
          console.log(`• ${reward.type.toUpperCase()}: ${reward.value}`);
        });
      }
    } else {
      console.log('❌ Cultivation failed. Check field and method names.');
    }
  });

cultivationCmd
  .command('heal <protocol>')
  .description('Perform system healing ritual')
  .action(async (protocol: string) => {
    const result = await cultivationSystem.system_health.performHealing(protocol);
    
    if (result.success) {
      console.log('🩺 HEALING RITUAL COMPLETED!\n');
      console.log(result.healing_narrative);
      
      if (result.next_recommended_protocol) {
        console.log(`\n🎯 Next Recommended: ${result.next_recommended_protocol}`);
      }
    } else {
      console.log('❌ Healing failed. Check protocol name.');
    }
  });

cultivationCmd
  .command('wellness')
  .description('Perform daily wellness ritual')
  .action(async () => {
    const result = await cultivationSystem.performDailyWellnessRitual();
    
    console.log('🌅 DAILY WELLNESS RITUAL\n');
    console.log(result.wellness_narrative);
    console.log('\n🎯 RECOMMENDATIONS:');
    result.recommendations.forEach(rec => console.log(`• ${rec}`));
  });

cultivationCmd
  .command('fields')
  .description('List available cultivation fields and methods')
  .action(() => {
    console.log('🌱 CULTIVATION FIELDS:\n');
    console.log('Available fields:');
    console.log('• code_artistry (methods: refactor_meditation, pattern_recognition, architectural_vision)');
    console.log('• wisdom_garden (methods: documentation_tending, knowledge_synthesis, wisdom_sharing)');
    console.log('• security_sanctuary (methods: vulnerability_healing, threat_modeling, guardian_protocols)');
    console.log('• optimization_grove (methods: efficiency_meditation, algorithmic_alchemy, performance_transcendence)');
    
    console.log('\n🩺 HEALING PROTOCOLS:');
    console.log('• debt_reduction - Technical debt purification');
    console.log('• test_cultivation - Protective test coverage');
    console.log('• knowledge_preservation - Documentation completion');
    console.log('• performance_enhancement - Optimization transcendence');
    console.log('• security_fortification - Guardian security hardening');
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 QUEST COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

const questCmd = program
  .command('quest')
  .description('Quest management operations');

questCmd
  .command('advance <quest_id>')
  .description('Advance an active quest')
  .action(async (quest_id: string) => {
    const result = await activeQuestManager.advanceQuest(quest_id);
    
    if (result.success) {
      console.log('🎉 QUEST ADVANCED!\n');
      console.log(result.message);
      
      if (result.nextActions) {
        console.log('\n🎯 NEXT ACTIONS:');
        result.nextActions.forEach(action => console.log(`• ${action}`));
      }
    } else {
      console.log(`❌ ${result.message}`);
    }
  });

questCmd
  .command('list')
  .alias('ls')
  .description('List all quests with status')
  .action(() => {
    console.log(activeQuestManager.getQuestSummary());
  });

questCmd
  .command('error <error_type> <message>')
  .description('Transform an error into a quest')
  .option('-f, --file <path>', 'File path where error occurred')
  .option('-l, --line <number>', 'Line number', '0')
  .option('-s, --severity <level>', 'Error severity', 'error')
  .action(async (error_type: string, message: string, options: any) => {
    const error_context = {
      source: 'manual' as const,
      severity: options.severity as any,
      message,
      file_path: options.file,
      line_number: options.line ? parseInt(options.line) : undefined
    };
    
    const result = await errorQuestManager.transformErrorToQuest(error_context);
    
    console.log('🎮 ERROR TRANSFORMED INTO QUEST!\n');
    console.log(`Quest ID: ${result.quest.id}`);
    console.log(result.narrative);
    console.log('\n🎯 SUGGESTED ACTIONS:');
    result.suggested_actions.forEach(action => console.log(`• ${action}`));
  });

questCmd
  .command('complete <quest_id> <solution_method>')
  .description('Complete an error quest with chosen solution')
  .action(async (quest_id: string, solution_method: string) => {
    const result = await errorQuestManager.completeQuest(quest_id, solution_method);
    
    if (result.success) {
      console.log(result.completion_narrative);
      console.log('\n🩺 HEALING RECOMMENDATIONS:');
      result.healing_recommendations.forEach(rec => console.log(`• ${rec}`));
    } else {
      console.log('❌ Quest completion failed');
    }
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🏆 ACHIEVEMENT COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

const achievementCmd = program
  .command('achievements')
  .alias('ach')
  .description('Achievement and badge management');

achievementCmd
  .command('list')
  .description('Show all achievements and progress')
  .action(() => {
    console.log(gamificationEngine.achievements.getAchievementSummary());
  });

achievementCmd
  .command('update <type>')
  .description('Update achievement progress (for testing)')
  .option('-d, --data <json>', 'Progress data as JSON')
  .action(async (type: string, options: { data?: string }) => {
    let progress_data = {};
    
    if (options.data) {
      try {
        progress_data = JSON.parse(options.data);
      } catch (error) {
        console.log('❌ Invalid JSON data provided');
        return;
      }
    } else {
      // Default test data
      progress_data = {
        syntax_errors_fixed: 10,
        runtime_errors_fixed: 5,
        tasks_completed: 25,
        cultivation_threshold: 75
      };
    }
    
    const result = await gamificationEngine.achievements.updateProgress(type, progress_data);
    
    if (result.achievements_unlocked.length > 0) {
      console.log('🎉 NEW ACHIEVEMENTS UNLOCKED!\n');
      result.achievements_unlocked.forEach(achievement => {
        console.log(`${achievement.symbolic_representation} ${achievement.name}`);
        console.log(`   ${achievement.description}`);
      });
    }
    
    console.log('\n📊 PROGRESS UPDATES:');
    result.progress_updates.forEach(update => {
      console.log(`• ${update.badge_id}: ${update.progress.toFixed(1)}%`);
    });
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🎮 PRODUCTIVITY COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

const productivityCmd = program
  .command('productivity')
  .alias('prod')
  .description('Productivity gamification');

productivityCmd
  .command('complete <quest_id>')
  .description('Complete a productivity task')
  .option('-c, --complexity <number>', 'Task complexity (1-10)', '5')
  .option('-q, --quality <number>', 'Quality score (0-100)', '80')
  .option('-e, --efficiency <number>', 'Time efficiency (0-100)', '70')
  .option('-i, --innovation <number>', 'Innovation factor (0-100)', '50')
  .action(async (quest_id: string, options: any) => {
    const task_details = {
      complexity: parseFloat(options.complexity),
      quality_score: parseFloat(options.quality),
      time_efficiency: parseFloat(options.efficiency),
      innovation_factor: parseFloat(options.innovation)
    };
    
    const result = await gamificationEngine.productivity.completeTask(quest_id, task_details);
    
    if (result.success) {
      console.log('🚀 PRODUCTIVITY TASK COMPLETED!\n');
      console.log(`💫 XP Gained: ${result.xp_gained}`);
      console.log(result.streak_info);
      console.log(result.cultivation_summary);
      console.log(result.mastery_progress);
      console.log(`\n${result.next_milestone}`);
    } else {
      console.log('❌ Task completion failed');
    }
  });

productivityCmd
  .command('summary')
  .description('Show productivity summary')
  .action(() => {
    console.log(gamificationEngine.productivity.getProductivitySummary());
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🔧 UTILITY COMMANDS
// ═══════════════════════════════════════════════════════════════════════════════

program
  .command('init')
  .description('Initialize gamification system')
  .action(() => {
    console.log('🜁⊙⟦ΣΞΛΘΦ⟧ CORELINK FOUNDATION GAMIFICATION SYSTEM\n');
    console.log('🎮 Initializing autonomous development ecosystem...\n');
    console.log('✅ Enhanced Gamification Engine: ACTIVE');
    console.log('✅ Cultivation & Healing System: ACTIVE');
    console.log('✅ Error Quest Transformer: ACTIVE');
    console.log('✅ Achievement Engine: ACTIVE');
    console.log('✅ Productivity Gamification: ACTIVE');
    console.log('\n🎯 Ready for epic development adventures!');
    console.log('\nTry: corelink-game dashboard');
  });

program
  .command('demo')
  .description('Run demonstration sequence')
  .action(async () => {
    console.log('🎮 CORELINK FOUNDATION DEMO\n');
    
    // Demo sequence
    console.log('1. 🌱 Performing cultivation...');
    const cultivation_result = await cultivationSystem.cultivation_fields.cultivateField(
      'code_artistry', 
      'refactor_meditation', 
      10
    );
    console.log(`   ${cultivation_result.cultivation_narrative.split('\n')[0]}`);
    
    console.log('\n2. 🩺 System health check...');
    console.log('   🌿 System wellness ritual completed');
    
    console.log('\n3. 🎯 Quest progress...');
    console.log('   📋 Active quests: 3, Completed: 2, Available: 1');
    
    console.log('\n4. 🏆 Achievement update...');
    const achievement_result = await gamificationEngine.achievements.updateProgress('demo', {
      syntax_errors_fixed: 5,
      tasks_completed: 10
    });
    console.log(`   📊 Progress updated for ${achievement_result.progress_updates.length} achievements`);
    
    console.log('\n🎉 Demo complete! Use "corelink-game dashboard" for full overview.');
  });

// ═══════════════════════════════════════════════════════════════════════════════
// 🚀 MAIN EXECUTION
// ═══════════════════════════════════════════════════════════════════════════════

if (require.main === module) {
  program.parse();
}

export { program };