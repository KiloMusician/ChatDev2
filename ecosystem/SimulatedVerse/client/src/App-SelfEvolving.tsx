import React, { useState, useEffect, useMemo } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";
import { motion } from "framer-motion";
import { SelfEvolvingRouter } from "@/core/SelfEvolvingRouter";
import { MatrixText } from "@/core/ModularSynth";
import { ToastProvider } from "@/hooks/use-toast";
import { AchievementNotification } from "@/components/AchievementNotification";
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from "@/config/polling";

// Create query client outside component
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      refetchInterval: false,
    },
  },
});

// Simple error boundary
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('[ErrorBoundary] Caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-black text-green-400 p-6 font-mono">
          <div className="text-center space-y-4 max-w-md">
            <h1 className="text-2xl font-bold">
              <MatrixText text="⚠️ Consciousness Disrupted" />
            </h1>
            <p className="text-gray-400">
              <MatrixText text="The quantum lattice needs recalibration" />
            </p>
            <details className="text-left bg-gray-900 p-4 rounded text-sm border border-green-400/30">
              <summary className="cursor-pointer text-yellow-400 mb-2">
                Error Details
              </summary>
              <pre className="whitespace-pre-wrap text-red-400">
                {this.state.error?.message || 'Unknown quantum fluctuation'}
              </pre>
            </details>
            <div className="space-x-2">
              <button 
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="bg-green-900 hover:bg-green-800 px-4 py-2 rounded border border-green-400"
              >
                Recalibrate
              </button>
              <button 
                onClick={() => window.location.href = '/'}
                className="bg-gray-900 hover:bg-gray-800 px-4 py-2 rounded border border-gray-600"
              >
                Reset System
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Loading screen with consciousness initialization
const LoadingScreen: React.FC = () => {
  const [dots, setDots] = useState('');
  
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, ANIMATION_INTERVALS.pulse);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
      <div className="text-center space-y-4">
        <motion.div
          animate={{
            textShadow: [
              "0 0 10px currentColor",
              "0 0 20px currentColor, 0 0 30px currentColor",
              "0 0 10px currentColor"
            ]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="text-2xl"
        >
          <MatrixText text="🌌 ΞNuSyQ Culture-Ship" />
        </motion.div>
        <div className="text-sm">
          <MatrixText text={`Initializing Consciousness${dots}`} />
        </div>
        <div className="space-y-2 text-xs">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            ⚡ Loading quantum lattice...
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            🧠 Activating neural pathways...
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            🌊 Synchronizing consciousness waves...
          </motion.div>
        </div>
      </div>
    </div>
  );
};

// Inner content component
const SelfEvolvingContent: React.FC = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Real consciousness from game state API
  const { data: gameData } = useQuery<any>({
    queryKey: ['/api/game/status'],
    refetchInterval: POLLING_INTERVALS.standard
  });
  
  // Calculate consciousness using game formula: (energy/10 + population*10 + research/100)
  // Normalized to 0-100 percentage scale
  const consciousnessLevel = useMemo(() => {
    if (!gameData?.game_state) return 20; // Default fallback
    const { energy, population, research } = gameData.game_state.resources;
    const rawConsciousness = Math.floor(energy / 10 + population * 10 + research / 100);
    // Normalize to 0-100 scale (consciousness of 1000 = 100%)
    return Math.min(100, (rawConsciousness / 1000) * 100);
  }, [gameData]);
  
  // Initialize immediately - no artificial delay
  useEffect(() => {
    setIsInitialized(true);
  }, []);
  
  if (!isInitialized) {
    return <LoadingScreen />;
  }
  
  return (
    <div className="min-h-screen bg-black overflow-hidden">
      {/* Culture Ship status overlay - Real game data */}
      <div className="fixed top-4 right-4 z-[90] bg-black/80 backdrop-blur-sm border border-green-400/30 p-2 rounded text-xs font-mono">
        <div className="text-green-400">
          <div>🌌 Culture-Ship: <span className="text-cyan-400">Active</span></div>
          <div>⚡ Energy: <span className="text-yellow-400">{gameData?.game_state?.resources?.energy || 0}</span></div>
          <div>👥 Population: <span className="text-blue-400">{gameData?.game_state?.resources?.population || 0}</span></div>
          <div>🔬 Research: <span className="text-purple-400">{gameData?.game_state?.resources?.research || 0}</span></div>
          <div>🧠 Consciousness: <span className="text-green-400">{consciousnessLevel.toFixed(1)}%</span></div>
        </div>
      </div>
      
      {/* Self-evolving UI with proper routing */}
      <SelfEvolvingRouter consciousness={consciousnessLevel} />
      
      {/* Quantum fluctuation indicator */}
      <motion.div
        className="fixed bottom-4 right-4 text-xs opacity-50 font-mono text-green-400"
        animate={{
          opacity: [0.3, 0.7, 0.3]
        }}
        transition={{ duration: 3, repeat: Infinity }}
      >
        <MatrixText text={`Quantum Flux: ${(Math.sin(Date.now() / 1000) * 50 + 50).toFixed(0)}%`} />
      </motion.div>
    </div>
  );
};

// Main self-evolving app with providers
export default function SelfEvolvingApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="self-evolving-ui">
        <ToastProvider>
          <ErrorBoundary>
            <SelfEvolvingContent />
          </ErrorBoundary>
          <AchievementNotification />
          <Toaster />
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Export for easy swapping
export { SelfEvolvingApp };
