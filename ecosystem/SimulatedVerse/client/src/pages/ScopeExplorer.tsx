import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { POLLING_INTERVALS } from '@/config/polling';

function ScopeExplorerWrapped() {
  const [selectedModes, setSelectedModes] = useState<string[]>(['game']);
  const [resolvedFiles, setResolvedFiles] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: scopeData } = useQuery<any>({
    queryKey: ['/api/scope/list'],
    refetchInterval: POLLING_INTERVALS.standard
  });

  const resolveMutation = useMutation({
    mutationFn: async (scope: any) => {
      const response = await fetch('/api/scope/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope })
      });
      return response.json();
    },
    onSuccess: (data) => {
      setResolvedFiles(data.files || []);
    }
  });

  const handleResolve = () => {
    resolveMutation.mutate({
      modes: selectedModes,
      include_proof: true
    });
  };

  const toggleMode = (mode: string) => {
    setSelectedModes(prev => 
      prev.includes(mode) 
        ? prev.filter(m => m !== mode)
        : [...prev, mode]
    );
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-cyan-300">🔍 Scope Explorer</h1>
          <div className="text-sm opacity-80">
            Workspace Scoping System
          </div>
        </div>

        {/* Mode Selection */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">Available Modes</h2>
          {scopeData ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {scopeData.modes?.map((mode: string) => (
                <button
                  key={mode}
                  onClick={() => toggleMode(mode)}
                  className={`px-4 py-2 rounded border transition-all ${
                    selectedModes.includes(mode)
                      ? 'bg-cyan-600/30 border-cyan-400 text-cyan-300'
                      : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          ) : (
            <div className="text-gray-400">Loading scope modes...</div>
          )}
          
          <div className="mt-4">
            <h3 className="text-lg font-semibold text-purple-300 mb-2">Combo Modes</h3>
            <div className="flex flex-wrap gap-2">
              {scopeData?.combos?.map((combo: string) => (
                <span key={combo} className="px-3 py-1 bg-purple-600/20 border border-purple-400/50 rounded text-sm">
                  {combo}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Resolution Controls */}
        <div className="bg-black/40 border border-green-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-green-300 mb-4">Scope Resolution</h2>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <div className="text-sm text-cyan-400 mb-2">Selected Modes:</div>
              <div className="flex flex-wrap gap-2">
                {selectedModes.map(mode => (
                  <span key={mode} className="px-2 py-1 bg-cyan-600/20 border border-cyan-400/50 rounded text-sm">
                    {mode}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={handleResolve}
              disabled={resolveMutation.isPending}
              className="px-6 py-2 bg-green-600/30 border border-green-400 text-green-300 rounded hover:bg-green-600/50 transition-all disabled:opacity-50"
            >
              {resolveMutation.isPending ? 'Resolving...' : 'Resolve Scope'}
            </button>
          </div>
          
          {resolvedFiles.length > 0 && (
            <div>
              <div className="text-sm text-green-400 mb-2">
                Resolved {resolvedFiles.length} files:
              </div>
              <div className="max-h-64 overflow-y-auto bg-black/60 border border-gray-600 rounded p-3">
                <div className="font-mono text-xs space-y-1">
                  {resolvedFiles.slice(0, 50).map((file, idx) => (
                    <div key={idx} className="text-gray-300">{file}</div>
                  ))}
                  {resolvedFiles.length > 50 && (
                    <div className="text-yellow-400">... and {resolvedFiles.length - 50} more files</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* System Policies */}
        {scopeData?.policies && (
          <div className="bg-black/40 border border-orange-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-orange-300 mb-4">System Policies</h2>
            <div className="space-y-2">
              {Object.entries(scopeData.policies).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-cyan-400">{key.replace(/_/g, ' ')}</span>
                  <span className={`text-sm ${value ? 'text-green-400' : 'text-red-400'}`}>
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ScopeExplorer() {
  return (
    <ErrorBoundary>
      <ScopeExplorerWrapped />
    </ErrorBoundary>
  );
}
