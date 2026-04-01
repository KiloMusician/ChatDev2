import React from 'react';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
}

export function Progress({ value, max = 100, className = '' }: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  return (
    <div className={`relative h-4 w-full overflow-hidden rounded-full bg-gray-200 ${className}`}>
      <div
        className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300 ease-out"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}