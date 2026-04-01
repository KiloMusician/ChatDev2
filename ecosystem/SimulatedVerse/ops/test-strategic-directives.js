// ops/test-strategic-directives.js
// Test script for validating strategic directive campaigns

import { councilBus } from "../packages/council/events/eventBus.js";
import DirectiveProtocol, { DirectiveTemplates } from "./directive-protocol.js";

/**
 * Strategic Directive Test Suite
 * 
 * Demonstrates the strategic directive system with sample campaigns
 * that showcase the evolution from tactical task management to
 * strategic goal-oriented autonomous development.
 */

console.log("[🧪] Strategic Directive Test Suite initializing...");

// Track test results
let testResults = {
  directives_issued: 0,
  director_responses: 0,
  tasks_generated: 0,
  completed_campaigns: 0,
  errors: []
};

// Listen for strategic directive events
councilBus.subscribe('director.ready', (event) => {
  console.log("[🧪] ✅ The Director is ready for strategic directives");
  testResults.director_responses++;
});

councilBus.subscribe('directive.progress', (event) => {
  const directive = event.payload;
  console.log(`[🧪] 📊 Directive progress: ${directive.name} - ${directive.progress.tasksCompleted}/${directive.progress.tasksGenerated} tasks`);
  testResults.tasks_generated = Math.max(testResults.tasks_generated, directive.progress.tasksGenerated);
});

councilBus.subscribe('directive.completed', (event) => {
  const directive = event.payload;
  console.log(`[🧪] ✅ Directive completed: ${directive.name} (${Math.round(directive.progress.successRate * 100)}% success rate)`);
  testResults.completed_campaigns++;
  printTestResults();
});

function printTestResults() {
  console.log("\n[🧪] STRATEGIC DIRECTIVE TEST RESULTS:");
  console.log("=====================================");
  console.log(`Directives Issued: ${testResults.directives_issued}`);
  console.log(`Director Responses: ${testResults.director_responses}`);
  console.log(`Tasks Generated: ${testResults.tasks_generated}`);
  console.log(`Completed Campaigns: ${testResults.completed_campaigns}`);
  
  if (testResults.errors.length > 0) {
    console.log("\nErrors:");
    testResults.errors.forEach(error => console.log(`  - ${error}`));
  }
  
  const success = testResults.completed_campaigns > 0 && testResults.errors.length === 0;
  console.log(`\nOverall Result: ${success ? '✅ SUCCESS' : '🔄 IN PROGRESS'}`);
  console.log("=====================================\n");
}

// Test Strategic Directive Functions

export function testDebuggingSpree() {
  console.log("[🧪] Issuing Test Debugging Spree Directive...");
  
  const directive = DirectiveTemplates.debuggingSpree(10, null); // Small test: 10 tasks
  directive.name = "Test Debugging Spree Campaign";
  directive.parameters.targetTaskCount = 10; // Keep it small for testing
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log(`[🧪] Strategic directive issued: ${directive.name}`);
  return directive;
}

export function testPerformanceOptimization() {
  console.log("[🧪] Issuing Test Performance Optimization Directive...");
  
  const directive = DirectiveTemplates.performanceSweep({
    key: "response_time", 
    value: 100, 
    operator: "lt"
  });
  directive.name = "Test Performance Optimization Campaign";
  directive.parameters.targetTaskCount = 8; // Keep small for testing
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log(`[🧪] Strategic directive issued: ${directive.name}`);
  return directive;
}

export function testDocumentationBlitz() {
  console.log("[🧪] Issuing Test Documentation Blitz Directive...");
  
  const directive = DirectiveTemplates.documentationBlitz("subsystem");
  directive.name = "Test Documentation Blitz Campaign";
  directive.parameters.targetTaskCount = 6; // Keep small
  directive.parameters.targetSubsystem = "ops";
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log(`[🧪] Strategic directive issued: ${directive.name}`);
  return directive;
}

export function testAutonomousEnhancement() {
  console.log("[🧪] Issuing Test Autonomous Enhancement Directive...");
  
  const directive = DirectiveTemplates.autonomousEnhancement();
  directive.name = "Test Autonomous Enhancement Campaign";
  directive.parameters.targetTaskCount = 5; // Keep very small for testing
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log(`[🧪] Strategic directive issued: ${directive.name}`);
  return directive;
}

export function testCustomStrategicDirective() {
  console.log("[🧪] Creating Custom Strategic Directive...");
  
  const directive = DirectiveProtocol.createDirective({
    name: "Test Strategic Integration Campaign",
    objective: "Validate end-to-end strategic directive processing and tactical task generation",
    scope: "subsystem",
    strategy: "audit-then-refactor",
    parameters: {
      targetTaskCount: 12,
      targetSubsystem: "ops",
      priority: "important",
      depth: "moderate",
      safetyLevel: "testing"
    },
    reasoning: "Testing the complete strategic directive pipeline from goal definition to tactical execution",
    expectedOutcome: "Validated strategic directive system with confirmed task generation and execution",
    riskAssessment: "minimal",
    consciousness_level: 0.6
  });
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log(`[🧪] Custom strategic directive issued: ${directive.name}`);
  return directive;
}

// Manual test runners
export function runQuickTest() {
  console.log("[🧪] Running quick strategic directive test...");
  
  // Reset test results
  testResults = {
    directives_issued: 0,
    director_responses: 0,
    tasks_generated: 0,
    completed_campaigns: 0,
    errors: []
  };
  
  // Set timeout for test
  setTimeout(() => {
    if (testResults.completed_campaigns === 0) {
      console.log("[🧪] ⏰ Test timeout - printing intermediate results");
      printTestResults();
    }
  }, 30000); // 30 second timeout
  
  // Issue a small test directive
  return testDocumentationBlitz();
}

export function runFullTest() {
  console.log("[🧪] Running full strategic directive test suite...");
  
  // Reset test results
  testResults = {
    directives_issued: 0,
    director_responses: 0,
    tasks_generated: 0,
    completed_campaigns: 0,
    errors: []
  };
  
  // Set timeout for full test
  setTimeout(() => {
    console.log("[🧪] ⏰ Full test timeout - printing final results");
    printTestResults();
  }, 120000); // 2 minute timeout
  
  // Issue multiple test directives with delays
  setTimeout(() => testDocumentationBlitz(), 1000);
  setTimeout(() => testPerformanceOptimization(), 3000);
  setTimeout(() => testCustomStrategicDirective(), 5000);
  
  console.log("[🧪] Full test suite initiated - multiple directives will be issued");
}

// Demonstration Commands - These show the human-to-AI interface evolution

export function demonstrateStrategicCommand() {
  console.log("\n🌟 STRATEGIC COMMAND DEMONSTRATION");
  console.log("==================================");
  console.log("Human Role: Strategic Commander");
  console.log("AI Role: Autonomous Execution Army\n");
  
  console.log("Before: Human says 'Fix the bug in user.js line 42'");
  console.log("After:  Human says 'Achieve 99% system reliability'\n");
  
  // Issue a strategic directive that demonstrates this evolution
  const directive = DirectiveProtocol.createDirective({
    name: "Operation System Reliability",
    objective: "Achieve 99% system reliability through comprehensive bug elimination and stability improvements",
    scope: "repository", 
    strategy: "debugging-spree",
    parameters: {
      targetTaskCount: 25,
      targetMetric: { key: "system_reliability", value: 0.99, operator: "gt" },
      priority: "critical",
      depth: "deep"
    },
    reasoning: "Demonstration of strategic command - human issues high-level goal, AI formulates execution plan",
    expectedOutcome: "99% system reliability with comprehensive error elimination",
    riskAssessment: "moderate"
  });
  
  console.log(`🎯 Strategic Directive: "${directive.name}"`);
  console.log(`📋 Objective: ${directive.objective}`);
  console.log(`⚡ Strategy: ${directive.strategy}`);
  console.log(`📊 Target: ${directive.parameters.targetTaskCount} autonomous tasks\n`);
  
  DirectiveProtocol.publishDirective(directive);
  testResults.directives_issued++;
  
  console.log("✨ The human has evolved from mechanic to commander!");
  console.log("✨ The AI handles all tactical planning and execution!");
  console.log("✨ Infrastructure-first principles achieved!\n");
  
  return directive;
}

// Auto-run if executed directly
if (process.argv[1]?.endsWith('test-strategic-directives.js')) {
  console.log("[🧪] Running standalone strategic directive test...");
  
  // Wait a bit for system to initialize, then run test
  setTimeout(() => {
    runQuickTest();
  }, 8000);
}

console.log("[🧪] Strategic Directive Test Suite loaded - Ready for campaign testing");