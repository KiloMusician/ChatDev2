/**
 * DevRoute - Dedicated System Interface Route
 * BOSS E: Clean separation between /dev (system) and / (game)
 */

import React from 'react';
import DevMenuExtended from '../../../client/src/components/DevMenuExtended';
import DevMenu from '../dev/DevMenu';

interface DevRouteProps {
  section?: string;
}

export function DevRoute({ section = 'main' }: DevRouteProps) {
  const switchToGame = () => {
    window.location.href = '/';
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#0a0a0a',
      color: '#fff',
      fontFamily: 'monospace'
    }}>
      {/* System Interface Header */}
      <div style={{ 
        borderBottom: '1px solid #333',
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ 
          margin: 0,
          color: '#00ff88',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          ΞNuSyQ System Interface - /dev
        </h1>
        
        <button
          onClick={switchToGame}
          style={{
            background: '#1a1a2e',
            border: '1px solid #0066cc',
            color: '#00aaff',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          → Game Interface
        </button>
      </div>

      {/* Route Section Content */}
      <div style={{ padding: '20px' }}>
        {section === 'main' && <DevMenuExtended />}
        {section === 'orchestration' && <DevMenu />}
        {section === 'receipts' && (
          <div>
            <h2>Development Receipts</h2>
            <p>Receipt monitoring interface would go here</p>
          </div>
        )}
      </div>
    </div>
  );
}