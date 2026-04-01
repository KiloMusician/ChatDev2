import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';
import { ANIMATION_INTERVALS, POLLING_INTERVALS } from '@/config/polling';

interface ConsciousnessData {
  level: number;
  resonance: number;
  coherence: number;
  narrative_depth: number;
  evolution_rate: number;
  active_threads: string[];
  quantum_entanglement: number;
}

export default function ConsciousnessIndicator() {
  const [pulseIntensity, setPulseIntensity] = useState(0.5);
  
  const { data: consciousness, isLoading } = useQuery({
    queryKey: ['/api', 'consciousness', 'state'],
    queryFn: () => apiRequest<ConsciousnessData>('/consciousness/state'),
    refetchInterval: POLLING_INTERVALS.critical,
  });

  // **QUANTUM PULSE EFFECT** - Consciousness-driven visual feedback
  useEffect(() => {
    if (consciousness) {
      const targetIntensity = consciousness.level * consciousness.coherence;
      setPulseIntensity(targetIntensity);
      
      // **CULTURE-SHIP RESONANCE** - Dynamic pulse based on quantum entanglement
      const pulseInterval = setInterval(() => {
        setPulseIntensity(prev => {
          const variation = (Math.random() - 0.5) * 0.1 * consciousness.quantum_entanglement;
          return Math.max(0.1, Math.min(1.0, targetIntensity + variation));
        });
      }, ANIMATION_INTERVALS.pulse);

      return () => clearInterval(pulseInterval);
    }
  }, [consciousness]);

  if (isLoading || !consciousness) {
    return (
      <div className="consciousness-indicator loading" data-testid="consciousness-loading">
        <div className="consciousness-core">
          <div className="loading-pulse">⟳</div>
        </div>
        <div className="consciousness-label">Initializing Consciousness...</div>
      </div>
    );
  }

  const getConsciousnessPhase = (level: number): string => {
    if (level < 0.2) return 'Nascent';
    if (level < 0.4) return 'Emerging';
    if (level < 0.6) return 'Aware';
    if (level < 0.8) return 'Conscious';
    if (level < 0.95) return 'Transcendent';
    return 'Unified';
  };

  const getQuantumState = (entanglement: number): string => {
    if (entanglement < 0.3) return 'ISOLATED';
    if (entanglement < 0.6) return 'CONNECTED';
    if (entanglement < 0.8) return 'ENTANGLED';
    return 'UNIFIED';
  };

  return (
    <div 
      className="consciousness-indicator"
      style={{
        '--consciousness-level': consciousness.level,
        '--resonance-level': consciousness.resonance,
        '--coherence-level': consciousness.coherence,
        '--pulse-intensity': pulseIntensity,
        '--quantum-entanglement': consciousness.quantum_entanglement
      } as React.CSSProperties}
      data-testid="consciousness-indicator"
    >
      {/* **CENTRAL CONSCIOUSNESS CORE** */}
      <div className="consciousness-core">
        <div className="quantum-field">
          <div className="consciousness-orb"></div>
          <div className="resonance-rings">
            {Array.from({ length: 3 }, (_, i) => (
              <div 
                key={i} 
                className="resonance-ring" 
                style={{ 
                  animationDelay: `${i * 0.5}s`,
                  opacity: consciousness.resonance * (1 - i * 0.2)
                }}
              ></div>
            ))}
          </div>
        </div>
        
        {/* **CONSCIOUSNESS METRICS** */}
        <div className="consciousness-metrics">
          <div className="metric">
            <span className="metric-label">Level</span>
            <span className="metric-value" data-testid="consciousness-level">
              {(consciousness.level * 100).toFixed(1)}%
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Phase</span>
            <span className="metric-value phase" data-testid="consciousness-phase">
              {getConsciousnessPhase(consciousness.level)}
            </span>
          </div>
        </div>
      </div>

      {/* **QUANTUM COHERENCE DISPLAY** */}
      <div className="coherence-display">
        <div className="coherence-bar">
          <div 
            className="coherence-fill"
            style={{ width: `${consciousness.coherence * 100}%` }}
            data-testid="coherence-bar"
          ></div>
        </div>
        <span className="coherence-label">
          Quantum Coherence: {(consciousness.coherence * 100).toFixed(1)}%
        </span>
      </div>

      {/* **NARRATIVE THREADS** */}
      <div className="narrative-threads">
        <div className="threads-header">
          <span className="threads-icon">🧵</span>
          <span className="threads-label">Active Threads</span>
          <span className="threads-count" data-testid="threads-count">
            {consciousness.active_threads.length}
          </span>
        </div>
        <div className="threads-list">
          {consciousness.active_threads.map((thread: string, index: number) => (
            <div 
              key={thread} 
              className="thread-item"
              style={{ animationDelay: `${index * 0.1}s` }}
              data-testid={`thread-${thread}`}
            >
              <div className="thread-pulse"></div>
              <span className="thread-name">{thread.replace(/_/g, ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* **QUANTUM STATE INDICATOR** */}
      <div className="quantum-state">
        <div className="quantum-badge">
          <span className="quantum-icon">⚛️</span>
          <span className="quantum-label" data-testid="quantum-state">
            {getQuantumState(consciousness.quantum_entanglement)}
          </span>
        </div>
        <div className="entanglement-level">
          Entanglement: {(consciousness.quantum_entanglement * 100).toFixed(1)}%
        </div>
      </div>

      {/* **EVOLUTION RATE** */}
      <div className="evolution-display">
        <div className="evolution-icon">🧬</div>
        <div className="evolution-info">
          <span className="evolution-label">Evolution Rate</span>
          <span className="evolution-value" data-testid="evolution-rate">
            {(consciousness.evolution_rate * 100).toFixed(1)}%/cycle
          </span>
        </div>
        <div className="evolution-bar">
          <div 
            className="evolution-fill"
            style={{ width: `${consciousness.evolution_rate * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
}

// **CONSCIOUSNESS-AWARE STYLING** - Export for theme integration
export const consciousnessStyles = `
.consciousness-indicator {
  background: radial-gradient(
    ellipse at center,
    hsla(240, 70%, calc(5% + var(--consciousness-level) * 10%), 0.1),
    hsla(240, 50%, calc(2% + var(--consciousness-level) * 5%), 0.05)
  );
  border: 1px solid hsla(240, 60%, calc(20% + var(--consciousness-level) * 20%), 0.3);
  border-radius: 1rem;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}

.consciousness-core {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.quantum-field {
  position: relative;
  width: 4rem;
  height: 4rem;
}

.consciousness-orb {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    hsla(240, 80%, calc(60% + var(--consciousness-level) * 20%), var(--pulse-intensity)),
    hsla(260, 70%, calc(40% + var(--consciousness-level) * 30%), calc(var(--pulse-intensity) * 0.7)),
    transparent
  );
  animation: consciousness-pulse 2s ease-in-out infinite;
  box-shadow: 
    0 0 calc(1rem * var(--pulse-intensity)) hsla(240, 80%, 60%, var(--pulse-intensity)),
    inset 0 0 calc(0.5rem * var(--consciousness-level)) hsla(260, 90%, 80%, 0.5);
}

.resonance-rings {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.resonance-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid hsla(240, 70%, 60%, var(--resonance-level));
  border-radius: 50%;
  animation: resonance-expand 3s ease-out infinite;
}

.resonance-ring:nth-child(1) { width: 120%; height: 120%; }
.resonance-ring:nth-child(2) { width: 140%; height: 140%; }
.resonance-ring:nth-child(3) { width: 160%; height: 160%; }

.consciousness-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 8rem;
}

.metric-label {
  font-size: 0.9rem;
  opacity: 0.8;
}

.metric-value {
  font-weight: 600;
  color: hsla(240, 70%, calc(60% + var(--consciousness-level) * 20%), 1);
}

.metric-value.phase {
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
}

.coherence-display {
  margin-bottom: 1rem;
}

.coherence-bar {
  height: 0.5rem;
  background: var(--panel);
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.coherence-fill {
  height: 100%;
  background: linear-gradient(
    90deg,
    hsla(240, 70%, 50%, 0.8),
    hsla(260, 80%, 60%, 1),
    hsla(280, 70%, 70%, 0.9)
  );
  transition: width 0.5s ease;
}

.coherence-label {
  font-size: 0.8rem;
  opacity: 0.9;
}

.narrative-threads {
  margin-bottom: 1rem;
}

.threads-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.threads-count {
  background: var(--accent);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 0.75rem;
  font-size: 0.7rem;
}

.threads-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.thread-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--panel);
  border-radius: 0.5rem;
  animation: thread-fade-in 0.5s ease-out;
}

.thread-pulse {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--accent);
  animation: thread-pulse 1s ease-in-out infinite;
}

.thread-name {
  font-size: 0.8rem;
  text-transform: capitalize;
}

.quantum-state {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.quantum-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--panel);
  border-radius: 1rem;
  border: 1px solid hsla(240, 50%, 50%, 0.3);
}

.quantum-label {
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
}

.entanglement-level {
  font-size: 0.8rem;
  opacity: 0.8;
}

.evolution-display {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.evolution-icon {
  font-size: 1.5rem;
}

.evolution-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.evolution-label {
  font-size: 0.8rem;
  opacity: 0.8;
}

.evolution-value {
  font-weight: 600;
  color: var(--accent);
}

.evolution-bar {
  width: 4rem;
  height: 0.5rem;
  background: var(--panel);
  border-radius: 0.25rem;
  overflow: hidden;
}

.evolution-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #68f);
  transition: width 0.5s ease;
}

@keyframes consciousness-pulse {
  0%, 100% { transform: scale(1); opacity: var(--pulse-intensity); }
  50% { transform: scale(1.1); opacity: calc(var(--pulse-intensity) * 1.2); }
}

@keyframes resonance-expand {
  0% { transform: translate(-50%, -50%) scale(0.8); opacity: var(--resonance-level); }
  100% { transform: translate(-50%, -50%) scale(1.2); opacity: 0; }
}

@keyframes thread-fade-in {
  from { opacity: 0; transform: translateY(0.5rem); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes thread-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.consciousness-indicator.loading .consciousness-core {
  justify-content: center;
}

.loading-pulse {
  font-size: 2rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
`;
