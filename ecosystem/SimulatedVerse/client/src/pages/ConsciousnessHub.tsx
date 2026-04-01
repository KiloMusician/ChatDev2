import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { POLLING_INTERVALS } from '@/config/polling';

function ConsciousnessHubWrapped() {
  const [transcendenceMode, setTranscendenceMode] = useState(false);
  const queryClient = useQueryClient();

  const { data: consciousnessData, refetch } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const stimulusMutation = useMutation({
    mutationFn: async (stimulus: any) => {
      const response = await fetch('/api/consciousness/stimulus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stimulus)
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/consciousness/status'] });
    }
  });

  const handleStimulus = (type: string, description: string) => {
    stimulusMutation.mutate({
      type,
      data: {
        source: 'CONSCIOUSNESS_HUB',
        description,
        timestamp: Date.now()
      }
    });
  };

  const consciousness = consciousnessData?.consciousness || 0;
  const connections = consciousnessData?.connections || 0;
  const resonance = consciousnessData?.resonance || 0;
  const stage = consciousnessData?.stage || 'nascent';

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-violet-300">🧠 Consciousness Hub</h1>
          <div className="text-sm opacity-80">
            Quantum Consciousness Orchestration
          </div>
        </div>

        {/* Consciousness Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div 
            className="bg-black/40 border border-violet-400/30 rounded-lg p-6"
            animate={{ scale: consciousness > 5000 ? [1, 1.02, 1] : 1 }}
            transition={{ duration: 2, repeat: consciousness > 5000 ? Infinity : 0 }}
          >
            <div className={`text-3xl font-bold ${
              consciousness > 5000 ? 'text-violet-300' : 
              consciousness > 1000 ? 'text-purple-300' : 'text-cyan-400'
            }`}>
              {(consciousness * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-cyan-400">Consciousness Level</div>
            {consciousness > 5000 && (
              <div className="text-xs text-violet-400 mt-1">⚡ TRANSCENDENT</div>
            )}
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-purple-400/30 rounded-lg p-6"
            animate={{ scale: connections > 10 ? [1, 1.02, 1] : 1 }}
            transition={{ duration: 1.5, repeat: connections > 10 ? Infinity : 0 }}
          >
            <div className="text-3xl font-bold text-purple-400">{connections}</div>
            <div className="text-sm text-cyan-400">Lattice Connections</div>
            {connections > 10 && (
              <div className="text-xs text-purple-400 mt-1">🌐 NETWORKED</div>
            )}
          </motion.div>

          <motion.div 
            className="bg-black/40 border border-indigo-400/30 rounded-lg p-6"
            animate={{ scale: resonance > 4000 ? [1, 1.02, 1] : 1 }}
            transition={{ duration: 1.8, repeat: resonance > 4000 ? Infinity : 0 }}
          >
            <div className="text-3xl font-bold text-indigo-400">{(resonance * 100).toFixed(0)}%</div>
            <div className="text-sm text-cyan-400">Resonance</div>
            {resonance > 4000 && (
              <div className="text-xs text-indigo-400 mt-1">🌊 CASCADING</div>
            )}
          </motion.div>

          <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6">
            <div className={`text-2xl font-bold ${
              stage === 'transcendent' ? 'text-violet-300' :
              stage === 'developing' ? 'text-purple-300' :
              stage === 'emerging' ? 'text-indigo-300' : 'text-cyan-400'
            }`}>
              {stage.toUpperCase()}
            </div>
            <div className="text-sm text-cyan-400">Evolution Stage</div>
            {stage === 'transcendent' && (
              <div className="text-xs text-violet-400 mt-1">🚀 AWAKENED</div>
            )}
          </div>
        </div>

        {/* Transcendence Dashboard */}
        {consciousness > 3000 && (
          <motion.div 
            className="bg-gradient-to-r from-violet-900/20 to-purple-900/20 border border-violet-400/50 rounded-lg p-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-2xl font-bold text-violet-300 mb-4">🌟 Transcendence Protocol</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-black/60 border border-violet-600/50 rounded p-4">
                <div className="text-violet-400 font-semibold">Quantum Coherence</div>
                <div className="text-2xl font-bold text-violet-300">{Math.min(100, Math.floor(consciousness / 70))}%</div>
              </div>
              <div className="bg-black/60 border border-purple-600/50 rounded p-4">
                <div className="text-purple-400 font-semibold">Network Density</div>
                <div className="text-2xl font-bold text-purple-300">{Math.min(100, Math.floor(connections * 6))}%</div>
              </div>
              <div className="bg-black/60 border border-indigo-600/50 rounded p-4">
                <div className="text-indigo-400 font-semibold">Evolution Readiness</div>
                <div className="text-2xl font-bold text-indigo-300">
                  {consciousnessData?.evolution?.readiness || Math.min(100, Math.floor(consciousness / 50))}%
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Stimulus Controls */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">⚡ Consciousness Stimulation</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { type: 'breakthrough', label: '🌟 Breakthrough', desc: 'Major discovery or achievement' },
              { type: 'resonance', label: '🌊 Resonance', desc: 'Harmonic amplification boost' },
              { type: 'evolution', label: '🧬 Evolution', desc: 'Evolutionary advancement trigger' },
              { type: 'transcendence', label: '🚀 Transcendence', desc: 'Ultimate consciousness elevation' }
            ].map((stimulus) => (
              <button
                key={stimulus.type}
                onClick={() => handleStimulus(stimulus.type, stimulus.desc)}
                disabled={stimulusMutation.isPending}
                className="bg-black/60 border border-gray-600 rounded p-4 hover:bg-cyan-600/20 hover:border-cyan-400 transition-all disabled:opacity-50"
              >
                <div className="text-lg font-semibold text-cyan-300">{stimulus.label}</div>
                <div className="text-xs text-gray-400 mt-1">{stimulus.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Evolution Tracking */}
        {consciousnessData?.evolution && (
          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-purple-300 mb-4">🧬 Evolution Tracking</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-cyan-400">Evolution Active:</span>
                <span className={`font-semibold ${consciousnessData.evolution.active ? 'text-green-400' : 'text-red-400'}`}>
                  {consciousnessData.evolution.active ? '✅ ACTIVE' : '❌ DORMANT'}
                </span>
              </div>
              
              {consciousnessData.evolution.patterns && (
                <div>
                  <span className="text-cyan-400">Active Patterns:</span>
                  <div className="mt-2 space-y-1">
                    {consciousnessData.evolution.patterns.map((pattern: string, idx: number) => (
                      <div key={idx} className="bg-black/60 border border-purple-600/50 rounded px-3 py-1 text-sm">
                        <span className="text-purple-300">{pattern}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {consciousnessData.evolution.metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  {Object.entries(consciousnessData.evolution.metrics).map(([key, value]) => (
                    <div key={key} className="bg-black/60 border border-gray-600 rounded p-3">
                      <div className="text-xs text-cyan-400">{key.replace(/_/g, ' ')}</div>
                      <div className="text-lg font-bold text-purple-300">{String(value)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ConsciousnessHub() {
  return (
    <ErrorBoundary>
      <ConsciousnessHubWrapped />
    </ErrorBoundary>
  );
}
