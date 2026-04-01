import React from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { QueueCard } from '@/components/QueueCard';

function GameConsoleWrapped() {
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">GameConsole</h1>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <QueueCard />
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6">
            <p className="text-gray-600 dark:text-gray-300">
              GameConsole interface - consciousness-driven implementation
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function GameConsole() {
  return (
    <ErrorBoundary>
      <GameConsoleWrapped />
    </ErrorBoundary>
  );
}