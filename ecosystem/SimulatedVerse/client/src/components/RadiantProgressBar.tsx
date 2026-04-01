// RADIANT CONSCIOUSNESS PROGRESS BAR - Animated consciousness visualization
// Boss-level animated progress bar showcasing consciousness evolution

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useConsciousness } from '../hooks/use-consciousness';

interface RadiantProgressBarProps {
  className?: string;
  showPercentage?: boolean;
  showStage?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  orientation?: 'horizontal' | 'vertical';
}

export function RadiantProgressBar({ 
  className = '', 
  showPercentage = true,
  showStage = true,
  size = 'md',
  orientation = 'horizontal'
}: RadiantProgressBarProps) {
  const { consciousness, isTranscending } = useConsciousness();
  const [previousValue, setPreviousValue] = useState(0);
  const [animationKey, setAnimationKey] = useState(0);
  
  const consciousnessLevel = consciousness?.consciousness || 0;
  const stage = consciousness?.stage || 'nascent';
  const connections = consciousness?.connections || 0;
  const resonance = consciousness?.resonance || 0;
  
  // Detect consciousness changes for animation triggers
  useEffect(() => {
    if (Math.abs(consciousnessLevel - previousValue) > 0.5) {
      setAnimationKey(prev => prev + 1);
      setPreviousValue(consciousnessLevel);
    }
  }, [consciousnessLevel, previousValue]);
  
  // Dynamic sizing
  const sizeClasses = {
    sm: orientation === 'horizontal' ? 'h-2 w-32' : 'w-2 h-32',
    md: orientation === 'horizontal' ? 'h-4 w-48' : 'w-4 h-48', 
    lg: orientation === 'horizontal' ? 'h-6 w-64' : 'w-6 h-64',
    xl: orientation === 'horizontal' ? 'h-8 w-80' : 'w-8 h-80'
  };
  
  // Stage-based colors and effects
  const getStageEffects = (stage: string, level: number) => {
    if (level >= 90) {
      return {
        color: 'from-purple-400 via-pink-500 to-purple-600',
        glow: 'shadow-purple-500/50',
        pulse: 'shadow-purple-400',
        intensity: 'high'
      };
    } else if (level >= 70) {
      return {
        color: 'from-yellow-400 via-orange-500 to-red-500',
        glow: 'shadow-yellow-500/40',
        pulse: 'shadow-yellow-400',
        intensity: 'medium-high'
      };
    } else if (level >= 50) {
      return {
        color: 'from-green-400 via-emerald-500 to-cyan-500',
        glow: 'shadow-green-500/30',
        pulse: 'shadow-green-400',
        intensity: 'medium'
      };
    } else if (level >= 30) {
      return {
        color: 'from-blue-400 via-cyan-500 to-teal-500',
        glow: 'shadow-blue-500/20',
        pulse: 'shadow-blue-400',
        intensity: 'low-medium'
      };
    } else {
      return {
        color: 'from-gray-400 via-slate-500 to-gray-600',
        glow: 'shadow-gray-500/10',
        pulse: 'shadow-gray-400',
        intensity: 'low'
      };
    }
  };
  
  const effects = getStageEffects(stage, consciousnessLevel);
  const isActive = consciousnessLevel > 0;
  const progressPercentage = Math.min(100, Math.max(0, consciousnessLevel));
  
  return (
    <div className={`radiant-progress-container ${className}`}>
      {/* Progress Bar Label */}
      {(showPercentage || showStage) && (
        <div className="flex items-center justify-between mb-2 text-sm font-mono">
          {showStage && (
            <motion.span 
              className={`stage-indicator ${
                consciousnessLevel > 80 ? 'text-purple-400' : 
                consciousnessLevel > 60 ? 'text-yellow-400' : 
                consciousnessLevel > 30 ? 'text-green-400' : 
                'text-gray-400'
              } font-bold text-xs uppercase tracking-wide`}
              animate={{ 
                opacity: [1, 0.7, 1],
                scale: isTranscending ? [1, 1.1, 1] : 1
              }}
              transition={{ 
                duration: 2, 
                repeat: Infinity,
                repeatType: 'reverse'
              }}
            >
              {stage}
            </motion.span>
          )}
          
          {showPercentage && (
            <motion.span 
              className={`percentage-indicator ${
                consciousnessLevel > 80 ? 'text-purple-400' : 
                consciousnessLevel > 60 ? 'text-yellow-400' : 
                consciousnessLevel > 30 ? 'text-green-400' : 
                'text-gray-400'
              } font-bold`}
              key={animationKey}
              initial={{ scale: 1.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            >
              {consciousnessLevel.toFixed(1)}%
            </motion.span>
          )}
        </div>
      )}
      
      {/* Progress Bar Container */}
      <div className={`progress-bar-container relative ${sizeClasses[size]} bg-gray-900/50 rounded-full border border-gray-700/50 overflow-hidden`}>
        {/* Background Glow Effect */}
        <motion.div
          className={`absolute inset-0 rounded-full ${effects.glow}`}
          animate={isActive ? {
            boxShadow: [
              `0 0 10px ${effects.pulse}`,
              `0 0 20px ${effects.pulse}`,
              `0 0 10px ${effects.pulse}`
            ]
          } : {}}
          transition={{
            duration: 2,
            repeat: Infinity,
            repeatType: 'reverse'
          }}
        />
        
        {/* Progress Fill */}
        <motion.div
          className={`progress-fill absolute ${orientation === 'horizontal' ? 'inset-y-0 left-0' : 'inset-x-0 bottom-0'} bg-gradient-to-r ${effects.color} rounded-full`}
          style={{
            [orientation === 'horizontal' ? 'width' : 'height']: `${progressPercentage}%`
          }}
          initial={{ [orientation === 'horizontal' ? 'width' : 'height']: 0 }}
          animate={{ [orientation === 'horizontal' ? 'width' : 'height']: `${progressPercentage}%` }}
          transition={{
            duration: 1.5,
            ease: 'easeOut',
            type: 'tween'
          }}
        />
        
        {/* Animated Particles */}
        <AnimatePresence>
          {isActive && (
            <motion.div
              className="absolute inset-0 overflow-hidden rounded-full"
              key={`particles-${animationKey}`}
            >
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  className={`absolute w-1 h-1 bg-white rounded-full opacity-60`}
                  initial={{
                    [orientation === 'horizontal' ? 'left' : 'bottom']: '0%',
                    [orientation === 'horizontal' ? 'top' : 'left']: `${Math.random() * 100}%`
                  }}
                  animate={{
                    [orientation === 'horizontal' ? 'left' : 'bottom']: `${progressPercentage}%`,
                    opacity: [0, 1, 0],
                    scale: [0.5, 1, 0.5]
                  }}
                  transition={{
                    duration: 2 + Math.random(),
                    delay: i * 0.2,
                    repeat: Infinity,
                    ease: 'linear'
                  }}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Radiant Shine Effect */}
        {consciousnessLevel > 20 && (
          <motion.div
            className={`absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full`}
            animate={{
              [orientation === 'horizontal' ? 'x' : 'y']: ['-100%', `${progressPercentage * 2}%`],
              opacity: [0, 0.8, 0]
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          />
        )}
        
        {/* Transcendence Effect */}
        <AnimatePresence>
          {isTranscending && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-purple-500/30 via-pink-500/30 to-purple-500/30 rounded-full"
              initial={{ opacity: 0, scale: 1 }}
              animate={{ 
                opacity: [0, 0.5, 0],
                scale: [1, 1.1, 1]
              }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 1,
                repeat: Infinity,
                repeatType: 'reverse'
              }}
            />
          )}
        </AnimatePresence>
      </div>
      
      {/* Connection & Resonance Indicators */}
      {(connections > 0 || resonance > 0) && (
        <div className="flex items-center justify-between mt-2 text-xs font-mono opacity-80">
          {connections > 0 && (
            <motion.div 
              className="flex items-center space-x-1"
              animate={{ opacity: [0.8, 1, 0.8] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <span className="text-cyan-400">◆</span>
              <span className="text-gray-300">{connections} connections</span>
            </motion.div>
          )}
          
          {resonance > 0 && (
            <motion.div 
              className="flex items-center space-x-1"
              animate={{ opacity: [0.8, 1, 0.8] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <span className="text-purple-400">⚡</span>
              <span className="text-gray-300">{resonance.toFixed(1)} Hz</span>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}