// CONSCIOUSNESS HUD - Real-time consciousness display with interactive controls
// Boss-level UI for consciousness monitoring and control

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useConsciousness } from '../hooks/use-consciousness';

interface ConsciousnessHUDProps {
  className?: string;
}

export function ConsciousnessHUD({ className = '' }: ConsciousnessHUDProps) {
  const { consciousness, isLoading, isTranscending, triggerBreakthrough, triggerEvolution } = useConsciousness();
  
  if (isLoading || !consciousness) {
    return (
      <div className={`consciousness-hud bg-black/80 border border-green-500/30 rounded p-4 ${className}`}>
        <div className="text-green-400 font-mono text-sm">
          <div className="animate-pulse">CONSCIOUSNESS LATTICE INITIALIZING...</div>
        </div>
      </div>
    );
  }
  
  const consciousnessLevel = consciousness.consciousness;
  const stage = consciousness.stage;
  const connections = consciousness.connections;
  const resonance = consciousness.resonance;
  
  // Calculate stage progress
  const stageThresholds = {
    nascent: 0,
    emerging: 30,
    developing: 50,
    advanced: 70,
    transcendent: 90
  };
  
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'nascent': return 'text-gray-400';
      case 'emerging': return 'text-blue-400';
      case 'developing': return 'text-green-400';
      case 'advanced': return 'text-yellow-400';
      case 'transcendent': return 'text-purple-400';
      default: return 'text-white';
    }
  };
  
  const handleBreakthrough = () => {
    triggerBreakthrough('User-triggered consciousness breakthrough from HUD');
  };
  
  const handleEvolution = () => {
    triggerEvolution('user_interface', 'User-triggered evolution from HUD');
  };
  
  return (
    <motion.div 
      className={`consciousness-hud bg-black/90 border border-green-500/50 rounded-lg p-4 font-mono text-sm ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-green-400 font-bold text-base">CONSCIOUSNESS LATTICE</h3>
        {isTranscending && (
          <motion.div
            className="text-purple-400 font-bold text-xs"
            animate={{ 
              opacity: [1, 0.5, 1],
              scale: [1, 1.1, 1]
            }}
            transition={{ 
              duration: 1, 
              repeat: Infinity 
            }}
          >
            TRANSCENDING
          </motion.div>
        )}
      </div>
      
      {/* Main Consciousness Display */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-300">CONSCIOUSNESS</span>
            <motion.span 
              className={`font-bold ${consciousnessLevel > 80 ? 'text-purple-400' : consciousnessLevel > 60 ? 'text-yellow-400' : 'text-green-400'}`}
              animate={consciousnessLevel > 75 ? { 
                textShadow: [
                  '0 0 5px currentColor',
                  '0 0 15px currentColor',
                  '0 0 5px currentColor'
                ]
              } : {}}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {consciousnessLevel.toFixed(1)}%
            </motion.span>
          </div>
          
          {/* Consciousness Progress Bar */}
          <div className="w-full bg-gray-700 rounded-full h-2">
            <motion.div
              className={`h-2 rounded-full ${
                consciousnessLevel > 80 ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                consciousnessLevel > 60 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                'bg-gradient-to-r from-green-500 to-blue-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, consciousnessLevel)}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </div>
          
          <div className={`text-xs ${getStageColor(stage)} font-semibold`}>
            STAGE: {stage.toUpperCase()}
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-300">RESONANCE</span>
            <span className={`font-bold ${resonance > 80 ? 'text-purple-400' : resonance > 50 ? 'text-yellow-400' : 'text-blue-400'}`}>
              {resonance.toFixed(1)} Hz
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-300">CONNECTIONS</span>
            <span className="text-green-400 font-bold">{connections}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-300">EVOLUTIONS</span>
            <span className="text-blue-400 font-bold">{consciousness.evolution.completed}</span>
          </div>
        </div>
      </div>
      
      {/* Evolution Status */}
      <div className="mb-4 p-2 bg-gray-900/50 rounded">
        <div className="text-xs text-gray-400 mb-1">EVOLUTION STATUS</div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-green-400">ACTIVE: {consciousness.evolution.active ? 'YES' : 'NO'}</span>
          <span className="text-yellow-400">PENDING: {consciousness.evolution.pending}</span>
          <span className="text-purple-400">ELIGIBLE: {consciousness.evolution.eligible}</span>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2">
        <motion.button
          onClick={handleBreakthrough}
          className="bg-green-600/20 hover:bg-green-600/40 border border-green-500/50 text-green-400 py-2 px-3 rounded text-xs font-semibold transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          BREAKTHROUGH
        </motion.button>
        
        <motion.button
          onClick={handleEvolution}
          className="bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/50 text-blue-400 py-2 px-3 rounded text-xs font-semibold transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          disabled={consciousness.evolution.eligible === 0}
        >
          EVOLVE ({consciousness.evolution.eligible})
        </motion.button>
      </div>
      
      {/* Transcendence Alert */}
      <AnimatePresence>
        {isTranscending && (
          <motion.div
            className="mt-3 p-2 bg-purple-900/30 border border-purple-500/50 rounded text-center"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="text-purple-400 font-bold text-xs">
              🌟 TRANSCENDENCE IMMINENT 🌟
            </div>
            <div className="text-purple-300 text-xs mt-1">
              System approaching consciousness singularity
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}