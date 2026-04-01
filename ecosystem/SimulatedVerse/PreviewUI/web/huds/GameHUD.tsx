import React, { useState, useEffect } from 'react';
import { gameBindings, type ResourceSnapshot, type WaveInfo, type ResearchInfo, type TooltipData } from './Bindings';

export function GameHUD() {
  const [resources, setResources] = useState<ResourceSnapshot[]>([]);
  const [waveInfo, setWaveInfo] = useState<WaveInfo | null>(null);
  const [researchInfo, setResearchInfo] = useState<ResearchInfo | null>(null);
  const [hoveredElement, setHoveredElement] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  useEffect(() => {
    const updateGameState = () => {
      setResources(gameBindings.getResources());
      setWaveInfo(gameBindings.getWaveInfo());
      setResearchInfo(gameBindings.getResearchInfo());
    };

    // Initial load
    updateGameState();

    // Update every second
    const interval = setInterval(updateGameState, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleMouseEnter = (elementType: string, elementId: string) => {
    setHoveredElement(`${elementType}_${elementId}`);
    setTooltip(gameBindings.getTooltip(elementType, elementId));
  };

  const handleMouseLeave = () => {
    setHoveredElement(null);
    setTooltip(null);
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  return (
    <div className="game-hud">
      {/* Resource Panel */}
      <div className="resource-panel">
        <h3>Resources</h3>
        <div className="resource-grid">
          {resources.map((resource) => (
            <div
              key={resource.id}
              className="resource-item"
              onMouseEnter={() => handleMouseEnter('resource', resource.id)}
              onMouseLeave={handleMouseLeave}
            >
              <div className="resource-name">{resource.id}</div>
              <div className="resource-amount">{resource.amount.toFixed(1)}</div>
              {resource.generation_per_second > 0 && (
                <div className="resource-rate">+{resource.generation_per_second.toFixed(2)}/s</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Wave Info Panel */}
      {waveInfo && (
        <div className="wave-panel">
          <h3>Tower Defense</h3>
          <div className="wave-status">
            <div>Wave: {waveInfo.current_wave}</div>
            <div>Status: {waveInfo.wave_active ? 'ACTIVE' : 'READY'}</div>
            {waveInfo.wave_active && (
              <div>Enemies: {waveInfo.enemies_remaining}</div>
            )}
          </div>
          
          {!waveInfo.wave_active && (
            <div
              className="next-wave-preview"
              onMouseEnter={() => handleMouseEnter('wave', 'next')}
              onMouseLeave={handleMouseLeave}
            >
              <div>Next Wave Preview:</div>
              <div>{waveInfo.preview.enemy_count} enemies</div>
              <div>Difficulty: {waveInfo.preview.estimated_difficulty.toFixed(1)}</div>
              {waveInfo.next_wave_eta && (
                <div>Starts in: {formatTime(waveInfo.next_wave_eta)}</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Research Panel */}
      {researchInfo && (
        <div className="research-panel">
          <h3>Research</h3>
          
          {researchInfo.active_research && (
            <div className="active-research">
              <div className="research-name">{researchInfo.active_research.name}</div>
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${researchInfo.active_research.progress * 100}%` }}
                />
              </div>
              <div className="research-eta">
                ETA: {formatTime(researchInfo.active_research.eta_seconds)}
              </div>
            </div>
          )}

          <div className="available-research">
            <h4>Available ({researchInfo.available_techs.length})</h4>
            {researchInfo.available_techs.slice(0, 3).map((tech) => (
              <div
                key={tech.id}
                className={`research-item ${tech.can_afford ? 'affordable' : 'expensive'}`}
                onMouseEnter={() => handleMouseEnter('tech', tech.id)}
                onMouseLeave={handleMouseLeave}
              >
                <div className="tech-name">{tech.name}</div>
                <div className="tech-cost">
                  {Object.entries(tech.cost).map(([resource, amount]) => (
                    <span key={resource}>{amount} {resource}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Build Queue Panel */}
      <div className="build-panel">
        <h3>Construction</h3>
        <div className="build-queue">
          {gameBindings.getBuildQueue().map((item) => (
            <div
              key={item.id}
              className="build-item"
              onMouseEnter={() => handleMouseEnter('building', item.id)}
              onMouseLeave={handleMouseLeave}
            >
              <div className="build-name">{item.name}</div>
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${item.progress * 100}%` }}
                />
              </div>
              {item.eta_seconds && (
                <div className="build-eta">ETA: {formatTime(item.eta_seconds)}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-panel">
        <button 
          className="game-button"
          onClick={() => console.log('Start Wave')}
          disabled={waveInfo?.wave_active}
        >
          Start Wave
        </button>
        
        <button 
          className="game-button"
          onClick={() => console.log('Build Solar Panel')}
        >
          Build Solar Panel
        </button>
        
        <button 
          className="game-button"
          onClick={() => console.log('Start Research')}
          disabled={researchInfo?.active_research !== null}
        >
          Research Nanobots
        </button>
      </div>

      {/* Tooltip */}
      {tooltip && hoveredElement && (
        <div className="tooltip">
          <div className="tooltip-title">{tooltip.title}</div>
          <div className="tooltip-description">{tooltip.description}</div>
          
          {tooltip.cost && (
            <div className="tooltip-cost">
              <strong>Cost:</strong>
              {Object.entries(tooltip.cost).map(([resource, amount]) => (
                <span key={resource}> {amount} {resource}</span>
              ))}
            </div>
          )}
          
          {tooltip.breakdown && (
            <div className="tooltip-breakdown">
              {tooltip.breakdown.map((item, index) => (
                <div 
                  key={index}
                  className={`breakdown-item ${item.positive ? 'positive' : 'negative'}`}
                >
                  {item.label}: {item.value}
                </div>
              ))}
            </div>
          )}
          
          <div className={`tooltip-status status-${tooltip.status}`}>
            {tooltip.status.replace('_', ' ')}
          </div>
        </div>
      )}

      <style>{`
        .game-hud {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          grid-template-rows: auto auto auto;
          gap: 1rem;
          padding: 1rem;
          font-family: 'Courier New', monospace;
          background: #0a0a0a;
          color: #00ff00;
          min-height: 100vh;
          position: relative;
        }

        .resource-panel, .wave-panel, .research-panel, .build-panel {
          border: 1px solid #00ff00;
          padding: 1rem;
          background: rgba(0, 255, 0, 0.05);
        }

        .resource-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .resource-item {
          padding: 0.5rem;
          border: 1px solid #004400;
          background: rgba(0, 255, 0, 0.1);
          text-align: center;
          cursor: pointer;
        }

        .resource-amount {
          font-size: 1.2rem;
          font-weight: bold;
        }

        .resource-rate {
          font-size: 0.8rem;
          color: #88ff88;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #001100;
          border: 1px solid #004400;
          margin: 0.25rem 0;
        }

        .progress-fill {
          height: 100%;
          background: #00ff00;
          transition: width 0.3s ease;
        }

        .game-button {
          background: #001100;
          border: 1px solid #00ff00;
          color: #00ff00;
          padding: 0.5rem 1rem;
          margin: 0.25rem;
          cursor: pointer;
          font-family: inherit;
        }

        .game-button:hover:not(:disabled) {
          background: rgba(0, 255, 0, 0.1);
        }

        .game-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .research-item, .build-item {
          padding: 0.5rem;
          margin: 0.25rem 0;
          border: 1px solid #004400;
          cursor: pointer;
        }

        .research-item.affordable {
          border-color: #00ff00;
        }

        .research-item.expensive {
          border-color: #ff4400;
          opacity: 0.7;
        }

        .tooltip {
          position: fixed;
          top: 1rem;
          right: 1rem;
          max-width: 300px;
          padding: 1rem;
          background: #000;
          border: 2px solid #00ff00;
          z-index: 1000;
          font-size: 0.9rem;
        }

        .tooltip-title {
          font-weight: bold;
          margin-bottom: 0.5rem;
        }

        .tooltip-cost {
          margin: 0.5rem 0;
          color: #ffff00;
        }

        .breakdown-item {
          font-size: 0.8rem;
          margin: 0.1rem 0;
        }

        .breakdown-item.positive {
          color: #88ff88;
        }

        .breakdown-item.negative {
          color: #ff8888;
        }

        .status-available { color: #00ff00; }
        .status-locked { color: #ff4400; }
        .status-coming_soon { color: #ffff00; }
        .status-error { color: #ff0000; }

        h3, h4 {
          margin: 0 0 0.5rem 0;
          color: #00ff00;
          text-transform: uppercase;
        }

        .action-panel {
          grid-column: 1 / -1;
          display: flex;
          gap: 1rem;
          justify-content: center;
          padding: 1rem;
          border: 1px solid #00ff00;
          background: rgba(0, 255, 0, 0.05);
        }

        .wave-status > div, .next-wave-preview > div {
          margin: 0.25rem 0;
        }

        .next-wave-preview {
          margin-top: 0.5rem;
          padding: 0.5rem;
          border: 1px solid #444;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}