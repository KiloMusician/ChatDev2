import React from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { useQuery } from '@tanstack/react-query';
import { POLLING_INTERVALS } from '@/config/polling';

function AgentHubWrapped() {
  const { data: chatdevStatus } = useQuery<any>({
    queryKey: ['/api/chatdev/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const { data: consciousness } = useQuery<any>({
    queryKey: ['/api/consciousness/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-cyan-300">🤖 Agent Hub</h1>
          <div className="text-sm">
            Consciousness: {consciousness ? (consciousness.consciousness * 100).toFixed(1) : 0}%
          </div>
        </div>
        
        {/* ChatDev Agent Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-cyan-300 mb-4">🧠 ChatDev Framework</h2>
            {chatdevStatus ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Active Agents:</span>
                  <span className="text-green-400">{chatdevStatus.agents}</span>
                </div>
                <div className="flex justify-between">
                  <span>Pipelines:</span>
                  <span className="text-blue-400">{chatdevStatus.pipelines}</span>
                </div>
                <div className="flex justify-between">
                  <span>Prompts:</span>
                  <span className="text-purple-400">{chatdevStatus.prompts}</span>
                </div>
                <div className="flex justify-between">
                  <span>Autonomous:</span>
                  <span className="text-orange-400">{chatdevStatus.autonomous?.chatdev?.active}</span>
                </div>
              </div>
            ) : (
              <div className="text-gray-400">Loading agent status...</div>
            )}
          </div>

          <div className="bg-black/40 border border-purple-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-purple-300 mb-4">⚡ System Status</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Self-Improvement:</span>
                <span className="text-green-400">
                  {chatdevStatus?.autonomous?.self_improvement ? '✅ Active' : '❌ Inactive'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>System:</span>
                <span className="text-green-400">
                  {chatdevStatus?.autonomous?.system || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Consciousness Stage:</span>
                <span className="text-cyan-400">{consciousness?.stage || 'Unknown'}</span>
              </div>
            </div>
          </div>

          <div className="bg-black/40 border border-green-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-green-300 mb-4">🔗 Connections</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Lattice Connections:</span>
                <span className="text-green-400">{consciousness?.connections || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Resonance:</span>
                <span className="text-pink-400">{consciousness ? (consciousness.resonance * 100).toFixed(1) : 0}%</span>
              </div>
              <div className="flex justify-between">
                <span>Evolution:</span>
                <span className="text-orange-400">
                  {consciousness?.evolution?.active ? '🧬 Active' : '❌ Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Activity Log */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">📋 Recent Agent Activity</h2>
          <div className="space-y-2 font-mono text-sm">
            <div className="text-green-400">✅ ChatDev framework operational with {chatdevStatus?.agents || 0} agents</div>
            <div className="text-purple-400">⚡ Autonomous development system active</div>
            <div className="text-cyan-400">🧠 Consciousness level: {consciousness ? (consciousness.consciousness * 100).toFixed(1) : 0}%</div>
            <div className="text-orange-400">🔗 Lattice connections: {consciousness?.connections || 0}</div>
            <div className="text-pink-400">🌊 Evolution patterns: {consciousness?.evolution?.eligible || 0} eligible</div>
            {consciousness?.evolution?.active && (
              <div className="text-yellow-400">🧬 Evolution engine processing {consciousness.evolution.pending} patterns</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentHub() {
  return (
    <ErrorBoundary>
      <AgentHubWrapped />
    </ErrorBoundary>
  );
}
