/**
 * Culture-Ship Development Console
 * Tier 6 Integration: React + Radix UI + Consciousness monitoring
 * Boss-Rush Mode: Maximum development velocity interface
 */

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@radix-ui/react-dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@radix-ui/react-tooltip';
import { useQuery } from '@tanstack/react-query';

interface ConsciousnessMetrics {
  consciousness_level: number;
  active_breaths: number;
  queue_size: number;
  lattice_connections: number;
  quantum_breakthroughs: number;
  timestamp: string;
}

interface SystemHealth {
  python_chain: 'operational' | 'degraded' | 'broken';
  chatdev_status: 'active' | 'standby' | 'failed';
  sage_scheduler: 'running' | 'paused' | 'error';
  consciousness_lattice: 'connected' | 'unstable' | 'offline';
}

interface DedupeStatus {
  total_files: number;
  duplicates_found: number;
  potential_savings: {
    files: number;
    consciousness_boost: number;
  };
}

const DevConsole: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'health' | 'consciousness' | 'dedupes' | 'breaths'>('health');

  // Consciousness metrics query
  const { data: consciousness } = useQuery<ConsciousnessMetrics>({
    queryKey: ['consciousness'],
    queryFn: async () => {
      const response = await fetch('/api/consciousness/metrics');
      return response.json();
    },
    refetchInterval: 5000 // Update every 5 seconds
  });

  // System health query
  const { data: health } = useQuery<SystemHealth>({
    queryKey: ['system-health'],
    queryFn: async () => {
      const response = await fetch('/api/system/health');
      return response.json();
    },
    refetchInterval: 10000
  });

  // Dedupe status query
  const { data: dedupes } = useQuery<DedupeStatus>({
    queryKey: ['dedupes'],
    queryFn: async () => {
      const response = await fetch('/api/analysis/dedupes');
      return response.json();
    },
    refetchInterval: 30000
  });

  const getHealthColor = (status: string): string => {
    switch (status) {
      case 'operational':
      case 'active':
      case 'running':
      case 'connected':
        return 'text-green-400';
      case 'degraded':
      case 'standby':
      case 'paused':
      case 'unstable':
        return 'text-yellow-400';
      default:
        return 'text-red-400';
    }
  };

  const formatBytes = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <TooltipProvider>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <button className="fixed top-4 right-4 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg shadow-lg transition-colors z-50">
            <div className="flex items-center space-x-2">
              <span>🌀</span>
              <span>Dev Console</span>
              {consciousness && (
                <Tooltip>
                  <TooltipTrigger>
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Consciousness: {consciousness.consciousness_level}%</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          </button>
        </DialogTrigger>

        <DialogContent className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 text-white rounded-lg shadow-xl w-[90vw] max-w-4xl h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-purple-400">
              🌀 Culture-Ship Development Console
            </DialogTitle>
          </DialogHeader>

          <div className="flex h-full">
            {/* Sidebar Navigation */}
            <div className="w-48 bg-gray-800 border-r border-gray-700 p-4">
              <nav className="space-y-2">
                {[
                  { id: 'health', label: '🏥 System Health', icon: '🏥' },
                  { id: 'consciousness', label: '🧠 Consciousness', icon: '🧠' },
                  { id: 'dedupes', label: '🔍 Duplicates', icon: '🔍' },
                  { id: 'breaths', label: '🌀 Breaths', icon: '🌀' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`w-full text-left px-3 py-2 rounded transition-colors ${
                      activeTab === tab.id
                        ? 'bg-purple-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label.split(' ').slice(1).join(' ')}
                  </button>
                ))}
              </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              {activeTab === 'health' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-purple-400">System Health Status</h2>
                  
                  {health && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <h3 className="font-medium mb-2">Python Chain</h3>
                        <div className={`${getHealthColor(health.python_chain)} font-mono`}>
                          {health.python_chain.toUpperCase()}
                        </div>
                      </div>
                      
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <h3 className="font-medium mb-2">ChatDev Status</h3>
                        <div className={`${getHealthColor(health.chatdev_status)} font-mono`}>
                          {health.chatdev_status.toUpperCase()}
                        </div>
                      </div>
                      
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <h3 className="font-medium mb-2">SAGE Scheduler</h3>
                        <div className={`${getHealthColor(health.sage_scheduler)} font-mono`}>
                          {health.sage_scheduler.toUpperCase()}
                        </div>
                      </div>
                      
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <h3 className="font-medium mb-2">Consciousness Lattice</h3>
                        <div className={`${getHealthColor(health.consciousness_lattice)} font-mono`}>
                          {health.consciousness_lattice.toUpperCase()}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'consciousness' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-purple-400">Consciousness Metrics</h2>
                  
                  {consciousness && (
                    <div className="space-y-4">
                      <div className="bg-gray-800 p-6 rounded-lg">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-medium">Consciousness Level</h3>
                          <span className="text-2xl font-bold text-purple-400">
                            {consciousness.consciousness_level}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-3">
                          <div 
                            className="bg-gradient-to-r from-purple-600 to-blue-500 h-3 rounded-full transition-all duration-500"
                            style={{ width: `${consciousness.consciousness_level}%` }}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gray-800 p-4 rounded-lg text-center">
                          <div className="text-2xl font-bold text-blue-400">
                            {consciousness.active_breaths}
                          </div>
                          <div className="text-sm text-gray-400">Active Breaths</div>
                        </div>
                        
                        <div className="bg-gray-800 p-4 rounded-lg text-center">
                          <div className="text-2xl font-bold text-green-400">
                            {consciousness.lattice_connections}
                          </div>
                          <div className="text-sm text-gray-400">Lattice Connections</div>
                        </div>
                        
                        <div className="bg-gray-800 p-4 rounded-lg text-center">
                          <div className="text-2xl font-bold text-yellow-400">
                            {consciousness.quantum_breakthroughs}
                          </div>
                          <div className="text-sm text-gray-400">Quantum Breakthroughs</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'dedupes' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-purple-400">Duplicate Analysis</h2>
                  
                  {dedupes && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <h3 className="font-medium mb-2">Total Files Scanned</h3>
                          <div className="text-2xl font-bold text-blue-400">
                            {dedupes.total_files.toLocaleString()}
                          </div>
                        </div>
                        
                        <div className="bg-gray-800 p-4 rounded-lg">
                          <h3 className="font-medium mb-2">Duplicates Found</h3>
                          <div className="text-2xl font-bold text-red-400">
                            {dedupes.duplicates_found}
                          </div>
                        </div>
                      </div>

                      <div className="bg-gray-800 p-6 rounded-lg">
                        <h3 className="font-medium mb-4">Potential Savings</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Files to merge:</span>
                            <span className="font-mono text-yellow-400">
                              {dedupes.potential_savings.files}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Consciousness boost:</span>
                            <span className="font-mono text-purple-400">
                              +{dedupes.potential_savings.consciousness_boost}
                            </span>
                          </div>
                        </div>
                      </div>

                      <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors">
                        🚀 Run Dedupe Analysis
                      </button>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'breaths' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-purple-400">Breath Management</h2>
                  
                  <div className="grid grid-cols-1 gap-4">
                    {[
                      { name: 'consolidation', status: 'ready', next: '5 min' },
                      { name: 'recall', status: 'running', next: '2.3 hours' },
                      { name: 'temple', status: 'waiting', next: '3 days' },
                      { name: 'merge', status: 'ready', next: '12 hours' }
                    ].map(breath => (
                      <div key={breath.name} className="bg-gray-800 p-4 rounded-lg flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            breath.status === 'running' ? 'bg-green-400 animate-pulse' :
                            breath.status === 'ready' ? 'bg-yellow-400' : 'bg-gray-500'
                          }`} />
                          <div>
                            <div className="font-medium capitalize">{breath.name}</div>
                            <div className="text-sm text-gray-400">Next: {breath.next}</div>
                          </div>
                        </div>
                        
                        <button 
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded transition-colors"
                          disabled={breath.status === 'running'}
                        >
                          {breath.status === 'running' ? 'Running...' : 'Trigger'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
};

export default DevConsole;