import { useEffect, useRef, useState } from "react";
import { startGame, stopGame, getGameManagers } from "../../game/game";
import { bus } from "../../game/events";
import { tiers } from "../../game/tiers";

export default function AsciiRoguelike() {
  const mountRef = useRef<HTMLPreElement>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [gameStats, setGameStats] = useState({ 
    tier: 1, 
    xp: 0, 
    receipts: 0,
    energy: 0,
    materials: 0,
    structures: 0,
    enemies: 0,
    wave: 0,
    waveActive: false,
  });

  useEffect(() => {
    if (mountRef.current && !isRunning) {
      startGame({ mount: mountRef.current });
      setIsRunning(true);
    }

    // Listen for receipts and breath ticks
    const handleReceipt = (receipt: any) => {
      setGameStats(prev => ({ ...prev, receipts: prev.receipts + 1 }));
    };

    const handleBreathTick = () => {
      const managers = getGameManagers();
      if (managers.resourceManager && managers.structureManager && managers.enemyManager && managers.waveManager) {
        const waveStats = managers.waveManager.getWaveStats();
        setGameStats(prev => ({
          tier: tiers.tier,
          xp: tiers.xp,
          receipts: prev.receipts,
          energy: Math.floor(managers.resourceManager!.getAmount("energy")),
          materials: Math.floor(managers.resourceManager!.getAmount("materials")),
          structures: managers.structureManager!.getAll().length,
          enemies: managers.enemyManager!.getAll().length,
          wave: waveStats.currentWave,
          waveActive: waveStats.isActive,
        }));
      }
    };

    bus.on("receipt", handleReceipt);
    bus.on("breath:tick", handleBreathTick);

    return () => {
      bus.off("receipt", handleReceipt);
      bus.off("breath:tick", handleBreathTick);
      if (isRunning) {
        stopGame();
        setIsRunning(false);
      }
    };
  }, [isRunning]);

  return (
    <div className="bg-slate-900/50 rounded-xl border border-green-400/30 overflow-hidden">
      <div className="bg-green-600/10 p-3 border-b border-green-400/20">
        <div className="text-green-300 font-semibold">🎮 ASCII Roguelike - Real Running Game</div>
        <div className="text-xs text-green-200/70">
          Live idle mechanics, ECS system, and Culture-Ship receipt integration
        </div>
        <div className="text-xs text-green-200/50 mt-1 grid grid-cols-2 gap-2">
          <div>Tier {gameStats.tier} | XP: {gameStats.xp}</div>
          <div>Wave: {gameStats.wave} {gameStats.waveActive ? "(Active)" : ""}</div>
          <div>⚡ Energy: {gameStats.energy} | 🔧 Materials: {gameStats.materials}</div>
          <div>🏗️ Structures: {gameStats.structures} | 👹 Enemies: {gameStats.enemies}</div>
        </div>
      </div>
      
      <div className="bg-black p-4">
        <pre
          ref={mountRef}
          className="w-full h-96 text-green-400 font-mono text-sm overflow-auto bg-black"
          style={{ lineHeight: 1.2 }}
        />
        
        <div className="mt-3 text-xs text-green-200/70 space-y-1">
          <div>🎯 Use WASD or arrow keys to move the @ symbol around</div>
          <div>⛏️ Press SPACE or ENTER to spawn energy resources at your location</div>
          <div>🏗️ Press B to build structures (generator, turret, storage)</div>
          <div>🌊 Press W to start next wave if available</div>
          <div>💾 Press S to save game state</div>
          <div>📈 Idle resources generate automatically, build economy and defenses</div>
          <div className="text-orange-300 mt-2">
            🌌 Full ECS game: Resources → Structures → Waves → Combat → Progression
          </div>
          <div className="text-cyan-300 mt-2 font-bold">
            🎮 COMPREHENSIVE GAME SYSTEMS ACTIVE - Tower Defense + Idle + RPG!
          </div>
        </div>
      </div>
    </div>
  );
}