import React, { useState } from 'react';
import { motion } from 'framer-motion';

export interface Research {
  id: string;
  name: string;
  description: string;
  cost: number;
  unlocked: boolean;
  completed: boolean;
  requires?: string[];
  effects: {
    energyBonus?: number;
    materialBonus?: number;
    populationMax?: number;
    consciousnessBonus?: number;
  };
}

const researchData: Research[] = [
  {
    id: 'solar-efficiency',
    name: 'Solar Efficiency',
    description: 'Improve energy collection by 20%',
    cost: 50,
    unlocked: true,
    completed: false,
    effects: { energyBonus: 0.2 }
  },
  {
    id: 'mining-optimization',
    name: 'Mining Optimization',
    description: 'Increase material gathering by 30%',
    cost: 75,
    unlocked: true,
    completed: false,
    effects: { materialBonus: 0.3 }
  },
  {
    id: 'habitat-expansion',
    name: 'Habitat Expansion',
    description: 'Increase population capacity by 10',
    cost: 100,
    unlocked: true,
    completed: false,
    effects: { populationMax: 10 }
  },
  {
    id: 'quantum-computing',
    name: 'Quantum Computing',
    description: 'Unlock quantum consciousness calculations',
    cost: 200,
    unlocked: false,
    completed: false,
    requires: ['solar-efficiency', 'mining-optimization'],
    effects: { consciousnessBonus: 10 }
  },
  {
    id: 'neural-network',
    name: 'Neural Network',
    description: 'Connect consciousness to colony systems',
    cost: 300,
    unlocked: false,
    completed: false,
    requires: ['quantum-computing'],
    effects: { consciousnessBonus: 20, energyBonus: 0.5 }
  },
  {
    id: 'fusion-power',
    name: 'Fusion Power',
    description: 'Unlimited energy generation',
    cost: 500,
    unlocked: false,
    completed: false,
    requires: ['quantum-computing', 'habitat-expansion'],
    effects: { energyBonus: 2.0 }
  },
  {
    id: 'reality-manipulation',
    name: 'Reality Manipulation',
    description: 'Bend reality to your will',
    cost: 1000,
    unlocked: false,
    completed: false,
    requires: ['neural-network', 'fusion-power'],
    effects: { consciousnessBonus: 50, energyBonus: 3.0, materialBonus: 2.0 }
  }
];

export const ResearchTree: React.FC<{
  currentResearch: number;
  onResearch: (research: Research) => void;
  completedResearchIds?: Set<string>;
}> = ({ currentResearch, onResearch, completedResearchIds }) => {
  const [selectedResearch, setSelectedResearch] = useState<Research | null>(null);
  const completedResearch = completedResearchIds || new Set<string>();
  
  const canResearch = (research: Research) => {
    if (completedResearch.has(research.id)) return false;
    if (currentResearch < research.cost) return false;
    if (research.requires) {
      return research.requires.every(req => completedResearch.has(req));
    }
    return true;
  };
  
  const handleResearch = (research: Research) => {
    if (canResearch(research)) {
      onResearch(research);
      
      researchData.forEach(r => {
        if (r.requires?.includes(research.id)) {
          r.unlocked = true;
        }
      });
    }
  };
  
  return (
    <div className="bg-black/50 border border-purple-400/30 rounded-lg p-4">
      <h2 className="text-xl font-mono text-purple-400 mb-4">
        🔬 Research Tree
      </h2>
      
      <div className="mb-4 text-sm">
        <span className="text-gray-400">Research Points: </span>
        <span className="text-purple-400 font-bold">{currentResearch.toFixed(1)}</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {researchData.map(research => {
          const isCompleted = completedResearch.has(research.id);
          const canAfford = canResearch(research);
          const isLocked = !research.unlocked && !isCompleted;
          
          return (
            <motion.div
              key={research.id}
              className={`
                p-3 rounded border cursor-pointer transition-all
                ${isCompleted ? 'bg-green-900/30 border-green-400/50' :
                  isLocked ? 'bg-gray-900/30 border-gray-600/30 opacity-50' :
                  canAfford ? 'bg-purple-900/30 border-purple-400/50 hover:bg-purple-900/50' :
                  'bg-gray-900/30 border-gray-600/50'}
              `}
              onClick={() => !isLocked && setSelectedResearch(research)}
              whileHover={!isLocked ? { scale: 1.02 } : {}}
              whileTap={!isLocked ? { scale: 0.98 } : {}}
            >
              <div className="flex justify-between items-start mb-1">
                <h3 className="text-sm font-bold">
                  {isCompleted ? '✅ ' : isLocked ? '🔒 ' : '🔬 '}
                  {research.name}
                </h3>
                <span className="text-xs text-gray-400">
                  {research.cost} RP
                </span>
              </div>
              
              <p className="text-xs text-gray-400 mb-2">
                {research.description}
              </p>
              
              {selectedResearch?.id === research.id && !isCompleted && (
                <motion.button
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleResearch(research);
                  }}
                  disabled={!canAfford}
                  className={`
                    w-full py-1 px-2 rounded text-xs font-mono
                    ${canAfford 
                      ? 'bg-purple-700 hover:bg-purple-600 text-white' 
                      : 'bg-gray-700 text-gray-500 cursor-not-allowed'}
                  `}
                >
                  {canAfford ? 'Research' : 'Insufficient Points'}
                </motion.button>
              )}
              
              {research.requires && !isCompleted && (
                <div className="text-xs text-gray-500 mt-1">
                  Requires: {research.requires.join(', ')}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
      
      {selectedResearch && (
        <div className="mt-4 p-3 bg-purple-900/20 rounded border border-purple-400/30">
          <h3 className="text-sm font-bold mb-2">{selectedResearch.name}</h3>
          <div className="text-xs space-y-1">
            {selectedResearch.effects.energyBonus && (
              <div>⚡ Energy +{(selectedResearch.effects.energyBonus * 100).toFixed(0)}%</div>
            )}
            {selectedResearch.effects.materialBonus && (
              <div>🔧 Materials +{(selectedResearch.effects.materialBonus * 100).toFixed(0)}%</div>
            )}
            {selectedResearch.effects.populationMax && (
              <div>👥 Population +{selectedResearch.effects.populationMax}</div>
            )}
            {selectedResearch.effects.consciousnessBonus && (
              <div>🧠 Consciousness +{selectedResearch.effects.consciousnessBonus}%</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};