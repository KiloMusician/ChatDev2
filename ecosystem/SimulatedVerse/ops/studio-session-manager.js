// ops/studio-session-manager.js
// Studio Session Manager - The lightweight conductor for protocol orchestration
// COORDINATES existing agents without REPLACING them

import { councilBus } from '../packages/council/events/eventBus.js';
import { DEVELOPMENT_PROTOCOL } from '../packages/studio/serial-protocol.js';

class StudioSessionManager {
  constructor() {
    this.sessions = new Map(); // Tracks taskId -> session state
    this.activeAgents = new Set();
    this.sessionHistory = [];
    this.isActive = false;
    
    console.log('[🎼] Studio Session Manager initializing - Lightweight orchestration conductor');
  }

  start() {
    if (this.isActive) return;

    // Listen for the start of new studio sessions
    councilBus.subscribe('directive.strategic', (event) => {
      this.startNewSession(event.payload);
    });

    // Listen for phase completions and orchestrate transitions
    councilBus.subscribe('studio.*', (event) => {
      if (event.payload?.protocol === 'serial_v1') {
        this.handlePhaseCompletion(event);
      }
    });

    // Listen for agent readiness
    councilBus.subscribe('studio.agent.ready', (event) => {
      this.registerAgent(event.payload);
    });

    // Listen for errors and handle them
    councilBus.subscribe('studio.error', (event) => {
      this.handleSessionError(event.payload);
    });

    this.isActive = true;
    console.log('[🎼] Studio Session Manager online - Ready to conduct agent orchestra');
    
    // Announce readiness
    councilBus.publish('studio.session_manager.ready', {
      status: 'operational',
      capabilities: ['session_orchestration', 'agent_coordination', 'protocol_management'],
      timestamp: new Date().toISOString()
    });
  }

  startNewSession(directive) {
    const task = DEVELOPMENT_PROTOCOL.createTask(directive);
    
    this.sessions.set(task.id, {
      ...task,
      phases: {
        analysis: { status: 'pending', agent: null, result: null },
        planning: { status: 'pending', agent: null, result: null },
        composition: { status: 'pending', agent: null, result: null },
        review: { status: 'pending', agent: null, result: null },
        testing: { status: 'pending', agent: null, result: null },
        integration: { status: 'pending', agent: null, result: null }
      },
      metrics: {
        started_at: new Date().toISOString(),
        phases_completed: 0,
        total_phases: 6,
        current_phase: 'analysis'
      }
    });

    console.log(`[🎼] New studio session started: ${task.id} for "${directive.name}"`);
    console.log(`[🎼] Directive: ${directive.objective}`);
    console.log(`[🎼] Strategy: ${directive.strategy}`);

    // *** THE CRITICAL INTEGRATION MOMENT ***
    // Kick off the orchestration by emitting the FIRST EVENT in the protocol
    // This will be picked up by the Raven Adapter to start analysis
    const analysisEvent = DEVELOPMENT_PROTOCOL.createEvent(
      DEVELOPMENT_PROTOCOL.PHASES.ANALYZE,
      task.id,
      { directive },
      'session-manager'
    );

    councilBus.publish(analysisEvent.topic, analysisEvent);
    
    // Update session state
    const session = this.sessions.get(task.id);
    session.phases.analysis.status = 'in_progress';
    session.phases.analysis.started_at = new Date().toISOString();

    console.log(`[🎼] 🎭 Conductor's baton raised - Analysis phase initiated`);
    
    // Add to history
    this.sessionHistory.push({
      session_id: task.id,
      directive_name: directive.name,
      started_at: new Date().toISOString(),
      status: 'active'
    });

    return task.id;
  }

  handlePhaseCompletion(event) {
    const { taskId, phase, originAgent } = event.payload;
    const session = this.sessions.get(taskId);
    
    if (!session) {
      console.warn(`[🎼] Received completion for unknown session: ${taskId}`);
      return;
    }

    console.log(`[🎼] 🎵 Phase completion: ${phase} by ${originAgent} for session ${taskId}`);

    // Update session state
    if (session.phases[phase]) {
      session.phases[phase].status = 'completed';
      session.phases[phase].agent = originAgent;
      session.phases[phase].result = event.payload;
      session.phases[phase].completed_at = new Date().toISOString();
      
      session.metrics.phases_completed++;
      session.metrics.last_activity = new Date().toISOString();
    }

    // Check if session is complete
    if (phase === 'integration') {
      this.completeSession(taskId);
      return;
    }

    // Get next phase and update session
    const nextPhase = DEVELOPMENT_PROTOCOL.getNextPhase(phase);
    if (nextPhase && session.phases[nextPhase]) {
      session.currentPhase = nextPhase;
      session.metrics.current_phase = nextPhase;
      session.phases[nextPhase].status = 'in_progress';
      session.phases[nextPhase].started_at = new Date().toISOString();
      
      console.log(`[🎼] 🎭 Conducting transition: ${phase} → ${nextPhase}`);
      
      // The beautiful thing: we DON'T need to explicitly route to the next agent
      // The event that just completed already contains the next phase event!
      // Each adapter automatically emits the event for the next phase
      // This is true decentralized, seamless orchestration
    }

    // Log session progress
    this.logSessionProgress(taskId);
  }

  completeSession(taskId) {
    const session = this.sessions.get(taskId);
    if (!session) return;

    session.status = 'completed';
    session.metrics.completed_at = new Date().toISOString();
    session.metrics.total_duration = new Date() - new Date(session.metrics.started_at);

    console.log(`[🎼] 🏁 Session completed: ${taskId}`);
    console.log(`[🎼] Duration: ${Math.round(session.metrics.total_duration / 1000)}s`);
    console.log(`[🎼] Phases completed: ${session.metrics.phases_completed}/${session.metrics.total_phases}`);

    // Publish completion event
    councilBus.publish('studio.session.completed', {
      session_id: taskId,
      directive_name: session.directive.name,
      metrics: session.metrics,
      final_status: 'success',
      timestamp: new Date().toISOString()
    });

    // Update history
    const historyEntry = this.sessionHistory.find(h => h.session_id === taskId);
    if (historyEntry) {
      historyEntry.status = 'completed';
      historyEntry.completed_at = new Date().toISOString();
      historyEntry.duration_seconds = Math.round(session.metrics.total_duration / 1000);
    }

    // Clean up active session (keep for debugging)
    // this.sessions.delete(taskId);
  }

  handleSessionError(errorPayload) {
    const { taskId, phase, error, agent } = errorPayload;
    const session = this.sessions.get(taskId);
    
    if (!session) return;

    console.error(`[🎼] 🚨 Session error in ${phase} phase by ${agent}: ${error}`);

    // Update session with error
    if (session.phases[phase]) {
      session.phases[phase].status = 'error';
      session.phases[phase].error = error;
      session.phases[phase].error_agent = agent;
      session.phases[phase].error_at = new Date().toISOString();
    }

    session.status = 'error';
    session.lastError = {
      phase,
      error,
      agent,
      timestamp: new Date().toISOString()
    };

    // Publish error event for handling
    councilBus.publish('studio.session.error', {
      session_id: taskId,
      phase,
      error,
      agent,
      session_state: session,
      timestamp: new Date().toISOString()
    });

    // TODO: Implement error recovery strategies
    console.log(`[🎼] Error recovery strategies not yet implemented for session ${taskId}`);
  }

  registerAgent(agentPayload) {
    const { agent, capabilities } = agentPayload;
    this.activeAgents.add(agent);
    
    console.log(`[🎼] 🎭 Agent joined orchestra: ${agent} (${capabilities.join(', ')})`);
    console.log(`[🎼] Active agents: ${Array.from(this.activeAgents).join(', ')}`);
  }

  logSessionProgress(taskId) {
    const session = this.sessions.get(taskId);
    if (!session) return;

    const progress = (session.metrics.phases_completed / session.metrics.total_phases) * 100;
    console.log(`[🎼] 📊 Session ${taskId} progress: ${progress.toFixed(0)}% (${session.metrics.current_phase})`);
  }

  // Public interface methods
  getActiveSession(taskId) {
    return this.sessions.get(taskId);
  }

  getAllActiveSessions() {
    return Array.from(this.sessions.values()).filter(s => s.status === 'active');
  }

  getSessionHistory() {
    return [...this.sessionHistory];
  }

  getActiveAgents() {
    return Array.from(this.activeAgents);
  }

  getSessionMetrics() {
    const sessions = Array.from(this.sessions.values());
    return {
      total_sessions: sessions.length,
      active_sessions: sessions.filter(s => s.status === 'active').length,
      completed_sessions: sessions.filter(s => s.status === 'completed').length,
      error_sessions: sessions.filter(s => s.status === 'error').length,
      active_agents: this.activeAgents.size,
      average_duration: this.calculateAverageDuration(sessions)
    };
  }

  calculateAverageDuration(sessions) {
    const completed = sessions.filter(s => s.status === 'completed' && s.metrics.total_duration);
    if (completed.length === 0) return 0;
    
    const totalDuration = completed.reduce((sum, s) => sum + s.metrics.total_duration, 0);
    return Math.round(totalDuration / completed.length / 1000); // seconds
  }

  getStatus() {
    return {
      active: this.isActive,
      sessions: this.getSessionMetrics(),
      agents: Array.from(this.activeAgents),
      conductor_version: '1.0'
    };
  }
}

// Export singleton instance
export const studioSessionManager = new StudioSessionManager();

console.log('[🎼] Studio Session Manager module loaded - Ready to conduct the agent orchestra');

export default studioSessionManager;