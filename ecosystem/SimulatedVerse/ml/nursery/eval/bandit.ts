// **EPSILON-GREEDY BANDIT** - For UI hint optimization and adaptive systems
export class EpsilonGreedy {
  private counts: number[];
  private rewards: number[];
  private totalRewards: number[];
  
  constructor(private k: number, private epsilon: number = 0.1) {
    this.counts = Array(k).fill(0);
    this.rewards = Array(k).fill(0);
    this.totalRewards = Array(k).fill(0);
  }
  
  // Select an arm (action)
  pick(): number {
    if (Math.random() < this.epsilon) {
      // Exploration: random choice
      return Math.floor(Math.random() * this.k);
    } else {
      // Exploitation: choose best arm
      const avgRewards = this.rewards.map((sum, i) => 
        this.counts[i] > 0 ? sum / this.counts[i] : 0
      );
      return avgRewards.indexOf(Math.max(...avgRewards));
    }
  }
  
  // Update arm with reward
  update(arm: number, reward: number): void {
    if (arm < 0 || arm >= this.k) {
      throw new Error(`Invalid arm ${arm}, must be 0-${this.k-1}`);
    }
    
    this.counts[arm]++;
    this.rewards[arm] += reward;
    this.totalRewards[arm] += reward;
  }
  
  // Get statistics
  getStats(): BanditStats {
    const avgRewards = this.rewards.map((sum, i) => 
      this.counts[i] > 0 ? sum / this.counts[i] : 0
    );
    
    const totalPulls = this.counts.reduce((a, b) => a + b, 0);
    const bestArm = avgRewards.indexOf(Math.max(...avgRewards));
    
    return {
      arms: this.k,
      totalPulls,
      counts: [...this.counts],
      averageRewards: avgRewards,
      bestArm,
      epsilon: this.epsilon,
      explorationRate: totalPulls > 0 ? this.counts.filter(c => c > 0).length / this.k : 0
    };
  }
  
  // Reset all data
  reset(): void {
    this.counts.fill(0);
    this.rewards.fill(0);
    this.totalRewards.fill(0);
  }
}

export interface BanditStats {
  arms: number;
  totalPulls: number;
  counts: number[];
  averageRewards: number[];
  bestArm: number;
  epsilon: number;
  explorationRate: number;
}

// **UPPER CONFIDENCE BOUND (UCB) BANDIT** - More sophisticated than epsilon-greedy
export class UCBBandit {
  private counts: number[];
  private rewards: number[];
  private totalPulls: number = 0;
  
  constructor(private k: number, private c: number = 2) {
    this.counts = Array(k).fill(0);
    this.rewards = Array(k).fill(0);
  }
  
  pick(): number {
    // If any arm hasn't been tried, try it
    for (let i = 0; i < this.k; i++) {
      if (this.counts[i] === 0) {
        return i;
      }
    }
    
    // Calculate UCB values
    const ucbValues = this.rewards.map((reward, i) => {
      const avgReward = reward / this.counts[i];
      const confidence = Math.sqrt((this.c * Math.log(this.totalPulls)) / this.counts[i]);
      return avgReward + confidence;
    });
    
    return ucbValues.indexOf(Math.max(...ucbValues));
  }
  
  update(arm: number, reward: number): void {
    if (arm < 0 || arm >= this.k) {
      throw new Error(`Invalid arm ${arm}, must be 0-${this.k-1}`);
    }
    
    this.counts[arm]++;
    this.rewards[arm] += reward;
    this.totalPulls++;
  }
  
  getStats(): BanditStats {
    const avgRewards = this.rewards.map((sum, i) => 
      this.counts[i] > 0 ? sum / this.counts[i] : 0
    );
    
    const bestArm = avgRewards.indexOf(Math.max(...avgRewards));
    
    return {
      arms: this.k,
      totalPulls: this.totalPulls,
      counts: [...this.counts],
      averageRewards: avgRewards,
      bestArm,
      epsilon: 0, // UCB doesn't use epsilon
      explorationRate: this.totalPulls > 0 ? this.counts.filter(c => c > 0).length / this.k : 0
    };
  }
  
  reset(): void {
    this.counts.fill(0);
    this.rewards.fill(0);
    this.totalPulls = 0;
  }
}

// **HINT OPTIMIZATION** - Use bandit to optimize which hints to show
export interface HintArm {
  id: string;
  title: string;
  category: string;
}

export class HintOptimizer {
  private bandit: EpsilonGreedy;
  private arms: HintArm[];
  
  constructor(hints: HintArm[], epsilon = 0.15) {
    this.arms = hints;
    this.bandit = new EpsilonGreedy(hints.length, epsilon);
  }
  
  selectHint(): HintArm {
    const armIndex = this.bandit.pick();
    return this.arms[armIndex];
  }
  
  recordOutcome(hintId: string, userFollowed: boolean): void {
    const armIndex = this.arms.findIndex(arm => arm.id === hintId);
    if (armIndex >= 0) {
      const reward = userFollowed ? 1 : 0;
      this.bandit.update(armIndex, reward);
    }
  }
  
  getBestHints(count = 3): HintArm[] {
    const stats = this.bandit.getStats();
    const indexed = this.arms.map((arm, i) => ({
      arm,
      avgReward: stats.averageRewards[i],
      count: stats.counts[i]
    }));
    
    // Sort by average reward, then by count as tiebreaker
    indexed.sort((a, b) => {
      if (Math.abs(a.avgReward - b.avgReward) < 0.01) {
        return b.count - a.count;
      }
      return b.avgReward - a.avgReward;
    });
    
    return indexed.slice(0, count).map(item => item.arm);
  }
  
  getOptimizationStats(): BanditStats & { arms: HintArm[] } {
    return {
      ...this.bandit.getStats(),
      arms: this.arms
    };
  }
}