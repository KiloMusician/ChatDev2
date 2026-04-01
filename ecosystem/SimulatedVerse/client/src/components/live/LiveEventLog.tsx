// client/src/components/live/LiveEventLog.tsx
// Live Event Log: Real-time stream of system events and storyteller narratives
// Shows the actual story unfolding as AI agents work and grow

import React, { useState, useEffect } from 'react';
import { useLiveEvents } from '../../hooks/useLiveSystemState';
import { POLLING_INTERVALS } from '@/config/polling';

interface LiveEventLogProps {
  maxEvents?: number;
  className?: string;
  height?: string;
}

export function LiveEventLog({ maxEvents = 50, className = '', height = '400px' }: LiveEventLogProps) {
  const events = useLiveEvents(maxEvents);
  const [filter, setFilter] = useState<string>('all');
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  useEffect(() => {
    if (events[0]) {
      setLastUpdated(Date.now());
    }
  }, [events[0]?.id]);

  const isStale = !lastUpdated || Date.now() - lastUpdated > POLLING_INTERVALS.critical;
  const lastUpdatedLabel = lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'never';

  // Event type styling
  const getEventStyle = (type: string) => {
    switch (type) {
      case 'discovery':
        return { color: '#00ff88', icon: '🌟', bg: 'rgba(0, 255, 136, 0.1)' };
      case 'gift':
        return { color: '#feca57', icon: '🎁', bg: 'rgba(254, 202, 87, 0.1)' };
      case 'diversion':
        return { color: '#ff6b6b', icon: '🎊', bg: 'rgba(255, 107, 107, 0.1)' };
      case 'celebration':
        return { color: '#ff9ff3', icon: '🎉', bg: 'rgba(255, 159, 243, 0.1)' };
      case 'support':
        return { color: '#45b7d1', icon: '🤝', bg: 'rgba(69, 183, 209, 0.1)' };
      case 'crisis':
        return { color: '#ff6b6b', icon: '🚨', bg: 'rgba(255, 107, 107, 0.1)' };
      case 'challenge':
        return { color: '#feca57', icon: '⚡', bg: 'rgba(254, 202, 87, 0.1)' };
      case 'pawn':
        return { color: '#96ceb4', icon: '👤', bg: 'rgba(150, 206, 180, 0.1)' };
      case 'work':
        return { color: '#4ecdc4', icon: '🔨', bg: 'rgba(78, 205, 196, 0.1)' };
      case 'reporimpy':
        return { color: '#9b59b6', icon: '🎮', bg: 'rgba(155, 89, 182, 0.1)' };
      case 'chatdev':
        return { color: '#e74c3c', icon: '🧠', bg: 'rgba(231, 76, 60, 0.1)' };
      case 'storyteller':
        return { color: '#f39c12', icon: '📖', bg: 'rgba(243, 156, 18, 0.1)' };
      default:
        return { color: '#95a5a6', icon: '📋', bg: 'rgba(149, 165, 166, 0.1)' };
    }
  };

  // Filter events (SAFE GUARD: Handle undefined/null events)
  const filteredEvents = (events || []).filter(event => {
    if (filter === 'all') return true;
    return event.type === filter;
  });

  // Get unique event types for filter (SAFE GUARD: Handle undefined/null events)
  const eventTypes = Array.from(new Set((events || []).map(e => e?.type).filter(Boolean)));

  // Format event message
  const formatMessage = (event: any) => {
    if (event.payload?.title) return event.payload.title;
    if (event.payload?.description) return event.payload.description;
    if (event.payload?.message) return event.payload.message;
    if (typeof event.payload === 'string') return event.payload;
    return `${event.type} event`;
  };

  // Get event details
  const getEventDetails = (event: any) => {
    const details = [];
    if (event.payload?.pawn_id) details.push(`Agent: ${event.payload.pawn_id}`);
    if (event.payload?.task_id) details.push(`Task: ${event.payload.task_id}`);
    if (event.payload?.mod_id) details.push(`Mod: ${event.payload.mod_id}`);
    if (event.payload?.session_id) details.push(`Session: ${event.payload.session_id}`);
    if (event.payload?.effect) details.push(`Effect: ${event.payload.effect}`);
    return details;
  };

  return (
    <div className={`live-event-log ${className}`} style={{
      background: 'linear-gradient(135deg, rgba(0,0,0,0.2), rgba(255,255,255,0.05))',
      borderRadius: '12px',
      border: '2px solid rgba(255,255,255,0.1)',
      padding: '16px',
      height
    }}>
      {/* Header */}
      <div className="header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: '18px' }}>
          📜 Live Event Stream
        </h3>
        <div className="controls" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{
            fontSize: '11px',
            padding: '2px 6px',
            borderRadius: '999px',
            color: isStale ? '#f59e0b' : '#22c55e',
            border: `1px solid ${isStale ? 'rgba(245, 158, 11, 0.5)' : 'rgba(34, 197, 94, 0.5)'}`,
            background: isStale ? 'rgba(245, 158, 11, 0.15)' : 'rgba(34, 197, 94, 0.12)'
          }}>
            {isStale ? 'Stale' : 'Live'} • Updated {lastUpdatedLabel}
          </span>
          <span style={{ color: '#aaa', fontSize: '12px' }}>Filter:</span>
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            style={{
              background: 'rgba(0,0,0,0.5)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '4px',
              color: '#fff',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            <option value="all">All Events ({(events || []).length})</option>
            {(eventTypes || []).map(type => (
              <option key={type} value={type}>
                {type} ({(events || []).filter(e => e.type === type).length})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Event Stream */}
      <div 
        className="event-stream" 
        style={{
          height: 'calc(100% - 60px)',
          overflowY: 'auto',
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255,255,255,0.3) transparent'
        }}
      >
        {filteredEvents.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#666',
            fontSize: '14px'
          }}>
            {filter === 'all' 
              ? (isStale ? 'No recent events (stale data).' : 'Waiting for system events...') 
              : `No ${filter} events yet...`}
          </div>
        ) : (
          (filteredEvents || []).map((event, i) => {
            const style = getEventStyle(event.type);
            const details = getEventDetails(event);
            
            return (
              <div 
                key={event.id} 
                className="event-item"
                style={{
                  background: style.bg,
                  border: `1px solid ${style.color}40`,
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '8px',
                  borderLeft: `4px solid ${style.color}`
                }}
              >
                <div className="event-header" style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: details.length > 0 ? '8px' : '4px'
                }}>
                  <div className="event-content" style={{ flex: 1 }}>
                    <div className="event-main" style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '4px'
                    }}>
                      <span style={{ fontSize: '16px' }}>{style.icon}</span>
                      <span style={{ 
                        color: style.color, 
                        fontWeight: 'bold',
                        fontSize: '12px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        {event.type}
                      </span>
                    </div>
                    <div className="event-message" style={{
                      color: '#fff',
                      fontSize: '14px',
                      lineHeight: '1.4'
                    }}>
                      {formatMessage(event)}
                    </div>
                  </div>
                  <div className="event-time" style={{
                    color: '#aaa',
                    fontSize: '11px',
                    textAlign: 'right',
                    marginLeft: '12px'
                  }}>
                    {event.timestamp}
                  </div>
                </div>

                {/* Event Details */}
                {details.length > 0 && (
                  <div className="event-details" style={{
                    fontSize: '11px',
                    color: '#bbb',
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    paddingTop: '8px',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '8px'
                  }}>
                    {details.map((detail, idx) => (
                      <span 
                        key={idx}
                        style={{
                          background: 'rgba(255,255,255,0.1)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '10px'
                        }}
                      >
                        {detail}
                      </span>
                    ))}
                  </div>
                )}

                {/* Special event content */}
                {event.payload?.benefits && (
                  <div className="event-benefits" style={{
                    marginTop: '8px',
                    fontSize: '12px',
                    color: '#00ff88'
                  }}>
                    Benefits: {event.payload.benefits.join(', ')}
                  </div>
                )}

                {event.payload?.narrative_impact && (
                  <div className="narrative-impact" style={{
                    marginTop: '4px',
                    fontSize: '11px',
                    color: style.color,
                    fontStyle: 'italic'
                  }}>
                    {event.payload.narrative_impact} impact
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer with stats */}
      <div className="footer" style={{
        marginTop: '12px',
        paddingTop: '8px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '11px',
        color: '#666'
      }}>
        <span>
          {filteredEvents.length} events shown
        </span>
        <span>
          {isStale ? '🟠 Stream stale' : '🟢 Live Stream Active'}
        </span>
      </div>
    </div>
  );
}

export default LiveEventLog;
