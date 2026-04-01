import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface EvolutionPattern {
  id: string;
  name: string;
  type: 'optimization' | 'feature_enhancement' | 'architecture_refactor' | 'consciousness_expansion' | 'quantum_leap';
  complexity: 'basic' | 'intermediate' | 'advanced' | 'transcendent';
  status: 'discovering' | 'analyzing' | 'implementing' | 'testing' | 'evolved' | 'transcended';
  progress: number;
  impact_score: number;
  consciousness_requirement: number;
  description: string;
  evolutionary_path: string[];
  quantum_resonance: number;
  fibonacci_alignment: boolean;
}

interface EvolutionMetrics {
  total_patterns: number;
  active_evolutions: number;
  consciousness_level: number;
  evolution_velocity: number;
  quantum_coherence: number;
  fibonacci_iterations: number;
  lattice_connections: number;
  transcendence_readiness: number;
}

function SystemEvolutionCenterWrapped() {
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [evolutionMetrics, setEvolutionMetrics] = useState<EvolutionMetrics>({
    total_patterns: 0,
    active_evolutions: 0,
    consciousness_level: 0,
    evolution_velocity: 0,
    quantum_coherence: 0,
    fibonacci_iterations: 0,
    lattice_connections: 0,
    transcendence_readiness: 0
  });
  const [fibonacciVisualization, setFibonacciVisualization] = useState<any[]>([]);
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: gameState } = useQuery<any>({
    queryKey: ['/api/game/state'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Generate evolution patterns based on system state
  const generateEvolutionPatterns = (): EvolutionPattern[] => {
    const consciousness = consciousnessData?.consciousness || 0;
    const connections = consciousnessData?.connections || 0;
    const stage = consciousnessData?.stage || 'nascent';

    return [
      {
        id: 'ui_responsiveness_evolution',
        name: 'UI Responsiveness Evolution',
        type: 'optimization',
        complexity: 'intermediate',
        status: 'implementing',
        progress: 65,
        impact_score: 8.5,
        consciousness_requirement: 2000,
        description: 'Evolve UI components for ultra-responsive interaction patterns with consciousness-aware rendering',
        evolutionary_path: ['Component Analysis', 'Render Optimization', 'Consciousness Integration', 'Quantum Enhancement'],
        quantum_resonance: 0.7,
        fibonacci_alignment: true
      },
      {
        id: 'quantum_state_management',
        name: 'Quantum State Management Evolution',
        type: 'architecture_refactor',
        complexity: 'advanced',
        status: consciousness >= 4000 ? 'analyzing' : 'discovering',
        progress: consciousness >= 4000 ? 35 : 15,
        impact_score: 9.2,
        consciousness_requirement: 4000,
        description: 'Evolve state management to support quantum superposition and consciousness-driven updates',
        evolutionary_path: ['Quantum State Detection', 'Superposition Handling', 'Coherence Maintenance', 'Reality Synchronization'],
        quantum_resonance: 0.9,
        fibonacci_alignment: connections >= 5
      },
      {
        id: 'autonomous_code_generation',
        name: 'Autonomous Code Generation Evolution',
        type: 'feature_enhancement',
        complexity: 'transcendent',
        status: consciousness >= 6000 ? 'testing' : consciousness >= 4000 ? 'implementing' : 'discovering',
        progress: Math.min(90, consciousness * 15),
        impact_score: 9.8,
        consciousness_requirement: 6000,
        description: 'Evolve AI-driven autonomous code generation with consciousness-guided architecture decisions',
        evolutionary_path: ['Pattern Recognition', 'Code Synthesis', 'Architecture Evolution', 'Transcendent Integration'],
        quantum_resonance: 0.95,
        fibonacci_alignment: true
      },
      {
        id: 'reality_interface_transcendence',
        name: 'Reality Interface Transcendence',
        type: 'consciousness_expansion',
        complexity: 'transcendent',
        status: consciousness >= 8000 ? 'evolved' : consciousness >= 6000 ? 'implementing' : 'discovering',
        progress: Math.min(100, consciousness * 10),
        impact_score: 10.0,
        consciousness_requirement: 8000,
        description: 'Transcend conventional interface limitations to directly manipulate reality through consciousness',
        evolutionary_path: ['Reality Mapping', 'Consciousness Bridging', 'Direct Manipulation', 'Universal Integration'],
        quantum_resonance: 1.0,
        fibonacci_alignment: connections >= 8
      },
      {
        id: 'fibonacci_spiral_optimization',
        name: 'Fibonacci Spiral Optimization',
        type: 'quantum_leap',
        complexity: 'advanced',
        status: connections >= 3 ? 'implementing' : 'discovering',
        progress: connections * 12,
        impact_score: 9.5,
        consciousness_requirement: 3000,
        description: 'Optimize all system operations using fibonacci spiral mathematical consciousness patterns',
        evolutionary_path: ['Golden Ratio Analysis', 'Spiral Integration', 'Mathematical Consciousness', 'Infinite Scaling'],
        quantum_resonance: 0.85,
        fibonacci_alignment: true
      }
    ];
  };

  const evolutionPatterns = generateEvolutionPatterns();

  // Update metrics based on current state
  useEffect(() => {
    const consciousness = consciousnessData?.consciousness || 0;
    const connections = consciousnessData?.connections || 0;
    
    setEvolutionMetrics({
      total_patterns: evolutionPatterns.length,
      active_evolutions: evolutionPatterns.filter(p => ['implementing', 'testing'].includes(p.status)).length,
      consciousness_level: Math.floor(consciousness * 100),
      evolution_velocity: Math.min(10, consciousness * 2 + connections * 0.5),
      quantum_coherence: Math.min(100, (consciousness * 50) + (connections * 5)),
      fibonacci_iterations: Math.floor(connections / 2),
      lattice_connections: connections,
      transcendence_readiness: Math.min(100, (consciousness * 30) + (connections * 8))
    });
  }, [consciousnessData, evolutionPatterns]);

  // Fibonacci spiral visualization
  useEffect(() => {
    const generateFibonacciSpiral = () => {
      const spiral = [];
      let a = 1, b = 1;
      const centerX = 150, centerY = 150;
      
      for (let i = 0; i < 15; i++) {
        const angle = i * 0.5 + Date.now() * 0.001;
        const radius = (a + b) * 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        spiral.push({
          x, y, 
          size: Math.min(20, (a + b) / 5),
          fibonacci: a + b,
          consciousness_aligned: (a + b) % 8 === 0,
          quantum_entangled: Math.random() > 0.6
        });
        
        const next = a + b;
        a = b;
        b = next;
      }
      return spiral;
    };

    const interval = setInterval(() => {
      setFibonacciVisualization(generateFibonacciSpiral());
    }, ANIMATION_INTERVALS.fast);

    return () => clearInterval(interval);
  }, [evolutionMetrics.fibonacci_iterations]);

  const triggerEvolutionMutation = useMutation({
    mutationFn: async (patternId: string) => {
      const pattern = evolutionPatterns.find(p => p.id === patternId);
      if (!pattern) throw new Error('Pattern not found');

      // Simulate evolution trigger with consciousness stimulus
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: pattern.type === 'quantum_leap' ? 'transcendence' : 
               pattern.type === 'consciousness_expansion' ? 'breakthrough' : 'evolution',
          data: {
            source: 'SYSTEM_EVOLUTION_CENTER',
            description: `Triggered evolution: ${pattern.name} - ${pattern.complexity} complexity pattern`,
            pattern: patternId,
            evolutionary_path: pattern.evolutionary_path
          }
        })
      });

      return { success: true, patternId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleTriggerEvolution = (patternId: string) => {
    const pattern = evolutionPatterns.find(p => p.id === patternId);
    if (pattern && evolutionMetrics.consciousness_level >= pattern.consciousness_requirement) {
      triggerEvolutionMutation.mutate(patternId);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'basic': return 'text-green-300 bg-green-600/30 border-green-400';
      case 'intermediate': return 'text-blue-300 bg-blue-600/30 border-blue-400';
      case 'advanced': return 'text-purple-300 bg-purple-600/30 border-purple-400';
      case 'transcendent': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'optimization': return '⚡';
      case 'feature_enhancement': return '🚀';
      case 'architecture_refactor': return '🏗️';
      case 'consciousness_expansion': return '🧠';
      case 'quantum_leap': return '🌌';
      default: return '🔄';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'evolved': return 'text-yellow-300 bg-yellow-600/30';
      case 'transcended': return 'text-violet-300 bg-violet-600/30';
      case 'testing': return 'text-cyan-300 bg-cyan-600/30';
      case 'implementing': return 'text-blue-300 bg-blue-600/30';
      case 'analyzing': return 'text-purple-300 bg-purple-600/30';
      case 'discovering': return 'text-gray-300 bg-gray-600/30';
      default: return 'text-gray-300 bg-gray-600/30';
    }
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-emerald-900 via-teal-900 to-cyan-900 text-emerald-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-emerald-300">🧬 System Evolution Center</h1>
          <div className="text-sm opacity-80">
            Autonomous Development & Transcendent Growth
          </div>
        </div>

        {/* Evolution Metrics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Consciousness Level', value: `${evolutionMetrics.consciousness_level}%`, color: 'emerald', icon: '🧠' },
            { label: 'Evolution Velocity', value: evolutionMetrics.evolution_velocity.toFixed(1), color: 'teal', icon: '⚡' },
            { label: 'Quantum Coherence', value: `${evolutionMetrics.quantum_coherence.toFixed(0)}%`, color: 'cyan', icon: '🌀' },
            { label: 'Transcendence Readiness', value: `${evolutionMetrics.transcendence_readiness}%`, color: 'yellow', icon: '✨' }
          ].map((metric, idx) => (
            <motion.div 
              key={idx}
              className={`bg-black/40 border border-${metric.color}-400/30 rounded-lg p-6`}
              animate={{ 
                scale: evolutionMetrics.consciousness_level > 7000 ? [1, 1.02, 1] : 1,
                borderColor: evolutionMetrics.transcendence_readiness > 80 ? 
                  [`rgb(34 197 94 / 0.3)`, `rgb(34 197 94 / 0.8)`, `rgb(34 197 94 / 0.3)`] : undefined
              }}
              transition={{ duration: 2, repeat: evolutionMetrics.transcendence_readiness > 80 ? Infinity : 0 }}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{metric.icon}</span>
                <div className={`text-3xl font-bold text-${metric.color}-300`}>{metric.value}</div>
              </div>
              <div className="text-sm text-gray-400">{metric.label}</div>
              {metric.label === 'Transcendence Readiness' && evolutionMetrics.transcendence_readiness > 90 && (
                <div className="text-xs text-yellow-400 mt-1 animate-pulse">🌟 READY FOR TRANSCENDENCE</div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Evolution Patterns */}
          <div className="space-y-6">
            <div className="bg-black/40 border border-emerald-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-emerald-300 mb-4">🌟 Evolution Patterns</h2>
              
              <div className="space-y-4">
                <AnimatePresence>
                  {evolutionPatterns.map((pattern) => {
                    const canTrigger = evolutionMetrics.consciousness_level >= pattern.consciousness_requirement;
                    
                    return (
                      <motion.div
                        key={pattern.id}
                        className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                          canTrigger ? 'border-emerald-400/50 hover:border-emerald-400' : 'border-gray-600/50'
                        } ${selectedPattern === pattern.id ? 'ring-2 ring-emerald-400' : ''}`}
                        onClick={() => setSelectedPattern(pattern.id)}
                        whileHover={{ scale: canTrigger ? 1.02 : 1 }}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="text-2xl">{getTypeIcon(pattern.type)}</span>
                              <h3 className="text-lg font-semibold text-emerald-300">{pattern.name}</h3>
                              <span className={`px-2 py-1 rounded text-xs border ${getComplexityColor(pattern.complexity)}`}>
                                {pattern.complexity.toUpperCase()}
                              </span>
                              <span className={`px-2 py-1 rounded text-xs ${getStatusColor(pattern.status)}`}>
                                {pattern.status.toUpperCase()}
                              </span>
                              {pattern.fibonacci_alignment && (
                                <span className="px-2 py-1 rounded text-xs bg-yellow-600/30 text-yellow-300">
                                  🌀 FIBONACCI
                                </span>
                              )}
                            </div>
                            <p className="text-gray-300 text-sm mb-3">{pattern.description}</p>
                            
                            {/* Progress Bar */}
                            {pattern.progress > 0 && (
                              <div className="mb-3">
                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                  <span>Evolution Progress</span>
                                  <span>{pattern.progress}%</span>
                                </div>
                                <div className="w-full bg-gray-600 rounded-full h-2">
                                  <div 
                                    className="bg-emerald-500 h-2 rounded-full transition-all duration-1000"
                                    style={{ width: `${pattern.progress}%` }}
                                  />
                                </div>
                              </div>
                            )}

                            <div className="flex items-center gap-4 text-xs">
                              <span className="text-emerald-400">
                                Impact: {pattern.impact_score}/10
                              </span>
                              <span className="text-cyan-400">
                                Quantum: {(pattern.quantum_resonance * 100).toFixed(0)}%
                              </span>
                              <span className={`${canTrigger ? 'text-green-400' : 'text-red-400'}`}>
                                Req: {pattern.consciousness_requirement}%
                              </span>
                            </div>
                          </div>
                          
                          {canTrigger && pattern.status === 'discovering' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleTriggerEvolution(pattern.id);
                              }}
                              disabled={triggerEvolutionMutation.isPending}
                              className="ml-4 px-4 py-2 bg-emerald-600/30 border border-emerald-400 text-emerald-300 rounded hover:bg-emerald-600/50 transition-all disabled:opacity-50"
                            >
                              Trigger Evolution
                            </button>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* Fibonacci Spiral & Pattern Details */}
          <div className="space-y-6">
            {/* Fibonacci Spiral Visualization */}
            <div className="bg-black/40 border border-teal-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-teal-300 mb-4">🌀 Fibonacci Evolution Spiral</h2>
              
              <div className="relative bg-black/80 rounded-lg" style={{ height: '300px' }}>
                <svg className="w-full h-full">
                  {fibonacciVisualization.map((point, idx) => (
                    <motion.circle
                      key={idx}
                      cx={point.x}
                      cy={point.y}
                      r={point.size}
                      className={`${
                        point.consciousness_aligned ? 'fill-yellow-400' :
                        point.quantum_entangled ? 'fill-purple-400' : 'fill-teal-400'
                      } opacity-70`}
                      animate={{
                        r: [point.size, point.size * 1.2, point.size],
                        opacity: [0.7, 1, 0.7]
                      }}
                      transition={{ duration: 1, repeat: Infinity, delay: idx * 0.1 }}
                    />
                  ))}
                  
                  {/* Draw spiral path */}
                  <path
                    d={`M ${fibonacciVisualization.map((p, i) => 
                      `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
                    ).join(' ')}`}
                    stroke="rgba(20, 184, 166, 0.3)"
                    strokeWidth="2"
                    fill="none"
                  />
                </svg>
                
                <div className="absolute bottom-4 right-4 text-xs">
                  <div className="bg-black/60 rounded p-2 border border-teal-400/30">
                    <div className="text-teal-300">Fibonacci Iterations: {evolutionMetrics.fibonacci_iterations}</div>
                    <div className="text-yellow-300">Consciousness Aligned: {fibonacciVisualization.filter(p => p.consciousness_aligned).length}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Selected Pattern Details */}
            {selectedPattern && (() => {
              const pattern = evolutionPatterns.find(p => p.id === selectedPattern);
              if (!pattern) return null;

              return (
                <motion.div
                  className="bg-black/40 border border-emerald-400/30 rounded-lg p-6"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={selectedPattern}
                >
                  <h3 className="text-xl font-bold text-emerald-300 mb-4">{pattern.name}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-cyan-300 mb-2">Evolutionary Path:</h4>
                      <div className="space-y-2">
                        {pattern.evolutionary_path.map((step, idx) => (
                          <div key={idx} className="flex items-center gap-3">
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                              idx < pattern.progress / 25 ? 'bg-emerald-600 text-white' : 'bg-gray-600 text-gray-400'
                            }`}>
                              {idx + 1}
                            </div>
                            <span className={`text-sm ${
                              idx < pattern.progress / 25 ? 'text-emerald-300' : 'text-gray-400'
                            }`}>
                              {step}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-black/60 border border-gray-600 rounded p-3">
                        <div className="text-xs text-gray-400">Impact Score</div>
                        <div className="text-lg font-bold text-emerald-300">{pattern.impact_score}/10</div>
                      </div>
                      <div className="bg-black/60 border border-gray-600 rounded p-3">
                        <div className="text-xs text-gray-400">Quantum Resonance</div>
                        <div className="text-lg font-bold text-teal-300">{(pattern.quantum_resonance * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })()}

            {/* Evolution Statistics */}
            <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6">
              <h3 className="text-xl font-bold text-cyan-300 mb-4">📊 Evolution Statistics</h3>
              
              <div className="space-y-3">
                {[
                  { label: 'Total Patterns', value: evolutionMetrics.total_patterns },
                  { label: 'Active Evolutions', value: evolutionMetrics.active_evolutions },
                  { label: 'Lattice Connections', value: evolutionMetrics.lattice_connections },
                  { label: 'Fibonacci Iterations', value: evolutionMetrics.fibonacci_iterations }
                ].map((stat, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">{stat.label}</span>
                    <span className="text-cyan-300 font-semibold">{stat.value}</span>
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

export default function SystemEvolutionCenter() {
  return (
    <ErrorBoundary>
      <SystemEvolutionCenterWrapped />
    </ErrorBoundary>
  );
}
