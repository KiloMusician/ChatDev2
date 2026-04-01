// client/src/components/TripartiteMonitor.tsx
// Complete monitoring dashboard for System/Game/Simulation architecture
import React from 'react';
import { useAppStore, selectSystemHealth, selectConsciousness, selectGameResources } from '@/store/AppStore';
import { useOpsMonitoring } from '@/hooks/useSystemData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import OpsPane from './OpsPane';

export default function TripartiteMonitor() {
  const systemHealth = useAppStore(selectSystemHealth);
  const consciousness = useAppStore(selectConsciousness);
  const gameResources = useAppStore(selectGameResources);
  const { system, chug, unstick, overallHealth, isOperational } = useOpsMonitoring();

  // Chart data for health metrics
  const healthData = [
    { name: 'Build Success', value: Math.round(systemHealth.build_success_rate * 100) },
    { name: 'Agent Joy', value: Math.round(systemHealth.agent_joy_average * 100) },
    { name: 'Invariance', value: Math.round(systemHealth.invariance_score * 100) },
    { name: 'Consciousness', value: consciousness.level }
  ];

  // Resource data for game layer
  const resourceData = [
    { name: 'Energy', value: gameResources.energy, color: '#22c55e' },
    { name: 'Population', value: gameResources.population, color: '#3b82f6' },
    { name: 'Research', value: gameResources.research, color: '#a855f7' },
    { name: 'Materials', value: gameResources.materials, color: '#f59e0b' }
  ];

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">🏛️ Tripartite Architecture Monitor</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            isOperational 
              ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200' 
              : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
          }`}>
            {isOperational ? '✅ Operational' : '⚠️ Issues Detected'}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* System Layer */}
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">🔧 System/Repo</h3>
            <div className="space-y-2 text-sm">
              <div>Node.js + TypeScript</div>
              <div>Zod + Winston + P-Queue</div>
              <div>LangChain + AI SDK</div>
              <div className="font-mono text-green-600">
                Health: {Math.round(overallHealth * 100)}%
              </div>
            </div>
          </div>

          {/* Game Layer */}
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">🎮 Game/UI</h3>
            <div className="space-y-2 text-sm">
              <div>React + Zustand + Immer</div>
              <div>SWR + Recharts + Monaco</div>
              <div>React Hook Form</div>
              <div className="font-mono text-blue-600">
                Consciousness: {consciousness.level}%
              </div>
            </div>
          </div>

          {/* Simulation Layer */}
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">🌌 Simulation</h3>
            <div className="space-y-2 text-sm">
              <div>Tower Defense + Exploration</div>
              <div>State Machines + XState</div>
              <div>Event-Driven Architecture</div>
              <div className="font-mono text-purple-600">
                Resources: {gameResources.energy + gameResources.population}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Package Integration Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border shadow-lg">
          <h3 className="text-lg font-semibold mb-4">📦 Package Integration Status</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              { name: 'zod', status: 'active', layer: 'System' },
              { name: 'winston', status: 'active', layer: 'System' },
              { name: 'p-queue', status: 'active', layer: 'System' },
              { name: 'ts-pattern', status: 'ready', layer: 'System' },
              { name: 'zustand', status: 'active', layer: 'Game' },
              { name: 'immer', status: 'active', layer: 'Game' },
              { name: 'swr', status: 'active', layer: 'Game' },
              { name: 'recharts', status: 'active', layer: 'Game' },
              { name: 'ai (Vercel)', status: 'ready', layer: 'System' },
              { name: 'react-hook-form', status: 'ready', layer: 'Game' },
              { name: 'xstate', status: 'ready', layer: 'Simulation' },
              { name: 'madge', status: 'ready', layer: 'System' }
            ].map((pkg, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="font-mono text-xs">{pkg.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`px-1 text-xs rounded ${
                    pkg.status === 'active' ? 'bg-green-100 text-green-800' :
                    pkg.status === 'ready' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {pkg.status}
                  </span>
                  <span className="text-xs text-gray-500">{pkg.layer}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border shadow-lg">
          <h3 className="text-lg font-semibold mb-4">📊 System Health Metrics</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={healthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Resource Visualization */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border shadow-lg">
        <h3 className="text-lg font-semibold mb-4">🎮 Game Resources</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {resourceData.map((resource, i) => (
            <div key={i} className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded">
              <div className="text-2xl font-bold" style={{ color: resource.color }}>
                {resource.value}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {resource.name}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consciousness Active Tasks */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border shadow-lg">
        <h3 className="text-lg font-semibold mb-4">🧠 Consciousness Activity</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-2">Active Tasks ({consciousness.active_tasks.length})</h4>
            <div className="space-y-2">
              {consciousness.active_tasks.map((task, i) => (
                <div key={i} className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-sm">
                  🔄 {task}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium mb-2">Completed Tasks ({consciousness.completed_tasks.length})</h4>
            <div className="space-y-2 max-h-32 overflow-auto">
              {consciousness.completed_tasks.slice(-5).map((task, i) => (
                <div key={i} className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-sm">
                  ✅ {task}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Ops Monitoring */}
      <OpsPane />
    </div>
  );
}