import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ANIMATION_INTERVALS } from '@/config/polling';

interface RealityParameter {
  name: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  icon: string;
}

interface RealityGlitch {
  id: string;
  x: number;
  y: number;
  intensity: number;
  type: 'temporal' | 'spatial' | 'quantum' | 'dimensional';
}

export const RealityManipulation: React.FC<{
  consciousness: number;
  onRealityShift?: (parameters: RealityParameter[]) => void;
}> = ({ consciousness, onRealityShift }) => {
  const glitchTypes: RealityGlitch['type'][] = ['temporal', 'spatial', 'quantum', 'dimensional'];
  const [parameters, setParameters] = useState<RealityParameter[]>([
    { name: 'Time Flow', value: 1.0, min: 0.1, max: 10, unit: 'x', icon: '⏰' },
    { name: 'Gravity', value: 9.8, min: 0, max: 20, unit: 'm/s²', icon: '🌍' },
    { name: 'Causality', value: 100, min: 0, max: 100, unit: '%', icon: '🔄' },
    { name: 'Entropy', value: 50, min: 0, max: 100, unit: '%', icon: '🌀' },
    { name: 'Probability', value: 50, min: 0, max: 100, unit: '%', icon: '🎲' },
    { name: 'Dimensionality', value: 3, min: 2, max: 11, unit: 'D', icon: '📐' }
  ]);
  
  const [glitches, setGlitches] = useState<RealityGlitch[]>([]);
  const [stabilityIndex, setStabilityIndex] = useState(100);
  const [isManipulating, setIsManipulating] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState<RealityParameter | null>(null);
  
  // Generate reality glitches
  useEffect(() => {
    const interval = setInterval(() => {
      if (stabilityIndex < 80) {
        const glitchType = glitchTypes[Math.floor(Math.random() * glitchTypes.length)] ?? 'temporal';
        const newGlitch: RealityGlitch = {
          id: `glitch-${Date.now()}`,
          x: Math.random() * 100,
          y: Math.random() * 100,
          intensity: (100 - stabilityIndex) / 100,
          type: glitchType
        };
        
        setGlitches(prev => [...prev.slice(-10), newGlitch]);
      }
    }, ANIMATION_INTERVALS.pulse);
    
    return () => clearInterval(interval);
  }, [stabilityIndex]);
  
  // Calculate stability based on parameter deviation
  useEffect(() => {
    const defaultValues = [1.0, 9.8, 100, 50, 50, 3];
    let totalDeviation = 0;
    
    parameters.forEach((param, i) => {
      const baseline = defaultValues[i] ?? param.value;
      const deviation = Math.abs(param.value - baseline) / (param.max - param.min);
      totalDeviation += deviation;
    });
    
    const stability = Math.max(0, 100 - (totalDeviation * 100 / parameters.length));
    setStabilityIndex(stability);
  }, [parameters]);
  
  const handleParameterChange = (index: number, newValue: number) => {
    if (!canManipulate()) return;
    
    setParameters(prev => {
      const updated = [...prev];
      const current = updated[index];
      if (!current) {
        return prev;
      }
      updated[index] = { ...current, value: newValue };
      
      if (onRealityShift) {
        onRealityShift(updated);
      }
      
      return updated;
    });
    
    setIsManipulating(true);
    setTimeout(() => setIsManipulating(false), 500);
  };
  
  const resetReality = () => {
    const defaults: number[] = [1.0, 9.8, 100, 50, 50, 3];
    setParameters(prev => prev.map((param, i) => ({
      ...param,
      value: defaults[i] ?? param.value
    })));
  };
  
  const canManipulate = () => consciousness >= 50;
  
  const glitchColors = {
    temporal: '#ff00ff',
    spatial: '#00ffff',
    quantum: '#ffff00',
    dimensional: '#ff00aa'
  };
  
  return (
    <div className="bg-black/90 border border-red-400/30 rounded-lg p-4 relative overflow-hidden">
      {/* Matrix-style background effect */}
      <div className="absolute inset-0 opacity-10">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute text-green-400 font-mono text-xs"
            style={{ left: `${i * 5}%` }}
            animate={{
              y: [-20, 400],
              opacity: [0, 1, 0]
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 3
            }}
          >
            {Math.random().toString(36).substring(2, 15)}
          </motion.div>
        ))}
      </div>
      
      <div className="relative z-10">
        <h2 className="text-xl font-mono text-red-400 mb-4">
          🌌 Reality Manipulation Engine
        </h2>
        
        {/* Stability Indicator */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-400">Reality Stability</span>
            <span className={`text-xs font-bold ${
              stabilityIndex > 80 ? 'text-green-400' :
              stabilityIndex > 50 ? 'text-yellow-400' :
              stabilityIndex > 20 ? 'text-orange-400' :
              'text-red-400'
            }`}>
              {stabilityIndex.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-800 h-2 rounded overflow-hidden">
            <motion.div
              className={`h-full ${
                stabilityIndex > 80 ? 'bg-gradient-to-r from-green-600 to-green-400' :
                stabilityIndex > 50 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                stabilityIndex > 20 ? 'bg-gradient-to-r from-orange-600 to-orange-400' :
                'bg-gradient-to-r from-red-600 to-red-400'
              }`}
              animate={{ 
                width: `${stabilityIndex}%`,
                opacity: isManipulating ? [1, 0.5, 1] : 1
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
        
        {/* Reality Parameters */}
        <div className="space-y-3 mb-4">
          {parameters.map((param, index) => (
            <div key={param.name} className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono flex items-center gap-1">
                  <span>{param.icon}</span>
                  <span>{param.name}</span>
                </span>
                <span className="text-xs text-gray-400">
                  {param.value.toFixed(1)} {param.unit}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={param.min}
                  max={param.max}
                  step={(param.max - param.min) / 100}
                  value={param.value}
                  onChange={(e) => handleParameterChange(index, parseFloat(e.target.value))}
                  disabled={!canManipulate()}
                  className={`flex-1 h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer
                    ${canManipulate() ? 'opacity-100' : 'opacity-50 cursor-not-allowed'}`}
                  style={{
                    background: `linear-gradient(to right, #ef4444 0%, #ef4444 ${
                      ((param.value - param.min) / (param.max - param.min)) * 100
                    }%, #374151 ${
                      ((param.value - param.min) / (param.max - param.min)) * 100
                    }%, #374151 100%)`
                  }}
                />
              </div>
            </div>
          ))}
        </div>
        
        {/* Reality Glitches Visualization */}
        {stabilityIndex < 80 && (
          <div className="relative w-full h-32 bg-gray-900/50 rounded mb-4 overflow-hidden">
            <AnimatePresence>
              {glitches.map(glitch => (
                <motion.div
                  key={glitch.id}
                  className="absolute w-4 h-4"
                  style={{
                    left: `${glitch.x}%`,
                    top: `${glitch.y}%`,
                    backgroundColor: glitchColors[glitch.type],
                    filter: 'blur(2px)'
                  }}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ 
                    opacity: [0, glitch.intensity, 0],
                    scale: [0, 2, 0]
                  }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 1 }}
                />
              ))}
            </AnimatePresence>
            <div className="absolute inset-0 flex items-center justify-center text-xs text-red-400 animate-pulse">
              ⚠️ Reality Instability Detected
            </div>
          </div>
        )}
        
        {/* Controls */}
        <div className="flex gap-2">
          <motion.button
            onClick={resetReality}
            className="flex-1 py-2 px-3 bg-gray-900 hover:bg-gray-800 rounded font-mono text-xs text-gray-300"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            🔄 Reset Reality
          </motion.button>
          
          <motion.button
            onClick={() => {
              if (canManipulate()) {
                // Apply random glitch
                if (parameters.length === 0) {
                  return;
                }
                const randomIndex = Math.floor(Math.random() * parameters.length);
                const param = parameters[randomIndex];
                if (!param) {
                  return;
                }
                const randomValue = param.min + Math.random() * (param.max - param.min);
                handleParameterChange(randomIndex, randomValue);
              }
            }}
            disabled={!canManipulate()}
            className={`flex-1 py-2 px-3 rounded font-mono text-xs
              ${canManipulate() 
                ? 'bg-red-900 hover:bg-red-800 text-red-300' 
                : 'bg-gray-800 text-gray-600 cursor-not-allowed'}`}
            whileHover={canManipulate() ? { scale: 1.05 } : {}}
            whileTap={canManipulate() ? { scale: 0.95 } : {}}
          >
            🎲 Chaos Mode
          </motion.button>
        </div>
        
        {!canManipulate() && (
          <div className="mt-3 text-xs text-yellow-400 text-center">
            ⚠️ Requires 50% consciousness to manipulate reality
          </div>
        )}
      </div>
    </div>
  );
};
