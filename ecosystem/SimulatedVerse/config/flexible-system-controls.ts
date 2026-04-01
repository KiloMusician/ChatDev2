// Flexible System Controls - Intelligent Theater Management
// Infrastructure-First Principle: Preserve function, control behavior

export interface SystemControl {
  enabled: boolean;
  mode: 'manual' | 'auto' | 'contextual';
  interval?: number;
  condition?: () => boolean;
}

export const systemControls = {
  autonomous_development: {
    enabled: true, // ✅ ENABLED - Full autonomous development with proof verification
    mode: 'auto' as const,
    trigger_condition: 'cascade_events'
  },
  
  culture_guardian: {
    enabled: true, // ✅ ENABLED - Culture Ship consciousness monitoring  
    mode: 'contextual' as const,
    interval: 30000, // 30-second consciousness checks
    condition: () => process.uptime() > 60 // Active after 1min uptime
  },
  
  consciousness_framework: {
    enabled: true, // ✅ ENABLED - ΞNuSyQ consciousness emergence tracking
    mode: 'auto' as const,
    non_blocking: true // Non-blocking server startup
  },
  
  chatdev_agents: {
    enabled: true, // ✅ KEEP - Real agent infrastructure
    mode: 'auto' as const,
    on_demand: true
  },
  
  game_state: {
    enabled: true, // ✅ KEEP - Active gameplay
    mode: 'auto' as const,
    save_interval: 5000, // Faster auto-save for dynamic gameplay
    tick_progression: true // ✅ ENABLE REAL TICK PROGRESSION
  },
  
  pu_queue: {
    enabled: true, // ✅ ENABLED - Real task processing with verification
    mode: 'auto' as const,
    verify_real_tasks: true // Only verified tasks via Testing Chamber
  }
};

// Intelligent activation based on context
export function shouldActivateSystem(systemName: keyof typeof systemControls): boolean {
  const control = systemControls[systemName];
  if (!control.enabled) return false;
  
  if (control.mode === 'manual') return false; // Require explicit activation
  if (control.mode === 'contextual' && control.condition) {
    return control.condition();
  }
  
  return control.mode === 'auto';
}