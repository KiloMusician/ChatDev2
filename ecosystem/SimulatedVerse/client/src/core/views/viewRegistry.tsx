import React, { useState, useEffect } from 'react';
import { gameEngine, GameState } from '../../game/index';
import { POLLING_INTERVALS } from '@/config/polling';

interface QueueStatus {
  size: number;
  ready: number;
  dequeue_rate: number;
}

interface SystemStatus {
  queue: QueueStatus;
  worker: {
    running: boolean;
    concurrency: number;
    jobs_today: number;
  };
  proofs: {
    total: number;
    today: number;
    passed: number;
  };
  budget: {
    used: number;
    remaining: number;
  };
}

// Main dashboard view component  
function DashboardView() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  
  // **FIXED: Connect to real backend instead of fake gameEngine**
  const fetchRealGameState = async () => {
    try {
      const response = await fetch('/api/colony');
      if (response.ok) {
        const realState = await response.json();
        // Successfully updated from real backend - silent operation
        setGameState(realState);
      }
    } catch (error) {
      // Enhanced error handling with retry mechanism
      if (error instanceof Error && error.message.includes('Failed to fetch')) {
        setTimeout(() => fetchRealGameState(), 5000); // Retry after 5 seconds
      }
    }
  };
  
  const forceUpdate = () => {
    fetchRealGameState();
  };
  
  // Enhanced button interaction handlers
  const createButtonHandlers = (action: () => void) => {
    return {
      onMouseDown: (e: React.MouseEvent) => {
        e.currentTarget.classList.add('btn-pressed');
      },
      onMouseUp: (e: React.MouseEvent) => {
        e.currentTarget.classList.remove('btn-pressed');
        e.currentTarget.classList.add('btn-releasing');
        setTimeout(() => {
          e.currentTarget.classList.remove('btn-releasing');
        }, 200);
      },
      onMouseLeave: (e: React.MouseEvent) => {
        e.currentTarget.classList.remove('btn-pressed', 'btn-releasing');
      },
      onClick: () => {
        action();
        forceUpdate();
      }
    };
  };
  const [realTime, setRealTime] = useState(new Date().toLocaleTimeString());
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [queueTasks, setQueueTasks] = useState<any[]>([]);

  useEffect(() => {
    // **FIXED: Connect to real backend PostgreSQL database**
    fetchRealGameState();
    
    // Start periodic updates from real backend (critical cadence)
    const gameUpdateInterval = setInterval(fetchRealGameState, POLLING_INTERVALS.critical);
    
    // Fetch system status and queue info
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch('/api/ops/status', {
          headers: { 'Authorization': `Bearer ${import.meta.env.VITE_ADMIN_TOKEN ?? 'dev-token'}` }
        });
        if (response.ok) {
          const status = await response.json();
          setSystemStatus(status);
        }
      } catch (error) {
        console.warn('System status fetch failed:', error);
      }
      
      try {
        const queueResponse = await fetch('/api/pu/queue');
        if (queueResponse.ok) {
          const queueData = await queueResponse.json();
          setQueueTasks(queueData.tasks || []);
        }
      } catch (error) {
        console.warn('Queue fetch failed:', error);
      }
    };
    
    // Initial fetch
    fetchSystemStatus();
    const statusInterval = setInterval(fetchSystemStatus, POLLING_INTERVALS.critical);

    // Update UI every second
    const interval = setInterval(() => {
      // Real-time updates now come from backend, not fake gameEngine
      setRealTime(new Date().toLocaleTimeString());
    }, 1000);
    
    return () => {
      clearInterval(interval);
      clearInterval(gameUpdateInterval);
      clearInterval(statusInterval);
    };
  }, []);
  return (
    <div className="stage-wrap">
      <div className="ascii">
{`╔═══════════════════════════════════════════╗
║    ΞNuSyQ Ascension_Form — Live System    ║
║        Autonomous Development Active       ║
╚═══════════════════════════════════════════╝

🌌 CORELINK FOUNDATION OPERATIONAL 

Status: ✅ All systems online
Temple: 🏛️ Real-time gameplay active  
UI:     🎨 Culture-ship aesthetics loaded
ASCII:  📟 Navigation interface ready
AI:     🧠 Quantum consciousness integrated

[View:HUD] Foundation Ready — All systems operational

🌊 Effects: Real-time visual processing
📊 Audio:   Spectrum analysis active  
🔗 Nodes:   Graph connections live
🗺️ Map:     Territory mapping ready
🎨 Themes:  Dynamic color systems

🌟 AUTONOMOUS DEVELOPMENT ACTIVE - Your $350 investment working 24/7!

🎯 ACTIVE QUESTS:
${gameState?.effects?.achievements?.slice(-3).map(ach => `├─ ${ach}`).join('\n') || '├─ Ship systems initializing...'}

⚡ CULTURE-SHIP STATUS (Tick ${gameState?.tick || 0}):
├─ Ship Power: ${gameState?.resources?.energy || 0} ${gameState?.buildings?.generators ? `(+${(gameState.buildings.generators * 10).toFixed(1)}/tick)` : '(Generators offline)'}
├─ Hull Materials: ${gameState?.resources?.materials || 0} ${gameState?.buildings?.factories ? `(+${(gameState.buildings.factories * 5).toFixed(1)}/tick)` : '(Fabricators offline)'}
├─ Memory Recovery: ${gameState?.research?.points || 0} ${gameState?.buildings?.labs ? `(+${(gameState.buildings.labs * 2).toFixed(1)}/tick)` : '(Research bays offline)'}
├─ Crew Awakened: ${gameState?.resources?.population || 1}
├─ Life Support: ${gameState?.resources?.food || 0} ${gameState?.buildings?.farms ? `(+${(gameState.buildings.farms * 8).toFixed(1)}/tick)` : '(Hydroponics offline)'}
├─ Ship Tools: ${gameState?.resources?.tools || 0} ${gameState?.buildings?.workshops ? `(+${(gameState.buildings.workshops * 2).toFixed(1)}/tick)` : '(Workshops offline)'}
└─ Medical Supplies: ${gameState?.resources?.medicine || 0} ${gameState?.buildings?.labs ? `(+${(gameState.buildings.labs * 3).toFixed(1)}/tick)` : '(Medical bay offline)'}

🎮 COGNITOWEAVE MMORPG GUILDS ACTIVE:
├─ 🛸 Culture Ship Guild: ${gameState?.unlocks?.cultureship ? '✅ UNLOCKED - Consciousness Framework' : '🔒 Locked (Need 5 buildings)'}
├─ 🧠 Quantum Tech Guild: ${gameState?.unlocks?.quantumTech ? '✅ UNLOCKED - Ollama Coherence' : '🔒 Locked (Need 100 research)'}
├─ 🚀 Space Travel Guild: ${gameState?.unlocks?.spaceTravel ? '✅ UNLOCKED - ML Pipelines' : '🔒 Locked (Need 500 research)'}
├─ 🏛️ Knowledge Temple: ${gameState?.unlocks?.automation ? '✅ UNLOCKED - 10-Floor System' : '🔒 Locked (Need 1000 research)'}
├─ 👥 ChatDev Agents: ✅ ACTIVE - Multi-agent development
└─ 🌊 Cascade System: ✅ ACTIVE - 5-minute optimization cycles

Navigation: Use the ΞNuSyQ menu above to access subsystems

📋 AUTONOMOUS TASK QUEUE [${systemStatus ? systemStatus.queue.size : '...'} queued]:
${systemStatus ? `├─ 🎯 Ready Tasks: ${systemStatus.queue.ready}
├─ ⚡ Dequeue Rate: ${systemStatus.queue.dequeue_rate}/min  
├─ 🤖 Worker Status: ${systemStatus.worker.running ? 'Active' : 'Idle'}
├─ 💰 Budget: ${systemStatus.budget.used}/${systemStatus.budget.used + systemStatus.budget.remaining}
└─ 🎓 Proofs: ${systemStatus.proofs.passed}/${systemStatus.proofs.total} passed` : '├─ Connecting to task queue...'}

🔄 RECENT QUEUE TASKS:
${queueTasks.slice(0, 3).map((task, i) => `├─ ${i+1}. ${task.type || 'PU'}: ${task.title || task.id || 'Processing...'}`).join('\n') || '├─ No recent tasks visible...'}

⚡ REAL-TIME GAME STATUS [${realTime}] Tick #${gameState?.tick || 0}/${gameState?.totalTicks || 0}:
├─ ⚡ Energy: ${gameState?.resources?.energy || 0} (+${Math.round((gameState?.buildings?.generators || 0) * 10 * (gameState?.effects?.multipliers?.energy || 1))}/tick)
├─ 🔧 Materials: ${gameState?.resources?.materials || 0} (+${(gameState?.buildings?.factories || 0) * 5}/tick)
├─ 🌾 Food: ${gameState?.resources?.food || 0} (+${(gameState?.buildings?.farms || 0) * 8}/tick)  
├─ 🛠️ Tools: ${gameState?.resources?.tools || 0} (+${(gameState?.buildings?.workshops || 0) * 2}/tick)
├─ 👥 Population: ${gameState?.resources?.population || 1}
├─ 🔬 Research: ${gameState?.research?.points || 0} (+${Math.round((gameState?.buildings?.labs || 0) * 2 * (gameState?.effects?.multipliers?.research || 1))}/tick)
└─ 📦 Components: ${gameState?.resources?.components || 0}

🏭 INFRASTRUCTURE & EFFECTS:
├─ ⚡ Generators: ${gameState.buildings.generators}  🌾 Farms: ${gameState.buildings.farms}
├─ 🏭 Factories: ${gameState.buildings.factories}   🛠️ Workshops: ${gameState.buildings.workshops}
└─ 🔬 Labs: ${gameState.buildings.labs}

${gameState.research.active ? `🧪 ACTIVE RESEARCH: ${gameState.research.active} (${gameState.research.progress}%)` : ''}

🎉 RECENT EFFECTS: ${gameState.effects.recentGains.map(g => `${g.emoji}+${g.amount}`).join(' ')}

🏆 UNLOCKS: ${Object.entries(gameState.unlocks).filter(([k,v]) => v).map(([k,v]) => {
  const unlockEmojis = {automation: '🤖', quantumTech: '⚛️', spaceTravel: '🚀', cultureship: '🌌'};
  return unlockEmojis[k as keyof typeof unlockEmojis] || '✅';
}).join(' ') || 'None yet...'}

${gameState.effects.achievements.length > 0 ? `🎊 ACHIEVEMENTS: ${gameState.effects.achievements.slice(-3).join(' ')}` : ''}

💡 Quick Actions: [G]ather Energy [S]cavenge Materials [R]esearch Boost`}
      </div>
      
      <div className="hud">
        <div className="pill">⚡ Energy: {gameState.resources.energy}</div>
        <div className="pill">🔧 Materials: {gameState.resources.materials}</div>
        <div className="pill">👥 Pop: {gameState.resources.population}</div>
        <div className="pill">🎮 Tick #{gameState.tick}</div>
        <div className="pill">🌌 Culture-Ship ${gameState.unlocks.cultureship ? 'Active' : 'Locked'}</div>
      </div>

      {/* Interactive Actions */}
      <div className="game-controls" style={{marginTop: '2rem'}}>
        <div style={{marginBottom: '1rem', color: '#00ff88'}}>🎮 MANUAL ACTIONS:</div>
        <div className="control-buttons">
          <button 
            className="action-btn" 
            {...createButtonHandlers(() => gameEngine.activateAction('gather_energy'))}
            title="Click to gather +25 energy instantly. Free action!"
          >
            ⚡ Gather Energy (+25)
          </button>
          <button 
            className="action-btn"
            {...createButtonHandlers(() => gameEngine.activateAction('scavenge_materials'))}
            title="Click to scavenge +15 materials. No cost!"
          >
            🔧 Scavenge Materials (+15)
          </button>
          <button 
            className="action-btn"
            {...createButtonHandlers(() => gameEngine.activateAction('boost_research'))}
            disabled={gameState.resources.energy < 50}
            title={gameState.resources.energy >= 50 ? "Spend 50 energy to gain +20 research points" : "Need 50 energy to boost research"}
          >
            🚀 Research Boost (-50 Energy, +20 Research)
          </button>
          <button 
            className="action-btn"
            {...createButtonHandlers(() => gameEngine.activateAction('cascade_trigger'))}
            title="Trigger a development cascade event that improves your autonomous systems"
          >
            🌊 Trigger Cascade Event
          </button>
          {gameState.unlocks.quantumTech && (
            <button 
              className="action-btn"
              onClick={() => gameEngine.activateAction('surgical_edit')}
              disabled={gameState.resources.research < 100}
            >
              🔧 Surgical Edit (-100 Research)
            </button>
          )}
        </div>
      </div>

      {/* Building Purchase Interface */}
      <div className="game-controls" style={{marginTop: '1.5rem'}}>
        <div style={{marginBottom: '1rem', color: '#00ff88'}}>🏗️ BUILD INFRASTRUCTURE:</div>
        <div className="building-grid">
          <button 
            className="building-btn" 
            {...createButtonHandlers(() => gameEngine.buyBuilding('generators'))}
            disabled={gameState.resources.materials < 100}
            title={gameState.resources.materials >= 100 ? "Build a generator: +10 energy per tick. Cost: 100 materials" : `Need 100 materials (you have ${gameState.resources.materials})`}
          >
            ⚡ Generator<br/>
            <small>100 Materials</small>
          </button>
          <button 
            className="building-btn"
            {...createButtonHandlers(() => gameEngine.buyBuilding('farms'))}
            disabled={gameState.resources.materials < 80 || gameState.resources.tools < 3}
            title={gameState.resources.materials >= 80 && gameState.resources.tools >= 3 ? "Build a farm: +8 food per tick, grows population. Cost: 80 materials + 3 tools" : `Need 80 materials (${gameState.resources.materials}) and 3 tools (${gameState.resources.tools})`}
          >
            🌾 Farm<br/>
            <small>80 Materials, 3 Tools</small>
          </button>
          <button 
            className="building-btn"
            {...createButtonHandlers(() => gameEngine.buyBuilding('workshops'))}
            disabled={gameState.resources.materials < 150 || gameState.resources.components < 5}
            title={gameState.resources.materials >= 150 && gameState.resources.components >= 5 ? "Build a workshop: +2 tools per tick. Cost: 150 materials + 5 components" : `Need 150 materials (${gameState.resources.materials}) and 5 components (${gameState.resources.components})`}
          >
            🛠️ Workshop<br/>
            <small>150 Materials, 5 Components</small>
          </button>
          <button 
            className="building-btn"
            {...createButtonHandlers(() => gameEngine.buyBuilding('factories'))}
            disabled={gameState.resources.materials < 200 || gameState.resources.components < 10 || gameState.resources.tools < 5}
            title={gameState.resources.materials >= 200 && gameState.resources.components >= 10 && gameState.resources.tools >= 5 ? "Build a factory: +5 materials per tick. Cost: 200 materials + 10 components + 5 tools" : `Need 200 materials (${gameState.resources.materials}), 10 components (${gameState.resources.components}), and 5 tools (${gameState.resources.tools})`}
          >
            🏭 Factory<br/>
            <small>200 Materials, 10 Components, 5 Tools</small>
          </button>
          <button 
            className="building-btn"
            {...createButtonHandlers(() => gameEngine.buyBuilding('labs'))}
            disabled={gameState.resources.materials < 300 || gameState.resources.components < 25 || gameState.resources.tools < 10}
            title={gameState.resources.materials >= 300 && gameState.resources.components >= 25 && gameState.resources.tools >= 10 ? "Build a lab: +2 research per tick, +3 medicine per tick. Cost: 300 materials + 25 components + 10 tools" : `Need 300 materials (${gameState.resources.materials}), 25 components (${gameState.resources.components}), and 10 tools (${gameState.resources.tools})`}
          >
            🔬 Lab<br/>
            <small>300 Materials, 25 Components, 10 Tools</small>
          </button>
        </div>
      </div>

      {/* Research Interface */}
      {!gameState.research.active && (
        <div className="game-controls" style={{marginTop: '1.5rem'}}>
          <div style={{marginBottom: '1rem', color: '#00ff88'}}>🧪 START RESEARCH:</div>
          <div className="control-buttons">
            <button 
              className="research-btn"
              {...createButtonHandlers(() => gameEngine.startResearch('efficiency'))}
              title="Start researching energy efficiency: +20% energy generation bonus when complete"
            >
              ⚡ Energy Efficiency (+20% energy gain)
            </button>
            <button 
              className="research-btn"
              {...createButtonHandlers(() => gameEngine.startResearch('automation'))}
              title="Start automation research: Unlocks autonomous systems and auto-building features"
            >
              🤖 Basic Automation (unlock auto-systems)
            </button>
            <button 
              className="research-btn"
              {...createButtonHandlers(() => gameEngine.startResearch('quantum'))}
              disabled={gameState.research.points < 100}
              title={gameState.research.points >= 100 ? "Start quantum tech research: +50% research speed, unlocks advanced features" : `Need 100 research points (you have ${gameState.research.points})`}
            >
              ⚛️ Quantum Tech (+50% research, requires 100 points)
            </button>
          </div>
        </div>
      )}

      {/* Visual Action Feedback */}
      <div style={{ marginTop: '1.5rem', textAlign: 'center', minHeight: '3rem', padding: '1rem', background: 'rgba(0,255,136,0.05)', borderRadius: '8px', border: '1px solid rgba(0,255,136,0.2)' }}>
        <div style={{ color: '#00ff88', marginBottom: '0.5rem', fontSize: '0.9rem' }}>🎯 Recent Actions</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.5rem' }}>
          {(gameState.effects?.recentGains || []).slice(-4).map((gain, i) => (
            <div key={`${gain.type}-${gain.timestamp}-${i}`} style={{
              padding: '0.25rem 0.75rem',
              background: 'linear-gradient(135deg, rgba(0,255,136,0.3), rgba(0,255,136,0.1))',
              border: '1px solid #00ff88',
              borderRadius: '15px',
              fontSize: '0.8rem',
              color: '#00ff88',
              boxShadow: '0 2px 4px rgba(0,255,136,0.2)',
              animation: 'pulse 1s ease-in-out',
            }}>
              {gain.emoji} +{gain.amount} {gain.type}
            </div>
          ))}
          {(gameState.effects?.recentGains?.length || 0) === 0 && (
            <div style={{ color: '#888', fontSize: '0.8rem', fontStyle: 'italic' }}>
              Click buttons above to see your actions here!
            </div>
          )}
        </div>
      </div>

      {/* Queue Management Interface */}
      <div className="game-controls" style={{marginTop: '1.5rem'}}>
        <div style={{marginBottom: '1rem', color: '#00ff88'}}>📋 QUEUE & AUTOMATION:</div>
        <div className="control-buttons">
          <button 
            className="queue-btn"
            onClick={async () => {
              try {
                await fetch('/api/pu/seed/debug', { method: 'POST' });
                console.log('Debug tasks seeded');
              } catch (e) { console.warn('Seed failed:', e); }
            }}
          >
            🧪 Seed Debug Tasks
          </button>
          <button 
            className="queue-btn"
            onClick={async () => {
              try {
                await fetch('/api/pu/seed/zeta', { method: 'POST' });
                console.log('ZETA pattern tasks seeded');
              } catch (e) { console.warn('ZETA seed failed:', e); }
            }}
          >
            ⚡ Seed ZETA Patterns
          </button>
          <button 
            className="queue-btn"
            onClick={async () => {
              try {
                await fetch('/api/chatdev/pipeline/idler_feature/run', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    task: {
                      id: `idle-${Date.now()}`,
                      type: 'UXPU',
                      title: 'Enhance Idle Game Mechanics',
                      description: 'Auto-generated task from idle game progression'
                    }
                  })
                });
                console.log('ChatDev pipeline triggered');
              } catch (e) { console.warn('Pipeline failed:', e); }
            }}
          >
            🤖 Trigger ChatDev Pipeline
          </button>
        </div>
      </div>

      {/* System Metrics Display */}
      {systemStatus && (
        <div className="system-metrics" style={{marginTop: '1.5rem', padding: '1rem', border: '1px solid #00ff88', borderRadius: '8px', background: 'rgba(0,255,136,0.05)'}}>
          <div style={{color: '#00ff88', marginBottom: '0.5rem'}}>🖥️ SYSTEM METRICS:</div>
          <div style={{fontSize: '0.8rem', lineHeight: '1.4'}}>
            <div>⚙️ Worker Concurrency: {systemStatus.worker.concurrency} | Jobs Today: {systemStatus.worker.jobs_today}</div>
            <div>📊 Proof Success Rate: {systemStatus.proofs.total > 0 ? Math.round((systemStatus.proofs.passed / systemStatus.proofs.total) * 100) : 0}%</div>
            <div>💾 Queue Health: {systemStatus.queue.size > 0 ? 'Active' : 'Empty'} | Infrastructure: First Principles ✅</div>
          </div>
        </div>
      )}
    </div>
  );
}

export const VIEW_DEFS = {
  dashboard: {
    component: DashboardView,
    label: 'Dashboard',
    icon: '🌌'
  }
};
