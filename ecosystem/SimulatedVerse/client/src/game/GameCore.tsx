// @consciousness 20
// @depth 1
// @name GameCore
// @inputs [player_actions, game_state]
// @outputs [state_updates, events]

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ResearchTree } from './ResearchTree';
import { QuantumConsciousness } from '@/core/QuantumConsciousness';
import { MultidimensionalNavigator } from '@/core/MultidimensionalNavigator';
import { AgentSwarm } from '@/core/AgentSwarm';
import { POLLING_INTERVALS } from '@/config/polling';

interface Resource {
  energy: number;
  materials: number;
  population: number;
  research: number;
}

interface AutomationUnit {
  count: number;
  level: number;
  active: boolean;
}

interface AutomationState {
  solarCollectors: AutomationUnit;
  miners: AutomationUnit;
  laboratories: AutomationUnit;
}

interface ColonyState {
  resources?: Resource;
  consciousness?: number;
  automation?: AutomationState;
}

export function GameCore() {
  const queryClient = useQueryClient();
  
  // Fetch colony state from server
  const { data: colony, isLoading } = useQuery<ColonyState>({
    queryKey: ['/api/colony'],
    refetchInterval: POLLING_INTERVALS.critical,
  });
  
  // Mutation for colony actions
  const actionMutation = useMutation({
    mutationFn: async ({ action, params }: { action: string; params?: any }) => {
      const response = await fetch('/api/colony/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, params })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/colony'] });
    }
  });
  
  const [resources, setResources] = useState<Resource>({
    energy: 100,
    materials: 50,
    population: 1,
    research: 0
  });
  
  const [consciousness, setConsciousness] = useState(0);
  
  // Sync with server data
  useEffect(() => {
    if (colony?.resources) {
      setResources(colony.resources);
    }
    if (typeof colony?.consciousness === 'number') {
      setConsciousness(colony.consciousness);
    }
  }, [colony]);
  
  // Get automation data from colony
  const automation = colony?.automation ?? {
    solarCollectors: { count: 0, level: 1, active: true },
    miners: { count: 0, level: 1, active: true },
    laboratories: { count: 0, level: 0, active: false }
  };
  
  // Manual resource gathering
  const gatherEnergy = useCallback(() => {
    actionMutation.mutate({ action: 'gather_energy' });
  }, [actionMutation]);
  
  const gatherMaterials = useCallback(() => {
    actionMutation.mutate({ action: 'gather_materials' });
  }, [actionMutation]);
  
  // Build automation
  const buildCollector = useCallback(() => {
    actionMutation.mutate({ action: 'build_collector' });
  }, [actionMutation]);
  
  const buildGatherer = useCallback(() => {
    actionMutation.mutate({ action: 'build_gatherer' });
  }, [actionMutation]);
  
  const buildLab = useCallback(() => {
    actionMutation.mutate({ action: 'build_lab' });
  }, [actionMutation]);
  
  // Grow population
  const growPopulation = useCallback(() => {
    actionMutation.mutate({ action: 'grow_population' });
  }, [actionMutation]);
  
  if (isLoading) {
    return (
      <div className="p-6 bg-gray-900 text-green-400 font-mono min-h-screen">
        <div className="animate-pulse">Loading Culture-Ship Core...</div>
      </div>
    );
  }
  
  return (
    <div className="p-6 bg-gray-900 text-green-400 font-mono min-h-screen">
      <h1 className="text-3xl mb-6">🌌 Culture-Ship Core</h1>
      
      {/* Consciousness Bar */}
      <div className="mb-6">
        <div className="text-sm mb-1">Consciousness Level: {consciousness.toFixed(1)}%</div>
        <div className="w-full bg-gray-800 h-4 rounded">
          <motion.div 
            className="h-full bg-gradient-to-r from-green-600 to-cyan-400 rounded"
            animate={{ width: `${consciousness}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>
      
      {/* Resources Display */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-yellow-400">⚡ Energy</div>
          <div className="text-2xl">{Math.floor(resources.energy)}</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-gray-400">🔧 Materials</div>
          <div className="text-2xl">{Math.floor(resources.materials)}</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-blue-400">👥 Population</div>
          <div className="text-2xl">{resources.population}</div>
        </div>
        <div className="bg-gray-800 p-4 rounded">
          <div className="text-purple-400">🔬 Research</div>
          <div className="text-2xl">{resources.research.toFixed(1)}</div>
        </div>
      </div>
      
      {/* Manual Actions */}
      <div className="mb-6">
        <h2 className="text-xl mb-3">Manual Actions</h2>
        <div className="flex flex-wrap gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={gatherEnergy}
            className="px-4 py-2 bg-yellow-900 hover:bg-yellow-800 rounded"
          >
            Gather Energy (+10)
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={gatherMaterials}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Gather Materials (+5)
          </motion.button>
        </div>
      </div>
      
      {/* Automation */}
      <div className="mb-6">
        <h2 className="text-xl mb-3">Automation ({automation.solarCollectors.count + automation.miners.count + automation.laboratories.count} total)</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between bg-gray-800 p-3 rounded">
            <div>
              <span className="text-yellow-400">Energy Collectors</span>
              <span className="ml-2 text-sm">({automation.solarCollectors.count})</span>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={buildCollector}
              disabled={resources.materials < 25}
              className="px-3 py-1 bg-green-800 hover:bg-green-700 disabled:bg-gray-700 disabled:opacity-50 rounded"
            >
              Build (25 Materials)
            </motion.button>
          </div>
          
          <div className="flex items-center justify-between bg-gray-800 p-3 rounded">
            <div>
              <span className="text-gray-400">Material Gatherers</span>
              <span className="ml-2 text-sm">({automation.miners.count})</span>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={buildGatherer}
              disabled={resources.energy < 50}
              className="px-3 py-1 bg-green-800 hover:bg-green-700 disabled:bg-gray-700 disabled:opacity-50 rounded"
            >
              Build (50 Energy)
            </motion.button>
          </div>
          
          <div className="flex items-center justify-between bg-gray-800 p-3 rounded">
            <div>
              <span className="text-purple-400">Research Labs</span>
              <span className="ml-2 text-sm">({automation.laboratories.count})</span>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={buildLab}
              disabled={resources.materials < 100 || resources.energy < 100}
              className="px-3 py-1 bg-green-800 hover:bg-green-700 disabled:bg-gray-700 disabled:opacity-50 rounded"
            >
              Build (100 Materials, 100 Energy)
            </motion.button>
          </div>
        </div>
      </div>
      
      {/* Population */}
      <div className="mb-6">
        <h2 className="text-xl mb-3">Colony</h2>
        <div className="flex items-center justify-between bg-gray-800 p-3 rounded">
          <div>
            <span className="text-blue-400">Population Growth</span>
            <span className="ml-2 text-sm">(Current: {resources.population})</span>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={growPopulation}
            disabled={resources.energy < 100 || resources.materials < 50}
            className="px-3 py-1 bg-blue-800 hover:bg-blue-700 disabled:bg-gray-700 disabled:opacity-50 rounded"
          >
            Grow (+1 for 100 Energy, 50 Materials)
          </motion.button>
        </div>
      </div>
      
      {/* Production Rates */}
      <div className="text-xs text-gray-500 mb-6">
        <div>Energy: +{automation.solarCollectors.count * 2}/s</div>
        <div>Materials: +{automation.miners.count * 1}/s</div>
        <div>Research: +{automation.laboratories.count * 0.5}/s</div>
      </div>
      
      {/* Research Tree */}
      <div className="mb-6">
        <ResearchTree 
          currentResearch={resources.research} 
          onResearch={(research) => {
            console.log('Research completed:', research);
          }}
        />
      </div>
      
      {/* Advanced Game Systems */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuantumConsciousness 
          consciousness={consciousness}
          onQuantumShift={(state) => {
            console.log('Quantum shift:', state);
          }}
        />
        
        <MultidimensionalNavigator
          consciousness={consciousness}
          energy={resources.energy}
          onDimensionShift={(dimension) => {
            console.log('Dimension shifted:', dimension);
          }}
        />
      </div>
      
      {/* Agent Swarm System */}
      <div className="mt-6">
        <AgentSwarm
          consciousness={consciousness}
          onSwarmAction={(action, data) => {
            console.log('Swarm action:', action, data);
          }}
        />
      </div>
    </div>
  );
}

export default GameCore;
