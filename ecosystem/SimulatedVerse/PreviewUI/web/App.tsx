/**
 * Dual-Rail Boot: DevMenu ↔ GameShell
 * UI↔Game Convergence with mode toggle and golden traces
 */

import React, { useState, useEffect } from 'react';
import { Bus, switchMode, emitGoldenTrace } from '../../SystemDev/scripts/breaths/event_bus';
import { OnboardingProvider } from './components/OnboardingProvider';

// Lazy load components to avoid circular dependencies
const DevMenu = React.lazy(() => import('./dev/DevMenu').catch(() => ({ default: () => <div>Dev Menu Loading...</div> })));
const GameShell = React.lazy(() => import('./adapters/GameShell').catch(() => ({ default: () => <div>Game Shell Loading...</div> })));

function readMode(): 'dev_menu' | 'game' {
  if (typeof window === 'undefined') return 'dev_menu';
  
  return (localStorage.getItem('PLAY_MODE') as 'dev_menu' | 'game') ?? 
         (process.env.PLAY_MODE as 'dev_menu' | 'game') ?? 
         'dev_menu';
}

export default function App() {
  const [mode, setMode] = useState<'dev_menu' | 'game'>(readMode());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Emit golden trace for UI mount
    emitGoldenTrace.uiRouteMount(mode === 'game' ? 'GameShell' : 'DevMenu');
    
    const onModeSwitch = (event: CustomEvent | Event) => {
      const newMode = readMode();
      setMode(newMode);
      emitGoldenTrace.uiRouteMount(newMode === 'game' ? 'GameShell' : 'DevMenu');
    };

    window.addEventListener('mode-switch', onModeSwitch);
    
    // Listen for storage changes (cross-tab sync)
    const onStorageChange = (e: StorageEvent) => {
      if (e.key === 'PLAY_MODE') {
        setMode(readMode());
      }
    };
    
    window.addEventListener('storage', onStorageChange);
    
    // Mark as loaded
    setIsLoading(false);
    
    return () => {
      window.removeEventListener('mode-switch', onModeSwitch);
      window.removeEventListener('storage', onStorageChange);
    };
  }, []);

  // Hotkey support (backtick to toggle)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '`' && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        const newMode = mode === 'dev_menu' ? 'game' : 'dev_menu';
        switchMode(newMode);
        emitGoldenTrace.uiRouteMount(newMode === 'game' ? 'GameShell' : 'DevMenu');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mode]);

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh', 
        background: '#0a0a0a', 
        color: '#fff',
        fontFamily: 'monospace' 
      }}>
        <div>
          <div>ΞNuSyQ Culture-Ship Initializing...</div>
          <div style={{ fontSize: '0.8em', opacity: 0.7, marginTop: '8px' }}>
            Mode: {mode} | Press ` to toggle
          </div>
        </div>
      </div>
    );
  }

  return (
    <OnboardingProvider>
      <div className="app-root" data-mode={mode}>
      {/* Mode Toggle - Always Visible */}
      <div style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        zIndex: 9999,
        display: 'flex',
        gap: '8px',
        background: 'rgba(0,0,0,0.8)',
        padding: '8px',
        borderRadius: '4px',
        fontFamily: 'monospace',
        fontSize: '12px',
      }}>
        <button
          onClick={() => switchMode('dev_menu')}
          style={{
            background: mode === 'dev_menu' ? '#0066cc' : '#333',
            color: '#fff',
            border: 'none',
            padding: '4px 8px',
            borderRadius: '2px',
            cursor: 'pointer',
          }}
        >
          Dev Menu
        </button>
        <button
          onClick={() => switchMode('game')}
          style={{
            background: mode === 'game' ? '#0066cc' : '#333',
            color: '#fff',
            border: 'none',
            padding: '4px 8px',
            borderRadius: '2px',
            cursor: 'pointer',
          }}
        >
          Play Game
        </button>
        <span style={{ color: '#888', fontSize: '10px', alignSelf: 'center' }}>
          (` to toggle)
        </span>
      </div>

      {/* Main Content */}
      <React.Suspense fallback={
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100vh',
          background: '#0a0a0a',
          color: '#fff',
          fontFamily: 'monospace'
        }}>
          Loading {mode === 'game' ? 'Game Shell' : 'Dev Menu'}...
        </div>
      }>
        {mode === 'game' ? <GameShell /> : <DevMenu />}
      </React.Suspense>
      </div>
    </OnboardingProvider>
  );
}