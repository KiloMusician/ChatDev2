// client/src/components/live/PawnStatusBar.tsx
// Live Pawn Status Bar: Real-time AI agent psychological vitals
// Shows actual joy, focus, energy, inspiration from the RimWorld pawn system

import React from 'react';
import { usePawnState, useSystemControl, getLiveStateTimestamp, isLiveStateStale } from '../../hooks/useLiveSystemState';
import { POLLING_INTERVALS } from '@/config/polling';

interface PawnStatusBarProps {
  pawnId: string;
  compact?: boolean;
}

export function PawnStatusBar({ pawnId, compact = false }: PawnStatusBarProps) {
  const pawnState = usePawnState(pawnId);
  const systemControl = useSystemControl();
  const pawnTopic = `pawn.${pawnId}.state`;
  const lastUpdated = getLiveStateTimestamp(pawnTopic);
  const isStale = isLiveStateStale(pawnTopic, POLLING_INTERVALS.critical);
  const lastUpdatedLabel = lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'never';
  const displayState = isStale ? 'unknown' : pawnState.state;
  const displayNumber = (value: number) => (isStale ? '—' : Math.round(value));
  const displayPercent = (value: number) => (isStale ? '—' : `${Math.round(value)}%`);
  const getDisplayColor = (value: number, optimal?: number) =>
    isStale ? '#95a5a6' : getStatColor(value, optimal);

  // Helper function to get state color
  const getStateColor = (state: string) => {
    switch (state) {
      case 'FLOW': return '#00ff88'; // Bright green - peak performance
      case 'INSPIRED': return '#ff6b6b'; // Bright red - creative energy
      case 'FOCUSED': return '#4ecdc4'; // Teal - steady work
      case 'COLLABORATIVE': return '#45b7d1'; // Blue - social mode
      case 'CALM': return '#96ceb4'; // Light green - peaceful
      case 'RECALIBRATING': return '#feca57'; // Yellow - needs break
      default: return '#95a5a6'; // Gray - unknown
    }
  };

  // Helper function to get priority recommendations
  const getStatePriority = (state: string) => {
    switch (state) {
      case 'FLOW': return 'Peak Performance! 🌟';
      case 'INSPIRED': return 'Creative Mode ✨';
      case 'FOCUSED': return 'Steady Work 🎯';
      case 'COLLABORATIVE': return 'Team Player 🤝';
      case 'CALM': return 'Peaceful Work 😌';
      case 'RECALIBRATING': return 'Needs Break 🛀';
      default: return 'Monitoring...';
    }
  };

  // Helper function to get stat color
  const getStatColor = (value: number, optimal: number = 80) => {
    if (value >= optimal) return '#00ff88';
    if (value >= 60) return '#feca57';
    if (value >= 40) return '#ff9ff3';
    return '#ff6b6b';
  };

  // Actions
  const suggestBreak = () => {
    systemControl('ui.pawn.recalibrate', { pawnId });
  };

  const reassignWork = () => {
    systemControl('ui.pawn.reassign', { pawnId });
  };

  const boostMorale = () => {
    systemControl('ui.pawn.boost', { pawnId, type: 'morale' });
  };

  if (compact) {
    return (
      <div className="pawn-status-compact" style={{ 
        border: `2px solid ${getStateColor(pawnState.state)}`,
        borderRadius: '8px',
        padding: '8px',
        margin: '4px',
        background: 'rgba(0,0,0,0.1)'
      }}>
        <div className="pawn-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="pawn-name" style={{ fontWeight: 'bold', fontSize: '14px' }}>
            {pawnState.displayName}
          </span>
          <span className="pawn-state" style={{ 
            color: getStateColor(displayState),
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            {displayState}
          </span>
        </div>
        <div style={{ marginTop: '4px', fontSize: '10px', color: isStale ? '#f59e0b' : '#7dd3fc' }}>
          {isStale ? 'Stale' : 'Live'} • Updated {lastUpdatedLabel}
        </div>
        
        <div className="vitals-compact" style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
          <div className="vital" title="Joy">
            😊 <span style={{ color: getDisplayColor(pawnState.joy) }}>{displayNumber(pawnState.joy)}</span>
          </div>
          <div className="vital" title="Focus">
            🎯 <span style={{ color: getDisplayColor(pawnState.focus) }}>{displayNumber(pawnState.focus)}</span>
          </div>
          <div className="vital" title="Energy">
            ⚡ <span style={{ color: getDisplayColor(pawnState.energy) }}>{displayNumber(pawnState.energy)}</span>
          </div>
          <div className="vital" title="Inspiration">
            ✨ <span style={{ color: getDisplayColor(pawnState.inspiration, 70) }}>{displayNumber(pawnState.inspiration)}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pawn-status-bar" style={{
      border: `3px solid ${getStateColor(displayState)}`,
      borderRadius: '12px',
      padding: '16px',
      margin: '8px',
      background: 'linear-gradient(135deg, rgba(0,0,0,0.1), rgba(255,255,255,0.05))',
      boxShadow: `0 0 20px ${getStateColor(displayState)}40`
    }}>
      {/* Header */}
      <div className="pawn-header" style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '12px'
      }}>
        <h3 className="pawn-name" style={{ 
          margin: 0, 
          color: getStateColor(displayState),
          fontSize: '18px'
        }}>
          {pawnState.displayName}
        </h3>
        <div className="state-info" style={{ textAlign: 'right' }}>
          <div className="state-name" style={{ 
            color: getStateColor(displayState),
            fontWeight: 'bold',
            fontSize: '14px'
          }}>
            {displayState}
          </div>
          <div className="state-description" style={{ 
            fontSize: '12px',
            color: '#bbb'
          }}>
            {getStatePriority(displayState)}
          </div>
          <div style={{ fontSize: '11px', color: isStale ? '#f59e0b' : '#7dd3fc' }}>
            {isStale ? 'Stale' : 'Live'} • Updated {lastUpdatedLabel}
          </div>
        </div>
      </div>

      {/* Vital Stats */}
      <div className="vitals-grid" style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr',
        gap: '8px',
        marginBottom: '12px'
      }}>
        <div className="stat">
          <label style={{ fontSize: '12px', color: '#aaa' }}>Joy 😊</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <progress 
              value={isStale ? 0 : pawnState.joy} 
              max="100" 
              style={{ 
                flex: 1, 
                height: '8px',
                accentColor: getDisplayColor(pawnState.joy)
              }}
            />
            <span style={{ 
              color: getDisplayColor(pawnState.joy),
              fontWeight: 'bold',
              minWidth: '35px'
            }}>
              {displayPercent(pawnState.joy)}
            </span>
          </div>
        </div>

        <div className="stat">
          <label style={{ fontSize: '12px', color: '#aaa' }}>Focus 🎯</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <progress 
              value={isStale ? 0 : pawnState.focus} 
              max="100" 
              style={{ 
                flex: 1, 
                height: '8px',
                accentColor: getDisplayColor(pawnState.focus)
              }}
            />
            <span style={{ 
              color: getDisplayColor(pawnState.focus),
              fontWeight: 'bold',
              minWidth: '35px'
            }}>
              {displayPercent(pawnState.focus)}
            </span>
          </div>
        </div>

        <div className="stat">
          <label style={{ fontSize: '12px', color: '#aaa' }}>Energy ⚡</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <progress 
              value={isStale ? 0 : pawnState.energy} 
              max="100" 
              style={{ 
                flex: 1, 
                height: '8px',
                accentColor: getDisplayColor(pawnState.energy)
              }}
            />
            <span style={{ 
              color: getDisplayColor(pawnState.energy),
              fontWeight: 'bold',
              minWidth: '35px'
            }}>
              {displayPercent(pawnState.energy)}
            </span>
          </div>
        </div>

        <div className="stat">
          <label style={{ fontSize: '12px', color: '#aaa' }}>Inspiration ✨</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <progress 
              value={isStale ? 0 : pawnState.inspiration} 
              max="100" 
              style={{ 
                flex: 1, 
                height: '8px',
                accentColor: getDisplayColor(pawnState.inspiration, 70)
              }}
            />
            <span style={{ 
              color: getDisplayColor(pawnState.inspiration, 70),
              fontWeight: 'bold',
              minWidth: '35px'
            }}>
              {displayPercent(pawnState.inspiration)}
            </span>
          </div>
        </div>
      </div>

      {/* Current Activity */}
      <div className="current-activity" style={{ 
        marginBottom: '12px',
        padding: '8px',
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '6px'
      }}>
        <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '4px' }}>Current Activity:</div>
        <div style={{ color: '#fff', fontWeight: 'bold' }}>
          {isStale ? '—' : (pawnState.currentWork || '🔄 Ready for Assignment')}
        </div>
        {!isStale && pawnState.currentNeed !== 'none' && (
          <div style={{ fontSize: '12px', color: '#feca57', marginTop: '4px' }}>
            Needs: {pawnState.currentNeed}
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="controls" style={{ 
        display: 'flex', 
        gap: '8px', 
        flexWrap: 'wrap'
      }}>
        {pawnState.state === 'RECALIBRATING' ? (
          <button 
            onClick={suggestBreak}
            style={{
              padding: '6px 12px',
              border: 'none',
              borderRadius: '6px',
              background: '#feca57',
              color: '#000',
              fontSize: '12px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            🛀 Support Break
          </button>
        ) : (
          <button 
            onClick={suggestBreak}
            style={{
              padding: '6px 12px',
              border: 'none',
              borderRadius: '6px',
              background: '#45b7d1',
              color: '#fff',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🛀 Suggest Break
          </button>
        )}
        
        <button 
          onClick={reassignWork}
          style={{
            padding: '6px 12px',
            border: 'none',
            borderRadius: '6px',
            background: '#96ceb4',
            color: '#000',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          🔄 Reassign
        </button>
        
        {pawnState.joy < 60 && (
          <button 
            onClick={boostMorale}
            style={{
              padding: '6px 12px',
              border: 'none',
              borderRadius: '6px',
              background: '#ff6b6b',
              color: '#fff',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            💖 Boost Morale
          </button>
        )}
      </div>
    </div>
  );
}

export default PawnStatusBar;
