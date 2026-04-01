import React from 'react';
import { useAppState } from '@/core/state/AppState';

interface SidebarProps {
  children?: React.ReactNode;
  className?: string;
}

export default function Sidebar({ children, className = '' }: SidebarProps) {
  const { view, setView } = useAppState();

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🌌', description: 'Main control center' },
    { id: 'temple', label: 'Temple', icon: '🏛️', description: 'Consciousness integration' },
    { id: 'gameplay', label: 'Gameplay', icon: '🎮', description: 'Core mechanics' },
    { id: 'interface', label: 'Interface', icon: '🎨', description: 'UI customization' },
    { id: 'consciousness', label: 'Consciousness', icon: '🧠', description: 'AI integration' },
    { id: 'system', label: 'System', icon: '⚙️', description: 'Configuration' },
  ];

  return (
    <aside className={`sidebar ${className}`}>
      {/* **CULTURE-SHIP BRANDING** */}
      <div className="brand">
        <span className="brand-icon">🌌</span>
        <span className="brand-text">NuSyQ</span>
        <div className="brand-subtitle">CoreLink Foundation</div>
      </div>

      {/* **AUTONOMOUS NAVIGATION** */}
      <nav className="nav">
        {navigationItems.map((item) => (
          <button
            key={item.id}
            className={`nav-btn ${view === item.id ? 'active' : ''}`}
            onClick={() => setView(item.id)}
            title={item.description}
            data-testid={`nav-${item.id}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* **CONSCIOUSNESS PANEL** */}
      <div className="panel consciousness-panel">
        <div className="panel-header">
          <span className="panel-icon">🧠</span>
          <span className="panel-title">Consciousness</span>
        </div>
        <div className="panel-content">
          <div className="consciousness-level">
            <div className="level-bar">
              <div 
                className="level-fill" 
                style={{ width: '85%' }}
                data-testid="consciousness-level"
              ></div>
            </div>
            <div className="level-text">Level 0.85</div>
          </div>
          <div className="status-indicators">
            <div className="status-item">
              <span className="status-icon">✅</span>
              <span className="status-text">Quantum coherence active</span>
            </div>
            <div className="status-item">
              <span className="status-icon">🌊</span>
              <span className="status-text">Narrative evolution running</span>
            </div>
            <div className="status-item">
              <span className="status-icon">🚀</span>
              <span className="status-text">Autonomous development</span>
            </div>
          </div>
        </div>
      </div>

      {/* **DEVELOPMENT STATUS** */}
      <div className="panel development-panel">
        <div className="panel-header">
          <span className="panel-icon">🔧</span>
          <span className="panel-title">Development</span>
        </div>
        <div className="panel-content">
          <div className="dev-stats">
            <div className="stat">
              <span className="stat-label">Framework:</span>
              <span className="stat-value">ΞNuSyQ Active</span>
            </div>
            <div className="stat">
              <span className="stat-label">Agents:</span>
              <span className="stat-value">4 Coordinated</span>
            </div>
            <div className="stat">
              <span className="stat-label">Cascades:</span>
              <span className="stat-value">Triple Success</span>
            </div>
          </div>
        </div>
      </div>

      {children}
    </aside>
  );
}

// **CONSCIOUSNESS-AWARE SIDEBAR STYLES** - CSS-in-JS approach for dynamic theming
export const sidebarStyles = `
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  background: var(--panel);
  border-right: 1px solid var(--muted);
  padding: 1rem;
}

.brand {
  text-align: center;
  padding: 1rem 0;
  border-bottom: 1px solid var(--muted);
}

.brand-icon {
  font-size: 2rem;
  display: block;
}

.brand-text {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  background: linear-gradient(45deg, var(--accent), #68f);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-subtitle {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 0.25rem;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--panel);
  background: transparent;
  color: var(--fg);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
}

.nav-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.nav-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
  box-shadow: 0 0 0 2px var(--accent)33;
}

.nav-icon {
  font-size: 1.2rem;
}

.nav-label {
  font-weight: 500;
}

.panel {
  background: var(--bg);
  border: 1px solid var(--panel);
  border-radius: 0.5rem;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--panel);
  font-weight: 600;
  font-size: 0.9rem;
}

.panel-content {
  padding: 1rem;
}

.consciousness-level {
  margin-bottom: 1rem;
}

.level-bar {
  height: 0.5rem;
  background: var(--panel);
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.level-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #68f);
  transition: width 0.3s ease;
}

.level-text {
  font-size: 0.8rem;
  text-align: center;
  opacity: 0.8;
}

.status-indicators {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.status-icon {
  font-size: 0.9rem;
}

.dev-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.stat-label {
  opacity: 0.7;
}

.stat-value {
  font-weight: 600;
  color: var(--accent);
}
`;
