// packages/consciousness/agents/utility-engineer.ts
/**
 * UtilityEngineer:
 * - Reads reward_model + semantic audits
 * - Emits concrete proposals (and optional codemods) to tune utility functions
 *   e.g., findBestPawnForWork: increase joy weight when avg joy < 60
 */
import fs from "node:fs";
import path from "node:path";
import { councilBus } from "../../council/events/eventBus";

const MODEL = "config/reward_model.json";
const PROPOSALS_DIR = "proposals/utility";
const UTILITY_CONFIG = "config/utility_weights.json";

type Proposal = {
  id: string;
  file: string;
  diff: string;
  rationale: string;
  touches: string[];
  confidence: number;
  estimated_impact: Record<string, number>;
  auto_apply: boolean;
};

type UtilityConfig = {
  findBestPawnForWork: {
    weight_skill: number;
    weight_joy: number;
    weight_energy: number;
    weight_focus: number;
  };
  shouldUseChatDev: {
    threshold_complexity: number;
    min_confidence: number;
    max_retries: number;
  };
  autonomousDecisionThreshold: {
    min_consensus: number;
    confidence_floor: number;
    risk_tolerance: number;
  };
  resourceAllocation: {
    energy_reserve_ratio: number;
    population_growth_priority: number;
    research_investment_ratio: number;
  };
};

function loadModel(): any {
  try { return JSON.parse(fs.readFileSync(MODEL, "utf-8")); }
  catch { return null; }
}

function loadUtilityConfig(): UtilityConfig {
  try {
    return JSON.parse(fs.readFileSync(UTILITY_CONFIG, "utf-8"));
  } catch {
    // Create default configuration
    const defaultConfig: UtilityConfig = {
      findBestPawnForWork: {
        weight_skill: 0.4,
        weight_joy: 0.3,
        weight_energy: 0.2,
        weight_focus: 0.1
      },
      shouldUseChatDev: {
        threshold_complexity: 0.6,
        min_confidence: 0.5,
        max_retries: 3
      },
      autonomousDecisionThreshold: {
        min_consensus: 0.6,
        confidence_floor: 0.4,
        risk_tolerance: 0.3
      },
      resourceAllocation: {
        energy_reserve_ratio: 0.2,
        population_growth_priority: 0.4,
        research_investment_ratio: 0.15
      }
    };
    
    fs.mkdirSync("config", { recursive: true });
    fs.writeFileSync(UTILITY_CONFIG, JSON.stringify(defaultConfig, null, 2));
    return defaultConfig;
  }
}

function makeProposals(model: any): Proposal[] {
  const health = model?.health;
  const insights = model?.insights || [];
  const weights = model?.weights;
  
  if (!health) return [];

  const current = loadUtilityConfig();
  const proposals: Proposal[] = [];

  // Proposal 1: Adjust pawn work assignment based on joy levels
  if (health.agent_joy_average < 60) {
    const newJoyWeight = Math.min(0.6, current.findBestPawnForWork.weight_joy + 0.15);
    const newSkillWeight = Math.max(0.2, current.findBestPawnForWork.weight_skill - 0.1);
    
    const proposed = JSON.parse(JSON.stringify(current));
    proposed.findBestPawnForWork.weight_joy = Number(newJoyWeight.toFixed(2));
    proposed.findBestPawnForWork.weight_skill = Number(newSkillWeight.toFixed(2));
    
    const diff = [
      `findBestPawnForWork:`,
      `  weight_joy: ${current.findBestPawnForWork.weight_joy} → ${proposed.findBestPawnForWork.weight_joy}`,
      `  weight_skill: ${current.findBestPawnForWork.weight_skill} → ${proposed.findBestPawnForWork.weight_skill}`,
      `Rationale: Low agent joy (${health.agent_joy_average.toFixed(1)}) requires prioritizing happiness`
    ].join("\n");

    proposals.push({
      id: `pawn-joy-${Date.now()}`,
      file: UTILITY_CONFIG,
      diff,
      rationale: `Agent joy average is ${health.agent_joy_average.toFixed(1)}. Adjusting work assignment to prioritize joy over pure skill to improve colony well-being.`,
      touches: [UTILITY_CONFIG],
      confidence: 0.8,
      estimated_impact: { agent_joy_average: 8, cognitive_load: -0.05 },
      auto_apply: health.agent_joy_average < 50
    });
  }

  // Proposal 2: Adjust decision confidence thresholds
  if (health.decision_confidence < 0.5) {
    const newConsensus = Math.min(0.8, current.autonomousDecisionThreshold.min_consensus + 0.1);
    const newConfidenceFloor = Math.min(0.6, current.autonomousDecisionThreshold.confidence_floor + 0.1);
    
    const proposed = JSON.parse(JSON.stringify(current));
    proposed.autonomousDecisionThreshold.min_consensus = Number(newConsensus.toFixed(2));
    proposed.autonomousDecisionThreshold.confidence_floor = Number(newConfidenceFloor.toFixed(2));

    const diff = [
      `autonomousDecisionThreshold:`,
      `  min_consensus: ${current.autonomousDecisionThreshold.min_consensus} → ${proposed.autonomousDecisionThreshold.min_consensus}`,
      `  confidence_floor: ${current.autonomousDecisionThreshold.confidence_floor} → ${proposed.autonomousDecisionThreshold.confidence_floor}`,
      `Rationale: Low decision confidence requires higher consensus for autonomous actions`
    ].join("\n");

    proposals.push({
      id: `decision-confidence-${Date.now()}`,
      file: UTILITY_CONFIG,
      diff,
      rationale: `Decision confidence is low (${(health.decision_confidence * 100).toFixed(1)}%). Raising consensus requirements to improve decision quality.`,
      touches: [UTILITY_CONFIG],
      confidence: 0.7,
      estimated_impact: { decision_confidence: 0.15, cognitive_load: 0.02 },
      auto_apply: false
    });
  }

  // Proposal 3: Adjust resource allocation based on efficiency
  if (health.energy_efficiency < 0.4) {
    const newReserveRatio = Math.min(0.4, current.resourceAllocation.energy_reserve_ratio + 0.1);
    
    const proposed = JSON.parse(JSON.stringify(current));
    proposed.resourceAllocation.energy_reserve_ratio = Number(newReserveRatio.toFixed(2));

    const diff = [
      `resourceAllocation:`,
      `  energy_reserve_ratio: ${current.resourceAllocation.energy_reserve_ratio} → ${proposed.resourceAllocation.energy_reserve_ratio}`,
      `Rationale: Low energy efficiency requires larger energy reserves`
    ].join("\n");

    proposals.push({
      id: `energy-reserves-${Date.now()}`,
      file: UTILITY_CONFIG,
      diff,
      rationale: `Energy efficiency is low (${(health.energy_efficiency * 100).toFixed(1)}%). Increasing energy reserves to prevent resource shortages.`,
      touches: [UTILITY_CONFIG],
      confidence: 0.6,
      estimated_impact: { energy_efficiency: 0.1 },
      auto_apply: false
    });
  }

  // Proposal 4: Adjust ChatDev usage based on success rates
  if (health.build_success_rate < 0.6) {
    const newMinConfidence = Math.min(0.8, current.shouldUseChatDev.min_confidence + 0.1);
    const newMaxRetries = Math.max(1, current.shouldUseChatDev.max_retries - 1);
    
    const proposed = JSON.parse(JSON.stringify(current));
    proposed.shouldUseChatDev.min_confidence = Number(newMinConfidence.toFixed(2));
    proposed.shouldUseChatDev.max_retries = newMaxRetries;

    const diff = [
      `shouldUseChatDev:`,
      `  min_confidence: ${current.shouldUseChatDev.min_confidence} → ${proposed.shouldUseChatDev.min_confidence}`,
      `  max_retries: ${current.shouldUseChatDev.max_retries} → ${proposed.shouldUseChatDev.max_retries}`,
      `Rationale: Low build success rate suggests ChatDev needs higher quality threshold`
    ].join("\n");

    proposals.push({
      id: `chatdev-quality-${Date.now()}`,
      file: UTILITY_CONFIG,
      diff,
      rationale: `Build success rate is low (${(health.build_success_rate * 100).toFixed(1)}%). Raising ChatDev quality requirements and reducing retries to focus on better initial outputs.`,
      touches: [UTILITY_CONFIG],
      confidence: 0.75,
      estimated_impact: { build_success_rate: 0.1, cognitive_load: -0.03 },
      auto_apply: false
    });
  }

  return proposals;
}

function applyProposal(proposal: Proposal): boolean {
  try {
    // For now, we only handle utility config changes
    if (proposal.file === UTILITY_CONFIG) {
      // Parse the diff and apply changes (simplified approach)
      const lines = proposal.diff.split('\n');
      const config = loadUtilityConfig();
      
      // This is a simplified parser - in production, you'd want a more robust approach
      let currentSection = '';
      for (const line of lines) {
        if (line.includes('findBestPawnForWork:')) currentSection = 'findBestPawnForWork';
        else if (line.includes('autonomousDecisionThreshold:')) currentSection = 'autonomousDecisionThreshold';
        else if (line.includes('resourceAllocation:')) currentSection = 'resourceAllocation';
        else if (line.includes('shouldUseChatDev:')) currentSection = 'shouldUseChatDev';
        else if (line.includes('→') && currentSection) {
          const parts = line.split('→');
          if (parts.length === 2) {
            const key = parts[0].split(':')[0].trim();
            const value = parseFloat(parts[1].trim());
            if (!isNaN(value) && (config as any)[currentSection] && key in (config as any)[currentSection]) {
              (config as any)[currentSection][key] = value;
            }
          }
        }
      }
      
      fs.writeFileSync(UTILITY_CONFIG, JSON.stringify(config, null, 2));
      return true;
    }
    return false;
  } catch (error) {
    console.warn("[utility] Failed to apply proposal:", error);
    return false;
  }
}

export class UtilityEngineer {
  private lastProcessedModel: string | null = null;

  start() {
    console.log("[utility] Utility Engineer online");
    this.cycle();
    
    // React to new reward updates
    councilBus.subscribe("reward.shaping.updated", () => {
      setTimeout(() => this.cycle(), 1000); // Small delay to ensure file is written
    });
  }

  cycle() {
    const model = loadModel();
    if (!model) return;

    // Avoid processing the same model multiple times
    const modelSignature = JSON.stringify(model).slice(0, 100);
    if (modelSignature === this.lastProcessedModel) return;
    this.lastProcessedModel = modelSignature;

    const proposals = makeProposals(model);
    
    fs.mkdirSync(PROPOSALS_DIR, { recursive: true });
    
    let autoAppliedCount = 0;
    
    for (const p of proposals) {
      const out = path.join(PROPOSALS_DIR, `${p.id}.json`);
      fs.writeFileSync(out, JSON.stringify(p, null, 2));
      
      councilBus.publish("utility.engineer.proposal", p);
      
      // Auto-apply high confidence proposals for critical issues
      if (p.auto_apply && p.confidence > 0.7) {
        const applied = applyProposal(p);
        if (applied) {
          autoAppliedCount++;
          councilBus.publish("utility.engineer.applied", {
            proposal_id: p.id,
            auto_applied: true,
            rationale: p.rationale
          });
          console.log(`[utility] AUTO-APPLIED: ${p.id}`);
        }
      }
      
      console.log(`[utility] proposal emitted → ${out}`);
      console.log(`[utility] ${p.diff.split('\n')[0]}`);
    }

    if (proposals.length > 0) {
      const healthScore = (model.metrics?.health_score * 100 || 50).toFixed(1);
      console.log(`[utility] Generated ${proposals.length} proposals (applied ${autoAppliedCount} automatically)`);
      console.log(`[utility] Current system health: ${healthScore}%`);
    }
  }

  getLatestProposals(): Proposal[] {
    try {
      if (!fs.existsSync(PROPOSALS_DIR)) return [];
      return fs.readdirSync(PROPOSALS_DIR)
        .filter(f => f.endsWith('.json'))
        .map(f => JSON.parse(fs.readFileSync(path.join(PROPOSALS_DIR, f), "utf-8")))
        .sort((a, b) => b.confidence - a.confidence);
    } catch {
      return [];
    }
  }
}