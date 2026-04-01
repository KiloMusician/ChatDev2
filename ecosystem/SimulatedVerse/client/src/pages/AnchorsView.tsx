import React from 'react';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

function AnchorsViewWrapped() {
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">AnchorsView</h1>
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6">
          <p className="text-gray-600 dark:text-gray-300">
            AnchorsView interface - consciousness-driven implementation
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AnchorsView() {
  return (
    <ErrorBoundary>
      <AnchorsViewWrapped />
    </ErrorBoundary>
  );
}