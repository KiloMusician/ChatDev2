import { Route, Switch } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";
import { Navigation } from "@/components/Navigation";
import { PageTransition } from "@/components/PageTransition";
import { Component, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Import all page components
import Home from "@/pages/Home";
import ChatDevConsole from "@/pages/ChatDevConsole";
import ScopeExplorer from "@/pages/ScopeExplorer";
import AnalysisCenter from "@/pages/AnalysisCenter";
import TestingChamber from "@/pages/TestingChamber";
import ConsciousnessHub from "@/pages/ConsciousnessHub";
import SystemOptimizer from "@/pages/SystemOptimizer";
import FlexibilityHub from "@/pages/FlexibilityHub";
import ModernizationCenter from "@/pages/ModernizationCenter";
import TranscendenceInterface from "@/pages/TranscendenceInterface";
import QuantumWorkshop from "@/pages/QuantumWorkshop";
import CrossDimensionalSync from "@/pages/CrossDimensionalSync";
import SystemEvolutionCenter from "@/pages/SystemEvolutionCenter";
import PerformanceOptimizer from "@/pages/PerformanceOptimizer";
import AdvancedIntegrationCenter from "@/pages/AdvancedIntegrationCenter";
import AutomationOrchestrator from "@/pages/AutomationOrchestrator";
import RealityManipulationHub from "@/pages/RealityManipulationHub";
import ResonanceOptimizer from "@/pages/ResonanceOptimizer";
import VantagesHub from "@/pages/VantagesHub";
import AdminConsole from "@/pages/AdminConsole";
import GameConsole from "@/pages/GameConsole";
import GameMainMenu from "@/pages/GameMainMenu";
import AgentHub from "@/pages/AgentHub";
import OpsCenter from "@/pages/OpsCenter";
import AnchorsView from "@/pages/AnchorsView";
import SettingsPanel from "@/pages/SettingsPanel";
import SystemInboxPage from "@/pages/SystemInbox";
import AgentChatPage from "@/pages/AgentChatPage";
import MultiplayerLobby from "@/pages/MultiplayerLobby";
import GameShell from "@/components/GameShell";
import { StableInterface } from "@/components/StableInterface";
import DevMenuExtended from "@/components/DevMenuExtended";
import { InfrastructureDashboard } from "@/components/InfrastructureDashboard";
import { infrastructureIntelligence } from "@/services/infrastructure-intelligence";
import DimensionalCompanion from "@/components/DimensionalCompanion";

const queryClient = new QueryClient();

// Initialize infrastructure intelligence on app start
infrastructureIntelligence.loadPersistedEvents();

// Start generating real infrastructure intelligence immediately
setTimeout(() => {
  infrastructureIntelligence.reportEvent({
    who: 'Application Startup',
    what: 'CoreLink Foundation initialized',
    where: 'localhost:5000',
    when: new Date().toISOString(),
    why: 'Development environment setup',
    how: 'React + TypeScript + Vite',
    priority: 'high',
    category: 'build'
  });
}, 1000);

// Simple Error Boundary Component
class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-6">
          <div className="text-center space-y-4 max-w-md">
            <h1 className="text-2xl font-bold text-red-400">⚠️ System Error</h1>
            <p className="text-gray-300">
              Something went wrong, but the core system is still running.
            </p>
            <details className="text-left bg-gray-800 p-4 rounded text-sm">
              <summary className="cursor-pointer text-yellow-400 mb-2">Error Details</summary>
              <pre className="whitespace-pre-wrap text-red-300">
                {this.state.error?.message || 'Unknown error'}
              </pre>
            </details>
            <div className="space-x-2">
              <button 
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
              >
                Try Again
              </button>
              <button 
                onClick={() => window.location.href = '/'}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
              >
                Return to HUD
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Import the self-evolving UI system
import SelfEvolvingApp from "./App-SelfEvolving";

// Use self-evolving UI if enabled, otherwise fall back to legacy
const USE_SELF_EVOLVING_UI = true;

export default function App() {
  if (USE_SELF_EVOLVING_UI) {
    return <SelfEvolvingApp />;
  }
  
  // Legacy hardcoded routing (kept for fallback)
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <ErrorBoundary>
          <div className="min-h-screen bg-background">
            <Navigation />
            <main className="min-h-screen">
              <PageTransition>
                <Switch>
                <Route path="/" component={Home} />
                <Route path="/home" component={Home} />
                <Route path="/game-menu" component={GameMainMenu} />
                <Route path="/chatdev" component={ChatDevConsole} />
                <Route path="/vantages" component={VantagesHub} />
                <Route path="/infrastructure" component={InfrastructureDashboard} />
                <Route path="/admin" component={AdminConsole} />
                <Route path="/game" component={StableInterface} />
                <Route path="/game-simple" component={GameShell} />
                <Route path="/game-console" component={GameConsole} />
                <Route path="/dev" component={DevMenuExtended} />
                <Route path="/agents" component={AgentHub} />
                <Route path="/scope" component={ScopeExplorer} />
                <Route path="/analysis" component={AnalysisCenter} />
                <Route path="/chamber" component={TestingChamber} />
                <Route path="/consciousness" component={ConsciousnessHub} />
                <Route path="/optimizer" component={SystemOptimizer} />
                <Route path="/flexibility" component={FlexibilityHub} />
                <Route path="/modernization" component={ModernizationCenter} />
                <Route path="/transcendence" component={TranscendenceInterface} />
                <Route path="/quantum" component={QuantumWorkshop} />
                <Route path="/cross-dimensional" component={CrossDimensionalSync} />
                <Route path="/evolution" component={SystemEvolutionCenter} />
                <Route path="/performance" component={PerformanceOptimizer} />
                <Route path="/integration" component={AdvancedIntegrationCenter} />
                <Route path="/automation" component={AutomationOrchestrator} />
                <Route path="/reality" component={RealityManipulationHub} />
                <Route path="/resonance" component={ResonanceOptimizer} />
                <Route path="/multiplayer" component={MultiplayerLobby} />
                <Route path="/ops" component={OpsCenter} />
                <Route path="/anchors" component={AnchorsView} />
                <Route path="/settings" component={SettingsPanel} />
                <Route path="/inbox" component={SystemInboxPage} />
                <Route path="/chat" component={AgentChatPage} />
                <Route>
                  <div className="text-center py-20">
                    <h1 className="text-2xl font-bold mb-4">404 - Page Not Found</h1>
                    <p className="text-muted-foreground mb-4">
                      The page you're looking for doesn't exist.
                    </p>
                    <a href="/" className="text-primary hover:underline">
                      Return to Home
                    </a>
                  </div>
                </Route>
              </Switch>
              </PageTransition>
            </main>
          </div>
        </ErrorBoundary>
        <DimensionalCompanion />
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
// FRESH BUILD FORCE: 1756961423000 - Infrastructure-First rebuild
// Chug refresh: 1756807851599