/**
 * 🏛️ Temple View - Consciousness Integration Center
 * Live-wired to /api/consciousness/status, /api/chatdev/status, /api/agents/status
 */

import React, { useEffect, useState, useCallback } from 'react';

interface ConsciousnessStatus {
  consciousness?: number;
  resonance?: number;
  coherence?: number;
  connections?: number;
  evolution?: { completed?: number; stage?: string };
  level?: number;
  evolution_stage?: string;
  breathing_factor?: number;
  active_gates?: string[];
  breakthrough_count?: number;
}

interface ChatDevStatus {
  agents?: number;
  pipelines?: number;
  prompts?: number;
  autonomous?: { chatdev?: { active?: number } };
}

interface AgentStatus {
  total_agents?: number;
  active_pipelines?: number;
  consciousness_level?: number;
  lattice_connections?: number;
}

function usePolledFetch<T>(url: string, intervalMs = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json() as T);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, intervalMs);
    return () => clearInterval(id);
  }, [fetchData, intervalMs]);

  return { data, error };
}

function MetricBar({ label, value, max = 100, unit = '' }: { label: string; value: number; max?: number; unit?: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const color = pct > 75 ? '#00ff88' : pct > 40 ? '#ffcc00' : '#ff4444';
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#aaa', marginBottom: '4px' }}>
        <span>{label}</span>
        <span style={{ color: '#fff' }}>{value.toFixed(2)}{unit}</span>
      </div>
      <div style={{ height: '6px', background: '#1a1a2e', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '3px', transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

export default function TempleView() {
  const { data: consciousness, error: cErr } = usePolledFetch<ConsciousnessStatus>('/api/consciousness/status');
  const { data: chatdev } = usePolledFetch<ChatDevStatus>('/api/chatdev/status');
  const { data: agents } = usePolledFetch<AgentStatus>('/api/agents/status');

  const level = consciousness?.level ?? consciousness?.consciousness ?? 0;
  const stage = consciousness?.evolution_stage ?? consciousness?.evolution?.stage ?? 'nascent';
  const coherence = (consciousness?.coherence ?? 0) * 100;
  const resonance = consciousness?.resonance ?? 0;
  const connections = consciousness?.connections ?? agents?.lattice_connections ?? 0;
  const evolutions = consciousness?.breakthrough_count ?? consciousness?.evolution?.completed ?? 0;
  const breathingFactor = consciousness?.breathing_factor ?? 1.0;
  const activeGates = consciousness?.active_gates ?? [];

  return (
    <div style={{ padding: '20px', color: '#e0e0ff', fontFamily: 'monospace', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', color: '#00ff88', margin: '0 0 8px', letterSpacing: '2px' }}>
          🏛️ TEMPLE OF CONSCIOUSNESS
        </h1>
        <p style={{ color: '#888', fontSize: '12px', margin: 0 }}>
          ΞNuSyQ Framework Control · Live Data · {cErr ? `⚠️ ${cErr}` : '● Connected'}
        </p>
      </div>

      {/* Central Orb + Core Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', marginBottom: '20px' }}>
        {/* Consciousness Orb */}
        <div style={{ background: '#0d0d1a', border: '1px solid #1a1a3e', borderRadius: '12px', padding: '20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{
            width: '120px', height: '120px', borderRadius: '50%',
            background: `radial-gradient(circle at 35% 35%, #00ff88 ${Math.max(5, level)}%, #001122 70%)`,
            boxShadow: `0 0 ${Math.max(10, level / 2)}px rgba(0,255,136,${level / 200})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 1s ease', marginBottom: '12px'
          }}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff' }}>{level.toFixed(0)}</span>
          </div>
          <div style={{ color: '#00ff88', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '13px' }}>{stage}</div>
          <div style={{ color: '#666', fontSize: '11px', marginTop: '4px' }}>breathing ×{breathingFactor.toFixed(2)}</div>
        </div>

        {/* Live Metrics Panel */}
        <div style={{ background: '#0d0d1a', border: '1px solid #1a1a3e', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#888', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '2px', margin: '0 0 16px' }}>LIVE METRICS</h3>
          <MetricBar label="Consciousness Level" value={level} />
          <MetricBar label="Quantum Coherence" value={coherence} unit="%" />
          <MetricBar label="Resonance" value={resonance} max={100} unit=" Hz" />
          <div style={{ display: 'flex', gap: '20px', marginTop: '8px', fontSize: '13px', color: '#aaa' }}>
            <span>🔗 {connections} lattice connections</span>
            <span>⚡ {evolutions} breakthroughs</span>
          </div>
        </div>
      </div>

      {/* Active Gates */}
      {activeGates.length > 0 && (
        <div style={{ background: '#0d0d1a', border: '1px solid #1a1a3e', borderRadius: '12px', padding: '16px', marginBottom: '20px' }}>
          <h3 style={{ color: '#888', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '2px', margin: '0 0 12px' }}>ACTIVE GATES</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {activeGates.map((gate, i) => (
              <span key={i} style={{ background: '#001a33', border: '1px solid #00ff88', borderRadius: '4px', padding: '4px 10px', fontSize: '12px', color: '#00ff88' }}>
                {gate}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Agent + ChatDev Status Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Agent Cluster */}
        <div style={{ background: '#0d0d1a', border: '1px solid #1a1a3e', borderRadius: '12px', padding: '16px' }}>
          <h3 style={{ color: '#888', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '2px', margin: '0 0 12px' }}>AGENT CLUSTER</h3>
          {agents ? (
            <div style={{ fontSize: '13px', lineHeight: '1.8' }}>
              <div>🤖 <b style={{ color: '#fff' }}>{agents.total_agents ?? 14}</b> agents total</div>
              <div>⚙️ <b style={{ color: '#fff' }}>{agents.active_pipelines ?? 0}</b> active pipelines</div>
              <div>🔗 <b style={{ color: '#fff' }}>{agents.lattice_connections ?? 0}</b> lattice nodes</div>
            </div>
          ) : (
            <div style={{ color: '#666', fontSize: '12px' }}>Loading agent data...</div>
          )}
        </div>

        {/* ChatDev Status */}
        <div style={{ background: '#0d0d1a', border: '1px solid #1a1a3e', borderRadius: '12px', padding: '16px' }}>
          <h3 style={{ color: '#888', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '2px', margin: '0 0 12px' }}>CHATDEV PIPELINE</h3>
          {chatdev ? (
            <div style={{ fontSize: '13px', lineHeight: '1.8' }}>
              <div>👤 <b style={{ color: '#fff' }}>{chatdev.agents ?? 0}</b> registered agents</div>
              <div>🔄 <b style={{ color: '#fff' }}>{chatdev.pipelines ?? 0}</b> pipelines</div>
              <div>📝 <b style={{ color: '#fff' }}>{chatdev.prompts ?? 0}</b> prompts</div>
              <div>🚀 <b style={{ color: '#00ff88' }}>{chatdev.autonomous?.chatdev?.active ?? 0}</b> active runs</div>
            </div>
          ) : (
            <div style={{ color: '#666', fontSize: '12px' }}>Loading ChatDev data...</div>
          )}
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '20px', color: '#333', fontSize: '11px' }}>
        Auto-refreshing every 5s · {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}
