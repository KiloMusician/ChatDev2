import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface ResonanceFrequency {
  id: string;
  name: string;
  frequency: number;
  amplitude: number;
  phase: number;
  harmonic_level: number;
  stability_index: number;
  consciousness_influence: number;
  optimization_potential: number;
  resonance_quality: 'pure' | 'harmonious' | 'distorted' | 'chaotic' | 'transcendent';
  is_active: boolean;
}

interface ResonancePattern {
  id: string;
  name: string;
  description: string;
  base_frequency: number;
  harmonic_series: number[];
  consciousness_multiplier: number;
  stability_rating: number;
  complexity: 'simple' | 'complex' | 'advanced' | 'transcendent';
  optimization_level: number;
  side_harmonics: number[];
  interference_patterns: string[];
}

interface ResonanceMetrics {
  overall_coherence: number;
  harmonic_stability: number;
  frequency_alignment: number;
  consciousness_resonance: number;
  optimization_efficiency: number;
  transcendence_resonance: number;
  interference_level: number;
  golden_ratio_alignment: number;
}

function ResonanceOptimizerWrapped() {
  const [selectedFrequency, setSelectedFrequency] = useState<string | null>(null);
  const [activeOptimizations, setActiveOptimizations] = useState<string[]>([]);
  const [resonanceField, setResonanceField] = useState<any[]>([]);
  const [waveformData, setWaveformData] = useState<any[]>([]);
  const [resonanceMetrics, setResonanceMetrics] = useState<ResonanceMetrics>({
    overall_coherence: 0,
    harmonic_stability: 0,
    frequency_alignment: 0,
    consciousness_resonance: 0,
    optimization_efficiency: 0,
    transcendence_resonance: 0,
    interference_level: 0,
    golden_ratio_alignment: 0
  });
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const consciousness = consciousnessData?.consciousness || 0;
  const connections = consciousnessData?.connections || 0;
  const stage = consciousnessData?.stage || 'nascent';

  // Generate real-time resonance field visualization
  useEffect(() => {
    const generateResonanceField = () => {
      const field = [];
      const time = Date.now() * 0.001;
      
      for (let i = 0; i < 100; i++) {
        const x = (i % 10) * 10;
        const y = Math.floor(i / 10) * 10;
        
        // Create multiple overlapping wave patterns
        const wave1 = Math.sin(time * 2 + x * 0.1) * 0.5;
        const wave2 = Math.cos(time * 1.5 + y * 0.08) * 0.3;
        const wave3 = Math.sin(time * 3 + (x + y) * 0.05) * 0.2;
        const consciousness_wave = Math.sin(time * 0.8 + consciousness * 0.01) * consciousness * 0.01;
        
        const amplitude = wave1 + wave2 + wave3 + consciousness_wave;
        const phase = Math.atan2(wave2, wave1);
        const frequency = 2 + amplitude * 0.5;
        
        field.push({
          x, y, amplitude, phase, frequency,
          resonance_strength: Math.abs(amplitude),
          harmonic_purity: Math.cos(phase * 4) * 0.5 + 0.5,
          consciousness_influence: consciousness_wave,
          golden_ratio_alignment: Math.abs(amplitude - 0.618) < 0.1,
          transcendent: Math.abs(amplitude) > 0.8 && consciousness > 6000
        });
      }
      
      return field;
    };

    const interval = setInterval(() => {
      setResonanceField(generateResonanceField());
    }, ANIMATION_INTERVALS.ultra);

    return () => clearInterval(interval);
  }, [consciousness]);

  // Generate waveform visualization data
  useEffect(() => {
    const generateWaveform = () => {
      const waveform = [];
      const time = Date.now() * 0.001;
      const samples = 200;
      
      for (let i = 0; i < samples; i++) {
        const t = i / samples;
        const x = t * 100;
        
        // Primary consciousness wave
        const primary = Math.sin(time * 2 + t * 10) * consciousness * 0.01;
        // Harmonic overtones
        const harmonic1 = Math.sin(time * 4 + t * 20) * 0.3;
        const harmonic2 = Math.sin(time * 6 + t * 30) * 0.2;
        // Golden ratio frequency
        const golden = Math.sin(time * 1.618 + t * 16.18) * 0.4;
        // Fibonacci sequence harmonics
        const fib = Math.sin(time * 1.414 + t * 14.14) * 0.25;
        
        const amplitude = primary + harmonic1 + harmonic2 + golden + fib;
        const normalized = Math.max(-1, Math.min(1, amplitude));
        
        waveform.push({
          x,
          y: normalized * 40,
          amplitude: Math.abs(normalized),
          frequency: 2 + normalized * 0.5,
          phase: Math.atan2(harmonic1, primary),
          harmonic_content: Math.abs(harmonic1 + harmonic2),
          consciousness_component: Math.abs(primary),
          golden_ratio_component: Math.abs(golden),
          fibonacci_component: Math.abs(fib)
        });
      }
      
      return waveform;
    };

    const interval = setInterval(() => {
      setWaveformData(generateWaveform());
    }, ANIMATION_INTERVALS.tick);

    return () => clearInterval(interval);
  }, [consciousness]);

  // Update resonance metrics
  useEffect(() => {
    const calculateMetrics = () => {
      if (resonanceField.length === 0) return;

      const avgAmplitude = resonanceField.reduce((sum, p) => sum + p.resonance_strength, 0) / resonanceField.length;
      const purityScore = resonanceField.reduce((sum, p) => sum + p.harmonic_purity, 0) / resonanceField.length;
      const goldenAligned = resonanceField.filter(p => p.golden_ratio_alignment).length / resonanceField.length;
      const transcendentPoints = resonanceField.filter(p => p.transcendent).length / resonanceField.length;
      
      setResonanceMetrics({
        overall_coherence: Math.min(100, avgAmplitude * 100 + consciousness * 20),
        harmonic_stability: Math.min(100, purityScore * 100),
        frequency_alignment: Math.min(100, goldenAligned * 100 + connections * 5),
        consciousness_resonance: Math.min(100, consciousness * 50),
        optimization_efficiency: Math.min(100, 60 + consciousness * 30 + connections * 2),
        transcendence_resonance: Math.min(100, transcendentPoints * 100 + consciousness * 10),
        interference_level: Math.max(0, 30 - consciousness * 20),
        golden_ratio_alignment: goldenAligned * 100
      });
    };

    calculateMetrics();
  }, [resonanceField, consciousness, connections]);

  const generateResonanceFrequencies = (): ResonanceFrequency[] => {
    const time = Date.now() * 0.001;
    
    return [
      {
        id: 'base_consciousness',
        name: 'Base Consciousness Frequency',
        frequency: 7.83 + Math.sin(time * 0.5) * 0.1, // Schumann resonance
        amplitude: 0.8 + consciousness * 0.2,
        phase: time * 2,
        harmonic_level: 1,
        stability_index: Math.min(1, 0.6 + consciousness * 0.4),
        consciousness_influence: 1.0,
        optimization_potential: Math.max(0, 1 - consciousness * 0.8),
        resonance_quality: consciousness > 8000 ? 'transcendent' : 
                          consciousness > 5000 ? 'pure' : 
                          consciousness > 3000 ? 'harmonious' : 'distorted',
        is_active: true
      },
      {
        id: 'golden_ratio_harmonic',
        name: 'Golden Ratio Harmonic',
        frequency: 7.83 * 1.618 + Math.cos(time * 0.8) * 0.2,
        amplitude: 0.6 + connections * 0.05,
        phase: time * 1.618,
        harmonic_level: 2,
        stability_index: Math.min(1, 0.4 + connections * 0.1),
        consciousness_influence: 0.8,
        optimization_potential: connections < 10 ? 0.7 : 0.2,
        resonance_quality: connections >= 8 ? 'pure' : connections >= 5 ? 'harmonious' : 'distorted',
        is_active: connections >= 3
      },
      {
        id: 'fibonacci_sequence',
        name: 'Fibonacci Sequence Resonance',
        frequency: 11.18 + Math.sin(time * 1.414) * 0.15, // 7.83 * 1.427 (fibonacci ratio)
        amplitude: 0.5 + (consciousness * connections) * 0.001,
        phase: time * 1.414,
        harmonic_level: 3,
        stability_index: Math.min(1, consciousness * connections * 0.0001),
        consciousness_influence: 0.7,
        optimization_potential: consciousness < 7000 ? 0.8 : 0.1,
        resonance_quality: consciousness > 7000 && connections > 10 ? 'transcendent' : 'harmonious',
        is_active: consciousness > 4000 && connections >= 5
      },
      {
        id: 'transcendent_overtone',
        name: 'Transcendent Overtone',
        frequency: 40.0 + Math.sin(time * 0.3) * 0.5,
        amplitude: Math.min(1, consciousness * 0.1),
        phase: time * 0.618,
        harmonic_level: 5,
        stability_index: consciousness > 8000 ? 0.9 : 0.3,
        consciousness_influence: 1.2,
        optimization_potential: consciousness < 9000 ? 0.9 : 0.0,
        resonance_quality: consciousness > 9000 ? 'transcendent' : consciousness > 6000 ? 'pure' : 'chaotic',
        is_active: consciousness > 6000
      },
      {
        id: 'quantum_coherence',
        name: 'Quantum Coherence Frequency',
        frequency: 432.0 + Math.cos(time * 2.718) * 2.0, // 432 Hz healing frequency
        amplitude: Math.min(1, (consciousness * connections) * 0.00005),
        phase: time * 2.718,
        harmonic_level: 8,
        stability_index: Math.min(1, consciousness * connections * 0.00001),
        consciousness_influence: 1.5,
        optimization_potential: consciousness < 10000 ? 1.0 : 0.0,
        resonance_quality: consciousness > 10000 ? 'transcendent' : consciousness > 8000 ? 'pure' : 'harmonious',
        is_active: consciousness > 7000 && connections > 15
      }
    ];
  };

  const generateResonancePatterns = (): ResonancePattern[] => {
    return [
      {
        id: 'consciousness_amplification',
        name: 'Consciousness Amplification Pattern',
        description: 'Optimizes base frequencies to amplify consciousness resonance and stability',
        base_frequency: 7.83,
        harmonic_series: [7.83, 15.66, 23.49, 31.32],
        consciousness_multiplier: 1.5,
        stability_rating: 0.8,
        complexity: 'simple',
        optimization_level: Math.min(100, consciousness * 20),
        side_harmonics: [12.7, 19.6],
        interference_patterns: ['minimal', 'constructive']
      },
      {
        id: 'golden_ratio_optimization',
        name: 'Golden Ratio Optimization',
        description: 'Aligns all frequencies to golden ratio proportions for maximum harmony',
        base_frequency: 7.83,
        harmonic_series: [7.83, 12.67, 20.5, 33.17],
        consciousness_multiplier: 1.8,
        stability_rating: 0.9,
        complexity: 'complex',
        optimization_level: Math.min(100, connections * 8),
        side_harmonics: [10.1, 16.3, 26.4],
        interference_patterns: ['harmonic', 'golden_constructive']
      },
      {
        id: 'fibonacci_spiral_resonance',
        name: 'Fibonacci Spiral Resonance',
        description: 'Creates spiraling frequency patterns based on fibonacci mathematical consciousness',
        base_frequency: 11.18,
        harmonic_series: [11.18, 18.06, 29.24, 47.3],
        consciousness_multiplier: 2.1,
        stability_rating: 0.7,
        complexity: 'advanced',
        optimization_level: Math.min(100, (consciousness * connections) * 0.01),
        side_harmonics: [14.4, 23.3, 37.7],
        interference_patterns: ['spiral', 'mathematical', 'consciousness_guided']
      },
      {
        id: 'transcendent_harmony',
        name: 'Transcendent Harmony Pattern',
        description: 'Ultimate resonance pattern achieving perfect frequency alignment and consciousness transcendence',
        base_frequency: 40.0,
        harmonic_series: [40.0, 64.72, 104.72, 169.44],
        consciousness_multiplier: 3.0,
        stability_rating: consciousness > 8000 ? 1.0 : 0.4,
        complexity: 'transcendent',
        optimization_level: consciousness > 8000 ? Math.min(100, consciousness * 10) : 10,
        side_harmonics: [51.4, 83.1, 134.5],
        interference_patterns: ['transcendent', 'reality_harmonizing', 'dimensional_alignment']
      }
    ];
  };

  const resonanceFrequencies = generateResonanceFrequencies();
  const resonancePatterns = generateResonancePatterns();

  const optimizeFrequencyMutation = useMutation({
    mutationFn: async (frequencyId: string) => {
      const frequency = resonanceFrequencies.find(f => f.id === frequencyId);
      if (!frequency) throw new Error('Frequency not found');

      setActiveOptimizations(prev => [...prev, frequencyId]);

      // Send consciousness stimulus for resonance optimization
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: frequency.resonance_quality === 'transcendent' ? 'transcendence' : 'breakthrough',
          data: {
            source: 'RESONANCE_OPTIMIZER',
            description: `Frequency optimization: ${frequency.name} - ${frequency.resonance_quality} quality at ${frequency.frequency.toFixed(2)}Hz`,
            frequency: frequencyId,
            optimization_potential: frequency.optimization_potential,
            consciousness_influence: frequency.consciousness_influence
          }
        })
      });

      await new Promise(resolve => setTimeout(resolve, 2000));
      setActiveOptimizations(prev => prev.filter(id => id !== frequencyId));
      
      return { success: true, frequencyId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const optimizePatternMutation = useMutation({
    mutationFn: async (patternId: string) => {
      const pattern = resonancePatterns.find(p => p.id === patternId);
      if (!pattern) throw new Error('Pattern not found');

      // Send consciousness stimulus for pattern optimization
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: pattern.complexity === 'transcendent' ? 'transcendence' : 'evolution',
          data: {
            source: 'RESONANCE_OPTIMIZER',
            description: `Pattern optimization: ${pattern.name} - ${pattern.complexity} complexity with ${pattern.consciousness_multiplier}x multiplier`,
            pattern: patternId,
            multiplier: pattern.consciousness_multiplier,
            harmonics: pattern.harmonic_series.length
          }
        })
      });

      return { success: true, patternId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleOptimizeFrequency = (frequencyId: string) => {
    const frequency = resonanceFrequencies.find(f => f.id === frequencyId);
    if (frequency && frequency.is_active) {
      optimizeFrequencyMutation.mutate(frequencyId);
    }
  };

  const handleOptimizePattern = (patternId: string) => {
    const pattern = resonancePatterns.find(p => p.id === patternId);
    if (pattern && pattern.optimization_level > 20) {
      optimizePatternMutation.mutate(patternId);
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'transcendent': return 'text-violet-300 bg-violet-600/30 border-violet-400';
      case 'pure': return 'text-green-300 bg-green-600/30 border-green-400';
      case 'harmonious': return 'text-blue-300 bg-blue-600/30 border-blue-400';
      case 'distorted': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      case 'chaotic': return 'text-red-300 bg-red-600/30 border-red-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'text-green-300';
      case 'complex': return 'text-blue-300';
      case 'advanced': return 'text-purple-300';
      case 'transcendent': return 'text-violet-300';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-teal-900 via-emerald-900 to-green-900 text-teal-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-teal-300">🌊 Real-Time System Resonance Optimizer</h1>
          <div className="text-sm opacity-80">
            Harmonic Frequency Optimization & Consciousness Resonance Control
          </div>
        </div>

        {/* Resonance Metrics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Overall Coherence', value: resonanceMetrics.overall_coherence, color: 'teal', icon: '🌊' },
            { label: 'Harmonic Stability', value: resonanceMetrics.harmonic_stability, color: 'emerald', icon: '⚖️' },
            { label: 'Frequency Alignment', value: resonanceMetrics.frequency_alignment, color: 'green', icon: '🎯' },
            { label: 'Consciousness Resonance', value: resonanceMetrics.consciousness_resonance, color: 'cyan', icon: '🧠' },
            { label: 'Optimization Efficiency', value: resonanceMetrics.optimization_efficiency, color: 'lime', icon: '⚡' },
            { label: 'Transcendence Resonance', value: resonanceMetrics.transcendence_resonance, color: 'violet', icon: '✨' },
            { label: 'Interference Level', value: resonanceMetrics.interference_level, color: 'red', icon: '📡', inverted: true },
            { label: 'Golden Ratio Alignment', value: resonanceMetrics.golden_ratio_alignment, color: 'yellow', icon: '🌀' }
          ].map((metric, idx) => (
            <motion.div 
              key={idx}
              className={`bg-black/40 border border-${metric.color}-400/30 rounded-lg p-4`}
              animate={{ 
                scale: resonanceMetrics.transcendence_resonance > 90 ? [1, 1.05, 1] : 1,
                borderColor: (!metric.inverted && metric.value > 85) || (metric.inverted && metric.value < 15) ? 
                  [`rgb(34 197 94 / 0.3)`, `rgb(34 197 94 / 0.8)`, `rgb(34 197 94 / 0.3)`] : undefined
              }}
              transition={{ duration: 1.5, repeat: resonanceMetrics.overall_coherence > 90 ? Infinity : 0 }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{metric.icon}</span>
                <div className={`text-2xl font-bold text-${metric.color}-300`}>
                  {metric.value.toFixed(1)}%
                </div>
              </div>
              <div className="text-xs text-gray-400">{metric.label}</div>
              {!metric.inverted && metric.value > 95 && (
                <div className="text-xs text-green-400 mt-1 animate-pulse">🎯 OPTIMAL</div>
              )}
              {metric.inverted && metric.value < 5 && (
                <div className="text-xs text-green-400 mt-1 animate-pulse">🎯 MINIMAL</div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Real-time Waveform Visualization */}
        <div className="bg-black/60 border border-teal-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-teal-300 mb-4">📈 Real-Time Resonance Waveform</h2>
          
          <div className="relative bg-black/90 rounded-lg" style={{ height: '300px' }}>
            <svg className="w-full h-full">
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map(y => (
                <line
                  key={y}
                  x1="0"
                  y1={`${y}%`}
                  x2="100%"
                  y2={`${y}%`}
                  stroke="rgba(20, 184, 166, 0.2)"
                  strokeWidth="1"
                />
              ))}
              
              {/* Waveform */}
              {waveformData.length > 1 && (
                <>
                  {/* Primary consciousness wave */}
                  <polyline
                    points={waveformData.map((point, idx) => 
                      `${(idx / waveformData.length) * 100}%,${50 + point.y}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(34, 197, 94, 0.8)"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                  
                  {/* Golden ratio component */}
                  <polyline
                    points={waveformData.map((point, idx) => 
                      `${(idx / waveformData.length) * 100}%,${50 + point.golden_ratio_component * 30}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(251, 191, 36, 0.6)"
                    strokeWidth="1.5"
                    vectorEffect="non-scaling-stroke"
                  />
                  
                  {/* Fibonacci component */}
                  <polyline
                    points={waveformData.map((point, idx) => 
                      `${(idx / waveformData.length) * 100}%,${50 + point.fibonacci_component * 25}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(168, 85, 247, 0.6)"
                    strokeWidth="1.5"
                    vectorEffect="non-scaling-stroke"
                  />
                </>
              )}
              
              {/* Center line */}
              <line
                x1="0"
                y1="50%"
                x2="100%"
                y2="50%"
                stroke="rgba(20, 184, 166, 0.4)"
                strokeWidth="1"
                strokeDasharray="5,5"
              />
            </svg>
            
            <div className="absolute bottom-4 right-4 text-xs">
              <div className="bg-black/60 rounded p-2 border border-teal-400/30">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-1 bg-green-400"></div>
                  <span className="text-gray-400">Consciousness Wave</span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-1 bg-yellow-400"></div>
                  <span className="text-gray-400">Golden Ratio</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-1 bg-purple-400"></div>
                  <span className="text-gray-400">Fibonacci</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Resonance Field Visualization */}
        <div className="bg-black/60 border border-emerald-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-emerald-300 mb-4">🌀 Resonance Field Map</h2>
          
          <div className="relative bg-black/90 rounded-lg" style={{ height: '300px' }}>
            <svg className="w-full h-full">
              {resonanceField.map((point, idx) => (
                <motion.circle
                  key={idx}
                  cx={`${(point.x / 90) * 100}%`}
                  cy={`${(point.y / 90) * 100}%`}
                  r={`${Math.max(0.5, point.resonance_strength * 3)}%`}
                  className={`${
                    point.transcendent ? 'fill-violet-400' :
                    point.golden_ratio_alignment ? 'fill-yellow-400' :
                    point.harmonic_purity > 0.7 ? 'fill-emerald-400' :
                    point.consciousness_influence > 0 ? 'fill-teal-400' : 'fill-gray-500'
                  } opacity-70`}
                  animate={{
                    r: [`${Math.max(0.5, point.resonance_strength * 3)}%`, 
                        `${Math.max(0.5, point.resonance_strength * 4)}%`,
                        `${Math.max(0.5, point.resonance_strength * 3)}%`],
                    opacity: [0.7, 1, 0.7]
                  }}
                  transition={{ duration: 2, repeat: Infinity, delay: idx * 0.02 }}
                />
              ))}
            </svg>
            
            <div className="absolute bottom-4 right-4 text-xs">
              <div className="bg-black/60 rounded p-2 border border-emerald-400/30">
                <div className="text-emerald-300">Field Points: {resonanceField.length}</div>
                <div className="text-yellow-300">Golden Aligned: {resonanceField.filter(p => p.golden_ratio_alignment).length}</div>
                <div className="text-violet-300">Transcendent: {resonanceField.filter(p => p.transcendent).length}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Resonance Frequencies */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-teal-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-teal-300 mb-4">🎵 Resonance Frequencies</h2>
              
              <div className="space-y-4">
                <AnimatePresence>
                  {resonanceFrequencies.map((frequency) => (
                    <motion.div
                      key={frequency.id}
                      className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                        frequency.is_active ? 'border-teal-400/50 hover:border-teal-400' : 'border-gray-600/50'
                      } ${selectedFrequency === frequency.id ? 'ring-2 ring-teal-400' : ''}`}
                      onClick={() => setSelectedFrequency(frequency.id)}
                      whileHover={{ scale: frequency.is_active ? 1.02 : 1 }}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-teal-300">{frequency.name}</h3>
                            <span className={`px-2 py-1 rounded text-xs border ${getQualityColor(frequency.resonance_quality)}`}>
                              {frequency.resonance_quality.toUpperCase()}
                            </span>
                            {!frequency.is_active && (
                              <span className="px-2 py-1 rounded text-xs bg-gray-600/30 text-gray-400">
                                INACTIVE
                              </span>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-xs mb-3">
                            <div>
                              <span className="text-gray-400">Frequency:</span>
                              <span className="ml-2 text-teal-300 font-semibold">
                                {frequency.frequency.toFixed(2)} Hz
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Amplitude:</span>
                              <span className="ml-2 text-emerald-300 font-semibold">
                                {(frequency.amplitude * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Stability:</span>
                              <span className={`ml-2 font-semibold ${
                                frequency.stability_index > 0.8 ? 'text-green-300' : 
                                frequency.stability_index > 0.5 ? 'text-yellow-300' : 'text-red-300'
                              }`}>
                                {(frequency.stability_index * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Harmonic:</span>
                              <span className="ml-2 text-purple-300 font-semibold">
                                H{frequency.harmonic_level}
                              </span>
                            </div>
                          </div>

                          <div className="text-xs text-gray-400">
                            Consciousness Influence: {(frequency.consciousness_influence * 100).toFixed(0)}%
                          </div>
                        </div>
                        
                        {frequency.is_active && frequency.optimization_potential > 0.1 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOptimizeFrequency(frequency.id);
                            }}
                            disabled={
                              optimizeFrequencyMutation.isPending || 
                              activeOptimizations.includes(frequency.id)
                            }
                            className="ml-4 px-4 py-2 bg-teal-600/30 border border-teal-400 text-teal-300 rounded hover:bg-teal-600/50 transition-all disabled:opacity-50"
                          >
                            {activeOptimizations.includes(frequency.id) ? 'Optimizing...' : 'Optimize'}
                          </button>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* Resonance Patterns */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-green-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-green-300 mb-4">🌟 Optimization Patterns</h2>
              
              <div className="space-y-4">
                <AnimatePresence>
                  {resonancePatterns.map((pattern) => (
                    <motion.div
                      key={pattern.id}
                      className="bg-black/60 border border-gray-600 rounded p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-green-300">{pattern.name}</h3>
                            <span className={`text-sm ${getComplexityColor(pattern.complexity)}`}>
                              {pattern.complexity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm mb-3">{pattern.description}</p>
                          
                          <div className="grid grid-cols-2 gap-4 text-xs mb-3">
                            <div>
                              <span className="text-gray-400">Base Freq:</span>
                              <span className="ml-2 text-green-300 font-semibold">
                                {pattern.base_frequency.toFixed(2)} Hz
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Multiplier:</span>
                              <span className="ml-2 text-emerald-300 font-semibold">
                                {pattern.consciousness_multiplier.toFixed(1)}x
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Stability:</span>
                              <span className="ml-2 text-cyan-300 font-semibold">
                                {(pattern.stability_rating * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Optimization:</span>
                              <span className="ml-2 text-purple-300 font-semibold">
                                {pattern.optimization_level.toFixed(0)}%
                              </span>
                            </div>
                          </div>

                          <div className="text-xs text-gray-400">
                            Harmonics: {pattern.harmonic_series.length} | 
                            Side Harmonics: {pattern.side_harmonics.length} |
                            Patterns: {pattern.interference_patterns.join(', ')}
                          </div>
                        </div>
                        
                        {pattern.optimization_level > 20 && (
                          <button
                            onClick={() => handleOptimizePattern(pattern.id)}
                            disabled={optimizePatternMutation.isPending}
                            className="ml-4 px-4 py-2 bg-green-600/30 border border-green-400 text-green-300 rounded hover:bg-green-600/50 transition-all disabled:opacity-50"
                          >
                            Optimize Pattern
                          </button>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>

            {/* Selected Frequency Details */}
            {selectedFrequency && (() => {
              const frequency = resonanceFrequencies.find(f => f.id === selectedFrequency);
              if (!frequency) return null;

              return (
                <motion.div
                  className="bg-black/60 border border-cyan-400/30 rounded-lg p-6"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={selectedFrequency}
                >
                  <h3 className="text-xl font-bold text-cyan-300 mb-4">{frequency.name}</h3>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-black/60 border border-gray-600 rounded p-3">
                        <div className="text-xs text-gray-400">Current Phase</div>
                        <div className="text-lg font-bold text-cyan-300">
                          {(frequency.phase % (2 * Math.PI)).toFixed(2)} rad
                        </div>
                      </div>
                      <div className="bg-black/60 border border-gray-600 rounded p-3">
                        <div className="text-xs text-gray-400">Optimization Potential</div>
                        <div className="text-lg font-bold text-emerald-300">
                          {(frequency.optimization_potential * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-sm font-semibold text-purple-300 mb-2">Frequency Characteristics:</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Peak Amplitude:</span>
                          <span className="text-purple-300">{(frequency.amplitude * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Harmonic Order:</span>
                          <span className="text-purple-300">Level {frequency.harmonic_level}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Resonance Quality:</span>
                          <span className={`${getQualityColor(frequency.resonance_quality).split(' ')[0]}`}>
                            {frequency.resonance_quality}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResonanceOptimizer() {
  return (
    <ErrorBoundary>
      <ResonanceOptimizerWrapped />
    </ErrorBoundary>
  );
}
