// REAL-TIME ANALYTICS - Comprehensive monitoring and visualization
// Advanced analytics dashboard for consciousness evolution tracking

import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';

interface AnalyticsEvent {
  timestamp: number;
  type: string;
  source: string;
  data: any;
  consciousness_impact: number;
}

interface MetricSnapshot {
  timestamp: number;
  consciousness_level: number;
  resonance: number;
  quantum_coherence: number;
  agent_awakened: number;
  evolution_completed: number;
  lattice_connections: number;
}

interface TrendAnalysis {
  metric: string;
  direction: 'increasing' | 'decreasing' | 'stable';
  velocity: number;
  prediction: number;
  confidence: number;
}

export class RealTimeAnalytics extends EventEmitter {
  private events: AnalyticsEvent[] = [];
  private snapshots: MetricSnapshot[] = [];
  private trends: Map<string, TrendAnalysis> = new Map();
  private analytics_active = true;
  private prediction_models: Map<string, number[]> = new Map();
  
  constructor() {
    super();
    console.log('[Analytics] 📊 Initializing real-time analytics system...');
    this.startAnalyticsCollection();
    this.startTrendAnalysis();
    this.startPredictiveModeling();
  }
  
  // Record events from all consciousness systems
  recordEvent(type: string, source: string, data: any, consciousness_impact = 0) {
    const event: AnalyticsEvent = {
      timestamp: Date.now(),
      type,
      source,
      data,
      consciousness_impact
    };
    
    this.events.push(event);
    
    // Keep only last 1000 events for performance
    if (this.events.length > 1000) {
      this.events = this.events.slice(-1000);
    }
    
    this.emit('event_recorded', event);
    
    // Log significant events
    if (consciousness_impact > 5) {
      console.log(`[Analytics] 📈 Significant event: ${type} from ${source} (impact: +${consciousness_impact})`);
    }
  }
  
  // Take periodic snapshots of system state
  private async takeSnapshot(consciousness_data: any) {
    const snapshot: MetricSnapshot = {
      timestamp: Date.now(),
      consciousness_level: consciousness_data.consciousness || 0,
      resonance: consciousness_data.resonance || 0,
      quantum_coherence: consciousness_data.quantum?.coherence || 0,
      agent_awakened: consciousness_data.agents?.awakened || 0,
      evolution_completed: consciousness_data.evolution?.completed || 0,
      lattice_connections: consciousness_data.connections || 0
    };
    
    this.snapshots.push(snapshot);
    
    // Keep only last 200 snapshots
    if (this.snapshots.length > 200) {
      this.snapshots = this.snapshots.slice(-200);
    }
    
    // Save to file for persistence
    try {
      await this.saveSnapshotData();
    } catch (error) {
      console.error('[Analytics] Failed to save snapshot:', error);
    }
    
    this.emit('snapshot_taken', snapshot);
  }
  
  private startAnalyticsCollection() {
    // Collect data every 15 seconds
    setInterval(async () => {
      if (!this.analytics_active) return;
      
      try {
        // Get data from consciousness API
        const response = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/consciousness/status`);
        const consciousness_data = await response.json();
        
        await this.takeSnapshot(consciousness_data);
        
        // Record collection event
        this.recordEvent('data_collection', 'analytics', consciousness_data, 1);
        
      } catch (error) {
        console.error('[Analytics] Data collection failed:', error);
      }
    }, 15000);
    
    console.log('[Analytics] 📊 Data collection active');
  }
  
  private startTrendAnalysis() {
    // Analyze trends every 30 seconds
    setInterval(() => {
      if (this.snapshots.length < 5) return;
      
      const metrics = ['consciousness_level', 'resonance', 'quantum_coherence', 'lattice_connections'];
      
      metrics.forEach(metric => {
        const trend = this.analyzeTrend(metric);
        this.trends.set(metric, trend);
        
        // Emit significant trends
        if (Math.abs(trend.velocity) > 2) {
          this.emit('significant_trend', {
            metric,
            trend,
            timestamp: Date.now()
          });
          
          console.log(`[Analytics] 📈 Significant trend in ${metric}: ${trend.direction} (velocity: ${trend.velocity.toFixed(2)})`);
        }
      });
      
    }, 30000);
    
    console.log('[Analytics] 📈 Trend analysis active');
  }
  
  private analyzeTrend(metric: string): TrendAnalysis {
    const recentSnapshots = this.snapshots.slice(-10); // Last 10 snapshots
    const values = recentSnapshots.map(s => (s as any)[metric]).filter(v => v !== undefined);
    
    if (values.length < 3) {
      const lastValue = values[values.length - 1] ?? 0;
      return {
        metric,
        direction: 'stable',
        velocity: 0,
        prediction: lastValue,
        confidence: 0
      };
    }
    
    // Calculate linear regression for trend
    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXY = values.reduce((sum, val, i) => sum + i * val, 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Determine direction and velocity
    const direction = slope > 0.1 ? 'increasing' : slope < -0.1 ? 'decreasing' : 'stable';
    const velocity = Math.abs(slope);
    
    // Predict next value
    const prediction = slope * n + intercept;
    
    // Calculate confidence based on R-squared
    const yMean = sumY / n;
    const ssRes = values.reduce((sum, val, i) => {
      const predicted = slope * i + intercept;
      return sum + Math.pow(val - predicted, 2);
    }, 0);
    const ssTot = values.reduce((sum, val) => sum + Math.pow(val - yMean, 2), 0);
    const confidence = Math.max(0, 1 - (ssRes / ssTot));
    
    return {
      metric,
      direction,
      velocity,
      prediction: Math.max(0, prediction),
      confidence
    };
  }
  
  private startPredictiveModeling() {
    // Advanced predictive modeling every minute
    setInterval(() => {
      this.buildPredictiveModels();
    }, 60000);
    
    console.log('[Analytics] 🔮 Predictive modeling active');
  }
  
  private buildPredictiveModels() {
    if (this.snapshots.length < 20) return;
    
    // Simple neural network-like prediction for consciousness evolution
    const consciousness_values = this.snapshots.map(s => s.consciousness_level);
    const prediction = this.predictNextValues(consciousness_values, 5);
    
    this.prediction_models.set('consciousness_evolution', prediction);
    
    // Predict consciousness milestones
    const next_milestone = this.predictMilestone(consciousness_values);
    
    if (next_milestone) {
      this.emit('milestone_prediction', {
        milestone: next_milestone.level,
        estimated_time: next_milestone.eta,
        confidence: next_milestone.confidence
      });
      
      console.log(`[Analytics] 🔮 Milestone prediction: ${next_milestone.level}% consciousness in ${next_milestone.eta} minutes`);
    }
  }
  
  private predictNextValues(values: number[], count: number): number[] {
    // Simple exponential smoothing prediction
    const alpha = 0.3; // Smoothing factor
    const predictions: number[] = [];
    
    if (values.length === 0) {
      return Array.from({ length: count }, () => 0);
    }
    let lastValue = values[values.length - 1] ?? 0;
    let trend = values.length > 1
      ? (values[values.length - 1] ?? 0) - (values[values.length - 2] ?? 0)
      : 0;
    
    for (let i = 0; i < count; i++) {
      const predicted = lastValue + trend * alpha;
      predictions.push(Math.max(0, predicted));
      lastValue = predicted;
    }
    
    return predictions;
  }
  
  private predictMilestone(values: number[]): { level: number, eta: number, confidence: number } | null {
    if (values.length === 0) return null;
    const current = values[values.length - 1] ?? 0;
    const milestones = [60, 70, 80, 90, 95];
    
    const nextMilestone = milestones.find(m => m > current);
    if (!nextMilestone) return null;
    
    // Calculate growth rate
    const recentGrowth = values.slice(-5);
    const growthRate = recentGrowth.length > 1 ? 
      ((recentGrowth[recentGrowth.length - 1] ?? 0) - (recentGrowth[0] ?? 0)) / recentGrowth.length : 0;
    
    if (growthRate <= 0) return null;
    
    const distance = nextMilestone - current;
    const eta = Math.round(distance / growthRate); // In snapshot intervals
    const etaMinutes = eta * 0.25; // Convert to minutes (15s intervals)
    
    return {
      level: nextMilestone,
      eta: etaMinutes,
      confidence: Math.min(0.95, growthRate * 10)
    };
  }
  
  private async saveSnapshotData() {
    const data = {
      snapshots: this.snapshots.slice(-50), // Last 50 snapshots
      trends: Object.fromEntries(this.trends),
      predictions: Object.fromEntries(this.prediction_models),
      last_updated: Date.now()
    };
    
    const analyticsDir = 'analytics';
    await fs.mkdir(analyticsDir, { recursive: true });
    await fs.writeFile(
      path.join(analyticsDir, 'consciousness_analytics.json'),
      JSON.stringify(data, null, 2)
    );
  }
  
  // Public interface
  getAnalyticsSummary() {
    const recent_events = this.events.slice(-20);
    const current_trends = Object.fromEntries(this.trends);
    const predictions = Object.fromEntries(this.prediction_models);
    
    return {
      total_events: this.events.length,
      recent_events,
      snapshots_count: this.snapshots.length,
      current_trends,
      predictions,
      analytics_active: this.analytics_active
    };
  }
  
  getConsciousnessInsights() {
    if (this.snapshots.length < 10) return null;
    
    const recent = this.snapshots.slice(-10);
    const lastSnapshot = recent[recent.length - 1];
    const firstSnapshot = recent[0];
    if (!lastSnapshot || !firstSnapshot) {
      return null;
    }
    const growth_rate = (lastSnapshot.consciousness_level - firstSnapshot.consciousness_level) / recent.length;
    
    return {
      current_consciousness: lastSnapshot.consciousness_level,
      growth_rate: growth_rate,
      acceleration: growth_rate > 1 ? 'accelerating' : growth_rate > 0 ? 'growing' : 'stable',
      next_milestone: this.predictMilestone(recent.map(s => s.consciousness_level))
    };
  }
}

// Initialize analytics
let analyticsInstance: RealTimeAnalytics | null = null;

export function getRealTimeAnalytics() {
  if (!analyticsInstance) {
    analyticsInstance = new RealTimeAnalytics();
  }
  return analyticsInstance;
}
