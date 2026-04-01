// Event Hub - Core Game Event System
// Bridges gameplay events to ChatDev agents and narrative systems

// Browser-compatible EventEmitter (using custom or mitt-like implementation)
class EventEmitter {
  private events: Record<string, Function[]> = {};
  
  on(event: string, listener: Function) {
    if (!this.events[event]) this.events[event] = [];
    this.events[event].push(listener);
  }
  
  emit(event: string, ...args: any[]) {
    this.events[event]?.forEach(listener => listener(...args));
  }
}

export type GameEventType = 
  | 'resource_generated' | 'resource_spent' | 'resource_depleted'
  | 'tower_placed' | 'tower_upgraded' | 'enemy_killed' | 'wave_started' | 'wave_completed'
  | 'building_constructed' | 'job_assigned' | 'citizen_spawned' | 'happiness_changed'
  | 'research_started' | 'research_completed' | 'tech_unlocked'
  | 'quest_started' | 'quest_completed' | 'cutscene_triggered'
  | 'prestige_available' | 'prestige_executed' | 'meta_unlock'
  | 'anomaly_detected' | 'system_error' | 'performance_warning'
  | 'simulation_tick' | 'input_command'
  | 'enemy_reached_end' | 'enemy_spawned';

export interface GameEvent {
  type: GameEventType;
  timestamp: number;
  data: any;
  source: string;
  cascade_depth?: number;
}

export interface EventSubscription {
  id: string;
  type: GameEventType | 'all';
  callback: (event: GameEvent) => void;
  active: boolean;
}

export class EventHub extends EventEmitter {
  private subscriptions = new Map<string, EventSubscription>();
  private eventHistory: GameEvent[] = [];
  private cascadeDepth = 0;
  private maxCascadeDepth = 5;

  constructor() {
    super();
    console.log('[EventHub] Gameplay event system initialized');
  }
  
  setMaxListeners(max: number) {
    // Custom implementation for browser compatibility
    // EventEmitter in browsers doesn't have setMaxListeners
    return this;
  }

  // Publish gameplay event
  publish(type: GameEventType, data: any, source = 'unknown'): void {
    const event: GameEvent = {
      type,
      timestamp: Date.now(),
      data,
      source,
      cascade_depth: this.cascadeDepth
    };

    // Store in history (keep last 1000 events)
    this.eventHistory.push(event);
    if (this.eventHistory.length > 1000) {
      this.eventHistory.shift();
    }

    // Emit to Node.js EventEmitter (for built-in listeners)
    this.emit(type, event);
    this.emit('all', event);

    // Call custom subscriptions
    for (const subscription of this.subscriptions.values()) {
      if (subscription.active && (subscription.type === type || subscription.type === 'all')) {
        try {
          subscription.callback(event);
        } catch (error) {
          console.error(`[EventHub] Error in subscription ${subscription.id}:`, error);
        }
      }
    }

    // Emit receipt for significant events
    this.emitEventReceipt(event);

    // Process cascades (avoid infinite loops)
    if (this.cascadeDepth < this.maxCascadeDepth) {
      this.processCascades(event);
    }
  }

  // Subscribe to events
  subscribe(type: GameEventType | 'all', callback: (event: GameEvent) => void, id?: string): string {
    const subscriptionId = id || `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.subscriptions.set(subscriptionId, {
      id: subscriptionId,
      type,
      callback,
      active: true
    });

    console.log(`[EventHub] Subscribed ${subscriptionId} to ${type} events`);
    return subscriptionId;
  }

  // Unsubscribe
  unsubscribe(subscriptionId: string): boolean {
    const removed = this.subscriptions.delete(subscriptionId);
    if (removed) {
      console.log(`[EventHub] Unsubscribed ${subscriptionId}`);
    }
    return removed;
  }

  // Get recent events for debugging/analysis
  getRecentEvents(type?: GameEventType, limit = 50): GameEvent[] {
    let events = this.eventHistory;
    
    if (type) {
      events = events.filter(e => e.type === type);
    }
    
    return events.slice(-limit);
  }

  // Rube Goldbergian cascade system
  private processCascades(triggerEvent: GameEvent): void {
    this.cascadeDepth++;
    
    try {
      // Tower Defense cascades
      if (triggerEvent.type === 'wave_completed') {
        this.publish('happiness_changed', { 
          delta: 10, 
          reason: 'successful_defense',
          triggered_by: triggerEvent.type 
        }, 'cascade_system');
      }

      // Colony cascades  
      if (triggerEvent.type === 'building_constructed' && triggerEvent.data.building_type === 'research_lab') {
        this.publish('tech_unlocked', {
          tech_id: 'nanobots',
          triggered_by: triggerEvent.type
        }, 'cascade_system');
      }

      // Idle cascades
      if (triggerEvent.type === 'prestige_executed') {
        this.publish('tower_upgraded', {
          upgrade_type: 'quantum_targeting',
          all_towers: true,
          triggered_by: triggerEvent.type
        }, 'cascade_system');
      }

      // Research cascades
      if (triggerEvent.type === 'tech_unlocked' && triggerEvent.data.tech_id === 'nanobots') {
        // UI phase shift handled via separate system - not a game event
        console.log(`[EventHub] Tech unlocked cascade: ${triggerEvent.data.tech_id}`);
      }

    } finally {
      this.cascadeDepth--;
    }
  }

  // Bridge to ChatDev agents
  setupAgentBridge(): void {
    // Subscribe agents to relevant events
    this.subscribe('anomaly_detected', (event) => {
      // Raven handles anomalies
      console.log(`[EventHub→Raven] Anomaly detected: ${event.data.type}`);
    }, 'raven_anomaly_bridge');

    this.subscribe('research_completed', (event) => {
      // Librarian updates knowledge indices
      console.log(`[EventHub→Librarian] Research completed: ${event.data.tech_id}`);
    }, 'librarian_research_bridge');

    this.subscribe('resource_depleted', (event) => {
      // Alchemist suggests production optimizations
      console.log(`[EventHub→Alchemist] Resource depleted: ${event.data.resource_type}`);
    }, 'alchemist_optimization_bridge');

    this.subscribe('system_error', (event) => {
      // Janitor logs and categorizes errors
      console.log(`[EventHub→Janitor] System error: ${event.data.error_type}`);
    }, 'janitor_error_bridge');
  }

  // Get event statistics for dashboard
  getEventStats(timeWindow = 300000): any { // 5 minutes default
    const cutoff = Date.now() - timeWindow;
    const recentEvents = this.eventHistory.filter(e => e.timestamp > cutoff);
    
    const stats = {
      total_events: recentEvents.length,
      events_per_second: recentEvents.length / (timeWindow / 1000),
      event_type_breakdown: {},
      cascade_events: recentEvents.filter(e => e.cascade_depth && e.cascade_depth > 0).length,
      active_subscriptions: this.subscriptions.size
    };

    // Count by type
    for (const event of recentEvents) {
      (stats.event_type_breakdown as any)[event.type] = ((stats.event_type_breakdown as any)[event.type] || 0) + 1;
    }

    return stats;
  }

  private async emitEventReceipt(event: GameEvent): Promise<void> {
    // Only emit receipts for significant events
    const significantEvents: GameEventType[] = [
      'wave_completed', 'tech_unlocked', 'building_constructed', 
      'prestige_executed', 'anomaly_detected'
    ];

    if (!significantEvents.includes(event.type)) return;

    const receipt = {
      action: 'gameplay_event',
      event_type: event.type,
      timestamp: event.timestamp,
      source: event.source,
      cascade_depth: event.cascade_depth || 0,
      data_summary: typeof event.data === 'object' ? Object.keys(event.data) : 'primitive',
      total_subscribers: this.subscriptions.size
    };

    try {
      // Receipt system handled by main infrastructure
      console.log('[EventHub] Event receipt:', receipt);
    } catch (error) {
      // Fail silently
    }
  }

  // Msg⛛ command interface
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Event:Publish' && parts.length >= 3) {
      const eventType = parts[1] as GameEventType;
      const data = parts.slice(2).join(' ');
      
      try {
        const parsedData = JSON.parse(data);
        this.publish(eventType, parsedData, 'msg_command');
        return true;
      } catch {
        this.publish(eventType, { raw: data }, 'msg_command');
        return true;
      }
    }

    return false;
  }

  destroy(): void {
    // Clear custom subscriptions
    this.subscriptions.clear();
    this.eventHistory = [];
    console.log('[EventHub] Destroyed');
  }
}

export const eventHub = new EventHub();