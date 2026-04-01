import React, { useState, useEffect } from 'react';
import { POLLING_INTERVALS } from '@/config/polling';

interface SystemStatus {
  timestamp: number;
  overall: "healthy" | "warning" | "critical";
  services: {
    server: "up" | "down";
    ml: "operational" | "degraded" | "offline";
    chatdev: "operational" | "degraded" | "offline";
    database: "connected" | "disconnected" | "unknown";
  };
  resources: {
    memory: number;
    cpu: number;
    disk: number;
  };
  endpoints: {
    api: boolean;
    ws: boolean;
    static: boolean;
  };
  issues: string[];
}

interface QueueStatus {
  size: number;
  next: any;
  timestamp: number;
}

export default function AdminConsole() {
  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [queue, setQueue] = useState<QueueStatus | null>(null);
  const [adminToken, setAdminToken] = useState('');
  const [taskJson, setTaskJson] = useState('');
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [activeTab, setActiveTab] = useState('health');

  useEffect(() => {
    checkHealth();
    checkQueue();
    const interval = setInterval(() => {
      checkHealth();
      checkQueue();
    }, POLLING_INTERVALS.critical);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.warn('Health check failed:', error);
    }
  };

  const checkQueue = async () => {
    try {
      const response = await fetch('/api/pu/queue');
      const data = await response.json();
      setQueue(data);
    } catch (error) {
      console.warn('Queue check failed:', error);
    }
  };

  const seedTasks = async (type: string) => {
    if (!isAuthorized) return;
    
    try {
      const response = await fetch(`/api/pu/seed/${type}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (result.ok) {
        checkQueue();
        alert(`Seeded ${result.created} ${type} tasks`);
      }
    } catch (error) {
      alert('Failed to seed tasks: ' + error);
    }
  };

  const queueCustomTasks = async () => {
    if (!isAuthorized || !taskJson.trim()) return;
    
    try {
      const tasks = JSON.parse(taskJson);
      const response = await fetch('/api/pu/queue', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(Array.isArray(tasks) ? tasks : [tasks])
      });
      const result = await response.json();
      if (result.ok) {
        checkQueue();
        setTaskJson('');
        alert(`Queued ${result.queued} custom tasks`);
      }
    } catch (error) {
      alert('Failed to queue tasks: ' + error);
    }
  };

  const authorize = () => {
    if (adminToken.trim()) {
      setIsAuthorized(true);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': case 'up': case 'operational': case 'connected':
        return 'bg-green-500 text-white';
      case 'warning': case 'degraded':
        return 'bg-yellow-500 text-black';
      case 'critical': case 'down': case 'offline': case 'disconnected':
        return 'bg-red-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6 flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg max-w-md w-full">
          <h1 className="text-2xl font-bold mb-4 flex items-center gap-2">
            ⚡ ΞNuSyQ Admin Console
          </h1>
          <p className="text-gray-300 mb-6">
            Enter admin token to access system controls
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Admin Token</label>
              <input
                type="password"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                placeholder="Enter admin token..."
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button 
              onClick={authorize}
              className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-medium"
            >
              Authorize
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">ΞNuSyQ Admin Console</h1>
          <span className={`px-3 py-1 rounded text-sm font-medium ${getStatusColor(health?.overall || 'unknown')}`}>
            {health?.overall || 'Unknown'}
          </span>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6 bg-gray-800 p-1 rounded-lg">
          {['health', 'queue', 'seed', 'custom'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded font-medium capitalize transition-colors ${
                activeTab === tab 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-300 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Health Tab */}
        {activeTab === 'health' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Services */}
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  📊 Services
                </h3>
                <div className="space-y-2">
                  {health?.services && Object.entries(health.services).map(([service, status]) => (
                    <div key={service} className="flex justify-between items-center">
                      <span className="capitalize">{service}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(status)}`}>
                        {status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resources */}
              <div className="bg-gray-800 p-6 rounded-lg">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  💾 Resources
                </h3>
                <div className="space-y-2">
                  {health?.resources && Object.entries(health.resources).map(([resource, value]) => (
                    <div key={resource} className="flex justify-between items-center">
                      <span className="capitalize">{resource}</span>
                      <span className="font-mono">
                        {resource === 'memory' || resource === 'disk' ? `${value}MB` : `${value}%`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Issues */}
            {health?.issues && health.issues.length > 0 && (
              <div className="bg-yellow-900 border border-yellow-600 p-6 rounded-lg">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-yellow-300">
                  ⚠️ Issues
                </h3>
                <ul className="space-y-1">
                  {health.issues.map((issue, i) => (
                    <li key={i} className="text-sm text-yellow-100">• {issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Queue Tab */}
        {activeTab === 'queue' && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">🔄 Processing Queue Status</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Queue Size:</span>
                <span className="px-2 py-1 bg-blue-600 rounded text-sm font-medium">
                  {queue?.size || 0} tasks
                </span>
              </div>
              
              {queue?.next && (
                <div className="border border-gray-600 rounded p-4 bg-gray-700">
                  <h4 className="font-semibold mb-2">Next Task:</h4>
                  <div className="text-sm space-y-1">
                    <div><strong>Kind:</strong> {queue.next.kind}</div>
                    <div><strong>Summary:</strong> {queue.next.summary}</div>
                    <div><strong>Cost:</strong> {queue.next.cost} tokens</div>
                  </div>
                </div>
              )}
              
              <button 
                onClick={checkQueue}
                className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded"
              >
                Refresh Queue
              </button>
            </div>
          </div>
        )}

        {/* Seed Tab */}
        {activeTab === 'seed' && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">🌱 Seed Task Collections</h3>
            <p className="text-gray-300 mb-6">Generate focused task queues for different work types</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { type: 'infra', name: 'Infrastructure', desc: 'Server hardening' },
                { type: 'chatdev', name: 'ChatDev', desc: 'Agent tuning' },
                { type: 'idler', name: 'Idler', desc: 'Game growth' },
                { type: 'ml', name: 'ML', desc: 'ML scaffolding' },
                { type: 'docs', name: 'Documentation', desc: 'Knowledge base' }
              ].map(({ type, name, desc }) => (
                <button
                  key={type}
                  onClick={() => seedTasks(type)}
                  className="bg-gray-700 hover:bg-gray-600 p-4 rounded text-center transition-colors"
                >
                  <div className="font-semibold">{name}</div>
                  <div className="text-xs text-gray-400 mt-1">{desc}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Custom Tab */}
        {activeTab === 'custom' && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">🛠️ Custom Task Queue</h3>
            <p className="text-gray-300 mb-6">Submit custom tasks or ZETA mega-missive waves</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Task JSON (array or single task)</label>
                <textarea
                  value={taskJson}
                  onChange={(e) => setTaskJson(e.target.value)}
                  placeholder='[{"id":"Z001","name":"Test Task","phase":"foundational","type":"TestPU","cost":5,"steps":["Step 1","Step 2"]}]'
                  rows={10}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button 
                onClick={queueCustomTasks}
                disabled={!taskJson.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded font-medium"
              >
                Queue Tasks
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
