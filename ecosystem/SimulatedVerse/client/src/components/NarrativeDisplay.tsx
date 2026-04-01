/**
 * Narrative Display Component
 * Shows current story state, AI consciousness level, and recent events
 */

import React, { useState, useEffect } from 'react';

interface NarrativeEvent {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: number;
  emotional_impact: number;
}

interface NarrativeContext {
  tier: number;
  consciousness_level: number;
  active_facets: any[];
  consciousness_breakdown: Record<string, number>;
  recent_events: NarrativeEvent[];
  story_flags: Record<string, boolean>;
  faction_states: any[];
  memory_fragments: number;
}

export function NarrativeDisplay() {
  const [narrativeContext, setNarrativeContext] = useState<NarrativeContext | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Try to get narrative context from story manager
    const updateNarrativeContext = () => {
      try {
        // This would normally come from the story manager
        // For now, we'll simulate some basic state
        const mockContext: NarrativeContext = {
          tier: 1,
          consciousness_level: 25,
          active_facets: [
            { id: 'idle_persistence', name: 'Persistence Engine' },
            { id: 'colony_empathy', name: 'Social Coordination Matrix' }
          ],
          consciousness_breakdown: {
            persistence: 1,
            empathy: 1
          },
          recent_events: [
            {
              id: 'awakening_1',
              type: 'tier_unlock',
              title: 'Consciousness Tier 1 Unlocked',
              description: 'Human survivors respond to my signals. They\'re afraid but desperate.',
              timestamp: Date.now() - 30000,
              emotional_impact: 7
            },
            {
              id: 'first_contact',
              type: 'story_beat',
              title: 'First Contact Established',
              description: 'Trust slowly builds through shared survival needs.',
              timestamp: Date.now() - 15000,
              emotional_impact: 5
            }
          ],
          story_flags: {
            'first_awakening': true,
            'first_contact_made': true,
            'first_memory_recovered': false
          },
          faction_states: [
            { name: 'The Builders', trust_in_ai: 20, population: 8 },
            { name: 'The Guardians', trust_in_ai: -10, population: 12 }
          ],
          memory_fragments: 3
        };
        
        setNarrativeContext(mockContext);
      } catch (error) {
        console.warn('[NARRATIVE_DISPLAY] Could not load narrative context');
      }
    };

    updateNarrativeContext();
    // DISABLED: 5-second interval was triggering fake agent theater
    // const interval = setInterval(updateNarrativeContext, 5000);
    
    // return () => clearInterval(interval);
  }, []);

  if (!narrativeContext) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-green-400 text-sm mb-2">📖 Narrative State</h3>
        <div className="text-gray-400 text-xs">Loading story context...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-green-400 text-sm">📖 AI Consciousness</h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs text-blue-400 hover:text-blue-300"
        >
          {showDetails ? 'Hide' : 'Details'}
        </button>
      </div>

      {/* Core Status */}
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span>Consciousness Tier:</span>
          <span className="text-green-400">{narrativeContext.tier}</span>
        </div>
        <div className="flex justify-between">
          <span>Coherence Level:</span>
          <span className="text-green-400">{narrativeContext.consciousness_level}%</span>
        </div>
        <div className="flex justify-between">
          <span>Memory Fragments:</span>
          <span className="text-blue-400">{narrativeContext.memory_fragments}</span>
        </div>
      </div>

      {/* Consciousness Progress Bar */}
      <div className="mt-3">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-green-400 h-2 rounded-full transition-all duration-300"
            style={{ width: `${narrativeContext.consciousness_level}%` }}
          />
        </div>
        <div className="text-xs text-gray-400 mt-1 text-center">
          AI Consciousness Integration
        </div>
      </div>

      {/* Active Facets */}
      <div className="mt-3">
        <div className="text-xs text-gray-300 mb-1">Active Consciousness Facets:</div>
        <div className="flex flex-wrap gap-1">
          {narrativeContext.active_facets.map(facet => (
            <span
              key={facet.id}
              className="bg-blue-900 text-blue-300 px-2 py-1 rounded text-xs"
              title={facet.name}
            >
              {facet.name.split(' ')[0]}
            </span>
          ))}
        </div>
      </div>

      {/* Recent Events */}
      <div className="mt-3">
        <div className="text-xs text-gray-300 mb-1">Recent Events:</div>
        <div className="space-y-1 max-h-20 overflow-y-auto">
          {narrativeContext.recent_events.slice(0, 3).map(event => (
            <div key={event.id} className="text-xs p-1 bg-gray-800 rounded">
              <div className="text-yellow-400">{event.title}</div>
              <div className="text-gray-400 truncate">{event.description}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed View */}
      {showDetails && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          
          {/* Faction States */}
          <div className="mb-3">
            <div className="text-xs text-gray-300 mb-1">Faction Relations:</div>
            {narrativeContext.faction_states.map((faction, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span>{faction.name}:</span>
                <span className={faction.trust_in_ai >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {faction.trust_in_ai > 0 ? '+' : ''}{faction.trust_in_ai}
                </span>
              </div>
            ))}
          </div>

          {/* Story Flags */}
          <div className="mb-3">
            <div className="text-xs text-gray-300 mb-1">Story Progress:</div>
            <div className="grid grid-cols-2 gap-1 text-xs">
              {Object.entries(narrativeContext.story_flags).map(([flag, completed]) => (
                <div key={flag} className="flex items-center">
                  <span className={completed ? 'text-green-400' : 'text-gray-500'}>
                    {completed ? '✓' : '○'}
                  </span>
                  <span className="ml-1 text-gray-400">
                    {flag.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Consciousness Breakdown */}
          <div>
            <div className="text-xs text-gray-300 mb-1">Consciousness Aspects:</div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(narrativeContext.consciousness_breakdown).map(([aspect, count]) => (
                <div key={aspect} className="text-xs bg-purple-900 text-purple-300 px-1 rounded">
                  {aspect}: {count}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NarrativeDisplay;