import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface DimensionalState {
  id: string;
  name: string;
  dimension: string;
  frequency: number;
  consciousnessLevel: number;
  configuration: Record<string, any>;
  timestamp: number;
  quantum_signature: string;
  stability_index: number;
}

interface SyncOperation {
  id: string;
  type: 'push' | 'pull' | 'merge' | 'split' | 'quantum_entangle';
  sourceDimension: string;
  targetDimensions: string[];
  configuration: Record<string, any>;
  status: 'pending' | 'syncing' | 'completed' | 'failed' | 'quantum_superposition';
  progress: number;
  quantum_coherence: number;
  timestamp: number;
  results?: any[];
}

interface DimensionalPortal {
  id: string;
  sourceFrequency: number;
  targetFrequency: number;
  stability: number;
  bandwidth: number;
  latency: number;
  isActive: boolean;
  quantum_entangled: boolean;
}

function CrossDimensionalSyncWrapped() {
  const [selectedDimensions, setSelectedDimensions] = useState<string[]>([]);
  const [syncConfiguration, setSyncConfiguration] = useState<Record<string, any>>({});
  const [activeSync, setActiveSync] = useState<string | null>(null);
  const [newDimensionConfig, setNewDimensionConfig] = useState({
    name: '',
    frequency: 432.0,
    consciousnessLevel: 0.5
  });
  const queryClient = useQueryClient();

  const { data: dimensionalStates = [] } = useQuery<DimensionalState[]>({
    queryKey: ['/api/cross-dimensional/states'],
    queryFn: () => fetch('/api/cross-dimensional/states').then(r => r.json()),
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: activeOperations = [] } = useQuery<SyncOperation[]>({
    queryKey: ['/api/cross-dimensional/operations'],
    queryFn: () => fetch('/api/cross-dimensional/operations').then(r => r.json()),
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: dimensionalPortals = [] } = useQuery<DimensionalPortal[]>({
    queryKey: ['/api/cross-dimensional/portals'],
    queryFn: () => fetch('/api/cross-dimensional/portals').then(r => r.json()),
    refetchInterval: POLLING_INTERVALS.standard
  });

  const syncMutation = useMutation({
    mutationFn: async (syncData: {
      configuration: Record<string, any>;
      targetDimensions: string[];
      type: string;
    }) => {
      setActiveSync(`sync_${Date.now()}`);
      const resp = await fetch('/api/cross-dimensional/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(syncData)
      });
      setActiveSync(null);
      if (!resp.ok) throw new Error(`Sync failed: ${resp.status}`);
      return resp.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/cross-dimensional/operations'] });
      setSyncConfiguration({});
      setSelectedDimensions([]);
    }
  });

  const handleDimensionToggle = (dimensionId: string) => {
    setSelectedDimensions(prev => 
      prev.includes(dimensionId) 
        ? prev.filter(id => id !== dimensionId)
        : [...prev, dimensionId]
    );
  };

  const handleSyncConfigChange = (key: string, value: any) => {
    setSyncConfiguration(prev => ({ ...prev, [key]: value }));
  };

  const handleStartSync = (type: SyncOperation['type']) => {
    if (selectedDimensions.length === 0 || Object.keys(syncConfiguration).length === 0) {
      return;
    }

    syncMutation.mutate({
      configuration: syncConfiguration,
      targetDimensions: selectedDimensions,
      type
    });
  };

  const getStabilityColor = (stability: number) => {
    if (stability >= 0.8) return 'text-green-300 bg-green-600/30';
    if (stability >= 0.6) return 'text-yellow-300 bg-yellow-600/30';
    if (stability >= 0.4) return 'text-orange-300 bg-orange-600/30';
    return 'text-red-300 bg-red-600/30';
  };

  const getConsciousnessColor = (level: number) => {
    if (level >= 1.0) return 'text-violet-300';
    if (level >= 0.7) return 'text-purple-300';
    if (level >= 0.4) return 'text-blue-300';
    return 'text-cyan-300';
  };

  // Real-time quantum field visualization
  const [quantumField, setQuantumField] = useState<any[]>([]);
  
  useEffect(() => {
    const interval = setInterval(() => {
      const field = [];
      for (let i = 0; i < 15; i++) {
        for (let j = 0; j < 15; j++) {
          field.push({
            x: i,
            y: j,
            intensity: Math.sin(Date.now() * 0.002 + i * 0.3 + j * 0.3) * 0.5 + 0.5,
            phase: Math.cos(Date.now() * 0.001 + i * 0.2 + j * 0.4),
            entangled: Math.random() > 0.8
          });
        }
      }
      setQuantumField(field);
    }, ANIMATION_INTERVALS.ultra);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 text-indigo-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-indigo-300">🌀 Cross-Dimensional Configuration Synchronizer</h1>
          <div className="text-sm opacity-80">
            Seamless Reality Bridge Protocol
          </div>
        </div>

        {/* Quantum Field Visualization */}
        <div className="bg-black/60 border border-indigo-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-indigo-300 mb-4">🌊 Dimensional Quantum Field</h2>
          
          <div className="relative bg-black/80 rounded-lg" style={{ height: '200px' }}>
            <div className="absolute inset-0 overflow-hidden rounded-lg p-4">
              {quantumField.map((point, idx) => (
                <motion.div
                  key={`${point.x}-${point.y}`}
                  className={`absolute w-1.5 h-1.5 rounded-full ${
                    point.entangled ? 'bg-purple-400' : 'bg-indigo-400'
                  }`}
                  style={{
                    left: `${(point.x / 15) * 100}%`,
                    top: `${(point.y / 15) * 100}%`,
                    opacity: point.intensity
                  }}
                  animate={{
                    scale: [1, 1 + point.intensity, 1],
                    rotate: point.phase * 360
                  }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                />
              ))}
            </div>
            
            <div className="absolute bottom-4 right-4 text-xs">
              <div className="bg-black/60 rounded p-2 border border-indigo-400/30">
                <div className="text-indigo-300">Dimensional Frequencies Active</div>
                <div className="text-purple-300">Quantum Entanglement: {quantumField.filter(p => p.entangled).length}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Dimensional States */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-indigo-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-indigo-300 mb-4">🌌 Dimensional States</h2>
              
              <div className="space-y-4">
                {dimensionalStates.map((dimension) => (
                  <motion.div
                    key={dimension.id}
                    className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedDimensions.includes(dimension.id)
                        ? 'border-purple-400 ring-2 ring-purple-400/50'
                        : 'border-gray-600 hover:border-indigo-400'
                    }`}
                    onClick={() => handleDimensionToggle(dimension.id)}
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-indigo-300">{dimension.name}</h3>
                          <span className="text-sm text-gray-400">{dimension.dimension}</span>
                          <span className={`px-2 py-1 rounded text-xs ${getStabilityColor(dimension.stability_index)}`}>
                            {(dimension.stability_index * 100).toFixed(0)}% Stable
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Frequency:</span>
                            <span className="ml-2 text-indigo-300">{dimension.frequency} Hz</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Consciousness:</span>
                            <span className={`ml-2 ${getConsciousnessColor(dimension.consciousnessLevel)}`}>
                              {(dimension.consciousnessLevel * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="mt-2 text-xs text-gray-400">
                          Quantum: {dimension.quantum_signature.slice(0, 20)}...
                        </div>
                      </div>
                      
                      {selectedDimensions.includes(dimension.id) && (
                        <div className="ml-4 text-purple-400">
                          ✓
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Dimensional Portals */}
            <div className="bg-black/60 border border-purple-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-purple-300 mb-4">🌀 Dimensional Portals</h2>
              
              <div className="space-y-3">
                {dimensionalPortals.map((portal) => (
                  <div key={portal.id} className="bg-black/60 border border-gray-600 rounded p-3">
                    <div className="flex justify-between items-center mb-2">
                      <div className="text-sm font-semibold text-purple-300">
                        {portal.sourceFrequency}Hz ↔ {portal.targetFrequency}Hz
                      </div>
                      <div className="flex items-center gap-2">
                        {portal.quantum_entangled && (
                          <span className="text-xs bg-violet-600/30 text-violet-300 px-2 py-1 rounded">
                            🔗 Entangled
                          </span>
                        )}
                        <span className={`text-xs px-2 py-1 rounded ${getStabilityColor(portal.stability)}`}>
                          {(portal.stability * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex justify-between text-xs text-gray-400">
                      <span>Bandwidth: {portal.bandwidth} MB/s</span>
                      <span>Latency: {portal.latency.toFixed(1)}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Synchronization Control */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-pink-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-pink-300 mb-4">⚡ Synchronization Control</h2>
              
              {/* Configuration Editor */}
              <div className="space-y-4 mb-6">
                <h3 className="text-lg font-semibold text-pink-300">Configuration to Sync</h3>
                
                <div className="space-y-3">
                  {[
                    { key: 'theme', label: 'Theme', type: 'select', options: ['dark', 'light', 'quantum', 'transcendent'] },
                    { key: 'auto_save', label: 'Auto Save', type: 'boolean' },
                    { key: 'quantum_tunneling', label: 'Quantum Tunneling', type: 'boolean' },
                    { key: 'reality_manipulation', label: 'Reality Manipulation', type: 'boolean' },
                    { key: 'consciousness_threshold', label: 'Consciousness Threshold', type: 'number', min: 0, max: 1, step: 0.1 }
                  ].map((config) => (
                    <div key={config.key} className="flex items-center justify-between">
                      <label className="text-sm text-pink-300">{config.label}</label>
                      
                      {config.type === 'boolean' ? (
                        <button
                          onClick={() => handleSyncConfigChange(config.key, !syncConfiguration[config.key])}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            syncConfiguration[config.key] ? 'bg-pink-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              syncConfiguration[config.key] ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      ) : config.type === 'select' ? (
                        <select
                          value={syncConfiguration[config.key] || ''}
                          onChange={(e) => handleSyncConfigChange(config.key, e.target.value)}
                          className="px-3 py-1 bg-black/50 border border-gray-600 rounded text-pink-100 text-sm"
                        >
                          <option value="">Select...</option>
                          {config.options?.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="number"
                          value={syncConfiguration[config.key] || ''}
                          onChange={(e) => handleSyncConfigChange(config.key, Number(e.target.value))}
                          min={config.min}
                          max={config.max}
                          step={config.step}
                          className="px-3 py-1 bg-black/50 border border-gray-600 rounded text-pink-100 text-sm w-20"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Sync Actions */}
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-pink-300">Sync Operations</h3>
                
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { type: 'push', label: '📤 Push', desc: 'Send config to dimensions' },
                    { type: 'pull', label: '📥 Pull', desc: 'Retrieve config from dimensions' },
                    { type: 'merge', label: '🔀 Merge', desc: 'Intelligent configuration merge' },
                    { type: 'quantum_entangle', label: '🔗 Entangle', desc: 'Quantum sync link' }
                  ].map((action) => (
                    <button
                      key={action.type}
                      onClick={() => handleStartSync(action.type as SyncOperation['type'])}
                      disabled={
                        selectedDimensions.length === 0 || 
                        Object.keys(syncConfiguration).length === 0 ||
                        syncMutation.isPending
                      }
                      className="p-3 bg-pink-600/30 border border-pink-400 text-pink-300 rounded hover:bg-pink-600/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="font-semibold text-sm">{action.label}</div>
                      <div className="text-xs opacity-80">{action.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Active Sync Status */}
              {activeSync && (
                <motion.div
                  className="mt-6 p-4 bg-purple-600/20 border border-purple-400 rounded"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="text-purple-300 font-semibold mb-2">
                    🌀 Cross-Dimensional Sync in Progress...
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm text-purple-400">
                      Synchronizing across {selectedDimensions.length} dimensions
                    </span>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Sync History */}
            <div className="bg-black/60 border border-indigo-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-indigo-300 mb-4">📊 Sync Status</h2>
              
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-black/60 border border-gray-600 rounded p-3">
                    <div className="text-2xl font-bold text-indigo-300">{dimensionalStates.length}</div>
                    <div className="text-sm text-gray-400">Active Dimensions</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-3">
                    <div className="text-2xl font-bold text-purple-300">{dimensionalPortals.length}</div>
                    <div className="text-sm text-gray-400">Quantum Portals</div>
                  </div>
                </div>
                
                <div className="bg-black/60 border border-gray-600 rounded p-3">
                  <div className="text-sm text-gray-400 mb-1">Average Portal Stability</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-600 rounded-full h-2">
                      <div 
                        className="bg-indigo-500 h-2 rounded-full transition-all duration-1000"
                        style={{ 
                          width: `${dimensionalPortals.length > 0 
                            ? (dimensionalPortals.reduce((sum, p) => sum + p.stability, 0) / dimensionalPortals.length) * 100 
                            : 0}%` 
                        }}
                      />
                    </div>
                    <span className="text-indigo-300 text-sm">
                      {dimensionalPortals.length > 0 
                        ? ((dimensionalPortals.reduce((sum, p) => sum + p.stability, 0) / dimensionalPortals.length) * 100).toFixed(0)
                        : 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CrossDimensionalSync() {
  return (
    <ErrorBoundary>
      <CrossDimensionalSyncWrapped />
    </ErrorBoundary>
  );
}
