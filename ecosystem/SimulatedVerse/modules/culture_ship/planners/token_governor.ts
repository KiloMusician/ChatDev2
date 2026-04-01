/**
 * 💰 TOKEN GOVERNOR - Culture-Ship Budget Management
 * Zero-token budget enforcement with local-first policies
 */

interface TokenPolicy {
  default_mode: "off" | "local" | "hybrid";
  max_budget: number;
  soft_limit: number;
  hard_limit: number;
  recovery_rate: number;
  escalation_threshold: number;
}

interface TokenStep {
  kind: string;
  title: string;
  cost?: number;
  benefit?: number;
  local_alternative?: boolean;
}

class TokenGovernor {
  private policy: TokenPolicy = {
    default_mode: "off",
    max_budget: 100,
    soft_limit: 70,
    hard_limit: 90,
    recovery_rate: 10,
    escalation_threshold: 5
  };
  
  private currentUsage = 0;
  private lastRecovery = Date.now();

  async init(policyPath: string): Promise<void> {
    console.log("💰 Culture-Ship Token Governor: Initializing budget management...");
    
    try {
      // Try to load policy file (if exists)
      const fs = await import("node:fs");
      if (fs.existsSync(policyPath)) {
        const content = fs.readFileSync(policyPath, "utf8");
        const loadedPolicy = JSON.parse(content);
        this.policy = { ...this.policy, ...loadedPolicy };
        console.log(`📋 Loaded token policy from ${policyPath}`);
      } else {
        console.log("📋 Using default token policy (zero-token mode)");
      }
    } catch (error) {
      console.warn(`⚠️ Could not load policy from ${policyPath}, using defaults`);
    }
    
    // Start recovery timer
    this.startRecoveryTimer();
  }

  permit(step: TokenStep): boolean {
    const stepCost = step.cost || 1;
    const projectedUsage = this.currentUsage + stepCost;
    
    // Hard limit check
    if (projectedUsage > this.policy.hard_limit) {
      console.log(`🚫 Token Governor: Blocking step "${step.title}" - would exceed hard limit (${projectedUsage}/${this.policy.hard_limit})`);
      return false;
    }
    
    // Soft limit check with local alternative preference
    if (projectedUsage > this.policy.soft_limit) {
      if (step.local_alternative) {
        console.log(`🔄 Token Governor: Preferring local alternative for "${step.title}"`);
        return true;
      } else {
        console.log(`⚠️ Token Governor: Warning - approaching soft limit (${projectedUsage}/${this.policy.soft_limit})`);
      }
    }
    
    // Default mode enforcement
    if (this.policy.default_mode === "off" && stepCost > 0) {
      if (!step.local_alternative) {
        console.log(`🛑 Token Governor: Blocking paid operation "${step.title}" - zero-token mode active`);
        return false;
      }
    }
    
    // Permit the step
    this.currentUsage += stepCost;
    console.log(`✅ Token Governor: Permitted "${step.title}" (${stepCost} tokens, total: ${this.currentUsage})`);
    return true;
  }
  
  getUsage(): { used: number; max: number; remaining: number; percent: number } {
    return {
      used: this.currentUsage,
      max: this.policy.max_budget,
      remaining: this.policy.max_budget - this.currentUsage,
      percent: (this.currentUsage / this.policy.max_budget) * 100
    };
  }
  
  requestEscalation(reason: string, estimatedCost: number): boolean {
    if (estimatedCost < this.policy.escalation_threshold) {
      console.log(`🔺 Token Governor: Auto-approving small escalation (${estimatedCost} tokens) - ${reason}`);
      return true;
    }
    
    console.log(`⚠️ Token Governor: Large escalation request (${estimatedCost} tokens) - ${reason}`);
    console.log(`   Current usage: ${this.currentUsage}/${this.policy.max_budget}`);
    console.log(`   Manual approval required`);
    
    // In real implementation, this would prompt for user approval
    return false;
  }
  
  private startRecoveryTimer(): void {
    setInterval(() => {
      const now = Date.now();
      const hoursSinceLastRecovery = (now - this.lastRecovery) / (1000 * 60 * 60);
      
      if (hoursSinceLastRecovery >= 1.0) {
        const recovery = Math.min(this.policy.recovery_rate, this.currentUsage);
        this.currentUsage = Math.max(0, this.currentUsage - recovery);
        this.lastRecovery = now;
        
        if (recovery > 0) {
          console.log(`💰 Token Governor: Budget recovered ${recovery} tokens (${this.currentUsage}/${this.policy.max_budget})`);
        }
      }
    }, 60000); // Check every minute
  }
  
  emergency(): void {
    console.log("🚨 Token Governor: Emergency budget reset activated");
    this.currentUsage = 0;
    this.lastRecovery = Date.now();
  }
}

export const tokenGovernor = new TokenGovernor();