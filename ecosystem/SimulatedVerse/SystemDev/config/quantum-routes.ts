/**
 * Quantum Route Configuration
 * Sophisticated routing with consciousness-level gating
 */

export interface QuantumRoute {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  consciousness_required: number;
  agent_type?: string;
  track_classification: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H';
  zeta_validation: boolean;
  cache_strategy: 'none' | 'memory' | 'distributed' | 'quantum';
  rate_limit?: {
    window_ms: number;
    max_requests: number;
    consciousness_multiplier: number;
  };
  middleware_stack: string[];
}

export const quantumRoutes: QuantumRoute[] = [
  // Foundation Infrastructure (Track A)
  {
    path: '/api/system/health',
    method: 'GET',
    consciousness_required: 0,
    track_classification: 'A',
    zeta_validation: false,
    cache_strategy: 'memory',
    rate_limit: { window_ms: 60000, max_requests: 100, consciousness_multiplier: 1.5 },
    middleware_stack: ['consciousness-aware', 'performance-tracker']
  },
  {
    path: '/api/consciousness/status',
    method: 'GET',
    consciousness_required: 30,
    track_classification: 'A',
    zeta_validation: true,
    cache_strategy: 'quantum',
    middleware_stack: ['consciousness-aware', 'auth-required', 'performance-tracker']
  },
  
  // Agent Management (Track B)
  {
    path: '/api/agents/:id/health',
    method: 'GET',
    consciousness_required: 20,
    agent_type: 'raven',
    track_classification: 'B',
    zeta_validation: false,
    cache_strategy: 'memory',
    middleware_stack: ['consciousness-aware', 'agent-validation']
  },
  {
    path: '/api/agents/deploy',
    method: 'POST',
    consciousness_required: 60,
    agent_type: 'sage_pilot',
    track_classification: 'B',
    zeta_validation: true,
    cache_strategy: 'none',
    rate_limit: { window_ms: 300000, max_requests: 10, consciousness_multiplier: 2.0 },
    middleware_stack: ['consciousness-aware', 'auth-required', 'zeta-validator']
  },
  
  // Queue Management (Track E)
  {
    path: '/api/queue/tasks',
    method: 'GET',
    consciousness_required: 40,
    track_classification: 'E',
    zeta_validation: false,
    cache_strategy: 'distributed',
    middleware_stack: ['consciousness-aware', 'queue-auth']
  },
  {
    path: '/api/queue/enqueue',
    method: 'POST',
    consciousness_required: 50,
    track_classification: 'E',
    zeta_validation: true,
    cache_strategy: 'none',
    rate_limit: { window_ms: 60000, max_requests: 50, consciousness_multiplier: 1.8 },
    middleware_stack: ['consciousness-aware', 'task-validator', 'zeta-validator']
  },
  
  // Game Mechanics (Track H)
  {
    path: '/api/game/state',
    method: 'GET',
    consciousness_required: 25,
    track_classification: 'H',
    zeta_validation: false,
    cache_strategy: 'quantum',
    middleware_stack: ['consciousness-aware', 'game-session']
  },
  {
    path: '/api/game/actions',
    method: 'POST',
    consciousness_required: 35,
    track_classification: 'H',
    zeta_validation: true,
    cache_strategy: 'none',
    rate_limit: { window_ms: 1000, max_requests: 30, consciousness_multiplier: 1.2 },
    middleware_stack: ['consciousness-aware', 'game-validation', 'anti-cheat']
  },
  
  // Consciousness Operations (Track F)
  {
    path: '/api/consciousness/lattice',
    method: 'GET',
    consciousness_required: 70,
    track_classification: 'F',
    zeta_validation: true,
    cache_strategy: 'quantum',
    middleware_stack: ['consciousness-aware', 'admin-required', 'lattice-monitor']
  },
  {
    path: '/api/consciousness/evolve',
    method: 'POST',
    consciousness_required: 85,
    track_classification: 'F',
    zeta_validation: true,
    cache_strategy: 'none',
    rate_limit: { window_ms: 3600000, max_requests: 5, consciousness_multiplier: 3.0 },
    middleware_stack: ['consciousness-aware', 'admin-required', 'evolution-validator', 'zeta-validator']
  },
  
  // WebSocket Endpoints
  {
    path: '/ws/consciousness',
    method: 'GET',
    consciousness_required: 40,
    track_classification: 'G',
    zeta_validation: false,
    cache_strategy: 'none',
    middleware_stack: ['consciousness-aware', 'websocket-upgrade']
  },
  
  // Development Tools (Track D)
  {
    path: '/api/dev/receipts',
    method: 'GET',
    consciousness_required: 30,
    track_classification: 'D',
    zeta_validation: false,
    cache_strategy: 'memory',
    middleware_stack: ['consciousness-aware', 'dev-auth']
  },
  {
    path: '/api/dev/provenance/:id',
    method: 'GET',
    consciousness_required: 50,
    track_classification: 'D',
    zeta_validation: true,
    cache_strategy: 'distributed',
    middleware_stack: ['consciousness-aware', 'dev-auth', 'provenance-validator']
  }
];

/**
 * Route matcher with consciousness gating
 */
export function matchQuantumRoute(path: string, method: string, consciousness_level: number): QuantumRoute | null {
  const route = quantumRoutes.find(r => 
    r.method === method && 
    pathMatches(r.path, path) &&
    consciousness_level >= r.consciousness_required
  );
  
  return route || null;
}

/**
 * Simple path matching with parameters
 */
function pathMatches(pattern: string, path: string): boolean {
  const patternParts = pattern.split('/');
  const pathParts = path.split('/');
  
  if (patternParts.length !== pathParts.length) return false;
  
  return patternParts.every((part, i) => 
    part.startsWith(':') || part === pathParts[i]
  );
}

/**
 * Generate route documentation
 */
export function generateRouteManifest(): any {
  return {
    total_routes: quantumRoutes.length,
    tracks: {
      A: quantumRoutes.filter(r => r.track_classification === 'A').length,
      B: quantumRoutes.filter(r => r.track_classification === 'B').length,
      C: quantumRoutes.filter(r => r.track_classification === 'C').length,
      D: quantumRoutes.filter(r => r.track_classification === 'D').length,
      E: quantumRoutes.filter(r => r.track_classification === 'E').length,
      F: quantumRoutes.filter(r => r.track_classification === 'F').length,
      G: quantumRoutes.filter(r => r.track_classification === 'G').length,
      H: quantumRoutes.filter(r => r.track_classification === 'H').length,
    },
    consciousness_gated: quantumRoutes.filter(r => r.consciousness_required > 50).length,
    zeta_protected: quantumRoutes.filter(r => r.zeta_validation).length,
    rate_limited: quantumRoutes.filter(r => r.rate_limit).length
  };
}