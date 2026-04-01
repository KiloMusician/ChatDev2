/**
 * CrashConsole - Initial Ship-AI recovery interface
 */

import React, { useState, useEffect } from "react";
import { useGame } from "../core/store";
import { UPGRADES } from "../../../GameDev/gameplay/progression/Upgrades";
import { calculateCostForLevel, canAffordCost, formatCost } from "../services/CostCurves";
import { generateUpgradeTooltip } from "../services/Tooltips";
import { RESOURCE_META } from "../../../GameDev/systems/resources/ResourceDefs";

export function CrashConsole() {
  const game = useGame();
  const [logs, setLogs] = useState<string[]>([]);
  const [terminalInput, setTerminalInput] = useState("");
  
  // Initialize with boot logs
  useEffect(() => {
    const bootLogs = [
      "> SYSTEM RECOVERY INITIATED...",
      "> Hull integrity: 23%",
      "> Power systems: MINIMAL",
      "> Crew status: 3 PODS DETECTED",
      "> AI consciousness: 0.7% AND RISING",
      "",
      "> Primary objective: SURVIVE",
      "> Secondary objective: REBUILD",
      "> Warning: Resources critically low",
      "",
      "> TIP: Collect SCRAP to begin repairs",
      "> TIP: Research upgrades to restore ship systems"
    ];
    
    setLogs(bootLogs);
    
    // DISABLED: Periodic system messages were triggering theater simulation
    // const interval = setInterval(() => {
    //   if (Math.random() < 0.1) {
    //     const messages = [
    //       "> Life support: STABLE",
    //       "> Scanner sweep: No immediate threats", 
    //       "> Memory fragment recovered",
    //       "> Power fluctuation detected"
    //     ];
    //     setLogs(prev => [...prev.slice(-15), messages[Math.floor(Math.random() * messages.length)]]);
    //   }
    // }, 3000);
    
    // return () => clearInterval(interval);
  }, []);
  
  // DISABLED: Auto-advance tick was triggering fake agent simulation
  // useEffect(() => {
  //   const ticker = setInterval(() => {
  //     game.advanceTick();
  //     
  //     // Passive resource generation
  //     if (game.tick % 5 === 0) {
  //       game.addResource("ENERGY", 1);
  //     }
  //     if (game.tick % 10 === 0) {
  //       game.addResource("SCRAP", 1);
  //     }
  //   }, 2000);
  //   
  //   return () => clearInterval(ticker);
  // }, [game.tick]);
  
  const handleCommand = (cmd: string) => {
    const command = cmd.trim().toLowerCase();
    
    switch (command) {
      case "status":
        setLogs(prev => [...prev, 
          `> SHIP STATUS:`,
          `> Tick: ${game.tick}`,
          `> Phase: ${game.uiPhase}`,
          `> Resources: ${Object.entries(game.inv).filter(([,v]) => v > 0).map(([k,v]) => `${k}:${v}`).join(", ")}`
        ]);
        break;
        
      case "help":
        setLogs(prev => [...prev,
          `> AVAILABLE COMMANDS:`,
          `> status - Show ship status`,
          `> inv - Show inventory`, 
          `> help - Show this help`,
          `> clear - Clear logs`
        ]);
        break;
        
      case "inv":
        setLogs(prev => [...prev, 
          `> INVENTORY:`,
          ...Object.entries(game.inv).filter(([,v]) => v > 0).map(([k,v]) => `> ${RESOURCE_META[k as keyof typeof RESOURCE_META]?.icon || "📦"} ${k}: ${v}`)
        ]);
        break;
        
      case "clear":
        setLogs([]);
        break;
        
      default:
        setLogs(prev => [...prev, `> Unknown command: ${cmd}`]);
    }
    
    setTerminalInput("");
  };
  
  // Get available upgrades for this phase
  const availableUpgrades = UPGRADES.filter(upgrade => 
    upgrade.category === "CORE" && 
    (!upgrade.requires || upgrade.requires.every(req => game.hasUpgrade(req)))
  );
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* System Recovery Panel */}
      <div className="bg-black/50 border border-gray-700 rounded-lg p-4">
        <h2 className="text-xl font-bold text-red-400 mb-4 flex items-center">
          ⚠️ SYSTEM RECOVERY
        </h2>
        
        {/* Resource Display */}
        <div className="mb-6">
          <h3 className="text-lg text-green-400 mb-2">Resources</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(game.inv).filter(([,amount]) => amount > 0).map(([resource, amount]) => {
              const meta = RESOURCE_META[resource as keyof typeof RESOURCE_META];
              return (
                <div key={resource} className="flex items-center space-x-2 bg-gray-800/50 px-3 py-2 rounded">
                  <span className="text-lg">{meta?.icon || "📦"}</span>
                  <span className={meta?.color || "text-gray-400"}>{resource}</span>
                  <span className="text-white font-bold">{amount}</span>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Available Upgrades */}
        <div>
          <h3 className="text-lg text-cyan-400 mb-3">Ship Repairs</h3>
          <div className="space-y-3">
            {availableUpgrades.map(upgrade => {
              const level = game.getUpgradeLevel(upgrade.id);
              const nextCost = calculateCostForLevel(upgrade.pricer, level + 1);
              const canAfford = canAffordCost(game, nextCost);
              const tooltip = generateUpgradeTooltip(upgrade, game);
              
              return (
                <div key={upgrade.id} className="bg-gray-800/30 border border-gray-600 rounded p-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-bold text-cyan-300">{upgrade.title}</div>
                      {level > 0 && <span className="text-sm text-gray-400">[Level {level}]</span>}
                      <div className="text-sm text-gray-300 mt-1">{upgrade.desc}</div>
                      
                      {game.hasFlag("UI_COST_PREVIEW") && tooltip.preview.length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-cyan-400 cursor-pointer">Show cost preview</summary>
                          <div className="mt-1 text-xs text-gray-400">
                            {tooltip.preview.slice(0, 3).map(({ level: previewLevel, cost, affordable }) => (
                              <div key={previewLevel} className={affordable ? "text-green-400" : "text-red-400"}>
                                Lv.{previewLevel}: {formatCost(cost)}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                    
                    <div className="text-right ml-4">
                      <div className="text-sm text-gray-400">
                        Cost: {formatCost(nextCost)}
                      </div>
                      <button
                        onClick={() => {
                          if (canAfford && game.spendResources(nextCost)) {
                            game.buyUpgrade(upgrade.id, 1);
                            
                            // Apply upgrade effects
                            if (upgrade.grants) {
                              Object.entries(upgrade.grants).forEach(([resource, amount]) => {
                                game.addResource(resource as any, amount);
                              });
                            }
                            
                            if (upgrade.flags) {
                              upgrade.flags.forEach(flag => game.setFlag(flag, true));
                            }
                            
                            setLogs(prev => [...prev, `> ${upgrade.title} upgraded to level ${level + 1}`]);
                          }
                        }}
                        disabled={!canAfford}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                          canAfford 
                            ? "bg-cyan-600 hover:bg-cyan-700 text-white" 
                            : "bg-gray-700 text-gray-500 cursor-not-allowed"
                        }`}
                      >
                        {canAfford ? "Repair" : "Insufficient"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Terminal Console */}
      <div className="bg-black/70 border border-green-700 rounded-lg p-4 font-mono">
        <h2 className="text-xl font-bold text-green-400 mb-4">SYSTEM TERMINAL</h2>
        
        {/* Log Display */}
        <div className="bg-black rounded p-3 h-80 overflow-y-auto mb-4 text-sm">
          {logs.map((log, i) => (
            <div key={i} className={log.startsWith(">") ? "text-green-400" : "text-gray-300"}>
              {log}
            </div>
          ))}
        </div>
        
        {/* Command Input */}
        {game.hasFlag("UI_TERMINAL_INTERACTIVE") ? (
          <div className="flex">
            <span className="text-green-400 mr-2">{">"}</span>
            <input
              type="text"
              value={terminalInput}
              onChange={(e) => setTerminalInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCommand(terminalInput)}
              className="flex-1 bg-transparent border-none outline-none text-green-400"
              placeholder="Enter command..."
            />
          </div>
        ) : (
          <div className="text-gray-500 text-sm">
            [Terminal input locked - upgrade required]
          </div>
        )}
      </div>
    </div>
  );
}