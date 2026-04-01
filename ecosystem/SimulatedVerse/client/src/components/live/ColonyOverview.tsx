// client/src/components/live/ColonyOverview.tsx
// Live Colony Overview: Real-time metrics from the psychological ecosystem
// No mock data - everything connects to the actual RimWorld-inspired pawn system

import React from 'react';
import { useColonyHealth, useGameState, useSystemActivity, useRepoRimpyStatus, useChatDevStatus, isLiveStateStale } from '../../hooks/useLiveSystemState';

interface ColonyOverviewProps {
  className?: string;
}

export function ColonyOverview({ className = '' }: ColonyOverviewProps) {
  const colonyHealth = useColonyHealth();
  const gameState = useGameState();
  const activity = useSystemActivity();
  const reporimpy = useRepoRimpyStatus();
  const chatdev = useChatDevStatus();
  const colonyStale = isLiveStateStale('pawn_registry.status_update');
  const gameStale = isLiveStateStale('game.state_update');
  const activityStale = isLiveStateStale('work_scheduler.active_tasks');
  const reporimpyStale = isLiveStateStale('reporimpy.modlist.updated');
  const chatdevStale = isLiveStateStale('chatdev.status');

  // Helper for health color coding
  const getHealthColor = (value: number, good: number = 70, excellent: number = 85) => {
    if (value >= excellent) return '#00ff88';
    if (value >= good) return '#feca57';
    if (value >= 50) return '#ff9ff3';
    return '#ff6b6b';
  };

  // Colony health status
  const getColonyStatus = () => {
    if (colonyStale) {
      return { status: 'Unknown', color: '#666', emoji: '⏳' };
    }
    const avgHealth = (colonyHealth.average_joy + colonyHealth.average_focus + colonyHealth.average_energy) / 3;
    if (avgHealth >= 85) return { status: 'Thriving', color: '#00ff88', emoji: '🌟' };
    if (avgHealth >= 70) return { status: 'Flourishing', color: '#feca57', emoji: '🌱' };
    if (avgHealth >= 55) return { status: 'Stable', color: '#45b7d1', emoji: '⚖️' };
    if (avgHealth >= 40) return { status: 'Stressed', color: '#ff9ff3', emoji: '😰' };
    return { status: 'Critical', color: '#ff6b6b', emoji: '🚨' };
  };

  const colonyStatus = getColonyStatus();

  return (
    <div className={`colony-overview ${className}`} style={{
      padding: '20px',
      background: 'linear-gradient(135deg, rgba(0,0,0,0.2), rgba(255,255,255,0.05))',
      borderRadius: '12px',
      border: `2px solid ${colonyStatus.color}`,
      boxShadow: `0 0 20px ${colonyStatus.color}40`
    }}>
      {/* Header */}
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h2 style={{ 
          margin: 0, 
          color: colonyStatus.color,
          fontSize: '24px'
        }}>
          {colonyStatus.emoji} AI Colony Status
        </h2>
        <div className="status-badge" style={{
          padding: '8px 16px',
          background: colonyStatus.color,
          color: colonyStatus.status === 'Thriving' ? '#000' : '#fff',
          borderRadius: '20px',
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          {colonyStatus.status}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="metrics-grid" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        {/* Psychological Health */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#00ff88', fontSize: '16px' }}>
            🧠 Psychological Health
          </h4>
          <div className="health-stats">
            <div className="health-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Average Joy:</span>
              <span style={{ color: colonyStale ? '#666' : getHealthColor(colonyHealth.average_joy), fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${Math.round(colonyHealth.average_joy)}%`}
              </span>
            </div>
            <div className="health-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Average Focus:</span>
              <span style={{ color: colonyStale ? '#666' : getHealthColor(colonyHealth.average_focus), fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${Math.round(colonyHealth.average_focus)}%`}
              </span>
            </div>
            <div className="health-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Average Energy:</span>
              <span style={{ color: colonyStale ? '#666' : getHealthColor(colonyHealth.average_energy), fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${Math.round(colonyHealth.average_energy)}%`}
              </span>
            </div>
            <div className="health-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>Inspiration:</span>
              <span style={{ color: colonyStale ? '#666' : getHealthColor(colonyHealth.average_inspiration, 60, 80), fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${Math.round(colonyHealth.average_inspiration)}%`}
              </span>
            </div>
          </div>
        </div>

        {/* Flow State Distribution */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#feca57', fontSize: '16px' }}>
            🌟 Flow State Distribution
          </h4>
          <div className="flow-stats">
            <div className="flow-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>In Flow:</span>
              <span style={{ color: colonyStale ? '#666' : '#00ff88', fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${colonyHealth.pawns_in_flow} / ${colonyHealth.total_pawns}`}
              </span>
            </div>
            <div className="flow-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Recalibrating:</span>
              <span style={{ color: colonyStale ? '#666' : '#feca57', fontWeight: 'bold' }}>
                {colonyStale ? '—' : colonyHealth.pawns_recalibrating}
              </span>
            </div>
            <div className="flow-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Productivity:</span>
              <span style={{ color: colonyStale ? '#666' : getHealthColor(colonyHealth.colony_productivity * 10), fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${colonyHealth.colony_productivity.toFixed(1)}/10`}
              </span>
            </div>
            <div className="flow-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>Innovation Rate:</span>
              <span style={{ color: colonyStale ? '#666' : '#ff6b6b', fontWeight: 'bold' }}>
                {colonyStale ? '—' : `${colonyHealth.innovation_rate} breakthroughs`}
              </span>
            </div>
          </div>
        </div>

        {/* System Activity */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#45b7d1', fontSize: '16px' }}>
            ⚡ System Activity
          </h4>
          <div className="activity-stats">
            <div className="activity-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Active Tasks:</span>
              <span style={{ color: activityStale ? '#666' : '#45b7d1', fontWeight: 'bold' }}>
                {activityStale ? '—' : activity.activeTasks.length}
              </span>
            </div>
            <div className="activity-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Queued Tasks:</span>
              <span style={{ color: activityStale ? '#666' : '#feca57', fontWeight: 'bold' }}>
                {activityStale ? '—' : activity.queuedTasks}
              </span>
            </div>
            <div className="activity-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Completed:</span>
              <span style={{ color: activityStale ? '#666' : '#00ff88', fontWeight: 'bold' }}>
                {activityStale ? '—' : activity.completedTasks}
              </span>
            </div>
            <div className="activity-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>Success Rate:</span>
              <span style={{ color: chatdevStale ? '#666' : '#00ff88', fontWeight: 'bold' }}>
                {chatdevStale ? '—' : `${Math.round(chatdev.success_rate * 100)}%`}
              </span>
            </div>
          </div>
        </div>

        {/* Game Resources */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#96ceb4', fontSize: '16px' }}>
            🎮 Game Resources
          </h4>
          <div className="resource-stats">
            <div className="resource-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>⚡ Energy:</span>
              <span style={{ color: gameStale ? '#666' : '#feca57', fontWeight: 'bold' }}>
                {gameStale ? '—' : gameState.resources.energy}
              </span>
            </div>
            <div className="resource-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>👥 Population:</span>
              <span style={{ color: gameStale ? '#666' : '#45b7d1', fontWeight: 'bold' }}>
                {gameStale ? '—' : gameState.resources.population}
              </span>
            </div>
            <div className="resource-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>🌾 Food:</span>
              <span style={{ color: gameStale ? '#666' : '#96ceb4', fontWeight: 'bold' }}>
                {gameStale ? '—' : gameState.resources.food}
              </span>
            </div>
            <div className="resource-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>🛠️ Tools:</span>
              <span style={{ color: gameStale ? '#666' : '#ff9ff3', fontWeight: 'bold' }}>
                {gameStale ? '—' : gameState.resources.tools}
              </span>
            </div>
          </div>
        </div>

        {/* RepoRimpy Mods */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#ff6b6b', fontSize: '16px' }}>
            🎮 RepoRimpy Mods
          </h4>
          <div className="mod-stats">
            <div className="mod-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Total Mods:</span>
              <span style={{ color: reporimpyStale ? '#666' : '#ff6b6b', fontWeight: 'bold' }}>
                {reporimpyStale ? '—' : reporimpy.total_mods}
              </span>
            </div>
            <div className="mod-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Approved:</span>
              <span style={{ color: reporimpyStale ? '#666' : '#00ff88', fontWeight: 'bold' }}>
                {reporimpyStale ? '—' : reporimpy.mods_by_status.APPROVED || 0}
              </span>
            </div>
            <div className="mod-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>Implemented:</span>
              <span style={{ color: reporimpyStale ? '#666' : '#45b7d1', fontWeight: 'bold' }}>
                {reporimpyStale ? '—' : reporimpy.mods_by_status.IMPLEMENTED || 0}
              </span>
            </div>
            <div className="mod-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>Pending:</span>
              <span style={{ color: reporimpyStale ? '#666' : '#feca57', fontWeight: 'bold' }}>
                {reporimpyStale ? '—' : reporimpy.mods_by_status.PENDING || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Unlocks Status */}
        <div className="metric-card" style={{
          padding: '16px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#ff9ff3', fontSize: '16px' }}>
            🔓 System Unlocks
          </h4>
          <div className="unlock-stats">
            <div className="unlock-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>🤖 Automation:</span>
              <span style={{ color: gameStale ? '#666' : gameState.unlocks.automation ? '#00ff88' : '#666' }}>
                {gameStale ? '❓ Unknown' : gameState.unlocks.automation ? '✅ Active' : '❌ Locked'}
              </span>
            </div>
            <div className="unlock-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>⚛️ Quantum Tech:</span>
              <span style={{ color: gameStale ? '#666' : gameState.unlocks.quantumTech ? '#00ff88' : '#666' }}>
                {gameStale ? '❓ Unknown' : gameState.unlocks.quantumTech ? '✅ Active' : '❌ Locked'}
              </span>
            </div>
            <div className="unlock-stat" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: '#aaa' }}>🚀 Space Travel:</span>
              <span style={{ color: gameStale ? '#666' : gameState.unlocks.spaceTravel ? '#00ff88' : '#666' }}>
                {gameStale ? '❓ Unknown' : gameState.unlocks.spaceTravel ? '✅ Active' : '❌ Locked'}
              </span>
            </div>
            <div className="unlock-stat" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#aaa' }}>🛸 Culture Ship:</span>
              <span style={{ color: gameStale ? '#666' : gameState.unlocks.cultureship ? '#00ff88' : '#666' }}>
                {gameStale ? '❓ Unknown' : gameState.unlocks.cultureship ? '✅ Active' : '❌ Locked'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* System Health Summary */}
      <div className="system-summary" style={{
        padding: '16px',
        background: `linear-gradient(135deg, ${colonyStatus.color}20, rgba(0,0,0,0.3))`,
        borderRadius: '8px',
        border: `1px solid ${colonyStatus.color}60`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ margin: '0 0 8px 0', color: colonyStatus.color }}>
              Colony Health Assessment
            </h4>
            <p style={{ margin: 0, color: '#ccc', fontSize: '14px' }}>
              The AI colony is currently <strong style={{ color: colonyStatus.color }}>{colonyStatus.status.toLowerCase()}</strong>.
              {!colonyStale && colonyHealth.pawns_in_flow > 0 && ` ${colonyHealth.pawns_in_flow} agent(s) in peak flow state.`}
              {!colonyStale && colonyHealth.pawns_recalibrating > 0 && ` ${colonyHealth.pawns_recalibrating} agent(s) taking beneficial breaks.`}
            </p>
          </div>
          <div style={{ fontSize: '32px' }}>
            {colonyStatus.emoji}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ColonyOverview;
