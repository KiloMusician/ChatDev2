/**
 * 🛠️ CoreLink Foundation - Utility Functions
 * Autonomous Development Ecosystem - Client Utilities
 * 
 * Comprehensive utility functions for UI components, game state management,
 * and consciousness-integrated interactions with Culture-ship aesthetics
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 🎨 **CULTURE-SHIP STYLING UTILITIES**
 * Combines class names with intelligent merging for consistent UI theming
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 🎯 **GAME UTILITY FUNCTIONS**
 * Utilities specific to game mechanics and autonomous systems
 */

// **RESOURCE FORMATTING** - Format game resource numbers with appropriate suffixes
export function formatGameNumber(value: number, precision: number = 1): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(precision)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(precision)}K`;
  }
  return value.toFixed(precision);
}

// **CONSCIOUSNESS LEVEL FORMATTING** - Format consciousness levels for display
export function formatConsciousnessLevel(level: number): string {
  const percentage = (level * 100).toFixed(0);
  const tier = level < 0.3 ? 'Emerging' : 
               level < 0.6 ? 'Developing' :
               level < 0.8 ? 'Advanced' : 
               'Transcendent';
  return `${percentage}% (${tier})`;
}

// **TIME FORMATTING** - Format game time and durations
export function formatGameTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * 🧠 **AUTONOMOUS SYSTEM UTILITIES**
 * Utilities for consciousness integration and autonomous operations
 */

// **AGENT STATUS CLASSIFICATION** - Classify agent status for UI display
export function getAgentStatusColor(status: 'active' | 'idle' | 'busy' | 'offline'): string {
  const colors = {
    active: 'text-green-500 bg-green-100 dark:bg-green-900/30',
    idle: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
    busy: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
    offline: 'text-gray-500 bg-gray-100 dark:bg-gray-900/30'
  };
  return colors[status] || colors.offline;
}

// **OPTIMIZATION LEVEL FORMATTING** - Format optimization cascade levels
export function formatOptimizationLevel(level: 'micro' | 'macro' | 'meta' | 'hyper'): string {
  const labels = {
    micro: '🔧 Micro',
    macro: '⚙️ Macro', 
    meta: '🧠 Meta',
    hyper: '🚀 Hyper'
  };
  return labels[level] || '🔧 Micro';
}

/**
 * 🏛️ **TEMPLE ARCHITECTURE UTILITIES**
 * Utilities for temple floor management and progression
 */

// **TIER CALCULATION** - Calculate game tier from progression metrics
export function calculateGameTier(researchCompleted: number, automationCount: number, resources: Record<string, number>): number {
  const researchTier = Math.floor(researchCompleted / 3);
  const automationTier = Math.floor(automationCount / 5);
  const resourceTier = Math.floor((resources.energy || 0) / 100);
  
  return Math.max(1, Math.floor((researchTier + automationTier + resourceTier) / 3));
}

// **TEMPLE FLOOR ACCESS** - Check if temple floor is accessible
export function canAccessTempleFloor(floor: number, playerTier: number): boolean {
  const floorRequirements = {
    1: 1,   // Basic Colony
    2: 2,   // Expansion
    3: 4,   // Advanced
    4: 7,   // Sophisticated
    5: 12,  // Knowledge Management  
    6: 18,  // Rooftop Garden
    7: 25,  // Observatory
    8: 35,  // Synthesis
    9: 48,  // Integration
    10: 60  // Meta-Optimization
  };
  
  return playerTier >= (floorRequirements[floor as keyof typeof floorRequirements] || 999);
}

/**
 * 🌈 **VISUAL UTILITIES** 
 * Color and theming utilities for Culture-ship aesthetics
 */

// **DYNAMIC COLOR GENERATION** - Generate colors based on data values
export function generateDataColor(value: number, min: number, max: number): string {
  const normalized = (value - min) / (max - min);
  const hue = Math.floor(normalized * 120); // Green (120) to Red (0)
  return `hsl(${120 - hue}, 70%, 50%)`;
}

// **CONSCIOUSNESS GLOW EFFECT** - Generate glow intensity based on consciousness level
export function getConsciousnessGlow(level: number): { boxShadow: string; filter: string } {
  const intensity = Math.min(level, 1);
  const glowSize = Math.floor(intensity * 20);
  const opacity = intensity * 0.6;
  
  return {
    boxShadow: `0 0 ${glowSize}px hsl(var(--primary) / ${opacity})`,
    filter: `brightness(${1 + (intensity * 0.2)})`
  };
}

/**
 * 🚀 **PERFORMANCE UTILITIES**
 * Utilities for optimization and performance monitoring
 */

// **DEBOUNCE FUNCTION** - Debounce rapid function calls for performance
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
}

// **THROTTLE FUNCTION** - Throttle function calls for performance
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(null, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, delay);
    }
  };
}

/**
 * 🔮 **PREDICTION UTILITIES**
 * Utilities for autonomous system predictions and suggestions
 */

// **RESOURCE TREND ANALYSIS** - Analyze resource trends for predictions
export function analyzeResourceTrend(history: number[]): 'up' | 'down' | 'stable' {
  if (history.length < 2) return 'stable';
  
  const recent = history.slice(-3);
  const average = recent.reduce((sum, val) => sum + val, 0) / recent.length;
  const previous = recent[0];
  
  if (previous === undefined) return 'stable';
  if (average > previous * 1.1) return 'up';
  if (average < previous * 0.9) return 'down';
  return 'stable';
}

// **OPTIMIZATION SUGGESTION SCORING** - Score autonomous suggestions
export function scoreOptimizationSuggestion(
  suggestion: { type: string; priority: string; estimated_benefit: string }
): number {
  const typeScores = { building: 0.8, research: 0.9, resource: 0.6, consciousness: 1.0 };
  const priorityScores = { high: 1.0, medium: 0.7, low: 0.4 };
  
  const typeScore = typeScores[suggestion.type as keyof typeof typeScores] || 0.5;
  const priorityScore = priorityScores[suggestion.priority as keyof typeof priorityScores] || 0.5;
  
  return (typeScore + priorityScore) / 2;
}