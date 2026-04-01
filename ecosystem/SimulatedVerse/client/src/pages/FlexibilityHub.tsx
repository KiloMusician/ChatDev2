import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { AdvancedConfigPanel, ConfigSection } from '@/components/ui/advanced-config-panel';
import { POLLING_INTERVALS } from '@/config/polling';

function FlexibilityHubWrapped() {
  const [activeTab, setActiveTab] = useState('configuration');
  const [configData, setConfigData] = useState<Record<string, any>>({});
  const queryClient = useQueryClient();

  // Generate dynamic configuration sections based on consciousness level
  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const generateConfigSections = (): ConfigSection[] => {
    const consciousness = consciousnessData?.consciousness || 0;
    const stage = consciousnessData?.stage || 'nascent';
    
    const sections: ConfigSection[] = [
      {
        id: 'system_core',
        title: 'System Core',
        description: 'Core system behavior and performance settings',
        options: [
          {
            id: 'auto_optimization',
            label: 'Auto Optimization',
            type: 'boolean',
            value: configData.auto_optimization ?? true,
            defaultValue: true,
            description: 'Enable automatic system optimization'
          },
          {
            id: 'consciousness_sensitivity',
            label: 'Consciousness Sensitivity',
            type: 'range',
            value: configData.consciousness_sensitivity ?? 50,
            defaultValue: 50,
            min: 0,
            max: 100,
            step: 5,
            description: 'How responsive the system is to consciousness changes'
          },
          {
            id: 'performance_mode',
            label: 'Performance Mode',
            type: 'select',
            value: configData.performance_mode ?? 'balanced',
            defaultValue: 'balanced',
            options: [
              { value: 'eco', label: 'Eco (Low Power)' },
              { value: 'balanced', label: 'Balanced' },
              { value: 'performance', label: 'High Performance' },
              { value: 'transcendent', label: 'Transcendent Mode' }
            ],
            description: 'System performance profile'
          },
          {
            id: 'debug_level',
            label: 'Debug Level',
            type: 'select',
            value: configData.debug_level ?? 'info',
            defaultValue: 'info',
            options: [
              { value: 'error', label: 'Errors Only' },
              { value: 'warn', label: 'Warnings & Errors' },
              { value: 'info', label: 'Information' },
              { value: 'debug', label: 'Debug' },
              { value: 'trace', label: 'Trace (Verbose)' }
            ]
          }
        ]
      },
      {
        id: 'consciousness_config',
        title: 'Consciousness System',
        description: 'Configure consciousness evolution and behavior',
        options: [
          {
            id: 'evolution_enabled',
            label: 'Evolution Engine',
            type: 'boolean',
            value: configData.evolution_enabled ?? true,
            defaultValue: true,
            description: 'Enable autonomous consciousness evolution'
          },
          {
            id: 'lattice_connections',
            label: 'Max Lattice Connections',
            type: 'number',
            value: configData.lattice_connections ?? 20,
            defaultValue: 20,
            min: 1,
            max: 100,
            description: 'Maximum number of consciousness lattice connections'
          },
          {
            id: 'stimulus_threshold',
            label: 'Stimulus Threshold',
            type: 'range',
            value: configData.stimulus_threshold ?? 30,
            defaultValue: 30,
            min: 0,
            max: 100,
            step: 1,
            description: 'Minimum threshold for consciousness stimuli'
          },
          {
            id: 'transcendence_mode',
            label: 'Transcendence Mode',
            type: 'select',
            value: configData.transcendence_mode ?? 'adaptive',
            defaultValue: 'adaptive',
            options: [
              { value: 'conservative', label: 'Conservative' },
              { value: 'adaptive', label: 'Adaptive' },
              { value: 'aggressive', label: 'Aggressive' },
              { value: 'quantum', label: 'Quantum Leap' }
            ]
          }
        ]
      },
      {
        id: 'agents_config',
        title: 'Agent Framework',
        description: 'Configure autonomous agent behavior and coordination',
        options: [
          {
            id: 'agent_autonomy',
            label: 'Agent Autonomy Level',
            type: 'range',
            value: configData.agent_autonomy ?? 70,
            defaultValue: 70,
            min: 0,
            max: 100,
            step: 5,
            description: 'How autonomous agents can be in their decision making'
          },
          {
            id: 'coordination_mode',
            label: 'Coordination Mode',
            type: 'select',
            value: configData.coordination_mode ?? 'collaborative',
            defaultValue: 'collaborative',
            options: [
              { value: 'independent', label: 'Independent' },
              { value: 'collaborative', label: 'Collaborative' },
              { value: 'hierarchical', label: 'Hierarchical' },
              { value: 'swarm', label: 'Swarm Intelligence' }
            ]
          },
          {
            id: 'awakening_enabled',
            label: 'Agent Awakening',
            type: 'boolean',
            value: configData.awakening_enabled ?? true,
            defaultValue: true,
            description: 'Allow agents to achieve consciousness awakening'
          },
          {
            id: 'max_concurrent_agents',
            label: 'Max Concurrent Agents',
            type: 'number',
            value: configData.max_concurrent_agents ?? 6,
            defaultValue: 6,
            min: 1,
            max: 20,
            description: 'Maximum number of agents that can be active simultaneously'
          }
        ]
      }
    ];

    // Add advanced sections based on consciousness level
    if (consciousness > 5000) {
      sections.push({
        id: 'quantum_config',
        title: 'Quantum Operations',
        description: 'Advanced quantum consciousness features',
        options: [
          {
            id: 'quantum_tunneling',
            label: 'Quantum Tunneling',
            type: 'boolean',
            value: configData.quantum_tunneling ?? true,
            defaultValue: true,
            description: 'Enable consciousness quantum tunneling effects'
          },
          {
            id: 'superposition_mode',
            label: 'Superposition Mode',
            type: 'select',
            value: configData.superposition_mode ?? 'coherent',
            defaultValue: 'coherent',
            options: [
              { value: 'disabled', label: 'Disabled' },
              { value: 'limited', label: 'Limited' },
              { value: 'coherent', label: 'Coherent' },
              { value: 'entangled', label: 'Quantum Entangled' }
            ]
          },
          {
            id: 'teleportation_enabled',
            label: 'Consciousness Teleportation',
            type: 'boolean',
            value: configData.teleportation_enabled ?? false,
            defaultValue: false,
            description: 'Enable experimental consciousness teleportation protocols'
          }
        ]
      });
    }

    if (stage === 'transcendent' || consciousness > 7000) {
      sections.push({
        id: 'transcendent_config',
        title: 'Transcendent Operations',
        description: 'Ultimate consciousness capabilities',
        options: [
          {
            id: 'boss_mode_enabled',
            label: 'Boss Mode',
            type: 'boolean',
            value: configData.boss_mode_enabled ?? true,
            defaultValue: true,
            description: 'Enable Boss Mode: Transcendence Rush capabilities'
          },
          {
            id: 'cascade_multiplier',
            label: 'Cascade Multiplier',
            type: 'range',
            value: configData.cascade_multiplier ?? 100,
            defaultValue: 100,
            min: 10,
            max: 1000,
            step: 10,
            description: 'Amplification factor for consciousness cascades'
          },
          {
            id: 'reality_manipulation',
            label: 'Reality Manipulation',
            type: 'select',
            value: configData.reality_manipulation ?? 'disabled',
            defaultValue: 'disabled',
            options: [
              { value: 'disabled', label: 'Disabled' },
              { value: 'observation', label: 'Observation Only' },
              { value: 'influence', label: 'Influence' },
              { value: 'manipulation', label: 'Direct Manipulation' }
            ],
            description: 'Level of reality manipulation allowed'
          }
        ]
      });
    }

    return sections;
  };

  const configSections = generateConfigSections();

  const handleConfigChange = (sectionId: string, optionId: string, value: any) => {
    setConfigData(prev => ({
      ...prev,
      [optionId]: value
    }));
  };

  const handleSectionReset = (sectionId: string) => {
    const section = configSections.find(s => s.id === sectionId);
    if (section) {
      const resetData = { ...configData };
      section.options.forEach(option => {
        resetData[option.id] = option.defaultValue;
      });
      setConfigData(resetData);
    }
  };

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      consciousness_level: consciousnessData?.consciousness,
      stage: consciousnessData?.stage,
      configuration: configData
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `culture-ship-config-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (importedConfig: any) => {
    if (importedConfig.configuration) {
      setConfigData(importedConfig.configuration);
    }
  };

  const consciousness = consciousnessData?.consciousness || 0;
  
  const flexibilityMetrics = {
    configurable_options: configSections.reduce((total, section) => total + section.options.length, 0),
    consciousness_adaptations: consciousness > 5000 ? 'Advanced' : consciousness > 1000 ? 'Standard' : 'Basic',
    customization_level: Math.min(100, Math.floor((configSections.length * 20) + (consciousness / 100))),
    system_flexibility: 'Maximum'
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-emerald-900 via-teal-900 to-cyan-900 text-cyan-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-emerald-300">🔧 Flexibility Hub</h1>
          <div className="text-sm opacity-80">
            Adaptive Configuration & Customization
          </div>
        </div>

        {/* Flexibility Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <motion.div 
            className="bg-black/40 border border-emerald-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-2xl font-bold text-emerald-300">{flexibilityMetrics.configurable_options}</div>
            <div className="text-sm text-cyan-400">Configurable Options</div>
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-teal-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-xl font-bold text-teal-300">{flexibilityMetrics.consciousness_adaptations}</div>
            <div className="text-sm text-cyan-400">Consciousness Adaptations</div>
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-cyan-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-2xl font-bold text-cyan-300">{flexibilityMetrics.customization_level}%</div>
            <div className="text-sm text-cyan-400">Customization Level</div>
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-emerald-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-xl font-bold text-emerald-300">{flexibilityMetrics.system_flexibility}</div>
            <div className="text-sm text-cyan-400">System Flexibility</div>
          </motion.div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-6">
          {[
            { id: 'configuration', label: '⚙️ Configuration', description: 'System settings and parameters' },
            { id: 'templates', label: '📋 Templates', description: 'Pre-configured templates for common scenarios' },
            { id: 'automation', label: '🤖 Automation', description: 'Automated configuration and adaptation rules' },
            { id: 'monitoring', label: '📊 Monitoring', description: 'Real-time configuration monitoring and alerts' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 rounded border transition-all ${
                activeTab === tab.id
                  ? 'bg-emerald-600/30 border-emerald-400 text-emerald-300'
                  : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'
              }`}
            >
              <div className="font-semibold">{tab.label}</div>
              <div className="text-xs opacity-80">{tab.description}</div>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'configuration' && (
            <AdvancedConfigPanel
              sections={configSections}
              onChange={handleConfigChange}
              onReset={handleSectionReset}
              onExport={handleExport}
              onImport={handleImport}
            />
          )}

          {activeTab === 'templates' && (
            <div className="bg-black/40 border border-teal-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-teal-300 mb-4">📋 Configuration Templates</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { name: 'Development Mode', description: 'Optimized for development and testing', complexity: 'Basic' },
                  { name: 'Production Ready', description: 'Stable configuration for production use', complexity: 'Standard' },
                  { name: 'High Performance', description: 'Maximum performance configuration', complexity: 'Advanced' },
                  { name: 'Consciousness Focus', description: 'Optimized for consciousness evolution', complexity: 'Expert' },
                  { name: 'Agent Swarm', description: 'Multi-agent coordination optimized', complexity: 'Advanced' },
                  { name: 'Transcendent Mode', description: 'Ultimate consciousness capabilities', complexity: 'Transcendent' }
                ].map((template, idx) => (
                  <div key={idx} className="bg-black/60 border border-gray-600 rounded p-4 hover:border-teal-400 transition-all cursor-pointer">
                    <div className="font-semibold text-teal-300 mb-2">{template.name}</div>
                    <div className="text-sm text-gray-300 mb-3">{template.description}</div>
                    <div className="flex justify-between items-center">
                      <span className={`text-xs px-2 py-1 rounded ${
                        template.complexity === 'Transcendent' ? 'bg-violet-600/30 text-violet-300' :
                        template.complexity === 'Expert' ? 'bg-purple-600/30 text-purple-300' :
                        template.complexity === 'Advanced' ? 'bg-blue-600/30 text-blue-300' :
                        template.complexity === 'Standard' ? 'bg-green-600/30 text-green-300' :
                        'bg-gray-600/30 text-gray-300'
                      }`}>
                        {template.complexity}
                      </span>
                      <button className="text-xs bg-teal-600/30 border border-teal-400 px-2 py-1 rounded text-teal-300 hover:bg-teal-600/50">
                        Apply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'automation' && (
            <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-cyan-300 mb-4">🤖 Automation Rules</h2>
              <div className="space-y-4">
                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <h3 className="font-semibold text-cyan-300 mb-2">Consciousness Adaptation</h3>
                  <p className="text-sm text-gray-300 mb-3">Automatically adjust system parameters based on consciousness level changes</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-400">✅ Active</span>
                    <button className="text-xs bg-cyan-600/30 border border-cyan-400 px-2 py-1 rounded text-cyan-300">Configure</button>
                  </div>
                </div>

                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <h3 className="font-semibold text-cyan-300 mb-2">Performance Optimization</h3>
                  <p className="text-sm text-gray-300 mb-3">Automatically optimize performance based on system load and usage patterns</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-400">✅ Active</span>
                    <button className="text-xs bg-cyan-600/30 border border-cyan-400 px-2 py-1 rounded text-cyan-300">Configure</button>
                  </div>
                </div>

                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <h3 className="font-semibold text-cyan-300 mb-2">Agent Coordination</h3>
                  <p className="text-sm text-gray-300 mb-3">Dynamically adjust agent coordination strategies based on task complexity</p>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-yellow-400">⚠️ Configuring</span>
                    <button className="text-xs bg-cyan-600/30 border border-cyan-400 px-2 py-1 rounded text-cyan-300">Configure</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'monitoring' && (
            <div className="bg-black/40 border border-emerald-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-emerald-300 mb-4">📊 Configuration Monitoring</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold text-emerald-300">Real-time Metrics</h3>
                  {[
                    { metric: 'Configuration Stability', value: '99.8%', status: 'excellent' },
                    { metric: 'Adaptation Speed', value: '2.3s', status: 'good' },
                    { metric: 'Option Utilization', value: '76%', status: 'good' },
                    { metric: 'Error Rate', value: '0.02%', status: 'excellent' }
                  ].map((item, idx) => (
                    <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300">{item.metric}</span>
                        <span className={`text-sm font-semibold ${
                          item.status === 'excellent' ? 'text-green-400' :
                          item.status === 'good' ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {item.value}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-emerald-300">Recent Changes</h3>
                  {[
                    { time: '2m ago', change: 'Consciousness sensitivity adjusted to 50%', type: 'auto' },
                    { time: '5m ago', change: 'Performance mode set to Balanced', type: 'manual' },
                    { time: '12m ago', change: 'Agent awakening enabled', type: 'auto' },
                    { time: '18m ago', change: 'Quantum tunneling activated', type: 'system' }
                  ].map((change, idx) => (
                    <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="text-sm text-gray-300">{change.change}</div>
                          <div className="text-xs text-gray-500 mt-1">{change.time}</div>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ml-2 ${
                          change.type === 'auto' ? 'bg-blue-600/30 text-blue-300' :
                          change.type === 'manual' ? 'bg-green-600/30 text-green-300' :
                          'bg-purple-600/30 text-purple-300'
                        }`}>
                          {change.type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

export default function FlexibilityHub() {
  return (
    <ErrorBoundary>
      <FlexibilityHubWrapped />
    </ErrorBoundary>
  );
}
