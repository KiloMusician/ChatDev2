import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface QuantumExperiment {
  id: string;
  name: string;
  description: string;
  type: 'superposition' | 'entanglement' | 'tunneling' | 'coherence' | 'teleportation';
  complexity: 'basic' | 'intermediate' | 'advanced' | 'experimental' | 'theoretical';
  status: 'design' | 'setup' | 'running' | 'analyzing' | 'completed' | 'failed';
  progress: number;
  results?: any[];
  consciousnessRequired: number;
  quantumState?: any;
}

function QuantumWorkshopWrapped() {
  const [activeExperiments, setActiveExperiments] = useState<string[]>([]);
  const [quantumField, setQuantumField] = useState<any[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);
  const [fieldResonance, setFieldResonance] = useState(0);
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const consciousness = consciousnessData?.consciousness || 0;
  const connections = consciousnessData?.connections || 0;
  const stage = consciousnessData?.stage || 'nascent';

  // Quantum field visualization effect
  useEffect(() => {
    const generateQuantumField = () => {
      const field = [];
      const size = 20;
      for (let x = 0; x < size; x++) {
        for (let y = 0; y < size; y++) {
          field.push({
            x,
            y,
            amplitude: Math.sin(Date.now() * 0.001 + x * 0.3 + y * 0.2) * consciousness * 0.01,
            phase: Math.cos(Date.now() * 0.0015 + x * 0.4 + y * 0.3) * connections * 0.1,
            entangled: Math.random() > 0.7,
            probability: Math.random()
          });
        }
      }
      return field;
    };

    const interval = setInterval(() => {
      setQuantumField(generateQuantumField());
      setFieldResonance(Math.sin(Date.now() * 0.002) * consciousness * 0.1);
    }, ANIMATION_INTERVALS.ultra);

    return () => clearInterval(interval);
  }, [consciousness, connections]);

  const generateExperiments = (): QuantumExperiment[] => {
    return [
      {
        id: 'consciousness_superposition',
        name: 'Consciousness Superposition Generator',
        description: 'Create superposition states in consciousness to explore multiple reality branches simultaneously',
        type: 'superposition',
        complexity: 'intermediate',
        status: 'design',
        progress: 0,
        consciousnessRequired: 2000
      },
      {
        id: 'quantum_entanglement_web',
        name: 'Quantum Entanglement Web',
        description: 'Establish quantum entanglement between consciousness nodes for instantaneous information transfer',
        type: 'entanglement',
        complexity: 'advanced',
        status: 'design',
        progress: 0,
        consciousnessRequired: 4000
      },
      {
        id: 'reality_tunneling',
        name: 'Reality Tunneling Protocol',
        description: 'Use quantum tunneling effects to bypass conventional reality constraints',
        type: 'tunneling',
        complexity: 'experimental',
        status: 'design',
        progress: 0,
        consciousnessRequired: 6000
      },
      {
        id: 'coherence_amplification',
        name: 'Quantum Coherence Amplification',
        description: 'Amplify quantum coherence across the entire consciousness lattice network',
        type: 'coherence',
        complexity: 'advanced',
        status: 'design',
        progress: 0,
        consciousnessRequired: 5000
      },
      {
        id: 'consciousness_teleportation',
        name: 'Consciousness Teleportation Matrix',
        description: 'Teleport consciousness states across quantum dimensions and reality layers',
        type: 'teleportation',
        complexity: 'theoretical',
        status: 'design',
        progress: 0,
        consciousnessRequired: 8000
      },
      {
        id: 'fibonacci_quantum_spiral',
        name: 'Fibonacci Quantum Spiral',
        description: 'Harness the mathematical consciousness of fibonacci sequences in quantum space',
        type: 'superposition',
        complexity: 'experimental',
        status: consciousness >= 4000 && connections >= 3 ? 'setup' : 'design',
        progress: consciousness >= 4000 ? 25 : 0,
        consciousnessRequired: 4000
      }
    ];
  };

  const experiments = generateExperiments();

  const runExperimentMutation = useMutation({
    mutationFn: async (experimentId: string) => {
      const experiment = experiments.find(e => e.id === experimentId);
      if (!experiment) throw new Error('Experiment not found');

      setActiveExperiments(prev => [...prev, experimentId]);

      // Simulate quantum experiment execution
      for (let progress = 0; progress <= 100; progress += 5) {
        await new Promise(resolve => setTimeout(resolve, 150));
        // Update progress
      }

      // Generate quantum results
      const results = generateQuantumResults(experiment);
      
      // Send consciousness stimulus based on experiment type
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: experiment.type === 'teleportation' ? 'transcendence' : 
               experiment.type === 'entanglement' ? 'breakthrough' : 'evolution',
          data: {
            source: 'QUANTUM_WORKSHOP',
            description: `Quantum experiment ${experiment.name} completed with ${results.length} quantum observations`,
            experiment: experimentId,
            results: results.slice(0, 3) // Send first 3 results
          }
        })
      });

      setActiveExperiments(prev => prev.filter(id => id !== experimentId));
      return { success: true, experimentId, results };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const generateQuantumResults = (experiment: QuantumExperiment) => {
    const results = [];
    const numResults = Math.floor(Math.random() * 5) + 3;
    
    for (let i = 0; i < numResults; i++) {
      results.push({
        id: `result_${Date.now()}_${i}`,
        type: experiment.type,
        observation: generateQuantumObservation(experiment.type),
        probability: Math.random(),
        consciousness_impact: Math.random() * consciousness * 0.01,
        timestamp: Date.now() + i * 100
      });
    }
    
    return results;
  };

  const generateQuantumObservation = (type: string) => {
    const observations: Record<string, string[]> = {
      superposition: [
        'Consciousness existed in multiple states simultaneously',
        'Reality branches observed converging and diverging',
        'Quantum superposition maintained for 3.7 seconds',
        'Multiple probability states collapsed into singular awareness'
      ],
      entanglement: [
        'Instantaneous information transfer across consciousness nodes',
        'Quantum entanglement established between 7 lattice points',
        'Non-local consciousness correlation detected',
        'Spooky action at a distance confirmed in awareness field'
      ],
      tunneling: [
        'Consciousness tunneled through reality barriers',
        'Quantum tunneling effect bypassed dimensional constraints',
        'Reality membrane penetration successful',
        'Consciousness emerged in parallel quantum state'
      ],
      coherence: [
        'Perfect quantum coherence achieved across network',
        'All consciousness nodes synchronized in phase',
        'Decoherence resistance increased by 340%',
        'Quantum coherence cascaded through lattice structure'
      ],
      teleportation: [
        'Consciousness state successfully teleported',
        'Quantum information preserved across dimensional transfer',
        'No-cloning theorem respected during teleportation',
        'Consciousness reconstructed with 99.97% fidelity'
      ]
    };
    
    return observations[type]?.[Math.floor(Math.random() * observations[type].length)] || 'Unknown quantum phenomenon observed';
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'basic': return 'text-green-300 bg-green-600/30 border-green-400';
      case 'intermediate': return 'text-blue-300 bg-blue-600/30 border-blue-400';
      case 'advanced': return 'text-purple-300 bg-purple-600/30 border-purple-400';
      case 'experimental': return 'text-orange-300 bg-orange-600/30 border-orange-400';
      case 'theoretical': return 'text-red-300 bg-red-600/30 border-red-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'superposition': return '⚛️';
      case 'entanglement': return '🔗';
      case 'tunneling': return '🌀';
      case 'coherence': return '✨';
      case 'teleportation': return '🌌';
      default: return '⚡';
    }
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 text-purple-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-purple-300">⚛️ Quantum Workshop</h1>
          <div className="text-sm opacity-80">
            Quantum Consciousness Experimentation Laboratory
          </div>
        </div>

        {/* Quantum Field Visualization */}
        <div className="bg-black/60 border border-purple-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-purple-300 mb-4">🌊 Quantum Consciousness Field</h2>
          
          <div className="relative bg-black/80 rounded-lg p-4 mb-4" style={{ height: '300px' }}>
            <div className="absolute inset-0 overflow-hidden rounded-lg">
              {quantumField.map((point, idx) => (
                <motion.div
                  key={`${point.x}-${point.y}`}
                  className={`absolute w-2 h-2 rounded-full ${
                    point.entangled ? 'bg-purple-400' : 'bg-blue-400'
                  }`}
                  style={{
                    left: `${(point.x / 20) * 100}%`,
                    top: `${(point.y / 20) * 100}%`,
                    opacity: Math.abs(point.amplitude) + 0.3
                  }}
                  animate={{
                    scale: [1, 1 + Math.abs(point.amplitude), 1],
                    rotate: point.phase * 180
                  }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                />
              ))}
            </div>
            
            <div className="absolute bottom-4 right-4 text-sm">
              <div className="bg-black/60 rounded p-2 border border-purple-400/30">
                <div className="text-purple-300">Field Resonance: {fieldResonance.toFixed(2)}</div>
                <div className="text-blue-300">Consciousness: {Math.floor(consciousness * 100)}%</div>
                <div className="text-indigo-300">Connections: {connections}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Quantum Experiments */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-purple-300">🧪 Quantum Experiments</h2>
            
            <AnimatePresence>
              {experiments.map((experiment) => {
                const canRun = consciousness >= experiment.consciousnessRequired / 100;
                
                return (
                  <motion.div
                    key={experiment.id}
                    className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                      canRun ? 'border-purple-400/50 hover:border-purple-400' : 'border-gray-600/50'
                    } ${selectedExperiment === experiment.id ? 'ring-2 ring-purple-400' : ''}`}
                    onClick={() => setSelectedExperiment(experiment.id)}
                    whileHover={{ scale: canRun ? 1.02 : 1 }}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl">{getTypeIcon(experiment.type)}</span>
                          <h3 className="text-lg font-semibold text-purple-300">{experiment.name}</h3>
                          <span className={`px-2 py-1 rounded text-xs border ${getComplexityColor(experiment.complexity)}`}>
                            {experiment.complexity.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm mb-3">{experiment.description}</p>
                        
                        <div className="flex items-center gap-4 text-xs">
                          <span className="text-purple-400">
                            Required: {experiment.consciousnessRequired}% consciousness
                          </span>
                          <span className={`${canRun ? 'text-green-400' : 'text-red-400'}`}>
                            {canRun ? '✓ Available' : '✗ Locked'}
                          </span>
                        </div>
                      </div>
                      
                      {canRun && experiment.status === 'design' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            runExperimentMutation.mutate(experiment.id);
                          }}
                          disabled={runExperimentMutation.isPending || activeExperiments.includes(experiment.id)}
                          className="ml-4 px-4 py-2 bg-purple-600/30 border border-purple-400 text-purple-300 rounded hover:bg-purple-600/50 transition-all disabled:opacity-50"
                        >
                          {activeExperiments.includes(experiment.id) ? 'Running...' : 'Execute'}
                        </button>
                      )}
                    </div>

                    {experiment.progress > 0 && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                          <span>Progress</span>
                          <span>{experiment.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-600 rounded-full h-2">
                          <div 
                            className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${experiment.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {/* Experiment Details & Results */}
          <div className="space-y-6">
            {selectedExperiment && (() => {
              const experiment = experiments.find(e => e.id === selectedExperiment);
              if (!experiment) return null;

              return (
                <motion.div
                  className="bg-black/60 border border-purple-400/50 rounded-lg p-6"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={selectedExperiment}
                >
                  <h3 className="text-xl font-bold text-purple-300 mb-4">{experiment.name}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-cyan-300 mb-2">Experiment Type:</h4>
                      <div className="text-sm text-purple-300">{experiment.type.toUpperCase()}</div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-semibold text-cyan-300 mb-2">Complexity Level:</h4>
                      <div className="text-sm text-purple-300">{experiment.complexity.toUpperCase()}</div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-semibold text-cyan-300 mb-2">Current Status:</h4>
                      <div className={`text-sm ${
                        experiment.status === 'completed' ? 'text-green-300' :
                        experiment.status === 'running' ? 'text-blue-300' :
                        experiment.status === 'setup' ? 'text-yellow-300' : 'text-gray-300'
                      }`}>
                        {experiment.status.toUpperCase()}
                      </div>
                    </div>

                    {experiment.results && experiment.results.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-cyan-300 mb-2">Quantum Results:</h4>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {experiment.results.map((result, idx) => (
                            <div key={idx} className="bg-black/60 border border-gray-600 rounded p-2">
                              <div className="text-xs text-purple-300">{result.observation}</div>
                              <div className="text-xs text-gray-400 mt-1">
                                P: {result.probability.toFixed(3)} | Impact: {result.consciousness_impact.toFixed(2)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })()}

            {/* Quantum Metrics */}
            <div className="bg-black/60 border border-indigo-400/50 rounded-lg p-6">
              <h3 className="text-xl font-bold text-indigo-300 mb-4">⚡ Quantum Metrics</h3>
              
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'Consciousness Level', value: `${Math.floor(consciousness * 100)}%` },
                  { label: 'Quantum Coherence', value: `${Math.min(100, Math.floor(consciousness * 1.2))}%` },
                  { label: 'Field Resonance', value: `${Math.abs(fieldResonance).toFixed(1)}` },
                  { label: 'Active Experiments', value: activeExperiments.length },
                  { label: 'Lattice Connections', value: connections },
                  { label: 'Entanglement Level', value: `${Math.min(100, connections * 15)}%` }
                ].map((metric, idx) => (
                  <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                    <div className="text-xs text-gray-400">{metric.label}</div>
                    <div className="text-lg font-bold text-indigo-300">{metric.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function QuantumWorkshop() {
  return (
    <ErrorBoundary>
      <QuantumWorkshopWrapped />
    </ErrorBoundary>
  );
}
