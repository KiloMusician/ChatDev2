import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

function TestingChamberWrapped() {
  const [testCode, setTestCode] = useState('console.log("Hello from testing chamber!");');
  const [chamberResults, setChamberResults] = useState<any>(null);

  const testMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('/api/chamber/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, sandbox: true })
      });
      return response.json();
    },
    onSuccess: (data) => {
      setChamberResults(data);
    }
  });

  const handleRunTest = () => {
    testMutation.mutate(testCode);
  };

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-cyan-300">🧪 Testing Chamber</h1>
          <div className="text-sm opacity-80">
            Sandboxed Code Execution Environment
          </div>
        </div>

        {/* Code Input */}
        <div className="bg-black/40 border border-cyan-400/30 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-cyan-300 mb-4">Code Sandbox</h2>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm text-cyan-400 mb-2 block">Test Code:</label>
              <textarea
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                className="w-full h-64 px-3 py-2 bg-black/60 border border-gray-600 rounded text-white font-mono text-sm"
                placeholder="Enter JavaScript code to test..."
              />
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={handleRunTest}
                disabled={testMutation.isPending}
                className="px-6 py-2 bg-green-600/30 border border-green-400 text-green-300 rounded hover:bg-green-600/50 transition-all disabled:opacity-50"
              >
                {testMutation.isPending ? 'Executing...' : 'Run Test'}
              </button>
              
              <button
                onClick={() => setTestCode('')}
                className="px-6 py-2 bg-gray-600/30 border border-gray-400 text-gray-300 rounded hover:bg-gray-600/50 transition-all"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Results Display */}
        {chamberResults && (
          <div className="space-y-6">
            {/* Execution Results */}
            <div className="bg-black/40 border border-green-400/30 rounded-lg p-6">
              <h2 className="text-xl font-bold text-green-300 mb-4">📊 Execution Results</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <div className={`text-2xl font-bold ${chamberResults.success ? 'text-green-400' : 'text-red-400'}`}>
                    {chamberResults.success ? '✅' : '❌'}
                  </div>
                  <div className="text-sm text-cyan-400">Status</div>
                </div>
                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <div className="text-2xl font-bold text-blue-400">{chamberResults.execution_time}ms</div>
                  <div className="text-sm text-cyan-400">Execution Time</div>
                </div>
                <div className="bg-black/60 border border-gray-600 rounded p-4">
                  <div className="text-2xl font-bold text-purple-400">{chamberResults.memory_used || 'N/A'}</div>
                  <div className="text-sm text-cyan-400">Memory Used</div>
                </div>
              </div>

              {/* Output */}
              {chamberResults.output && (
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-cyan-300 mb-2">Output:</h3>
                  <div className="bg-black/60 border border-gray-600 rounded p-3">
                    <pre className="font-mono text-sm text-gray-300 whitespace-pre-wrap">
                      {chamberResults.output}
                    </pre>
                  </div>
                </div>
              )}

              {/* Errors */}
              {chamberResults.error && (
                <div>
                  <h3 className="text-lg font-semibold text-red-300 mb-2">Error:</h3>
                  <div className="bg-red-900/20 border border-red-600/50 rounded p-3">
                    <pre className="font-mono text-sm text-red-300 whitespace-pre-wrap">
                      {chamberResults.error}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* Security Analysis */}
            {chamberResults.security && (
              <div className="bg-black/40 border border-yellow-400/30 rounded-lg p-6">
                <h2 className="text-xl font-bold text-yellow-300 mb-4">🔒 Security Analysis</h2>
                <div className="space-y-3">
                  {chamberResults.security.risks?.map((risk: any, idx: number) => (
                    <div key={idx} className="bg-black/60 border border-gray-600 rounded p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="text-cyan-400 font-semibold">{risk.type}</div>
                          <div className="text-gray-300 text-sm mt-1">{risk.description}</div>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          risk.level === 'high' ? 'bg-red-600/30 text-red-300' :
                          risk.level === 'medium' ? 'bg-yellow-600/30 text-yellow-300' :
                          'bg-green-600/30 text-green-300'
                        }`}>
                          {risk.level}
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
        {testMutation.isError && (
          <div className="bg-red-900/40 border border-red-400/30 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-300 mb-2">Chamber Error</h2>
            <p className="text-red-200">Testing chamber is initializing. Please try again in a moment.</p>
          </div>
        )}

        {/* Quick Examples */}
        <div className="bg-black/40 border border-purple-400/30 rounded-lg p-6 mt-6">
          <h2 className="text-xl font-bold text-purple-300 mb-4">💡 Quick Examples</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                title: 'Simple Math',
                code: 'const result = 2 + 2;\nconsole.log("2 + 2 =", result);'
              },
              {
                title: 'Array Operations',
                code: 'const numbers = [1, 2, 3, 4, 5];\nconst doubled = numbers.map(n => n * 2);\nconsole.log("Doubled:", doubled);'
              },
              {
                title: 'Object Processing',
                code: 'const user = { name: "Agent", level: 42 };\nconsole.log(`User ${user.name} is level ${user.level}`);'
              },
              {
                title: 'Error Handling',
                code: 'try {\n  JSON.parse("invalid json");\n} catch (e) {\n  console.log("Caught error:", e.message);\n}'
              }
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => setTestCode(example.code)}
                className="text-left bg-black/60 border border-gray-600 rounded p-3 hover:bg-purple-600/20 transition-all"
              >
                <div className="text-purple-400 font-semibold mb-1">{example.title}</div>
                <pre className="font-mono text-xs text-gray-400 overflow-hidden">
                  {example.code.split('\n')[0]}...
                </pre>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TestingChamber() {
  return (
    <ErrorBoundary>
      <TestingChamberWrapped />
    </ErrorBoundary>
  );
}