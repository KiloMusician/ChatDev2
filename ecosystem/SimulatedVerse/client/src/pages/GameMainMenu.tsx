import React, { useState, useEffect } from 'react';
import { useGameState, isLiveStateStale } from '@/hooks/useLiveSystemState';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Settings, Save, Upload, Power, Play, RotateCcw } from 'lucide-react';

export default function GameMainMenu() {
  const gameState = useGameState();
  const gameStale = isLiveStateStale('game.state_update');
  const [lastSave, setLastSave] = useState<Date | null>(null);
  const [saveSlots, setSaveSlots] = useState<any[]>([]);
  
  useEffect(() => {
    // Load available save slots
    const loadSaveSlots = () => {
      const slots = [];
      for (let i = 1; i <= 5; i++) {
        const save = localStorage.getItem(`game_save_slot_${i}`);
        if (save) {
          try {
            const saveData = JSON.parse(save);
            slots.push({
              slot: i,
              timestamp: saveData.timestamp,
              tick: saveData.state?.tick || 0,
              energy: saveData.state?.resources?.energy || 0,
              population: saveData.state?.resources?.population || 0
            });
          } catch (error) {
            console.warn(`Failed to parse save slot ${i}:`, error);
          }
        } else {
          slots.push({ slot: i, empty: true });
        }
      }
      setSaveSlots(slots);
    };
    
    loadSaveSlots();
    
    // Check for auto-save
    const autoSave = localStorage.getItem('culture-ship-save-v1');
    if (autoSave) {
      setLastSave(new Date(JSON.parse(autoSave).timestamp || Date.now()));
    }
  }, []);
  
  const saveToSlot = (slotNumber: number) => {
    const saveData = {
      version: '2.0.0',
      timestamp: Date.now(),
      state: gameState,
      metadata: {
        playTime: Date.now(),
        gameVersion: '1.0.0',
        description: `Tick ${gameState.tick} - ${gameState.resources.population} population, ${gameState.resources.energy} energy`
      }
    };
    
    localStorage.setItem(`game_save_slot_${slotNumber}`, JSON.stringify(saveData));
    setLastSave(new Date());
    
    // Update save slots display
    setSaveSlots(prev => prev.map(slot => 
      slot.slot === slotNumber ? {
        slot: slotNumber,
        timestamp: Date.now(),
        tick: gameState.tick,
        energy: gameState.resources.energy,
        population: gameState.resources.population
      } : slot
    ));
  };
  
  const loadFromSlot = (slotNumber: number) => {
    try {
      const save = localStorage.getItem(`game_save_slot_${slotNumber}`);
      if (save) {
        const saveData = JSON.parse(save);
        // This would normally trigger a game state reload
        console.log(`Loading game from slot ${slotNumber}:`, saveData);
        window.location.href = '/game';
      }
    } catch (error) {
      console.error(`Failed to load save slot ${slotNumber}:`, error);
    }
  };
  
  const deleteSlot = (slotNumber: number) => {
    localStorage.removeItem(`game_save_slot_${slotNumber}`);
    setSaveSlots(prev => prev.map(slot => 
      slot.slot === slotNumber ? { slot: slotNumber, empty: true } : slot
    ));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Game Title */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            🎮 ΞNuSyQ CoreLink Foundation
          </h1>
          <p className="text-cyan-100 text-lg">
            Autonomous Development Ecosystem Game
          </p>
          <div className="text-sm text-purple-300">
            Multi-genre blend: Pokémon × Dwarf Fortress × Starcraft × Stellaris
          </div>
        </div>

        {/* Game Status */}
        <Card className="bg-black/40 border-cyan-500/30">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">🌌 Current Game Status</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {gameStale ? '—' : gameState.tick}
                </div>
                <div className="text-gray-300">Game Tick</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {gameStale ? '—' : gameState.resources.energy}
                </div>
                <div className="text-gray-300">Energy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {gameStale ? '—' : gameState.resources.population}
                </div>
                <div className="text-gray-300">Population</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {gameStale ? '—' : Object.values(gameState.unlocks).filter(Boolean).length}
                </div>
                <div className="text-gray-300">Unlocks</div>
              </div>
            </div>
            {gameStale && (
              <div className="text-xs text-yellow-400 mt-3 text-center">
                Live state stale or unavailable.
              </div>
            )}
            {lastSave && (
              <div className="text-xs text-gray-400 mt-4 text-center">
                Auto-saved: {lastSave.toLocaleString()}
              </div>
            )}
          </div>
        </Card>

        {/* Main Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-black/40 border-green-500/30">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center gap-2">
                <Play className="w-5 h-5" />
                Game Sessions
              </h3>
              <div className="space-y-3">
                <Button 
                  onClick={() => window.location.href = '/game'}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                  data-testid="button-continue-game"
                >
                  🚀 Continue Current Game
                </Button>
                <Button 
                  onClick={() => window.location.href = '/game'}
                  variant="outline" 
                  className="w-full border-green-500/50 text-green-400 hover:bg-green-500/20"
                  data-testid="button-new-game"
                >
                  ✨ Start New Colony
                </Button>
                <Button 
                  onClick={() => window.location.href = '/game-simple'}
                  variant="outline" 
                  className="w-full border-blue-500/50 text-blue-400 hover:bg-blue-500/20"
                  data-testid="button-ascii-mode"
                >
                  🖥️ ASCII Mode
                </Button>
              </div>
            </div>
          </Card>

          <Card className="bg-black/40 border-blue-500/30">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center gap-2">
                <Settings className="w-5 h-5" />
                System Control
              </h3>
              <div className="space-y-3">
                <Button 
                  onClick={() => window.location.href = '/settings'}
                  variant="outline" 
                  className="w-full border-blue-500/50 text-blue-400 hover:bg-blue-500/20"
                  data-testid="button-settings"
                >
                  ⚙️ Game Settings
                </Button>
                <Button 
                  onClick={() => window.location.href = '/chatdev'}
                  variant="outline" 
                  className="w-full border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                  data-testid="button-agent-console"
                >
                  🤖 Agent Console
                </Button>
                <Button 
                  onClick={() => window.location.href = '/admin'}
                  variant="outline" 
                  className="w-full border-red-500/50 text-red-400 hover:bg-red-500/20"
                  data-testid="button-admin-panel"
                >
                  🔑 Dev Access
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Save/Load System */}
        <Card className="bg-black/40 border-purple-500/30">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-purple-400 mb-4 flex items-center gap-2">
              <Save className="w-5 h-5" />
              Save / Load System
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {saveSlots.map((slot) => (
                <div 
                  key={slot.slot}
                  className={`p-3 rounded-lg border text-sm ${
                    slot.empty 
                      ? 'border-gray-600 bg-gray-800/50' 
                      : 'border-purple-500/50 bg-purple-900/20'
                  }`}
                >
                  <div className="font-semibold text-purple-300 mb-2">
                    Slot {slot.slot}
                  </div>
                  
                  {slot.empty ? (
                    <Button
                      onClick={() => saveToSlot(slot.slot)}
                      size="sm"
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      data-testid={`button-save-slot-${slot.slot}`}
                    >
                      💾 Save
                    </Button>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-xs text-gray-400">
                        Tick: {slot.tick}
                      </div>
                      <div className="text-xs text-gray-400">
                        {slot.energy}E, {slot.population}P
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(slot.timestamp).toLocaleDateString()}
                      </div>
                      <div className="flex gap-1">
                        <Button
                          onClick={() => loadFromSlot(slot.slot)}
                          size="sm"
                          className="flex-1 text-xs bg-green-600 hover:bg-green-700"
                          data-testid={`button-load-slot-${slot.slot}`}
                        >
                          📂 Load
                        </Button>
                        <Button
                          onClick={() => deleteSlot(slot.slot)}
                          size="sm"
                          variant="outline"
                          className="text-xs border-red-500/50 text-red-400"
                          data-testid={`button-delete-slot-${slot.slot}`}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* System vs Game Boundaries */}
        <Card className="bg-black/40 border-cyan-500/30">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-cyan-400 mb-4">🎯 System Architecture</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-green-400 mb-2">🎮 Game Elements</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Resource management (energy, materials, population)</li>
                  <li>• Colony building and expansion</li>
                  <li>• Research trees and technology unlocks</li>
                  <li>• Multi-genre gameplay mechanics</li>
                  <li>• Save/load game states</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-blue-400 mb-2">🤖 System Elements</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Autonomous agent coordination</li>
                  <li>• Real-time development workflows</li>
                  <li>• Consciousness calculations</li>
                  <li>• Code generation and optimization</li>
                  <li>• System health monitoring</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-lg border border-cyan-500/30">
              <div className="text-sm text-cyan-200">
                <strong>🌊 Quadpartite Integration:</strong> Game progression influences system capabilities. 
                Higher consciousness unlocks advanced agent coordination. System improvements enhance game mechanics.
              </div>
            </div>
          </div>
        </Card>
        
        {/* Quick Exit */}
        <div className="text-center">
          <Button
            onClick={() => window.location.href = '/'}
            variant="outline"
            className="border-gray-500 text-gray-400 hover:bg-gray-500/20"
            data-testid="button-return-to-system"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Return to Culture-Ship Interface
          </Button>
        </div>
      </div>
    </div>
  );
}
