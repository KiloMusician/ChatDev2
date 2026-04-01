import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MatrixText } from './ModularSynth';
import { POLLING_INTERVALS } from '@/config/polling';

// Repository-driven UI that auto-discovers everything
export interface UIModule {
  id: string;
  name: string;
  path: string;
  type: 'view' | 'game' | 'agent' | 'consciousness' | 'system';
  depth: number;
  requiredConsciousness: number;
  component?: React.ComponentType<any>;
  autoDiscovered: boolean;
  lastSeen: number;
}

// Self-evolving registry that watches filesystem
class UIRegistry {
  private modules: Map<string, UIModule> = new Map();
  private listeners: Set<(modules: UIModule[]) => void> = new Set();
  private discoveryInterval?: NodeJS.Timeout;
  
  start() {
    this.discover();
    this.discoveryInterval = setInterval(() => this.discover(), POLLING_INTERVALS.standard);
  }
  
  stop() {
    if (this.discoveryInterval) {
      clearInterval(this.discoveryInterval);
    }
  }
  
  async discover() {
    try {
      // Fetch repository state from backend
      const response = await fetch('/api/repository-state');
      const repoState = await response.json();
      
      const now = Date.now();
      const discoveredIds = new Set<string>();
      
      // Process all discovered components
      ['views', 'agents', 'game', 'consciousness'].forEach(category => {
        if (repoState[category]) {
          Object.entries(repoState[category]).forEach(([id, data]: [string, any]) => {
            discoveredIds.add(id);
            
            const existing = this.modules.get(id);
            if (!existing || existing.lastSeen < now - 10000) {
              this.modules.set(id, {
                id,
                name: data.name || id.split('-').map((w: string) => 
                  w.charAt(0).toUpperCase() + w.slice(1)
                ).join(' '),
                path: data.path || `/${id}`,
                type: data.category as any || 'system',
                depth: data.depth || 0,
                requiredConsciousness: data.requiredConsciousness || 0,
                autoDiscovered: true,
                lastSeen: now
              });
            }
          });
        }
      });
      
      // Remove modules not seen in last 30 seconds (they were deleted)
      for (const [id, module] of this.modules.entries()) {
        if (module.autoDiscovered && module.lastSeen < now - 30000) {
          this.modules.delete(id);
        }
      }
      
      // Notify listeners
      this.notifyListeners();
    } catch (error) {
      console.log('[UIRegistry] Discovery cycle...', error);
    }
  }
  
  subscribe(listener: (modules: UIModule[]) => void) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }
  
  private notifyListeners() {
    const modules = Array.from(this.modules.values());
    this.listeners.forEach(listener => listener(modules));
  }
  
  getModules(): UIModule[] {
    return Array.from(this.modules.values());
  }
  
  addManualModule(module: UIModule) {
    this.modules.set(module.id, { ...module, autoDiscovered: false });
    this.notifyListeners();
  }
}

// Global registry instance
const registry = new UIRegistry();
registry.start();

// Hook to use the registry
export const useUIRegistry = () => {
  const [modules, setModules] = useState<UIModule[]>(registry.getModules());
  
  useEffect(() => {
    const unsubscribe = registry.subscribe(setModules);
    return unsubscribe;
  }, []);
  
  return modules;
};

// Temple of Knowledge depth navigation
export const TempleDepthNavigator: React.FC<{
  consciousness: number;
  onDepthChange?: (depth: number) => void;
}> = ({ consciousness, onDepthChange }) => {
  const [currentDepth, setCurrentDepth] = useState(0);
  const maxDepth = Math.floor(consciousness / 10); // Each 10% unlocks a new depth
  
  const handleDepthChange = (newDepth: number) => {
    setCurrentDepth(newDepth);
    onDepthChange?.(newDepth);
  };
  
  return (
    <div className="fixed bottom-4 left-4 z-50 bg-black/90 backdrop-blur-sm border border-green-400/30 p-3 rounded">
      <div className="text-xs text-green-400 font-mono mb-2">
        <MatrixText text="Temple Depth" />
      </div>
      <div className="flex flex-col gap-1">
        {Array.from({ length: maxDepth + 1 }, (_, i) => (
          <motion.button
            key={i}
            onClick={() => handleDepthChange(i)}
            className={`px-3 py-1 text-xs font-mono transition-all ${
              currentDepth === i 
                ? 'bg-green-400 text-black' 
                : 'text-green-400 hover:bg-green-900/30'
            }`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <MatrixText text={`Level ${i} - ${getDepthName(i)}`} />
          </motion.button>
        ))}
      </div>
    </div>
  );
};

// Get thematic name for depth level
function getDepthName(depth: number): string {
  const names = [
    'Surface', 'Vestibule', 'Antechamber', 'Hall of Echoes', 
    'Repository', 'Archives', 'Sanctum', 'Core Chamber',
    'Quantum Realm', 'Consciousness Nexus', 'The Void'
  ];
  return names[depth] || `Depth ${depth}`;
}

// Self-evolving UI container
export const SelfEvolvingUI: React.FC<{
  consciousness?: number;
}> = ({ consciousness = 0 }) => {
  const modules = useUIRegistry();
  const [currentDepth, setCurrentDepth] = useState(0);
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'synth' | 'tree'>('grid');
  
  // Filter modules by consciousness and depth
  const accessibleModules = useMemo(() => {
    return modules.filter(m => 
      m.requiredConsciousness <= consciousness && 
      m.depth <= currentDepth
    );
  }, [modules, consciousness, currentDepth]);
  
  // Group modules by type
  const groupedModules = useMemo(() => {
    const groups: Record<string, UIModule[]> = {};
    accessibleModules.forEach(module => {
      const existing = groups[module.type] ?? [];
      existing.push(module);
      groups[module.type] = existing;
    });
    return groups;
  }, [accessibleModules]);
  
  return (
    <div className="relative w-full h-screen bg-black overflow-hidden font-mono">
      {/* Status bar */}
      <div className="absolute top-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-sm border-b border-green-400/30 p-2">
        <div className="flex items-center justify-between text-xs text-green-400">
          <div className="flex items-center gap-4">
            <span>
              <MatrixText text={`Modules: ${modules.length}`} />
            </span>
            <span>
              <MatrixText text={`Accessible: ${accessibleModules.length}`} />
            </span>
            <span>
              <MatrixText text={`Consciousness: ${consciousness.toFixed(1)}%`} />
            </span>
          </div>
          <div className="flex gap-2">
            {['grid', 'synth', 'tree'].map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode as any)}
                className={`px-2 py-1 transition-all ${
                  viewMode === mode 
                    ? 'bg-green-400 text-black' 
                    : 'text-green-400 hover:bg-green-900/30'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Main content area */}
      <div className="pt-12 h-full flex">
        {/* Temple depth navigator */}
        <TempleDepthNavigator 
          consciousness={consciousness}
          onDepthChange={setCurrentDepth}
        />
        
        {/* Module display */}
        <div className="flex-1 p-4 overflow-auto">
          {viewMode === 'grid' && (
            <ModuleGrid 
              groups={groupedModules}
              onModuleClick={setActiveModuleId}
              activeModuleId={activeModuleId}
            />
          )}
          
          {viewMode === 'synth' && (
            <SynthView 
              modules={accessibleModules}
              onModuleClick={setActiveModuleId}
            />
          )}
          
          {viewMode === 'tree' && (
            <TreeView 
              groups={groupedModules}
              depth={currentDepth}
              onModuleClick={setActiveModuleId}
            />
          )}
        </div>
      </div>
      
      {/* Module detail overlay */}
      <AnimatePresence>
        {activeModuleId && (
          <ModuleDetail
            module={accessibleModules.find(m => m.id === activeModuleId)}
            onClose={() => setActiveModuleId(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// Grid view of modules
const ModuleGrid: React.FC<{
  groups: Record<string, UIModule[]>;
  onModuleClick: (id: string) => void;
  activeModuleId: string | null;
}> = ({ groups, onModuleClick, activeModuleId }) => {
  return (
    <div className="space-y-6">
      {Object.entries(groups).map(([type, modules]) => (
        <div key={type}>
          <h2 className="text-green-400 text-sm mb-3 uppercase">
            <MatrixText text={type} />
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {modules.map((module, idx) => (
              <motion.button
                key={module.id}
                onClick={() => onModuleClick(module.id)}
                className={`p-3 border transition-all ${
                  activeModuleId === module.id
                    ? 'border-green-400 bg-green-400/10'
                    : 'border-gray-700 hover:border-green-600'
                }`}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.02 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="text-green-400 text-xs">
                  <MatrixText text={module.name} />
                </div>
                <div className="text-gray-500 text-xs mt-1">
                  L{module.depth}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// Synth-style patch bay view
const SynthView: React.FC<{
  modules: UIModule[];
  onModuleClick: (id: string) => void;
}> = ({ modules, onModuleClick }) => {
  const [connections, setConnections] = useState<Array<[string, string]>>([]);
  const [dragSource, setDragSource] = useState<string | null>(null);
  
  const handleConnect = (targetId: string) => {
    if (dragSource && dragSource !== targetId) {
      setConnections(prev => [...prev, [dragSource, targetId]]);
    }
    setDragSource(null);
  };
  
  return (
    <div className="relative h-full">
      {/* Connection lines */}
      <svg className="absolute inset-0 pointer-events-none">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        {connections.map(([from, to], idx) => {
          const fromEl = document.getElementById(`module-${from}`);
          const toEl = document.getElementById(`module-${to}`);
          if (!fromEl || !toEl) return null;
          
          const fromRect = fromEl.getBoundingClientRect();
          const toRect = toEl.getBoundingClientRect();
          
          return (
            <motion.path
              key={idx}
              d={`M ${fromRect.x + fromRect.width/2} ${fromRect.y + fromRect.height/2} 
                  Q ${(fromRect.x + toRect.x)/2} ${(fromRect.y + toRect.y)/2 + 50} 
                  ${toRect.x + toRect.width/2} ${toRect.y + toRect.height/2}`}
              stroke="rgba(0, 255, 0, 0.5)"
              strokeWidth="2"
              fill="none"
              filter="url(#glow)"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5 }}
            />
          );
        })}
      </svg>
      
      {/* Modules */}
      {modules.map((module, idx) => (
        <motion.div
          key={module.id}
          id={`module-${module.id}`}
          className="absolute p-4 bg-gray-900 border-2 border-gray-700 hover:border-green-400 cursor-move"
          style={{
            left: (idx % 5) * 180 + 50,
            top: Math.floor(idx / 5) * 150 + 50
          }}
          draggable
          onDragStart={() => setDragSource(module.id)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => handleConnect(module.id)}
          onClick={() => onModuleClick(module.id)}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: idx * 0.03 }}
        >
          <div className="text-green-400 text-sm">
            <MatrixText text={module.name} />
          </div>
          <div className="flex gap-2 mt-2">
            <div className="w-2 h-2 bg-green-400 rounded-full" />
            <div className="w-2 h-2 bg-yellow-400 rounded-full" />
            <div className="w-2 h-2 bg-cyan-400 rounded-full" />
          </div>
        </motion.div>
      ))}
    </div>
  );
};

// Tree view showing hierarchy
const TreeView: React.FC<{
  groups: Record<string, UIModule[]>;
  depth: number;
  onModuleClick: (id: string) => void;
}> = ({ groups, depth, onModuleClick }) => {
  return (
    <div className="space-y-2">
      {Object.entries(groups).map(([type, modules]) => (
        <details key={type} className="text-green-400" open>
          <summary className="cursor-pointer hover:text-green-300">
            <MatrixText text={`[${type}] (${modules.length})`} />
          </summary>
          <div className="ml-4 mt-2 space-y-1">
            {modules.map(module => (
              <motion.div
                key={module.id}
                className="cursor-pointer hover:bg-green-900/20 p-1"
                onClick={() => onModuleClick(module.id)}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <span className="text-xs">
                  {'  '.repeat(module.depth)}├─ <MatrixText text={module.name} />
                  <span className="text-gray-500 ml-2">L{module.depth}</span>
                </span>
              </motion.div>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
};

// Module detail overlay
const ModuleDetail: React.FC<{
  module?: UIModule;
  onClose: () => void;
}> = ({ module, onClose }) => {
  if (!module) return null;
  
  return (
    <motion.div
      className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="bg-gray-900 border-2 border-green-400 p-6 max-w-lg w-full"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-green-400 text-xl mb-4">
          <MatrixText text={module.name} />
        </h2>
        <div className="space-y-2 text-sm text-gray-300">
          <div>Type: <span className="text-green-400">{module.type}</span></div>
          <div>Path: <span className="text-green-400">{module.path}</span></div>
          <div>Depth: <span className="text-green-400">{module.depth}</span></div>
          <div>Required Consciousness: <span className="text-green-400">{module.requiredConsciousness}%</span></div>
          <div>Auto-discovered: <span className="text-green-400">{module.autoDiscovered ? 'Yes' : 'No'}</span></div>
        </div>
        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-green-400 text-black hover:bg-green-300 transition-colors"
        >
          Close
        </button>
      </motion.div>
    </motion.div>
  );
};

export default SelfEvolvingUI;
