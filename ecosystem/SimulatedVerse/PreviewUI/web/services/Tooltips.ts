/**
 * Tooltip generation service for Culture-Ship upgrades
 */

import { UpgradeDef } from "../../../GameDev/gameplay/progression/Upgrades";
import { RESOURCE_META } from "../../../GameDev/systems/resources/ResourceDefs";
import { PlayerState } from "../core/store";
import { calculateCostForLevel, previewNextNCosts, canAffordCost, formatCost } from "./CostCurves";

export interface TooltipData {
  header: string;
  body: string;
  nextCost: Array<{ r: string; amount: number }>;
  preview: Array<{ level: number; cost: Array<{ r: string; amount: number }>; affordable: boolean }>;
  canAfford: boolean;
  resourceDetails: Array<{ icon: string; color: string; desc: string }>;
  currentLevel: number;
  maxLevel?: number;
}

export function generateUpgradeTooltip(
  upgrade: UpgradeDef, 
  player: PlayerState,
  previewDepth?: number
): TooltipData {
  const currentLevel = player.upgrades[upgrade.id] || 0;
  const nextLevel = currentLevel + 1;
  const nextCost = calculateCostForLevel(upgrade.pricer, nextLevel);
  const depth = previewDepth || upgrade.pricer.previewDepth || 5;
  
  const preview = previewNextNCosts(upgrade.pricer, currentLevel, depth).map(({ level, cost }) => ({
    level,
    cost,
    affordable: canAffordCost(player, cost)
  }));
  
  const resourceDetails = nextCost.map(({ r }) => ({
    icon: RESOURCE_META[r as keyof typeof RESOURCE_META]?.icon || "📦",
    color: RESOURCE_META[r as keyof typeof RESOURCE_META]?.color || "text-gray-400",
    desc: RESOURCE_META[r as keyof typeof RESOURCE_META]?.desc || "Unknown resource"
  }));
  
  return {
    header: `${upgrade.title} [Lv.${currentLevel}]`,
    body: upgrade.desc,
    nextCost,
    preview,
    canAfford: canAffordCost(player, nextCost),
    resourceDetails,
    currentLevel,
    maxLevel: upgrade.pricer.curve.cap ? Math.floor(upgrade.pricer.curve.cap) : undefined
  };
}

export function generateResourceTooltip(resourceId: string, amount: number) {
  const meta = RESOURCE_META[resourceId as keyof typeof RESOURCE_META];
  if (!meta) return null;
  
  return {
    header: `${meta.icon} ${resourceId}`,
    body: meta.desc,
    amount: amount,
    color: meta.color
  };
}

export function generateFlagTooltip(flagName: string, enabled: boolean) {
  const flagDescriptions: Record<string, string> = {
    UI_TIPS: "Shows detailed tooltips on hover",
    UI_COST_PREVIEW: "Preview next 5 upgrade costs",
    UI_BATCH_BUY: "Enable bulk purchase options",
    UI_HOTKEYS: "Keyboard shortcuts for quick actions",
    UI_THEME_HOLOGRAPHIC: "Holographic visual theme",
    UI_TERMINAL_INTERACTIVE: "Interactive command terminal",
    UI_NODEWEAVE: "Node graph interface for logistics",
    UI_SYNTHBAY: "Synthesis and modulation controls",
    SYS_NANOBOT_FOUNDRY: "Automated construction capabilities",
    SYS_AUTOTICKS: "Passive resource generation",
    LORE_CHANNEL_2: "Access to deep lore archives"
  };
  
  return {
    header: `${enabled ? "✅" : "❌"} ${flagName}`,
    body: flagDescriptions[flagName] || "Unknown system flag",
    enabled
  };
}