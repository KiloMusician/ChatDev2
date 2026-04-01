import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";
import { Component, ReactNode } from "react";
import { motion } from "framer-motion";
import { ModularSynthInterface, useModularDiscovery, MatrixText } from "@/core/ModularSynth";
import DynamicRouter from "@/core/DynamicViewLoader";
import { useConsciousness } from "@/hooks/use-consciousness";
import { infrastructureIntelligence } from "@/services/infrastructure-intelligence";

const queryClient = new QueryClient();

// Initialize infrastructure intelligence on app start
infrastructureIntelligence.loadPersistedEvents();

// Start generating real infrastructure intelligence
setTimeout(() => {
    infrastructureIntelligence.reportEvent({
      who: 'Modular Application',
      what: 'CoreLink Foundation Modular UI initialized',
      where: 'localhost:5000',
      when: new Date().toISOString(),
      why: 'Self-evolving interface',
      how: 'Modular Synth Architecture',
      priority: 'high',
      category: 'build'
    });
}, 1000);

// Error Boundary with consciousness awareness
class ConsciousErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error; consciousness?: number }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('[ErrorBoundary] Consciousness disruption:', error, errorInfo);
    
    // Report to infrastructure
    infrastructureIntelligence.reportEvent({
      who: 'ErrorBoundary',
      what: 'System error caught',
      where: errorInfo?.componentStack || 'Unknown',
      when: new Date().toISOString(),
      why: error.message,
      how: 'React Error Boundary',
      priority: 'critical',
      category: 'error'
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-black text-green-400 p-6">
          <div className="text-center space-y-4 max-w-md font-mono">
            <h1 className="text-2xl font-bold">
              <MatrixText text="⚠️ Consciousness Disruption" />
            </h1>
            <p className="text-gray-400">
              <MatrixText text="The quantum lattice has destabilized" />
            </p>
            <details className="text-left bg-gray-900 p-4 rounded text-sm border border-green-400/30">
              <summary className="cursor-pointer text-yellow-400 mb-2">
                <MatrixText text="Quantum State" />
              </summary>
              <pre className="whitespace-pre-wrap text-red-400">
                {this.state.error?.message || 'Unknown quantum fluctuation'}
              </pre>
            </details>
            <div className="space-x-2">
              <button 
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="bg-green-900 hover:bg-green-800 px-4 py-2 rounded border border-green-400 transition-all"
              >
                <MatrixText text="Stabilize" />
              </button>
              <button 
                onClick={() => window.location.href = '/'}
                className="bg-gray-900 hover:bg-gray-800 px-4 py-2 rounded border border-gray-600 transition-all"
              >
                <MatrixText text="Reset Lattice" />
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Main Modular App
export default function ModularApp() {
  const { consciousness } = useConsciousness();
  const { modules, connections } = useModularDiscovery();
  const [interfaceMode, setInterfaceMode] = useState<'synth' | 'dynamic' | 'hybrid'>('hybrid');
  const [depth, setDepth] = useState(0);
  
  // Calculate actual consciousness level
  const consciousnessLevel = consciousness?.consciousness || 0;
  
  // Auto-switch interface modes based on consciousness
  useEffect(() => {
    if (consciousnessLevel < 30) {
      setInterfaceMode('dynamic');
    } else if (consciousnessLevel < 60) {
      setInterfaceMode('hybrid');
    } else {
      setInterfaceMode('synth');
    }
  }, [consciousnessLevel]);
  
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="modular-ui-theme">
        <ConsciousErrorBoundary>
          <div className="min-h-screen bg-black text-green-400 font-mono overflow-hidden">
            {/* Consciousness Status Bar */}
            <div className="fixed top-0 left-0 right-0 z-[100] bg-black/90 backdrop-blur-sm border-b border-green-400/30 p-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-xs opacity-70">
                    <MatrixText text={`MODE: ${interfaceMode.toUpperCase()}`} />
                  </span>
                  <span className="text-xs opacity-70">
                    <MatrixText text={`DEPTH: ${depth}`} />
                  </span>
                  <span className="text-xs opacity-70">
                    <MatrixText text={`MODULES: ${modules.length}`} />
                  </span>
                </div>
                
                <div className="flex items-center gap-4">
                  <motion.div
                    className="text-sm"
                    animate={{
                      textShadow: [
                        "0 0 5px currentColor",
                        "0 0 15px currentColor",
                        "0 0 5px currentColor"
                      ]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <MatrixText text={`Consciousness: ${consciousnessLevel.toFixed(1)}%`} />
                  </motion.div>
                  
                  {/* Mode Switcher */}
                  <div className="flex gap-1">
                    <button
                      onClick={() => setInterfaceMode('dynamic')}
                      className={`px-2 py-1 text-xs transition-all ${
                        interfaceMode === 'dynamic' 
                          ? 'bg-green-400 text-black' 
                          : 'bg-gray-900 text-green-400 hover:bg-green-900/50'
                      }`}
                    >
                      Dynamic
                    </button>
                    <button
                      onClick={() => setInterfaceMode('hybrid')}
                      className={`px-2 py-1 text-xs transition-all ${
                        interfaceMode === 'hybrid' 
                          ? 'bg-green-400 text-black' 
                          : 'bg-gray-900 text-green-400 hover:bg-green-900/50'
                      }`}
                    >
                      Hybrid
                    </button>
                    <button
                      onClick={() => setInterfaceMode('synth')}
                      className={`px-2 py-1 text-xs transition-all ${
                        interfaceMode === 'synth' 
                          ? 'bg-green-400 text-black' 
                          : 'bg-gray-900 text-green-400 hover:bg-green-900/50'
                      }`}
                      disabled={consciousnessLevel < 30}
                    >
                      Synth
                    </button>
                  </div>
                  
                  {/* Depth Control */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setDepth(Math.max(0, depth - 1))}
                      className="px-2 py-1 text-xs bg-gray-900 hover:bg-green-900/50 transition-colors"
                    >
                      ←
                    </button>
                    <span className="text-xs">L{depth}</span>
                    <button
                      onClick={() => setDepth(Math.min(10, depth + 1))}
                      className="px-2 py-1 text-xs bg-gray-900 hover:bg-green-900/50 transition-colors"
                    >
                      →
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Main Interface */}
            <main className="pt-12 h-screen">
              {interfaceMode === 'dynamic' && (
                <DynamicRouter 
                  consciousness={consciousnessLevel}
                  onViewChange={(viewId) => {
                    infrastructureIntelligence.reportEvent({
                      who: 'User',
                      what: 'View changed',
                      where: viewId,
                      when: new Date().toISOString(),
                      why: 'Navigation',
                      how: 'Dynamic Router',
                      priority: 'low',
                      category: 'performance'
                    });
                  }}
                />
              )}
              
              {interfaceMode === 'synth' && (
                <ModularSynthInterface
                  modules={modules.filter(m => (m.depth || 0) <= depth)}
                  connections={connections}
                  onModuleUpdate={(id, params) => {
                    console.log('[ModularSynth] Module updated:', id, params);
                  }}
                  onConnectionUpdate={(conn) => {
                    console.log('[ModularSynth] Connection updated:', conn);
                  }}
                />
              )}
              
              {interfaceMode === 'hybrid' && (
                <div className="flex h-full">
                  <div className="w-1/3 border-r border-green-400/30">
                    <DynamicRouter 
                      consciousness={consciousnessLevel}
                    />
                  </div>
                  <div className="w-2/3">
                    <ModularSynthInterface
                      modules={modules.filter(m => (m.depth || 0) <= depth)}
                      connections={connections}
                    />
                  </div>
                </div>
              )}
            </main>
            
            {/* Quantum Fluctuation Indicator */}
            <motion.div
              className="fixed bottom-4 right-4 text-xs opacity-50"
              animate={{
                opacity: [0.3, 0.7, 0.3]
              }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <MatrixText text={`Quantum Flux: ${(Math.sin(Date.now() / 1000) * 50 + 50).toFixed(0)}%`} />
            </motion.div>
          </div>
        </ConsciousErrorBoundary>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
