/**
 * NanoFoundry - Advanced nanobot manufacturing interface
 */

import React, { useState } from "react";
import { useGame } from "../core/store";
import { UPGRADES } from "../../../GameDev/gameplay/progression/Upgrades";
import { calculateCostForLevel, canAffordCost, formatCost, calculateBatchCost, findMaxAffordable } from "../services/CostCurves";
import { generateUpgradeTooltip } from "../services/Tooltips";

export function NanoFoundry() {
  const game = useGame();
  const [selectedUpgrade, setSelectedUpgrade] = useState<string | null>(null);
  
  // Get nanobot-related upgrades
  const nanoUpgrades = UPGRADES.filter(upgrade => 
    upgrade.category === "NANO" || upgrade.id.includes("NANO")
  );
  
  // Get QoL upgrades unlocked by having nanobots
  const qolUpgrades = UPGRADES.filter(upgrade => 
    upgrade.category === "QOL" && 
    (!upgrade.requires || upgrade.requires.every(req => game.hasUpgrade(req)))
  );
  
  const allUpgrades = [...nanoUpgrades, ...qolUpgrades];
  
  const buyUpgrade = (upgradeId: string, amount: number = 1) => {
    const upgrade = UPGRADES.find(u => u.id === upgradeId);
    if (!upgrade) return false;
    
    const currentLevel = game.getUpgradeLevel(upgradeId);
    const totalCost = amount === 1 
      ? calculateCostForLevel(upgrade.pricer, currentLevel + 1)
      : calculateBatchCost(upgrade.pricer, currentLevel, amount);
    
    if (canAffordCost(game, totalCost) && game.spendResources(totalCost)) {
      game.buyUpgrade(upgradeId, amount);
      
      // Apply upgrade effects
      if (upgrade.grants) {
        Object.entries(upgrade.grants).forEach(([resource, grantAmount]) => {
          game.addResource(resource as any, grantAmount * amount);
        });
      }
      
      if (upgrade.flags) {
        upgrade.flags.forEach(flag => game.setFlag(flag, true));
      }
      
      return true;
    }
    
    return false;
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-emerald-400 mb-2">🤖 Nanobot Foundry</h1>
        <p className="text-gray-300">
          Advanced manufacturing and automation systems online
        </p>
        <div className="mt-4 flex justify-center space-x-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400">{game.inv.NANOBOTS}</div>
            <div className="text-sm text-gray-400">Active Nanobots</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-400">{game.upgradesPurchased}</div>
            <div className="text-sm text-gray-400">Systems Upgraded</div>
          </div>
        </div>
      </div>
      
      {/* Upgrade Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {allUpgrades.map(upgrade => {
          const level = game.getUpgradeLevel(upgrade.id);
          const nextCost = calculateCostForLevel(upgrade.pricer, level + 1);
          const canAfford = canAffordCost(game, nextCost);
          const tooltip = generateUpgradeTooltip(upgrade, game);
          const maxAffordable = findMaxAffordable(game, upgrade.pricer, level);
          
          return (
            <div 
              key={upgrade.id} 
              className={`bg-gradient-to-br from-gray-800/50 to-gray-900/50 border rounded-lg p-4 transition-all hover:border-emerald-400/50 ${
                selectedUpgrade === upgrade.id ? "border-emerald-400 shadow-lg shadow-emerald-400/20" : "border-gray-600"
              }`}
              onClick={() => setSelectedUpgrade(selectedUpgrade === upgrade.id ? null : upgrade.id)}
            >
              {/* Upgrade Header */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="font-bold text-lg text-emerald-300">{upgrade.title}</div>
                  {level > 0 && (
                    <div className="text-sm text-emerald-400">Level {level}</div>
                  )}
                  <div className="text-sm text-gray-400 mt-1">{upgrade.desc}</div>
                </div>
                {upgrade.category && (
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    upgrade.category === "NANO" ? "bg-emerald-900/50 text-emerald-300" :
                    upgrade.category === "QOL" ? "bg-blue-900/50 text-blue-300" :
                    "bg-gray-900/50 text-gray-300"
                  }`}>
                    {upgrade.category}
                  </span>
                )}
              </div>
              
              {/* Cost and Actions */}
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-sm text-gray-400 mb-1">Next Level Cost:</div>
                  <div className={`font-medium ${canAfford ? "text-emerald-400" : "text-red-400"}`}>
                    {formatCost(nextCost)}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      buyUpgrade(upgrade.id, 1);
                    }}
                    disabled={!canAfford}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      canAfford 
                        ? "bg-emerald-600 hover:bg-emerald-700 text-white" 
                        : "bg-gray-700 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    +1
                  </button>
                  
                  {game.hasFlag("UI_BATCH_BUY") && maxAffordable > 1 && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          buyUpgrade(upgrade.id, Math.min(10, maxAffordable));
                        }}
                        className="px-3 py-1 rounded text-sm font-medium bg-emerald-700 hover:bg-emerald-800 text-white"
                      >
                        +10
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          buyUpgrade(upgrade.id, maxAffordable);
                        }}
                        className="px-3 py-1 rounded text-sm font-medium bg-emerald-800 hover:bg-emerald-900 text-white"
                      >
                        Max ({maxAffordable})
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              {/* Detailed Information (when selected) */}
              {selectedUpgrade === upgrade.id && game.hasFlag("UI_COST_PREVIEW") && (
                <div className="mt-4 pt-4 border-t border-gray-600">
                  <h4 className="text-sm font-medium text-emerald-400 mb-2">Cost Preview:</h4>
                  <div className="space-y-1">
                    {tooltip.preview.slice(0, 5).map(({ level: previewLevel, cost, affordable }) => (
                      <div key={previewLevel} className={`text-xs ${affordable ? "text-emerald-400" : "text-red-400"}`}>
                        Level {previewLevel}: {formatCost(cost as any)}
                      </div>
                    ))}
                  </div>
                  
                  {upgrade.flags && upgrade.flags.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-cyan-400 mb-1">Unlocks:</h4>
                      <div className="flex flex-wrap gap-1">
                        {upgrade.flags.map(flag => (
                          <span key={flag} className="px-2 py-1 bg-cyan-900/30 text-cyan-300 text-xs rounded">
                            {flag.replace("UI_", "").replace("SYS_", "")}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Status Footer */}
      <div className="bg-black/30 rounded-lg p-4 text-sm">
        <div className="flex justify-between items-center">
          <div className="text-gray-400">
            Total Nanobots: <span className="text-emerald-400 font-bold">{game.inv.NANOBOTS}</span>
          </div>
          <div className="text-gray-400">
            Automation Capacity: <span className="text-cyan-400 font-bold">{game.getUpgradeLevel("NANO_THREAD")}</span>
          </div>
          <div className="text-gray-400">
            Ship Phase: <span className="text-purple-400 font-bold">{game.uiPhase}</span>
          </div>
        </div>
      </div>
    </div>
  );
}