// packages/studio/serial-protocol.js
// Universal Serial Protocol - The shared contract for all existing agents
// This CONNECTS agents without REPLACING them

export const DEVELOPMENT_PROTOCOL = Object.freeze({
  VERSION: '0.1',
  
  // The development phases that map to existing agent capabilities
  PHASES: {
    ANALYZE: 'analysis',        // Raven's existing purpose
    PLAN: 'planning',           // The Director's existing purpose  
    COMPOSE: 'composition',     // ChatDev's existing purpose
    REVIEW: 'review',           // AI Council's existing purpose
    TEST: 'testing',            // Testing Chamber's existing purpose
    INTEGRATE: 'integration'    // Zeta-Driver's existing purpose
  },

  // Standard event schema that ALL agents can publish and understand
  createEvent: (phase, taskId, payload, originAgent) => ({
    topic: `studio.${phase}`,
    payload: {
      protocol: 'serial_v1',
      taskId,
      phase,
      originAgent,
      timestamp: new Date().toISOString(),
      ...payload
    }
  }),

  // Phase progression map - defines the natural flow
  FLOW: {
    'analysis': 'planning',
    'planning': 'composition', 
    'composition': 'review',
    'review': 'testing',
    'testing': 'integration',
    'integration': null // Terminal phase
  },

  // Agent capability mapping to existing agents
  AGENTS: {
    'raven': ['analysis'],
    'director': ['planning'],
    'chatdev': ['composition'],
    'council': ['review'],
    'testing-chamber': ['testing'],
    'zeta-driver': ['integration']
  },

  // Create a complete task for the protocol
  createTask: (directive) => ({
    id: `studio_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    directive,
    currentPhase: 'analysis',
    phases: {},
    startTime: new Date().toISOString(),
    status: 'active'
  }),

  // Helper to get next phase
  getNextPhase: (currentPhase) => {
    return DEVELOPMENT_PROTOCOL.FLOW[currentPhase] || null;
  },

  // Validate event structure
  validateEvent: (event) => {
    return event.payload && 
           event.payload.protocol === 'serial_v1' &&
           event.payload.taskId &&
           event.payload.phase &&
           event.payload.originAgent;
  }
});

console.log('[🎼] Universal Serial Protocol loaded - Agent coordination language ready');

export default DEVELOPMENT_PROTOCOL;