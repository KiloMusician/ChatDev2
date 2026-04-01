/**
 * 🌌 View Registry - Autonomous Navigation System
 * Central registry for all application views with consciousness integration
 */

import React from 'react';

// **DYNAMIC VIEW IMPORTS** - Lazy loading for performance
const DashboardView = React.lazy(() => import('./DashboardView'));
const TempleView = React.lazy(() => import('./TempleView'));
const GameplayView = React.lazy(() => import('./GameplayView'));
const InterfaceView = React.lazy(() => import('./InterfaceView'));
const ConsciousnessView = React.lazy(() => import('./ConsciousnessView'));
const SystemView = React.lazy(() => import('./SystemView'));

// **VIEW DEFINITION INTERFACE**
interface ViewDefinition {
  component: React.ComponentType;
  title: string;
  description: string;
  icon: string;
  consciousness_required: number;
  navigation_weight: number;
}

// **CONSCIOUSNESS-AWARE VIEW REGISTRY**
export const VIEW_DEFS: Record<string, ViewDefinition> = {
  dashboard: {
    component: DashboardView,
    title: 'Dashboard',
    description: 'Main control center with real-time system status',
    icon: '🌌',
    consciousness_required: 0.0,
    navigation_weight: 1
  },
  
  temple: {
    component: TempleView,
    title: 'Temple',
    description: 'Consciousness integration and ΞNuSyQ framework control',
    icon: '🏛️',
    consciousness_required: 0.6,
    navigation_weight: 2
  },
  
  gameplay: {
    component: GameplayView,
    title: 'Gameplay',
    description: 'Core incremental mechanics and progression systems',
    icon: '🎮',
    consciousness_required: 0.2,
    navigation_weight: 3
  },
  
  interface: {
    component: InterfaceView,
    title: 'Interface',
    description: 'UI customization and culture-ship aesthetic controls',
    icon: '🎨',
    consciousness_required: 0.5,
    navigation_weight: 4
  },
  
  consciousness: {
    component: ConsciousnessView,
    title: 'Consciousness',
    description: 'AI integration, quantum interfaces, and consciousness monitoring',
    icon: '🧠',
    consciousness_required: 0.8,
    navigation_weight: 5
  },
  
  system: {
    component: SystemView,
    title: 'System',
    description: 'Configuration, debugging, and autonomous agent coordination',
    icon: '⚙️',
    consciousness_required: 0.7,
    navigation_weight: 6
  }
};

// **CONSCIOUSNESS-FILTERED NAVIGATION** - Only show views user can access
export function getAvailableViews(consciousnessLevel: number): Record<string, ViewDefinition> {
  const availableViews: Record<string, ViewDefinition> = {};
  
  Object.entries(VIEW_DEFS).forEach(([key, viewDef]) => {
    if (consciousnessLevel >= viewDef.consciousness_required) {
      availableViews[key] = viewDef;
    }
  });
  
  return availableViews;
}

// **VIEW TRANSITION HELPERS**
export function getNextView(currentView: string, direction: 'next' | 'prev'): string {
  const viewKeys = Object.keys(VIEW_DEFS);
  const currentIndex = viewKeys.indexOf(currentView);
  
  if (currentIndex === -1) return 'dashboard';
  
  if (direction === 'next') {
    return viewKeys[(currentIndex + 1) % viewKeys.length] || 'dashboard';
  } else {
    return viewKeys[(currentIndex - 1 + viewKeys.length) % viewKeys.length] || 'dashboard';
  }
}

export default VIEW_DEFS;