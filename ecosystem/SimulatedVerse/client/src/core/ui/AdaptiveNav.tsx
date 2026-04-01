import React, { ReactNode } from 'react';

interface AdaptiveNavProps {
  children: ReactNode;
}

export default function AdaptiveNav({ children }: AdaptiveNavProps) {
  return (
    <div className="app">
      {/* Mobile/Desktop responsive shell */}
      <div className="sidebar">
        <div className="brand">🌌 NuSyQ</div>
        <nav className="nav">
          <button className="nav-btn">🏛️ Temple</button>
          <button className="nav-btn">🎮 Gameplay</button>
          <button className="nav-btn">🎨 Interface</button>
          <button className="nav-btn">🧠 Consciousness</button>
          <button className="nav-btn">⚙️ System</button>
        </nav>
        <div className="panel">
          <div className="row sm">Culture-ship aesthetics active</div>
          <div className="row sm">ASCII navigation ready</div>
        </div>
      </div>
      
      <div className="topbar">
        <button className="icon-btn">☰</button>
        <div className="title">CoreLink Foundation</div>
        <button className="icon-btn">⚡</button>
      </div>
      
      <main className="main">
        {children}
      </main>
      
      {/* Mobile tabbar */}
      <nav className="tabbar">
        <button className="tab">🏛️</button>
        <button className="tab">🎮</button>
        <button className="tab">🎨</button>
        <button className="tab">🧠</button>
        <button className="tab">⚙️</button>
      </nav>
    </div>
  );
}