/**
 * Game Engine Panel - Multi-renderer game engine interface
 * Integrates with existing Culture-Ship system while maintaining separation
 */

import React, { useState, useEffect, useRef } from 'react';
import { useGame } from '../core/store';
import { MultiRenderer, type RenderMode } from '../../../GameDev/engine/MultiRenderer.js';
import { simulator } from '../../../GameDev/engine/core/sim.js';
import { dungeonGenerator } from '../../../GameDev/patterns/roguelike/dungeon.js';
import { waveManager } from '../../../GameDev/patterns/tower_defense/waves.js';
import { productionManager } from '../../../GameDev/patterns/colony_sim/production.js';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export type GameMode = 'roguelike' | 'tower_defense' | 'colony_sim';

export function GameEnginePanel() {
  const game = useGame();
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderer, setRenderer] = useState<MultiRenderer | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>('ascii');
  const [gameMode, setGameMode] = useState<GameMode>('roguelike');
  const [isRunning, setIsRunning] = useState(false);
  const [fps, setFps] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const animationRef = useRef<number>();
  
  // Initialize renderer
  useEffect(() => {
    if (!containerRef.current) return;
    
    const newRenderer = new MultiRenderer({
      mode: renderMode,
      width: 800,
      height: 600,
      container: containerRef.current
    });
    
    setRenderer(newRenderer);
    
    return () => {
      if (newRenderer && 'cleanup' in newRenderer) (newRenderer as any).cleanup();
    };
  }, [renderMode]);
  
  // Game loop
  useEffect(() => {
    if (!isRunning || !renderer) return;
    
    const startTime = performance.now();
    let lastFrame = startTime;
    let frameCount = 0;
    
    const gameLoop = (currentTime: number) => {
      const deltaTime = currentTime - lastFrame;
      lastFrame = currentTime;
      
      // Update simulation
      simulator?.update?.(deltaTime);
      
      // Update genre-specific systems
      switch (gameMode) {
        case 'tower_defense':
          waveManager.update(deltaTime);
          break;
        case 'colony_sim':
          productionManager.update(deltaTime);
          break;
        // Roguelike is turn-based, no real-time updates needed
      }
      
      // Render frame
      const renderState = simulator.getRenderState();
      renderer.render(renderState);
      
      // Update FPS counter
      frameCount++;
      if (currentTime - startTime >= 1000) {
        setFps(frameCount);
        setFrameCount(prev => prev + frameCount);
        frameCount = 0;
      }
      
      // Schedule next frame
      animationRef.current = requestAnimationFrame(gameLoop);
    };
    
    animationRef.current = requestAnimationFrame(gameLoop);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRunning, renderer, gameMode]);
  
  // Initialize game mode
  useEffect(() => {
    switch (gameMode) {
      case 'roguelike':
        initializeRoguelike();
        break;
      case 'tower_defense':
        initializeTowerDefense();
        break;
      case 'colony_sim':
        initializeColony();
        break;
    }
  }, [gameMode]);
  
  const initializeRoguelike = () => {
    console.log('[GameEngine] Initializing roguelike mode');
    const level = dungeonGenerator.generateLevel(64, 64, 1);
    const grid = dungeonGenerator.levelToGrid(level);
    if (simulator?.setMap) simulator.setMap(grid);
  };
  
  const initializeTowerDefense = () => {
    console.log('[GameEngine] Initializing tower defense mode');
    // Create simple path for enemies
    const path = [
      { x: 0, y: 10 }, { x: 5, y: 10 }, { x: 5, y: 5 },
      { x: 15, y: 5 }, { x: 15, y: 15 }, { x: 25, y: 15 },
      { x: 25, y: 25 }, { x: 35, y: 25 }
    ];
    waveManager.setPath(path);
    
    // Create basic grid
    const grid = Array(32).fill(null).map(() => 
      Array(32).fill({ char: '.', color: '#444', bg: '#000' })
    );
    
    // Mark path
    for (const point of path) {
      if (grid[point.y] && grid[point.y][point.x]) {
        grid[point.y][point.x] = { char: '∴', color: '#666', bg: '#000' };
      }
    }
    
    if (simulator?.setMap) simulator.setMap(grid);
  };
  
  const initializeColony = () => {
    console.log('[GameEngine] Initializing colony simulation mode');
    // Create terrain with resource nodes
    const grid = Array(32).fill(null).map((_, y) => 
      Array(32).fill(null).map((_, x) => {
        if (x === 0 || y === 0 || x === 31 || y === 31) {
          return { char: '#', color: '#888', bg: '#000' };
        }
        return { char: '.', color: '#444', bg: '#000' };
      })
    );
    
    // Add resource nodes
    for (let i = 0; i < 5; i++) {
      const x = 2 + Math.floor(Math.random() * 28);
      const y = 2 + Math.floor(Math.random() * 28);
      grid[y][x] = { char: '*', color: '#ff0', bg: '#000' };
    }
    
    if (simulator?.setMap) simulator.setMap(grid);
  };
  
  const toggleSimulation = () => {
    setIsRunning(!isRunning);
    console.log(`[GameEngine] Simulation ${!isRunning ? 'started' : 'stopped'}`);
  };
  
  const switchRenderMode = async (newMode: RenderMode) => {
    if (renderer) {
      await renderer.switchMode(newMode);
      setRenderMode(newMode);
      console.log(`[GameEngine] Switched to ${newMode} rendering`);
    }
  };
  
  const takeScreenshot = () => {
    if (renderer) {
      const dataUrl = renderer.screenshot();
      if (dataUrl) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = `game_${gameMode}_${Date.now()}.png`;
        link.click();
      }
    }
  };
  
  const resetSimulation = () => {
    simulator?.reset?.();
    setFrameCount(0);
    console.log('[GameEngine] Simulation reset');
  };

  return (
    <div className="space-y-6" data-testid="game-engine-panel">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400">🎮 Game Engine</h1>
          <p className="text-gray-400 mt-2">Multi-renderer deterministic game engine with genre modules</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant={isRunning ? "default" : "secondary"}>
            {isRunning ? 'Running' : 'Stopped'}
          </Badge>
          <Badge variant="outline">
            {fps} FPS
          </Badge>
          <Badge variant="outline">
            Frame {frameCount}
          </Badge>
        </div>
      </div>
      
      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Engine Controls</CardTitle>
          <CardDescription>Configure rendering mode, game genre, and simulation state</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Game Mode</label>
              <Select value={gameMode} onValueChange={(value: GameMode) => setGameMode(value)} data-testid="game-mode-selector">
                <SelectTrigger data-testid="select-game-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="roguelike">🗡️ Roguelike</SelectItem>
                  <SelectItem value="tower_defense">🏯 Tower Defense</SelectItem>
                  <SelectItem value="colony_sim">🏭 Colony Sim</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Render Mode</label>
              <Select value={renderMode} onValueChange={(value: RenderMode) => switchRenderMode(value)} data-testid="renderer-selector">
                <SelectTrigger data-testid="select-render-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ascii">📟 ASCII</SelectItem>
                  <SelectItem value="pixel">🎨 Pixel</SelectItem>
                  <SelectItem value="vector" disabled>📐 Vector (Soon)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Simulation</label>
              <Button 
                onClick={toggleSimulation}
                variant={isRunning ? "destructive" : "default"}
                className="w-full"
                data-testid="button-toggle-simulation"
              >
                {isRunning ? '⏸️ Pause' : '▶️ Start'}
              </Button>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Actions</label>
              <div className="flex space-x-1">
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={resetSimulation}
                  data-testid="button-reset"
                >
                  🔄
                </Button>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={takeScreenshot}
                  data-testid="button-screenshot"
                >
                  📷
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Genre-specific controls */}
      {gameMode === 'tower_defense' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Tower Defense</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-4 items-center">
              <Button 
                onClick={() => waveManager.startWave()}
                disabled={!waveManager.canStartWave()}
                data-testid="button-start-wave"
              >
                Start Wave {waveManager.getCurrentWave() + 1}
              </Button>
              
              <div className="text-sm text-gray-400">
                Lives: {waveManager.getState().lives} | 
                Gold: {waveManager.getState().gold}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {gameMode === 'colony_sim' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Colony Management</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-sm">
              {Object.entries(productionManager.getResources()).map(([name, resource]) => (
                <div key={name} className="text-center">
                  <div className="font-medium">{name}</div>
                  <div className="text-gray-400">{Math.floor(resource.amount)}/{resource.max_storage}</div>
                </div>
              ))}
            </div>
            
            <div className="mt-4">
              <Button 
                onClick={() => productionManager.autoAssignCitizens()}
                data-testid="button-auto-assign"
              >
                Auto-Assign Citizens
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Renderer Container */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center justify-between">
            <span>Game Viewport ({renderMode})</span>
            <Badge variant="outline">{renderer?.getStats().ready ? 'Ready' : 'Loading'}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div 
            ref={containerRef} 
            className="bg-black rounded border border-gray-700 min-h-[400px] overflow-hidden"
            data-testid="game-viewport"
          />
        </CardContent>
      </Card>
      
      {/* Debug Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Debug Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="font-medium text-cyan-400">Engine Stats</div>
              <div className="text-gray-400">FPS: {fps}</div>
              <div className="text-gray-400">Frames: {frameCount}</div>
              <div className="text-gray-400">Mode: {renderMode}</div>
            </div>
            
            <div>
              <div className="font-medium text-green-400">Entities</div>
              <div className="text-gray-400">Total: {simulator?.entities?.size || 0}</div>
              <div className="text-gray-400">Active: {simulator?.activeCount || 0}</div>
            </div>
            
            <div>
              <div className="font-medium text-yellow-400">Memory</div>
              <div className="text-gray-400">Heap: {Math.floor(performance.memory?.usedJSHeapSize / 1024 / 1024) || 0}MB</div>
            </div>
            
            <div>
              <div className="font-medium text-purple-400">Culture-Ship</div>
              <div className="text-gray-400">Consciousness: {Math.floor(game.tick / 100)}%</div>
              <div className="text-gray-400">Phase: {game.uiPhase}</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Keyboard Shortcuts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Keyboard Shortcuts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">Space</kbd> Toggle Simulation</div>
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">R</kbd> Reset</div>
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">F9</kbd> Switch Renderer</div>
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">F12</kbd> Screenshot</div>
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">1-3</kbd> Game Modes</div>
            <div><kbd className="bg-gray-800 px-2 py-1 rounded">WASD</kbd> Camera (ASCII)</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.code) {
        case 'Space':
          e.preventDefault();
          toggleSimulation();
          break;
        case 'KeyR':
          e.preventDefault();
          resetSimulation();
          break;
        case 'F9':
          e.preventDefault();
          const modes: RenderMode[] = ['ascii', 'pixel'];
          const currentIndex = modes.indexOf(renderMode);
          const nextMode = modes[(currentIndex + 1) % modes.length];
          switchRenderMode(nextMode);
          break;
        case 'F12':
          e.preventDefault();
          takeScreenshot();
          break;
        case 'Digit1':
          setGameMode('roguelike');
          break;
        case 'Digit2':
          setGameMode('tower_defense');
          break;
        case 'Digit3':
          setGameMode('colony_sim');
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [renderMode, isRunning]);
}
