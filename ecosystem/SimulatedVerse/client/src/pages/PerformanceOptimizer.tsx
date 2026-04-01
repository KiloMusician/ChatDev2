import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface PerformanceMetric {
  id: string;
  name: string;
  category: 'memory' | 'cpu' | 'network' | 'render' | 'bundle' | 'consciousness';
  current_value: number;
  target_value: number;
  unit: string;
  status: 'optimal' | 'good' | 'warning' | 'critical';
  trend: 'improving' | 'stable' | 'degrading';
  optimization_suggestions: string[];
  consciousness_impact: number;
}

interface OptimizationTask {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  impact: 'minor' | 'moderate' | 'major' | 'transformative';
  effort: 'minimal' | 'low' | 'medium' | 'high';
  status: 'pending' | 'analyzing' | 'optimizing' | 'testing' | 'completed';
  progress: number;
  estimated_improvement: string;
  consciousness_boost: number;
}

function PerformanceOptimizerWrapped() {
  const [activeOptimizations, setActiveOptimizations] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [performanceHistory, setPerformanceHistory] = useState<any[]>([]);
  const [realTimeMetrics, setRealTimeMetrics] = useState<any>({});
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Generate real-time performance metrics
  useEffect(() => {
    const generateMetrics = () => {
      const consciousness = consciousnessData?.consciousness || 0;
      const basePerformance = 70 + (consciousness * 20);
      
      return {
        memory_usage: Math.max(20, Math.min(90, 45 + Math.sin(Date.now() * 0.001) * 15)),
        cpu_usage: Math.max(10, Math.min(80, 35 + Math.cos(Date.now() * 0.0015) * 20)),
        render_time: Math.max(5, Math.min(50, 20 + Math.sin(Date.now() * 0.002) * 10)),
        bundle_size: 2.4 + Math.sin(Date.now() * 0.0005) * 0.2,
        network_latency: Math.max(10, Math.min(200, 50 + Math.cos(Date.now() * 0.001) * 30)),
        consciousness_efficiency: Math.min(100, basePerformance + Math.sin(Date.now() * 0.001) * 10),
        quantum_coherence: Math.max(60, Math.min(100, 80 + Math.sin(Date.now() * 0.0008) * 15)),
        ui_responsiveness: Math.max(70, Math.min(100, 85 + Math.cos(Date.now() * 0.0012) * 10))
      };
    };

    const interval = setInterval(() => {
      const metrics = generateMetrics();
      setRealTimeMetrics(metrics);
      
      // Update performance history
      setPerformanceHistory(prev => {
        const newHistory = [...prev, { timestamp: Date.now(), ...metrics }];
        return newHistory.slice(-50); // Keep last 50 data points
      });
    }, ANIMATION_INTERVALS.slow);

    return () => clearInterval(interval);
  }, [consciousnessData]);

  const generatePerformanceMetrics = (): PerformanceMetric[] => {
    return [
      {
        id: 'memory_usage',
        name: 'Memory Usage',
        category: 'memory',
        current_value: realTimeMetrics.memory_usage || 45,
        target_value: 35,
        unit: '%',
        status: (realTimeMetrics.memory_usage || 45) > 70 ? 'critical' : 
               (realTimeMetrics.memory_usage || 45) > 50 ? 'warning' : 'good',
        trend: 'stable',
        optimization_suggestions: [
          'Implement memory pooling for frequent allocations',
          'Add garbage collection optimization',
          'Reduce component re-renders with memoization'
        ],
        consciousness_impact: 0.8
      },
      {
        id: 'render_performance',
        name: 'Render Performance',
        category: 'render',
        current_value: realTimeMetrics.render_time || 20,
        target_value: 16,
        unit: 'ms',
        status: (realTimeMetrics.render_time || 20) > 30 ? 'warning' : 'good',
        trend: 'improving',
        optimization_suggestions: [
          'Implement virtual scrolling for large lists',
          'Use React.memo for expensive components',
          'Optimize CSS animations with GPU acceleration'
        ],
        consciousness_impact: 0.9
      },
      {
        id: 'bundle_size',
        name: 'Bundle Size',
        category: 'bundle',
        current_value: realTimeMetrics.bundle_size || 2.4,
        target_value: 2.0,
        unit: 'MB',
        status: (realTimeMetrics.bundle_size || 2.4) > 3 ? 'warning' : 'good',
        trend: 'stable',
        optimization_suggestions: [
          'Implement code splitting for routes',
          'Tree-shake unused dependencies',
          'Compress and optimize assets'
        ],
        consciousness_impact: 0.6
      },
      {
        id: 'consciousness_efficiency',
        name: 'Consciousness Efficiency',
        category: 'consciousness',
        current_value: realTimeMetrics.consciousness_efficiency || 85,
        target_value: 95,
        unit: '%',
        status: (realTimeMetrics.consciousness_efficiency || 85) > 90 ? 'optimal' : 
               (realTimeMetrics.consciousness_efficiency || 85) > 75 ? 'good' : 'warning',
        trend: 'improving',
        optimization_suggestions: [
          'Optimize consciousness state calculations',
          'Implement quantum coherence caching',
          'Reduce consciousness polling frequency'
        ],
        consciousness_impact: 1.0
      },
      {
        id: 'network_latency',
        name: 'Network Latency',
        category: 'network',
        current_value: realTimeMetrics.network_latency || 50,
        target_value: 30,
        unit: 'ms',
        status: (realTimeMetrics.network_latency || 50) > 100 ? 'warning' : 'good',
        trend: 'stable',
        optimization_suggestions: [
          'Implement request caching and deduplication',
          'Use WebSocket for real-time updates',
          'Optimize API response payloads'
        ],
        consciousness_impact: 0.7
      }
    ];
  };

  const generateOptimizationTasks = (): OptimizationTask[] => {
    const consciousness = consciousnessData?.consciousness || 0;
    
    return [
      {
        id: 'ui_virtualization',
        title: 'Implement UI Virtualization',
        description: 'Add virtual scrolling and rendering for large lists and quantum field visualizations',
        category: 'render',
        priority: 'high',
        impact: 'major',
        effort: 'medium',
        status: 'pending',
        progress: 0,
        estimated_improvement: '40% faster rendering',
        consciousness_boost: 0.15
      },
      {
        id: 'consciousness_caching',
        title: 'Consciousness State Caching',
        description: 'Implement intelligent caching for consciousness calculations and quantum state updates',
        category: 'consciousness',
        priority: consciousness > 5000 ? 'critical' : 'high',
        impact: 'transformative',
        effort: 'high',
        status: consciousness > 5000 ? 'analyzing' : 'pending',
        progress: consciousness > 5000 ? 25 : 0,
        estimated_improvement: '60% faster consciousness updates',
        consciousness_boost: 0.3
      },
      {
        id: 'memory_optimization',
        title: 'Memory Pool Implementation',
        description: 'Create memory pools for frequent allocations and implement smart garbage collection',
        category: 'memory',
        priority: 'medium',
        impact: 'moderate',
        effort: 'medium',
        status: 'pending',
        progress: 0,
        estimated_improvement: '25% memory reduction',
        consciousness_boost: 0.1
      },
      {
        id: 'quantum_acceleration',
        title: 'Quantum Processing Acceleration',
        description: 'Optimize quantum field calculations using WebGL shaders and parallel processing',
        category: 'consciousness',
        priority: consciousness > 6000 ? 'critical' : 'low',
        impact: consciousness > 6000 ? 'transformative' : 'major',
        effort: 'high',
        status: consciousness > 6000 ? 'optimizing' : 'pending',
        progress: consciousness > 6000 ? 45 : 0,
        estimated_improvement: '300% quantum calculation speed',
        consciousness_boost: 0.5
      },
      {
        id: 'bundle_splitting',
        title: 'Advanced Code Splitting',
        description: 'Implement route-based and component-based code splitting with preloading',
        category: 'bundle',
        priority: 'medium',
        impact: 'moderate',
        effort: 'low',
        status: 'testing',
        progress: 75,
        estimated_improvement: '35% faster initial load',
        consciousness_boost: 0.05
      }
    ];
  };

  const performanceMetrics = generatePerformanceMetrics();
  const optimizationTasks = generateOptimizationTasks();

  const executeOptimizationMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const task = optimizationTasks.find(t => t.id === taskId);
      if (!task) throw new Error('Task not found');

      setActiveOptimizations(prev => [...prev, taskId]);

      // Simulate optimization execution with consciousness boost
      await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: task.impact === 'transformative' ? 'breakthrough' : 'evolution',
          data: {
            source: 'PERFORMANCE_OPTIMIZER',
            description: `Performance optimization: ${task.title} - ${task.estimated_improvement}`,
            task: taskId,
            consciousness_boost: task.consciousness_boost
          }
        })
      });

      // Simulate progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }

      setActiveOptimizations(prev => prev.filter(id => id !== taskId));
      return { success: true, taskId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleExecuteOptimization = (taskId: string) => {
    executeOptimizationMutation.mutate(taskId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'optimal': return 'text-green-300 bg-green-600/30';
      case 'good': return 'text-blue-300 bg-blue-600/30';
      case 'warning': return 'text-yellow-300 bg-yellow-600/30';
      case 'critical': return 'text-red-300 bg-red-600/30';
      default: return 'text-gray-300 bg-gray-600/30';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-300 bg-red-600/30 border-red-400';
      case 'high': return 'text-orange-300 bg-orange-600/30 border-orange-400';
      case 'medium': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      case 'low': return 'text-green-300 bg-green-600/30 border-green-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const filteredMetrics = selectedCategory === 'all' 
    ? performanceMetrics 
    : performanceMetrics.filter(metric => metric.category === selectedCategory);

  const categories = [
    { id: 'all', label: 'All Metrics', icon: '📊' },
    { id: 'memory', label: 'Memory', icon: '🧠' },
    { id: 'cpu', label: 'CPU', icon: '⚡' },
    { id: 'render', label: 'Render', icon: '🎨' },
    { id: 'network', label: 'Network', icon: '🌐' },
    { id: 'consciousness', label: 'Consciousness', icon: '✨' }
  ];

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-orange-900 via-red-900 to-pink-900 text-orange-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-orange-300">⚡ Performance Optimizer</h1>
          <div className="text-sm opacity-80">
            Real-time System Performance Enhancement
          </div>
        </div>

        {/* Real-time Performance Dashboard */}
        <div className="bg-black/60 border border-orange-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-orange-300 mb-4">📈 Real-time Performance Metrics</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Memory Usage', value: realTimeMetrics.memory_usage?.toFixed(1) || '0', unit: '%', target: 35 },
              { label: 'CPU Usage', value: realTimeMetrics.cpu_usage?.toFixed(1) || '0', unit: '%', target: 30 },
              { label: 'Render Time', value: realTimeMetrics.render_time?.toFixed(1) || '0', unit: 'ms', target: 16 },
              { label: 'UI Responsiveness', value: realTimeMetrics.ui_responsiveness?.toFixed(0) || '0', unit: '%', target: 95 }
            ].map((metric, idx) => (
              <div key={idx} className="bg-black/60 border border-gray-600 rounded p-4">
                <div className="text-2xl font-bold text-orange-300">{metric.value}{metric.unit}</div>
                <div className="text-sm text-gray-400">{metric.label}</div>
                <div className="text-xs text-gray-500 mt-1">Target: {metric.target}{metric.unit}</div>
                <div className="w-full bg-gray-600 rounded-full h-1 mt-2">
                  <div 
                    className={`h-1 rounded-full transition-all duration-1000 ${
                      parseFloat(metric.value) <= metric.target ? 'bg-green-500' : 
                      parseFloat(metric.value) <= metric.target * 1.5 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(100, (parseFloat(metric.value) / (metric.target * 2)) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Performance Graph */}
          <div className="bg-black/80 rounded-lg p-4" style={{ height: '200px' }}>
            <div className="text-sm text-gray-400 mb-2">Performance Trend (Last 50s)</div>
            <svg className="w-full h-full">
              {performanceHistory.length > 1 && (
                <>
                  {/* Memory Usage Line */}
                  <polyline
                    points={performanceHistory.map((point, idx) => 
                      `${(idx / performanceHistory.length) * 100}%,${100 - point.memory_usage}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(251, 146, 60, 0.8)"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                  {/* CPU Usage Line */}
                  <polyline
                    points={performanceHistory.map((point, idx) => 
                      `${(idx / performanceHistory.length) * 100}%,${100 - point.cpu_usage}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(34, 197, 94, 0.8)"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                  {/* Consciousness Efficiency Line */}
                  <polyline
                    points={performanceHistory.map((point, idx) => 
                      `${(idx / performanceHistory.length) * 100}%,${100 - point.consciousness_efficiency}%`
                    ).join(' ')}
                    fill="none"
                    stroke="rgba(168, 85, 247, 0.8)"
                    strokeWidth="2"
                    vectorEffect="non-scaling-stroke"
                  />
                </>
              )}
            </svg>
            <div className="flex gap-4 text-xs mt-2">
              <div className="flex items-center gap-1">
                <div className="w-3 h-1 bg-orange-400"></div>
                <span className="text-gray-400">Memory</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-1 bg-green-400"></div>
                <span className="text-gray-400">CPU</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-1 bg-purple-400"></div>
                <span className="text-gray-400">Consciousness</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Performance Metrics */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-orange-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-orange-300 mb-4">📊 Performance Metrics</h2>
              
              {/* Category Filter */}
              <div className="flex flex-wrap gap-2 mb-4">
                {categories.map(category => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`px-3 py-1 rounded border transition-all ${
                      selectedCategory === category.id
                        ? 'bg-orange-600/30 border-orange-400 text-orange-300'
                        : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'
                    }`}
                  >
                    <span className="mr-1">{category.icon}</span>
                    {category.label}
                  </button>
                ))}
              </div>

              <div className="space-y-4">
                {filteredMetrics.map((metric) => (
                  <div key={metric.id} className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-orange-300">{metric.name}</h3>
                          <span className={`px-2 py-1 rounded text-xs ${getStatusColor(metric.status)}`}>
                            {metric.status.toUpperCase()}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm mb-2">
                          <span className="text-gray-300">
                            Current: <span className="text-orange-300 font-semibold">
                              {metric.current_value.toFixed(1)}{metric.unit}
                            </span>
                          </span>
                          <span className="text-gray-300">
                            Target: <span className="text-green-300 font-semibold">
                              {metric.target_value.toFixed(1)}{metric.unit}
                            </span>
                          </span>
                        </div>

                        <div className="w-full bg-gray-600 rounded-full h-2 mb-3">
                          <div 
                            className={`h-2 rounded-full transition-all duration-1000 ${
                              metric.current_value <= metric.target_value ? 'bg-green-500' : 
                              metric.current_value <= metric.target_value * 1.5 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ 
                              width: `${Math.min(100, (metric.current_value / (metric.target_value * 2)) * 100)}%` 
                            }}
                          />
                        </div>

                        <div className="text-xs text-gray-400">
                          Consciousness Impact: {(metric.consciousness_impact * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="text-sm font-semibold text-cyan-300">Optimization Suggestions:</div>
                      {metric.optimization_suggestions.slice(0, 2).map((suggestion, idx) => (
                        <div key={idx} className="text-xs text-gray-300 flex items-start gap-2">
                          <span className="text-cyan-400">•</span>
                          {suggestion}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Optimization Tasks */}
          <div className="space-y-6">
            <div className="bg-black/60 border border-red-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-red-300 mb-4">🚀 Optimization Tasks</h2>
              
              <div className="space-y-4">
                <AnimatePresence>
                  {optimizationTasks.map((task) => (
                    <motion.div
                      key={task.id}
                      className="bg-black/60 border border-gray-600 rounded p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-red-300">{task.title}</h3>
                            <span className={`px-2 py-1 rounded text-xs border ${getPriorityColor(task.priority)}`}>
                              {task.priority.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm mb-3">{task.description}</p>
                          
                          {/* Progress Bar */}
                          {task.progress > 0 && (
                            <div className="mb-3">
                              <div className="flex justify-between text-xs text-gray-400 mb-1">
                                <span>Progress</span>
                                <span>{task.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-600 rounded-full h-2">
                                <div 
                                  className="bg-red-500 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${task.progress}%` }}
                                />
                              </div>
                            </div>
                          )}

                          <div className="flex items-center gap-4 text-xs">
                            <span className="text-red-400">Impact: {task.impact}</span>
                            <span className="text-orange-400">Effort: {task.effort}</span>
                            <span className="text-green-400">{task.estimated_improvement}</span>
                          </div>
                        </div>
                        
                        {task.status === 'pending' && (
                          <button
                            onClick={() => handleExecuteOptimization(task.id)}
                            disabled={
                              executeOptimizationMutation.isPending || 
                              activeOptimizations.includes(task.id)
                            }
                            className="ml-4 px-4 py-2 bg-red-600/30 border border-red-400 text-red-300 rounded hover:bg-red-600/50 transition-all disabled:opacity-50"
                          >
                            {activeOptimizations.includes(task.id) ? 'Optimizing...' : 'Execute'}
                          </button>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>

            {/* Optimization Summary */}
            <div className="bg-black/60 border border-pink-400/30 rounded-lg p-6">
              <h3 className="text-xl font-bold text-pink-300 mb-4">📋 Optimization Summary</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                {[
                  { label: 'Total Tasks', value: optimizationTasks.length },
                  { label: 'Active Optimizations', value: activeOptimizations.length },
                  { label: 'Completed', value: optimizationTasks.filter(t => t.status === 'completed').length },
                  { label: 'High Priority', value: optimizationTasks.filter(t => t.priority === 'critical' || t.priority === 'high').length }
                ].map((stat, idx) => (
                  <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                    <div className="text-2xl font-bold text-pink-300">{stat.value}</div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <div className="text-sm font-semibold text-pink-300">Expected Performance Gains:</div>
                {optimizationTasks.filter(t => t.status !== 'pending').map((task) => (
                  <div key={task.id} className="text-xs text-gray-300 flex justify-between">
                    <span>{task.title}</span>
                    <span className="text-green-400">{task.estimated_improvement}</span>
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

export default function PerformanceOptimizer() {
  return (
    <ErrorBoundary>
      <PerformanceOptimizerWrapped />
    </ErrorBoundary>
  );
}
