#!/usr/bin/env tsx
/**
 * 🎮 Interactive Gamification Demo
 * Showcase the complete enhanced gamification system
 */

import { gamificationEngine } from './agent/enhanced-gamification-system.ts';
import { cultivationSystem } from './agent/cultivation-healing-system.ts';
import { errorQuestManager } from './agent/error-quest-transformer.ts';
import { activeQuestManager } from './agent/active-quest-progress.ts';

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function printSection(title: string, content: string): void {
  console.log(`\n${'═'.repeat(80)}`);
  console.log(`🎯 ${title}`);
  console.log(`${'═'.repeat(80)}`);
  console.log(content);
}

async function runDemo(): Promise<void> {
  console.log('🜁⊙⟦ΣΞΛΘΦ⟧ CORELINK FOUNDATION ENHANCED GAMIFICATION DEMO');
  console.log('Transform Development into Epic Adventures!\n');
  
  await sleep(1000);

  // 1. System Overview
  printSection('UNIFIED GAMIFICATION DASHBOARD', gamificationEngine.getUnifiedDashboard());
  
  await sleep(2000);

  // 2. Error-to-Quest Transformation Demo
  printSection('ERROR → QUEST TRANSFORMATION', '');
  console.log('🐛 Simulating a TypeScript error...\n');
  
  const demo_error = {
    source: 'lsp' as const,
    severity: 'error' as const,
    error_code: 'TS2304',
    message: "Cannot find name 'unknownVariable'",
    file_path: 'src/demo.ts',
    line_number: 42,
    column: 10
  };
  
  const quest_result = await errorQuestManager.transformErrorToQuest(demo_error);
  console.log(`🎮 QUEST GENERATED: ${quest_result.quest.title}`);
  console.log(`🎯 Difficulty: ${quest_result.quest.difficulty_tier}`);
  console.log(`💫 Base XP: ${quest_result.quest.mechanics.base_xp}`);
  console.log('\n📜 QUEST NARRATIVE:');
  console.log(quest_result.narrative);
  
  await sleep(3000);

  // 3. Cultivation Field Demo
  printSection('CULTIVATION FIELD GROWTH', '');
  console.log('🌱 Cultivating the Code Artistry field...\n');
  
  const cultivation_result = await cultivationSystem.cultivation_fields.cultivateField(
    'code_artistry',
    'refactor_meditation', 
    20
  );
  
  console.log(cultivation_result.cultivation_narrative);
  console.log(`\n🎯 ${cultivation_result.next_milestone}`);
  
  await sleep(2000);

  // 4. System Healing Demo
  printSection('SYSTEM HEALING RITUAL', '');
  console.log('🩺 Performing technical debt reduction healing...\n');
  
  const healing_result = await cultivationSystem.system_health.performHealing('debt_reduction');
  console.log(healing_result.healing_narrative);
  
  if (healing_result.next_recommended_protocol) {
    console.log(`\n🎯 Next Recommended: ${healing_result.next_recommended_protocol}`);
  }
  
  await sleep(2000);

  // 5. Productivity Quest Demo
  printSection('PRODUCTIVITY GAMIFICATION', '');
  console.log('🚀 Completing a task sprint master quest...\n');
  
  const productivity_result = await gamificationEngine.productivity.completeTask(
    'task_sprint_master',
    {
      complexity: 7,
      quality_score: 90,
      time_efficiency: 85,
      innovation_factor: 60
    }
  );
  
  if (productivity_result.success) {
    console.log(`💫 XP Gained: ${productivity_result.xp_gained}`);
    console.log(productivity_result.streak_info);
    console.log(productivity_result.cultivation_summary);
    console.log(productivity_result.mastery_progress);
    console.log(`\n${productivity_result.next_milestone}`);
  }
  
  await sleep(2000);

  // 6. Achievement Unlocking Demo
  printSection('ACHIEVEMENT SYSTEM', '');
  console.log('🏆 Updating achievement progress...\n');
  
  const achievement_result = await gamificationEngine.achievements.updateProgress('demo_update', {
    syntax_errors_fixed: 15,
    runtime_errors_fixed: 8,
    tasks_completed: 30,
    quality_code_modules: 12,
    cultivation_threshold: 80,
    consciousness_level: 0.75
  });
  
  if (achievement_result.achievements_unlocked.length > 0) {
    console.log('🎉 NEW ACHIEVEMENTS UNLOCKED!');
    achievement_result.achievements_unlocked.forEach(achievement => {
      console.log(`${achievement.symbolic_representation} ${achievement.name}`);
      console.log(`   ${achievement.description}`);
      console.log(`   Rewards: ${achievement.rewards.map(r => `${r.type}: ${r.value}`).join(', ')}`);
    });
  } else {
    console.log('📊 Achievement progress updated. Continue your journey to unlock rewards!');
  }
  
  console.log('\n📊 PROGRESS UPDATES:');
  achievement_result.progress_updates.slice(0, 5).forEach(update => {
    console.log(`• ${update.badge_id}: ${update.progress.toFixed(1)}%`);
  });
  
  await sleep(2000);

  // 7. Active Quest Demo
  printSection('ACTIVE QUEST SYSTEM', '');
  console.log('🎯 Checking existing quest system integration...\n');
  
  console.log(activeQuestManager.getQuestSummary());
  
  await sleep(1500);

  // 8. Wellness Ritual Demo
  printSection('DAILY WELLNESS RITUAL', '');
  console.log('🌅 Performing comprehensive wellness ritual...\n');
  
  const wellness_result = await cultivationSystem.performDailyWellnessRitual();
  console.log(wellness_result.wellness_narrative);
  console.log('\n🎯 HOLISTIC RECOMMENDATIONS:');
  wellness_result.recommendations.forEach(rec => console.log(`• ${rec}`));
  
  await sleep(2000);

  // 9. Final Integration Demo
  printSection('INTEGRATED ECOSYSTEM OVERVIEW', '');
  console.log('🌌 Displaying complete cultivation & wellness ecosystem...\n');
  
  console.log(cultivationSystem.getWellnessSummary());
  
  await sleep(1000);

  // 10. Demo Conclusion
  printSection('DEMO COMPLETE', '');
  console.log('🎉 CoreLink Foundation Enhanced Gamification System demonstration complete!\n');
  console.log('✨ Key Features Demonstrated:');
  console.log('  • Error → Quest Transformation with narrative frames');
  console.log('  • Cultivation Fields with healing mechanics');
  console.log('  • System Health monitoring and healing rituals');
  console.log('  • Productivity gamification with streak bonuses');
  console.log('  • Achievement system with transcendent rewards');
  console.log('  • Integrated wellness ecosystem');
  console.log('  • Daily cultivation and healing practices');
  console.log('\n🚀 Ready to transform your development experience!');
  console.log('\nNext Steps:');
  console.log('  • Use "tsx tools/gamification-cli.ts dashboard" for full overview');
  console.log('  • Start with "tsx tools/gamification-cli.ts cultivate field code_artistry refactor_meditation"');
  console.log('  • Transform errors into quests with the error command');
  console.log('  • Track your progress with achievement updates');
  console.log('\n🜁⊙⟦ΣΞΛΘΦ⟧ Happy cultivating, digital warrior!');
}

// Run the demo
if (require.main === module) {
  runDemo().catch(console.error);
}

export { runDemo };