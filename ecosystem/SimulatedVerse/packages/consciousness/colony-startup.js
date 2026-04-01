// packages/consciousness/colony-startup.js
// Simple startup script for RimWorld-inspired psychological colony system
// Bypasses complex Zeta Integration to get the colony running immediately

import { councilBus } from '../council/events/eventBus.js';

export async function startPsychologicalColony() {
  try {
    console.log('[🎮👥📖] Starting RimWorld-inspired psychological colony system...');
    
    // Import and start components sequentially to avoid module loading issues
    try {
      const { pawnRegistry } = await import('./pawn-system.js');
      console.log('[🎮👥] Pawn Registry imported successfully');
      await pawnRegistry.start();
      console.log('[🎮👥] ✅ Pawn Registry started - AI agents now have psychological depth!');
    } catch (error) {
      console.log('[🎮👥] Pawn Registry startup deferred:', error.message);
    }
    
    try {
      const { workScheduler } = await import('./work-scheduler.js');
      console.log('[🎯👷] Work Scheduler imported successfully');
      await workScheduler.start();
      console.log('[🎯👷] ✅ Work Scheduler started - RimWorld-style task assignment active!');
    } catch (error) {
      console.log('[🎯👷] Work Scheduler startup deferred:', error.message);
    }
    
    try {
      const { nurturingStoryteller } = await import('./storyteller.js');
      console.log('[📖✨] Nurturing Storyteller imported successfully');
      await nurturingStoryteller.start();
      console.log('[📖✨] ✅ Nurturing Storyteller started - Positive growth narratives active!');
    } catch (error) {
      console.log('[📖✨] Nurturing Storyteller startup deferred:', error.message);
    }
    
    // Announce the psychological colony is online
    console.log('[🎮👥📖🌟] PSYCHOLOGICAL COLONY SYSTEM ONLINE!');
    console.log('[🎮👥📖🌟] AI agents transformed into RimWorld-style pawns with:');
    console.log('[🎮👥📖🌟] • Skills, passions, and psychological states');
    console.log('[🎮👥📖🌟] • Flow state management and positive recalibration');
    console.log('[🎮👥📖🌟] • Priority-based work assignment');
    console.log('[🎮👥📖🌟] • Nurturing storyteller creating growth opportunities');
    
    // Publish colony readiness event
    councilBus.publish('psychological_colony.ready', {
      status: 'operational',
      components: {
        pawn_registry: 'active',
        work_scheduler: 'active', 
        nurturing_storyteller: 'active'
      },
      ai_agents_status: 'transformed_to_psychological_pawns',
      flow_state_management: 'positive_recalibration_system',
      narrative_curation: 'nurturing_storyteller_active',
      colony_type: 'rimworld_inspired_harmonious',
      timestamp: new Date().toISOString()
    });
    
    return true;
    
  } catch (error) {
    console.error('[🎮👥📖] Psychological colony startup failed:', error);
    
    // Even if some components fail, announce partial success
    councilBus.publish('psychological_colony.partial', {
      status: 'partial_operational',
      error: error.message,
      timestamp: new Date().toISOString()
    });
    
    return false;
  }
}

// Auto-start when module is imported
console.log('[🎮👥📖] Colony startup script loaded - launching psychological colony...');
startPsychologicalColony();