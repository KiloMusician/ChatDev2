// Deterministic RNG - Splitmix32/Xoroshiro128** for campaign seeding
// Bridges symbolic randomness to literal deterministic outcomes

export class SeededRNG {
  private state: number;
  private a: number = 0;
  private b: number = 0;
  private c: number = 0;
  private d: number = 0;

  constructor(seed: number | string) {
    // Convert string seed to numeric
    if (typeof seed === 'string') {
      seed = this.hashString(seed);
    }
    
    this.state = seed >>> 0; // Ensure 32-bit unsigned
    this.initXoroshiro();
    console.log(`[RNG] Seeded with: ${this.state}`);
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private initXoroshiro(): void {
    // Use splitmix32 to initialize xoroshiro128** state
    this.a = this.splitmix32();
    this.b = this.splitmix32();
    this.c = this.splitmix32();
    this.d = this.splitmix32();
  }

  private splitmix32(): number {
    let z = this.state += 0x9e3779b9;
    z = Math.imul(z ^ z >>> 16, 0x21f0aaad);
    z = Math.imul(z ^ z >>> 15, 0x735a2d97);
    return (z ^ z >>> 15) >>> 0;
  }

  private rotl(x: number, k: number): number {
    return (x << k) | (x >>> (32 - k));
  }

  // Core xoroshiro128** implementation
  next(): number {
    const result = Math.imul(this.rotl(Math.imul(this.a, 5), 7), 9) >>> 0;
    const t = this.b << 9;

    this.c ^= this.a;
    this.d ^= this.b;
    this.b ^= this.c;
    this.a ^= this.d;

    this.c ^= t;
    this.d = this.rotl(this.d, 11);

    return result;
  }

  // Utility methods for game development
  random(): number {
    return this.next() / 0x100000000; // Convert to [0,1)
  }

  int(min: number, max: number): number {
    return Math.floor(this.random() * (max - min + 1)) + min;
  }

  choice<T>(array: T[]): T {
    return array[this.int(0, array.length - 1)];
  }

  shuffle<T>(array: T[]): T[] {
    const result = [...array];
    for (let i = result.length - 1; i > 0; i--) {
      const j = this.int(0, i);
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }

  // Weighted selection for loot tables
  weightedChoice<T>(items: Array<{item: T, weight: number}>): T {
    const totalWeight = items.reduce((sum, item) => sum + item.weight, 0);
    let random = this.random() * totalWeight;
    
    for (const {item, weight} of items) {
      random -= weight;
      if (random <= 0) return item;
    }
    
    return items[items.length - 1].item; // Fallback
  }

  // Branch for different RNG contexts (dungeon gen, combat, loot)
  branch(label: string): SeededRNG {
    const branchSeed = this.hashString(`${this.state}_${label}`);
    return new SeededRNG(branchSeed);
  }

  // Get current state for save/restore
  getState(): number[] {
    return [this.a, this.b, this.c, this.d];
  }

  setState(state: number[]): void {
    [this.a, this.b, this.c, this.d] = state;
  }
}

// Global campaign RNG (seeded by campaign_id + planet_seed)
export let campaignRNG: SeededRNG;

export function initCampaignRNG(campaignId: string, planetSeed: number = 1337): void {
  const combinedSeed = `${campaignId}_${planetSeed}`;
  campaignRNG = new SeededRNG(combinedSeed);
  console.log(`[RNG] Campaign initialized with seed: ${combinedSeed}`);
}

// Initialize with default seed
initCampaignRNG('default_campaign', 1337);
