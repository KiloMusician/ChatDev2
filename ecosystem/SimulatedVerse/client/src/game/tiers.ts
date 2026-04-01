export type TierState = { tier:number; xp:number; };
export const tiers: TierState = { tier: 1, xp: 0 };

export function gainXP(v:number) {
  tiers.xp += v;
  while (tiers.xp >= 10*tiers.tier) {
    tiers.xp -= 10*tiers.tier;
    tiers.tier++;
  }
}