import React from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import TripartiteMonitor from '@/components/TripartiteMonitor';

function OpsCenterWrapped() {
  return (
    <div className="min-h-screen p-6 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            🏛️ CognitoWeave Operations Center
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Tripartite Architecture Monitoring Dashboard
          </p>
        </div>
        <TripartiteMonitor />
      </div>
    </div>
  );
}

export default function OpsCenter() {
  return (
    <ErrorBoundary>
      <OpsCenterWrapped />
    </ErrorBoundary>
  );
}