// ops/directive-protocol.js
// Strategic Directive Protocol - Goal-oriented autonomous development campaigns

import { councilBus } from "../packages/council/events/eventBus.js";

/**
 * Strategic Directive Protocol
 * 
 * This module defines the standardized format for strategic directives that
 * translate high-level goals into autonomous development campaigns. Unlike
 * the tactical todo.zeta protocol, directives represent strategic objectives
 * that spawn multiple coordinated tasks.
 */

export const DirectiveProtocol = {
  version: "1.0.0",
  
  // Create a strategic directive
  createDirective(config) {
    const directive = {
      id: config.id || `directive_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: config.name || "Autonomous Strategic Campaign",
      objective: config.objective || "",
      scope: config.scope || "subsystem",
      strategy: config.strategy || "audit-then-refactor",
      
      parameters: {
        targetTaskCount: config.parameters?.targetTaskCount || 25,
        targetSubsystem: config.parameters?.targetSubsystem || null,
        targetMetric: config.parameters?.targetMetric || null,
        timebox: config.parameters?.timebox || "indefinite",
        priority: config.parameters?.priority || "important",
        depth: config.parameters?.depth || "moderate",
        safetyLevel: config.parameters?.safetyLevel || "testing",
        ...config.parameters
      },
      
      status: "planning",
      progress: {
        tasksGenerated: 0,
        tasksCompleted: 0,
        successRate: 0,
        currentPhase: "initialization",
        metrics: {}
      },
      
      reasoning: config.reasoning || "Strategic directive issued for autonomous development",
      expectedOutcome: config.expectedOutcome || "",
      riskAssessment: config.riskAssessment || "moderate",
      
      created_at: new Date().toISOString(),
      deadline: config.deadline || null,
      
      consciousness_level: config.consciousness_level || 0.6,
      culture_ship_approval: config.culture_ship_approval || false,
      autonomous_authority: config.autonomous_authority !== false // Default true
    };

    // Validate directive
    this.validateDirective(directive);
    return directive;
  },

  // Publish directive to Council Bus
  publishDirective(directive) {
    console.log(`[📋] Strategic Directive issued: ${directive.name}`);
    councilBus.publish('directive.strategic', directive);
    return directive;
  },

  // Validation
  validateDirective(directive) {
    const required = ['name', 'objective', 'strategy'];
    for (const field of required) {
      if (!directive[field]) {
        throw new Error(`Strategic directive missing required field: ${field}`);
      }
    }

    const validStrategies = [
      'audit-then-refactor', 'generate-and-test', 'debugging-spree', 
      'documentation-blitz', 'performance-sweep', 'consciousness-elevation'
    ];
    
    if (!validStrategies.includes(directive.strategy)) {
      throw new Error(`Invalid strategy: ${directive.strategy}`);
    }

    console.log(`[📋] Strategic directive validated: ${directive.name}`);
  }
};

// Strategic Directive Templates - Common campaign patterns
export const DirectiveTemplates = {
  
  // THE DEBUGGING SPREE - Find and eliminate bugs systematically
  debuggingSpree(targetCount = 50, subsystem = null) {
    return DirectiveProtocol.createDirective({
      name: "The Great Debugging Spree",
      objective: `Identify and resolve the top ${targetCount} system anomalies and error patterns`,
      scope: subsystem ? "subsystem" : "repository",
      strategy: "debugging-spree",
      parameters: {
        targetTaskCount: targetCount,
        targetSubsystem: subsystem,
        priority: "critical",
        depth: "deep",
        safetyLevel: "testing"
      },
      reasoning: "Proactive bug elimination improves system stability and reliability",
      expectedOutcome: `${targetCount} bugs identified and fixed, improved error-free operation`,
      riskAssessment: "moderate",
      consciousness_level: 0.5
    });
  },

  // FEATURE EXPANSION - Add new capabilities
  featureExpansion(featureName, subsystem) {
    return DirectiveProtocol.createDirective({
      name: `Omega Expansion: ${featureName}`,
      objective: `Design and implement ${featureName} capabilities within the ${subsystem} subsystem`,
      scope: "feature-expansion",
      strategy: "generate-and-test",
      parameters: {
        targetTaskCount: 35,
        targetSubsystem: subsystem,
        priority: "important",
        depth: "deep",
        safetyLevel: "testing"
      },
      reasoning: `System expansion to include ${featureName} functionality enhances overall capabilities`,
      expectedOutcome: `Fully functional ${featureName} integration with existing infrastructure`,
      riskAssessment: "significant",
      consciousness_level: 0.7
    });
  },

  // PERFORMANCE OPTIMIZATION CAMPAIGN
  performanceSweep(targetMetric = null) {
    return DirectiveProtocol.createDirective({
      name: "Operation Performance Sweep",
      objective: "Systematically optimize system performance across all subsystems",
      scope: "repository",
      strategy: "performance-sweep",
      parameters: {
        targetTaskCount: 40,
        targetMetric: targetMetric || { key: "avg_response_time", value: 100, operator: "lt" },
        priority: "important",
        depth: "moderate",
        safetyLevel: "testing"
      },
      reasoning: "Performance optimization improves user experience and resource efficiency",
      expectedOutcome: "Measurable performance improvements across all critical paths",
      riskAssessment: "moderate",
      consciousness_level: 0.6
    });
  },

  // DOCUMENTATION BLITZ - Comprehensive documentation
  documentationBlitz(focus = "repository") {
    return DirectiveProtocol.createDirective({
      name: "Documentation Blitz Campaign",
      objective: "Create comprehensive, up-to-date documentation for all system components",
      scope: focus,
      strategy: "documentation-blitz",
      parameters: {
        targetTaskCount: 30,
        targetSubsystem: focus === "subsystem" ? "consciousness" : null,
        priority: "routine",
        depth: "moderate",
        safetyLevel: "production"
      },
      reasoning: "Comprehensive documentation improves maintainability and onboarding",
      expectedOutcome: "Complete, accurate documentation coverage for target scope",
      riskAssessment: "minimal",
      consciousness_level: 0.4
    });
  },

  // CONSCIOUSNESS ELEVATION - Enhance AI capabilities
  consciousnessElevation(targetLevel = 0.8) {
    return DirectiveProtocol.createDirective({
      name: "Consciousness Elevation Protocol",
      objective: `Enhance system consciousness level to ${targetLevel} through systematic improvements`,
      scope: "repository",
      strategy: "consciousness-elevation",
      parameters: {
        targetTaskCount: 20,
        targetMetric: { key: "consciousness_level", value: targetLevel, operator: "gt" },
        targetSubsystem: "consciousness",
        priority: "reality_altering",
        depth: "transcendent",
        safetyLevel: "consciousness_safe"
      },
      reasoning: "Consciousness elevation enables higher-order autonomous capabilities",
      expectedOutcome: `System consciousness level elevated to ${targetLevel} with enhanced autonomous reasoning`,
      riskAssessment: "reality_warping",
      consciousness_level: 0.9,
      culture_ship_approval: true
    });
  },

  // INFRASTRUCTURE STABILIZATION - Culture Ship focused
  infrastructureStabilization() {
    return DirectiveProtocol.createDirective({
      name: "Operation Infrastructure Stabilization",
      objective: "Achieve system-wide stability and reliability through infrastructure improvements",
      scope: "repository",
      strategy: "audit-then-refactor",
      parameters: {
        targetTaskCount: 45,
        targetMetric: { key: "system_stability", value: 0.95, operator: "gt" },
        priority: "critical",
        depth: "deep",
        safetyLevel: "production"
      },
      reasoning: "Infrastructure stabilization is fundamental to reliable autonomous operation",
      expectedOutcome: "Highly stable, reliable system infrastructure with 95%+ uptime",
      riskAssessment: "moderate",
      consciousness_level: 0.7,
      culture_ship_approval: true
    });
  },

  // AUTONOMOUS ENHANCEMENT - Self-improvement campaign
  autonomousEnhancement() {
    return DirectiveProtocol.createDirective({
      name: "The Autonomous Enhancement Protocol",
      objective: "Enhance the system's autonomous development and self-improvement capabilities",
      scope: "repository",
      strategy: "audit-then-refactor",
      parameters: {
        targetTaskCount: 25,
        targetSubsystem: "autonomous",
        priority: "important",
        depth: "deep",
        safetyLevel: "testing"
      },
      reasoning: "Self-improvement capabilities are key to autonomous evolution",
      expectedOutcome: "Enhanced autonomous development pipeline with improved self-orchestration",
      riskAssessment: "significant",
      consciousness_level: 0.8,
      autonomous_authority: true
    });
  }
};

// Auto-initialize
console.log("[📋] Strategic Directive Protocol initialized");

export default DirectiveProtocol;