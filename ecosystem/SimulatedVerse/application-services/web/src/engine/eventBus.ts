export type EventPayload = Record<string, unknown>;
type Listener = (p: EventPayload) => void;

export class EventBus {
  private map = new Map<string, Set<Listener>>();
  
  on(type: string, listener: Listener) {
    if (!this.map.has(type)) this.map.set(type, new Set());
    this.map.get(type)!.add(listener);
  }
  
  off(type: string, listener: Listener) { 
    this.map.get(type)?.delete(listener); 
  }
  
  emit(type: string, payload: EventPayload = {}) { 
    this.map.get(type)?.forEach(fn => fn(payload)); 
  }
}

export const bus = new EventBus();