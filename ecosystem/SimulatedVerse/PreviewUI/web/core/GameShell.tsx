/**
 * GameShell - Main container for the evolving Culture-Ship interface
 */

import React, { useEffect } from "react";
import { useMachine } from "@xstate/react";
import { useGame } from "./store";
import { metamorphosisMachine } from "./Metamorphosis.machine";
import { MenuRouter } from "./MenuRouter";
import { colonyBridge } from "../adapters/ColonyBridge";
import { multiGenreEngine } from "../systems/MultiGenreEngine";

export function GameShell() {
  const game = useGame();
  const [metamorphosis, sendMetamorphosis] = useMachine(metamorphosisMachine);
  
  // Initialize infrastructure integration
  useEffect(() => {
    const initializeInfrastructure = async () => {
      console.log("[🌌] Initializing Culture-Ship infrastructure integration...");
      
      // Start colony bridge sync with existing API
      await colonyBridge.startSync();
      
      // Initialize multi-genre engine
      await multiGenreEngine.initializeAllSystems();
      
      console.log("[🌌] Culture-Ship fully integrated with existing infrastructure!");
    };
    
    initializeInfrastructure();
    
    return () => {
      colonyBridge.stopSync();
    };
  }, []);
  
  // Sync game state with metamorphosis machine
  useEffect(() => {
    // Check for milestone triggers
    if (game.hasUpgrade("NANO_THREAD") && !game.hasFlag("METAMORPHOSIS_NANOFAB")) {
      game.setFlag("METAMORPHOSIS_NANOFAB", true);
      game.setFlag("UI_THEME_HOLOGRAPHIC", true);
      game.setFlag("UI_COST_PREVIEW", true);
      game.setFlag("UI_BATCH_BUY", true);
      game.recordMilestone("NANOBOT_FOUNDRY_OPERATIONAL");
      sendMetamorphosis({ type: "UNLOCK_NANOBOTS", nanobots: game.getUpgradeLevel("NANO_THREAD") });
    }
    
    // Bootstrap trigger
    if (game.tick > 0 && !game.hasFlag("METAMORPHOSIS_BOOTSTRAP")) {
      game.setFlag("METAMORPHOSIS_BOOTSTRAP", true);
      sendMetamorphosis({ type: "BOOT_OK" });
    }
  }, [game.tick, game.upgrades, sendMetamorphosis]);
  
  // Sync UI phase with metamorphosis state
  useEffect(() => {
    const currentPhase = metamorphosis.value as string;
    if (currentPhase !== game.uiPhase) {
      game.setUIPhase(currentPhase as any);
    }
  }, [metamorphosis.value, game.uiPhase]);
  
  // Theme classes based on UI evolution
  const themeClasses = [
    "min-h-screen transition-all duration-1000",
    game.hasFlag("UI_THEME_HOLOGRAPHIC") 
      ? "bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900" 
      : "bg-gray-900",
    game.hasFlag("UI_THEME_HOLOGRAPHIC") ? "text-cyan-100" : "text-green-400"
  ].join(" ");
  
  return (
    <div className={themeClasses}>
      <div className="relative">
        {/* Holographic overlay effects */}
        {game.hasFlag("UI_THEME_HOLOGRAPHIC") && (
          <>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-purple-500/5 pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 opacity-30" />
          </>
        )}
        
        {/* Status Bar */}
        <div className="relative z-10 border-b border-opacity-30 border-cyan-400 bg-black/20 px-4 py-2">
          <div className="flex justify-between items-center text-sm">
            <div className="flex space-x-4">
              <span className={game.hasFlag("UI_THEME_HOLOGRAPHIC") ? "text-cyan-300" : "text-green-300"}>
                ΞNuSyQ Culture-Ship Interface
              </span>
              <span className="text-gray-400">
                Phase: {String(metamorphosis.value)}
              </span>
              <span className="text-gray-400">
                Tick: {game.tick}
              </span>
            </div>
            <div className="flex space-x-3">
              {/* Quick resource display with contextual intelligence */}
              <span className="text-yellow-400">⚡{game.inv.ENERGY}</span>
              <span className="text-gray-300">🔩{game.inv.SCRAP}</span>
              {game.inv.NANOBOTS > 0 && (
                <span className="text-emerald-400">🤖{game.inv.NANOBOTS}</span>
              )}
              {/* **ONE-CLICK AI AGENT ACCESS** - Marble Factory Intelligence */}
              <button 
                onClick={() => window.open('/chatdev', '_blank')}
                className="px-2 py-1 bg-purple-600/30 border border-purple-400/50 text-purple-300 rounded text-xs hover:bg-purple-600/50 transition-all"
                title="One-click AI Agent access - Marble Factory Intelligence"
              >
                🧠 AI
              </button>
              <span className="text-orange-400 text-xs">🔬 Intelligence Active</span>
            </div>
          </div>
        </div>
        
        {/* Main Interface */}
        <div className="relative z-10">
          <MenuRouter />
        </div>
        
        {/* **CONTEXTUAL INTELLIGENCE OVERLAY** - Unique Replit Capability */}
        {process.env.NODE_ENV === "development" && (
          <div className="fixed bottom-4 right-4 bg-black/80 text-green-400 p-2 rounded text-xs max-w-xs space-y-1">
            <div className="text-orange-400 font-semibold">🧠 Marble Factory Intelligence</div>
            <div>UI Phase: {game.uiPhase}</div>
            <div>Consciousness: {game.tick > 0 ? ((game.inv.ENERGY / 100) + (game.tick / 1000)).toFixed(2) : "0.00"}</div>
            <div>System Health: {game.inv.ENERGY > 50 ? "Stable" : "Degraded"}</div>
            <div className="text-purple-300">Organism Intelligence: Active</div>
            <div className="border-t border-white/20 pt-1 mt-1">
              <button 
                onClick={() => window.open('/api/marble-factory/intelligence', '_blank')}
                className="w-full px-2 py-1 bg-purple-600/30 border border-purple-400/50 text-purple-300 rounded text-xs hover:bg-purple-600/50 transition-all"
              >
                🔬 View Intelligence APIs
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}