/**
 * REAL INFRASTRUCTURE DASHBOARD
 * Shows actual coding work, file changes, builds, errors - WHO/WHAT/WHERE/WHEN/WHY/HOW
 * Completely replaces game theater with actionable development intelligence
 */

import React, { useState, useEffect } from 'react';
import { POLLING_INTERVALS } from '@/config/polling';
import { infrastructureIntelligence, InfrastructureEvent } from '../services/infrastructure-intelligence';

export function InfrastructureDashboard() {
  const [events, setEvents] = useState<InfrastructureEvent[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  useEffect(() => {
    // Generate real-time infrastructure intelligence
    const updateEvents = () => {
      const realTimeEvents = infrastructureIntelligence.generateRealTimeIntel();
      const recentEvents = infrastructureIntelligence.getRecentEvents(50);
      setEvents([...realTimeEvents, ...recentEvents]);
    };

    // Update immediately and then on the critical cadence
    updateEvents();
    const interval = setInterval(updateEvents, POLLING_INTERVALS.critical);

    return () => clearInterval(interval);
  }, []);

  const filteredEvents = activeCategory === 'all' 
    ? events 
    : events.filter(event => event.category === activeCategory);

  const getPriorityColor = (priority: InfrastructureEvent['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-500 bg-red-100 border-red-300';
      case 'high': return 'text-orange-500 bg-orange-100 border-orange-300';
      case 'medium': return 'text-blue-500 bg-blue-100 border-blue-300';
      case 'low': return 'text-gray-500 bg-gray-100 border-gray-300';
    }
  };

  const getCategoryIcon = (category: InfrastructureEvent['category']) => {
    switch (category) {
      case 'build': return '🔨';
      case 'error': return '❌';
      case 'dependency': return '📦';
      case 'performance': return '⚡';
      case 'security': return '🔒';
      case 'test': return '🧪';
    }
  };

  return (
    <div className="infrastructure-dashboard p-6 bg-white dark:bg-gray-900 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            🔧 Infrastructure Intelligence
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real WHO/WHAT/WHERE/WHEN/WHY/HOW information about actual coding work
          </p>
        </div>

        {/* Category Filter */}
        <div className="mb-6 flex flex-wrap gap-2">
          {['all', 'build', 'error', 'dependency', 'performance', 'security', 'test'].map(category => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {category === 'all' ? '📊 All' : `${getCategoryIcon(category as any)} ${category}`}
            </button>
          ))}
        </div>

        {/* Real-Time Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          {['build', 'error', 'dependency', 'performance', 'security', 'test'].map(category => {
            const categoryEvents = events.filter(e => e.category === category);
            const critical = categoryEvents.filter(e => e.priority === 'critical').length;
            
            return (
              <div key={category} className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border">
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {getCategoryIcon(category as any)} {category}
                </div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {categoryEvents.length}
                </div>
                {critical > 0 && (
                  <div className="text-sm text-red-500 font-medium">
                    🔥 {critical} critical
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Events List */}
        <div className="space-y-3">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Recent Infrastructure Activity
          </h2>
          
          {filteredEvents.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No infrastructure events to display. System monitoring in progress...
            </div>
          ) : (
            filteredEvents.slice(0, 20).map((event, index) => (
              <div 
                key={index}
                className={`border rounded-lg p-4 ${getPriorityColor(event.priority)}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-semibold text-sm">
                    {getCategoryIcon(event.category)} {event.priority.toUpperCase()}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(event.when).toLocaleTimeString()}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
                  <div>
                    <div><strong>WHO:</strong> {event.who}</div>
                    <div><strong>WHAT:</strong> {event.what}</div>
                    <div><strong>WHERE:</strong> {event.where}</div>
                  </div>
                  <div>
                    <div><strong>WHY:</strong> {event.why}</div>
                    <div><strong>HOW:</strong> {event.how}</div>
                    {event.metadata && Object.keys(event.metadata).length > 0 && (
                      <div className="mt-2">
                        <strong>Details:</strong>
                        <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded mt-1 overflow-x-auto">
                          {JSON.stringify(event.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Actions */}
        <div className="mt-8 flex flex-wrap gap-4">
          <button
            onClick={() => {
              infrastructureIntelligence.monitorBuild(true, 1250);
              setEvents(prev => [...infrastructureIntelligence.getRecentEvents(50)]);
            }}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            🔨 Simulate Successful Build
          </button>
          
          <button
            onClick={() => {
              infrastructureIntelligence.monitorError(
                new Error('TypeError: Cannot read property of undefined'),
                'client/src/components/Dashboard.tsx:42'
              );
              setEvents(prev => [...infrastructureIntelligence.getRecentEvents(50)]);
            }}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            ❌ Simulate Error Detection
          </button>
          
          <button
            onClick={() => {
              infrastructureIntelligence.monitorApiCall('/api/colony', 'GET', 200, 85);
              setEvents(prev => [...infrastructureIntelligence.getRecentEvents(50)]);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            🌐 Simulate API Call
          </button>
          
          <button
            onClick={() => {
              infrastructureIntelligence.monitorTestRun('src/components/**/*.test.tsx', 12, 2, 3400);
              setEvents(prev => [...infrastructureIntelligence.getRecentEvents(50)]);
            }}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            🧪 Simulate Test Run
          </button>
        </div>
      </div>
    </div>
  );
}
