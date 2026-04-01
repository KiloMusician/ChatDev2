import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

function AnalysisCenterWrapped() {
  const [selectedScope, setSelectedScope] = useState({ modes: ['system'] });
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  const analysisMutation = useMutation({
    mutationFn: async (scope: any) => {
      const response = await fetch('/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope })
      });
      return response.json();
    },
    onSuccess: (data) => {
      setAnalysisResults(data);
    }
  });

  const handleAnalyze = () => {
    analysisMutation.mutate(selectedScope);
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-cyan-300">📊 Analysis Center</h1>
          <div className="text-sm opacity-80">
            Maximum-Depth Repository Analysis
          </div>
        </div>

        {/* Analysis Controls */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">Analysis Configuration</h2>
          
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <label className="text-sm text-cyan-400 mb-2 block">Analysis Scope:</label>
              <select 
                value={selectedScope.modes[0]}
                onChange={(e) => setSelectedScope({ modes: [e.target.value] })}
                className="w-full px-3 py-2 bg-black/60 border border-gray-600 rounded text-white"
              >
                <option value="system">System Analysis</option>
                <option value="game">Game Components</option>
                <option value="everything">Full Repository</option>
                <option value="simulation">Simulation Systems</option>
              </select>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={analysisMutation.isPending}
              className="px-6 py-2 bg-cyan-600/30 border border-cyan-400 text-cyan-300 rounded hover:bg-cyan-600/50 transition-all disabled:opacity-50"
            >
              {analysisMutation.isPending ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        </div>

        {/* Analysis Results */}
        {analysisResults && (
          <div className="space-y-6">
            {/* Inventory Results */}
            {analysisResults.inventory && (
              <div className="bg-black/40 border border-green-400/30 rounded-lg p-6">
                <h2 className="text-xl font-bold text-green-300 mb-4">📁 File Inventory</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-green-400">{analysisResults.inventory.total_files}</div>
                    <div className="text-sm text-cyan-400">Total Files</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-orange-400">{analysisResults.inventory.missing_headers?.length || 0}</div>
                    <div className="text-sm text-cyan-400">Missing Headers</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-purple-400">{analysisResults.inventory.orphaned_files?.length || 0}</div>
                    <div className="text-sm text-cyan-400">Orphaned Files</div>
                  </div>
                </div>

                {analysisResults.inventory.by_type && (
                  <div className="mt-4">
                    <h3 className="text-lg font-semibold text-green-300 mb-2">File Types:</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {Object.entries(analysisResults.inventory.by_type).map(([type, count]) => (
                        <div key={type} className="flex justify-between bg-black/60 border border-gray-600 rounded px-3 py-1">
                          <span className="text-cyan-400">{type}</span>
                          <span className="text-green-400">{count as number}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Health Results */}
            {analysisResults.health && (
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-6">
                <h2 className="text-xl font-bold text-yellow-300 mb-4">🏥 System Health</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-red-400">{analysisResults.health.lsp_errors}</div>
                    <div className="text-sm text-cyan-400">LSP Errors</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-green-400">{(analysisResults.health.test_coverage * 100).toFixed(1)}%</div>
                    <div className="text-sm text-cyan-400">Test Coverage</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-blue-400">{(analysisResults.health.documentation_coverage * 100).toFixed(1)}%</div>
                    <div className="text-sm text-cyan-400">Documentation</div>
                  </div>
                  <div className="bg-black/60 border border-gray-600 rounded p-4">
                    <div className="text-2xl font-bold text-purple-400">{analysisResults.health.technical_debt_score}</div>
                    <div className="text-sm text-cyan-400">Tech Debt Score</div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations */}
            {analysisResults.recommendations && (
              <div className="bg-black/40 border border-purple-400/30 rounded-lg p-6">
                <h2 className="text-xl font-bold text-purple-300 mb-4">💡 Recommendations</h2>
                <div className="space-y-3">
                  {analysisResults.recommendations.slice(0, 10).map((rec: any, idx: number) => (
                    <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="text-cyan-400 font-semibold">{rec.title}</div>
                          <div className="text-gray-300 text-sm mt-1">{rec.description}</div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          rec.priority === 'high' ? 'bg-red-600/30 text-red-300' :
                          rec.priority === 'medium' ? 'bg-yellow-600/30 text-yellow-300' :
                          'bg-green-600/30 text-green-300'
                        }`}>
                          {rec.priority}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {analysisMutation.isError && (
          <div className="bg-red-900/40 border border-red-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-300 mb-2">Analysis Error</h2>
            <p className="text-red-200">Analysis system is initializing. Please try again in a moment.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AnalysisCenter() {
  return (
    <ErrorBoundary>
      <AnalysisCenterWrapped />
    </ErrorBoundary>
  );
}