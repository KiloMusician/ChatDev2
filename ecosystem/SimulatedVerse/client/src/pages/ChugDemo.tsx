// client/src/pages/ChugDemo.tsx
// Demo page showing the chug system fixing m.map errors
import React, { useState, useEffect } from 'react';
import { SafeList } from '@/components/SafeList';
import { safeMap, safePct, safeNum } from '@/lib/guardedOps';

interface ChugStatus {
  ok: boolean;
  issues: string[];
  last_check: string;
}

export default function ChugDemo() {
  const [chugStatus, setChugStatus] = useState<ChugStatus | null>(null);
  const [exampleData, setExampleData] = useState<any[]>([]);

  // Fetch chug system status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/ops-report/status.json');
        if (response.ok) {
          const data = await response.json();
          setChugStatus(data);
        }
      } catch (error) {
        console.log('Chug status not ready yet');
      }
    };

    fetchStatus();
    // DISABLED: 5-second interval may be triggering fake agent theater
    // const interval = setInterval(fetchStatus, 5000);
    // return () => clearInterval(interval);
  }, []);

  // Example data that could break with .map() but is safe with safeMap()
  useEffect(() => {
    setExampleData([
      { id: 1, name: 'TypeScript Check', status: 'running' },
      { id: 2, name: 'ESLint Scan', status: 'completed' },
      { id: 3, name: 'Map Footgun Detection', status: 'warning' },
      null, // This would break .map() but safeMap() handles it
      undefined, // This would break .map() but safeMap() handles it
      { id: 4, name: 'Duplicate Sentry', status: 'active' }
    ]);
  }, []);

  return (
    <div className="min-h-screen p-6 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
          🚀 Chug Mode Demo - Relentless Error Hunting
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Chug System Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              System Status
            </h2>
            
            {chugStatus ? (
              <div className="space-y-3">
                <div className={`p-3 rounded-lg ${chugStatus.ok ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'}`}>
                  <div className={`font-medium ${chugStatus.ok ? 'text-green-800 dark:text-green-100' : 'text-red-800 dark:text-red-100'}`}>
                    {chugStatus.ok ? '✅ All Checks Passing' : '⚠️ Issues Detected'}
                  </div>
                </div>
                
                {chugStatus.issues.length > 0 && (
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Issues:</div>
                    {safeMap(chugStatus.issues, (issue, i) => (
                      <div key={i} className="text-sm text-red-600 dark:text-red-400">
                        • {issue}
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Last check: {new Date(chugStatus.last_check).toLocaleTimeString()}
                </div>
              </div>
            ) : (
              <div className="text-gray-500 dark:text-gray-400">
                📡 Connecting to chug system...
              </div>
            )}
          </div>

          {/* Safe Operations Demo */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Safe Operations Demo
            </h2>
            
            <div className="space-y-4">
              <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Progress: {safePct(0.73)}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Fixed: {safeNum(15, ' issues')}
                </div>
              </div>
              
              <div className="text-sm text-gray-600 dark:text-gray-400">
                ✅ Using safeMap() instead of .map()<br/>
                ✅ Using safePct() for safe percentages<br/>
                ✅ Using safeNum() for safe numbers
              </div>
            </div>
          </div>
        </div>

        {/* Safe List Demo */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            SafeList Demo - No More m.map Errors
          </h2>
          
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            This list includes null and undefined values that would crash .map() but SafeList handles them gracefully:
          </div>

          <SafeList
            data={exampleData}
            render={(item, i) => (
              <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                {item ? (
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {item.name || 'Unnamed'}
                    </div>
                    <div className={`text-sm ${
                      item.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                      item.status === 'warning' ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-blue-600 dark:text-blue-400'
                    }`}>
                      Status: {item.status || 'unknown'}
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500 dark:text-gray-400 italic">
                    Null/undefined data (handled safely)
                  </div>
                )}
              </div>
            )}
          />
        </div>

        {/* Chug Principles */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            🎯 Chug Mode Principles
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">Error Hunting</h3>
              <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                <li>• TypeScript errors (highest priority)</li>
                <li>• ESLint warnings</li>
                <li>• .map() footguns (m.map errors)</li>
                <li>• Routing issues</li>
                <li>• Consciousness cycling</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">No Deletions Policy</h3>
              <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                <li>• Smart aliasing for duplicates</li>
                <li>• Annealing existing code</li>
                <li>• Feature flags for compatibility</li>
                <li>• Preserve all work history</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}