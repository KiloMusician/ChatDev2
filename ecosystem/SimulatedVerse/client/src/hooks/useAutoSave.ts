import { useEffect, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';
import { useToast } from '@/hooks/use-toast';
import { useGameStore } from '@/store/gameStore';

const AUTO_SAVE_INTERVAL = 30000; // Auto-save every 30 seconds
const MANUAL_SAVE_DEBOUNCE = 3000; // Debounce manual saves by 3 seconds

interface SaveGameParams {
  playerId: string;
  gameState: any;
}

export function useAutoSave() {
  const { toast } = useToast();
  const gameState = useGameStore();
  const lastSaveRef = useRef<Date | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const sessionStartRef = useRef<Date>(new Date());
  
  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async (params: SaveGameParams) => {
      const response = await apiRequest('/api/game/save', {
        method: 'POST',
        body: JSON.stringify(params)
      }) as Response;
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save game');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      lastSaveRef.current = new Date();
      console.log('[AutoSave] Game saved successfully:', data.gameId);
    },
    onError: (error) => {
      console.error('[AutoSave] Save failed:', error);
      toast({
        title: 'Auto-save failed',
        description: 'Your progress may not be saved. Please try saving manually.',
        variant: 'destructive'
      });
    }
  });
  
  // Load game mutation
  const loadMutation = useMutation({
    mutationFn: async (playerId: string) => {
      const response = await apiRequest(`/api/game/load/${playerId}`, {
        method: 'GET'
      }) as Response;
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to load game');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      if (data.gameState && data.gameState.id !== 'default') {
        // Update game store with loaded state
        gameState.setResources(data.gameState.resources);
        gameState.setStructures(data.gameState.structures);
        gameState.setAutomation(data.gameState.automation);
        gameState.setConsciousness(data.gameState.consciousness);
        
        toast({
          title: 'Game loaded',
          description: 'Your previous progress has been restored.'
        });
      }
    },
    onError: (error) => {
      console.error('[AutoSave] Load failed:', error);
      toast({
        title: 'Load failed',
        description: 'Starting with a new game.',
        variant: 'destructive'
      });
    }
  });
  
  // Calculate session time
  const getSessionTime = useCallback(() => {
    const now = new Date();
    return Math.floor((now.getTime() - sessionStartRef.current.getTime()) / 1000);
  }, []);
  
  // Get current game state
  const getCurrentGameState = useCallback(() => {
    return {
      resources: gameState.resources,
      structures: gameState.structures,
      automation: gameState.automation,
      consciousness: gameState.consciousness,
      achievements: gameState.achievements || [],
      statistics: {
        totalClicks: gameState.totalClicks || 0,
        totalEnergy: gameState.totalEnergyGenerated || 0,
        totalMaterials: gameState.totalMaterialsGathered || 0,
        sessionTime: getSessionTime()
      },
      sessionTime: getSessionTime(),
      newAchievements: [] // Track new achievements in this session
    };
  }, [gameState, getSessionTime]);
  
  // Save game function
  const saveGame = useCallback(async (force = false) => {
    // Skip if already saving
    if (saveMutation.isPending) {
      console.log('[AutoSave] Save already in progress, skipping');
      return;
    }
    
    // Check if enough time has passed since last save (unless forced)
    if (!force && lastSaveRef.current) {
      const timeSinceLastSave = Date.now() - lastSaveRef.current.getTime();
      if (timeSinceLastSave < MANUAL_SAVE_DEBOUNCE) {
        console.log('[AutoSave] Too soon since last save, skipping');
        return;
      }
    }
    
    // Get player ID (in production, this would come from auth)
    const playerId = localStorage.getItem('playerId') || 'default-player';
    
    // Save the game
    const gameStateData = getCurrentGameState();
    saveMutation.mutate({
      playerId,
      gameState: gameStateData
    });
  }, [saveMutation, getCurrentGameState]);
  
  // Load game function
  const loadGame = useCallback(async () => {
    const playerId = localStorage.getItem('playerId') || 'default-player';
    loadMutation.mutate(playerId);
  }, [loadMutation]);
  
  // Manual save with debounce
  const triggerManualSave = useCallback(() => {
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Set new timeout for debounced save
    saveTimeoutRef.current = setTimeout(() => {
      saveGame(true);
      toast({
        title: 'Game saved',
        description: 'Your progress has been saved manually.'
      });
    }, 500);
  }, [saveGame, toast]);
  
  // Set up auto-save interval
  useEffect(() => {
    // Load game on mount
    loadGame();
    
    // Set up auto-save interval
    const interval = setInterval(() => {
      saveGame(false);
    }, AUTO_SAVE_INTERVAL);
    
    // Save on page unload
    const handleUnload = () => {
      saveGame(true);
    };
    
    window.addEventListener('beforeunload', handleUnload);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('beforeunload', handleUnload);
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [saveGame, loadGame]);
  
  // Save when game state changes significantly
  useEffect(() => {
    const significantChange = 
      gameState.consciousness % 10 === 0 || // Every 10% consciousness
      gameState.resources.research % 100 === 0; // Every 100 research points
    
    if (significantChange && lastSaveRef.current) {
      const timeSinceLastSave = Date.now() - lastSaveRef.current.getTime();
      if (timeSinceLastSave > 10000) { // At least 10 seconds since last save
        saveGame(false);
      }
    }
  }, [gameState.consciousness, gameState.resources.research, saveGame]);
  
  return {
    saveGame: triggerManualSave,
    loadGame,
    isSaving: saveMutation.isPending,
    isLoading: loadMutation.isPending,
    lastSave: lastSaveRef.current,
    saveError: saveMutation.error,
    loadError: loadMutation.error
  };
}