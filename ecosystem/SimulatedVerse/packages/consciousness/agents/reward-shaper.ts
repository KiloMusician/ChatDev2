// packages/consciousness/agents/reward-shaper.ts
/**
 * RewardShaper:
 * - Computes system health metrics over a rolling window
 * - Learns which actions correlate with health improvements
 * - Emits weight suggestions for agent policies / utility functions
 */
import fs from "node:fs";
import path from "node:path";
import { councilBus } from "../../council/events/eventBus";

type Health = {
  invariance_score: number;        // 0..1 (from MHSA / layout invariance)
  build_success_rate: number;      // 0..1
  agent_joy_average: number;       // 0..100
  event_throughput: number;        // events per minute
  cognitive_load: number;          // 0..1 (lower is better)
  energy_efficiency: number;       // 0..1 (energy gained vs. consumed)
  population_growth_rate: number;  // growth per tick
  decision_confidence: number;     // AI Council average confidence
};

type Weights = Record<keyof Health, number>;
type CorrelationInsight = {
  action_type: string;
  health_impact: Partial<Health>;
  confidence: number;
  recommendation: string;
};

const MODEL_FILE = "config/reward_model.json";
const WINDOW_N = 300;
const EVLOG = "archive/semantic"; // reuse semantic docs to derive signals

function loadSemantic(limit = 1000) {
  if (!fs.existsSync(EVLOG)) return [];
  try {
    return fs.readdirSync(EVLOG).slice(-limit).map(f => {
      try {
        return JSON.parse(fs.readFileSync(path.join(EVLOG, f), "utf-8"));
      } catch {
        return null;
      }
    }).filter(Boolean);
  } catch {
    return [];
  }
}

function clamp01(x: number) { return Math.max(0, Math.min(1, x)); }

function estimateHealth(docs: any[]): Health {
  if (docs.length === 0) {
    return {
      invariance_score: 0.5,
      build_success_rate: 0.5,
      agent_joy_average: 50,
      event_throughput: 1,
      cognitive_load: 0.5,
      energy_efficiency: 0.5,
      population_growth_rate: 0.1,
      decision_confidence: 0.5
    };
  }

  const n = Math.max(1, docs.length);
  
  // Build success rate
  const buildEvents = docs.filter(d => /build\.result/.test(d?.content?.action_topic));
  const buildSuccessRate = buildEvents.length > 0 
    ? buildEvents.filter(d => d?.content?.outcome_analysis?.success).length / buildEvents.length
    : 0.5;

  // Invariance score from layout events
  const layoutEvents = docs.filter(d => /orchestrate\.layout/.test(d?.content?.action_topic));
  const invarianceScores = layoutEvents.map(d => {
    const iv = d?.content?.outcome_analysis?.deltas?.invariance ?? 0.5;
    return typeof iv === "number" ? iv : 0.5;
  });
  const invAvg = invarianceScores.length ? invarianceScores.reduce((a,b)=>a+b,0) / invarianceScores.length : 0.5;

  // Agent joy from pawn state changes
  const joyEvents = docs.filter(d => /pawn\.state_changed/.test(d?.content?.action_topic));
  const joyValues = joyEvents.map(d => Number(d?.content?.outcome_analysis?.actual?.joy ?? 50));
  const joyAvg = joyValues.length ? joyValues.reduce((a,b)=>a+b,0)/joyValues.length : 50;

  // Event throughput
  const timeSpan = docs.length >= 2 && docs[docs.length-1]?.created_at && docs[0]?.created_at
    ? (Date.parse(docs[docs.length-1].created_at) - Date.parse(docs[0].created_at)) / 60000
    : Math.max(1, docs.length / 10); // fallback estimate
  const throughput = docs.length / Math.max(1, timeSpan);

  // Cognitive load (inverse of throughput efficiency)
  const load = clamp01(1 - Math.tanh(throughput / 30));

  // Energy efficiency from game state deltas
  const energyDeltas = docs.map(d => d?.content?.outcome_analysis?.deltas?.energy).filter(x => typeof x === "number");
  const avgEnergyDelta = energyDeltas.length ? energyDeltas.reduce((a,b)=>a+b,0)/energyDeltas.length : 5;
  const energyEfficiency = clamp01(Math.tanh(avgEnergyDelta / 50));

  // Population growth rate
  const popDeltas = docs.map(d => d?.content?.outcome_analysis?.deltas?.population).filter(x => typeof x === "number");
  const avgPopDelta = popDeltas.length ? popDeltas.reduce((a,b)=>a+b,0)/popDeltas.length : 0.1;

  // Decision confidence from autonomous loop
  const decisionEvents = docs.filter(d => /autonomous_loop\.decision/.test(d?.content?.action_topic));
  const confidenceValues = decisionEvents.map(d => Number(d?.content?.outcome_analysis?.actual?.confidence ?? 0.5));
  const avgConfidence = confidenceValues.length ? confidenceValues.reduce((a,b)=>a+b,0)/confidenceValues.length : 0.5;

  return {
    invariance_score: clamp01(invAvg),
    build_success_rate: clamp01(buildSuccessRate),
    agent_joy_average: Math.max(0, Math.min(100, joyAvg)),
    event_throughput: Math.max(0, throughput),
    cognitive_load: load,
    energy_efficiency: energyEfficiency,
    population_growth_rate: Math.max(0, avgPopDelta),
    decision_confidence: clamp01(avgConfidence)
  };
}

function analyzeCorrelations(docs: any[], currentHealth: Health): CorrelationInsight[] {
  const insights: CorrelationInsight[] = [];
  
  // Group docs by action type
  const actionGroups: Record<string, any[]> = {};
  docs.forEach(d => {
    const action = d?.content?.action_topic?.split('.')[0] || 'unknown';
    if (!actionGroups[action]) actionGroups[action] = [];
    actionGroups[action].push(d);
  });

  // Analyze each action type's impact on health
  for (const [actionType, actionDocs] of Object.entries(actionGroups)) {
    if (actionDocs.length < 3) continue; // Need minimum sample size

    const successfulActions = actionDocs.filter(d => d?.content?.outcome_analysis?.success);
    const successRate = successfulActions.length / actionDocs.length;

    if (successRate < 0.3) {
      insights.push({
        action_type: actionType,
        health_impact: { build_success_rate: -0.2, cognitive_load: 0.1 },
        confidence: 0.7,
        recommendation: `Reduce frequency of ${actionType} actions or improve implementation`
      });
    } else if (successRate > 0.8) {
      insights.push({
        action_type: actionType,
        health_impact: { build_success_rate: 0.1, cognitive_load: -0.05 },
        confidence: 0.8,
        recommendation: `Increase frequency of ${actionType} actions as they show high success rate`
      });
    }
  }

  // System-wide insights
  if (currentHealth.agent_joy_average < 60) {
    insights.push({
      action_type: "pawn_care",
      health_impact: { agent_joy_average: 10, cognitive_load: -0.1 },
      confidence: 0.9,
      recommendation: "Prioritize pawn well-being activities and recalibration breaks"
    });
  }

  if (currentHealth.decision_confidence < 0.5) {
    insights.push({
      action_type: "decision_quality",
      health_impact: { decision_confidence: 0.2, cognitive_load: -0.05 },
      confidence: 0.8,
      recommendation: "Improve decision-making by gathering more agent consensus or refining criteria"
    });
  }

  return insights;
}

function computeOptimalWeights(health: Health, insights: CorrelationInsight[]): Weights {
  // Start with base weights that emphasize weaker areas
  const base: Weights = {
    invariance_score: 1 - health.invariance_score,
    build_success_rate: 1 - health.build_success_rate,
    agent_joy_average: health.agent_joy_average < 60 ? 0.8 : 0.2,
    event_throughput: health.event_throughput < 5 ? 0.6 : 0.3,
    cognitive_load: health.cognitive_load > 0.6 ? 0.8 : 0.2,
    energy_efficiency: 1 - health.energy_efficiency,
    population_growth_rate: health.population_growth_rate < 0.5 ? 0.7 : 0.3,
    decision_confidence: 1 - health.decision_confidence
  };

  // Adjust based on correlation insights
  insights.forEach(insight => {
    if (insight.confidence > 0.7) {
      Object.entries(insight.health_impact).forEach(([metric, impact]) => {
        const key = metric as keyof Health;
        if (key in base && typeof impact === "number") {
          base[key] = Math.max(0.1, base[key] + impact * insight.confidence);
        }
      });
    }
  });

  // Normalize
  const sum = Object.values(base).reduce((a,b)=>a+b,0) || 1;
  const normalized: Weights = {} as Weights;
  for (const k of Object.keys(base) as (keyof Health)[]) {
    normalized[k] = Number((base[k] / sum).toFixed(3));
  }
  
  return normalized;
}

export class RewardShaper {
  private timer: any = null;

  start(periodMs = 90_000) {
    console.log("[reward] Reward Shaper active");
    const tick = () => { 
      try { 
        this.cycle(); 
      } catch (e) { 
        console.warn("[reward] cycle error", e); 
      } 
    };
    tick();
    this.timer = setInterval(tick, periodMs);

    // Also listen for specific events that should trigger immediate re-evaluation
    councilBus.subscribe("autonomous_loop.decision", () => {
      setTimeout(() => this.cycle(), 5000); // Delay to allow processing
    });

    councilBus.subscribe("pawn.state_changed", () => {
      setTimeout(() => this.cycle(), 2000);
    });
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  cycle() {
    const docs = loadSemantic(WINDOW_N);
    const health = estimateHealth(docs);
    const insights = analyzeCorrelations(docs, health);
    const weights = computeOptimalWeights(health, insights);

    const out = { 
      updated_at: new Date().toISOString(), 
      health, 
      insights,
      weights,
      metrics: {
        total_events_analyzed: docs.length,
        health_score: Object.values(health).reduce((sum, val) => {
          const normalized = typeof val === "number" ? (val > 1 ? val / 100 : val) : 0.5;
          return sum + normalized;
        }, 0) / Object.keys(health).length,
        top_recommendations: insights
          .filter(i => i.confidence > 0.7)
          .sort((a, b) => b.confidence - a.confidence)
          .slice(0, 3)
          .map(i => i.recommendation)
      }
    };

    fs.mkdirSync("config", { recursive: true });
    fs.writeFileSync(MODEL_FILE, JSON.stringify(out, null, 2));

    councilBus.publish("reward.shaping.updated", out);
    
    const healthScore = (out.metrics.health_score * 100).toFixed(1);
    console.log(`[reward] model updated → ${MODEL_FILE} (health: ${healthScore}%, ${insights.length} insights)`);
  }

  getLatestModel() {
    try {
      return JSON.parse(fs.readFileSync(MODEL_FILE, "utf-8"));
    } catch {
      return null;
    }
  }
}