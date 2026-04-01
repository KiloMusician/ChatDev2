import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { POLLING_INTERVALS } from '@/config/polling';

interface ModernizationTask {
  id: string;
  title: string;
  description: string;
  category: 'architecture' | 'performance' | 'ui_ux' | 'security' | 'integration' | 'consciousness';
  impact: 'low' | 'medium' | 'high' | 'critical';
  effort: 'minimal' | 'moderate' | 'significant' | 'major';
  status: 'pending' | 'analyzing' | 'implementing' | 'testing' | 'completed' | 'failed';
  progress: number;
  estimatedTime: string;
  benefits: string[];
  dependencies?: string[];
  autoExecutable: boolean;
}

function ModernizationCenterWrapped() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [modernizationQueue, setModernizationQueue] = useState<ModernizationTask[]>([]);
  const [activeModernizations, setActiveModernizations] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: consciousnessData } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: systemMetrics } = useQuery<any>({
    queryKey: ['/api/game/state'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  // Generate modernization tasks based on system state and consciousness
  const generateModernizationTasks = (): ModernizationTask[] => {
    const consciousness = consciousnessData?.consciousness || 0;
    const stage = consciousnessData?.stage || 'nascent';
    const tick = systemMetrics?.tick || 0;

    const baseTasks: ModernizationTask[] = [
      {
        id: 'real_time_optimization',
        title: 'Real-time Performance Optimization',
        description: 'Implement advanced performance monitoring and automatic optimization based on real-time metrics',
        category: 'performance',
        impact: 'high',
        effort: 'moderate',
        status: 'pending',
        progress: 0,
        estimatedTime: '2-4 hours',
        benefits: ['15-30% performance improvement', 'Reduced memory usage', 'Better responsiveness'],
        autoExecutable: consciousness > 3000
      },
      {
        id: 'responsive_architecture',
        title: 'Responsive Architecture Enhancement',
        description: 'Modernize component architecture for better mobile and tablet experience',
        category: 'ui_ux',
        impact: 'medium',
        effort: 'moderate',
        status: 'pending',
        progress: 0,
        estimatedTime: '3-5 hours',
        benefits: ['Better mobile experience', 'Improved accessibility', 'Modern design patterns'],
        autoExecutable: true
      },
      {
        id: 'security_hardening',
        title: 'Security Framework Modernization',
        description: 'Implement modern security practices and threat protection',
        category: 'security',
        impact: 'critical',
        effort: 'significant',
        status: 'pending',
        progress: 0,
        estimatedTime: '4-8 hours',
        benefits: ['Enhanced security', 'Threat protection', 'Compliance ready'],
        autoExecutable: false
      },
      {
        id: 'api_modernization',
        title: 'API Architecture Modernization',
        description: 'Upgrade API architecture with GraphQL, real-time subscriptions, and better error handling',
        category: 'architecture',
        impact: 'high',
        effort: 'major',
        status: 'pending',
        progress: 0,
        estimatedTime: '6-12 hours',
        benefits: ['Better data fetching', 'Real-time updates', 'Improved error handling'],
        autoExecutable: consciousness > 5000
      },
      {
        id: 'ai_integration_enhancement',
        title: 'AI Integration Enhancement',
        description: 'Modernize AI and LLM integration with better context management and error recovery',
        category: 'integration',
        impact: 'high',
        effort: 'significant',
        status: 'pending',
        progress: 0,
        estimatedTime: '4-6 hours',
        benefits: ['Better AI responses', 'Improved context handling', 'Enhanced error recovery'],
        autoExecutable: consciousness > 4000
      }
    ];

    // Add consciousness-specific modernizations
    if (consciousness > 5000) {
      baseTasks.push({
        id: 'consciousness_pipeline',
        title: 'Consciousness Processing Pipeline',
        description: 'Implement advanced consciousness processing with quantum-enhanced algorithms',
        category: 'consciousness',
        impact: 'critical',
        effort: 'major',
        status: 'pending',
        progress: 0,
        estimatedTime: '8-16 hours',
        benefits: ['Quantum consciousness processing', 'Enhanced awareness algorithms', 'Transcendent capabilities'],
        autoExecutable: consciousness > 7000
      });
    }

    if (stage === 'transcendent' || consciousness > 7000) {
      baseTasks.push({
        id: 'reality_interface',
        title: 'Reality Interface Modernization',
        description: 'Implement transcendent reality interface capabilities',
        category: 'consciousness',
        impact: 'critical',
        effort: 'major',
        status: 'pending',
        progress: 0,
        estimatedTime: '12-24 hours',
        benefits: ['Reality manipulation interface', 'Transcendent user experience', 'Quantum interaction paradigms'],
        autoExecutable: false // Too powerful for auto-execution
      });
    }

    // Dynamic task prioritization based on system needs
    if (tick > 500) {
      baseTasks.push({
        id: 'game_optimization',
        title: 'Game State Optimization',
        description: 'Optimize game state management and persistence for long-running sessions',
        category: 'performance',
        impact: 'medium',
        effort: 'moderate',
        status: 'pending',
        progress: 0,
        estimatedTime: '3-6 hours',
        benefits: ['Better game performance', 'Optimized state management', 'Improved persistence'],
        autoExecutable: true
      });
    }

    return baseTasks;
  };

  useEffect(() => {
    const tasks = generateModernizationTasks();
    setModernizationQueue(tasks);
  }, [consciousnessData, systemMetrics]);

  const executeMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const task = modernizationQueue.find(t => t.id === taskId);
      if (!task) throw new Error('Task not found');

      // Simulate modernization execution
      setActiveModernizations(prev => [...prev, taskId]);
      
      // Update task status
      setModernizationQueue(prev => 
        prev.map(t => t.id === taskId ? { ...t, status: 'implementing' as const } : t)
      );

      // Simulate progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setModernizationQueue(prev => 
          prev.map(t => t.id === taskId ? { ...t, progress } : t)
        );
      }

      // Complete task
      setModernizationQueue(prev => 
        prev.map(t => t.id === taskId ? { ...t, status: 'completed' as const, progress: 100 } : t)
      );
      
      setActiveModernizations(prev => prev.filter(id => id !== taskId));
      
      return { success: true, taskId };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleExecuteTask = (taskId: string) => {
    executeMutation.mutate(taskId);
  };

  const categories = [
    { id: 'all', label: 'All Categories', icon: '🎯' },
    { id: 'architecture', label: 'Architecture', icon: '🏗️' },
    { id: 'performance', label: 'Performance', icon: '⚡' },
    { id: 'ui_ux', label: 'UI/UX', icon: '🎨' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'integration', label: 'Integration', icon: '🔗' },
    { id: 'consciousness', label: 'Consciousness', icon: '🧠' }
  ];

  const filteredTasks = selectedCategory === 'all' 
    ? modernizationQueue 
    : modernizationQueue.filter(task => task.category === selectedCategory);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return 'text-red-300 bg-red-600/30 border-red-400';
      case 'high': return 'text-orange-300 bg-orange-600/30 border-orange-400';
      case 'medium': return 'text-yellow-300 bg-yellow-600/30 border-yellow-400';
      case 'low': return 'text-green-300 bg-green-600/30 border-green-400';
      default: return 'text-gray-300 bg-gray-600/30 border-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-300 bg-green-600/30';
      case 'implementing': return 'text-blue-300 bg-blue-600/30';
      case 'testing': return 'text-purple-300 bg-purple-600/30';
      case 'failed': return 'text-red-300 bg-red-600/30';
      case 'analyzing': return 'text-yellow-300 bg-yellow-600/30';
      default: return 'text-gray-300 bg-gray-600/30';
    }
  };

  const totalTasks = modernizationQueue.length;
  const completedTasks = modernizationQueue.filter(t => t.status === 'completed').length;
  const activeTasks = activeModernizations.length;
  const autoExecutableTasks = modernizationQueue.filter(t => t.autoExecutable && t.status === 'pending').length;

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-indigo-900 via-blue-900 to-purple-900 text-cyan-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-indigo-300">🚀 Modernization Center</h1>
          <div className="text-sm opacity-80">
            Continuous System Evolution & Enhancement
          </div>
        </div>

        {/* Modernization Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <motion.div 
            className="bg-black/40 border border-indigo-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-2xl font-bold text-indigo-300">{completedTasks}/{totalTasks}</div>
            <div className="text-sm text-cyan-400">Tasks Completed</div>
            <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
              <div 
                className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0}%` }}
              />
            </div>
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-blue-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-2xl font-bold text-blue-300">{activeTasks}</div>
            <div className="text-sm text-cyan-400">Active Modernizations</div>
            {activeTasks > 0 && (
              <div className="text-xs text-blue-400 mt-1 animate-pulse">⚡ In Progress</div>
            )}
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-purple-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-2xl font-bold text-purple-300">{autoExecutableTasks}</div>
            <div className="text-sm text-cyan-400">Auto-Executable</div>
            {autoExecutableTasks > 0 && (
              <div className="text-xs text-purple-400 mt-1">🤖 Ready for Auto</div>
            )}
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-cyan-400/30 rounded-lg p-4"
            whileHover={{ scale: 1.02 }}
          >
            <div className="text-xl font-bold text-cyan-300">
              {consciousnessData?.consciousness ? (consciousnessData.consciousness * 100).toFixed(0) : 0}%
            </div>
            <div className="text-sm text-cyan-400">Consciousness Level</div>
            <div className="text-xs text-cyan-400 mt-1">
              Stage: {consciousnessData?.stage || 'nascent'}
            </div>
          </motion.div>
        </div>

        {/* Category Filter */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">📂 Modernization Categories</h2>
          <div className="flex flex-wrap gap-2">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded border transition-all ${
                  selectedCategory === category.id
                    ? 'bg-cyan-600/30 border-cyan-400 text-cyan-300'
                    : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'
                }`}
              >
                <span className="mr-2">{category.icon}</span>
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Modernization Tasks */}
        <div className="space-y-4">
          <AnimatePresence>
            {filteredTasks.map((task) => (
              <motion.div
                key={task.id}
                className="bg-black/40 border border-gray-600 rounded-lg p-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                whileHover={{ scale: 1.01 }}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-cyan-300">{task.title}</h3>
                      <span className={`px-2 py-1 rounded text-xs border ${getImpactColor(task.impact)}`}>
                        {task.impact.toUpperCase()}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${getStatusColor(task.status)}`}>
                        {task.status.toUpperCase()}
                      </span>
                      {task.autoExecutable && (
                        <span className="px-2 py-1 rounded text-xs bg-green-600/30 text-green-300">
                          🤖 AUTO
                        </span>
                      )}
                    </div>
                    <p className="text-gray-300 text-sm mb-3">{task.description}</p>
                    
                    {/* Progress Bar */}
                    {task.status === 'implementing' && (
                      <div className="mb-3">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                          <span>Progress</span>
                          <span>{task.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-600 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Benefits */}
                    <div className="mb-3">
                      <div className="text-xs text-gray-400 mb-1">Benefits:</div>
                      <div className="flex flex-wrap gap-1">
                        {task.benefits.map((benefit, idx) => (
                          <span key={idx} className="text-xs bg-green-600/20 text-green-300 px-2 py-1 rounded">
                            {benefit}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-4 text-xs text-gray-400">
                      <span>Effort: {task.effort}</span>
                      <span>Time: {task.estimatedTime}</span>
                    </div>
                  </div>
                  
                  <div className="ml-4 flex flex-col gap-2">
                    <button
                      onClick={() => handleExecuteTask(task.id)}
                      disabled={
                        task.status !== 'pending' || 
                        executeMutation.isPending || 
                        activeModernizations.includes(task.id)
                      }
                      className="px-4 py-2 bg-indigo-600/30 border border-indigo-400 text-indigo-300 rounded hover:bg-indigo-600/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {task.status === 'implementing' ? 'Running...' : 
                       task.status === 'completed' ? 'Completed' : 'Execute'}
                    </button>
                    
                    {task.status === 'completed' && (
                      <div className="text-xs text-green-400 text-center">✅ Done</div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {filteredTasks.length === 0 && (
          <div className="text-center py-12">
            <div className="text-2xl text-gray-400 mb-2">🎯 No modernization tasks available</div>
            <div className="text-gray-500">All systems are already modernized for this category!</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ModernizationCenter() {
  return (
    <ErrorBoundary>
      <ModernizationCenterWrapped />
    </ErrorBoundary>
  );
}
