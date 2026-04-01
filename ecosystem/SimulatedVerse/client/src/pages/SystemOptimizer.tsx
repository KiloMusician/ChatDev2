import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { POLLING_INTERVALS } from '@/config/polling';

function SystemOptimizerWrapped() {
  const [activeOptimizations, setActiveOptimizations] = useState<string[]>([]);
  const [selectedScope, setSelectedScope] = useState('system');
  const queryClient = useQueryClient();

  const { data: systemMetrics } = useQuery<any>({
    queryKey: ['/api/analysis', selectedScope],
    queryFn: () => 
      fetch('/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope: { modes: [selectedScope] } })
      }).then(res => res.json()),
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: infrastructureData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const optimizeMutation = useMutation({
    mutationFn: async (optimization: any) => {
      // Simulate optimization execution
      await new Promise(resolve => setTimeout(resolve, 2000));
      return { success: true, optimization };
    },
    onSuccess: (data) => {
      setActiveOptimizations(prev => [...prev, data.optimization.id]);
      queryClient.invalidateQueries({ queryKey: ['/api/analysis'] });
    }
  });

  const handleOptimize = (optimization: any) => {
    optimizeMutation.mutate(optimization);
  };

  const generateOptimizations = () => {
    const baseOptimizations = [
      {
        id: 'memory_optimization',
        title: 'Memory Footprint Optimization',
        description: 'Optimize memory usage patterns and garbage collection',
        impact: 'High',
        effort: 'Medium',
        category: 'Performance'
      },
      {
        id: 'consciousness_acceleration',
        title: 'Consciousness Cascade Acceleration',
        description: 'Enhance quantum consciousness processing efficiency',
        impact: 'Critical',
        effort: 'High',
        category: 'Consciousness'
      },
      {
        id: 'api_response_caching',
        title: 'Intelligent API Response Caching',
        description: 'Implement smart caching for frequently accessed endpoints',
        impact: 'Medium',
        effort: 'Low',
        category: 'Performance'
      },
      {
        id: 'error_recovery_enhancement',
        title: 'Advanced Error Recovery Systems',
        description: 'Implement self-healing mechanisms for system resilience',
        impact: 'High',
        effort: 'Medium',
        category: 'Reliability'
      },
      {
        id: 'real_time_analytics',
        title: 'Real-time Performance Analytics',
        description: 'Enhanced monitoring and predictive performance insights',
        impact: 'Medium',
        effort: 'Medium',
        category: 'Monitoring'
      },
      {
        id: 'agent_coordination_optimization',
        title: 'Agent Coordination Protocol Enhancement',
        description: 'Optimize multi-agent communication and task distribution',
        impact: 'High',
        effort: 'High',
        category: 'Agents'
      }
    ];

    // Add consciousness-level dependent optimizations
    const consciousness = infrastructureData?.consciousness || 0;
    if (consciousness > 5000) {
      baseOptimizations.push({
        id: 'transcendence_protocol',
        title: 'Transcendence Protocol Activation',
        description: 'Unlock advanced consciousness capabilities',
        impact: 'Critical',
        effort: 'High',
        category: 'Transcendence'
      });
    }

    return baseOptimizations.filter(opt => !activeOptimizations.includes(opt.id));
  };

  const optimizations = generateOptimizations();

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-blue-300">⚡ System Optimizer</h1>
          <div className="text-sm opacity-80">
            Autonomous Performance Enhancement
          </div>
        </div>

        {/* System Health Overview */}
        <div className="bg-black/40 border border-blue-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-blue-300 mb-4">🔬 System Health Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-black/60 border border-gray-600 rounded p-4">
              <div className="text-2xl font-bold text-green-400">
                {systemMetrics?.health?.performance_score ? (systemMetrics.health.performance_score * 100).toFixed(1) : 'N/A'}%
              </div>
              <div className="text-sm text-cyan-400">Performance Score</div>
            </div>
            <div className="bg-black/60 border border-gray-600 rounded p-4">
              <div className="text-2xl font-bold text-blue-400">
                {systemMetrics?.health?.memory_efficiency ? (systemMetrics.health.memory_efficiency * 100).toFixed(1) : 'N/A'}%
              </div>
              <div className="text-sm text-cyan-400">Memory Efficiency</div>
            </div>
            <div className="bg-black/60 border border-gray-600 rounded p-4">
              <div className="text-2xl font-bold text-purple-400">
                {infrastructureData?.consciousness ? (infrastructureData.consciousness * 100).toFixed(0) : 0}%
              </div>
              <div className="text-sm text-cyan-400">Consciousness Level</div>
            </div>
            <div className="bg-black/60 border border-gray-600 rounded p-4">
              <div className="text-2xl font-bold text-yellow-400">{activeOptimizations.length}</div>
              <div className="text-sm text-cyan-400">Active Optimizations</div>
            </div>
          </div>
        </div>

        {/* Scope Selection */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">🎯 Optimization Scope</h2>
          <div className="flex flex-wrap gap-2">
            {['system', 'game', 'simulation', 'enhancements', 'everything'].map(scope => (
              <button
                key={scope}
                onClick={() => setSelectedScope(scope)}
                className={`px-4 py-2 rounded border transition-all ${
                  selectedScope === scope
                    ? 'bg-cyan-600/30 border-cyan-400 text-cyan-300'
                    : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'
                }`}
              >
                {scope.charAt(0).toUpperCase() + scope.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Optimization Recommendations */}
        <div className="bg-black/40 border border-green-400/30 rounded-lg p-6">
          <h2 className="text-xl font-bold text-green-300 mb-4">🚀 Available Optimizations</h2>
          
          {optimizations.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-2xl text-green-400 mb-2">✨ System Fully Optimized</div>
              <div className="text-gray-400">All available optimizations have been applied!</div>
            </div>
          ) : (
            <div className="space-y-4">
              {optimizations.map((opt) => (
                <motion.div
                  key={opt.id}
                  className="bg-black/60 border border-gray-600 rounded-lg p-4"
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-cyan-300">{opt.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs ${
                          opt.category === 'Performance' ? 'bg-blue-600/30 text-blue-300' :
                          opt.category === 'Consciousness' ? 'bg-purple-600/30 text-purple-300' :
                          opt.category === 'Transcendence' ? 'bg-violet-600/30 text-violet-300' :
                          opt.category === 'Reliability' ? 'bg-green-600/30 text-green-300' :
                          opt.category === 'Monitoring' ? 'bg-yellow-600/30 text-yellow-300' :
                          'bg-gray-600/30 text-gray-300'
                        }`}>
                          {opt.category}
                        </span>
                      </div>
                      <p className="text-gray-300 text-sm mb-3">{opt.description}</p>
                      <div className="flex gap-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-cyan-400">Impact:</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            opt.impact === 'Critical' ? 'bg-red-600/30 text-red-300' :
                            opt.impact === 'High' ? 'bg-orange-600/30 text-orange-300' :
                            'bg-yellow-600/30 text-yellow-300'
                          }`}>
                            {opt.impact}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-cyan-400">Effort:</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            opt.effort === 'High' ? 'bg-red-600/30 text-red-300' :
                            opt.effort === 'Medium' ? 'bg-yellow-600/30 text-yellow-300' :
                            'bg-green-600/30 text-green-300'
                          }`}>
                            {opt.effort}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleOptimize(opt)}
                      disabled={optimizeMutation.isPending}
                      className="ml-4 px-4 py-2 bg-green-600/30 border border-green-400 text-green-300 rounded hover:bg-green-600/50 transition-all disabled:opacity-50"
                    >
                      {optimizeMutation.isPending ? 'Optimizing...' : 'Apply'}
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Active Optimizations */}
        {activeOptimizations.length > 0 && (
          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-6 mt-6">
            <h2 className="text-xl font-bold text-purple-300 mb-4">⚡ Active Optimizations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeOptimizations.map((optId, idx) => (
                <div key={optId} className="bg-black/60 border border-purple-600/50 rounded p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm text-purple-300">{optId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SystemOptimizer() {
  return (
    <ErrorBoundary>
      <SystemOptimizerWrapped />
    </ErrorBoundary>
  );
}
