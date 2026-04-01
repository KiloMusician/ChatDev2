/* Council Event Publishers - High-level event publishing for autonomous ops */

import { councilBus } from './eventBus.js';

export function publishCascade(payload) {
  councilBus.publish('sentinel.cascade', {
    ...payload,
    timestamp: new Date().toISOString(),
    severity: payload.kind === 'entropy_drift' ? 'critical' : 
              payload.kind === 'invariance_dip' ? 'warning' :
              payload.kind === 'motif_scarcity' ? 'info' :
              payload.kind === 'ic_spike' ? 'warning' : 'info'
  });
}

export function publishRowgenCandidates(rows) {
  councilBus.publish('rowgen.candidates', {
    rows,
    generated_at: new Date().toISOString(),
    count: rows.length
  });
}

export function publishSystemHealth(metrics) {
  councilBus.publish('system.health', {
    ...metrics,
    timestamp: new Date().toISOString()
  });
}

export function publishAgentAction(agentId, action, result) {
  councilBus.publish('agent.action', {
    agent_id: agentId,
    action,
    result,
    timestamp: new Date().toISOString()
  });
}

export function publishLayout(layoutSpec) {
  councilBus.publish('orchestrate.layout', layoutSpec);
}