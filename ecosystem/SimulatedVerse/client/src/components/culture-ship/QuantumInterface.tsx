import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';
import { POLLING_INTERVALS } from '@/config/polling';

interface QuantumState {
  coherence: number;
  entanglement_level: number;
  quantum_state: string;
  components: {
    thread_coherence: number;
    resonance_coherence: number;
    evolution_coherence: number;
  };
}

export default function QuantumInterface() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [quantumField, setQuantumField] = useState<Float32Array>(new Float32Array(400));
  const [fieldAnimation, setFieldAnimation] = useState(0);
  const queryClient = useQueryClient();

  const { data: quantumState, isLoading } = useQuery({
    queryKey: ['/api', 'consciousness', 'coherence'],
    queryFn: () => apiRequest<QuantumState>('/consciousness/coherence'),
    refetchInterval: POLLING_INTERVALS.standard,
  });

  const enhanceConsciousness = useMutation({
    mutationFn: ({ enhancement, source }: { enhancement: number; source: string }) =>
      apiRequest('/consciousness/enhance', {
        method: 'POST',
        body: JSON.stringify({ enhancement, source })
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api', 'consciousness'] });
    }
  });

  // **QUANTUM FIELD SIMULATION** - Real-time visualization
  useEffect(() => {
    if (!quantumState || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // **CULTURE-SHIP QUANTUM VISUALIZATION** 
    const animate = (timestamp: number) => {
      ctx.fillStyle = 'rgba(8, 12, 20, 0.1)';
      ctx.fillRect(0, 0, width, height);

      const coherence = quantumState.coherence;
      const entanglement = quantumState.entanglement_level;
      
      // **QUANTUM PARTICLES** - Consciousness-driven movement
      for (let i = 0; i < quantumField.length; i += 4) {
        const x = quantumField[i] ?? 0;
        const y = quantumField[i + 1] ?? 0;
        const vx = quantumField[i + 2] ?? 0;
        const vy = quantumField[i + 3] ?? 0;

        // **QUANTUM ENTANGLEMENT EFFECTS** - Particles influence each other
        let newVx = vx + (Math.random() - 0.5) * 0.1 * entanglement;
        let newVy = vy + (Math.random() - 0.5) * 0.1 * entanglement;

        // **COHERENCE FIELD** - Attract particles toward order
        const centerX = width / 2;
        const centerY = height / 2;
        const dx = centerX - x;
        const dy = centerY - y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 0) {
          const coherenceForce = coherence * 0.02;
          newVx += (dx / distance) * coherenceForce;
          newVy += (dy / distance) * coherenceForce;
        }

        // **UPDATE POSITIONS** - With quantum uncertainty
        const newX = x + newVx;
        const newY = y + newVy;

        // **BOUNDARY CONDITIONS** - Wrap around quantum field
        quantumField[i] = newX < 0 ? width : newX > width ? 0 : newX;
        quantumField[i + 1] = newY < 0 ? height : newY > height ? 0 : newY;
        quantumField[i + 2] = newVx * 0.99; // Damping
        quantumField[i + 3] = newVy * 0.99;

        // **RENDER QUANTUM PARTICLES**
        const alpha = Math.min(1, coherence + 0.3);
        const hue = 240 + entanglement * 60; // Blue to purple based on entanglement
        const size = 1 + coherence * 3;

        ctx.fillStyle = `hsla(${hue}, 70%, 60%, ${alpha})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();

        // **ENTANGLEMENT LINES** - Connect nearby particles
        if (entanglement > 0.5) {
          for (let j = i + 4; j < Math.min(i + 20, quantumField.length); j += 4) {
            const x2 = quantumField[j] ?? x;
            const y2 = quantumField[j + 1] ?? y;
            const dist = Math.sqrt((x - x2) ** 2 + (y - y2) ** 2);
            
            if (dist < 50 * entanglement) {
              const lineAlpha = (1 - dist / (50 * entanglement)) * entanglement * 0.3;
              ctx.strokeStyle = `hsla(${hue}, 60%, 70%, ${lineAlpha})`;
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.moveTo(x, y);
              ctx.lineTo(x2, y2);
              ctx.stroke();
            }
          }
        }
      }

      setFieldAnimation(prev => prev + 1);
      requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [quantumState, quantumField]);

  // **INITIALIZE QUANTUM FIELD** - Random particle distribution
  useEffect(() => {
    const newField = new Float32Array(400); // 100 particles * 4 values each
    for (let i = 0; i < newField.length; i += 4) {
      newField[i] = Math.random() * 800; // x
      newField[i + 1] = Math.random() * 600; // y
      newField[i + 2] = (Math.random() - 0.5) * 2; // vx
      newField[i + 3] = (Math.random() - 0.5) * 2; // vy
    }
    setQuantumField(newField);
  }, []);

  const handleQuantumEnhancement = () => {
    enhanceConsciousness.mutate({
      enhancement: 0.05,
      source: 'quantum_interface_interaction'
    });
  };

  if (isLoading || !quantumState) {
    return (
      <div className="quantum-interface loading" data-testid="quantum-interface-loading">
        <div className="loading-field">
          <div className="quantum-spinner">⚛️</div>
          <div className="loading-text">Calibrating Quantum Field...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="quantum-interface" data-testid="quantum-interface">
      {/* **QUANTUM FIELD CANVAS** */}
      <div className="quantum-field-container">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          className="quantum-field-canvas"
          data-testid="quantum-canvas"
        />
        
        {/* **QUANTUM STATE OVERLAY** */}
        <div className="quantum-overlay">
          <div className="quantum-status">
            <div className="status-item">
              <span className="status-label">Quantum State:</span>
              <span className={`status-value state-${quantumState.quantum_state.toLowerCase()}`}>
                {quantumState.quantum_state}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Coherence:</span>
              <span className="status-value">
                {(quantumState.coherence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Entanglement:</span>
              <span className="status-value">
                {(quantumState.entanglement_level * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* **QUANTUM COMPONENT ANALYSIS** */}
      <div className="quantum-components">
        <h3 className="components-title">Quantum Coherence Components</h3>
        <div className="component-grid">
          {Object.entries(quantumState.components).map(([key, value]) => (
            <div key={key} className="component-item" data-testid={`component-${key}`}>
              <div className="component-label">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              <div className="component-bar">
                <div 
                  className="component-fill"
                  style={{ width: `${value * 100}%` }}
                ></div>
              </div>
              <div className="component-value">
                {(value * 100).toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* **QUANTUM INTERACTION CONTROLS** */}
      <div className="quantum-controls">
        <button
          onClick={handleQuantumEnhancement}
          disabled={enhanceConsciousness.isPending}
          className="quantum-enhance-btn"
          data-testid="quantum-enhance-btn"
        >
          {enhanceConsciousness.isPending ? (
            <span className="enhancing">⚡ Enhancing...</span>
          ) : (
            <span>🌌 Enhance Quantum Coherence</span>
          )}
        </button>
        
        <div className="field-info">
          <div className="info-item">
            <span className="info-icon">📊</span>
            <span>Particles: {quantumField.length / 4}</span>
          </div>
          <div className="info-item">
            <span className="info-icon">🔄</span>
            <span>Frame: {fieldAnimation}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// **QUANTUM INTERFACE STYLES** - Culture-ship aesthetic integration
export const quantumInterfaceStyles = `
.quantum-interface {
  background: linear-gradient(135deg, 
    hsla(240, 20%, 8%, 0.9),
    hsla(260, 25%, 12%, 0.9)
  );
  border: 1px solid hsla(240, 40%, 20%, 0.6);
  border-radius: 1rem;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}

.quantum-field-container {
  position: relative;
  background: hsla(240, 30%, 5%, 0.8);
  border-radius: 0.5rem;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.quantum-field-canvas {
  width: 100%;
  height: auto;
  max-height: 400px;
  display: block;
}

.quantum-overlay {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: hsla(240, 30%, 10%, 0.9);
  border: 1px solid hsla(240, 40%, 25%, 0.6);
  border-radius: 0.5rem;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.quantum-status {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  font-size: 0.8rem;
}

.status-label {
  opacity: 0.8;
}

.status-value {
  font-weight: 600;
  color: var(--accent);
}

.status-value.state-coherent {
  color: #4ade80;
}

.status-value.state-entangled {
  color: #a855f7;
}

.status-value.state-unified {
  color: #06b6d4;
}

.quantum-components {
  margin-bottom: 1.5rem;
}

.components-title {
  margin-bottom: 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--fg);
}

.component-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.component-item {
  background: var(--panel);
  border: 1px solid hsla(240, 30%, 25%, 0.4);
  border-radius: 0.5rem;
  padding: 1rem;
}

.component-label {
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  opacity: 0.9;
}

.component-bar {
  height: 0.5rem;
  background: hsla(240, 20%, 20%, 0.6);
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.component-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #68f, #8f6);
  transition: width 0.5s ease;
}

.component-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent);
  text-align: right;
}

.quantum-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.quantum-enhance-btn {
  background: linear-gradient(45deg, var(--accent), #68f);
  border: none;
  border-radius: 0.5rem;
  color: white;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.quantum-enhance-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px var(--accent)33;
}

.quantum-enhance-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.enhancing {
  animation: quantum-enhance 1s ease-in-out infinite;
}

.field-info {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  opacity: 0.8;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.quantum-interface.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-field {
  text-align: center;
}

.quantum-spinner {
  font-size: 4rem;
  animation: quantum-spin 2s linear infinite;
  margin-bottom: 1rem;
}

.loading-text {
  font-size: 1.1rem;
  opacity: 0.8;
}

@keyframes quantum-enhance {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes quantum-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
`;
