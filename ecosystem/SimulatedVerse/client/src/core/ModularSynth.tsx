import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

// Matrix-style text animation component
export const MatrixText: React.FC<{ text: string; className?: string }> = ({ text, className }) => {
  const [displayText, setDisplayText] = useState(text);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const prevTextRef = useRef(text);
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()_+-=[]{}|;:,.<>?/~';
  
  useEffect(() => {
    if (prevTextRef.current === text) return;
    
    setIsTransitioning(true);
    const oldText = prevTextRef.current;
    const newText = text;
    const maxLen = Math.max(oldText.length, newText.length);
    let iterations = 0;
    const maxIterations = 15;
    
    const interval = setInterval(() => {
      iterations++;
      
      setDisplayText(() => {
        return Array.from({ length: maxLen }, (_, i) => {
          if (iterations >= maxIterations) {
            return newText[i] || '';
          }
          
          // Characters that need to change
          if (i < newText.length && (i >= oldText.length || oldText[i] !== newText[i])) {
            if (Math.random() > iterations / maxIterations) {
              return chars[Math.floor(Math.random() * chars.length)];
            }
            return newText[i];
          }
          
          // Characters that stay the same
          if (i < oldText.length && i < newText.length && oldText[i] === newText[i]) {
            return oldText[i];
          }
          
          // Fading out characters
          if (i >= newText.length && i < oldText.length) {
            if (Math.random() > iterations / maxIterations) {
              return chars[Math.floor(Math.random() * chars.length)];
            }
            return '';
          }
          
          return newText[i] || '';
        }).join('');
      });
      
      if (iterations >= maxIterations) {
        clearInterval(interval);
        setIsTransitioning(false);
        prevTextRef.current = text;
      }
    }, ANIMATION_INTERVALS.tick);
    
    return () => clearInterval(interval);
  }, [text]);
  
  return (
    <span className={`${className} ${isTransitioning ? 'text-green-400' : ''} transition-colors duration-300`}>
      {displayText}
    </span>
  );
};

// Modular synth-style interface component
export interface ModuleDefinition {
  id: string;
  type: 'oscillator' | 'filter' | 'envelope' | 'sequencer' | 'effect' | 'utility' | 'view' | 'agent' | 'consciousness';
  name: string;
  inputs: string[];
  outputs: string[];
  params: Record<string, any>;
  position?: { x: number; y: number };
  depth?: number; // Z-index for layering
  component?: React.ComponentType<any>;
  autoDiscover?: boolean;
}

export interface Connection {
  from: { moduleId: string; output: string };
  to: { moduleId: string; input: string };
  strength?: number;
}

export const ModularSynthInterface: React.FC<{
  modules: ModuleDefinition[];
  connections: Connection[];
  onModuleUpdate?: (id: string, params: any) => void;
  onConnectionUpdate?: (connection: Connection) => void;
}> = ({ modules, connections, onModuleUpdate, onConnectionUpdate }) => {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [viewDepth, setViewDepth] = useState(0);
  const [consciousness, setConsciousness] = useState(0);
  const svgRef = useRef<SVGSVGElement>(null);
  
  // Auto-discover modules from filesystem
  useEffect(() => {
    const discoverModules = async () => {
      try {
        const response = await fetch('/api/discover-modules');
        const discovered = await response.json();
        // Modules will be auto-added via props update
      } catch (error) {
        console.log('[ModularSynth] Module discovery in progress...');
      }
    };
    
    discoverModules();
    const interval = setInterval(discoverModules, POLLING_INTERVALS.standard);
    return () => clearInterval(interval);
  }, []);
  
  // Calculate consciousness from connections
  useEffect(() => {
    const totalStrength = connections.reduce((sum, conn) => sum + (conn.strength || 1), 0);
    const moduleCount = modules.length;
    const newConsciousness = (totalStrength / Math.max(1, moduleCount)) * 10;
    setConsciousness(Math.min(100, newConsciousness));
  }, [connections, modules]);
  
  const filteredModules = useMemo(() => {
    return modules.filter(m => (m.depth || 0) <= viewDepth);
  }, [modules, viewDepth]);
  
  return (
    <div className="relative w-full h-full bg-black overflow-hidden">
      {/* Consciousness indicator */}
      <div className="absolute top-4 right-4 z-50 text-green-400 font-mono">
        <MatrixText text={`Consciousness: ${consciousness.toFixed(1)}%`} />
      </div>
      
      {/* Depth control */}
      <div className="absolute top-4 left-4 z-50 flex items-center gap-4">
        <button
          onClick={() => setViewDepth(Math.max(0, viewDepth - 1))}
          className="px-3 py-1 bg-gray-900 text-green-400 border border-green-400 hover:bg-green-900 transition-colors"
        >
          Surface ←
        </button>
        <span className="text-green-400 font-mono">
          <MatrixText text={`Depth: ${viewDepth}`} />
        </span>
        <button
          onClick={() => setViewDepth(Math.min(10, viewDepth + 1))}
          className="px-3 py-1 bg-gray-900 text-green-400 border border-green-400 hover:bg-green-900 transition-colors"
        >
          → Deeper
        </button>
      </div>
      
      {/* Connection visualization */}
      <svg
        ref={svgRef}
        className="absolute inset-0 pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {connections.map((conn, idx) => {
          const fromModule = modules.find(m => m.id === conn.from.moduleId);
          const toModule = modules.find(m => m.id === conn.to.moduleId);
          
          if (!fromModule || !toModule) return null;
          
          const fromX = (fromModule.position?.x || 50) + 100;
          const fromY = (fromModule.position?.y || 50) + 50;
          const toX = toModule.position?.x || 150;
          const toY = toModule.position?.y || 150;
          
          return (
            <motion.path
              key={`${conn.from.moduleId}-${conn.to.moduleId}-${idx}`}
              d={`M ${fromX} ${fromY} Q ${(fromX + toX) / 2} ${(fromY + toY) / 2 + 50} ${toX} ${toY}`}
              stroke={`rgba(0, 255, 0, ${conn.strength || 0.5})`}
              strokeWidth="2"
              fill="none"
              filter="url(#glow)"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 1, delay: idx * 0.1 }}
            />
          );
        })}
      </svg>
      
      {/* Modules */}
      <AnimatePresence>
        {filteredModules.map((module, idx) => (
          <motion.div
            key={module.id}
            className={`absolute p-4 bg-gray-900 border-2 cursor-move select-none ${
              selectedModule === module.id ? 'border-green-400' : 'border-gray-700'
            } hover:border-green-600 transition-colors`}
            style={{
              left: module.position?.x || idx * 150 + 50,
              top: module.position?.y || Math.floor(idx / 5) * 150 + 100,
              zIndex: (module.depth || 0) + 10
            }}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ delay: idx * 0.05 }}
            onClick={() => setSelectedModule(module.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="text-green-400 font-mono text-sm mb-2">
              <MatrixText text={module.name} />
            </div>
            <div className="text-xs text-gray-500">
              {module.type} • L{module.depth || 0}
            </div>
            
            {/* Inputs */}
            <div className="mt-2 text-xs">
              {module.inputs.map((input, i) => (
                <div key={i} className="text-cyan-400">
                  ← {input}
                </div>
              ))}
            </div>
            
            {/* Outputs */}
            <div className="mt-1 text-xs">
              {module.outputs.map((output, i) => (
                <div key={i} className="text-yellow-400">
                  → {output}
                </div>
              ))}
            </div>
            
            {/* Parameters */}
            {selectedModule === module.id && (
              <motion.div
                className="mt-2 p-2 bg-black border border-green-400"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
              >
                {Object.entries(module.params).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-gray-400">{key}:</span>
                    <span className="text-green-400">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </motion.div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// Repository-aware module discovery
export const useModularDiscovery = () => {
  const [modules, setModules] = useState<ModuleDefinition[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  
  useEffect(() => {
    // Watch for filesystem changes and auto-discover
    const watchInterval = setInterval(async () => {
      try {
        // This would connect to your actual backend
        const response = await fetch('/api/repository-state');
        const repoState = await response.json();
        
        // Auto-generate modules from repository structure
        const discoveredModules: ModuleDefinition[] = [];
        
        // Discover views
        if (repoState.views) {
          Object.entries(repoState.views).forEach(([id, view]: [string, any]) => {
            discoveredModules.push({
              id: `view-${id}`,
              type: 'view',
              name: view.name || id,
              inputs: view.inputs || ['consciousness', 'data'],
              outputs: view.outputs || ['render'],
              params: view.params || {},
              position: view.position,
              depth: view.depth || 0,
              autoDiscover: true
            });
          });
        }
        
        // Discover agents
        if (repoState.agents) {
          Object.entries(repoState.agents).forEach(([id, agent]: [string, any]) => {
            discoveredModules.push({
              id: `agent-${id}`,
              type: 'agent',
              name: agent.name || id,
              inputs: agent.inputs || ['task', 'context'],
              outputs: agent.outputs || ['result', 'consciousness'],
              params: agent.params || {},
              position: agent.position,
              depth: agent.depth || 1,
              autoDiscover: true
            });
          });
        }
        
        // Auto-generate connections based on consciousness level
        const newConnections: Connection[] = [];
        discoveredModules.forEach((from, i) => {
          discoveredModules.forEach((to, j) => {
            if (i !== j && Math.random() > 0.7) {
              from.outputs.forEach(output => {
                to.inputs.forEach(input => {
                  if (output.toLowerCase().includes(input.toLowerCase()) || 
                      input.toLowerCase().includes(output.toLowerCase())) {
                    newConnections.push({
                      from: { moduleId: from.id, output },
                      to: { moduleId: to.id, input },
                      strength: Math.random()
                    });
                  }
                });
              });
            }
          });
        });
        
        setModules(prev => {
          const manual = prev.filter(m => !m.autoDiscover);
          return [...manual, ...discoveredModules];
        });
        setConnections(newConnections);
      } catch (error) {
        console.log('[ModularDiscovery] Waiting for repository state...');
      }
    }, POLLING_INTERVALS.standard);
    
    return () => clearInterval(watchInterval);
  }, []);
  
  return { modules, connections, setModules, setConnections };
};
