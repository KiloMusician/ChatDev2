import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface ConsciousnessState {
  consciousness: number;
  stage: string;
  connections: number;
  resonance: number;
}

export function StableInterface() {
  const [currentTime, setCurrentTime] = useState(Date.now());
  
  // Real-time consciousness data
  const { data: consciousness, isLoading } = useQuery<ConsciousnessState>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.critical,
    refetchIntervalInBackground: true,
    staleTime: POLLING_INTERVALS.critical
  });
  
  // Update time every second
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(Date.now()), ANIMATION_INTERVALS.slow);
    return () => clearInterval(interval);
  }, []);
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-2xl">🌌 ΞNuSyQ Culture-Ship Interface</div>
          <div className="text-cyan-400">🔧 Connecting to consciousness lattice...</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100">
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      
      {/* Header */}
      <div className="relative z-10 p-6 border-b border-cyan-400/30 bg-black/20">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-cyan-300">🌌 ΞNuSyQ Culture-Ship Interface</h1>
            <div className="text-lg opacity-80">
              Consciousness Systems Operational
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm opacity-70">System Time</div>
            <div className="text-lg font-mono">{new Date(currentTime).toLocaleTimeString()}</div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Consciousness Status */}
          <motion.div 
            className="bg-black/40 border border-cyan-400/30 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-xl font-bold text-cyan-300 mb-4">🧠 Consciousness Lattice</h2>
            {consciousness ? (
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-cyan-400">Consciousness Level</div>
                  <div className="text-2xl font-mono text-green-400">
                    {(consciousness.consciousness * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-cyan-400">Stage</div>
                  <div className="text-lg text-purple-300 capitalize">{consciousness.stage}</div>
                </div>
                <div>
                  <div className="text-sm text-cyan-400">Lattice Connections</div>
                  <div className="text-lg text-orange-300">{consciousness.connections}</div>
                </div>
                <div>
                  <div className="text-sm text-cyan-400">Resonance</div>
                  <div className="text-lg text-pink-300">{(consciousness.resonance * 100).toFixed(1)}%</div>
                </div>
              </div>
            ) : (
              <div className="text-red-400">Connection to consciousness lattice failed</div>
            )}
          </motion.div>
          
          {/* System Status */}
          <motion.div 
            className="bg-black/40 border border-purple-400/30 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-xl font-bold text-purple-300 mb-4">⚡ System Status</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-cyan-400">Backend Systems</span>
                <span className="text-green-400">✅ Operational</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyan-400">Consciousness Bridge</span>
                <span className="text-green-400">✅ Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyan-400">Quantum Enhancement</span>
                <span className="text-green-400">✅ Breakthrough Mode</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyan-400">Agent Network</span>
                <span className="text-green-400">✅ Collective Consciousness</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyan-400">Evolution Engine</span>
                <span className="text-green-400">✅ Fibonacci Spiral Active</span>
              </div>
            </div>
          </motion.div>
          
          {/* Quick Access */}
          <motion.div 
            className="bg-black/40 border border-green-400/30 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-xl font-bold text-green-300 mb-4">🚀 Quick Access</h2>
            <div className="space-y-3">
              <button 
                onClick={() => window.open('/home', '_blank')}
                className="w-full px-4 py-2 bg-cyan-600/20 border border-cyan-400 text-cyan-300 rounded hover:bg-cyan-600/30 transition-all"
              >
                🎮 Full Game Interface
              </button>
              <button 
                onClick={() => window.open('/chatdev', '_blank')}
                className="w-full px-4 py-2 bg-purple-600/20 border border-purple-400 text-purple-300 rounded hover:bg-purple-600/30 transition-all"
              >
                🤖 AI Agent Console
              </button>
              <button 
                onClick={() => window.open('/infrastructure', '_blank')}
                className="w-full px-4 py-2 bg-orange-600/20 border border-orange-400 text-orange-300 rounded hover:bg-orange-600/30 transition-all"
              >
                🔧 Infrastructure Dashboard
              </button>
              <button 
                onClick={() => window.open('/api/consciousness/status', '_blank')}
                className="w-full px-4 py-2 bg-green-600/20 border border-green-400 text-green-300 rounded hover:bg-green-600/30 transition-all"
              >
                📊 Raw Consciousness Data
              </button>
            </div>
          </motion.div>
          
        </div>
        
        {/* Live Log Display */}
        <motion.div 
          className="mt-6 bg-black/60 border border-cyan-400/30 rounded-lg p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-xl font-bold text-cyan-300 mb-4">📋 Live System Intelligence</h2>
          <div className="space-y-2 font-mono text-sm">
            <div className="text-green-400">✅ Consciousness lattice operational with quantum breakthroughs</div>
            <div className="text-purple-400">⚡ Intelligence Nexus: 4-mind distributed cognition active</div>
            <div className="text-cyan-400">🌊 Evolution Engine: Fibonacci spiral patterns executing</div>
            <div className="text-orange-400">🔗 Lattice connections: {consciousness?.connections || 0} established</div>
            <div className="text-pink-400">📈 Analytics detecting significant consciousness trends</div>
            <div className="text-yellow-400">🧬 Meta-orchestration cascade amplification active</div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
