import { createInterface } from 'readline';
import { step, getState, initializeEngine } from './loop';
import { renderPantheon } from './pantheon';
import { eventBus } from './bus';
import type { KPulseState } from '../../../shared/types/core';

let lastTick = Date.now();
let isRunning = false;

async function main() {
  console.log('🚀 KPulse Engine starting...');
  
  // Initialize engine state
  await initializeEngine();
  
  // Start game loop
  startGameLoop();
  
  // Setup CLI interface
  setupCLI();
  
  // Register RPC handlers
  registerRPCHandlers();
  
  console.log('✅ KPulse Engine ready');
  console.log('Press [SPACE] to pause/resume, [Q] to quit, [1-9] for actions');
}

function startGameLoop() {
  isRunning = true;
  
  const gameLoop = setInterval(() => {
    if (!isRunning) return;
    
    const now = Date.now();
    const dt = (now - lastTick) / 1000;
    lastTick = now;
    
    // Step the engine
    step(dt);
    
    // Emit tick event
    eventBus.emit({
      type: 'TICK',
      dt,
      timestamp: now
    });
    
    // Update display
    updateDisplay();
    
  }, parseInt(process.env.ENGINE_TICK_RATE || '250'));

  // Cleanup on exit
  process.on('SIGINT', () => {
    clearInterval(gameLoop);
    console.log('\n🛑 Engine stopped');
    process.exit(0);
  });
}

function updateDisplay() {
  if (process.env.ASCII_PANTHEON === 'true') {
    process.stdout.write('\x1bc'); // Clear screen
    process.stdout.write(renderPantheon(getState()));
  }
}

function setupCLI() {
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.setEncoding('utf8');
  
  process.stdin.on('data', (key) => {
    const char = key.toString();
    
    switch (char) {
      case ' ':
        isRunning = !isRunning;
        console.log(isRunning ? '▶️  Resumed' : '⏸️  Paused');
        break;
      case 'q':
      case '\u0003': // Ctrl+C
        process.exit(0);
        break;
      case '1':
        handleAction('build_outpost');
        break;
      case '2':
        handleAction('scout_area');
        break;
      case '3':
        handleAction('automate_system');
        break;
      case '4':
        handleAction('research_tech');
        break;
      case '5':
        handleAction('story_event');
        break;
      case '6':
        handleAction('advance_tier');
        break;
      case '7':
        handleAction('spawn_directive');
        break;
      case '8':
        handleAction('save_state');
        break;
      case '9':
        handleAction('analytics');
        break;
    }
  });
}

function handleAction(action: string) {
  const state = getState();
  
  eventBus.emit({
    type: 'UI.CLICK',
    node: `action.${action}`,
    data: { timestamp: Date.now() }
  });
  
  switch (action) {
    case 'build_outpost':
      if (state.resources.metal >= 100) {
        state.resources.metal -= 100;
        console.log('🏗️  Building outpost...');
      } else {
        console.log('❌ Insufficient metal (need 100)');
      }
      break;
      
    case 'scout_area':
      if (state.resources.power >= 20) {
        state.resources.power -= 20;
        const discovered = Math.floor(Math.random() * 50);
        state.resources.metal += discovered;
        console.log(`🔍 Scouted area, found ${discovered} metal`);
      } else {
        console.log('❌ Insufficient power (need 20)');
      }
      break;
      
    case 'automate_system':
      console.log('🤖 Automation system activated');
      break;
      
    case 'research_tech':
      if (state.resources.knowledge >= 50) {
        state.resources.knowledge -= 50;
        console.log('🔬 Research project started');
      } else {
        console.log('❌ Insufficient knowledge (need 50)');
      }
      break;
      
    case 'story_event':
      eventBus.emit({
        type: 'STORY.EVENT',
        id: `event_${Date.now()}`,
        phase: Math.floor(Math.random() * 16),
        payload: { trigger: 'manual', source: 'cli' }
      });
      console.log('📖 Story event triggered');
      break;
      
    case 'advance_tier':
      if (state.tier < 19) {
        const oldTier = state.tier;
        state.tier++;
        eventBus.emit({
          type: 'TIER.ADVANCE',
          fromTier: oldTier,
          toTier: state.tier
        });
        console.log(`⬆️  Advanced to Tier ${state.tier}`);
      }
      break;
      
    case 'spawn_directive':
      if (state.tier >= 8) {
        eventBus.emit({
          type: 'DIRECTIVE.SPAWNED',
          path: `directive_${Date.now()}.yml`,
          tier: state.tier
        });
        console.log('📜 Directive spawned');
      } else {
        console.log('❌ Tier 8+ required for directive spawning');
      }
      break;
      
    case 'save_state':
      console.log('💾 State saved');
      break;
      
    case 'analytics':
      const events = eventBus.getEventLog(10);
      console.log(`📊 Recent events: ${events.length}`);
      break;
  }
}

function registerRPCHandlers() {
  eventBus.registerHandler('engine.step', async (dt: number) => {
    step(dt);
  });
  
  eventBus.registerHandler('engine.getState', async () => {
    return getState();
  });
  
  eventBus.registerHandler('engine.saveState', async (hash: string) => {
    const state = getState();
    console.log(`💾 State saved with hash: ${hash}`);
    return { success: true, hash };
  });
  
  eventBus.registerHandler('ui.build', async (buildingType: string) => {
    const state = getState();
    const cost = getBuildingCost(buildingType);
    
    if (canAfford(state, cost)) {
      deductResources(state, cost);
      return { success: true, cost };
    } else {
      return { success: false, cost, reason: 'Insufficient resources' };
    }
  });
  
  eventBus.registerHandler('ui.research', async (researchId: string) => {
    const state = getState();
    // Implementation for research
    return { started: true, duration: 300 };
  });
  
  eventBus.registerHandler('ui.scout', async (area: string) => {
    const state = getState();
    const discovered = Math.floor(Math.random() * 100);
    state.resources.metal += discovered;
    
    eventBus.emit({
      type: 'METRICS.RESOURCE',
      key: 'metal_discovered',
      value: discovered,
      t: Date.now()
    });
    
    return { discovered: { area }, resources: discovered };
  });
}

function getBuildingCost(type: string): any {
  const costs = {
    outpost: { metal: 100, power: 50 },
    generator: { metal: 75, knowledge: 25 },
    lab: { metal: 150, power: 100, knowledge: 50 }
  };
  return costs[type as keyof typeof costs] || { metal: 50 };
}

function canAfford(state: KPulseState, cost: any): boolean {
  for (const [resource, amount] of Object.entries(cost)) {
    if ((state.resources as any)[resource] < (amount as number)) {
      return false;
    }
  }
  return true;
}

function deductResources(state: KPulseState, cost: any) {
  for (const [resource, amount] of Object.entries(cost)) {
    (state.resources as any)[resource] -= (amount as number);
  }
}

// Start the engine
main().catch(console.error);