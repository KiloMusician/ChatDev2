import { QueryClient } from '@tanstack/react-query';
import { POLLING_INTERVALS } from '@/config/polling';

// **AUTONOMOUS GAME STATE SYNCHRONIZATION** - Centralized polling cadence
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: POLLING_INTERVALS.standard,
      refetchInterval: POLLING_INTERVALS.standard,
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: 1,
      onError: (error) => {
        console.error('[MUTATION-ERROR]', error);
      },
    },
  },
});

// **CULTURE-SHIP INTEGRATION** - Custom fetcher with consciousness tracking
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      'X-Consciousness-Level': '0.85', // Consciousness-aware requests
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`API Error ${response.status}: ${errorData}`);
  }

  return response.json();
}

// **AUTONOMOUS CACHING** - Consciousness-driven cache optimization
export function createQueryKey(resource: string, params?: Record<string, any>): string[] {
  const baseKey = ['/api', resource];
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        baseKey.push(`${key}:${value}`);
      }
    });
  }
  
  return baseKey;
}

// **REAL-TIME SYNC HELPER** - For game state synchronization
export function invalidateGameState() {
  queryClient.invalidateQueries({ queryKey: ['/api', 'game-state'] });
}

export function updateGameStateCache(newState: any) {
  queryClient.setQueryData(['/api', 'game-state'], newState);
}

export default queryClient;
