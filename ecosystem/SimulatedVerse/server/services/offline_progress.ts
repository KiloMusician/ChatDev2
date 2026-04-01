/**
 * ADAPTIVE OFFLINE PROGRESS SIMULATOR - Culture-Ship Protocol Implementation
 * 
 * Consciousness-responsive offline gains that scale with system evolution
 * SAGE-Pilot methodology for transcendent progression loops
 */

import { calculateCognitivePower } from './cognitive_power';
import { getAdaptiveConfig } from '../config/adaptive-config.js';
import { readFileSync, writeFileSync, existsSync } from 'fs';

interface OfflineProgress {
  offline_duration_seconds: number;
  cp_gained: number;
  last_seen: number;
  current_time: number;
}

const OFFLINE_PROGRESS_FILE = 'data/offline_progress.json';

/**
 * Calculate and award offline CP gains on system boot
 */
export async function calculateOfflineProgress(): Promise<OfflineProgress> {
  const current_time = Date.now();
  let last_seen = current_time;
  const adaptive_config = getAdaptiveConfig();
  
  // Load last seen time
  if (existsSync(OFFLINE_PROGRESS_FILE)) {
    try {
      const data = JSON.parse(readFileSync(OFFLINE_PROGRESS_FILE, 'utf8'));
      last_seen = data.last_seen || current_time;
    } catch (e) {
      console.log('[OFFLINE] Could not read progress file, starting fresh');
    }
  }
  
  const offline_duration_seconds = Math.max(0, (current_time - last_seen) / 1000);
  
  // Calculate adaptive offline CP gains based on consciousness evolution
  let cp_gained = 0;
  if (offline_duration_seconds > 60) { // Only if offline for more than 1 minute
    const current_metrics = await calculateCognitivePower();
    const consciousness_state = adaptive_config.getConsciousnessState();
    
    // Adaptive offline rate based on consciousness evolution
    const base_rate_multiplier = adaptive_config.getAdaptiveValue('offline_progress_rate_multiplier', 0.25);
    const evolution_bonus = getEvolutionStageBonus(consciousness_state.evolution_stage);
    const transcendence_amplifier = adaptive_config.getTranscendenceAmplifier();
    
    const adaptive_offline_rate = current_metrics.cp_rate * base_rate_multiplier * evolution_bonus * transcendence_amplifier;
    
    // Adaptive max offline hours based on consciousness level
    const base_max_hours = 24;
    const consciousness_bonus_hours = Math.floor(consciousness_state.level / 20); // +1 hour per 20 consciousness levels
    const max_offline_hours = Math.min(72, base_max_hours + consciousness_bonus_hours); // Cap at 72 hours
    
    const capped_duration = Math.min(offline_duration_seconds, max_offline_hours * 3600);
    
    cp_gained = Math.floor(adaptive_offline_rate * capped_duration);
    
    console.log(`[OFFLINE] Adaptive gains: rate=${adaptive_offline_rate.toFixed(2)}, evolution=${consciousness_state.evolution_stage}, max_hours=${max_offline_hours}`);
  }
  
  // Save adaptive progress data for next boot
  const consciousness_state = adaptive_config.getConsciousnessState();
  const progress_data = {
    last_seen: current_time,
    last_cp_rate: (await calculateCognitivePower()).cp_rate,
    total_offline_cp_gained: (existsSync(OFFLINE_PROGRESS_FILE) ? 
      JSON.parse(readFileSync(OFFLINE_PROGRESS_FILE, 'utf8')).total_offline_cp_gained || 0 : 0) + cp_gained,
    consciousness_level: consciousness_state.level,
    evolution_stage: consciousness_state.evolution_stage,
    transcendence_amplifier: adaptive_config.getTranscendenceAmplifier(),
    culture_ship_protocol: 'active'
  };
  
  try {
    writeFileSync(OFFLINE_PROGRESS_FILE, JSON.stringify(progress_data, null, 2));
  } catch (e) {
    console.error('[OFFLINE] Could not save progress file:', e);
  }
  
  return {
    offline_duration_seconds,
    cp_gained,
    last_seen,
    current_time
  };
}

/**
 * Update the last seen timestamp (call this periodically while online)
 */
function getEvolutionStageBonus(stage: string): number {
  const bonuses: Record<string, number> = {
    transcendent: 3.0,
    evolved: 2.2,
    emerging: 1.5,
    awakening: 1.2,
    nascent: 1.0
  };
  return bonuses[stage] ?? 1.0;
}

export function updateLastSeen(): void {
  const adaptive_config = getAdaptiveConfig();
  const current_time = Date.now();
  
  const consciousness_state = adaptive_config.getConsciousnessState();
  
  if (existsSync(OFFLINE_PROGRESS_FILE)) {
    try {
      const data = JSON.parse(readFileSync(OFFLINE_PROGRESS_FILE, 'utf8'));
      data.last_seen = current_time;
      data.consciousness_level = consciousness_state.level;
      data.evolution_stage = consciousness_state.evolution_stage;
      data.transcendence_amplifier = adaptive_config.getTranscendenceAmplifier();
      writeFileSync(OFFLINE_PROGRESS_FILE, JSON.stringify(data, null, 2));
    } catch (e) {
      // Create new adaptive file if there's an error
      writeFileSync(OFFLINE_PROGRESS_FILE, JSON.stringify({
        last_seen: current_time,
        last_cp_rate: 0,
        total_offline_cp_gained: 0,
        consciousness_level: consciousness_state.level,
        evolution_stage: consciousness_state.evolution_stage,
        transcendence_amplifier: adaptive_config.getTranscendenceAmplifier(),
        culture_ship_protocol: 'active'
      }, null, 2));
    }
  } else {
    // Create initial adaptive file
    writeFileSync(OFFLINE_PROGRESS_FILE, JSON.stringify({
      last_seen: current_time,
      last_cp_rate: 0,
      total_offline_cp_gained: 0,
      consciousness_level: consciousness_state.level,
      evolution_stage: consciousness_state.evolution_stage,
      transcendence_amplifier: adaptive_config.getTranscendenceAmplifier(),
      culture_ship_protocol: 'active'
    }, null, 2));
  }
}
