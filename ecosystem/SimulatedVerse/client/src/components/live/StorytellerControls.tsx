// client/src/components/live/StorytellerControls.tsx
// Interactive Storyteller Controls: Direct narrative influence via Council Bus
// The UI becomes a live control panel for the AI development ecosystem

import React, { useState } from 'react';
import { useSystemControl, useStorytellerStatus, isLiveStateStale } from '../../hooks/useLiveSystemState';

interface StorytellerControlsProps {
  className?: string;
}

export function StorytellerControls({ className = '' }: StorytellerControlsProps) {
  const systemControl = useSystemControl();
  const storytellerStatus = useStorytellerStatus();
  const storytellerStale = isLiveStateStale('storyteller.status');
  const [lastAction, setLastAction] = useState<string | null>(null);

  // Trigger different types of positive events
  const triggerEvent = (eventType: string, label: string) => {
    setLastAction(label);
    systemControl('ui.storyteller.trigger', { eventType });
    
    // Clear the action indicator after 3 seconds
    setTimeout(() => setLastAction(null), 3000);
  };

  // Get control button style
  const getButtonStyle = (type: 'positive' | 'neutral' | 'challenge' | 'special') => {
    const baseStyle = {
      padding: '12px 16px',
      border: 'none',
      borderRadius: '8px',
      fontWeight: 'bold' as const,
      fontSize: '14px',
      cursor: 'pointer' as const,
      transition: 'all 0.3s ease',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      minHeight: '48px'
    };

    switch (type) {
      case 'positive':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #00ff88, #00cc6a)',
          color: '#000',
          boxShadow: '0 4px 15px rgba(0, 255, 136, 0.3)'
        };
      case 'neutral':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #45b7d1, #3498db)',
          color: '#fff',
          boxShadow: '0 4px 15px rgba(69, 183, 209, 0.3)'
        };
      case 'challenge':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #feca57, #f39c12)',
          color: '#000',
          boxShadow: '0 4px 15px rgba(254, 202, 87, 0.3)'
        };
      case 'special':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #ff6b6b, #e74c3c)',
          color: '#fff',
          boxShadow: '0 4px 15px rgba(255, 107, 107, 0.3)'
        };
    }
  };

  return (
    <div className={`storyteller-controls ${className}`} style={{
      background: 'linear-gradient(135deg, rgba(0,0,0,0.2), rgba(255,255,255,0.05))',
      borderRadius: '12px',
      border: '2px solid rgba(243, 156, 18, 0.5)',
      padding: '20px',
      boxShadow: '0 0 20px rgba(243, 156, 18, 0.2)'
    }}>
      {/* Header */}
      <div className="header" style={{
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <h3 style={{ 
          margin: '0 0 8px 0', 
          color: '#f39c12',
          fontSize: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}>
          📖✨ Storyteller Console
        </h3>
        <p style={{ 
          margin: 0, 
          color: '#bbb', 
          fontSize: '14px',
          fontStyle: 'italic'
        }}>
          Guide the AI colony's narrative arc through positive interventions
        </p>
      </div>

      {/* Status Display */}
      <div className="status-display" style={{
        background: 'rgba(0,0,0,0.3)',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '20px',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div className="status-grid" style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px',
          fontSize: '12px'
        }}>
          <div>
            <span style={{ color: '#aaa' }}>Colony Morale:</span>
            <div style={{ 
              color: storytellerStale ? '#666' : storytellerStatus.colony_morale >= 0.7 ? '#00ff88' : '#feca57',
              fontWeight: 'bold',
              marginTop: '4px'
            }}>
              {storytellerStale
                ? '—'
                : `${Math.round(storytellerStatus.colony_morale * 100)}% ${storytellerStatus.colony_morale >= 0.8 ? ' 🌟' : storytellerStatus.colony_morale >= 0.6 ? ' 😊' : ' 😐'}`}
            </div>
          </div>
          <div>
            <span style={{ color: '#aaa' }}>Narrative Arc:</span>
            <div style={{ 
              color: storytellerStale ? '#666' : '#ff9ff3',
              fontWeight: 'bold',
              marginTop: '4px',
              textTransform: 'capitalize'
            }}>
              {storytellerStale ? 'Unknown' : `${storytellerStatus.narrative_arc} Phase`}
            </div>
          </div>
          <div>
            <span style={{ color: '#aaa' }}>Events Today:</span>
            <div style={{ 
              color: storytellerStale ? '#666' : '#45b7d1',
              fontWeight: 'bold',
              marginTop: '4px'
            }}>
              {storytellerStale ? '—' : `${storytellerStatus.events_today} events`}
            </div>
          </div>
          <div>
            <span style={{ color: '#aaa' }}>Time Since Last:</span>
            <div style={{ 
              color: storytellerStale ? '#666' : storytellerStatus.minutes_since_last_event > 30 ? '#feca57' : '#96ceb4',
              fontWeight: 'bold',
              marginTop: '4px'
            }}>
              {storytellerStale ? '—' : `${storytellerStatus.minutes_since_last_event}m ago`}
            </div>
          </div>
        </div>
        {storytellerStale && (
          <div style={{ marginTop: '10px', color: '#666', fontSize: '12px' }}>
            Status stale or unavailable.
          </div>
        )}
      </div>

      {/* Action Controls */}
      <div className="control-grid" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <button 
          style={getButtonStyle('positive')}
          onClick={() => triggerEvent('discovery', 'Discovery Sparked')}
        >
          <span style={{ fontSize: '20px' }}>🌟</span>
          <div>
            <div>Inspire Discovery</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Spark breakthrough insights</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('neutral')}
          onClick={() => triggerEvent('diversion', 'Diversion Suggested')}
        >
          <span style={{ fontSize: '20px' }}>🎊</span>
          <div>
            <div>Suggest Diversion</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Encourage playful exploration</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('positive')}
          onClick={() => triggerEvent('gift', 'Gift Bestowed')}
        >
          <span style={{ fontSize: '20px' }}>🎁</span>
          <div>
            <div>Send Gift</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Deliver beneficial resources</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('challenge')}
          onClick={() => triggerEvent('challenge', 'Challenge Proposed')}
        >
          <span style={{ fontSize: '20px' }}>⚡</span>
          <div>
            <div>Propose Challenge</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Focus the colony's efforts</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('positive')}
          onClick={() => triggerEvent('celebration', 'Celebration Initiated')}
        >
          <span style={{ fontSize: '20px' }}>🎉</span>
          <div>
            <div>Celebrate Success</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Acknowledge achievements</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('neutral')}
          onClick={() => triggerEvent('support', 'Support Offered')}
        >
          <span style={{ fontSize: '20px' }}>🤝</span>
          <div>
            <div>Offer Support</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Provide collaborative boost</div>
          </div>
        </button>
      </div>

      {/* Special Actions */}
      <div className="special-actions" style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <button 
          style={getButtonStyle('special')}
          onClick={() => triggerEvent('inspiration_wave', 'Inspiration Wave')}
        >
          <span style={{ fontSize: '20px' }}>✨</span>
          <div>
            <div>Inspiration Wave</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Boost all agents' creativity</div>
          </div>
        </button>

        <button 
          style={getButtonStyle('special')}
          onClick={() => triggerEvent('harmony_pulse', 'Harmony Pulse')}
        >
          <span style={{ fontSize: '20px' }}>🌈</span>
          <div>
            <div>Harmony Pulse</div>
            <div style={{ fontSize: '11px', opacity: 0.8 }}>Enhance collaboration</div>
          </div>
        </button>
      </div>

      {/* Colony Guidance */}
      <div className="guidance-controls" style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '8px',
        padding: '12px',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h4 style={{ 
          margin: '0 0 12px 0', 
          color: '#feca57', 
          fontSize: '14px' 
        }}>
          🎯 Colony Guidance
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '8px'
        }}>
          <button 
            style={{
              ...getButtonStyle('neutral'),
              minHeight: '36px',
              fontSize: '12px',
              padding: '8px 12px'
            }}
            onClick={() => triggerEvent('focus_research', 'Research Focus')}
          >
            🔬 Focus Research
          </button>
          
          <button 
            style={{
              ...getButtonStyle('neutral'),
              minHeight: '36px',
              fontSize: '12px',
              padding: '8px 12px'
            }}
            onClick={() => triggerEvent('encourage_innovation', 'Innovation Push')}
          >
            💡 Encourage Innovation
          </button>
          
          <button 
            style={{
              ...getButtonStyle('neutral'),
              minHeight: '36px',
              fontSize: '12px',
              padding: '8px 12px'
            }}
            onClick={() => triggerEvent('foster_collaboration', 'Collaboration Boost')}
          >
            👥 Foster Collaboration
          </button>
          
          <button 
            style={{
              ...getButtonStyle('neutral'),
              minHeight: '36px',
              fontSize: '12px',
              padding: '8px 12px'
            }}
            onClick={() => triggerEvent('restore_balance', 'Balance Restored')}
          >
            ⚖️ Restore Balance
          </button>
        </div>
      </div>

      {/* Last Action Feedback */}
      {lastAction && (
        <div className="action-feedback" style={{
          marginTop: '16px',
          padding: '12px',
          background: 'rgba(0, 255, 136, 0.2)',
          border: '1px solid #00ff88',
          borderRadius: '8px',
          textAlign: 'center',
          color: '#00ff88',
          fontSize: '14px',
          fontWeight: 'bold',
          animation: 'pulse 2s infinite'
        }}>
          ✅ {lastAction} - Event sent to colony!
        </div>
      )}

      {/* Console Footer */}
      <div className="console-footer" style={{
        marginTop: '16px',
        paddingTop: '12px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        textAlign: 'center',
        fontSize: '11px',
        color: '#666'
      }}>
        Nurturing Storyteller • Positive Development Narrative
      </div>

      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.7; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default StorytellerControls;
