// client/src/components/live/DashboardRealityLayer.tsx
// The Dashboard Reality Layer: Where The Game IS the System; The System IS the Game
// Every UI element is a live readout and control for the AI development ecosystem

import React, { useState } from 'react';
import PawnStatusBar from './PawnStatusBar';
import ColonyOverview from './ColonyOverview';
import LiveEventLog from './LiveEventLog';
import StorytellerControls from './StorytellerControls';
import { useGameState, isLiveStateStale } from '../../hooks/useLiveSystemState';

interface DashboardRealityLayerProps {
  className?: string;
}

export function DashboardRealityLayer({ className = '' }: DashboardRealityLayerProps) {
  const gameState = useGameState();
  const gameStale = isLiveStateStale('game.state_update');
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'events' | 'storyteller'>('overview');

  // Known AI agents (pawns) in the system
  const knownAgents = [
    'agent:chatdev',
    'agent:raven',
    'agent:zeta-driver',
    'agent:librarian',
    'agent:architect',
    'agent:artificer',
    'agent:alchemist',
    'agent:culture-ship'
  ];

  const tabStyle = (tabName: string) => ({
    padding: '12px 20px',
    background: activeTab === tabName ? 'linear-gradient(135deg, #00ff88, #00cc6a)' : 'rgba(255,255,255,0.1)',
    color: activeTab === tabName ? '#000' : '#fff',
    border: 'none',
    borderRadius: '8px 8px 0 0',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '14px',
    transition: 'all 0.3s ease'
  });

  return (
    <div className={`dashboard-reality-layer ${className}`} style={{
      background: 'linear-gradient(135deg, #1a1a2e, #16213e, #0f3460)',
      minHeight: '100vh',
      color: '#fff',
      fontFamily: 'monospace'
    }}>
      {/* Header */}
      <div className="header" style={{
        background: 'linear-gradient(135deg, rgba(0,0,0,0.5), rgba(255,255,255,0.05))',
        padding: '20px',
        borderBottom: '2px solid rgba(0, 255, 136, 0.3)',
        boxShadow: '0 2px 20px rgba(0, 255, 136, 0.2)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ 
              margin: '0 0 8px 0', 
              fontSize: '28px',
              background: 'linear-gradient(135deg, #00ff88, #45b7d1)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              🎮👥📖 Dashboard Reality Layer
            </h1>
            <p style={{ 
              margin: 0, 
              color: '#bbb', 
              fontSize: '16px',
              fontStyle: 'italic'
            }}>
              The Game IS the System • The System IS the Game • Live AI Colony Management
            </p>
          </div>
          
          {/* Real-time System Status */}
          <div className="system-status" style={{
            display: 'flex',
            gap: '20px',
            alignItems: 'center',
            fontSize: '14px'
          }}>
            <div className="status-item">
              <div style={{ color: '#feca57', fontWeight: 'bold' }}>⚡ Energy</div>
              <div style={{ color: gameStale ? '#666' : '#fff', fontSize: '18px' }}>
                {gameStale ? '—' : gameState.resources.energy}
              </div>
            </div>
            <div className="status-item">
              <div style={{ color: '#45b7d1', fontWeight: 'bold' }}>👥 Population</div>
              <div style={{ color: gameStale ? '#666' : '#fff', fontSize: '18px' }}>
                {gameStale ? '—' : gameState.resources.population}
              </div>
            </div>
            <div className="status-item">
              <div style={{ color: '#96ceb4', fontWeight: 'bold' }}>🎮 Tick</div>
              <div style={{ color: gameStale ? '#666' : '#fff', fontSize: '18px' }}>
                {gameStale ? '—' : gameState.tick}
              </div>
            </div>
            <div className="status-item">
              <div style={{ color: gameStale ? '#666' : gameState.unlocks.automation ? '#00ff88' : '#666', fontWeight: 'bold' }}>
                🤖 Auto
              </div>
              <div style={{ color: gameStale ? '#666' : gameState.unlocks.automation ? '#00ff88' : '#666', fontSize: '12px' }}>
                {gameStale ? 'UNKNOWN' : gameState.unlocks.automation ? 'ACTIVE' : 'LOCKED'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="navigation" style={{
        background: 'rgba(0,0,0,0.3)',
        padding: '0 20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button 
            style={tabStyle('overview')}
            onClick={() => setActiveTab('overview')}
          >
            🌟 Colony Overview
          </button>
          <button 
            style={tabStyle('agents')}
            onClick={() => setActiveTab('agents')}
          >
            👥 AI Agents (Pawns)
          </button>
          <button 
            style={tabStyle('events')}
            onClick={() => setActiveTab('events')}
          >
            📜 Live Events
          </button>
          <button 
            style={tabStyle('storyteller')}
            onClick={() => setActiveTab('storyteller')}
          >
            📖 Storyteller Console
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="content" style={{
        padding: '20px',
        minHeight: 'calc(100vh - 200px)'
      }}>
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <ColonyOverview />
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="agents-tab">
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ 
                color: '#00ff88', 
                fontSize: '24px',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                👥🧠 AI Agent Colony (RimWorld-Style Pawns)
              </h2>
              <p style={{ color: '#bbb', fontSize: '14px', margin: 0 }}>
                Live psychological vitals from the autonomous development ecosystem. 
                Each agent is a RimWorld-inspired pawn with skills, passions, and flow states.
              </p>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '16px'
            }}>
              {knownAgents.map(agentId => (
                <PawnStatusBar key={agentId} pawnId={agentId} />
              ))}
            </div>

            {/* Compact Agent Overview */}
            <div style={{ marginTop: '30px' }}>
              <h3 style={{ color: '#feca57', marginBottom: '16px' }}>Quick Agent Status</h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '8px'
              }}>
                {knownAgents.map(agentId => (
                  <PawnStatusBar key={`compact-${agentId}`} pawnId={agentId} compact={true} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'events' && (
          <div className="events-tab">
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ 
                color: '#ff6b6b', 
                fontSize: '24px',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                📜⚡ Live System Event Stream
              </h2>
              <p style={{ color: '#bbb', fontSize: '14px', margin: 0 }}>
                Real-time events from the psychological colony system, storyteller narratives, 
                and autonomous development activities. No mock data - everything is live!
              </p>
            </div>
            
            <LiveEventLog height="calc(100vh - 300px)" />
          </div>
        )}

        {activeTab === 'storyteller' && (
          <div className="storyteller-tab">
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ 
                color: '#f39c12', 
                fontSize: '24px',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                📖✨ Nurturing Storyteller Console
              </h2>
              <p style={{ color: '#bbb', fontSize: '14px', margin: 0 }}>
                Direct the narrative arc of your AI colony through positive interventions.
                Every button triggers real events in the Council Bus that affect agent psychology and system behavior.
              </p>
            </div>
            
            <StorytellerControls />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="footer" style={{
        background: 'rgba(0,0,0,0.5)',
        padding: '16px 20px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        textAlign: 'center',
        fontSize: '12px',
        color: '#666'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            🔴 Live Connection Active • No Mock Data • Real-Time AI Colony Management
          </span>
          <span>
            CognitoWeave Dashboard Reality Layer v1.0 • "The Game IS the System"
          </span>
        </div>
      </div>
    </div>
  );
}

export default DashboardRealityLayer;
