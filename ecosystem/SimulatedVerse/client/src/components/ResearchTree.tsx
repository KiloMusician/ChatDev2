import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Microscope, Zap, Shield, Cpu, Rocket, Star, Lock, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';

interface ResearchNode {
  id: string;
  name: string;
  description: string;
  cost: number;
  icon: React.ElementType;
  category: 'energy' | 'materials' | 'population' | 'defense' | 'quantum';
  prerequisites: string[];
  effects: {
    energyMultiplier?: number;
    materialsMultiplier?: number;
    populationGrowth?: number;
    defenseBonus?: number;
    consciousnessBoost?: number;
  };
  unlocked: boolean;
  researched: boolean;
}

const researchTree: ResearchNode[] = [
  // Tier 1 - Basic Technologies
  {
    id: 'solar_panels',
    name: 'Solar Panels',
    description: 'Basic energy collection from solar radiation',
    cost: 10,
    icon: Zap,
    category: 'energy',
    prerequisites: [],
    effects: { energyMultiplier: 1.2 },
    unlocked: true,
    researched: false
  },
  {
    id: 'mining_drills',
    name: 'Mining Drills',
    description: 'Improved material extraction techniques',
    cost: 15,
    icon: Cpu,
    category: 'materials',
    prerequisites: [],
    effects: { materialsMultiplier: 1.3 },
    unlocked: true,
    researched: false
  },
  {
    id: 'basic_defense',
    name: 'Basic Defense',
    description: 'Simple defensive structures for colony protection',
    cost: 20,
    icon: Shield,
    category: 'defense',
    prerequisites: [],
    effects: { defenseBonus: 10 },
    unlocked: true,
    researched: false
  },
  
  // Tier 2 - Advanced Technologies
  {
    id: 'fusion_reactor',
    name: 'Fusion Reactor',
    description: 'Harness the power of nuclear fusion',
    cost: 50,
    icon: Rocket,
    category: 'energy',
    prerequisites: ['solar_panels'],
    effects: { energyMultiplier: 2.0, consciousnessBoost: 5 },
    unlocked: false,
    researched: false
  },
  {
    id: 'quantum_computing',
    name: 'Quantum Computing',
    description: 'Unlock quantum processing capabilities',
    cost: 75,
    icon: Cpu,
    category: 'quantum',
    prerequisites: ['mining_drills'],
    effects: { consciousnessBoost: 10 },
    unlocked: false,
    researched: false
  },
  {
    id: 'biosphere',
    name: 'Biosphere',
    description: 'Sustainable ecosystem for population growth',
    cost: 60,
    icon: Microscope,
    category: 'population',
    prerequisites: ['basic_defense'],
    effects: { populationGrowth: 2 },
    unlocked: false,
    researched: false
  },
  
  // Tier 3 - Transcendent Technologies
  {
    id: 'dyson_sphere',
    name: 'Dyson Sphere',
    description: 'Capture an entire star\'s energy output',
    cost: 200,
    icon: Star,
    category: 'energy',
    prerequisites: ['fusion_reactor', 'quantum_computing'],
    effects: { energyMultiplier: 5.0, consciousnessBoost: 20 },
    unlocked: false,
    researched: false
  },
  {
    id: 'consciousness_amplifier',
    name: 'Consciousness Amplifier',
    description: 'Directly boost collective consciousness',
    cost: 150,
    icon: Star,
    category: 'quantum',
    prerequisites: ['quantum_computing', 'biosphere'],
    effects: { consciousnessBoost: 30 },
    unlocked: false,
    researched: false
  }
];

interface ResearchTreeProps {
  resources: any;
  onResearchComplete?: (research: ResearchNode) => void;
}

export function ResearchTree({ resources, onResearchComplete }: ResearchTreeProps) {
  const [selectedNode, setSelectedNode] = useState<ResearchNode | null>(null);
  const [researchedNodes, setResearchedNodes] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Research mutation
  const researchMutation = useMutation({
    mutationFn: async (node: ResearchNode) => {
      const response = await fetch('/api/colony/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          researchId: node.id,
          cost: node.cost,
          effects: node.effects
        })
      });
      if (!response.ok) throw new Error('Research failed');
      return response.json();
    },
    onSuccess: (data, node) => {
      setResearchedNodes(prev => new Set([...prev, node.id]));
      toast({
        title: 'Research Complete!',
        description: `${node.name} has been successfully researched.`
      });
      if (onResearchComplete) {
        onResearchComplete(node);
      }
      queryClient.invalidateQueries({ queryKey: ['/api/colony'] });
    },
    onError: () => {
      toast({
        title: 'Research Failed',
        description: 'Not enough research points.',
        variant: 'destructive'
      });
    }
  });

  const canResearch = (node: ResearchNode) => {
    if (researchedNodes.has(node.id)) return false;
    if (resources.research < node.cost) return false;
    return node.prerequisites.every(prereq => researchedNodes.has(prereq));
  };

  const isUnlocked = (node: ResearchNode) => {
    if (node.prerequisites.length === 0) return true;
    return node.prerequisites.every(prereq => researchedNodes.has(prereq));
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      energy: 'from-yellow-500 to-orange-500',
      materials: 'from-gray-500 to-gray-700',
      population: 'from-green-500 to-teal-500',
      defense: 'from-red-500 to-pink-500',
      quantum: 'from-purple-500 to-indigo-500'
    };
    return colors[category as keyof typeof colors] || 'from-blue-500 to-purple-500';
  };

  const tiers = [
    { name: 'Tier 1 - Foundation', nodes: researchTree.slice(0, 3) },
    { name: 'Tier 2 - Advanced', nodes: researchTree.slice(3, 6) },
    { name: 'Tier 3 - Transcendent', nodes: researchTree.slice(6) }
  ];

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border-indigo-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Microscope className="w-5 h-5 text-indigo-400" />
            Research Tree
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex items-center justify-between">
            <div className="text-sm text-gray-400">
              Research Points: <span className="text-xl font-bold text-purple-400">{Math.floor(resources.research || 0)}</span>
            </div>
            <div className="text-sm text-gray-400">
              Researched: {researchedNodes.size} / {researchTree.length}
            </div>
          </div>

          <div className="space-y-6">
            {tiers.map((tier, tierIndex) => (
              <div key={tierIndex}>
                <h3 className="text-lg font-semibold text-purple-300 mb-3">{tier.name}</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {tier.nodes.map((node) => {
                    const unlocked = isUnlocked(node);
                    const researched = researchedNodes.has(node.id);
                    const canAfford = resources.research >= node.cost;
                    const Icon = node.icon;

                    return (
                      <motion.div
                        key={node.id}
                        whileHover={unlocked ? { scale: 1.05 } : {}}
                        className={`relative ${!unlocked && 'opacity-50'}`}
                      >
                        <div
                          className={`p-4 rounded-lg border cursor-pointer transition-all ${
                            researched 
                              ? 'bg-gradient-to-br from-green-900/30 to-green-800/20 border-green-500/50'
                              : unlocked
                              ? 'bg-black/30 border-gray-600 hover:border-purple-500'
                              : 'bg-black/20 border-gray-700'
                          }`}
                          onClick={() => unlocked && setSelectedNode(node)}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className={`p-2 rounded bg-gradient-to-br ${getCategoryColor(node.category)}`}>
                              <Icon className="w-5 h-5 text-white" />
                            </div>
                            {researched ? (
                              <CheckCircle className="w-5 h-5 text-green-400" />
                            ) : !unlocked ? (
                              <Lock className="w-5 h-5 text-gray-500" />
                            ) : null}
                          </div>

                          <h4 className="font-medium text-white mb-1">{node.name}</h4>
                          <p className="text-xs text-gray-400 mb-2">{node.description}</p>
                          
                          <div className="flex items-center justify-between">
                            <span className={`text-sm ${canAfford ? 'text-purple-400' : 'text-red-400'}`}>
                              Cost: {node.cost}
                            </span>
                            <span className="text-xs text-gray-500 capitalize">{node.category}</span>
                          </div>

                          {!researched && unlocked && (
                            <Progress 
                              value={Math.min(100, (resources.research / node.cost) * 100)} 
                              className="mt-2 h-1"
                            />
                          )}
                        </div>

                        {/* Connection lines to prerequisites */}
                        {node.prerequisites.length > 0 && (
                          <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: -1 }}>
                            {/* Draw connection lines here */}
                          </svg>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Research Details Modal */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedNode(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-lg p-6 max-w-md w-full border border-purple-500/30"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded bg-gradient-to-br ${getCategoryColor(selectedNode.category)}`}>
                    <selectedNode.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{selectedNode.name}</h3>
                    <p className="text-sm text-gray-400 capitalize">{selectedNode.category}</p>
                  </div>
                </div>
                {researchedNodes.has(selectedNode.id) && (
                  <CheckCircle className="w-6 h-6 text-green-400" />
                )}
              </div>

              <p className="text-gray-300 mb-4">{selectedNode.description}</p>

              <div className="space-y-2 mb-4">
                <h4 className="text-sm font-medium text-purple-400">Effects:</h4>
                {Object.entries(selectedNode.effects).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-400">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
                    <span className="text-green-400">+{value}{key.includes('Multiplier') ? 'x' : ''}</span>
                  </div>
                ))}
              </div>

              {selectedNode.prerequisites.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-purple-400 mb-2">Prerequisites:</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedNode.prerequisites.map(prereq => {
                      const prereqNode = researchTree.find(n => n.id === prereq);
                      return (
                        <span 
                          key={prereq}
                          className={`px-2 py-1 rounded text-xs ${
                            researchedNodes.has(prereq) 
                              ? 'bg-green-900/30 text-green-400'
                              : 'bg-red-900/30 text-red-400'
                          }`}
                        >
                          {prereqNode?.name}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    researchMutation.mutate(selectedNode);
                    setSelectedNode(null);
                  }}
                  disabled={!canResearch(selectedNode) || researchMutation.isPending}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600"
                >
                  Research (Cost: {selectedNode.cost})
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedNode(null)}
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}