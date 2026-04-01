/* Council Event Bus - Central event coordination for autonomous ops */

class CouncilBus {
  constructor() {
    this.listeners = new Map();
    this.eventHistory = [];
  }

  publish(topic, payload) {
    const event = {
      id: Date.now() + '-' + Math.random().toString(36).substr(2, 9),
      topic,
      payload,
      timestamp: new Date().toISOString()
    };

    this.eventHistory.push(event);
    
    // Keep only recent history
    if (this.eventHistory.length > 1000) {
      this.eventHistory.shift();
    }

    const topicListeners = this.listeners.get(topic) || [];
    topicListeners.forEach(listener => {
      try {
        listener(event);
      } catch (e) {
        console.warn(`[councilBus] Listener error for topic ${topic}:`, e);
      }
    });

    console.log(`[councilBus] Published: ${topic} - ${JSON.stringify(payload).substring(0, 100)}`);
  }

  subscribe(topic, listener) {
    if (!this.listeners.has(topic)) {
      this.listeners.set(topic, []);
    }
    this.listeners.get(topic).push(listener);
    
    return () => {
      const listeners = this.listeners.get(topic);
      if (listeners) {
        const index = listeners.indexOf(listener);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  getRecentEvents(topic = null, limit = 50) {
    let events = this.eventHistory;
    if (topic) {
      events = events.filter(e => e.topic === topic);
    }
    return events.slice(-limit);
  }
}

export const councilBus = new CouncilBus();

// Add wildcard subscription support for archivist
councilBus.subscribeAll = function(listener) {
  this._globalListeners = this._globalListeners || [];
  this._globalListeners.push(listener);
  
  return () => {
    const index = this._globalListeners.indexOf(listener);
    if (index > -1) {
      this._globalListeners.splice(index, 1);
    }
  };
};

// Agent health monitoring
councilBus.agentHealth = new Map();

councilBus.reportAgentHealth = function(agentId, status) {
  const healthData = {
    agentId,
    status,
    lastSeen: Date.now(),
    timestamp: new Date().toISOString()
  };
  
  this.agentHealth.set(agentId, healthData);
  this.publish('agent.health.update', healthData);
  
  // Clean old health data (older than 5 minutes)
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
  for (const [id, data] of this.agentHealth) {
    if (data.lastSeen < fiveMinutesAgo) {
      this.agentHealth.delete(id);
      this.publish('agent.health.timeout', { agentId: id, lastSeen: data.lastSeen });
    }
  }
};

councilBus.getAgentHealth = function(agentId = null) {
  if (agentId) {
    return this.agentHealth.get(agentId);
  }
  return Array.from(this.agentHealth.values());
};

// Override publish to notify global listeners
const originalPublish = councilBus.publish.bind(councilBus);
councilBus.publish = function(topic, payload) {
  const event = originalPublish(topic, payload);
  
  // Notify global listeners
  const globalListeners = this._globalListeners || [];
  globalListeners.forEach(listener => {
    try {
      listener({ topic, payload, ts: Date.now(), id: event?.id || Date.now().toString(), timestamp: new Date().toISOString() });
    } catch (e) {
      console.warn(`[councilBus] Global listener error:`, e);
    }
  });
  
  return event;
};