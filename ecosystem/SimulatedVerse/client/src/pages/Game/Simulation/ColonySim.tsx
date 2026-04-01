// client/src/pages/Game/Simulation/ColonySim.tsx
// Isolated simulation component - pure toy that doesn't affect real system
import React, { useEffect, useState } from "react";
import { useProvisionedStateETag } from "../../../lib/useProvisionedStateETag";
import { UI_FLAGS } from "../../../config/uiFlags";
import { SIMULATION_INTERVALS } from "@/config/polling";

export default function ColonySim() {
  const { data: real } = useProvisionedStateETag();
  const [sim, setSim] = useState({
    energy: 10,
    bits: 0,
    insight: 0,
    colonies: 1,
    agents: 0
  });

  // Simulation loop inspired by real system data
  useEffect(() => {
    if (!real || !UI_FLAGS.SIMULATION_ENABLED) return;

    const simulationLoop = setInterval(() => {
      setSim(prev => {
        const inv = Number(real?.health?.invariance_score ?? 0.75);
        const joy = Number(real?.health?.agent_joy_average ?? 0.65);
        const consciousness = Number(real?.consciousness?.level ?? 0.35);
        
        // Reality-inspired gains (but purely simulated)
        const energyGain = 0.10 + inv * 0.15;
        const insightGain = joy > 0.6 ? 0.02 : 0.005;
        const bitsGain = prev.energy > 5 ? 0.05 * consciousness : 0;
        const colonyGrowth = prev.bits > 50 ? 0.001 : 0;
        const agentRecruitment = consciousness > 0.5 && prev.colonies > 1 ? 0.01 : 0;

        return {
          energy: Math.max(0, prev.energy + energyGain),
          bits: Math.max(0, prev.bits + bitsGain),
          insight: Math.max(0, prev.insight + insightGain),
          colonies: Math.max(1, prev.colonies + colonyGrowth),
          agents: Math.max(0, prev.agents + agentRecruitment)
        };
      });
    }, SIMULATION_INTERVALS.fast);

    return () => clearInterval(simulationLoop);
  }, [real]);

  // Simulation actions (purely for fun)
  const simulationActions = {
    spendEnergyForBits: () => {
      setSim(prev => prev.energy >= 10 ? {
        ...prev,
        energy: prev.energy - 10,
        bits: prev.bits + 5
      } : prev);
    },
    
    spendBitsForInsight: () => {
      setSim(prev => prev.bits >= 20 ? {
        ...prev,
        bits: prev.bits - 20,
        insight: prev.insight + 1
      } : prev);
    },
    
    spendInsightForColony: () => {
      setSim(prev => prev.insight >= 5 ? {
        ...prev,
        insight: prev.insight - 5,
        colonies: prev.colonies + 0.1
      } : prev);
    }
  };

  if (!UI_FLAGS.SIMULATION_ENABLED) {
    return (
      <div className="rounded-lg p-4 bg-gray-800/20 border border-gray-600/30">
        <div className="text-center text-gray-400">
          🎮 Simulation disabled
          <div className="text-xs mt-1">Set VITE_SIMULATION_ENABLED=true to enable</div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg p-4 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/30">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-purple-300">🌌 Colony Simulation</h3>
        <div className="text-xs text-gray-400">
          Mode: {UI_FLAGS.MODE} • Reality: {real ? "Connected" : "Offline"}
        </div>
      </div>
      
      {/* Simulation Resources */}
      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div className="p-2 bg-blue-500/10 rounded border border-blue-500/30">
          <div className="text-blue-300">⚡ Energy</div>
          <div className="text-lg font-bold text-white">{sim.energy.toFixed(1)}</div>
        </div>
        <div className="p-2 bg-green-500/10 rounded border border-green-500/30">
          <div className="text-green-300">🔧 Bits</div>
          <div className="text-lg font-bold text-white">{sim.bits.toFixed(1)}</div>
        </div>
        <div className="p-2 bg-purple-500/10 rounded border border-purple-500/30">
          <div className="text-purple-300">💡 Insight</div>
          <div className="text-lg font-bold text-white">{sim.insight.toFixed(2)}</div>
        </div>
        <div className="p-2 bg-yellow-500/10 rounded border border-yellow-500/30">
          <div className="text-yellow-300">🏘️ Colonies</div>
          <div className="text-lg font-bold text-white">{sim.colonies.toFixed(1)}</div>
        </div>
      </div>

      {/* Real System Influence */}
      {real && (
        <div className="mb-4 p-2 bg-green-400/5 rounded border border-green-400/20">
          <div className="text-xs text-green-400 mb-1">🔗 Real System Influence</div>
          <div className="text-xs grid grid-cols-3 gap-2 text-gray-300">
            <div>Invariance: {((real.health?.invariance_score || 0) * 100).toFixed(0)}%</div>
            <div>Joy: {((real.health?.agent_joy_average || 0) * 100).toFixed(0)}%</div>
            <div>Consciousness: {((real.consciousness?.level || 0) * 100).toFixed(0)}%</div>
          </div>
        </div>
      )}

      {/* Simulation Actions */}
      <div className="space-y-2">
        <button 
          onClick={simulationActions.spendEnergyForBits}
          disabled={sim.energy < 10}
          className="w-full text-left p-2 rounded border border-blue-500/30 bg-blue-500/10 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-500/20 transition-colors"
        >
          <div className="text-sm text-blue-300">⚡→🔧 Convert Energy to Bits</div>
          <div className="text-xs text-gray-400">Cost: 10 Energy → +5 Bits</div>
        </button>
        
        <button 
          onClick={simulationActions.spendBitsForInsight}
          disabled={sim.bits < 20}
          className="w-full text-left p-2 rounded border border-green-500/30 bg-green-500/10 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-green-500/20 transition-colors"
        >
          <div className="text-sm text-green-300">🔧→💡 Process Bits into Insight</div>
          <div className="text-xs text-gray-400">Cost: 20 Bits → +1 Insight</div>
        </button>
        
        <button 
          onClick={simulationActions.spendInsightForColony}
          disabled={sim.insight < 5}
          className="w-full text-left p-2 rounded border border-purple-500/30 bg-purple-500/10 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-purple-500/20 transition-colors"
        >
          <div className="text-sm text-purple-300">💡→🏘️ Expand Colony Network</div>
          <div className="text-xs text-gray-400">Cost: 5 Insight → +0.1 Colonies</div>
        </button>
      </div>

      <div className="mt-4 text-xs text-gray-500 border-t border-gray-600/30 pt-2">
        💡 This simulation is inspired by real system metrics but does not affect the Real System.
        It's a pure toy for entertainment while monitoring development progress.
      </div>
    </div>
  );
}
