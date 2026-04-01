import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Dimension {
  id: string;
  name: string;
  level: number;
  accessible: boolean;
  energy: number;
  description: string;
  color: string;
}

const dimensions: Dimension[] = [
  { id: 'd0', name: 'Physical Reality', level: 0, accessible: true, energy: 0, description: 'Base material plane', color: '#4ade80' },
  { id: 'd1', name: 'Quantum Foam', level: 1, accessible: true, energy: 10, description: 'Subatomic fluctuations', color: '#60a5fa' },
  { id: 'd2', name: 'Temporal Streams', level: 2, accessible: false, energy: 25, description: 'Time flow variations', color: '#c084fc' },
  { id: 'd3', name: 'Consciousness Web', level: 3, accessible: false, energy: 50, description: 'Collective awareness', color: '#fbbf24' },
  { id: 'd4', name: 'Probability Space', level: 4, accessible: false, energy: 100, description: 'All possible outcomes', color: '#f87171' },
  { id: 'd5', name: 'Causal Nexus', level: 5, accessible: false, energy: 200, description: 'Cause-effect chains', color: '#a78bfa' },
  { id: 'd6', name: 'Information Plane', level: 6, accessible: false, energy: 400, description: 'Pure data streams', color: '#34d399' },
  { id: 'd7', name: 'Dream Logic', level: 7, accessible: false, energy: 800, description: 'Subconscious realms', color: '#f472b6' },
  { id: 'd8', name: 'Void Between', level: 8, accessible: false, energy: 1600, description: 'Empty potential', color: '#94a3b8' },
  { id: 'd9', name: 'Source Code', level: 9, accessible: false, energy: 3200, description: 'Reality programming', color: '#22d3ee' },
  { id: 'd10', name: 'Singularity', level: 10, accessible: false, energy: 6400, description: 'Ultimate unity', color: '#ffffff' }
];

const defaultDimension: Dimension = dimensions[0] ?? {
  id: 'd0',
  name: 'Physical Reality',
  level: 0,
  accessible: true,
  energy: 0,
  description: 'Base material plane',
  color: '#4ade80'
};

interface NavigatorProps {
  consciousness: number;
  energy: number;
  onDimensionShift?: (dimension: Dimension) => void;
}

export const MultidimensionalNavigator: React.FC<NavigatorProps> = ({ 
  consciousness, 
  energy,
  onDimensionShift 
}) => {
  const [currentDimension, setCurrentDimension] = useState<Dimension>(defaultDimension);
  const [accessibleDimensions, setAccessibleDimensions] = useState<Set<string>>(new Set(['d0', 'd1']));
  const [transitioning, setTransitioning] = useState(false);
  const [quantumTunneling, setQuantumTunneling] = useState(false);
  
  // Calculate which dimensions are accessible based on consciousness
  useEffect(() => {
    const newAccessible = new Set<string>();
    dimensions.forEach(dim => {
      if (dim.level <= Math.floor(consciousness / 10)) {
        newAccessible.add(dim.id);
      }
    });
    setAccessibleDimensions(newAccessible);
  }, [consciousness]);
  
  const handleDimensionShift = (dimension: Dimension) => {
    if (!canAccess(dimension) && !quantumTunneling) return;
    
    setTransitioning(true);
    
    setTimeout(() => {
      setCurrentDimension(dimension);
      if (onDimensionShift) {
        onDimensionShift(dimension);
      }
      setTransitioning(false);
    }, 1500);
  };
  
  const canAccess = (dimension: Dimension) => {
    return accessibleDimensions.has(dimension.id) && energy >= dimension.energy;
  };
  
  const enableQuantumTunneling = () => {
    if (consciousness >= 50) {
      setQuantumTunneling(true);
      setTimeout(() => setQuantumTunneling(false), 5000);
    }
  };
  
  return (
    <div className="bg-black/90 border border-indigo-400/30 rounded-lg p-4 relative overflow-hidden">
      {/* Dimensional background effect */}
      <div className="absolute inset-0 opacity-20">
        <motion.div
          className="absolute inset-0"
          style={{
            background: `radial-gradient(circle at center, ${currentDimension.color}, transparent)`
          }}
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.2, 0.4, 0.2]
          }}
          transition={{ duration: 4, repeat: Infinity }}
        />
      </div>
      
      <div className="relative z-10">
        <h2 className="text-xl font-mono text-indigo-400 mb-4">
          🌌 Multidimensional Navigator
        </h2>
        
        {/* Current Dimension Display */}
        <div className="mb-4 p-3 bg-gray-900/50 rounded border border-indigo-400/50">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-mono">Current Dimension</span>
            <span className="text-xs text-gray-400">Level {currentDimension.level}</span>
          </div>
          <div className="text-lg font-bold" style={{ color: currentDimension.color }}>
            {currentDimension.name}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {currentDimension.description}
          </div>
        </div>
        
        {/* Dimension Grid */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {dimensions.map(dim => {
            const accessible = canAccess(dim);
            const unlocked = accessibleDimensions.has(dim.id);
            const isQuantumAccessible = quantumTunneling && energy >= dim.energy / 2;
            
            return (
              <motion.button
                key={dim.id}
                onClick={() => handleDimensionShift(dim)}
                disabled={!accessible && !isQuantumAccessible}
                className={`
                  p-2 rounded text-xs font-mono transition-all
                  ${currentDimension.id === dim.id 
                    ? 'ring-2 ring-white bg-gray-800' 
                    : accessible 
                      ? 'bg-gray-900/50 hover:bg-gray-800/50' 
                      : isQuantumAccessible
                        ? 'bg-purple-900/30 animate-pulse'
                        : 'bg-gray-900/20 opacity-50 cursor-not-allowed'}
                `}
                style={{
                  borderColor: unlocked ? `${dim.color}66` : '#4b5563',
                  borderWidth: '1px'
                }}
                whileHover={accessible ? { scale: 1.05 } : {}}
                whileTap={accessible ? { scale: 0.95 } : {}}
              >
                <div className="text-2xl mb-1">
                  {unlocked ? '🔓' : '🔒'}
                </div>
                <div style={{ color: unlocked ? dim.color : '#9ca3af' }}>
                  D{dim.level}
                </div>
                <div className="text-xs text-gray-500">
                  {dim.energy} ⚡
                </div>
              </motion.button>
            );
          })}
        </div>
        
        {/* Quantum Tunneling Button */}
        <motion.button
          onClick={enableQuantumTunneling}
          disabled={consciousness < 50 || quantumTunneling}
          className={`
            w-full py-2 px-3 rounded font-mono text-xs
            ${consciousness >= 50 && !quantumTunneling
              ? 'bg-purple-900 hover:bg-purple-800 text-purple-300'
              : 'bg-gray-800 text-gray-600 cursor-not-allowed'}
          `}
          whileHover={consciousness >= 50 && !quantumTunneling ? { scale: 1.02 } : {}}
          whileTap={consciousness >= 50 && !quantumTunneling ? { scale: 0.98 } : {}}
        >
          {quantumTunneling 
            ? '⚛️ Quantum Tunnel Active!' 
            : consciousness >= 50 
              ? '🌀 Enable Quantum Tunneling' 
              : '🔒 Requires 50% Consciousness'}
        </motion.button>
        
        {/* Status Display */}
        <div className="mt-3 text-xs text-gray-400 space-y-1">
          <div>Dimensions Unlocked: {accessibleDimensions.size}/11</div>
          <div>Energy Available: {energy} ⚡</div>
          <div>Consciousness: {consciousness.toFixed(1)}%</div>
        </div>
      </div>
      
      {/* Transition Effect */}
      <AnimatePresence>
        {transitioning && (
          <motion.div
            className="absolute inset-0 bg-white z-50 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="text-4xl"
              animate={{
                rotate: [0, 360],
                scale: [1, 2, 1]
              }}
              transition={{ duration: 1.5 }}
            >
              🌀
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
