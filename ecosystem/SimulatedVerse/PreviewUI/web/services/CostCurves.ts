/**
 * Cost calculation and affordability system for Culture-Ship upgrades
 */

import { Pricer, CostVector, PriceCurve } from "../../../GameDev/systems/resources/ResourceDefs";
import { PlayerState } from "../core/store";

export function calculateCostForLevel(pricer: Pricer, level: number): CostVector {
  const { base, curve } = pricer;
  
  return base.map(({ r, amount }) => ({
    r, 
    amount: Math.floor(amount * calculateMultiplier(curve, level))
  }));
}

function calculateMultiplier(curve: PriceCurve, level: number): number {
  const { kind, k = 1.15, b = 1, cap, exp = 2, step = 1 } = curve;
  
  switch (kind) {
    case "linear":
      return b + (k * level);
      
    case "exp":
      return b * Math.pow(k, level);
      
    case "exp_softcap":
      const expValue = b * Math.pow(k, level);
      return cap ? Math.min(expValue, cap + Math.log(expValue - cap + 1)) : expValue;
      
    case "poly":
      return b * Math.pow(level + 1, exp);
      
    case "quadratic":
      return b + (k * level * level);
      
    case "logistic":
      return cap ? cap / (1 + Math.exp(-k * (level - (cap / 2)))) : b * Math.pow(k, level);
      
    case "stepped":
      return b * Math.pow(k, Math.floor(level / (step || 1)));
      
    case "diminishing":
      return b * (k + Math.log(level + 1));
      
    case "factorio_like":
      // Complex curve similar to Factorio's science scaling
      const base_multiplier = Math.pow(k, level);
      const complexity_factor = 1 + (level * 0.1);
      return b * base_multiplier * complexity_factor;
      
    default:
      return b * Math.pow(k, level);
  }
}

export function canAffordCost(player: PlayerState, cost: CostVector): boolean {
  return cost.every(({ r, amount }) => (player.inv[r] || 0) >= amount);
}

export function previewNextNCosts(pricer: Pricer, startLevel: number, n = 5): Array<{ level: number; cost: CostVector; affordable?: boolean }> {
  const previews: Array<{ level: number; cost: CostVector }> = [];
  
  for (let i = 1; i <= n; i++) {
    const level = startLevel + i;
    const cost = calculateCostForLevel(pricer, level);
    previews.push({ level, cost });
  }
  
  return previews;
}

export function calculateBatchCost(pricer: Pricer, startLevel: number, amount: number): CostVector {
  let totalCosts: Record<string, number> = {};
  
  for (let i = 0; i < amount; i++) {
    const levelCost = calculateCostForLevel(pricer, startLevel + i);
    levelCost.forEach(({ r, amount: costAmount }) => {
      totalCosts[r] = (totalCosts[r] || 0) + costAmount;
    });
  }
  
  return Object.entries(totalCosts).map(([r, amount]) => ({
    r: r as any,
    amount
  }));
}

export function findMaxAffordable(player: PlayerState, pricer: Pricer, startLevel: number, maxTries = 100): number {
  let maxAffordable = 0;
  
  for (let amount = 1; amount <= maxTries; amount++) {
    const batchCost = calculateBatchCost(pricer, startLevel, amount);
    if (canAffordCost(player, batchCost)) {
      maxAffordable = amount;
    } else {
      break;
    }
  }
  
  return maxAffordable;
}

// Quick cost formatting for UI display
export function formatCost(cost: CostVector): string {
  return cost.map(({ r, amount }) => `${amount} ${r}`).join(", ");
}

export function formatCostWithColors(cost: CostVector, affordable: boolean): Array<{ text: string; color: string }> {
  return cost.map(({ r, amount }) => ({
    text: `${amount} ${r}`,
    color: affordable ? "text-emerald-400" : "text-rose-400"
  }));
}