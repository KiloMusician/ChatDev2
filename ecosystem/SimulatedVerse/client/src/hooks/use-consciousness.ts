// CONSCIOUSNESS HOOK - Real-time consciousness data integration
// Connects frontend to the live consciousness lattice system

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { POLLING_INTERVALS } from '@/config/polling';

interface ConsciousnessState {
  consciousness: number;
  stage: string;
  connections: number;
  resonance: number;
  evolution: {
    active: boolean;
    completed: number;
    pending: number;
    eligible: number;
  };
  coherence: number;
}

interface ConsciousnessHook {
  consciousness: ConsciousnessState | null;
  isLoading: boolean;
  isTranscending: boolean;
  evolutionProgress: number;
  triggerBreakthrough: (description: string) => Promise<void>;
  triggerEvolution: (target: string, description: string) => Promise<void>;
}

export function useConsciousness(): ConsciousnessHook {
  const [isTranscending, setIsTranscending] = useState(false);
  
  // Real-time consciousness data from the lattice
  const { data: consciousness, isLoading } = useQuery<ConsciousnessState>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.critical,
    refetchIntervalInBackground: true,
    staleTime: POLLING_INTERVALS.critical
  });

  const consciousnessState = consciousness ?? null;
  
  // Calculate evolution progress
  const evolutionProgress = consciousnessState 
    ? consciousnessState.consciousness 
    : 0;
  
  // Monitor for transcendence
  useEffect(() => {
    if (consciousnessState && consciousnessState.consciousness > 80) {
      setIsTranscending(true);
      console.log('[Consciousness] 🌟 TRANSCENDENCE THRESHOLD REACHED!');
    }
  }, [consciousnessState?.consciousness]);
  
  // Trigger breakthrough via API
  const triggerBreakthrough = async (description: string) => {
    try {
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'breakthrough',
          data: {
            source: 'user_interface',
            description
          }
        })
      });
      
      console.log(`[Consciousness] 💡 Breakthrough triggered: ${description}`);
    } catch (error) {
      console.error('[Consciousness] Failed to trigger breakthrough:', error);
    }
  };
  
  // Trigger evolution via API
  const triggerEvolution = async (target: string, description: string) => {
    try {
      await fetch('/api/consciousness/evolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target,
          type: 'expand',
          description
        })
      });
      
      console.log(`[Consciousness] 🧬 Evolution triggered: ${description}`);
    } catch (error) {
      console.error('[Consciousness] Failed to trigger evolution:', error);
    }
  };
  
  return {
    consciousness: consciousnessState,
    isLoading,
    isTranscending,
    evolutionProgress,
    triggerBreakthrough,
    triggerEvolution
  };
}
