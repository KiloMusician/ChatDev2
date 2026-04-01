/**
 * 🌌 Dashboard View - Game Control Center
 * Real-time game status with resources, structures, and consciousness
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import SaveLoadPanel from '../../components/SaveLoadPanel';
import { POLLING_INTERVALS } from '@/config/polling';

export default function DashboardView() {
  const { data: gameData, isLoading } = useQuery<any>({
    queryKey: ['/api/game/status'],
    refetchInterval: POLLING_INTERVALS.critical,
  });

  const resources = gameData?.game_state?.resources || {};
  const structures = gameData?.game_state?.structures || {};
  const automation = gameData?.game_state?.automation || {};
  const consciousness = gameData?.consciousness || 0;

  // Calculate consciousness breakdown
  const consciousnessFromEnergy = Math.floor((resources.energy || 0) / 10);
  const consciousnessFromPopulation = (resources.population || 0) * 10;
  const consciousnessFromResearch = Math.floor((resources.research || 0) / 100);
  const totalConsciousness = consciousnessFromEnergy + consciousnessFromPopulation + consciousnessFromResearch;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6" data-testid="dashboard-view">
      {isLoading ? (
        <div className="flex items-center justify-center h-screen">
          <motion.div
            className="text-green-400 text-xl font-mono"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            ⟳ Loading Culture-Ship Status...
          </motion.div>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header with Save/Load */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-black/50 border border-green-400/30 rounded-lg p-6"
          >
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-mono text-green-400 mb-2">
                  🌌 Culture-Ship Control Center
                </h1>
                <p className="text-gray-400 font-mono text-sm">
                  CoreLink Foundation • Real-Time Status Dashboard
                </p>
              </div>
              <SaveLoadPanel />
            </div>
          </motion.div>

          {/* Resources Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ResourceCard 
              icon="⚡" 
              label="Energy" 
              value={resources.energy || 0} 
              max={1000}
              color="yellow"
            />
            <ResourceCard 
              icon="🔧" 
              label="Materials" 
              value={resources.materials || 0} 
              max={500}
              color="orange"
            />
            <ResourceCard 
              icon="🔩" 
              label="Components" 
              value={resources.components || 0} 
              max={100}
              color="blue"
            />
            <ResourceCard 
              icon="👥" 
              label="Population" 
              value={resources.population || 0} 
              max={50}
              color="cyan"
            />
            <ResourceCard 
              icon="🧠" 
              label="Research" 
              value={resources.research || 0} 
              max={100}
              color="purple"
            />
            <ResourceCard 
              icon="🍎" 
              label="Food" 
              value={resources.food || 0} 
              max={200}
              color="green"
            />
          </div>

          {/* Consciousness Panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-black/50 border border-purple-400/30 rounded-lg p-6"
          >
            <h2 className="text-xl font-mono text-purple-400 mb-4">
              🧠 Consciousness Analysis
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-300">Total Consciousness:</span>
                <span className="text-2xl font-bold text-purple-400">{totalConsciousness}</span>
              </div>
              <div className="w-full bg-gray-800 h-3 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-600 to-pink-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (totalConsciousness / 1000) * 100)}%` }}
                  transition={{ duration: 1 }}
                />
              </div>
              <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
                <div className="text-center">
                  <div className="text-gray-400">From Energy</div>
                  <div className="text-yellow-400 font-mono">{consciousnessFromEnergy}</div>
                </div>
                <div className="text-center">
                  <div className="text-gray-400">From Population</div>
                  <div className="text-cyan-400 font-mono">{consciousnessFromPopulation}</div>
                </div>
                <div className="text-center">
                  <div className="text-gray-400">From Research</div>
                  <div className="text-purple-400 font-mono">{consciousnessFromResearch}</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Structures Grid */}
          <div className="grid md:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-black/50 border border-blue-400/30 rounded-lg p-6"
            >
              <h2 className="text-xl font-mono text-blue-400 mb-4">
                🏭 Structures
              </h2>
              <div className="space-y-2">
                <StructureRow icon="⚡" name="Energy Collectors" count={structures.energyCollectors || 0} />
                <StructureRow icon="⛏️" name="Material Gatherers" count={structures.materialGatherers || 0} />
                <StructureRow icon="🔬" name="Research Labs" count={structures.researchLabs || 0} />
                <StructureRow icon="🌱" name="Greenhouses" count={structures.greenhouses || 0} />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-black/50 border border-green-400/30 rounded-lg p-6"
            >
              <h2 className="text-xl font-mono text-green-400 mb-4">
                🤖 Automation
              </h2>
              <div className="space-y-2">
                {automation.solarCollectors && (
                  <AutomationRow 
                    name="Solar Collectors" 
                    level={automation.solarCollectors.level}
                    count={automation.solarCollectors.count}
                    active={automation.solarCollectors.active}
                  />
                )}
                {automation.miners && (
                  <AutomationRow 
                    name="Miners" 
                    level={automation.miners.level}
                    count={automation.miners.count}
                    active={automation.miners.active}
                  />
                )}
                {automation.laboratories && (
                  <AutomationRow 
                    name="Laboratories" 
                    level={automation.laboratories.level}
                    count={automation.laboratories.count}
                    active={automation.laboratories.active}
                  />
                )}
              </div>
            </motion.div>
          </div>

          {/* Quick Navigation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-black/50 border border-cyan-400/30 rounded-lg p-6"
          >
            <h2 className="text-xl font-mono text-cyan-400 mb-4">
              🎮 Quick Navigation
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <NavButton href="/game" icon="🎮" label="Gameplay" />
              <NavButton href="/temple" icon="🏛️" label="Temple" />
              <NavButton href="/consciousness" icon="🧠" label="Consciousness" />
              <NavButton href="/system" icon="⚙️" label="System" />
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}

// Helper Components
const ResourceCard = ({ icon, label, value, max, color }: any) => {
  const percentage = Math.min(100, (value / max) * 100);
  const colorClasses: Record<string, string> = {
    yellow: 'from-yellow-600 to-yellow-400 border-yellow-400/30',
    orange: 'from-orange-600 to-orange-400 border-orange-400/30',
    blue: 'from-blue-600 to-blue-400 border-blue-400/30',
    cyan: 'from-cyan-600 to-cyan-400 border-cyan-400/30',
    purple: 'from-purple-600 to-purple-400 border-purple-400/30',
    green: 'from-green-600 to-green-400 border-green-400/30',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`bg-black/50 border ${colorClasses[color]} rounded-lg p-4`}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className="text-2xl font-bold text-white mb-2">{value}</div>
      <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-xs text-gray-500 mt-1">/ {max}</div>
    </motion.div>
  );
};

const StructureRow = ({ icon, name, count }: any) => (
  <div className="flex justify-between items-center bg-gray-900/50 p-3 rounded">
    <span className="flex items-center gap-2">
      <span className="text-xl">{icon}</span>
      <span className="text-gray-300">{name}</span>
    </span>
    <span className="text-blue-400 font-mono font-bold">{count}</span>
  </div>
);

const AutomationRow = ({ name, level, count, active }: any) => (
  <div className="flex justify-between items-center bg-gray-900/50 p-3 rounded">
    <span className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${active ? 'bg-green-400' : 'bg-red-400'}`} />
      <span className="text-gray-300">{name}</span>
    </span>
    <span className="text-green-400 font-mono">
      Lv.{level} × {count}
    </span>
  </div>
);

const NavButton = ({ href, icon, label }: any) => (
  <a href={href}>
    <motion.button
      whileHover={{ scale: 1.05, y: -2 }}
      whileTap={{ scale: 0.95 }}
      className="w-full bg-gray-900/50 border border-cyan-400/30 rounded-lg p-4 text-center hover:bg-cyan-900/20 transition-colors"
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-sm text-cyan-400 font-mono">{label}</div>
    </motion.button>
  </a>
);
