import fs from 'fs';
import path from 'path';
import yaml from 'yaml';
import type { KPulseState, Directive } from '../../../shared/types/core';
import { eventBus } from './application-services/engine/src/bus.ts';

let lastSpawnTime = 0;
const SPAWN_COOLDOWN = 30000; // 30 seconds between spawns

export function spawnIfEligible(state: KPulseState) {
  const now = Date.now();
  if (now - lastSpawnTime < SPAWN_COOLDOWN) return;
  
  // Check spawning conditions
  if (state.tier >= 8 && state.resources.power > 1000 && state.resources.knowledge > 500) {
    spawnDirective(state);
    lastSpawnTime = now;
  }
}

function spawnDirective(state: KPulseState) {
  const directiveType = selectDirectiveType(state);
  const directive = generateDirective(directiveType, state);
  
  // Validate against schema
  if (!validateDirective(directive)) {
    console.error('Generated directive failed validation');
    return;
  }
  
  // Write to content directory
  const fileName = `${directive.id}.yml`;
  const filePath = path.join(process.cwd(), 'content', 'directives', fileName);
  
  // Ensure directory exists
  const dirPath = path.dirname(filePath);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  
  // Write YAML file
  const yamlContent = yaml.stringify(directive);
  fs.writeFileSync(filePath, yamlContent);
  
  console.log(`📜 Directive spawned: ${fileName}`);
  
  // Emit event
  eventBus.emit({
    type: 'DIRECTIVE.SPAWNED',
    path: fileName,
    tier: state.tier
  });
  
  // Apply directive effects immediately if conditions are met
  applyDirective(directive, state);
}

function selectDirectiveType(state: KPulseState): string {
  const weights = {
    building: 0.4,
    upgrade: 0.3,
    subsystem: 0.2,
    event: 0.1
  };
  
  // Adjust weights based on state
  if (Object.keys(state.buildings).length < 5) {
    weights.building = 0.6;
  }
  
  if (state.tier >= 10) {
    weights.subsystem = 0.4;
    weights.event = 0.2;
  }
  
  const random = Math.random();
  let cumulative = 0;
  
  for (const [type, weight] of Object.entries(weights)) {
    cumulative += weight;
    if (random <= cumulative) {
      return type;
    }
  }
  
  return 'building';
}

function generateDirective(type: string, state: KPulseState): Directive {
  const id = `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  
  switch (type) {
    case 'building':
      return generateBuildingDirective(id, state);
    case 'upgrade':
      return generateUpgradeDirective(id, state);
    case 'subsystem':
      return generateSubsystemDirective(id, state);
    case 'event':
      return generateEventDirective(id, state);
    default:
      return generateBuildingDirective(id, state);
  }
}

function generateBuildingDirective(id: string, state: KPulseState): Directive {
  const buildingTypes = [
    'quantum_reactor',
    'reality_anchor',
    'consciousness_matrix',
    'dimensional_gateway',
    'entropy_reverser',
    'probability_manipulator',
    'time_dilation_chamber',
    'universal_constructor'
  ];
  
  const buildingType = buildingTypes[Math.floor(Math.random() * buildingTypes.length)];
  const powerMultiplier = 1.1 + (Math.random() * 0.3); // 1.1x - 1.4x
  
  return {
    id,
    kind: 'building',
    tier: state.tier,
    unlock: {
      tier: state.tier,
      resources: {
        metal: Math.floor(state.resources.metal * 0.8),
        power: Math.floor(state.resources.power * 0.6),
        exotic: Math.floor(state.resources.exotic * 0.5)
      }
    },
    effects: [
      {
        type: 'multiplier',
        target: 'power',
        value: powerMultiplier
      },
      {
        type: 'unlock',
        target: 'building_type',
        value: buildingType
      }
    ],
    metadata: {
      spawned: Date.now(),
      validated: true,
      active: false
    }
  };
}

function generateUpgradeDirective(id: string, state: KPulseState): Directive {
  const upgradeTargets = ['efficiency', 'capacity', 'speed', 'range', 'precision'];
  const target = upgradeTargets[Math.floor(Math.random() * upgradeTargets.length)];
  const bonus = 0.15 + (Math.random() * 0.2); // 15% - 35% improvement
  
  return {
    id,
    kind: 'upgrade',
    tier: state.tier,
    unlock: {
      tier: state.tier - 1,
      knowledge: Math.floor(state.resources.knowledge * 0.4)
    },
    effects: [
      {
        type: 'multiplier',
        target: `global_${target}`,
        value: 1 + bonus
      }
    ],
    metadata: {
      spawned: Date.now(),
      validated: true,
      active: false
    }
  };
}

function generateSubsystemDirective(id: string, state: KPulseState): Directive {
  const subsystems = [
    'neural_network_optimizer',
    'quantum_entanglement_coordinator',
    'reality_stability_monitor',
    'consciousness_backup_protocol',
    'temporal_anomaly_detector'
  ];
  
  const subsystem = subsystems[Math.floor(Math.random() * subsystems.length)];
  
  return {
    id,
    kind: 'subsystem',
    tier: state.tier,
    unlock: {
      tier: state.tier,
      research: [`advanced_${subsystem.split('_')[0]}`]
    },
    effects: [
      {
        type: 'additive',
        target: 'automation_efficiency',
        value: 0.25
      },
      {
        type: 'spawn',
        target: 'subsystem',
        value: subsystem
      }
    ],
    metadata: {
      spawned: Date.now(),
      validated: true,
      active: false
    }
  };
}

function generateEventDirective(id: string, state: KPulseState): Directive {
  const events = [
    'dimensional_rift_detected',
    'ancient_artifact_discovered',
    'parallel_universe_contact',
    'consciousness_awakening',
    'reality_cascade_event'
  ];
  
  const eventType = events[Math.floor(Math.random() * events.length)];
  
  return {
    id,
    kind: 'event',
    tier: state.tier,
    unlock: {
      tier: state.tier,
      time: Date.now() + (Math.random() * 3600000) // Random time in next hour
    },
    effects: [
      {
        type: 'modify',
        target: 'narrative_intensity',
        value: 7
      },
      {
        type: 'spawn',
        target: 'story_event',
        value: eventType
      }
    ],
    metadata: {
      spawned: Date.now(),
      validated: true,
      active: false
    }
  };
}

function validateDirective(directive: Directive): boolean {
  // Basic validation - in production this would use JSON Schema
  if (!directive.id || !directive.kind || !directive.tier) {
    return false;
  }
  
  if (!directive.unlock) {
    return false;
  }
  
  if (!Array.isArray(directive.effects) || directive.effects.length === 0) {
    return false;
  }
  
  return true;
}

function applyDirective(directive: Directive, state: KPulseState) {
  // Check if unlock conditions are met
  if (!checkUnlockConditions(directive.unlock, state)) {
    return;
  }
  
  console.log(`🎯 Applying directive: ${directive.id}`);
  
  // Apply effects
  directive.effects.forEach(effect => {
    switch (effect.type) {
      case 'multiplier':
        applyMultiplierEffect(effect, state);
        break;
      case 'additive':
        applyAdditiveEffect(effect, state);
        break;
      case 'unlock':
        applyUnlockEffect(effect, state);
        break;
      case 'spawn':
        applySpawnEffect(effect, state);
        break;
      case 'modify':
        applyModifyEffect(effect, state);
        break;
    }
  });
  
  directive.metadata.active = true;
}

function checkUnlockConditions(unlock: any, state: KPulseState): boolean {
  if (unlock.tier && state.tier < unlock.tier) {
    return false;
  }
  
  if (unlock.resources) {
    for (const [resource, amount] of Object.entries(unlock.resources)) {
      if ((state.resources as any)[resource] < amount) {
        return false;
      }
    }
  }
  
  if (unlock.research) {
    for (const researchId of unlock.research) {
      if (!state.research.completed.has(researchId)) {
        return false;
      }
    }
  }
  
  if (unlock.time && Date.now() < unlock.time) {
    return false;
  }
  
  return true;
}

function applyMultiplierEffect(effect: any, state: KPulseState) {
  // This would modify production rates, efficiency, etc.
  console.log(`📈 Multiplier applied: ${effect.target} x${effect.value}`);
}

function applyAdditiveEffect(effect: any, state: KPulseState) {
  // This would add flat bonuses
  console.log(`➕ Additive bonus: ${effect.target} +${effect.value}`);
}

function applyUnlockEffect(effect: any, state: KPulseState) {
  // This would unlock new buildings, research, etc.
  console.log(`🔓 Unlocked: ${effect.target} = ${effect.value}`);
}

function applySpawnEffect(effect: any, state: KPulseState) {
  // This would create new entities
  console.log(`🆕 Spawned: ${effect.target} = ${effect.value}`);
}

function applyModifyEffect(effect: any, state: KPulseState) {
  // This would modify existing values
  console.log(`🔧 Modified: ${effect.target} = ${effect.value}`);
}