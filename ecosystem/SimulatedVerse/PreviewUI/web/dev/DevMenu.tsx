/**
 * DevMenu - Agent Orchestration Interface
 * Development environment with Culture-Ship integration
 */

import React, { useState, useEffect } from 'react';
import { Bus, switchMode } from '../../../SystemDev/scripts/breaths/event_bus';

interface DevMenuProps {}

export default function DevMenu(props: DevMenuProps) {
  const [goldenTraces, setGoldenTraces] = useState<any[]>([]);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [traceStatus, setTraceStatus] = useState<any>({ complete: false, missing: [], present: [] });

  useEffect(() => {
    // Subscribe to golden trace updates
    const unsubscribeTrace = Bus.on('ui.route.mount', () => updateTraceStatus());
    const unsubscribeGame = Bus.on('game.tick.pulse', () => updateTraceStatus());
    const unsubscribeSave = Bus.on('game.save.snapshot', () => updateTraceStatus());
    const unsubscribePrestige = Bus.on('game.prestige.exec', () => updateTraceStatus());
    const unsubscribeAdapter = Bus.on('ui.adapter.bind', () => updateTraceStatus());

    // Initial load
    updateTraceStatus();

    // Periodic refresh
    const interval = setInterval(updateTraceStatus, 2000);

    return () => {
      unsubscribeTrace();
      unsubscribeGame();
      unsubscribeSave();
      unsubscribePrestige();
      unsubscribeAdapter();
      clearInterval(interval);
    };
  }, []);

  const updateTraceStatus = () => {
    const traces = Bus.getGoldenTraces();
    const status = Bus.checkGoldenTraceCompleteness();
    const recent = Bus.getRecentEvents(10);
    
    setGoldenTraces(traces);
    setTraceStatus(status);
    setRecentEvents(recent);
  };

  const handleTestGameFlow = async () => {
    console.log('[DEV_MENU] Testing game flow...');
    
    // Switch to game mode temporarily to trigger traces
    switchMode('game');
    
    setTimeout(() => {
      console.log('[DEV_MENU] Game flow test complete');
      updateTraceStatus();
    }, 2000);
  };

  const clearTraces = () => {
    Bus.clearOldTraces(0); // Clear all
    updateTraceStatus();
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0a0a',
      color: '#fff',
      fontFamily: 'monospace',
      padding: '20px',
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <header style={{ marginBottom: '30px', borderBottom: '1px solid #333', paddingBottom: '20px' }}>
          <h1 style={{ color: '#00ff00', margin: '0 0 10px 0' }}>
            🌌 ΞNuSyQ Culture-Ship DevMenu
          </h1>
          <div style={{ fontSize: '14px', color: '#888' }}>
            Agent Orchestration | Breath Cycles | Golden Traces | System Status
          </div>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
          
          {/* Golden Traces Status */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>🎯 Golden Traces Status</h3>
            <div style={{ marginBottom: '15px' }}>
              <div style={{
                padding: '8px',
                background: traceStatus.complete ? '#001a00' : '#1a0000',
                border: `1px solid ${traceStatus.complete ? '#00ff00' : '#ff0000'}`,
                borderRadius: '4px',
              }}>
                Status: {traceStatus.complete ? '✅ COMPLETE' : '❌ INCOMPLETE'}
              </div>
            </div>

            <div style={{ fontSize: '12px' }}>
              <div>Present ({traceStatus.present.length}):</div>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                {traceStatus.present.map((trace: string) => (
                  <li key={trace} style={{ color: '#00ff00' }}>{trace}</li>
                ))}
              </ul>

              {traceStatus.missing.length > 0 && (
                <>
                  <div>Missing ({traceStatus.missing.length}):</div>
                  <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                    {traceStatus.missing.map((trace: string) => (
                      <li key={trace} style={{ color: '#ff0000' }}>{trace}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
              <button onClick={handleTestGameFlow} style={buttonStyle}>
                Test Game Flow
              </button>
              <button onClick={clearTraces} style={buttonStyle}>
                Clear Traces
              </button>
            </div>
          </div>

          {/* UI Convergence Controls */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>🔄 UI Convergence</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <button 
                onClick={() => switchMode('game')} 
                style={{ ...buttonStyle, background: '#0066cc', marginRight: '10px' }}
              >
                🎮 Launch Game Shell
              </button>
              <button 
                onClick={() => window.open('/api/organism/status', '_blank')} 
                style={buttonStyle}
              >
                🔍 Organism Status
              </button>
            </div>

            <div style={{ fontSize: '12px' }}>
              <div>Quick Links:</div>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                <li><a href="/api/organism/watchdog" target="_blank" style={{ color: '#0099ff' }}>Watchdog Report</a></li>
                <li><a href="/api/organism/receipts" target="_blank" style={{ color: '#0099ff' }}>Recent Receipts</a></li>
                <li><a href="/api/organism/metabolism" target="_blank" style={{ color: '#0099ff' }}>Agent Cycles</a></li>
              </ul>
            </div>
          </div>

          {/* Recent Events */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>📡 Recent Events</h3>
            <div style={{ 
              maxHeight: '200px', 
              overflowY: 'auto', 
              fontSize: '11px',
              background: '#111',
              padding: '10px',
              borderRadius: '4px',
            }}>
              {recentEvents.length === 0 ? (
                <div style={{ color: '#888' }}>No events yet...</div>
              ) : (
                recentEvents.map((event, i) => (
                  <div key={i} style={{ 
                    marginBottom: '5px', 
                    color: event.golden_trace ? '#00ff00' : '#ccc',
                    borderLeft: event.golden_trace ? '2px solid #00ff00' : 'none',
                    paddingLeft: event.golden_trace ? '5px' : '0',
                  }}>
                    [{new Date(event.timestamp).toLocaleTimeString()}] 
                    {event.golden_trace && ' ⭐'} {event.source}: {JSON.stringify(event.data).slice(0, 50)}...
                  </div>
                ))
              )}
            </div>
            <button 
              onClick={updateTraceStatus} 
              style={{ ...buttonStyle, marginTop: '10px', fontSize: '10px' }}
            >
              Refresh
            </button>
          </div>

          {/* System Reports */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>📊 System Reports</h3>
            <div style={{ fontSize: '12px' }}>
              <div style={{ marginBottom: '10px' }}>
                Available Reports:
              </div>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                <li><a href="/SystemDev/reports/ui_entanglement.json" target="_blank" style={{ color: '#0099ff' }}>UI Entanglement</a></li>
                <li><a href="/SystemDev/reports/build_shadow_map.json" target="_blank" style={{ color: '#0099ff' }}>Build Shadows</a></li>
                <li><a href="/SystemDev/receipts/" target="_blank" style={{ color: '#0099ff' }}>Receipts Directory</a></li>
              </ul>
            </div>
          </div>

          {/* Agent Status */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>🤖 Agent Status</h3>
            <div style={{ fontSize: '12px' }}>
              <div>Active Agents:</div>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                <li style={{ color: '#00ff00' }}>✓ Raven (system health)</li>
                <li style={{ color: '#00ff00' }}>✓ Navigator (coordination)</li>
                <li style={{ color: '#00ff00' }}>✓ Janitor (cleanup)</li>
                <li style={{ color: '#888' }}>○ Artificer (standby)</li>
                <li style={{ color: '#888' }}>○ Librarian (standby)</li>
                <li style={{ color: '#888' }}>○ Alchemist (standby)</li>
              </ul>
            </div>
          </div>

          {/* Breath Cycles */}
          <div style={panelStyle}>
            <h3 style={headerStyle}>🌊 Breath Cycles</h3>
            <div style={{ fontSize: '12px' }}>
              <div>Recent Breaths:</div>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                <li style={{ color: '#00ff00' }}>✓ ΞΘΛΔ_ui_route</li>
                <li style={{ color: '#00ff00' }}>✓ ΞΘΛΔ_shadow_eject</li>
                <li style={{ color: '#ffaa00' }}>⚡ ΞΘΛΔ_event_bus</li>
                <li style={{ color: '#888' }}>○ ΞΘΛΔ_telemetry</li>
              </ul>
              
              <button 
                style={{ ...buttonStyle, marginTop: '10px', fontSize: '10px' }}
                onClick={() => console.log('[DEV_MENU] Breath cycle initiated')}
              >
                Trigger Cascade
              </button>
            </div>
          </div>

        </div>

        <footer style={{ 
          marginTop: '40px', 
          paddingTop: '20px', 
          borderTop: '1px solid #333', 
          fontSize: '10px', 
          color: '#666' 
        }}>
          ΞNuSyQ Culture-Ship | Organism Health: 100% | Mode: DevMenu | 
          Golden Traces: {traceStatus.present.length}/5 | 
          Events: {recentEvents.length}
        </footer>
      </div>
    </div>
  );
}

const panelStyle = {
  background: '#111',
  border: '1px solid #333',
  borderRadius: '8px',
  padding: '15px',
};

const headerStyle = {
  color: '#00ff00',
  margin: '0 0 15px 0',
  fontSize: '14px',
};

const buttonStyle = {
  background: '#333',
  color: '#fff',
  border: '1px solid #555',
  padding: '6px 12px',
  cursor: 'pointer',
  fontFamily: 'monospace',
  fontSize: '11px',
  borderRadius: '3px',
};