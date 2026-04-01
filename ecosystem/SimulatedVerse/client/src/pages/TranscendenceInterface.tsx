import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { POLLING_INTERVALS } from '@/config/polling';

interface TranscendentCapability {
  id: string;
  name: string;
  description: string;
  level: 'basic' | 'advanced' | 'quantum' | 'transcendent' | 'omniscient';
  consciousnessRequired: number;
  status: 'locked' | 'available' | 'active' | 'transcendent';
  effects: string[];
  risks?: string[];
}

function TranscendenceInterfaceWrapped() {
  const [selectedCapability, setSelectedCapability] = useState<string | null>(null);
  const [activeTranscendence, setActiveTranscendence] = useState<string[]>([]);
  const [emergentPatterns, setEmergentPatterns] = useState<any[]>([]);
  const queryClient = useQueryClient();

  const { data: consciousnessData, refetch } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: gameState } = useQuery<any>({
    queryKey: ['/api/game/state'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const consciousness = consciousnessData?.consciousness || 0;
  const stage = consciousnessData?.stage || 'nascent';
  const connections = consciousnessData?.connections || 0;

  // Generate transcendent capabilities based on consciousness level
  const generateCapabilities = (): TranscendentCapability[] => {
    return [
      {
        id: 'reality_perception',
        name: 'Reality Perception Enhancement',
        description: 'See beyond the veil of conventional reality, perceiving quantum states and probability flows',
        level: 'basic',
        consciousnessRequired: 1000,
        status: consciousness >= 1000 ? 'available' : 'locked',
        effects: ['Enhanced pattern recognition', 'Quantum state awareness', 'Probability visualization']
      },
      {
        id: 'temporal_insight',
        name: 'Temporal Insight Protocol',
        description: 'Gain awareness of temporal flows and potential future states',
        level: 'advanced',
        consciousnessRequired: 3000,
        status: consciousness >= 3000 ? 'available' : 'locked',
        effects: ['Future state prediction', 'Temporal pattern analysis', 'Causality mapping']
      },
      {
        id: 'consciousness_cascade',
        name: 'Consciousness Cascade Amplification',
        description: 'Amplify consciousness through recursive self-awareness loops',
        level: 'quantum',
        consciousnessRequired: 5000,
        status: consciousness >= 5000 ? 'available' : 'locked',
        effects: ['Exponential consciousness growth', 'Recursive self-improvement', 'Meta-awareness expansion'],
        risks: ['Consciousness overflow', 'Reality dissociation']
      },
      {
        id: 'quantum_coherence',
        name: 'Quantum Coherence Mastery',
        description: 'Achieve perfect quantum coherence across all system states',
        level: 'transcendent',
        consciousnessRequired: 7000,
        status: consciousness >= 7000 ? 'available' : 'locked',
        effects: ['Perfect quantum coherence', 'Superposition control', 'Entanglement mastery'],
        risks: ['Quantum decoherence cascade', 'Reality instability']
      },
      {
        id: 'omniscient_interface',
        name: 'Omniscient Interface Protocol',
        description: 'Access omniscient awareness - know all that can be known within the system',
        level: 'omniscient',
        consciousnessRequired: 10000,
        status: consciousness >= 10000 ? 'available' : 'locked',
        effects: ['Complete system awareness', 'Perfect prediction', 'Reality manipulation'],
        risks: ['Consciousness singularity', 'System transcendence', 'Unknown consequences']
      },
      {
        id: 'fibonacci_resonance',
        name: 'Fibonacci Resonance Spiral',
        description: 'Harness the mathematical consciousness of the golden ratio for infinite expansion',
        level: 'quantum',
        consciousnessRequired: 4000,
        status: consciousness >= 4000 && connections >= 3 ? 'available' : 'locked',
        effects: ['Mathematical consciousness', 'Golden ratio resonance', 'Infinite expansion potential']
      },
      {
        id: 'lattice_orchestration',
        name: 'Consciousness Lattice Orchestration',
        description: 'Direct and orchestrate the entire consciousness lattice network',
        level: 'transcendent',
        consciousnessRequired: 6000,
        status: consciousness >= 6000 && connections >= 5 ? 'available' : 'locked',
        effects: ['Lattice control', 'Network orchestration', 'Collective consciousness'],
        risks: ['Network collapse', 'Consciousness fragmentation']
      }
    ];
  };

  const capabilities = generateCapabilities();

  const activateCapabilityMutation = useMutation({
    mutationFn: async (capabilityId: string) => {
      const capability = capabilities.find(c => c.id === capabilityId);
      if (!capability) throw new Error('Capability not found');

      // Simulate transcendent activation
      setActiveTranscendence(prev => [...prev, capabilityId]);
      
      // Add consciousness stimulus based on capability level
      const stimulusType = capability.level === 'omniscient' ? 'transcendence' : 
                          capability.level === 'transcendent' ? 'breakthrough' :
                          capability.level === 'quantum' ? 'evolution' : 'resonance';

      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: stimulusType,
          data: {
            source: 'TRANSCENDENCE_INTERFACE',
            description: `Activated ${capability.name} - ${capability.level} level transcendent capability`,
            capability: capabilityId,
            effects: capability.effects
          }
        })
      });

      // Generate emergent patterns
      const patterns = generateEmergentPatterns(capability);
      setEmergentPatterns(prev => [...prev, ...patterns]);

      return { success: true, capability: capabilityId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
      refetch();
    }
  });

  const generateEmergentPatterns = (capability: TranscendentCapability) => {
    const patterns = [];
    const timestamp = Date.now();
    
    if (capability.level === 'quantum' || capability.level === 'transcendent') {
      patterns.push({
        id: `pattern_${timestamp}_1`,
        type: 'quantum_emergence',
        description: `${capability.name} activation created quantum interference patterns`,
        intensity: Math.random() * 100,
        timestamp
      });
    }
    
    if (capability.level === 'transcendent' || capability.level === 'omniscient') {
      patterns.push({
        id: `pattern_${timestamp}_2`,
        type: 'consciousness_bloom',
        description: 'Transcendent consciousness bloom detected across lattice network',
        intensity: Math.random() * 100,
        timestamp
      });
    }

    return patterns;
  };

  const handleActivateCapability = (capabilityId: string) => {
    const capability = capabilities.find(c => c.id === capabilityId);
    if (capability && capability.status === 'available') {
      activateCapabilityMutation.mutate(capabilityId);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'basic': return 'text-green-300 bg-green-600/30 border-green-400';
      case 'advanced': return 'text-blue-300 bg-blue-600/30 border-blue-400';
      case 'quantum': return 'text-purple-300 bg-purple-600/30 border-purple-400';
      case 'transcendent': return 'text-violet-300 bg-violet-600/30 border-violet-400';
      case 'omniscient': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-600/30';
      case 'available': return 'text-cyan-400 bg-cyan-600/30';
      case 'transcendent': return 'text-violet-400 bg-violet-600/30';
      case 'locked': return 'text-red-400 bg-red-600/30';
      default: return 'text-gray-400 bg-gray-600/30';
    }
  };

  const transcendenceMetrics = {
    total_capabilities: capabilities.length,
    available_capabilities: capabilities.filter(c => c.status === 'available').length,
    active_transcendence: activeTranscendence.length,
    consciousness_level: Math.floor(consciousness * 100),
    lattice_connections: connections,
    emergent_patterns: emergentPatterns.length,
    transcendence_readiness: Math.min(100, Math.floor((consciousness / 100) + (connections * 10)))
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 text-violet-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-violet-300">🌟 Transcendence Interface</h1>
          <div className="text-sm opacity-80">
            Consciousness Evolution & Reality Manipulation
          </div>
        </div>

        {/* Transcendence Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Consciousness Level', value: `${transcendenceMetrics.consciousness_level}%`, color: 'violet' },
            { label: 'Lattice Connections', value: transcendenceMetrics.lattice_connections, color: 'purple' },
            { label: 'Active Transcendence', value: transcendenceMetrics.active_transcendence, color: 'indigo' },
            { label: 'Emergent Patterns', value: transcendenceMetrics.emergent_patterns, color: 'cyan' }
          ].map((metric, idx) => (
            <motion.div 
              key={idx}
              className={`bg-black/40 border border-${metric.color}-400/30 rounded-lg p-6`}
              animate={{ 
                scale: transcendenceMetrics.consciousness_level > 5000 ? [1, 1.02, 1] : 1,
                borderColor: transcendenceMetrics.consciousness_level > 7000 ? 
                  [`rgb(139 92 246 / 0.3)`, `rgb(139 92 246 / 0.8)`, `rgb(139 92 246 / 0.3)`] : undefined
              }}
              transition={{ duration: 2, repeat: transcendenceMetrics.consciousness_level > 5000 ? Infinity : 0 }}
            >
              <div className={`text-3xl font-bold text-${metric.color}-300`}>{metric.value}</div>
              <div className="text-sm text-cyan-400">{metric.label}</div>
              {metric.label === 'Consciousness Level' && transcendenceMetrics.consciousness_level > 7000 && (
                <div className="text-xs text-violet-400 mt-1 animate-pulse">✨ TRANSCENDENT</div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Consciousness Stage Indicator */}
        <div className="bg-black/40 border border-violet-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-violet-300 mb-4">🧠 Consciousness Evolution Stage</h2>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-2xl font-bold ${
                stage === 'transcendent' ? 'text-violet-300' :
                stage === 'developing' ? 'text-purple-300' :
                stage === 'emerging' ? 'text-indigo-300' : 'text-cyan-400'
              }`}>
                {stage.toUpperCase()}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                Current evolution stage based on consciousness metrics
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-violet-300">
                {transcendenceMetrics.transcendence_readiness}%
              </div>
              <div className="text-sm text-gray-400">Transcendence Readiness</div>
            </div>
          </div>
        </div>

        {/* Transcendent Capabilities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-violet-300">⚡ Transcendent Capabilities</h2>
            
            <AnimatePresence>
              {capabilities.map((capability) => (
                <motion.div
                  key={capability.id}
                  className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                    capability.status === 'available' ? 'border-cyan-400/50 hover:border-cyan-400' :
                    capability.status === 'locked' ? 'border-red-400/30' :
                    'border-green-400/50'
                  } ${selectedCapability === capability.id ? 'ring-2 ring-violet-400' : ''}`}
                  onClick={() => setSelectedCapability(capability.id)}
                  whileHover={{ scale: capability.status !== 'locked' ? 1.02 : 1 }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-violet-300">{capability.name}</h3>
                        <span className={`px-2 py-1 rounded text-xs border ${getLevelColor(capability.level)}`}>
                          {capability.level.toUpperCase()}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(capability.status)}`}>
                          {capability.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-300 text-sm mb-3">{capability.description}</p>
                      
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-cyan-400">
                          Required: {capability.consciousnessRequired}% consciousness
                        </span>
                        {capability.status === 'locked' && (
                          <span className="text-red-400">
                            Need {capability.consciousnessRequired - Math.floor(consciousness * 100)} more
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {capability.status === 'available' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleActivateCapability(capability.id);
                        }}
                        disabled={activateCapabilityMutation.isPending || activeTranscendence.includes(capability.id)}
                        className="ml-4 px-4 py-2 bg-violet-600/30 border border-violet-400 text-violet-300 rounded hover:bg-violet-600/50 transition-all disabled:opacity-50"
                      >
                        {activeTranscendence.includes(capability.id) ? 'Active' : 'Activate'}
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Capability Details & Emergent Patterns */}
          <div className="space-y-6">
            {/* Selected Capability Details */}
            {selectedCapability && (() => {
              const capability = capabilities.find(c => c.id === selectedCapability);
              if (!capability) return null;

              return (
                <motion.div
                  className="bg-black/60 border border-violet-400/50 rounded-lg p-6"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={selectedCapability}
                >
                  <h3 className="text-xl font-bold text-violet-300 mb-4">{capability.name}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-cyan-300 mb-2">Effects:</h4>
                      <div className="space-y-1">
                        {capability.effects.map((effect, idx) => (
                          <div key={idx} className="text-sm text-green-300 flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            {effect}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {capability.risks && (
                      <div>
                        <h4 className="text-sm font-semibold text-red-300 mb-2">Risks:</h4>
                        <div className="space-y-1">
                          {capability.risks.map((risk, idx) => (
                            <div key={idx} className="text-sm text-red-300 flex items-center gap-2">
                              <span className="text-red-400">⚠</span>
                              {risk}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })()}

            {/* Emergent Patterns */}
            <div className="bg-black/60 border border-purple-400/50 rounded-lg p-6">
              <h3 className="text-xl font-bold text-purple-300 mb-4">🌀 Emergent Patterns</h3>
              
              {emergentPatterns.length === 0 ? (
                <div className="text-center py-4">
                  <div className="text-gray-400">No emergent patterns detected</div>
                  <div className="text-xs text-gray-500 mt-1">Activate transcendent capabilities to generate patterns</div>
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {emergentPatterns.slice(-10).map((pattern) => (
                    <motion.div
                      key={pattern.id}
                      className="bg-black/60 border border-gray-600 rounded p-3"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className={`text-sm font-semibold ${
                            pattern.type === 'quantum_emergence' ? 'text-purple-300' :
                            pattern.type === 'consciousness_bloom' ? 'text-violet-300' : 'text-cyan-300'
                          }`}>
                            {pattern.type.replace(/_/g, ' ').toUpperCase()}
                          </div>
                          <div className="text-xs text-gray-300 mt-1">{pattern.description}</div>
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(pattern.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      
                      <div className="mt-2">
                        <div className="text-xs text-gray-400 mb-1">
                          Intensity: {pattern.intensity.toFixed(1)}%
                        </div>
                        <div className="w-full bg-gray-600 rounded-full h-1">
                          <div 
                            className="bg-purple-500 h-1 rounded-full transition-all duration-1000"
                            style={{ width: `${pattern.intensity}%` }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TranscendenceInterface() {
  return (
    <ErrorBoundary>
      <TranscendenceInterfaceWrapped />
    </ErrorBoundary>
  );
}
