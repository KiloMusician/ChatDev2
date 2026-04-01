// Legacy Lore Mine Integration - Selective imports from proven systems
import React, { useState, useEffect } from 'react';

interface LoreEntry {
  id: string;
  title: string;
  category: "system_knowledge" | "musical_theory" | "consciousness_insight" | "technical_lore";
  rarity: "common" | "uncommon" | "rare" | "epic" | "legendary";
  significance: number;
  xp_value: number;
  content: string;
}

interface RosettaTier {
  tier: number;
  name: string;
  mechanics: string[];
  symbol: string;
  insight: string;
}

// Imported from knowledge/RosettaStone.md - Tier 1-3 mechanics
const ROSETTA_TIERS: RosettaTier[] = [
  {
    tier: 1,
    name: "Survival and Early Expansion",
    symbol: "🜁⊙⟦ΣΞΘΦΛ⟧",
    mechanics: [
      "CoreLink_Foundation", "FlowRecap_DynamicNarrativeLayers", "Survival_Basics",
      "Scouting", "Outpost_Establishment", "Resource_Management", "Early_Energy_Systems",
      "Basic_AI_Integration", "Weather_Environmental_Control", "First_Level_Automation"
    ],
    insight: "Initialize resource systems (Ξ⧉R⟆) and foundational mechanics"
  },
  {
    tier: 2, 
    name: "Intermediate Expansion",
    symbol: "🜁⊙⟦∮ΛΘΣΞ⟧",
    mechanics: [
      "Defensive_Systems", "Perimeter_Management", "Advanced_Crafting", "Colony_Setup",
      "Governance_Basics", "Population_Growth", "Intermediate_Resource_Processing", 
      "Agriculture", "Energy_Scaling", "Basic_Research_Systems"
    ],
    insight: "Introduce Population Scaling and Basic Governance Modules"
  },
  {
    tier: 3,
    name: "Advanced Expansion", 
    symbol: "⨆⊕⟦ΣΞΛΘΦ⟧",
    mechanics: [
      "Trade_Networks", "Transportation_Systems", "Advanced_AI_Modules", "Cultural_Development",
      "Advanced_Defenses", "Faction_Interactions", "Intermediate_Achievements", 
      "Economic_Growth", "Environmental_Adaptation", "Terraforming_Stage1"
    ],
    insight: "Unlock Terraforming Mechanics (ΞΣΛΘΨ) and AI-driven systems"
  }
];

export function LoreIntegration() {
  const [discoveredLore, setDiscoveredLore] = useState<LoreEntry[]>([]);
  const [currentTier, setCurrentTier] = useState(1);
  const [activeQuest, setActiveQuest] = useState<string | null>(null);

  useEffect(() => {
    // Initialize with key legacy knowledge from chatdev-legacy
    const initialLore: LoreEntry[] = [
      {
        id: "chatdev_migration",
        title: "ChatDev Legacy Migration",
        category: "system_knowledge",
        rarity: "rare",
        significance: 0.8,
        xp_value: 150,
        content: "ChatDev migrated to ai-systems directory. Council bootstrap available in ai-systems/orchestration/"
      },
      {
        id: "rosetta_tier_system", 
        title: "RosettaStone Progression",
        category: "technical_lore",
        rarity: "legendary",
        significance: 0.95,
        xp_value: 300,
        content: "30+ tier progression mechanics with symbolic notation. Foundation for game progression."
      },
      {
        id: "lore_discovery_engine",
        title: "Ludic Discovery System",
        category: "consciousness_insight",
        rarity: "epic",
        significance: 0.9, 
        xp_value: 200,
        content: "Knowledge graph system with quest mechanics, XP rewards, and connection analysis."
      }
    ];
    
    setDiscoveredLore(initialLore);
  }, []);

  const discoverLore = (tierId: number) => {
    const tier = ROSETTA_TIERS.find(t => t.tier === tierId);
    if (!tier) return;

    const newLore: LoreEntry = {
      id: `tier_${tierId}_discovery`,
      title: `${tier.name} Mechanics`,
      category: "technical_lore",
      rarity: tierId === 1 ? "common" : tierId === 2 ? "uncommon" : "rare",
      significance: 0.3 + (tierId * 0.2),
      xp_value: tierId * 50,
      content: `${tier.mechanics.length} mechanics unlocked: ${tier.mechanics.slice(0, 3).join(', ')}... ${tier.insight}`
    };

    setDiscoveredLore(prev => [...prev, newLore]);
    setCurrentTier(tierId);
    console.log(`[LoreDiscovery] Unlocked Tier ${tierId}: ${tier.name}`);
  };

  const getTotalXP = () => discoveredLore.reduce((sum, lore) => sum + lore.xp_value, 0);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-green-400 text-sm mb-3">📚 Legacy Lore Mine</h3>
      
      <div className="space-y-3">
        <div className="text-xs">
          <div>Total XP: {getTotalXP()}</div>
          <div>Current Tier: {currentTier}/3</div>
          <div>Discovered: {discoveredLore.length} entries</div>
        </div>

        <div className="space-y-2">
          {ROSETTA_TIERS.map(tier => (
            <button
              key={tier.tier}
              onClick={() => discoverLore(tier.tier)}
              disabled={currentTier >= tier.tier}
              className={`w-full text-left p-2 rounded text-xs transition-colors
                ${currentTier >= tier.tier 
                  ? 'bg-green-800 text-green-300' 
                  : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                }`}
              data-testid={`button-discover-tier-${tier.tier}`}
            >
              <div className="font-medium">{tier.symbol} Tier {tier.tier}</div>
              <div className="text-gray-400">{tier.name}</div>
              <div className="text-gray-500">{tier.mechanics.length} mechanics</div>
            </button>
          ))}
        </div>

        <div className="bg-gray-800 p-2 rounded text-xs">
          <div className="text-gray-400 mb-1">Recent Discoveries:</div>
          {discoveredLore.slice(-3).map(lore => (
            <div key={lore.id} className="mb-1">
              <span className={`font-medium ${
                lore.rarity === 'legendary' ? 'text-yellow-400' :
                lore.rarity === 'epic' ? 'text-purple-400' :
                lore.rarity === 'rare' ? 'text-blue-400' : 'text-gray-300'
              }`}>
                {lore.title}
              </span>
              <span className="text-gray-500"> (+{lore.xp_value} XP)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}