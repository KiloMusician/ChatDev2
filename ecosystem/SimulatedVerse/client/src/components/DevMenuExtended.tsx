/**
 * DevMenuExtended - Enhanced Development Interface
 * Provides convergence monitoring and golden trace status
 */

import React, { useState, useEffect } from 'react';
import NarrativeDisplay from './NarrativeDisplay';
import { LoreIntegration } from './LoreIntegration';
// BOSS E: Cross-contamination removed - dev and game components separated
// import { OnboardingTrigger, OnboardingStatus } from '../../../PreviewUI/web/components/OnboardingProvider';

interface DevMenuExtendedProps {}

export default function DevMenuExtended(props: DevMenuExtendedProps) {
  const [convergenceStatus, setConvergenceStatus] = useState<any>({
    golden_traces: [],
    convergence_complete: false,
  });

  const [systemHealth, setSystemHealth] = useState<any>({
    health: { overall_health: 0 }
  });

  useEffect(() => {
    // Load convergence status
    loadConvergenceStatus();
    
    // Load system health
    loadSystemHealth();
    
    // DISABLED: 5-second interval may be triggering fake agent theater
    // const interval = setInterval(() => {
    //   loadConvergenceStatus();
    //   loadSystemHealth();
    // }, 5000);

    // return () => clearInterval(interval);
  }, []);

  const loadConvergenceStatus = async () => {
    try {
      const response = await fetch('/SystemDev/reports/ui_game_convergence.json');
      if (response.ok) {
        const data = await response.json();
        setConvergenceStatus(data);
      }
    } catch (error) {
      console.warn('[DEV_MENU] Could not load convergence status');
    }
  };

  const loadSystemHealth = async () => {
    try {
      const response = await fetch('/api/organism/status');
      if (response.ok) {
        const data = await response.json();
        setSystemHealth(data);
      }
    } catch (error) {
      console.warn('[DEV_MENU] Could not load system health');
    }
  };

  const switchToGame = () => {
    // Set localStorage and navigate
    localStorage.setItem('PLAY_MODE', 'game');
    window.location.href = '/game';
  };

  const runConvergenceTest = async () => {
    try {
      console.log('[DEV_MENU] Running convergence test...');
      
      // Trigger game mode briefly to test traces
      const originalMode = localStorage.getItem('PLAY_MODE');
      localStorage.setItem('PLAY_MODE', 'game');
      
      // Wait a moment then restore
      setTimeout(() => {
        if (originalMode) {
          localStorage.setItem('PLAY_MODE', originalMode);
        } else {
          localStorage.removeItem('PLAY_MODE');
        }
        loadConvergenceStatus();
      }, 2000);
      
    } catch (error) {
      console.error('[DEV_MENU] Convergence test failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-mono p-5">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8 border-b border-gray-700 pb-5">
          <h1 className="text-green-400 text-2xl mb-2">
            🌌 ΞNuSyQ Culture-Ship DevMenu
          </h1>
          <div className="text-sm text-gray-400">
            Agent Orchestration | Breath Cycles | Golden Traces | System Status
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          
          {/* Golden Traces Status */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">🎯 Golden Traces Status</h3>
            <div className="mb-3">
              <div className={`p-2 border rounded ${
                convergenceStatus.world_online 
                  ? 'bg-green-900 border-green-400' 
                  : 'bg-red-900 border-red-400'
              }`}>
                Status: {convergenceStatus.world_online ? '✅ WORLD ONLINE' : '❌ CONVERGENCE INCOMPLETE'}
              </div>
            </div>

            <div className="text-xs">
              <div>Trace Count: {convergenceStatus.golden_trace_status?.present?.length || 0}/5</div>
              {convergenceStatus.golden_trace_status?.missing?.length > 0 && (
                <>
                  <div className="mt-2 text-red-400">Missing:</div>
                  <ul className="ml-4">
                    {convergenceStatus.golden_trace_status.missing.map((trace: string) => (
                      <li key={trace}>• {trace}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            <div className="mt-3 flex gap-2">
              <button 
                onClick={runConvergenceTest}
                className="bg-blue-600 text-white border-none px-3 py-1 cursor-pointer font-mono text-xs rounded"
              >
                Test Convergence
              </button>
            </div>
          </div>

          {/* Onboarding Controls */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">🎓 Interactive Guide</h3>
            
            {/* BOSS E: Game onboarding removed from dev interface */}
            
            <div className="mt-3 space-y-2">
              {/* BOSS E: Dev menu tour removed - system interface separation */}
              <div className="w-full bg-gray-600 px-3 py-1 rounded text-xs text-center opacity-50">
                🎯 Dev Menu Tour (Disabled)
              </div>
              
              {/* BOSS E: Game interface tour removed - kept for reference only */}
              <div className="w-full bg-gray-600 px-3 py-1 rounded text-xs text-center opacity-50">
                🎮 Game Interface Tour (Access via /game)
              </div>
            </div>
          </div>

          {/* BOSS J: Lore-Integrated Culture-Ship UI Switcher */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">⚡ Lore-Bridge Interface Control</h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">APP_MODE</label>
                <select 
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs"
                  defaultValue={localStorage.getItem('APP_MODE') || 'hybrid'}
                  onChange={(e) => {
                    localStorage.setItem('APP_MODE', e.target.value);
                    console.log(`[Culture-Ship] APP_MODE → ${e.target.value}`);
                  }}
                  data-testid="select-app-mode"
                >
                  <option value="dev_menu">System Interface (Dev)</option>
                  <option value="game">Player Experience (Game)</option>
                  <option value="hybrid">Dual-Mode (Hybrid)</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-gray-400 block mb-1">UI_VERSION</label>
                <select 
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs"
                  defaultValue={localStorage.getItem('UI_VERSION') || 'stable'}
                  onChange={(e) => {
                    localStorage.setItem('UI_VERSION', e.target.value);
                    console.log(`[Culture-Ship] UI_VERSION → ${e.target.value}`);
                  }}
                  data-testid="select-ui-version"
                >
                  <option value="stable">Stable</option>
                  <option value="next">Next</option>
                </select>
              </div>
              
              <button 
                onClick={() => window.location.reload()}
                className="w-full bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-xs transition-colors"
                data-testid="button-apply-ui-settings"
              >
⚡ Apply Lore Bridge & Reload
              </button>
            </div>
          </div>

          {/* UI Convergence Controls */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">🔄 UI Convergence</h3>
            
            <div className="mb-3">
              <button 
                onClick={switchToGame} 
                className="bg-blue-600 text-white border-none px-3 py-2 cursor-pointer font-mono text-xs rounded mr-2"
              >
                🎮 Launch Game Shell
              </button>
            </div>

            <div className="text-xs">
              <div>Quick Links:</div>
              <ul className="ml-4 mt-1">
                <li><a href="/api/organism/status" target="_blank" className="text-blue-400 hover:text-blue-300">Organism Status</a></li>
                <li><a href="/api/organism/watchdog" target="_blank" className="text-blue-400 hover:text-blue-300">Watchdog Report</a></li>
                <li><a href="/SystemDev/reports/" target="_blank" className="text-blue-400 hover:text-blue-300">System Reports</a></li>
              </ul>
            </div>
          </div>

          {/* System Health */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">💚 System Health</h3>
            <div className="text-xs">
              <div>Overall: {systemHealth.health?.overall_health || 0}%</div>
              <div>Nervous System: {systemHealth.health?.nervous_system || 'Unknown'}</div>
              <div>Immune System: {systemHealth.health?.immune_system || 'Unknown'}</div>
            </div>
          </div>

          {/* Legacy Lore Mine */}
          <LoreIntegration />

          {/* Narrative State */}
          <NarrativeDisplay />

          {/* Recent Activity */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">📡 Recent Activity</h3>
            <div className="text-xs text-gray-400">
              <div>Last Update: {new Date().toLocaleTimeString()}</div>
              <div>Mode: DevMenu</div>
              <div>Session: Active</div>
            </div>
          </div>

          {/* Agent Status */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">🤖 Agent Status</h3>
            <div className="text-xs">
              <div>Active Agents:</div>
              <ul className="ml-4 mt-1">
                <li className="text-green-400">✓ Raven (system health)</li>
                <li className="text-green-400">✓ Navigator (coordination)</li>
                <li className="text-green-400">✓ Janitor (cleanup)</li>
                <li className="text-gray-400">○ Artificer (standby)</li>
                <li className="text-gray-400">○ Librarian (standby)</li>
              </ul>
            </div>
          </div>

          {/* Breath Cycles */}
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <h3 className="text-green-400 text-sm mb-3">🌊 Breath Cycles</h3>
            <div className="text-xs">
              <div>Recent Breaths:</div>
              <ul className="ml-4 mt-1">
                <li className="text-green-400">✓ ΞΘΛΔ_ui_route</li>
                <li className="text-green-400">✓ ΞΘΛΔ_shadow_eject</li>
                <li className="text-green-400">✓ ΞΘΛΔ_telemetry</li>
                <li className="text-yellow-400">⚡ ΞΘΛΔ_convergence</li>
              </ul>
            </div>
          </div>

        </div>

        <footer className="mt-8 pt-5 border-t border-gray-700 text-xs text-gray-400">
          ΞNuSyQ Culture-Ship | Organism Health: {systemHealth.health?.overall_health || 0}% | 
          Mode: DevMenu | Golden Traces: {convergenceStatus.golden_trace_status?.present?.length || 0}/5
        </footer>
      </div>
    </div>
  );
}