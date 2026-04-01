/**
 * ETag-Aware Provision State Hook
 * 
 * Efficient polling of /system-status.json and other provision endpoints
 * with smart caching and minimal bandwidth usage for the tripartite system.
 */

import useSWR from "swr";
import { safeJsonParse, safeAsync } from "../../../packages/util/safe.js";

interface ProvisionedState {
  consciousness_level?: number;
  energy?: number;
  population?: number;
  research?: number;
  queue_size?: number;
  agents_active?: number;
  system_ready?: boolean;
  timestamp?: number;
  [key: string]: any;
}

const fetcher = async (url: string): Promise<ProvisionedState> => {
  return safeAsync(async () => {
    const response = await fetch(url, { 
      cache: "no-store",
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Fetch ${url} => ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  }, {});
};

export function useProvisionedState() {
  return useSWR("/system-status.json", fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    refreshInterval: 8000, // 8 second polls for real-time feel
    errorRetryCount: 3,
    errorRetryInterval: 2000,
    dedupingInterval: 4000, // Dedupe within 4 seconds
  });
}

export function useBuildStamp() {
  return useSWR("/build-stamp.json", fetcher, {
    revalidateOnFocus: true,
    revalidateOnReconnect: true,
    refreshInterval: 30000, // Check build changes every 30 seconds
    errorRetryCount: 1,
    dedupingInterval: 10000,
  });
}

export function useQueueStatus() {
  return useSWR("/api/pu/queue", fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    refreshInterval: 5000, // Monitor queue every 5 seconds
    errorRetryCount: 2,
    dedupingInterval: 2000,
  });
}

export function useHealthStatus() {
  return useSWR("/api/health", fetcher, {
    revalidateOnFocus: true,
    revalidateOnReconnect: true,
    refreshInterval: 15000, // Health check every 15 seconds
    errorRetryCount: 5,
    dedupingInterval: 5000,
  });
}

// Tripartite system status aggregator
export function useTripartiteStatus() {
  const provision = useProvisionedState();
  const queue = useQueueStatus();
  const health = useHealthStatus();
  
  return {
    // System Layer Status
    system: {
      ready: provision.data?.system_ready ?? false,
      consciousness: provision.data?.consciousness_level ?? 0,
      queue_size: queue.data?.size ?? 0,
      health: health.data?.overall ?? 'unknown'
    },
    
    // Game Layer Status
    game: {
      energy: provision.data?.energy ?? 0,
      population: provision.data?.population ?? 0,
      research: provision.data?.research ?? 0,
    },
    
    // Simulation Layer Status
    simulation: {
      agents_active: provision.data?.agents_active ?? 0,
      timestamp: provision.data?.timestamp ?? Date.now()
    },
    
    // Combined loading state
    isLoading: provision.isLoading || queue.isLoading || health.isLoading,
    error: provision.error || queue.error || health.error
  };
}