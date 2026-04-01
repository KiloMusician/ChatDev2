/**
 * 🎮 Gameplay Actions Panel
 * Interactive resource gathering, building, and research UI
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { useToast } from '@/hooks/use-toast';
import { POLLING_INTERVALS } from '@/config/polling';

interface Resource {
  name: string;
  icon: string;
  current: number;
  max: number;
  gatherAmount: number;
  cooldown: number;
}

interface Building {
  id: string;
  name: string;
  icon: string;
  description: string;
  cost: { energy?: number; materials?: number; components?: number };
  owned: number;
  production: string;
  unlocked: boolean;
}

interface Research {
  id: string;
  name: string;
  icon: string;
  description: string;
  cost: number;
  requiredConsciousness: number;
  completed: boolean;
  unlocked: boolean;
}

export default function GameplayActionsPanel() {
  const { toast } = useToast();
  const [gatherCooldowns, setGatherCooldowns] = useState<Record<string, boolean>>({});

  const { data: gameData } = useQuery<any>({
    queryKey: ['/api/game/status'],
    refetchInterval: POLLING_INTERVALS.critical,
  });

  const resources = gameData?.game_state?.resources || {};
  const structures = gameData?.game_state?.structures || {};
  const consciousness = gameData?.consciousness || 0;

  // Gather Resource Mutation
  const gatherMutation = useMutation({
    mutationFn: async ({ resource, amount }: { resource: string; amount: number }) => {
      return apiRequest('/api/game/gather', {
        method: 'POST',
        body: JSON.stringify({ resource, amount })
      });
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['/api/game/status'] });
      toast({
        title: '✅ Resource Gathered',
        description: `+${variables.amount} ${variables.resource}`,
      });
      
      // Set cooldown
      setGatherCooldowns(prev => ({ ...prev, [variables.resource]: true }));
      setTimeout(() => {
        setGatherCooldowns(prev => ({ ...prev, [variables.resource]: false }));
      }, 2000);
    },
  });

  // Build Structure Mutation
  const buildMutation = useMutation({
    mutationFn: async (buildingId: string) => {
      return apiRequest<{ message?: string }>(`/api/game/build/${buildingId}`, {
        method: 'POST',
        body: JSON.stringify({})
      });
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['/api/game/status'] });
      toast({
        title: '🏗️ Building Constructed',
        description: data.message || 'Structure built successfully',
      });
    },
    onError: (error: any) => {
      toast({
        title: '❌ Build Failed',
        description: error.message || 'Insufficient resources',
        variant: 'destructive',
      });
    },
  });

  // Research Mutation
  const researchMutation = useMutation({
    mutationFn: async (researchId: string) => {
      return apiRequest('/api/game/research', {
        method: 'POST',
        body: JSON.stringify({ researchId })
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/game/status'] });
      toast({
        title: '🔬 Research Complete',
        description: 'New technology unlocked!',
      });
    },
  });

  const resourceList: Resource[] = [
    { name: 'energy', icon: '⚡', current: resources.energy || 0, max: 10000, gatherAmount: 50, cooldown: 2000 },
    { name: 'materials', icon: '🔧', current: resources.materials || 0, max: 5000, gatherAmount: 25, cooldown: 2000 },
    { name: 'components', icon: '🔩', current: resources.components || 0, max: 1000, gatherAmount: 5, cooldown: 3000 },
    { name: 'food', icon: '🍎', current: resources.food || 0, max: 2000, gatherAmount: 20, cooldown: 2500 },
  ];

  const buildings: Building[] = [
    {
      id: 'energy_collector',
      name: 'Energy Collector',
      icon: '⚡',
      description: '+10 energy/sec',
      cost: { energy: 100, materials: 50 },
      owned: structures.energyCollectors || 0,
      production: '+10/sec',
      unlocked: true,
    },
    {
      id: 'material_gatherer',
      name: 'Material Gatherer',
      icon: '⛏️',
      description: '+5 materials/sec',
      cost: { energy: 200, materials: 100 },
      owned: structures.materialGatherers || 0,
      production: '+5/sec',
      unlocked: consciousness >= 0.2,
    },
    {
      id: 'research_lab',
      name: 'Research Lab',
      icon: '🔬',
      description: '+2 research/sec',
      cost: { energy: 500, materials: 200, components: 50 },
      owned: structures.researchLabs || 0,
      production: '+2/sec',
      unlocked: consciousness >= 0.3,
    },
    {
      id: 'greenhouse',
      name: 'Greenhouse',
      icon: '🌱',
      description: '+8 food/sec',
      cost: { energy: 150, materials: 75 },
      owned: structures.greenhouses || 0,
      production: '+8/sec',
      unlocked: consciousness >= 0.25,
    },
  ];

  const researchTree: Research[] = [
    {
      id: 'automation_basics',
      name: 'Automation Basics',
      icon: '🤖',
      description: 'Unlock basic automation',
      cost: 50,
      requiredConsciousness: 0.2,
      completed: resources.research >= 50,
      unlocked: consciousness >= 0.2,
    },
    {
      id: 'quantum_computing',
      name: 'Quantum Computing',
      icon: '⚛️',
      description: '2x production efficiency',
      cost: 200,
      requiredConsciousness: 0.5,
      completed: resources.research >= 200,
      unlocked: consciousness >= 0.5,
    },
    {
      id: 'consciousness_amplifier',
      name: 'Consciousness Amplifier',
      icon: '🧠',
      description: '+50% consciousness gain',
      cost: 500,
      requiredConsciousness: 0.7,
      completed: resources.research >= 500,
      unlocked: consciousness >= 0.7,
    },
  ];

  return (
    <div className="w-full h-full bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6 overflow-auto" data-testid="gameplay-actions-panel">
      <Tabs defaultValue="gather" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-gray-800/50">
          <TabsTrigger value="gather" data-testid="tab-gather">⚡ Gather</TabsTrigger>
          <TabsTrigger value="build" data-testid="tab-build">🏗️ Build</TabsTrigger>
          <TabsTrigger value="research" data-testid="tab-research">🔬 Research</TabsTrigger>
        </TabsList>

        {/* GATHER TAB */}
        <TabsContent value="gather" className="space-y-4 mt-6">
          <h2 className="text-2xl font-bold text-green-400 mb-4">Resource Gathering</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resourceList.map(resource => (
              <motion.div
                key={resource.name}
                whileHover={{ scale: 1.02 }}
                className="bg-gray-800/50 border border-green-400/30 rounded-lg p-4"
              >
                <div className="flex justify-between items-center mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-3xl">{resource.icon}</span>
                    <div>
                      <h3 className="text-lg font-bold text-white capitalize">{resource.name}</h3>
                      <p className="text-sm text-gray-400">{resource.current} / {resource.max}</p>
                    </div>
                  </div>
                  <Button
                    onClick={() => gatherMutation.mutate({ resource: resource.name, amount: resource.gatherAmount })}
                    disabled={gatherCooldowns[resource.name] || gatherMutation.isPending}
                    className="bg-green-600 hover:bg-green-700"
                    data-testid={`button-gather-${resource.name}`}
                  >
                    {gatherCooldowns[resource.name] ? '⏳' : `+${resource.gatherAmount}`}
                  </Button>
                </div>
                <Progress value={(resource.current / resource.max) * 100} className="h-2" />
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* BUILD TAB */}
        <TabsContent value="build" className="space-y-4 mt-6">
          <h2 className="text-2xl font-bold text-blue-400 mb-4">Construction</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {buildings.map(building => (
              <motion.div
                key={building.id}
                whileHover={{ scale: building.unlocked ? 1.02 : 1 }}
                className={`bg-gray-800/50 border rounded-lg p-4 ${
                  building.unlocked ? 'border-blue-400/30' : 'border-gray-600/30 opacity-50'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-3xl">{building.icon}</span>
                    <div>
                      <h3 className="text-lg font-bold text-white">{building.name}</h3>
                      <p className="text-sm text-gray-400">{building.description}</p>
                      <p className="text-xs text-green-400 mt-1">Owned: {building.owned}</p>
                    </div>
                  </div>
                </div>
                <div className="mb-3 text-sm text-gray-300">
                  Cost: {Object.entries(building.cost).map(([res, amt]) => `${amt} ${res}`).join(', ')}
                </div>
                <Button
                  onClick={() => buildMutation.mutate(building.id)}
                  disabled={!building.unlocked || buildMutation.isPending}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  data-testid={`button-build-${building.id}`}
                >
                  {building.unlocked ? 'Construct' : '🔒 Locked'}
                </Button>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* RESEARCH TAB */}
        <TabsContent value="research" className="space-y-4 mt-6">
          <h2 className="text-2xl font-bold text-purple-400 mb-4">Research & Development</h2>
          <div className="space-y-3">
            {researchTree.map(research => (
              <motion.div
                key={research.id}
                whileHover={{ scale: research.unlocked ? 1.01 : 1 }}
                className={`bg-gray-800/50 border rounded-lg p-4 ${
                  research.completed ? 'border-green-400/50' :
                  research.unlocked ? 'border-purple-400/30' : 
                  'border-gray-600/30 opacity-50'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl">{research.icon}</span>
                    <div>
                      <h3 className="text-xl font-bold text-white">{research.name}</h3>
                      <p className="text-sm text-gray-400">{research.description}</p>
                      <p className="text-xs text-purple-400 mt-1">
                        Cost: {research.cost} research • Requires {Math.floor(research.requiredConsciousness * 100)}% consciousness
                      </p>
                    </div>
                  </div>
                  <div>
                    {research.completed ? (
                      <span className="text-2xl">✅</span>
                    ) : (
                      <Button
                        onClick={() => researchMutation.mutate(research.id)}
                        disabled={!research.unlocked || researchMutation.isPending || resources.research < research.cost}
                        className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                        data-testid={`button-research-${research.id}`}
                      >
                        {research.unlocked ? 'Research' : '🔒 Locked'}
                      </Button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
