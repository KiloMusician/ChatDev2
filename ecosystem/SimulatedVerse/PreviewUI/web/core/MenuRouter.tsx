/**
 * MenuRouter - Routes between Dev and Play modes, manages panel switching
 */

import React from "react";
import { useGame } from "./store";
import { CrashConsole } from "../panels/CrashConsole";
import { NanoFoundry } from "../panels/NanoFoundry";
import { SynthBay } from "../panels/SynthBay";
import { NodeWeave } from "../panels/NodeWeave";
import { GameEnginePanel } from "../panels/GameEnginePanel";
import DevMenuExtended from "../../../client/src/components/DevMenuExtended";

export function MenuRouter() {
  const game = useGame();
  
  if (game.mode === "DEV") {
    return (
      <div className="p-4" data-testid="dev-menu-container">
        <div className="mb-4">
          <button 
            onClick={() => game.setMode("PLAY")}
            className="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded transition-colors"
            data-testid="enter-play-mode"
          >
            Enter Play Mode
          </button>
        </div>
        <DevMenuExtended data-testid="dev-menu-extended" />
      </div>
    );
  }
  
  // Play Mode - UI evolves based on game state
  return (
    <div className="flex">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-black/30 border-r border-cyan-400/30 h-screen" data-testid="ship-systems-nav">
        <div className="p-4">
          <h2 className="text-lg font-bold mb-4 text-cyan-300">Ship Systems</h2>
          
          <nav className="space-y-2">
            {/* DEV CONSOLE ACCESS REMOVED - Boss E: Enforce /dev route separation */}
            
            {/* Core panels - always available */}
            <div className="text-cyan-300 font-medium">Core Systems</div>
            <PanelButton id="crash" title="System Recovery" available={true} />
            
            {/* Advanced panels - gated by flags */}
            {game.hasFlag("SYS_NANOBOT_FOUNDRY") && (
              <>
                <div className="text-emerald-300 font-medium mt-4">Nanobot Systems</div>
                <PanelButton id="nanofab" title="Nanobot Foundry" available={true} />
              </>
            )}
            
            {game.hasFlag("UI_SYNTHBAY") && (
              <>
                <div className="text-purple-300 font-medium mt-4">Synthesis</div>
                <PanelButton id="synthbay" title="Synthesis Bay" available={true} />
              </>
            )}
            
            {game.hasFlag("UI_NODEWEAVE") && (
              <>
                <div className="text-indigo-300 font-medium mt-4">Logistics</div>
                <PanelButton id="nodeweave" title="NodeWeave" available={true} />
              </>
            )}
            
            {/* Game Engine - always available for testing */}
            <div className="text-yellow-300 font-medium mt-4">Game Engine</div>
            <button
              onClick={() => game.setUIPhase("GAME_ENGINE")}
              className="w-full text-left px-3 py-2 rounded hover:bg-cyan-900/30 transition-colors text-cyan-100"
              data-testid="game-engine-button"
            >
              🎮 Multi-Renderer Engine
            </button>
            
            {/* Ghost previews of locked features */}
            {game.hasFlag("UI_GHOST_PREVIEWS") && (
              <div className="mt-6 space-y-1">
                <div className="text-gray-500 font-medium text-sm">Locked Systems</div>
                {!game.hasFlag("SYS_NANOBOT_FOUNDRY") && (
                  <div className="text-gray-600 text-sm px-3 py-1">🤖 Nanobot Foundry</div>
                )}
                {!game.hasFlag("UI_SYNTHBAY") && (
                  <div className="text-gray-600 text-sm px-3 py-1">🎵 Synthesis Bay</div>
                )}
              </div>
            )}
          </nav>
        </div>
      </div>
      
      {/* Main Panel Area */}
      <div className="flex-1 p-6">
        <MainPanel />
      </div>
    </div>
  );
}

function PanelButton({ id, title, available }: { id: string; title: string; available: boolean }) {
  const game = useGame();
  
  return (
    <button
      className={`w-full text-left px-3 py-2 rounded transition-colors ${
        available 
          ? "hover:bg-cyan-900/30 text-cyan-100" 
          : "text-gray-600 cursor-not-allowed"
      }`}
      disabled={!available}
    >
      {title}
    </button>
  );
}

function MainPanel() {
  const game = useGame();
  
  // Route to appropriate panel based on game state
  switch (game.uiPhase) {
    case "CRASH_CONSOLE":
    case "BOOTSTRAP_PANEL":
      return <CrashConsole />;
      
    case "NANOFAB_PANEL":
      return <NanoFoundry />;
      
    case "SYNTHBAY":
      return <SynthBay />;
      
    case "NODEWEAVE":
      return <NodeWeave />;
      
    case "HOLOGRAPHIC_BRIDGE":
      return <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-cyan-400 mb-4">🌌 Holographic Bridge</h2>
        <p className="text-gray-400">Full consciousness integration achieved.</p>
      </div>;
      
    case "GAME_ENGINE":
      return <GameEnginePanel />;
      
    default:
      return <CrashConsole />;
  }
}