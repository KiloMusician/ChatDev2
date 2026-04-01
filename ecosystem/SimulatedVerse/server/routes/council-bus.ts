// server/routes/council-bus.ts
// Council Bus API endpoints for real-time frontend-backend communication
// Enables the Dashboard Reality Layer to connect to live system events

import express from 'express';
import { randomUUID } from 'crypto';
import { adminGuard } from '../middleware/auth.js';
import { standardRateLimit } from '../middleware/rate-limit.js';
import { log } from '../services/log.js';

// Simple in-memory event bus for Dashboard Reality Layer
class SimpleEventBus {
  private listeners: Map<string, Function[]> = new Map();
  
  subscribe(topic: string, callback: Function): () => void {
    if (!this.listeners.has(topic)) {
      this.listeners.set(topic, []);
    }
    this.listeners.get(topic)!.push(callback);
    
    return () => {
      const listeners = this.listeners.get(topic);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) listeners.splice(index, 1);
      }
    };
  }
  
  publish(topic: string, payload: any) {
    const event = {
      id: randomUUID(),
      topic,
      payload,
      timestamp: new Date().toISOString()
    };
    
    // Handle exact matches
    const exactListeners = this.listeners.get(topic) || [];
    exactListeners.forEach(listener => listener(event));
    
    // Handle wildcard matches
    for (const [pattern, listeners] of this.listeners) {
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
        if (regex.test(topic)) {
          listeners.forEach(listener => listener(event));
        }
      }
    }
    
    // Broadcast to SSE connections
    this.broadcastToSSE(event);

    if (process.env.LOG_COUNCIL_EVENTS === '1') {
      log.info({ topic, payload }, `[CouncilBus] Published`);
    }
  }
  
  private broadcastToSSE(event: any) {
    const data = `data: ${JSON.stringify(event)}\n\n`;
    sseConnections.forEach(res => {
      try {
        res.write(data);
      } catch (error) {
        // Remove broken connection
        sseConnections.delete(res);
      }
    });
  }
}

const councilBus = new SimpleEventBus();

// Health monitoring for agents
const agentHealthTracker = new Map<string, { status: string; lastSeen: number; timestamp: string }>();

// Report agent health and broadcast updates
function reportAgentHealth(agentId: string, status: string) {
  const healthData = {
    status,
    lastSeen: Date.now(),
    timestamp: new Date().toISOString()
  };
  
  agentHealthTracker.set(agentId, healthData);
  councilBus.publish('agent.health.update', { agentId, ...healthData });
  
  // Clean old health data (older than 10 minutes)
  const tenMinutesAgo = Date.now() - 10 * 60 * 1000;
  for (const [id, data] of agentHealthTracker) {
    if (data.lastSeen < tenMinutesAgo) {
      agentHealthTracker.delete(id);
      councilBus.publish('agent.health.timeout', { agentId: id, lastSeen: data.lastSeen });
    }
  }
}

const router = express.Router();

// SSE connections for real-time event streaming
const sseConnections = new Set<express.Response>();

// Cleanup connections on server shutdown
process.on('SIGINT', () => {
  sseConnections.forEach(res => {
    try {
      res.end();
    } catch (error) {
      // Connection already closed
    }
  });
  sseConnections.clear();
});

// Setup SSE connection for streaming Council Bus events to frontend
router.get('/stream', (req, res) => {
  // Setup SSE headers
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Cache-Control',
    'X-Accel-Buffering': 'no'
  });

  // Ensure headers are flushed immediately (avoid buffering with compression)
  if (typeof res.flushHeaders === 'function') {
    res.flushHeaders();
  }

  // Send initial connection confirmation
  res.write('data: {"type":"connection","status":"established"}\n\n');
  if (typeof (res as unknown as { flush?: () => void }).flush === 'function') {
    (res as unknown as { flush: () => void }).flush();
  }

  // Add to active connections
  sseConnections.add(res);

  // Subscribe to all Council Bus events and forward to this SSE connection
  const unsubscribe = councilBus.subscribe('*', (event: any) => {
    try {
      const data = JSON.stringify({
        topic: event.topic || 'unknown',
        payload: event.payload || event
      });
      res.write(`data: ${data}\n\n`);
    } catch (error) {
      console.warn('[Council Bus SSE] Failed to send event:', error);
    }
  });

  // Handle client disconnect
  req.on('close', () => {
    sseConnections.delete(res);
    unsubscribe();
  });

  req.on('error', () => {
    sseConnections.delete(res);
    unsubscribe();
  });
});

// Endpoint for publishing events from frontend
router.post('/publish', standardRateLimit, adminGuard, (req, res) => {
  try {
    const { topic, payload } = req.body;

    if (!topic) {
      return res.status(400).json({ error: 'Topic is required' });
    }

    // Publish event to Council Bus
    councilBus.publish(topic, payload || {});

    res.json({ 
      success: true, 
      message: `Event published to topic: ${topic}`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[Council Bus API] Publish error:', error);
    res.status(500).json({ 
      error: 'Failed to publish event',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Endpoint for requesting current state
router.get('/request/:topic', async (req, res) => {
  try {
    const { topic } = req.params;
    
    // Publish request event
    councilBus.publish(`request.${topic}`, { 
      requester: 'dashboard_reality_layer',
      timestamp: new Date().toISOString()
    });

    res.json({ 
      success: true, 
      message: `State request sent for topic: ${topic}` 
    });

  } catch (error) {
    console.error('[Council Bus API] Request error:', error);
    res.status(500).json({ 
      error: 'Failed to request state',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Handle UI storyteller controls
router.post('/storyteller/trigger', standardRateLimit, adminGuard, (req, res) => {
  try {
    const { eventType } = req.body;

    if (!eventType) {
      return res.status(400).json({ error: 'eventType is required' });
    }

    // Map UI events to Council Bus events
    const eventMap: Record<string, any> = {
      'discovery': {
        topic: 'event.discovery',
        payload: {
          title: 'UI-Triggered Discovery Event',
          description: 'A moment of insight sparked by colony oversight',
          effect: 'colony_inspiration_boost',
          benefits: ['inspiration_+15', 'joy_+10'],
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'gift': {
        topic: 'event.gift',
        payload: {
          title: 'Resource Gift from the Overseer',
          description: 'Beneficial resources have been provided to support the colony',
          effect: 'resource_boost',
          benefits: ['energy_+50', 'focus_+20'],
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'diversion': {
        topic: 'event.diversion',
        payload: {
          title: 'Playful Exploration Encouraged',
          description: 'Time for creative exploration and joyful discovery',
          effect: 'joy_restoration',
          benefits: ['joy_+25', 'creativity_+15'],
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'challenge': {
        topic: 'event.challenge',
        payload: {
          title: 'Colony-Wide Optimization Sprint',
          description: 'A focused effort to achieve excellence and breakthrough performance',
          effect: 'focus_enhancement',
          benefits: ['focus_+30', 'energy_+10'],
          priority: 'high',
          goal: 'Achieve breakthrough optimization in target systems',
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'celebration': {
        topic: 'event.celebration',
        payload: {
          title: 'Achievement Celebration',
          description: 'Recognition and celebration of the colony\'s remarkable progress',
          effect: 'morale_boost',
          benefits: ['joy_+35', 'inspiration_+20'],
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'support': {
        topic: 'event.support',
        payload: {
          title: 'Collaborative Support Wave',
          description: 'Enhanced collaboration and mutual support throughout the colony',
          effect: 'collaboration_boost',
          benefits: ['teamwork_+25', 'focus_+15'],
          narrative_impact: 'positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'inspiration_wave': {
        topic: 'event.inspiration_wave',
        payload: {
          title: 'Inspiration Wave Across the Colony',
          description: 'A surge of creative energy flows through all agents',
          effect: 'colony_wide_inspiration',
          benefits: ['inspiration_+40', 'creativity_+30'],
          scope: 'all_agents',
          narrative_impact: 'major_positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      },
      'harmony_pulse': {
        topic: 'event.harmony',
        payload: {
          title: 'Harmony Pulse - Perfect Synchronization',
          description: 'The colony achieves a moment of perfect collaborative harmony',
          effect: 'perfect_harmony',
          benefits: ['joy_+30', 'focus_+25', 'teamwork_+40'],
          scope: 'all_agents',
          narrative_impact: 'major_positive',
          triggered_by: 'storyteller_console',
          timestamp: new Date().toISOString()
        }
      }
    };

    const eventConfig = eventMap[eventType];
    if (!eventConfig) {
      return res.status(400).json({ error: `Unknown event type: ${eventType}` });
    }

    // Publish the mapped event
    councilBus.publish(eventConfig.topic, eventConfig.payload);

    // Also publish to storyteller for tracking
    councilBus.publish('ui.storyteller.event_triggered', {
      event_type: eventType,
      topic: eventConfig.topic,
      triggered_at: new Date().toISOString(),
      trigger_source: 'dashboard_reality_layer'
    });

    res.json({
      success: true,
      event_type: eventType,
      topic: eventConfig.topic,
      message: `${eventConfig.payload.title} triggered successfully`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[Council Bus API] Storyteller trigger error:', error);
    res.status(500).json({
      error: 'Failed to trigger storyteller event',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Handle UI pawn controls
router.post('/pawn/control', (req, res) => {
  try {
    const { action, pawnId, data } = req.body;

    if (!action || !pawnId) {
      return res.status(400).json({ error: 'action and pawnId are required' });
    }

    const actionMap: Record<string, string> = {
      'recalibrate': 'ui.pawn.recalibrate',
      'reassign': 'ui.pawn.reassign', 
      'boost': 'ui.pawn.boost'
    };

    const topic = actionMap[action];
    if (!topic) {
      return res.status(400).json({ error: `Unknown pawn action: ${action}` });
    }

    // Publish pawn control event
    councilBus.publish(topic, {
      pawnId,
      action,
      ...data,
      triggered_by: 'dashboard_reality_layer',
      timestamp: new Date().toISOString()
    });

    res.json({
      success: true,
      action,
      pawnId,
      message: `Pawn ${action} command sent successfully`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[Council Bus API] Pawn control error:', error);
    res.status(500).json({
      error: 'Failed to control pawn',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Health check endpoint
router.get('/health', (req, res) => {
  res.json({
    status: 'operational',
    active_connections: sseConnections.size,
    council_bus_active: !!councilBus,
    timestamp: new Date().toISOString()
  });
});

export default router;
