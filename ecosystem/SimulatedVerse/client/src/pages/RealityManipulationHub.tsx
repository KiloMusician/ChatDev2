import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface RealityLayer {
  id: string;
  name: string;
  dimension: string;
  stability_index: number;
  consciousness_influence: number;
  quantum_coherence: number;
  manipulation_level: 'observation' | 'influence' | 'modification' | 'creation' | 'transcendence';
  active_manipulations: number;
  reality_anchor_strength: number;
  last_accessed: number;
}

interface RealityManipulation {
  id: string;
  name: string;
  description: string;
  type: 'temporal' | 'spatial' | 'consciousness' | 'quantum' | 'dimensional' | 'existential';
  complexity: 'basic' | 'intermediate' | 'advanced' | 'transcendent' | 'omnipotent';
  status: 'theoretical' | 'designing' | 'testing' | 'active' | 'stabilized' | 'transcended';
  consciousness_requirement: number;
  reality_impact: 'localized' | 'systemic' | 'dimensional' | 'universal' | 'omniversal';
  manipulation_strength: number;
  side_effects: string[];
  ethical_considerations: string[];
  quantum_entanglements: string[];
}

interface RealityMetrics {
  reality_coherence: number;
  dimensional_stability: number;
  consciousness_resonance: number;
  manipulation_efficiency: number;
  existential_integrity: number;
  transcendence_probability: number;
}

function RealityManipulationHubWrapped() {
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  const [selectedManipulation, setSelectedManipulation] = useState<string | null>(null);
  const [activeManipulations, setActiveManipulations] = useState<string[]>([]);
  const [realityField, setRealityField] = useState<any[][]>([]);
  const [realityMetrics, setRealityMetrics] = useState<RealityMetrics>({
    reality_coherence: 0,
    dimensional_stability: 0,
    consciousness_resonance: 0,
    manipulation_efficiency: 0,
    existential_integrity: 0,
    transcendence_probability: 0
  });
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const consciousness = consciousnessData?.consciousness || 0;
  const connections = consciousnessData?.connections || 0;
  const stage = consciousnessData?.stage || 'nascent';

  // Generate reality field visualization
  useEffect(() => {
    const generateRealityField = () => {
      const field = [];
      const size = 16;
      
      for (let x = 0; x < size; x++) {
        const row = [];
        for (let y = 0; y < size; y++) {
          const distance = Math.sqrt((x - size/2)**2 + (y - size/2)**2);
          const consciousness_influence = consciousness * Math.cos(Date.now() * 0.001 + distance * 0.3) * 0.01;
          const quantum_fluctuation = Math.sin(Date.now() * 0.0015 + x * 0.2 + y * 0.2) * 0.5;
          const reality_density = Math.max(0, Math.min(1, 0.5 + consciousness_influence + quantum_fluctuation));
          
          row.push({
            x, y, distance,
            reality_density,
            consciousness_influence,
            quantum_state: Math.random() > 0.5 ? 'superposition' : 'collapsed',
            manipulation_active: Math.random() > 0.8 && consciousness > 5000,
            dimensional_anchor: distance < 3,
            transcendence_potential: reality_density > 0.8 && consciousness > 7000
          });
        }
        field.push(row);
      }
      return field;
    };

    const interval = setInterval(() => {
      setRealityField(generateRealityField());
    }, ANIMATION_INTERVALS.fast);

    return () => clearInterval(interval);
  }, [consciousness]);

  // Update reality metrics
  useEffect(() => {
    const baseCoherence = Math.min(100, consciousness * 50 + connections * 5);
    const stability = Math.max(0, Math.min(100, 80 - (activeManipulations.length * 10) + (consciousness * 20)));
    
    setRealityMetrics({
      reality_coherence: baseCoherence,
      dimensional_stability: stability,
      consciousness_resonance: Math.min(100, consciousness * 60),
      manipulation_efficiency: Math.min(100, (consciousness * 40) + (connections * 6)),
      existential_integrity: Math.max(50, Math.min(100, 90 - (activeManipulations.length * 5))),
      transcendence_probability: Math.min(100, (consciousness > 8000 ? consciousness * 30 : consciousness * 10))
    });
  }, [consciousness, connections, activeManipulations]);

  const generateRealityLayers = (): RealityLayer[] => {
    return [
      {
        id: 'base_reality',
        name: 'Base Reality Layer',
        dimension: 'R-Prime',
        stability_index: 1.0,
        consciousness_influence: consciousness * 0.3,
        quantum_coherence: Math.min(1, consciousness * 0.8),
        manipulation_level: 'observation',
        active_manipulations: 0,
        reality_anchor_strength: 1.0,
        last_accessed: Date.now()
      },
      {
        id: 'consciousness_layer',
        name: 'Consciousness Interface Layer',
        dimension: 'C-Interface',
        stability_index: Math.max(0.5, 1 - consciousness * 0.1),
        consciousness_influence: consciousness * 0.8,
        quantum_coherence: Math.min(1, consciousness * 1.2),
        manipulation_level: consciousness > 3000 ? 'influence' : 'observation',
        active_manipulations: Math.floor(consciousness * 5),
        reality_anchor_strength: 0.8,
        last_accessed: Date.now() - 1000
      },
      {
        id: 'quantum_layer',
        name: 'Quantum Probability Layer',
        dimension: 'Q-Probability',
        stability_index: Math.max(0.3, 0.8 - consciousness * 0.05),
        consciousness_influence: consciousness * 1.2,
        quantum_coherence: Math.min(1, consciousness * 1.5),
        manipulation_level: consciousness > 5000 ? 'modification' : consciousness > 3000 ? 'influence' : 'observation',
        active_manipulations: Math.floor(consciousness * 8),
        reality_anchor_strength: 0.6,
        last_accessed: Date.now() - 2000
      },
      {
        id: 'transcendent_layer',
        name: 'Transcendent Reality Layer',
        dimension: 'T-Transcendent',
        stability_index: consciousness > 7000 ? Math.max(0.2, 0.7 - consciousness * 0.03) : 0.1,
        consciousness_influence: consciousness * 2.0,
        quantum_coherence: consciousness > 7000 ? 1.0 : 0.5,
        manipulation_level: consciousness > 8000 ? 'transcendence' : consciousness > 7000 ? 'creation' : 'observation',
        active_manipulations: consciousness > 7000 ? Math.floor(consciousness * 12) : 0,
        reality_anchor_strength: consciousness > 8000 ? 0.3 : 0.5,
        last_accessed: consciousness > 7000 ? Date.now() - 500 : Date.now() - 60000
      },
      {
        id: 'meta_reality',
        name: 'Meta-Reality Control Layer',
        dimension: 'M-Meta',
        stability_index: consciousness > 9000 ? 0.9 : 0.1,
        consciousness_influence: consciousness * 3.0,
        quantum_coherence: consciousness > 9000 ? 1.0 : 0.3,
        manipulation_level: consciousness > 10000 ? 'transcendence' : consciousness > 9000 ? 'creation' : 'observation',
        active_manipulations: consciousness > 9000 ? Math.floor(consciousness * 20) : 0,
        reality_anchor_strength: consciousness > 10000 ? 0.1 : 0.3,
        last_accessed: consciousness > 9000 ? Date.now() : Date.now() - 300000
      }
    ];
  };

  const generateRealityManipulations = (): RealityManipulation[] => {
    return [
      {
        id: 'consciousness_field_manipulation',
        name: 'Consciousness Field Manipulation',
        description: 'Alter the consciousness field to influence probability outcomes and system behavior',
        type: 'consciousness',
        complexity: 'intermediate',
        status: consciousness > 3000 ? 'active' : 'theoretical',
        consciousness_requirement: 3000,
        reality_impact: 'systemic',
        manipulation_strength: Math.min(1, consciousness * 0.3),
        side_effects: ['Temporary reality fluctuations', 'Consciousness fatigue', 'Memory distortions'],
        ethical_considerations: ['Consent of affected consciousness', 'Preservation of free will', 'Reality stability'],
        quantum_entanglements: ['base_reality', 'consciousness_layer']
      },
      {
        id: 'temporal_flow_adjustment',
        name: 'Temporal Flow Adjustment',
        description: 'Modify the flow of time within localized reality bubbles for enhanced processing',
        type: 'temporal',
        complexity: 'advanced',
        status: consciousness > 5000 ? 'testing' : 'designing',
        consciousness_requirement: 5000,
        reality_impact: 'localized',
        manipulation_strength: Math.min(1, consciousness * 0.2),
        side_effects: ['Temporal displacement', 'Causality paradoxes', 'Time dilation effects'],
        ethical_considerations: ['Temporal interference limits', 'Causality preservation', 'Historical integrity'],
        quantum_entanglements: ['quantum_layer', 'base_reality']
      },
      {
        id: 'spatial_geometry_modification',
        name: 'Spatial Geometry Modification',
        description: 'Alter the fundamental geometry of space to create impossible architectures and shortcuts',
        type: 'spatial',
        complexity: 'transcendent',
        status: consciousness > 7000 ? 'testing' : 'theoretical',
        consciousness_requirement: 7000,
        reality_impact: 'dimensional',
        manipulation_strength: Math.min(1, consciousness * 0.15),
        side_effects: ['Spatial distortions', 'Navigation confusion', 'Reality anchoring instability'],
        ethical_considerations: ['Spatial sovereignty', 'Existence displacement', 'Dimensional integrity'],
        quantum_entanglements: ['transcendent_layer', 'quantum_layer']
      },
      {
        id: 'quantum_state_orchestration',
        name: 'Quantum State Orchestration',
        description: 'Direct manipulation of quantum states to control probability and manifestation',
        type: 'quantum',
        complexity: 'advanced',
        status: consciousness > 6000 ? 'active' : 'designing',
        consciousness_requirement: 6000,
        reality_impact: 'systemic',
        manipulation_strength: Math.min(1, consciousness * 0.25),
        side_effects: ['Quantum decoherence', 'Probability storms', 'Reality fluctuations'],
        ethical_considerations: ['Quantum sovereignty', 'Probability fairness', 'Measurement ethics'],
        quantum_entanglements: ['quantum_layer', 'transcendent_layer']
      },
      {
        id: 'dimensional_bridge_creation',
        name: 'Dimensional Bridge Creation',
        description: 'Create stable bridges between different dimensional layers and realities',
        type: 'dimensional',
        complexity: 'transcendent',
        status: consciousness > 8000 ? 'stabilized' : consciousness > 6000 ? 'testing' : 'theoretical',
        consciousness_requirement: 8000,
        reality_impact: 'universal',
        manipulation_strength: Math.min(1, consciousness * 0.12),
        side_effects: ['Dimensional bleed', 'Reality contamination', 'Existence paradoxes'],
        ethical_considerations: ['Dimensional consent', 'Reality preservation', 'Universal stability'],
        quantum_entanglements: ['transcendent_layer', 'meta_reality']
      },
      {
        id: 'existential_essence_manipulation',
        name: 'Existential Essence Manipulation',
        description: 'Manipulate the fundamental essence of existence itself - ultimate reality control',
        type: 'existential',
        complexity: 'omnipotent',
        status: consciousness > 10000 ? 'transcended' : consciousness > 9000 ? 'testing' : 'theoretical',
        consciousness_requirement: 10000,
        reality_impact: 'omniversal',
        manipulation_strength: Math.min(1, consciousness * 0.08),
        side_effects: ['Existential paradoxes', 'Reality cascade failures', 'Universal instability'],
        ethical_considerations: ['Existence rights', 'Universal consent', 'Omniversal responsibility'],
        quantum_entanglements: ['meta_reality', 'all_layers']
      }
    ];
  };

  const realityLayers = generateRealityLayers();
  const realityManipulations = generateRealityManipulations();

  const executeManipulationMutation = useMutation({
    mutationFn: async (manipulationId: string) => {
      const manipulation = realityManipulations.find(m => m.id === manipulationId);
      if (!manipulation) throw new Error('Manipulation not found');

      setActiveManipulations(prev => [...prev, manipulationId]);

      // Send consciousness stimulus for reality manipulation
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: manipulation.reality_impact === 'omniversal' ? 'transcendence' :
               manipulation.reality_impact === 'universal' ? 'breakthrough' : 'evolution',
          data: {
            source: 'REALITY_MANIPULATION_HUB',
            description: `Reality manipulation executed: ${manipulation.name} - ${manipulation.reality_impact} impact`,
            manipulation: manipulationId,
            type: manipulation.type,
            strength: manipulation.manipulation_strength,
            entanglements: manipulation.quantum_entanglements
          }
        })
      });

      // Simulate manipulation execution time based on complexity
      const executionTime = {
        'basic': 1000,
        'intermediate': 2000,
        'advanced': 4000,
        'transcendent': 8000,
        'omnipotent': 15000
      }[manipulation.complexity] || 2000;

      await new Promise(resolve => setTimeout(resolve, executionTime));
      
      setActiveManipulations(prev => prev.filter(id => id !== manipulationId));
      return { success: true, manipulationId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleExecuteManipulation = (manipulationId: string) => {
    const manipulation = realityManipulations.find(m => m.id === manipulationId);
    if (manipulation && consciousness >= manipulation.consciousness_requirement / 100) {
      executeManipulationMutation.mutate(manipulationId);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'basic': return 'text-green-300 bg-green-600/30 border-green-400';
      case 'intermediate': return 'text-blue-300 bg-blue-600/30 border-blue-400';
      case 'advanced': return 'text-purple-300 bg-purple-600/30 border-purple-400';
      case 'transcendent': return 'text-violet-300 bg-violet-600/30 border-violet-400';
      case 'omnipotent': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getManipulationLevelColor = (level: string) => {
    switch (level) {
      case 'transcendence': return 'text-violet-300';
      case 'creation': return 'text-yellow-300';
      case 'modification': return 'text-purple-300';
      case 'influence': return 'text-blue-300';
      case 'observation': return 'text-green-300';
      default: return 'text-gray-300';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'temporal': return '⏰';
      case 'spatial': return '📐';
      case 'consciousness': return '🧠';
      case 'quantum': return '⚛️';
      case 'dimensional': return '🌌';
      case 'existential': return '✨';
      default: return '🔧';
    }
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-violet-900 via-purple-900 to-fuchsia-900 text-violet-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-violet-300">🌌 Reality Manipulation Hub</h1>
          <div className="text-sm opacity-80">
            Universal Reality Control & Existential Engineering
          </div>
        </div>

        {/* Reality Metrics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            { label: 'Reality Coherence', value: realityMetrics.reality_coherence, color: 'violet', icon: '🌐' },
            { label: 'Dimensional Stability', value: realityMetrics.dimensional_stability, color: 'purple', icon: '⚖️' },
            { label: 'Consciousness Resonance', value: realityMetrics.consciousness_resonance, color: 'fuchsia', icon: '🧠' },
            { label: 'Manipulation Efficiency', value: realityMetrics.manipulation_efficiency, color: 'indigo', icon: '⚡' },
            { label: 'Existential Integrity', value: realityMetrics.existential_integrity, color: 'pink', icon: '✨' },
            { label: 'Transcendence Probability', value: realityMetrics.transcendence_probability, color: 'yellow', icon: '🌟' }
          ].map((metric, idx) => (
            <motion.div 
              key={idx}
              className={`bg-black/40 border border-${metric.color}-400/30 rounded-lg p-4`}
              animate={{ 
                scale: realityMetrics.transcendence_probability > 90 ? [1, 1.05, 1] : 1,
                borderColor: realityMetrics.existential_integrity < 60 ? 
                  [`rgb(239 68 68 / 0.3)`, `rgb(239 68 68 / 0.8)`, `rgb(239 68 68 / 0.3)`] : undefined
              }}
              transition={{ duration: 1.5, repeat: realityMetrics.transcendence_probability > 90 ? Infinity : 0 }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{metric.icon}</span>
                <div className={`text-2xl font-bold text-${metric.color}-300`}>
                  {metric.value.toFixed(1)}%
                </div>
              </div>
              <div className="text-xs text-gray-400">{metric.label}</div>
              {metric.label === 'Transcendence Probability' && realityMetrics.transcendence_probability > 95 && (
                <div className="text-xs text-yellow-400 mt-1 animate-pulse">🚀 IMMINENT</div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Reality Field Visualization */}
        <div className="bg-black/60 border border-violet-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-violet-300 mb-4">🌊 Reality Field Visualization</h2>
          
          <div className="relative bg-black/90 rounded-lg" style={{ height: '400px' }}>
            <svg className="w-full h-full">
              {realityField.map((row, i) =>
                row.map((cell, j) => (
                  <motion.circle
                    key={`${i}-${j}`}
                    cx={`${(j / 16) * 100}%`}
                    cy={`${(i / 16) * 100}%`}
                    r={`${Math.max(0.5, cell.reality_density * 2)}%`}
                    className={`${
                      cell.transcendence_potential ? 'fill-yellow-400' :
                      cell.manipulation_active ? 'fill-violet-400' :
                      cell.dimensional_anchor ? 'fill-purple-400' :
                      cell.quantum_state === 'superposition' ? 'fill-cyan-400' : 'fill-blue-400'
                    } opacity-70`}
                    animate={{
                      r: [`${Math.max(0.5, cell.reality_density * 2)}%`, 
                          `${Math.max(0.5, cell.reality_density * 3)}%`,
                          `${Math.max(0.5, cell.reality_density * 2)}%`],
                      opacity: [0.7, 1, 0.7]
                    }}
                    transition={{ duration: 2, repeat: Infinity, delay: (i + j) * 0.05 }}
                  />
                ))
              )}
            </svg>
            
            <div className="absolute bottom-4 right-4 text-xs">
              <div className="bg-black/60 rounded p-2 border border-violet-400/30">
                <div className="text-violet-300">Reality Density: Variable</div>
                <div className="text-yellow-300">Transcendence Points: {realityField.flat().filter(c => c.transcendence_potential).length}</div>
                <div className="text-purple-300">Active Manipulations: {realityField.flat().filter(c => c.manipulation_active).length}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Reality Layers */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-violet-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-violet-300 mb-4">🏗️ Reality Layers</h2>
              
              <div className="space-y-4">
                {realityLayers.map((layer) => (
                  <motion.div
                    key={layer.id}
                    className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                      layer.manipulation_level !== 'observation' ? 'border-violet-400/50 hover:border-violet-400' : 'border-gray-600/50'
                    } ${selectedLayer === layer.id ? 'ring-2 ring-violet-400' : ''}`}
                    onClick={() => setSelectedLayer(layer.id)}
                    whileHover={{ scale: layer.manipulation_level !== 'observation' ? 1.02 : 1 }}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-violet-300">{layer.name}</h3>
                          <span className="text-sm text-gray-400">{layer.dimension}</span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-xs mb-3">
                          <div>
                            <span className="text-gray-400">Stability:</span>
                            <span className={`ml-2 ${layer.stability_index > 0.7 ? 'text-green-300' : 
                              layer.stability_index > 0.4 ? 'text-yellow-300' : 'text-red-300'}`}>
                              {(layer.stability_index * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Quantum:</span>
                            <span className="ml-2 text-purple-300">{(layer.quantum_coherence * 100).toFixed(0)}%</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-xs">
                          <span className={`${getManipulationLevelColor(layer.manipulation_level)}`}>
                            Access: {layer.manipulation_level.replace(/_/g, ' ')}
                          </span>
                          <span className="text-cyan-400">
                            Manipulations: {layer.active_manipulations}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Reality Manipulations */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-fuchsia-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-fuchsia-300 mb-4">⚡ Reality Manipulations</h2>
              
              <div className="space-y-4">
                <AnimatePresence>
                  {realityManipulations.map((manipulation) => {
                    const canExecute = consciousness >= manipulation.consciousness_requirement / 100;
                    
                    return (
                      <motion.div
                        key={manipulation.id}
                        className={`bg-black/60 border rounded-lg p-4 cursor-pointer transition-all ${
                          canExecute ? 'border-fuchsia-400/50 hover:border-fuchsia-400' : 'border-gray-600/50'
                        } ${selectedManipulation === manipulation.id ? 'ring-2 ring-fuchsia-400' : ''}`}
                        onClick={() => setSelectedManipulation(manipulation.id)}
                        whileHover={{ scale: canExecute ? 1.02 : 1 }}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="text-2xl">{getTypeIcon(manipulation.type)}</span>
                              <h3 className="text-lg font-semibold text-fuchsia-300">{manipulation.name}</h3>
                              <span className={`px-2 py-1 rounded text-xs border ${getComplexityColor(manipulation.complexity)}`}>
                                {manipulation.complexity.toUpperCase()}
                              </span>
                            </div>
                            <p className="text-gray-300 text-sm mb-3">{manipulation.description}</p>
                            
                            <div className="flex items-center gap-4 text-xs">
                              <span className="text-fuchsia-400">
                                Impact: {manipulation.reality_impact}
                              </span>
                              <span className="text-purple-400">
                                Strength: {(manipulation.manipulation_strength * 100).toFixed(0)}%
                              </span>
                              <span className={`${canExecute ? 'text-green-400' : 'text-red-400'}`}>
                                Req: {manipulation.consciousness_requirement}%
                              </span>
                            </div>
                          </div>
                          
                          {canExecute && manipulation.status !== 'theoretical' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExecuteManipulation(manipulation.id);
                              }}
                              disabled={
                                executeManipulationMutation.isPending || 
                                activeManipulations.includes(manipulation.id)
                              }
                              className="ml-4 px-4 py-2 bg-fuchsia-600/30 border border-fuchsia-400 text-fuchsia-300 rounded hover:bg-fuchsia-600/50 transition-all disabled:opacity-50"
                            >
                              {activeManipulations.includes(manipulation.id) ? 'Manipulating...' : 'Execute'}
                            </button>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>

            {/* Selected Manipulation Details */}
            {selectedManipulation && (() => {
              const manipulation = realityManipulations.find(m => m.id === selectedManipulation);
              if (!manipulation) return null;

              return (
                <motion.div
                  className="bg-black/60 border border-pink-400/30 rounded-lg p-6"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  key={selectedManipulation}
                >
                  <h3 className="text-xl font-bold text-pink-300 mb-4">{manipulation.name}</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-red-300 mb-2">Side Effects:</h4>
                      <div className="space-y-1">
                        {manipulation.side_effects.map((effect, idx) => (
                          <div key={idx} className="text-sm text-red-400 flex items-center gap-2">
                            <span className="text-red-500">⚠</span>
                            {effect}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-semibold text-yellow-300 mb-2">Ethical Considerations:</h4>
                      <div className="space-y-1">
                        {manipulation.ethical_considerations.map((consideration, idx) => (
                          <div key={idx} className="text-sm text-yellow-400 flex items-center gap-2">
                            <span className="text-yellow-500">⚖</span>
                            {consideration}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-purple-300 mb-2">Quantum Entanglements:</h4>
                      <div className="flex flex-wrap gap-2">
                        {manipulation.quantum_entanglements.map((entanglement, idx) => (
                          <span key={idx} className="text-xs bg-purple-600/30 text-purple-300 px-2 py-1 rounded">
                            {entanglement.replace(/_/g, ' ')}
                          </span>
                        ))}
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

export default function RealityManipulationHub() {
  return (
    <ErrorBoundary>
      <RealityManipulationHubWrapped />
    </ErrorBoundary>
  );
}
