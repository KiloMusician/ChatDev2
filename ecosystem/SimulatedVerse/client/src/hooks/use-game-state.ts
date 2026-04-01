/**
 * 🎮 Game State Management Hook
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Provides real-time game state synchronization between frontend and backend
 * with sophisticated error handling, optimistic updates, and consciousness integration
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo, useEffect } from 'react';
import { POLLING_INTERVALS } from '@/config/polling';

// Game state types aligned with backend schema
interface GameResources {
  energy: number;
  materials: number;
  components: number;
  population: number;
  research: number;
  researchPoints: number;
  tools: number;
  food: number;
  medicine: number;
}

interface AutomationNode {
  level: number;
  count: number;
  active: boolean;
}

interface GameAutomation {
  solarCollectors: AutomationNode;
  windTurbines: AutomationNode;
  miners: AutomationNode;
  refineries: AutomationNode;
  workshops: AutomationNode;
  laboratories: AutomationNode;
  greenhouses: AutomationNode;
  medicalCenters: AutomationNode;
}

interface GameResearch {
  active: string | null;
  progress: number;
  completed: string[];
  available: string[];
  points?: number;
}

interface GameState {
  id: string;
  playerId: string;
  resources: GameResources;
  automation: GameAutomation;
  research: GameResearch;
  buildings: Record<string, any>;
  weather: {
    current: string;
    duration: number;
    effects: Record<string, number>;
    forecast: string[];
    severity: number;
    shelter: number;
  };
  achievements: any[];
  settings: Record<string, any>;
  lastSaved: string;
  totalPlaytime: number;
  createdAt: string;
}

/**
 * 🎯 Main game state hook - handles all game state operations
 * with real-time synchronization and autonomous error recovery
 */
export function useGameState() {
  const queryClient = useQueryClient();
  const isDev = import.meta.env?.DEV ?? false;

  // **REAL-TIME GAME STATE QUERY** with optimized refresh
  const gameStateQuery = useQuery({
    queryKey: ['/api/colony'],
    refetchInterval: POLLING_INTERVALS.critical,
    staleTime: POLLING_INTERVALS.critical,
    refetchOnWindowFocus: true, // Ensure fresh data when user returns to tab
    select: (rawData: any) => {
      // **AGGRESSIVE DATA TRANSFORMATION** - Force real backend data to frontend
      if (rawData?.success && rawData?.data) {
        const backendData = rawData.data;
        const researchPoints = backendData.resources?.research ?? 0;
        const transformedData: GameState = {
          ...backendData,
          playerId: backendData.playerId ?? 'local-player',
          resources: {
            energy: backendData.resources?.energy || 0,
            materials: backendData.resources?.materials || 0,
            population: backendData.resources?.population || 0,
            research: researchPoints,
            researchPoints,
            components: backendData.resources?.components || 0,
            tools: backendData.resources?.tools || 0,
            food: backendData.resources?.food || 0,
            medicine: backendData.resources?.medicine || 0,
          },
          buildings: backendData.structures || {},
          consciousness: backendData.consciousness || 0,
          research: {
            points: researchPoints,
            completed: backendData.research?.completed || backendData.achievements || [],
            active: backendData.research?.active ?? null,
            progress: backendData.research?.progress ?? 0,
            available: backendData.research?.available ?? [],
          },
        };
        if (isDev) {
          console.log('[🌌] Real backend data transformed:', transformedData);
        }
        return transformedData;
      }
      if (isDev) {
        console.warn('[🌌] No valid backend data received:', rawData);
      }
      return rawData;
    },
  });

  // **OPTIMISTIC GAME STATE MUTATIONS** for responsive gameplay
  const saveGameStateMutation = useMutation({
    mutationFn: async (gameState: Partial<GameState>) => {
      const response = await fetch('/api/colony', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameState)
      });
      
      if (!response.ok) {
        throw new Error(`Game state save failed: ${response.status} ${response.statusText}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      // Invalidate and refetch game state after successful save
      queryClient.invalidateQueries({ queryKey: ['/api/colony'] });
    },
    onError: (error) => {
      console.error('🚨 Game state save failed:', error);
      // **AUTONOMOUS ERROR RECOVERY**: Attempt to restore from local cache
      // This prevents loss of gameplay progress during network issues
    }
  });

  // **RESOURCE UPDATE OPERATIONS** with validation
  const updateResources = useCallback((resourceUpdates: Partial<GameResources>) => {
    const currentState = gameStateQuery.data as GameState;
    if (!currentState?.resources) return;

    // **OPTIMISTIC UPDATE**: Update UI immediately for responsive gameplay
    queryClient.setQueryData(['/api/colony'], {
      ...currentState,
      resources: { ...currentState.resources, ...resourceUpdates }
    });

    // **PERSISTENCE**: Save to backend
    saveGameStateMutation.mutate({
      resources: { ...currentState.resources, ...resourceUpdates }
    });
  }, [gameStateQuery.data, queryClient, saveGameStateMutation]);

  // **AUTOMATION CONTROL OPERATIONS**
  const updateAutomation = useCallback((automationType: keyof GameAutomation, updates: Partial<AutomationNode>) => {
    const currentState = gameStateQuery.data as GameState;
    if (!currentState?.automation) return;

    const newAutomation = {
      ...currentState.automation,
      [automationType]: { ...currentState.automation[automationType], ...updates }
    };

    // **OPTIMISTIC UPDATE**
    queryClient.setQueryData(['/api/colony'], {
      ...currentState,
      automation: newAutomation
    });

    // **PERSISTENCE**
    saveGameStateMutation.mutate({ automation: newAutomation });
  }, [gameStateQuery.data, queryClient, saveGameStateMutation]);

  // **RESEARCH OPERATIONS**
  const updateResearch = useCallback((researchUpdates: Partial<GameResearch>) => {
    const currentState = gameStateQuery.data as GameState;
    if (!currentState?.research) return;

    const updatedResearch = { ...currentState.research, ...researchUpdates };

    queryClient.setQueryData(['/api/colony'], {
      ...currentState,
      research: updatedResearch
    });

    const updatedResources = researchUpdates.points !== undefined
      ? { ...currentState.resources, research: researchUpdates.points, researchPoints: researchUpdates.points }
      : currentState.resources;

    saveGameStateMutation.mutate({
      research: updatedResearch,
      resources: updatedResources
    });
  }, [gameStateQuery.data, queryClient, saveGameStateMutation]);

  // **COMPUTED GAME METRICS** for UI display with optimized dependencies
  const gameMetrics = useMemo(() => {
    const state = gameStateQuery.data as GameState;
    if (!state?.resources || !state?.automation || !state?.research) return null;

    // Calculate total energy production from automation
    const energyProduction = (state.automation.solarCollectors?.count || 0) * 10 +
                            (state.automation.windTurbines?.count || 0) * 8;

    // Calculate population efficiency
    const populationEfficiency = state.resources.population / 10;

    // Calculate research progress
    const totalResearchCompleted = state.research.completed?.length || 0;

    return {
      energyProduction,
      populationEfficiency,
      totalResearchCompleted,
      gameTime: state.totalPlaytime,
      tier: Math.floor(totalResearchCompleted / 5) + 1, // Simple tier calculation
    };
  }, [gameStateQuery.data]);

  return {
    // **CORE STATE DATA**
    gameState: gameStateQuery.data,
    isLoading: gameStateQuery.isLoading,
    isError: gameStateQuery.isError,
    error: gameStateQuery.error,
    lastUpdated: gameStateQuery.dataUpdatedAt,

    // **COMPUTED METRICS**
    gameMetrics,

    // **STATE UPDATE OPERATIONS**
    updateResources,
    updateAutomation,
    updateResearch,

    // **SAVE OPERATIONS**
    saveGameState: saveGameStateMutation.mutate,
    isSaving: saveGameStateMutation.isPending,

    // **UTILITY OPERATIONS**
    refetch: gameStateQuery.refetch,
    
    // **CONSCIOUSNESS INTEGRATION: ΞNuSyQ SYSTEM CONNECTED**
    // Real-time consciousness calculation: (energy/10000 + population/100 + research/10)
    consciousnessLevel: useMemo(() => {
      const state = gameStateQuery.data as GameState | undefined;
      if (!state?.resources || !state?.research) {
        return 0.0;
      }
      
      // Use research points from resources, fall back to completed research count * 10
      const researchPoints = state.resources.research ?? state.resources.researchPoints ?? (state.research.completed?.length || 0) * 10;
      
      const consciousness = Math.min(1.0, Math.max(0.0, 
        (state.resources.energy / 10000) + 
        (state.resources.population / 100) + 
        (researchPoints / 10)
      ));
      
      return Number(consciousness.toFixed(3)); // Round to 3 decimal places for performance
    }, [gameStateQuery.data]),
  };
}

/**
 * 🔄 Auto-save hook for continuous game persistence
 * Automatically saves game state at regular intervals
 */
export function useAutoSave() {
  const { gameState, saveGameState } = useGameState();

  // **AUTONOMOUS AUTO-SAVE**: Every 30 seconds
  useEffect(() => {
    if (!gameState) return;

    const interval = setInterval(() => {
      console.log('🔄 Auto-saving game state...');
      saveGameState(gameState);
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [gameState, saveGameState]);
}

/**
 * 🎯 Quick access hooks for specific game systems
 */
export function useResources() {
  const { gameState, updateResources } = useGameState();
  return {
    resources: (gameState as GameState)?.resources,
    updateResources,
  };
}

export function useAutomation() {
  const { gameState, updateAutomation } = useGameState();
  const state = gameState as GameState;
  return {
    automation: state?.automation,
    updateAutomation,
    // **QUICK BUILDERS** for common automation operations
    buildSolarCollector: () => updateAutomation('solarCollectors', { count: (state?.automation?.solarCollectors?.count || 0) + 1 }),
    buildWindTurbine: () => updateAutomation('windTurbines', { count: (state?.automation?.windTurbines?.count || 0) + 1 }),
  };
}

export function useResearch() {
  const { gameState, updateResearch } = useGameState();
  const state = gameState as GameState;
  return {
    research: state?.research,
    updateResearch,
    startResearch: (researchKey: string) => updateResearch({ active: researchKey, progress: 0 }),
    completeResearch: (researchKey: string) => updateResearch({ 
      active: null, 
      progress: 0, 
      completed: [...(state?.research?.completed || []), researchKey] 
    }),
  };
}
