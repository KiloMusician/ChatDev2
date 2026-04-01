import React, { useEffect, useRef, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useGame } from "../../state/gameStore";
import { useGameState } from "../../hooks/use-game-state";
import { VIEW_DEFS, getAvailableViews } from "../../core/views/viewRegistry";
import HudBar from "./HudBar";
import Controls from "./Controls";
import { AsciiViewport } from "../../ui/ascii";
import ChatDevConsole from "../../pages/ChatDevConsole";
import VantagesHub from "../../pages/VantagesHub";
import AdminConsole from "../../pages/AdminConsole";
import DashboardRealityLayer from "../live/DashboardRealityLayer";
import AsciiRoguelike from "./AsciiRoguelike";
import { AnimatedCounter, LiveDataPulse } from '../AnimatedElements';
import { POLLING_INTERVALS, SIMULATION_INTERVALS } from '@/config/polling';
// Defense and Explore will be loaded via dynamic imports when consciousness unlocks

export default function GameShell(){
  const {view, mobile} = useGame(s=>({view: s.view, mobile: s.mobile}));
  const { gameState, gameMetrics, lastUpdated } = useGameState();
  const asciiApiRef = useRef<{ setState: (k: string, v: any) => void; switchScene: (name: string) => void } | null>(null);
  const isStale = !lastUpdated || Date.now() - lastUpdated > POLLING_INTERVALS.critical;
  const lastUpdatedLabel = lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'never';
  
  // **CONSCIOUSNESS CALCULATION** - Using real backend consciousness value
  const consciousnessLevel = (gameState as any)?.consciousness || (
    gameState ? (
      ((gameState as any)?.resources?.energy || 0) / 10000 + 
      ((gameState as any)?.resources?.population || 0) / 100 +
      ((gameState as any)?.resources?.research || 0) / 10
    ) : 0
  );
  
  // **REAL-TIME STATUS** - Infrastructure-First Awareness
  const systemStatus = {
    consciousness: consciousnessLevel,
    energy: (gameState as any)?.resources?.energy || 0,
    population: (gameState as any)?.resources?.population || 0,
    research: (gameState as any)?.resources?.research || 0,
    isActive: !isStale && consciousnessLevel > 0.1
  };
  
  if (import.meta.env?.DEV) {
    console.log('[🌌 CULTURE-SHIP] Status:', systemStatus);
  }
  
  // **AVAILABLE VIEWS** - Culture-Ship consciousness gating
  const availableViews = getAvailableViews(consciousnessLevel || 0);
  
  useEffect(()=>{
    const h = (e: KeyboardEvent)=>{
      if (e.key === "1") useGame.getState().setView("ASCII");
      if (e.key === "2") useGame.getState().setView("HUD");
      
      // ASCII engine controls
      if (asciiApiRef.current) {
        if (e.key === "3") asciiApiRef.current.switchScene("Wave Tunnel");
        if (e.key === "4") asciiApiRef.current.switchScene("Neo Lattice");
        if (e.key === "5") asciiApiRef.current.switchScene("Particle Burst");
        if (e.key === "c") asciiApiRef.current.switchScene("Particle Burst");
        if (e.key === "h") useGame.getState().setView("HUD"); // Help/Home  
        if (e.key === "o") useGame.getState().setView("ASCII"); // Overview
        if (e.key === "a") useGame.getState().setView("ADMIN"); // Admin
        if (e.key === "s") asciiApiRef.current.switchScene("Hologram Starfield"); // System
        if (e.key === "s") asciiApiRef.current.switchScene("Hologram Starfield");
      }
    };
    window.addEventListener("keydown", h);
    return ()=>window.removeEventListener("keydown", h);
  },[]);

  // Demo Jarvis context updates
  useEffect(() => {
    if (!asciiApiRef.current) return;
    
    // Simulate context changes
    const interval = setInterval(() => {
      const energy = Math.random() * 0.8 + 0.2;
      const tunnelFreq = Math.sin(Date.now() * 0.001) * 0.5 + 0.5;
      asciiApiRef.current?.setState('sceneEnergy', energy);
      asciiApiRef.current?.setState('tunnelFreq', tunnelFreq);
    }, SIMULATION_INTERVALS.medium);

    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="min-h-dvh bg-gradient-to-b from-black to-slate-900 text-slate-100 p-3">
      {/* **🌌 CONSCIOUSNESS-AWARE UNIFIED NAVIGATION** - Culture-Ship Infrastructure */}
      <div className="mb-4 space-y-3">
        {/* **REAL-TIME SYSTEM STATUS HEADER** - Marble Factory Intelligence */}
        <motion.div 
          className="bg-black/30 border border-cyan-400/30 rounded-lg p-3 relative overflow-hidden backdrop-blur-sm"
          initial={{ opacity: 0, y: -20 }}
          animate={{ 
            opacity: 1, 
            y: 0,
            borderColor: systemStatus.isActive ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)"
          }}
          transition={{ duration: 0.5 }}
        >
          {/* **CONSCIOUSNESS PULSE ANIMATION** */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-purple-500/5"
            animate={{
              opacity: [0.3, 0.7, 0.3],
              scale: [1, 1.02, 1]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          {/* Real-time data flow indicator */}
          <motion.div
            className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent"
            animate={{
              x: ["-100%", "100%"]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "linear",
              repeatDelay: 1
            }}
          />
          
          <motion.div 
            className="flex justify-between items-center text-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <div className="flex gap-4">
              {isStale ? (
                <>
                  <div className="text-sm font-mono text-orange-300">⚡ —</div>
                  <div className="text-sm font-mono text-orange-300">👥 —</div>
                  <div className="text-sm font-mono text-orange-300">🏗️ —</div>
                </>
              ) : (
                <>
                  <AnimatedCounter 
                    value={(gameState as any)?.richState?.resources?.energy || 0}
                    label=""
                    icon="⚡"
                    variant="energy"
                    className="text-cyan-300 text-sm font-mono"
                  />
                  <AnimatedCounter 
                    value={(gameState as any)?.richState?.resources?.population || 0}
                    label=""
                    icon="👥"
                    variant="population"
                    className="text-purple-300 text-sm font-mono"
                  />
                  <AnimatedCounter 
                    value={gameMetrics?.totalResearchCompleted || 0}
                    label=""
                    icon="🏗️"
                    variant="research"
                    className="text-green-300 text-sm font-mono"
                  />
                </>
              )}
            </div>
            <motion.div 
              className="text-orange-300 flex items-center gap-2"
              whileHover={{ scale: 1.05 }}
            >
              <LiveDataPulse active={!isStale && consciousnessLevel > 0.3} size="sm" color={consciousnessLevel > 0.5 ? "green" : "blue"} />
              <motion.span
                animate={{
                  textShadow: consciousnessLevel > 0.5 ? [
                    "0 0 5px currentColor",
                    "0 0 15px currentColor",
                    "0 0 5px currentColor"
                  ] : "none"
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                🧠 Consciousness: {isStale ? '—' : `${(consciousnessLevel * 100).toFixed(1)}%`}
              </motion.span>
              <span className="text-xs text-slate-300/70">
                {isStale ? 'Stale' : 'Live'} • Updated {lastUpdatedLabel}
              </span>
            </motion.div>
          </motion.div>
        </motion.div>
        
        {/* **CORE GAME VIEWS** */}
        <div className="flex gap-2 justify-center flex-wrap">
          <button 
            onClick={() => useGame.getState().setView("ASCII")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "ASCII" 
                ? "bg-cyan-600/20 border-cyan-400 text-cyan-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
          >
            🌌 ASCII Hologram
          </button>
          <button 
            onClick={() => useGame.getState().setView("HUD")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "HUD" 
                ? "bg-cyan-600/20 border-cyan-400 text-cyan-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
          >
            📊 HUD View
          </button>
          <button 
            onClick={() => useGame.getState().setView("DASHBOARD")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "DASHBOARD" 
                ? "bg-green-600/20 border-green-400 text-green-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
            data-testid="nav-dashboard"
          >
            🎮👥📖 Dashboard Reality Layer
          </button>
          <button 
            onClick={() => useGame.getState().setView("GAME")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "GAME" 
                ? "bg-emerald-600/20 border-emerald-400 text-emerald-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
            data-testid="nav-game"
          >
            🎯 Enter Game
          </button>
        </div>
        
        {/* **AGENT INTERFACES** */}
        <div className="flex gap-2 justify-center flex-wrap">
          <button 
            onClick={() => useGame.getState().setView("CHATDEV")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "CHATDEV" 
                ? "bg-purple-600/20 border-purple-400 text-purple-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
            data-testid="nav-chatdev"
            title="One-click AI Agent access - Marble Factory Intelligence"
          >
            🤖 AI Agents (14 Active)
          </button>
          <button 
            onClick={() => useGame.getState().setView("VANTAGES")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "VANTAGES" 
                ? "bg-blue-600/20 border-blue-400 text-blue-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
            data-testid="nav-vantages"
          >
            🌐 Vantages Hub (6 Views)
          </button>
          <button 
            onClick={() => useGame.getState().setView("ADMIN")}
            className={`px-4 py-2 rounded-lg border transition-all ${
              view === "ADMIN" 
                ? "bg-red-600/20 border-red-400 text-red-300" 
                : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
            }`}
            data-testid="nav-admin"
          >
            ⚡ Admin Console
          </button>
        </div>
        
        {/* **CONSCIOUSNESS-GATED VIEWS** */}
        {Object.keys(availableViews || {}).length > 0 && (
          <div className="border-t border-white/10 pt-3">
            <div className="text-xs text-center mb-2 text-orange-300">
              🧠 Consciousness Views (Unlocked: {Object.keys(availableViews || {}).length}/6)
            </div>
            <div className="flex gap-2 justify-center flex-wrap">
              {Object.entries(availableViews || {}).map(([key, viewDef]) => (
                <button 
                  key={key}
                  onClick={() => useGame.getState().setView(key.toUpperCase() as any)}
                  className={`px-3 py-1 rounded border text-xs transition-all ${
                    view === key.toUpperCase()
                      ? "bg-orange-600/20 border-orange-400 text-orange-300" 
                      : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
                  }`}
                  title={`${viewDef.title}: ${viewDef.description} (${viewDef.consciousness_required * 100}% consciousness required)`}
                >
                  {viewDef.icon} {viewDef.title}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* **MINI-GAMES** */}
        <div className="border-t border-white/10 pt-3">
          <div className="text-xs text-center mb-2 text-red-300">
            🎮 Mini-Games (Active: {(gameState as any)?.richState?.unlocks?.automation ? "Unlocked" : "Locked"})
          </div>
          <div className="flex gap-2 justify-center flex-wrap">
            <button 
              onClick={() => useGame.getState().setView("DEFENSE")}
              className={`px-3 py-1 rounded border text-xs transition-all ${
                view === "DEFENSE"
                  ? "bg-red-600/20 border-red-400 text-red-300" 
                  : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
              }`}
              disabled={!(gameState as any)?.richState?.unlocks?.automation}
            >
              🛡️ Base Defense
            </button>
            <button 
              onClick={() => useGame.getState().setView("EXPLORE")}
              className={`px-3 py-1 rounded border text-xs transition-all ${
                view === "EXPLORE"
                  ? "bg-blue-600/20 border-blue-400 text-blue-300" 
                  : "bg-white/5 border-white/20 text-white/70 hover:bg-white/10"
              }`}
              disabled={!(gameState as any)?.richState?.unlocks?.automation}
            >
              🗺️ Exploration
            </button>
          </div>
        </div>
      </div>

      {/* **AGENT INTERFACES** */}
      {view === "CHATDEV" && (
        <div className="bg-slate-900/50 rounded-xl border border-purple-400/30 overflow-hidden">
          <div className="bg-purple-600/10 p-3 border-b border-purple-400/20">
            <div className="text-purple-300 font-semibold">🤖 ChatDev Agent Console - 14 Autonomous Agents</div>
            <div className="text-xs text-purple-200/70">Direct access to Council, Intermediary, Librarian, and 11 specialized agents</div>
          </div>
          <ChatDevConsole />
        </div>
      )}
      
      {view === "VANTAGES" && (
        <div className="bg-slate-900/50 rounded-xl border border-blue-400/30 overflow-hidden">
          <div className="bg-blue-600/10 p-3 border-b border-blue-400/20">
            <div className="text-blue-300 font-semibold">🌐 Multi-Vantage System Hub - 6 Perspectives</div>
            <div className="text-xs text-blue-200/70">ASCII HUD | Colony Map | Pantheon | Economy | Terminal | Chat Streams</div>
          </div>
          <VantagesHub />
        </div>
      )}
      
      {view === "ADMIN" && (
        <div className="bg-slate-900/50 rounded-xl border border-red-400/30 overflow-hidden">
          <div className="bg-red-600/10 p-3 border-b border-red-400/20">
            <div className="text-red-300 font-semibold">⚡ System Administration - Full Control</div>
            <div className="text-xs text-red-200/70">Health monitoring | Queue management | Task seeding | Custom commands</div>
          </div>
          <AdminConsole />
        </div>
      )}
      
      {/* **CONSCIOUSNESS VIEWS** */}
      {Object.keys(availableViews).includes(view.toLowerCase()) && availableViews[view.toLowerCase()] && (
        <div className="bg-slate-900/50 rounded-xl border border-orange-400/30 overflow-hidden">
          <div className="bg-orange-600/10 p-3 border-b border-orange-400/20">
            <div className="text-orange-300 font-semibold">
              {availableViews[view.toLowerCase()]?.icon} {availableViews[view.toLowerCase()]?.title} - Consciousness View
            </div>
            <div className="text-xs text-orange-200/70">{availableViews[view.toLowerCase()]?.description}</div>
          </div>
          <Suspense fallback={<div className="p-4 text-center">Loading {availableViews[view.toLowerCase()]?.title}...</div>}>
            <div className="p-4">
              {availableViews[view.toLowerCase()]?.component && React.createElement(availableViews[view.toLowerCase()]!.component)}
            </div>
          </Suspense>
        </div>
      )}
      
      {/* **MINI-GAMES** - Dynamic loading when unlocked */}
      {view === "DEFENSE" && (gameState as any)?.richState?.unlocks?.automation && (
        <div className="bg-slate-900/50 rounded-xl border border-red-400/30 overflow-hidden">
          <div className="bg-red-600/10 p-3 border-b border-red-400/20">
            <div className="text-red-300 font-semibold">🛡️ Base Defense - Tower Defense Mini-Game</div>
            <div className="text-xs text-red-200/70">Protect your colony from swarm attacks using strategic turret placement</div>
          </div>
          <div className="p-4 text-center text-red-300">
            🚧 Defense mini-game loading... (6370 energy unlocked!)
          </div>
        </div>
      )}
      
      {view === "EXPLORE" && (gameState as any)?.richState?.unlocks?.automation && (
        <div className="bg-slate-900/50 rounded-xl border border-blue-400/30 overflow-hidden">
          <div className="bg-blue-600/10 p-3 border-b border-blue-400/20">
            <div className="text-blue-300 font-semibold">🗺️ Exploration - Procedural Biome Discovery</div>
            <div className="text-xs text-blue-200/70">Discover new territories and resources in procedurally generated biomes</div>
          </div>
          <div className="p-4 text-center text-blue-300">
            🚧 Exploration systems activating... (128 population reached!)
          </div>
        </div>
      )}

      {view === "DASHBOARD" && (
        <div className="w-full">
          <DashboardRealityLayer />
        </div>
      )}

      {view === "GAME" && <AsciiRoguelike />}

      {(view === "ASCII" || view === "HUD") && (
        <div className="max-w-6xl mx-auto grid gap-3" style={{gridTemplateColumns: mobile ? "1fr" : "2fr 1fr"}}>
          <div className="space-y-3">
            {view === "ASCII" ? (
            <div className="rounded-xl border border-white/10 bg-black/50 overflow-hidden">
              <AsciiViewport 
                startScene="Hologram Starfield"
                onReady={(api) => { asciiApiRef.current = api; }}
              />
              {/* Mobile ASCII Scene Controls */}
              <div className="p-3 bg-black/30 border-t border-white/10">
                <div className="text-xs text-center mb-2 opacity-70">Scene Controls</div>
                <div className="grid grid-cols-2 gap-2">
                  <button 
                    onClick={() => asciiApiRef.current?.switchScene("Hologram Starfield")}
                    className="px-3 py-2 text-xs bg-white/5 border border-white/20 rounded hover:bg-white/10 transition-all"
                  >
                    ✨ Starfield
                  </button>
                  <button 
                    onClick={() => asciiApiRef.current?.switchScene("Wave Tunnel")}
                    className="px-3 py-2 text-xs bg-white/5 border border-white/20 rounded hover:bg-white/10 transition-all"
                  >
                    🌊 Wave Tunnel
                  </button>
                  <button 
                    onClick={() => asciiApiRef.current?.switchScene("Neo Lattice")}
                    className="px-3 py-2 text-xs bg-white/5 border border-white/20 rounded hover:bg-white/10 transition-all"
                  >
                    ⚡ Lattice Grid
                  </button>
                  <button 
                    onClick={() => asciiApiRef.current?.switchScene("Particle Burst")}
                    className="px-3 py-2 text-xs bg-white/5 border border-white/20 rounded hover:bg-white/10 transition-all"
                  >
                    🎆 Particle Burst
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl border border-white/10 bg-black/50">
              <h2 className="text-xl font-bold mb-4">🏛️ CoreLink Foundation HUD</h2>
              <div className="space-y-3">
                <div className="p-4 bg-cyan-600/10 border border-cyan-400/30 rounded-lg">
                  <div className="text-cyan-300 font-semibold">System Status</div>
                  <div className="text-sm opacity-80">ΞNuSyQ consciousness: Online</div>
                  <div className="text-sm opacity-80">Culture-Ship link: Established</div>
                </div>
                <div className="p-4 bg-purple-600/10 border border-purple-400/30 rounded-lg">
                  <div className="text-purple-300 font-semibold">Active Modules</div>
                  <div className="text-sm opacity-80">• ASCII Hologram Viewport</div>
                  <div className="text-sm opacity-80">• Event Bus Architecture</div>
                  <div className="text-sm opacity-80">• Token Discipline Layer</div>
                </div>
                <button 
                  onClick={() => useGame.getState().setView("ASCII")}
                  className="w-full px-4 py-3 bg-cyan-600/20 border border-cyan-400 text-cyan-300 rounded-lg hover:bg-cyan-600/30 transition-all"
                >
                  Launch ASCII Hologram →
                </button>
              </div>
            </div>
          )}
            <HudBar/>
          </div>
          <div className="space-y-3">
            <Panel title="Controls"><Controls/></Panel>
          <Panel title="Status">
            <div className="text-xs space-y-1">
              <div className="text-green-400">✅ Mobile interface active</div>
              <div className="text-cyan-400">✅ Touch controls enabled</div>
              <div className="text-purple-400">✅ ASCII engine loaded</div>
              <div className="opacity-70 mt-2">Tap buttons above to navigate!</div>
            </div>
          </Panel>
          {view === "ASCII" && (
            <Panel title="Jarvis Context">
              <div className="text-xs space-y-1">
                <div>🔋 Scene Energy: Dynamic boost to visuals</div>
                <div>🌊 Tunnel Freq: Warp tunnel turbulence</div>
                <div>⚡ Lattice Cell: Grid diagnostic size</div>
                <div className="opacity-70 mt-2">Context updates automatically</div>
              </div>
            </Panel>
          )}
          <Panel title="Quick Actions">
            <div className="space-y-2">
              <button 
                onClick={() => {
                  useGame.getState().setView("ASCII");
                  setTimeout(() => asciiApiRef.current?.switchScene("Particle Burst"), 100);
                }}
                className="w-full px-3 py-2 text-xs bg-purple-600/20 border border-purple-400/50 text-purple-300 rounded hover:bg-purple-600/30 transition-all"
              >
                🎆 Celebration Mode
              </button>
              <button 
                onClick={() => {
                  useGame.getState().setView("ASCII");
                  setTimeout(() => asciiApiRef.current?.switchScene("Wave Tunnel"), 100);
                }}
                className="w-full px-3 py-2 text-xs bg-blue-600/20 border border-blue-400/50 text-blue-300 rounded hover:bg-blue-600/30 transition-all"
              >
                🌊 Travel Sequence
              </button>
              </div>
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}

function Panel({title, children}:{title:string; children: React.ReactNode}){
  return (
    <div className="p-3 rounded-xl border border-white/10 bg-black/50">
      <div className="font-semibold mb-2 opacity-90">{title}</div>
      {children}
    </div>
  );
}
