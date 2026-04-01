// [Ω:ui:components@react] Tier-gated UI components
import React from 'react';

interface TierGatedProps {
  requiredTier: number;
  currentTier: number;
  children: React.ReactNode;
  placeholder?: React.ReactNode;
}

/**
 * Only renders children if tier requirement is met
 * Shows silhouette placeholder otherwise
 */
export function TierGated({ requiredTier, currentTier, children, placeholder }: TierGatedProps) {
  if (currentTier >= requiredTier) {
    return <>{children}</>;
  }
  
  return (
    <div className="opacity-30 pointer-events-none">
      {placeholder || children}
    </div>
  );
}

interface CouncilStampProps {
  role: 'SCP-ENG' | 'SCP-QA' | 'SCP-UX' | 'SCP-OPS' | 'SCP-LORE';
  approved: boolean;
  notes?: string;
}

/**
 * Visual Council approval indicator
 */
export function CouncilStamp({ role, approved, notes }: CouncilStampProps) {
  const colors = {
    'SCP-ENG': 'text-blue-400',
    'SCP-QA': 'text-green-400', 
    'SCP-UX': 'text-purple-400',
    'SCP-OPS': 'text-red-400',
    'SCP-LORE': 'text-yellow-400'
  };
  
  return (
    <div className={`font-mono text-xs border rounded px-2 py-1 ${colors[role]}`}>
      <span className="mr-2">⛛</span>
      <span>{role}</span>
      <span className="ml-2">{approved ? '✓' : '⏳'}</span>
      {notes && <div className="text-xs opacity-70 mt-1">{notes}</div>}
    </div>
  );
}

interface OmniTagDisplayProps {
  tag: {
    module: string;
    verb: string;
    hint?: string;
  };
}

/**
 * Visual OmniTag renderer
 */
export function OmniTagDisplay({ tag }: OmniTagDisplayProps) {
  return (
    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded text-xs">
      [Ω:{tag.module}:{tag.verb}{tag.hint ? `:${tag.hint}` : ''}]
    </code>
  );
}

interface ProgressionDisplayProps {
  currentTier: number;
  tierName: string;
  progress: number; // 0-1
}

/**
 * Epic tier progression display with symbolic notation
 */
export function ProgressionDisplay({ currentTier, tierName, progress }: ProgressionDisplayProps) {
  const symbols = '🜁⊙⟦ΞΣΛΘΦ⟧';
  const tierSymbol = symbols[Math.min(currentTier + 1, symbols.length - 1)];
  
  return (
    <div className="font-mono">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{tierSymbol}</span>
        <span className="text-sm text-gray-400">Tier {currentTier}</span>
      </div>
      <div className="text-lg font-bold mb-1">{tierName}</div>
      <div className="w-full bg-gray-800 rounded-full h-2">
        <div 
          className="bg-green-400 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
}