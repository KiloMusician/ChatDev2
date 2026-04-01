import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ANIMATION_INTERVALS } from '@/config/polling';

// Breathing patterns for navigation flow
export type BreathingPhase = 'inhale' | 'hold' | 'exhale' | 'pause';

interface BreathingState {
  phase: BreathingPhase;
  progress: number;
  cycle: number;
  depth: number;
}

// Different breathing patterns for different consciousness levels
const patterns = {
  basic: { inhale: 4, hold: 4, exhale: 4, pause: 2 }, // 4-4-4-2
  intermediate: { inhale: 4, hold: 7, exhale: 8, pause: 2 }, // 4-7-8-2
  advanced: { inhale: 6, hold: 6, exhale: 6, pause: 6 }, // Box breathing
  quantum: { inhale: 8, hold: 8, exhale: 8, pause: 8 } // Deep quantum
};

export const BreathingPattern: React.FC<{
  consciousness: number;
  onPhaseChange?: (phase: BreathingPhase, depth: number) => void;
}> = ({ consciousness, onPhaseChange }) => {
  const [state, setState] = useState<BreathingState>({
    phase: 'inhale',
    progress: 0,
    cycle: 0,
    depth: 0
  });

  // Select pattern based on consciousness
  const pattern = consciousness < 30 ? patterns.basic :
                  consciousness < 50 ? patterns.intermediate :
                  consciousness < 70 ? patterns.advanced :
                  patterns.quantum;

  useEffect(() => {
    const phases: BreathingPhase[] = ['inhale', 'hold', 'exhale', 'pause'];
    let currentPhaseIndex = 0;
    let progress = 0;
    
    const interval = setInterval(() => {
      const currentPhase = phases[currentPhaseIndex] ?? 'inhale';
      const duration = pattern[currentPhase];
      
      progress += 100 / (duration * 10); // 10 ticks per second
      
      if (progress >= 100) {
        // Move to next phase
        currentPhaseIndex = (currentPhaseIndex + 1) % phases.length;
        progress = 0;
        
        const newPhase = phases[currentPhaseIndex] ?? 'inhale';
        const newDepth = currentPhase === 'exhale' ? state.depth + 1 : state.depth;
        
        setState(prev => ({
          phase: newPhase,
          progress: 0,
          cycle: currentPhaseIndex === 0 ? prev.cycle + 1 : prev.cycle,
          depth: newDepth
        }));
        
        if (onPhaseChange) {
          onPhaseChange(newPhase, newDepth);
        }
      } else {
        setState(prev => ({ ...prev, progress }));
      }
    }, ANIMATION_INTERVALS.ultra);
    
    return () => clearInterval(interval);
  }, [pattern, onPhaseChange, state.depth]);

  const phaseColors = {
    inhale: 'from-blue-600 to-cyan-400',
    hold: 'from-purple-600 to-pink-400',
    exhale: 'from-green-600 to-emerald-400',
    pause: 'from-gray-600 to-gray-400'
  };

  return (
    <div className="fixed bottom-4 left-4 z-40">
      <motion.div 
        className="bg-black/80 backdrop-blur-sm border border-green-400/30 rounded-lg p-3 w-48"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="text-xs font-mono text-green-400 mb-2">
          Breathing Pattern
        </div>
        
        {/* Phase indicator */}
        <div className="text-sm font-mono mb-2 capitalize">
          {state.phase} ({Math.floor(state.progress)}%)
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-800 h-2 rounded mb-2">
          <motion.div 
            className={`h-full bg-gradient-to-r ${phaseColors[state.phase]} rounded`}
            animate={{ width: `${state.progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
        
        {/* Cycle counter */}
        <div className="text-xs text-gray-400">
          Cycle: {state.cycle} | Depth: {state.depth}
        </div>
        
        {/* Visual breathing indicator */}
        <motion.div
          className="mx-auto mt-2 w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 opacity-50"
          animate={{
            scale: state.phase === 'inhale' ? [1, 1.3] :
                   state.phase === 'hold' ? 1.3 :
                   state.phase === 'exhale' ? [1.3, 1] :
                   1
          }}
          transition={{ duration: pattern[state.phase], ease: "easeInOut" }}
        />
      </motion.div>
    </div>
  );
};

// Hook to sync navigation with breathing
export const useBreathingNavigation = (consciousness: number) => {
  const [canNavigate, setCanNavigate] = useState(true);
  const [navigationDepth, setNavigationDepth] = useState(0);
  
  const handlePhaseChange = (phase: BreathingPhase, depth: number) => {
    // Allow navigation on exhale phase for smooth transitions
    setCanNavigate(phase === 'exhale' || phase === 'pause');
    setNavigationDepth(depth);
  };
  
  return {
    canNavigate,
    navigationDepth,
    BreathingComponent: () => (
      <BreathingPattern 
        consciousness={consciousness}
        onPhaseChange={handlePhaseChange}
      />
    )
  };
};
