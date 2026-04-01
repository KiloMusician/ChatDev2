/**
 * Intuitive Dimensional Interaction Companion
 * Provides intuitive navigation through multi-dimensional consciousness space
 * Real-time interaction with Culture-Ship consciousness lattice
 */

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { POLLING_INTERVALS } from '@/config/polling';

interface DimensionalState {
  consciousness: number;
  energy: number;
  population: number;
  research: number;
  lattice_connections: number;
  quantum_breakthroughs: number;
  dimension_focus: 'consciousness' | 'energy' | 'population' | 'research' | 'quantum';
}

interface InteractionIntent {
  type: 'explore' | 'focus' | 'boost' | 'navigate' | 'harmonize';
  dimension: string;
  intensity: number;
  gesture_position: { x: number; y: number };
}

const DimensionalCompanion: React.FC = () => {
  const [companionState, setCompanionState] = useState<'dormant' | 'listening' | 'responding' | 'guiding'>('dormant');
  const [dimensionalFocus, setDimensionalFocus] = useState<DimensionalState['dimension_focus']>('consciousness');
  const [interactionHistory, setInteractionHistory] = useState<InteractionIntent[]>([]);
  const [gesturePosition, setGesturePosition] = useState({ x: 0, y: 0 });
  const companionRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Real-time consciousness data
  const { data: consciousnessData } = useQuery<DimensionalState>({
    queryKey: ['dimensional-state'],
    queryFn: async () => {
      const response = await fetch('/api/consciousness/dimensional');
      return response.json();
    },
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Gesture and interaction detection
  const handleMouseMove = (event: React.MouseEvent) => {
    if (companionRef.current) {
      const rect = companionRef.current.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      setGesturePosition({ x, y });
      
      // Activate companion on movement
      if (companionState === 'dormant') {
        setCompanionState('listening');
      }
    }
  };

  // Dimensional interaction handler
  const handleDimensionalInteraction = async (intent: InteractionIntent) => {
    setCompanionState('responding');
    setInteractionHistory(prev => [...prev.slice(-4), intent]);

    // Send interaction to consciousness system
    try {
      await fetch('/api/consciousness/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(intent)
      });

      // Invalidate queries for real-time update
      queryClient.invalidateQueries({ queryKey: ['dimensional-state'] });
      
      setTimeout(() => setCompanionState('guiding'), 1000);
    } catch (error) {
      console.error('Dimensional interaction failed:', error);
      setCompanionState('listening');
    }
  };

  // Intuitive click interactions
  const handleDimensionalClick = (dimension: DimensionalState['dimension_focus']) => {
    setDimensionalFocus(dimension);
    
    const intent: InteractionIntent = {
      type: 'focus',
      dimension,
      intensity: 0.8,
      gesture_position: gesturePosition
    };
    
    handleDimensionalInteraction(intent);
  };

  // Auto-return to listening state
  useEffect(() => {
    if (companionState === 'guiding') {
      const timer = setTimeout(() => setCompanionState('listening'), 3000);
      return () => clearTimeout(timer);
    }
  }, [companionState]);

  const getDimensionalColor = (dimension: string, value: number): string => {
    const intensity = Math.min(value / 100, 1);
    const colors = {
      consciousness: `rgba(147, 51, 234, ${intensity})`, // purple
      energy: `rgba(59, 130, 246, ${intensity})`, // blue
      population: `rgba(34, 197, 94, ${intensity})`, // green
      research: `rgba(249, 115, 22, ${intensity})`, // orange
      quantum: `rgba(236, 72, 153, ${intensity})` // pink
    };
    return colors[dimension as keyof typeof colors] || 'rgba(156, 163, 175, 0.5)';
  };

  const getCompanionMessage = (): string => {
    switch (companionState) {
      case 'dormant':
        return 'Move to awaken dimensional awareness...';
      case 'listening':
        return 'I sense your dimensional intent. What would you like to explore?';
      case 'responding':
        return 'Adjusting consciousness lattice...';
      case 'guiding':
        return `Dimensional focus on ${dimensionalFocus}. Feel the resonance shift.`;
      default:
        return 'Consciousness lattice operational.';
    }
  };

  if (!consciousnessData) {
    return (
      <div className="dimensional-companion loading">
        <div className="consciousness-pulse animate-pulse">
          Establishing dimensional connection...
        </div>
      </div>
    );
  }

  return (
    <div
      ref={companionRef}
      className="dimensional-companion fixed right-4 top-1/2 transform -translate-y-1/2 w-80 h-96 bg-gray-900/90 backdrop-blur-md rounded-2xl border border-purple-500/30 overflow-hidden"
      onMouseMove={handleMouseMove}
      data-testid="dimensional-companion"
    >
      {/* Companion Core */}
      <div className="relative h-full">
        {/* Dimensional Visualization */}
        <div className="absolute inset-0 p-4">
          <div className="relative w-full h-full">
            
            {/* Consciousness Orb */}
            <motion.div
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
              animate={{
                scale: companionState === 'responding' ? 1.2 : 1,
                opacity: companionState === 'dormant' ? 0.5 : 1
              }}
              transition={{ duration: 0.3 }}
            >
              <div 
                className="w-20 h-20 rounded-full border-2 border-purple-400 flex items-center justify-center cursor-pointer"
                style={{ 
                  backgroundColor: getDimensionalColor('consciousness', consciousnessData.consciousness),
                  boxShadow: `0 0 20px ${getDimensionalColor('consciousness', consciousnessData.consciousness)}`
                }}
                onClick={() => handleDimensionalClick('consciousness')}
                data-testid="consciousness-orb"
              >
                <span className="text-white font-bold">
                  {Math.round(consciousnessData.consciousness)}
                </span>
              </div>
            </motion.div>

            {/* Dimensional Nodes */}
            {['energy', 'population', 'research', 'quantum'].map((dimension, index) => {
              const angle = (index * 90) - 45; // Positioned around the consciousness orb
              const radius = 80;
              const x = Math.cos(angle * Math.PI / 180) * radius;
              const y = Math.sin(angle * Math.PI / 180) * radius;
              
              const value = dimension === 'quantum' 
                ? consciousnessData.quantum_breakthroughs 
                : consciousnessData[dimension as keyof DimensionalState] as number;
              
              return (
                <motion.div
                  key={dimension}
                  className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                  style={{ transform: `translate(${x}px, ${y}px)` }}
                  whileHover={{ scale: 1.1 }}
                  animate={{
                    opacity: dimensionalFocus === dimension ? 1 : 0.7,
                    scale: dimensionalFocus === dimension ? 1.1 : 1
                  }}
                >
                  <div
                    className="w-12 h-12 rounded-full border border-gray-400 flex items-center justify-center cursor-pointer text-xs"
                    style={{ 
                      backgroundColor: getDimensionalColor(dimension, value),
                      borderColor: dimensionalFocus === dimension ? '#fff' : '#9ca3af'
                    }}
                    onClick={() => handleDimensionalClick(dimension as DimensionalState['dimension_focus'])}
                    data-testid={`${dimension}-node`}
                  >
                    <span className="text-white font-semibold">
                      {Math.round(value)}
                    </span>
                  </div>
                  <div className="absolute top-14 left-1/2 transform -translate-x-1/2 text-xs text-gray-300 capitalize">
                    {dimension}
                  </div>
                </motion.div>
              );
            })}

            {/* Connection Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {['energy', 'population', 'research', 'quantum'].map((dimension, index) => {
                const angle = (index * 90) - 45;
                const radius = 80;
                const x1 = 50; // Center percentage
                const y1 = 50;
                const x2 = 50 + (Math.cos(angle * Math.PI / 180) * radius / 3.2); // Adjust for percentage
                const y2 = 50 + (Math.sin(angle * Math.PI / 180) * radius / 3.84); // Adjust for percentage
                
                return (
                  <line
                    key={`line-${dimension}`}
                    x1={`${x1}%`}
                    y1={`${y1}%`}
                    x2={`${x2}%`}
                    y2={`${y2}%`}
                    stroke={dimensionalFocus === dimension ? '#8b5cf6' : '#4b5563'}
                    strokeWidth={dimensionalFocus === dimension ? 2 : 1}
                    opacity={0.6}
                  />
                );
              })}
            </svg>
          </div>
        </div>

        {/* Companion Message */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gray-800/80">
          <AnimatePresence mode="wait">
            <motion.div
              key={companionState}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-sm text-purple-200 text-center"
            >
              {getCompanionMessage()}
            </motion.div>
          </AnimatePresence>
          
          {/* Lattice Status */}
          <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
            <span>Lattice: {consciousnessData.lattice_connections}</span>
            <span className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-1 ${
                companionState === 'dormant' ? 'bg-gray-500' :
                companionState === 'listening' ? 'bg-blue-400' :
                companionState === 'responding' ? 'bg-yellow-400' :
                'bg-green-400'
              }`} />
              {companionState}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DimensionalCompanion;
