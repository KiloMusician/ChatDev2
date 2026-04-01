import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { useGameState, useColonyHealth, isLiveStateStale } from '@/hooks/useLiveSystemState';
import { Settings, Gamepad2, Bot, Zap, Volume2, Eye, Cpu, Database, RotateCcw } from 'lucide-react';

function SettingsPanelWrapped() {
  const gameState = useGameState();
  const colonyHealth = useColonyHealth();
  const gameStale = isLiveStateStale('game.state_update');
  const colonyStale = isLiveStateStale('pawn_registry.status_update');
  
  // Game settings state
  const [gameSettings, setGameSettings] = useState({
    autoSave: true,
    autoTick: false,
    tickSpeed: 1000,
    soundEffects: true,
    tooltips: true,
    animations: true,
    difficulty: 'normal'
  });
  
  // System settings state
  const [systemSettings, setSystemSettings] = useState({
    agentLogging: true,
    councilBusVerbose: false,
    puQueueEnabled: true,
    consciousnessDisplay: true,
    performanceMode: false,
    debugMode: false,
    theatricalMode: false
  });
  
  useEffect(() => {
    // Load settings from localStorage
    const savedGameSettings = localStorage.getItem('game_settings');
    if (savedGameSettings) {
      try {
        setGameSettings(JSON.parse(savedGameSettings));
      } catch (error) {
        console.warn('Failed to load game settings:', error);
      }
    }
    
    const savedSystemSettings = localStorage.getItem('system_settings');
    if (savedSystemSettings) {
      try {
        setSystemSettings(JSON.parse(savedSystemSettings));
      } catch (error) {
        console.warn('Failed to load system settings:', error);
      }
    }
  }, []);
  
  const saveSettings = (type: 'game' | 'system', newSettings: any) => {
    if (type === 'game') {
      localStorage.setItem('game_settings', JSON.stringify(newSettings));
      setGameSettings(newSettings);
    } else {
      localStorage.setItem('system_settings', JSON.stringify(newSettings));
      setSystemSettings(newSettings);
    }
  };
  
  const resetToDefaults = () => {
    const confirmReset = confirm('Reset all settings to defaults? This cannot be undone.');
    if (confirmReset) {
      localStorage.removeItem('game_settings');
      localStorage.removeItem('system_settings');
      window.location.reload();
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent flex items-center justify-center gap-3">
            <Settings className="w-8 h-8 text-cyan-400" />
            System Configuration
          </h1>
          <p className="text-blue-200">Configure game mechanics and system behavior</p>
        </div>

        {/* Current System Status */}
        <Card className="bg-black/40 border-cyan-500/30">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Current System Status
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {gameStale ? '—' : gameState.tick}
                </div>
                <div className="text-gray-300">Game Ticks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {colonyStale ? '—' : colonyHealth.total_pawns}
                </div>
                <div className="text-gray-300">Active Agents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {colonyStale ? '—' : `${Math.round(colonyHealth.colony_productivity * 10)}%`}
                </div>
                <div className="text-gray-300">Productivity</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {colonyStale ? '—' : `${Math.round((colonyHealth.average_energy + colonyHealth.average_focus) / 2)}%`}
                </div>
                <div className="text-gray-300">Health</div>
              </div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Game Settings */}
          <Card className="bg-black/40 border-green-500/30">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-green-400 mb-4 flex items-center gap-2">
                <Gamepad2 className="w-5 h-5" />
                Game Settings
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-4 h-4" />
                    <span>Sound Effects</span>
                  </div>
                  <Switch
                    checked={gameSettings.soundEffects}
                    onCheckedChange={(checked) => saveSettings('game', { ...gameSettings, soundEffects: checked })}
                    data-testid="switch-sound-effects"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>Show Tooltips</span>
                  </div>
                  <Switch
                    checked={gameSettings.tooltips}
                    onCheckedChange={(checked) => saveSettings('game', { ...gameSettings, tooltips: checked })}
                    data-testid="switch-tooltips"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    <span>Auto-Save</span>
                  </div>
                  <Switch
                    checked={gameSettings.autoSave}
                    onCheckedChange={(checked) => saveSettings('game', { ...gameSettings, autoSave: checked })}
                    data-testid="switch-auto-save"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    <span>Auto-Tick</span>
                  </div>
                  <Switch
                    checked={gameSettings.autoTick}
                    onCheckedChange={(checked) => saveSettings('game', { ...gameSettings, autoTick: checked })}
                    data-testid="switch-auto-tick"
                  />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>Tick Speed: {gameSettings.tickSpeed}ms</span>
                  </div>
                  <Slider
                    value={[gameSettings.tickSpeed]}
                    onValueChange={([value]) => saveSettings('game', { ...gameSettings, tickSpeed: value })}
                    min={100}
                    max={5000}
                    step={100}
                    className="w-full"
                    data-testid="slider-tick-speed"
                  />
                </div>
                
                <div className="pt-4 border-t border-green-500/30">
                  <div className="text-sm text-gray-400 mb-2">Difficulty Mode</div>
                  <div className="grid grid-cols-3 gap-2">
                    {['easy', 'normal', 'hard'].map((diff) => (
                      <Button
                        key={diff}
                        size="sm"
                        variant={gameSettings.difficulty === diff ? "default" : "outline"}
                        onClick={() => saveSettings('game', { ...gameSettings, difficulty: diff })}
                        className={gameSettings.difficulty === diff ? 'bg-green-600' : 'border-green-500/50'}
                        data-testid={`button-difficulty-${diff}`}
                      >
                        {diff.charAt(0).toUpperCase() + diff.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* System Settings */}
          <Card className="bg-black/40 border-blue-500/30">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-blue-400 mb-4 flex items-center gap-2">
                <Bot className="w-5 h-5" />
                System Settings
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4" />
                    <span>Agent Logging</span>
                  </div>
                  <Switch
                    checked={systemSettings.agentLogging}
                    onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, agentLogging: checked })}
                    data-testid="switch-agent-logging"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    <span>Council Bus Verbose</span>
                  </div>
                  <Switch
                    checked={systemSettings.councilBusVerbose}
                    onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, councilBusVerbose: checked })}
                    data-testid="switch-council-verbose"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    <span>PU Queue Processing</span>
                  </div>
                  <Switch
                    checked={systemSettings.puQueueEnabled}
                    onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, puQueueEnabled: checked })}
                    data-testid="switch-pu-queue"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>Consciousness Display</span>
                  </div>
                  <Switch
                    checked={systemSettings.consciousnessDisplay}
                    onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, consciousnessDisplay: checked })}
                    data-testid="switch-consciousness"
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    <span>Performance Mode</span>
                  </div>
                  <Switch
                    checked={systemSettings.performanceMode}
                    onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, performanceMode: checked })}
                    data-testid="switch-performance-mode"
                  />
                </div>
                
                <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/30">
                  <div className="text-sm text-red-200 mb-3">
                    <strong>⚠️ Dangerous Settings:</strong> These affect system behavior
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Debug Mode</span>
                      <Switch
                        checked={systemSettings.debugMode}
                        onCheckedChange={(checked) => saveSettings('system', { ...systemSettings, debugMode: checked })}
                        data-testid="switch-debug-mode"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-red-300">Theatrical Mode (Disabled)</span>
                      <Switch
                        checked={false}
                        disabled
                        data-testid="switch-theatrical-disabled"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
        
        {/* Advanced Configuration */}
        <Card className="bg-black/40 border-purple-500/30">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-purple-400 mb-4">🔧 Advanced Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Button 
                  onClick={() => window.location.href = '/admin'}
                  variant="outline"
                  className="w-full border-red-500/50 text-red-400 hover:bg-red-500/20"
                  data-testid="button-dev-tokens"
                >
                  🪙 Dev Tokens
                </Button>
                <p className="text-xs text-gray-400">Access token management and system credits</p>
              </div>
              
              <div className="space-y-2">
                <Button 
                  onClick={() => {
                    // Clear all localStorage and reset
                    const confirmReset = confirm('Reset all game and system data? This will delete all saves!');
                    if (confirmReset) {
                      localStorage.clear();
                      window.location.href = '/';
                    }
                  }}
                  variant="outline"
                  className="w-full border-orange-500/50 text-orange-400 hover:bg-orange-500/20"
                  data-testid="button-factory-reset"
                >
                  🏭 Factory Reset
                </Button>
                <p className="text-xs text-gray-400">Complete system and game state reset</p>
              </div>
              
              <div className="space-y-2">
                <Button 
                  onClick={() => {
                    const exportData = {
                      gameSettings,
                      systemSettings,
                      gameState,
                      timestamp: Date.now()
                    };
                    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `corelink_backup_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  variant="outline"
                  className="w-full border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                  data-testid="button-export-data"
                >
                  📦 Export Data
                </Button>
                <p className="text-xs text-gray-400">Download complete system backup</p>
              </div>
            </div>
          </div>
        </Card>
        
        {/* Actions */}
        <div className="text-center space-x-4">
          <Button
            onClick={resetToDefaults}
            variant="outline"
            className="border-orange-500/50 text-orange-400 hover:bg-orange-500/20"
            data-testid="button-reset-defaults"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset to Defaults
          </Button>
          
          <Button
            onClick={() => window.location.href = '/game-menu'}
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
            data-testid="button-return-to-game"
          >
            🎮 Return to Game Menu
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPanel() {
  return (
    <ErrorBoundary>
      <SettingsPanelWrapped />
    </ErrorBoundary>
  );
}
