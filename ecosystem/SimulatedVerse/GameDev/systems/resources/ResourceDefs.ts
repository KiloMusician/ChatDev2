/**
 * Resource definitions and cost calculation system for Culture-Ship
 */

import { z } from "zod";

export const ResourceId = z.enum([
  "SCRAP", "ENERGY", "FOOD", "WATER", "ORE", "SILICON",
  "CIRCUITS", "NANOBOTS", "DATA", "CULTURE", "CREDITS"
]);
export type ResourceId = z.infer<typeof ResourceId>;

export type Cost = { r: ResourceId; amount: number };
export type CostVector = Cost[];

export type CurveKind =
  | "linear" | "exp" | "exp_softcap" | "poly" | "logistic"
  | "factorio_like" | "diminishing" | "stepped" | "quadratic";

export interface PriceCurve {
  kind: CurveKind;
  k?: number;          // growth multiplier
  b?: number;          // base value
  cap?: number;        // softcap limit
  exp?: number;        // exponent for polynomial
  step?: number;       // step size for stepped curves
}

export interface Pricer {
  base: CostVector;          // base costs
  curve: PriceCurve;         // scaling curve
  multiCurrency?: boolean;   // multi-resource gate
  previewDepth?: number;     // default hover preview levels (e.g. 5)
}

// Default resource starting values
export const STARTING_RESOURCES: Record<ResourceId, number> = {
  SCRAP: 10,
  ENERGY: 5,
  FOOD: 3,
  WATER: 2,
  ORE: 0,
  SILICON: 0,
  CIRCUITS: 0,
  NANOBOTS: 0,
  DATA: 1,
  CULTURE: 0,
  CREDITS: 0
};

// Resource display metadata
export const RESOURCE_META: Record<ResourceId, { icon: string; color: string; desc: string }> = {
  SCRAP: { icon: "🔩", color: "text-gray-400", desc: "Salvaged materials from the wreckage" },
  ENERGY: { icon: "⚡", color: "text-yellow-400", desc: "Power to run ship systems" },
  FOOD: { icon: "🌾", color: "text-green-400", desc: "Sustenance for biological crew" },
  WATER: { icon: "💧", color: "text-blue-400", desc: "Essential for life support" },
  ORE: { icon: "⛏️", color: "text-orange-400", desc: "Raw materials for construction" },
  SILICON: { icon: "💎", color: "text-purple-400", desc: "Electronics and computing substrate" },
  CIRCUITS: { icon: "🔌", color: "text-cyan-400", desc: "Manufactured electronic components" },
  NANOBOTS: { icon: "🤖", color: "text-emerald-400", desc: "Self-replicating construction units" },
  DATA: { icon: "💾", color: "text-indigo-400", desc: "Information and computational resources" },
  CULTURE: { icon: "🎭", color: "text-pink-400", desc: "Social cohesion and creativity" },
  CREDITS: { icon: "💰", color: "text-amber-400", desc: "Universal exchange medium" }
};