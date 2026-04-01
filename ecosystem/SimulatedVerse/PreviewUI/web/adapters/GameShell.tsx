/**
 * GameShell Adapter - ASCII/Godot Game Runtime
 * Mounts actual game engine with fallback to ASCII
 */

import React, { useEffect, useRef, useState } from 'react';
import { Bus, emitGoldenTrace } from '../../../SystemDev/scripts/breaths/event_bus';

interface GameState {
  resources: {
    energy: number;
    materials: number;
    population: number;
    research: number;
  };
  tick: number;
  lastTick: number;
  autoTick: boolean;
}

interface ASCIIGameProps {
  onMount?: () => void;
}

function ASCIIGame({ onMount }: ASCIIGameProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const gameStateRef = useRef<GameState>({
    resources: { energy: 100, materials: 50, population: 1, research: 0 },
    tick: 0,
    lastTick: Date.now(),
    autoTick: true,
  });
  const [displayState, setDisplayState] = useState(gameStateRef.current);
  const animationRef = useRef<number>();

  useEffect(() => {
    // Emit golden trace for adapter binding
    emitGoldenTrace.uiAdapterBind('GameShell', 'ascii');
    
    // Signal mount complete
    onMount?.();
    
    // Start game loop
    startGameLoop();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const startGameLoop = () => {
    const gameLoop = () => {
      const now = Date.now();
      const dt = (now - gameStateRef.current.lastTick) / 1000;
      
      if (dt >= 1.0) { // Tick every second
        tick(dt);
        gameStateRef.current.lastTick = now;
        setDisplayState({ ...gameStateRef.current });
      }
      
      render();
      animationRef.current = requestAnimationFrame(gameLoop);
    };
    
    gameLoop();
  };

  const tick = (deltaTime: number) => {
    const state = gameStateRef.current;
    
    if (state.autoTick) {
      // Basic idle progression
      state.resources.energy += 1;
      state.resources.materials += state.resources.population * 0.5;
      
      // Cap resources
      state.resources.energy = Math.min(state.resources.energy, 1000);
      state.resources.materials = Math.min(state.resources.materials, 500);
    }
    
    state.tick++;
    
    // Emit golden trace for game tick
    emitGoldenTrace.gameTickPulse(deltaTime, state.resources);
    
    // Auto-save every 10 ticks
    if (state.tick % 10 === 0) {
      saveGame();
    }
  };

  const render = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // ASCII-style rendering
    ctx.fillStyle = '#00ff00';
    ctx.font = '16px monospace';
    
    const state = displayState;
    const lines = [
      '┌─────────────────────────────────────┐',
      '│ ΞNuSyQ Culture-Ship Colony Interface│',
      '├─────────────────────────────────────┤',
      `│ ⚡ Energy:     ${String(Math.floor(state.resources.energy)).padStart(4)} / 1000 │`,
      `│ 🔧 Materials:  ${String(Math.floor(state.resources.materials)).padStart(4)} / 500  │`,
      `│ 👥 Population: ${String(state.resources.population).padStart(4)}       │`,
      `│ 🧠 Research:   ${String(Math.floor(state.resources.research)).padStart(4)}       │`,
      '├─────────────────────────────────────┤',
      '│ [S] Scout   [B] Build   [R] Research│',
      '│ [A] Automate [P] Prestige [?] Help  │',
      '├─────────────────────────────────────┤',
      `│ Tick: ${String(state.tick).padStart(6)}  Auto: ${state.autoTick ? 'ON ' : 'OFF'}  │`,
      '└─────────────────────────────────────┘',
    ];
    
    lines.forEach((line, i) => {
      ctx.fillText(line, 10, 25 + i * 20);
    });
    
    // Add data-game-root marker for watchdog
    if (!canvas.dataset.gameRoot) {
      canvas.dataset.gameRoot = 'fallback-colony';
    }
  };

  const handleAction = (action: string) => {
    const state = gameStateRef.current;
    
    switch (action) {
      case 'scout':
        if (state.resources.energy >= 10) {
          state.resources.energy -= 10;
          state.resources.materials += 5;
        }
        break;
        
      case 'build':
        if (state.resources.materials >= 20) {
          state.resources.materials -= 20;
          state.resources.population += 1;
        }
        break;
        
      case 'research':
        if (state.resources.energy >= 15) {
          state.resources.energy -= 15;
          state.resources.research += 1;
        }
        break;
        
      case 'automate':
        state.autoTick = !state.autoTick;
        break;
        
      case 'prestige':
        if (state.resources.research >= 10) {
          performPrestige();
        }
        break;
    }
    
    setDisplayState({ ...state });
  };

  const performPrestige = () => {
    const state = gameStateRef.current;
    const oldResources = { ...state.resources };
    
    // Prestige logic: reset most resources, gain meta currency
    const metaCurrency = Math.floor(state.resources.research / 5);
    
    state.resources = {
      energy: 100 + metaCurrency * 10,
      materials: 50 + metaCurrency * 5,
      population: 1,
      research: 0,
    };
    
    // Emit golden trace for prestige
    emitGoldenTrace.gamePrestigeExec(oldResources, state.resources, metaCurrency);
    
    console.log(`[PRESTIGE] Gained ${metaCurrency} meta currency`);
  };

  const saveGame = () => {
    const saveData = {
      version: '1.0.0',
      timestamp: Date.now(),
      state: gameStateRef.current,
    };
    
    // Save to localStorage
    localStorage.setItem('game_save', JSON.stringify(saveData));
    
    // Emit golden trace for save
    emitGoldenTrace.gameSaveSnapshot(saveData, saveData.version);
  };

  const loadGame = () => {
    try {
      const saved = localStorage.getItem('game_save');
      if (saved) {
        const saveData = JSON.parse(saved);
        if (saveData.state) {
          gameStateRef.current = saveData.state;
          setDisplayState({ ...saveData.state });
          console.log('[LOAD] Game state restored');
        }
      }
    } catch (error) {
      console.error('[LOAD] Failed to load game:', error);
    }
  };

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return; // Don't interfere with form inputs
      
      switch (e.key.toLowerCase()) {
        case 's': handleAction('scout'); break;
        case 'b': handleAction('build'); break;
        case 'r': handleAction('research'); break;
        case 'a': handleAction('automate'); break;
        case 'p': handleAction('prestige'); break;
        case 'l': loadGame(); break;
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#0a0a0a',
      color: '#00ff00',
      fontFamily: 'monospace',
      padding: '20px',
    }}>
      <canvas
        ref={canvasRef}
        width={600}
        height={300}
        style={{
          border: '1px solid #333',
          background: '#000',
        }}
        data-game-root="fallback-colony"
      />
      
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button onClick={() => handleAction('scout')} style={buttonStyle}>Scout (S)</button>
        <button onClick={() => handleAction('build')} style={buttonStyle}>Build (B)</button>
        <button onClick={() => handleAction('research')} style={buttonStyle}>Research (R)</button>
        <button onClick={() => handleAction('automate')} style={buttonStyle}>
          Auto: {displayState.autoTick ? 'ON' : 'OFF'} (A)
        </button>
        <button onClick={() => handleAction('prestige')} style={buttonStyle}>Prestige (P)</button>
        <button onClick={loadGame} style={buttonStyle}>Load (L)</button>
        <button onClick={saveGame} style={buttonStyle}>Save</button>
      </div>
      
      <div style={{ marginTop: '10px', fontSize: '12px', opacity: 0.7 }}>
        Press keys S/B/R/A/P to play, or click buttons
      </div>
    </div>
  );
}

const buttonStyle = {
  background: '#333',
  color: '#00ff00',
  border: '1px solid #555',
  padding: '8px 12px',
  cursor: 'pointer',
  fontFamily: 'monospace',
  fontSize: '12px',
};

export default function GameShell() {
  const [mounted, setMounted] = useState(false);

  return (
    <div data-component="GameShell" data-game-root="shell">
      <ASCIIGame onMount={() => setMounted(true)} />
      {mounted && (
        <div style={{
          position: 'fixed',
          bottom: '10px',
          left: '10px',
          fontSize: '10px',
          color: '#666',
          fontFamily: 'monospace',
        }}>
          Engine: ASCII | Adapter: GameShell | Golden Traces: Active
        </div>
      )}
    </div>
  );
}