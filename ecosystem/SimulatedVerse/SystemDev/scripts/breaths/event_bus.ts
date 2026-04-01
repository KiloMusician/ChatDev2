/**
 * ΞΘΛΔ_event_bus - Unified Event Bus Contract
 * Single event bus for UI ↔ Game coordination with Golden Traces
 */

export type EventKind = 
  | 'tick' 
  | 'save' 
  | 'load' 
  | 'prestige' 
  | 'achievement' 
  | 'anomaly' 
  | 'log'
  | 'ui.route.mount'
  | 'ui.adapter.bind'
  | 'game.tick.pulse'
  | 'game.save.snapshot'
  | 'game.prestige.exec'
  | 'culture_ship.ui'
  | 'mode.switch';

export interface EventPayload {
  timestamp: number;
  source: string;
  data: any;
  trace_id?: string;
  golden_trace?: boolean;
}

type EventSubscriber = (payload: EventPayload) => void;

class EventBus {
  private topics = new Map<EventKind, Set<EventSubscriber>>();
  private goldenTraces: EventPayload[] = [];
  private receiptBuffer: EventPayload[] = [];

  on(eventKind: EventKind, subscriber: EventSubscriber): () => void {
    if (!this.topics.has(eventKind)) {
      this.topics.set(eventKind, new Set());
    }
    
    this.topics.get(eventKind)!.add(subscriber);
    
    // Return unsubscribe function
    return () => {
      this.topics.get(eventKind)?.delete(subscriber);
    };
  }

  off(eventKind: EventKind, subscriber: EventSubscriber): void {
    this.topics.get(eventKind)?.delete(subscriber);
  }

  emit(eventKind: EventKind, data: any, source = 'unknown'): void {
    const payload: EventPayload = {
      timestamp: Date.now(),
      source,
      data,
      trace_id: this.generateTraceId(),
      golden_trace: this.isGoldenTrace(eventKind),
    };

    // Store golden traces
    if (payload.golden_trace) {
      this.goldenTraces.push(payload);
      console.log(`[BUS:GOLDEN] ${eventKind} from ${source}`);
    }

    // Buffer for receipts
    this.receiptBuffer.push(payload);
    if (this.receiptBuffer.length > 1000) {
      this.receiptBuffer = this.receiptBuffer.slice(-500); // Keep last 500
    }

    // Emit to subscribers
    const subscribers = this.topics.get(eventKind);
    if (subscribers) {
      subscribers.forEach(fn => {
        try {
          fn(payload);
        } catch (error) {
          console.error(`[BUS:ERROR] Subscriber failed for ${eventKind}:`, error);
        }
      });
    }
  }

  // Get golden traces for telemetry
  getGoldenTraces(): EventPayload[] {
    return [...this.goldenTraces];
  }

  // Check if all required golden traces have fired
  checkGoldenTraceCompleteness(): {
    complete: boolean;
    missing: EventKind[];
    present: EventKind[];
  } {
    const requiredTraces: EventKind[] = [
      'ui.route.mount',
      'ui.adapter.bind', 
      'game.tick.pulse',
      'game.save.snapshot',
      'game.prestige.exec',
    ];

    const presentTraces = new Set(
      this.goldenTraces.map(trace => trace.data.event_kind as EventKind)
    );

    const missing = requiredTraces.filter(trace => !presentTraces.has(trace));
    
    return {
      complete: missing.length === 0,
      missing,
      present: [...presentTraces],
    };
  }

  // Get recent events for debugging
  getRecentEvents(count = 50): EventPayload[] {
    return this.receiptBuffer.slice(-count);
  }

  // Clear old traces (for memory management)
  clearOldTraces(olderThanMs = 60000): void {
    const cutoff = Date.now() - olderThanMs;
    this.goldenTraces = this.goldenTraces.filter(trace => trace.timestamp > cutoff);
    this.receiptBuffer = this.receiptBuffer.filter(event => event.timestamp > cutoff);
  }

  private generateTraceId(): string {
    return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private isGoldenTrace(eventKind: EventKind): boolean {
    const goldenEvents: EventKind[] = [
      'ui.route.mount',
      'ui.adapter.bind',
      'game.tick.pulse', 
      'game.save.snapshot',
      'game.prestige.exec',
    ];
    
    return goldenEvents.includes(eventKind);
  }
}

// Singleton instance
export const Bus = new EventBus();

// Convenience helpers for common patterns
export const emitGoldenTrace = {
  uiRouteMount: (component: string) => 
    Bus.emit('ui.route.mount', { component, mode: localStorage.getItem('PLAY_MODE') }, 'ui'),
  
  uiAdapterBind: (adapter: string, engine: string) =>
    Bus.emit('ui.adapter.bind', { adapter, engine }, 'adapter'),
  
  gameTickPulse: (deltaTime: number, resources: any) =>
    Bus.emit('game.tick.pulse', { deltaTime, resources }, 'game'),
  
  gameSaveSnapshot: (saveData: any, version: string) =>
    Bus.emit('game.save.snapshot', { saveData, version }, 'save'),
  
  gamePrestigeExec: (oldResources: any, newResources: any, metaCurrency: number) =>
    Bus.emit('game.prestige.exec', { oldResources, newResources, metaCurrency }, 'prestige'),
};

// Mode switching helper
export function switchMode(newMode: 'dev_menu' | 'game'): void {
  localStorage.setItem('PLAY_MODE', newMode);
  Bus.emit('mode.switch', { newMode, timestamp: Date.now() }, 'ui');
  
  // Trigger React re-render if available
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('mode-switch', { detail: { mode: newMode } }));
  }
}

// Export for server-side telemetry
export { EventBus };