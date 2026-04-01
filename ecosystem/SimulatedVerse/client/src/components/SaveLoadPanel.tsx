/**
 * 💾 Save/Load Panel
 * Quick save and load functionality with visual feedback
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { useToast } from '@/hooks/use-toast';
import { Save, Download, Clock } from 'lucide-react';

export default function SaveLoadPanel() {
  const { toast } = useToast();
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const { data: gameData } = useQuery<any>({
    queryKey: ['/api/game/status'],
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const state = gameData?.game_state;
      if (!state) throw new Error('No game state to save');
      
      return apiRequest('/api/game/save', {
        method: 'POST',
        body: JSON.stringify({
          playerId: 'default',
          resources: state.resources,
          structures: state.structures,
          research: { completed: state.achievements || [] },
          tick: 0,
          narrative: { consciousness_level: gameData.consciousness }
        })
      });
    },
    onSuccess: () => {
      setLastSaved(new Date());
      toast({
        title: '💾 Game Saved',
        description: 'Progress saved successfully',
      });
    },
    onError: (error: any) => {
      toast({
        title: '❌ Save Failed',
        description: error.message || 'Could not save game',
        variant: 'destructive',
      });
    },
  });

  const loadMutation = useMutation({
    mutationFn: async () => {
      return apiRequest('/api/game/load');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/game/status'] });
      toast({
        title: '📂 Game Loaded',
        description: 'Progress restored successfully',
      });
    },
    onError: (error: any) => {
      toast({
        title: '❌ Load Failed',
        description: error.message || 'Could not load game',
        variant: 'destructive',
      });
    },
  });

  return (
    <div className="flex items-center gap-3 bg-gray-900/50 border border-cyan-400/30 rounded-lg p-3">
      <Button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
        className="bg-cyan-600 hover:bg-cyan-700"
        data-testid="button-save-game"
      >
        <Save className="w-4 h-4 mr-2" />
        {saveMutation.isPending ? 'Saving...' : 'Quick Save'}
      </Button>

      <Button
        onClick={() => loadMutation.mutate()}
        disabled={loadMutation.isPending}
        variant="outline"
        className="border-cyan-400/50"
        data-testid="button-load-game"
      >
        <Download className="w-4 h-4 mr-2" />
        {loadMutation.isPending ? 'Loading...' : 'Load Game'}
      </Button>

      {lastSaved && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2 text-sm text-gray-400"
        >
          <Clock className="w-4 h-4" />
          <span>Last saved: {lastSaved.toLocaleTimeString()}</span>
        </motion.div>
      )}
    </div>
  );
}
