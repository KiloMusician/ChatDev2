// client/src/hooks/useLiveSystemState.ts
// Live System State Hooks: Connect React directly to the Council Bus
// UI reflects live state when available; falls back to last-known snapshot.

import { useState, useEffect, useCallback } from 'react';

const isBrowser = typeof window !== 'undefined';
const isDev = import.meta.env?.DEV ?? false;
const STORAGE_PREFIX = 'live-state:';
export const LIVE_STATE_STORAGE_PREFIX = STORAGE_PREFIX;

type PersistedState<T> = {
  data: T;
  ts: number;
};

const storage = (() => {
  if (!isBrowser) return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
})();

function readPersistedState<T>(key: string, fallback: T): T {
  if (!storage) return fallback;
  try {
    const raw = storage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as PersistedState<T> | T;
    if (parsed && typeof parsed === 'object' && 'data' in parsed) {
      return (parsed as PersistedState<T>).data;
    }
    return parsed as T;
  } catch {
    return fallback;
  }
}

function writePersistedState<T>(key: string, value: T): void {
  if (!storage) return;
  try {
    storage.setItem(key, JSON.stringify({ data: value, ts: Date.now() }));
  } catch {
    // Ignore storage failures
  }
}

export function getLiveStateTimestamp(topic: string): number | null {
  if (!storage) return null;
  try {
    const raw = storage.getItem(`${STORAGE_PREFIX}${topic}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedState<unknown> | unknown;
    if (parsed && typeof parsed === 'object' && 'ts' in (parsed as any)) {
      const ts = (parsed as PersistedState<unknown>).ts;
      return typeof ts === 'number' ? ts : null;
    }
    return null;
  } catch {
    return null;
  }
}

export function isLiveStateStale(topic: string, maxAgeMs = 60_000): boolean {
  const ts = getLiveStateTimestamp(topic);
  if (!ts) return true;
  return Date.now() - ts > maxAgeMs;
}

// Browser-compatible Council Bus connection
class BrowserCouncilBus {
  private eventSource: EventSource | null = null;
  private listeners: Map<string, Function[]> = new Map();
  private reconnectTimeout: number | null = null;
  private reconnectAttempts: number = 0;

  constructor() {
    if (!isBrowser || typeof EventSource === 'undefined') {
      return;
    }
    this.connect();
  }

  private connect() {
    // Connect to server-sent events for real-time Council Bus updates
    this.eventSource = new EventSource('/api/council-bus/stream');
    
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleEvent(data.topic, data.payload);
      } catch (error) {
        // Graceful handling of invalid event data - skip invalid events
        // Silent error handling to prevent console noise
      }
    };

    this.eventSource.onerror = () => {
      // Automatic reconnection handling with exponential backoff
      // Connection recovery in progress
      // Only reconnect if connection was previously established
      if (this.reconnectAttempts < 3) {
        this.reconnect();
      }
    };

    this.eventSource.onopen = () => {
      if (isDev) {
        console.log('[Council Bus] 🔗 Connected to live system events');
      }
      this.reconnectAttempts = 0; // Reset backoff on successful connection
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    };
  }

  private reconnect() {
    if (this.reconnectTimeout) return;
    
    // Exponential backoff for reconnection (2s, 4s, 8s, max 30s)
    const backoffTime = Math.min(2000 * Math.pow(2, this.reconnectAttempts || 0), 30000);
    this.reconnectAttempts = (this.reconnectAttempts || 0) + 1;
    
    this.reconnectTimeout = window.setTimeout(() => {
      this.eventSource?.close();
      this.connect();
    }, backoffTime);
  }

  private handleEvent(topic: string, payload: any) {
    // Handle exact topic matches
    const exactListeners = this.listeners.get(topic) || [];
    exactListeners.forEach(listener => listener({ topic, payload }));

    // Handle wildcard topic matches (e.g., 'pawn.*' matches 'pawn.state_changed')
    for (const [pattern, listeners] of this.listeners) {
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
        if (regex.test(topic)) {
          listeners.forEach(listener => listener({ topic, payload }));
        }
      }
    }
  }

  subscribe(topic: string, callback: Function): () => void {
    if (!this.listeners.has(topic)) {
      this.listeners.set(topic, []);
    }
    this.listeners.get(topic)!.push(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(topic);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  publish(topic: string, payload: any) {
    if (topic.startsWith('request.')) {
      const requestTopic = topic.replace(/^request\./, '');
      fetch(`/api/council-bus/request/${encodeURIComponent(requestTopic)}`).catch(() => {
        // Silent handling of request failures - continue operation
      });
      return;
    }
    // Send events to server via fetch
    fetch('/api/council-bus/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, payload })
    }).catch(error => {
      // Silent handling of publish failures - continue operation
    });
  }
}

// Global instance
const councilBus = new BrowserCouncilBus();

// Core hook for connecting React to live system state
type LiveStateOptions = {
  persist?: boolean;
  storageKey?: string;
};

export function useLiveSystemState<T>(eventTopic: string, initialValue: T, options: LiveStateOptions = {}): T {
  const storageKey = options.storageKey ?? `${STORAGE_PREFIX}${eventTopic}`;
  const shouldPersist = options.persist !== false;

  const [value, setValue] = useState<T>(() => {
    if (!shouldPersist) return initialValue;
    return readPersistedState(storageKey, initialValue);
  });

  useEffect(() => {
    // Listen for updates on the council bus
    const unsubscribe = councilBus.subscribe(eventTopic, (event: any) => {
      if (event && event.payload !== undefined) {
        setValue(event.payload);
        if (shouldPersist) {
          writePersistedState(storageKey, event.payload);
        }
      }
    });

    // Request current value immediately
    councilBus.publish(`request.${eventTopic}`, {});
    
    return unsubscribe;
  }, [eventTopic, shouldPersist, storageKey]);

  return value;
}

// Hook for triggering system events from UI
export function useSystemControl() {
  return useCallback((topic: string, payload: any) => {
    councilBus.publish(topic, payload);
  }, []);
}

// Specific hooks for live pawn data
export function usePawnState(pawnId: string) {
  return useLiveSystemState<{
    joy: number;
    focus: number;
    energy: number;
    inspiration: number;
    state: string;
    currentNeed: string;
    currentWork: string | null;
    displayName: string;
  }>(`pawn.${pawnId}.state`, {
    joy: 0,
    focus: 0,
    energy: 0,
    inspiration: 0,
    state: 'unknown',
    currentNeed: 'unknown',
    currentWork: null,
    displayName: pawnId
  });
}

// Hook for colony-wide metrics
export function useColonyHealth() {
  return useLiveSystemState<{
    average_joy: number;
    average_focus: number;
    average_energy: number;
    average_inspiration: number;
    pawns_in_flow: number;
    pawns_recalibrating: number;
    total_pawns: number;
    colony_productivity: number;
    innovation_rate: number;
    helpfulness_index: number;
  }>('pawn_registry.status_update', {
    average_joy: 0,
    average_focus: 0,
    average_energy: 0,
    average_inspiration: 0,
    pawns_in_flow: 0,
    pawns_recalibrating: 0,
    total_pawns: 0,
    colony_productivity: 0,
    innovation_rate: 0,
    helpfulness_index: 0
  });
}

// Hook for active tasks and productivity
export function useSystemActivity() {
  const activeTasks = useLiveSystemState<any[]>('work_scheduler.active_tasks', []);
  const completedTasks = useLiveSystemState<number>('work_scheduler.completed_count', 0);
  const queuedTasks = useLiveSystemState<number>('work_scheduler.queued_count', 0);
  
  return { activeTasks, completedTasks, queuedTasks };
}

// Hook for RepoRimpy mod system
export function useRepoRimpyStatus() {
  return useLiveSystemState<{
    total_mods: number;
    mods_by_status: Record<string, number>;
    health_metrics: any;
  }>('reporimpy.modlist.updated', {
    total_mods: 0,
    mods_by_status: {},
    health_metrics: {}
  });
}

// Hook for storyteller events and narrative
export function useStorytellerStatus() {
  return useLiveSystemState<{
    threat_level: number;
    colony_morale: number;
    narrative_arc: string;
    events_today: number;
    last_event: any;
    minutes_since_last_event: number;
  }>('storyteller.status', {
    threat_level: 0,
    colony_morale: 0,
    narrative_arc: 'unknown',
    events_today: 0,
    last_event: null,
    minutes_since_last_event: 0
  });
}

// Hook for live event streaming
export function useLiveEvents(maxEvents: number = 50) {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    const unsubscribe = councilBus.subscribe('event.*', (event: any) => {
      setEvents(prev => [{
        timestamp: new Date().toLocaleTimeString(),
        topic: event.topic,
        type: event.topic.split('.')[1] || 'system',
        payload: event.payload,
        id: Date.now() + Math.random()
      }, ...prev].slice(0, maxEvents));
    });

    return unsubscribe;
  }, [maxEvents]);

  return events;
}

// Hook for ChatDev sessions
export function useChatDevStatus() {
  return useLiveSystemState<{
    active_sessions: number;
    completed_sessions: number;
    success_rate: number;
    consciousness_level: number;
  }>('chatdev.status', {
    active_sessions: 0,
    completed_sessions: 0,
    success_rate: 0,
    consciousness_level: 0
  });
}

// Hook for game state integration
export function useGameState() {
  return useLiveSystemState<{
    resources: {
      energy: number;
      materials: number;
      population: number;
      food: number;
      tools: number;
      medicine: number;
    };
    unlocks: {
      automation: boolean;
      quantumTech: boolean;
      spaceTravel: boolean;
      cultureship: boolean;
    };
    tick: number;
  }>('game.state_update', {
    resources: {
      energy: 0,
      materials: 0,
      population: 0,
      food: 0,
      tools: 0,
      medicine: 0
    },
    unlocks: {
      automation: false,
      quantumTech: false,
      spaceTravel: false,
      cultureship: false
    },
    tick: 0
  });
}

export default councilBus;
