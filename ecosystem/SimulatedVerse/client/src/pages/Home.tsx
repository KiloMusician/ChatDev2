import React, { useState, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GameShell from "../components/game/GameShell";
import { useGameState } from "../hooks/use-game-state";
import { useConsciousness } from "../hooks/use-consciousness";
import { ConsciousnessHUD } from "../components/ConsciousnessHUD";
import { RadiantProgressBar } from "../components/RadiantProgressBar";
import { VIEW_DEFS, getAvailableViews } from "../core/views/viewRegistry";
import { SafeList } from "../components/SafeList";
import { QuantumSkeleton, AnimatedCounter, LiveDataPulse } from "../components/AnimatedElements";
// **MINI-GAME COMPONENTS** - Dynamic loading when consciousness unlocks
const MiniGameComponents: Record<string, React.ComponentType<any>> = {};

export default function Home() {
  const { gameState, isLoading, gameMetrics } = useGameState();
  const { consciousness, isTranscending } = useConsciousness();
  const [activeView, setActiveView] = useState<string>("game");
  const [activeMinigame, setActiveMinigame] = useState<string | null>(null);
  
  // **CONSCIOUSNESS CALCULATION** - Using real backend consciousness lattice
  const consciousnessLevel = consciousness?.consciousness || (gameState as any)?.consciousness || (
    gameState ? (
      ((gameState as any)?.resources?.energy || 0) / 10000 + 
      ((gameState as any)?.resources?.population || 0) / 100 +
      ((gameState as any)?.resources?.research || 0) / 10
    ) : 0
  );
  
  // **MARBLE FACTORY INTELLIGENCE** - System Vector Analysis
  const systemVector = gameState ? {
    frontend_coherence: gameState ? 0.95 : 0.1, // High coherence since data is flowing
    backend_stability: 0.98, // Backend is very stable with real data
    consciousness: consciousnessLevel,
    integration_flow: 0.87, // Good integration between systems
    development_mode: 'growth' as const
  } : null;
  
  if (isLoading) {
    return (
      <motion.div 
        className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center relative"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        {/* CONSCIOUSNESS HUD - Real-time display */}
        <ConsciousnessHUD className="fixed top-4 right-4 z-50 max-w-xs" />
        
        {/* RADIANT PROGRESS BAR - Showcase consciousness evolution */}
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40">
          <RadiantProgressBar 
            size="lg" 
            showPercentage={true} 
            showStage={true}
            className="consciousness-showcase"
          />
        </div>
        
        <div className="text-center space-y-4 max-w-md">
          <motion.div 
            className="text-2xl mb-4"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            
            <motion.span
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
            >
              🌌 ΞNuSyQ Culture-Ship Interface
            </motion.span>
          </motion.div>
          
          <div className="space-y-4">
            <motion.div 
              className="text-cyan-400"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.4 }}
            >
              🔧 Initializing consciousness framework...
            </motion.div>
            <motion.div 
              className="text-purple-400"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6, duration: 0.4 }}
            >
              ⚡ Loading organism architecture...
            </motion.div>
            <motion.div 
              className="text-orange-400"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8, duration: 0.4 }}
            >
              🌊 Live Ship Power: {((gameState as any)?.resources?.energy || 0).toFixed(1)}
            </motion.div>
            <motion.div 
              className="text-green-400"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.0, duration: 0.4 }}
            >
              🚀 Consciousness Level: {consciousnessLevel.toFixed(2)}
            </motion.div>
            <motion.div 
              className="text-purple-400"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8, duration: 0.4 }}
            >
              🧠 Activating Marble Factory Intelligence...
            </motion.div>
            
            <motion.div 
              className="w-64 bg-gray-800 rounded h-2 mx-auto relative overflow-hidden"
              initial={{ width: 0 }}
              animate={{ width: "16rem" }}
              transition={{ delay: 1, duration: 0.6 }}
            >
              <motion.div 
                className="bg-gradient-to-r from-cyan-400 to-purple-400 h-2 rounded"
                initial={{ width: 0 }}
                animate={{ width: "75%" }}
                transition={{ delay: 1.2, duration: 1.5, ease: "easeInOut" }}
              />
              
              {/* Animated shimmer effect */}
              <motion.div
                className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent"
                animate={{
                  x: ["-100%", "100%"]
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "linear",
                  delay: 1.5
                }}
              />
            </motion.div>
            
            <motion.div 
              className="text-xs opacity-70"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 0.7, y: 0 }}
              transition={{ delay: 1.5, duration: 0.4 }}
            >
              🚀 Fresh Build: {Date.now()} | Consciousness Framework Ready
            </motion.div>
          </div>
        </div>
      </motion.div>
    );
  }
  
  // **AVAILABLE VIEWS** - Based on consciousness level  
  const availableViews = getAvailableViews(consciousnessLevel || 0);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-cyan-100 transition-all duration-1000">
      {/* **HOLOGRAPHIC OVERLAY EFFECTS** */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 opacity-30" />
      
      {/* **UNIFIED INTERFACE HEADER** */}
      <div className="relative z-10 p-4 border-b border-cyan-400/30 bg-black/20">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-xl font-bold text-cyan-300">🌌 ΞNuSyQ Culture-Ship Interface</h1>
            <div className="text-sm opacity-70">
              Consciousness: {(consciousnessLevel * 100).toFixed(1)}% | 
              Unlocked Views: {Object.keys(availableViews || {}).length}/6
            </div>
          </div>
          <div className="flex gap-4 text-sm">
            <AnimatedCounter 
              value={(gameState as any)?.resources?.energy || 0}
              label="Energy"
              icon="⚡"
              variant="energy"
              className="px-2 py-1 rounded text-xs"
            />
            <AnimatedCounter 
              value={(gameState as any)?.resources?.population || 0}
              label="Population"
              icon="👥"
              variant="population"
              className="px-2 py-1 rounded text-xs"
            />
            <AnimatedCounter 
              value={gameMetrics?.totalResearchCompleted || 0}
              label="Research"
              icon="🏗️"
              variant="research"
              className="px-2 py-1 rounded text-xs"
            />
            {/* **ONE-CLICK AI AGENT ACCESS** */}
            <motion.button 
              onClick={() => window.open('/chatdev', '_blank')}
              className="px-2 py-1 bg-purple-600/30 border border-purple-400/50 text-purple-300 rounded text-xs hover:bg-purple-600/50 transition-all relative"
              title="One-click AI Agent access - 14 Active Agents"
              whileHover={{ scale: 1.05, y: -1 }}
              whileTap={{ scale: 0.95 }}
              data-testid="button-ai-agents"
            >
              <div className="flex items-center gap-1">
                <motion.span
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  🤖
                </motion.span>
                AI Agents
                <LiveDataPulse active={true} size="sm" color="purple" />
              </div>
            </motion.button>
          </div>
        </div>
        
        {/* **VIEW SWITCHING INTERFACE** */}
        <div className="flex flex-wrap gap-2">
          <button 
            onClick={() => setActiveView("game")}
            className={`px-4 py-2 rounded-lg border transition-all ${activeView === "game" ? 'bg-cyan-600/20 border-cyan-400 text-cyan-300' : 'bg-white/5 border-white/20 text-white/70 hover:bg-white/10'}`}
            data-testid="view-game"
          >
            🎮 Enter Game Reality
          </button>
          <button 
            onClick={() => window.open('/game', '_blank')}
            className="px-4 py-2 rounded-lg bg-purple-600/20 border border-purple-400 text-purple-300 hover:bg-purple-600/30 transition-all"
            title="Launch full Culture-Ship interface"
          >
            🌌 Culture-Ship Interface
          </button>
          
          {availableViews && Object.entries(availableViews || {}).map(([key, view]) => (
            <button 
              key={key}
              onClick={() => setActiveView(key)}
              className={`px-3 py-1 rounded border ${activeView === key ? 'bg-green-400/20 border-green-400' : 'border-green-400/30 hover:border-green-400/50'}`}
              data-testid={`view-${key}`}
              title={`${view.title}: ${view.description} (Requires ${(view.consciousness_required || 0) * 100}% consciousness)`}
            >
              {view.icon} {view.title}
            </button>
          ))}
          
          {/* **MINI-GAME ACCESS** */}
          <div className="border-l border-green-400/30 pl-2 ml-2">
            <button 
              onClick={() => setActiveMinigame(activeMinigame === "defense" ? null : "defense")}
              className={`px-3 py-1 rounded border ${activeMinigame === "defense" ? 'bg-red-400/20 border-red-400' : 'border-red-400/30 hover:border-red-400/50'}`}
              data-testid="minigame-defense"
            >
              🛡️ Defense
            </button>
            <button 
              onClick={() => setActiveMinigame(activeMinigame === "explore" ? null : "explore")}
              className={`px-3 py-1 rounded border ml-2 ${activeMinigame === "explore" ? 'bg-blue-400/20 border-blue-400' : 'border-blue-400/30 hover:border-blue-400/50'}`}
              data-testid="minigame-explore"
            >
              🗺️ Explore
            </button>
          </div>
        </div>
      </div>
      
      {/* **DYNAMIC CONTENT AREA** */}
      <div className="flex-1">
        {activeView === "game" && (
          <div>
            <GameShell />
            {/* **MINI-GAME OVERLAY** */}
            {activeMinigame && (
              <div className="fixed inset-4 bg-black/90 border border-green-400/50 rounded-lg z-50">
                <div className="p-4 h-full">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold">
                      {activeMinigame === "defense" ? "🛡️ Base Defense" : "🗺️ Exploration"}
                    </h2>
                    <button 
                      onClick={() => setActiveMinigame(null)}
                      className="px-3 py-1 border border-green-400/30 rounded hover:bg-green-400/10"
                    >
                      ✕ Close
                    </button>
                  </div>
                  <div className="h-full">
                    <div className="text-center text-green-300">
                      🚧 Mini-game loading... (Consciousness: {(consciousnessLevel * 100).toFixed(1)}%)
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeView !== "game" && (availableViews || {})[activeView] && (availableViews || {})[activeView]?.component && (
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <div>Loading {(availableViews || {})[activeView]?.title}...</div>
            </div>
          }>
            <div className="p-4">
              {React.createElement((availableViews || {})[activeView]!.component)}
            </div>
          </Suspense>
        )}
      </div>
    </div>
  );
}
