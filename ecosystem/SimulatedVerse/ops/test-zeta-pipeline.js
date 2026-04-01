// ops/test-zeta-pipeline.js
// Test script to validate the complete Zeta-Driver autonomous development pipeline

import { councilBus } from "../packages/council/events/eventBus.js";
import ZetaProtocol, { ZetaTemplates } from "./zeta-protocol.js";

/**
 * Test the complete autonomous development pipeline:
 * 1. Create todo.zeta task
 * 2. Zeta-Driver picks it up
 * 3. ChatDev session created
 * 4. Testing Chamber execution
 * 5. Integration back to main repo
 */

console.log("[🧪] Starting Zeta-Driver pipeline test...");

// Track test progress
let testResults = {
  task_published: false,
  zeta_driver_received: false,
  chatdev_session_created: false,
  testing_chamber_queued: false,
  task_completed: false,
  errors: []
};

// Listen for pipeline events
councilBus.subscribe('zeta_driver.task_queued', (event) => {
  console.log("[🧪] ✅ Zeta-Driver received task:", event.payload.title);
  testResults.zeta_driver_received = true;
});

councilBus.subscribe('chatdev.session_created', (event) => {
  console.log("[🧪] ✅ ChatDev session created:", event.payload.title);
  testResults.chatdev_session_created = true;
});

councilBus.subscribe('testing_chamber.task_queued', (event) => {
  console.log("[🧪] ✅ Testing Chamber task queued:", event.payload.task.title);
  testResults.testing_chamber_queued = true;
});

councilBus.subscribe('zeta_driver.task_completed', (event) => {
  console.log("[🧪] ✅ Zeta task completed successfully!");
  testResults.task_completed = true;
  printTestResults();
});

councilBus.subscribe('zeta_driver.task_failed', (event) => {
  console.log("[🧪] ❌ Zeta task failed:", event.payload.error);
  testResults.errors.push(event.payload.error);
  printTestResults();
});

function printTestResults() {
  console.log("\n[🧪] ZETA-DRIVER PIPELINE TEST RESULTS:");
  console.log("=======================================");
  console.log(`Task Published: ${testResults.task_published ? '✅' : '❌'}`);
  console.log(`Zeta-Driver Received: ${testResults.zeta_driver_received ? '✅' : '❌'}`);
  console.log(`ChatDev Session: ${testResults.chatdev_session_created ? '✅' : '❌'}`);
  console.log(`Testing Chamber: ${testResults.testing_chamber_queued ? '✅' : '❌'}`);
  console.log(`Task Completed: ${testResults.task_completed ? '✅' : '❌'}`);
  
  if (testResults.errors.length > 0) {
    console.log("\nErrors:");
    testResults.errors.forEach(error => console.log(`  - ${error}`));
  }
  
  const success = testResults.task_completed && testResults.errors.length === 0;
  console.log(`\nOverall Result: ${success ? '✅ SUCCESS' : '❌ FAILED'}`);
  console.log("=======================================\n");
}

// Test functions
export function testDocumentationTask() {
  console.log("[🧪] Creating test documentation task...");
  
  const task = ZetaTemplates.enhanceDocumentation([
    'ops/zeta-driver.js',
    'ops/zeta-protocol.js'
  ]);
  
  task.title = "Test Documentation Task";
  task.description = "Generate comprehensive documentation for the Zeta-Driver autonomous development system";
  task.context.test_run = true;
  
  ZetaProtocol.publishTask(task);
  testResults.task_published = true;
  
  console.log("[🧪] Test documentation task published:", task.title);
  return task;
}

export function testRefactorTask() {
  console.log("[🧪] Creating test refactor task...");
  
  const task = ZetaTemplates.improveModularity([
    'ops/zeta-driver.js'
  ]);
  
  task.title = "Test Refactor Task";
  task.description = "Refactor Zeta-Driver for improved modularity and maintainability";
  task.context.test_run = true;
  task.priority = 3; // Lower priority for testing
  
  ZetaProtocol.publishTask(task);
  testResults.task_published = true;
  
  console.log("[🧪] Test refactor task published:", task.title);
  return task;
}

export function testOptimizationTask() {
  console.log("[🧪] Creating test optimization task...");
  
  const task = ZetaTemplates.optimizePerformance([
    'ops/autonomous-loop.js'
  ]);
  
  task.title = "Test Optimization Task";
  task.description = "Optimize autonomous loop performance and resource usage";
  task.context.test_run = true;
  task.priority = 4;
  
  ZetaProtocol.publishTask(task);
  testResults.task_published = true;
  
  console.log("[🧪] Test optimization task published:", task.title);
  return task;
}

export function testCustomTask() {
  console.log("[🧪] Creating custom test task...");
  
  const task = ZetaProtocol.createTask({
    title: "Test Custom Zeta Task",
    description: "This is a custom test task to validate the complete Zeta-Driver pipeline from todo.zeta event to ChatDev execution to Testing Chamber integration",
    type: "enhancement",
    target_files: ["ops/test-zeta-pipeline.js"],
    priority: 2,
    context: {
      test_run: true,
      test_type: "custom_validation",
      expected_outcome: "Complete pipeline execution"
    },
    success_criteria: [
      "Task received by Zeta-Driver",
      "ChatDev session initiated",
      "Testing Chamber execution started",
      "No critical errors during execution"
    ],
    requester: "pipeline_test",
    safety_mode: "testing"
  });
  
  ZetaProtocol.publishTask(task);
  testResults.task_published = true;
  
  console.log("[🧪] Custom test task published:", task.title);
  return task;
}

// Manual test runner
export function runTest(testType = 'documentation') {
  console.log(`[🧪] Running ${testType} test...`);
  
  // Reset test results
  testResults = {
    task_published: false,
    zeta_driver_received: false,
    chatdev_session_created: false,
    testing_chamber_queued: false,
    task_completed: false,
    errors: []
  };
  
  // Set timeout for test
  setTimeout(() => {
    if (!testResults.task_completed && testResults.errors.length === 0) {
      console.log("[🧪] ⏰ Test timeout - printing intermediate results");
      printTestResults();
    }
  }, 60000); // 1 minute timeout
  
  // Run the appropriate test
  switch (testType) {
    case 'documentation':
      return testDocumentationTask();
    case 'refactor':
      return testRefactorTask();
    case 'optimization':
      return testOptimizationTask();
    case 'custom':
      return testCustomTask();
    default:
      console.error("[🧪] Unknown test type:", testType);
      return null;
  }
}

// Auto-run if executed directly
if (process.argv[1]?.endsWith('test-zeta-pipeline.js')) {
  console.log("[🧪] Running standalone Zeta-Driver pipeline test...");
  
  // Wait a bit for system to initialize, then run test
  setTimeout(() => {
    runTest('custom');
  }, 5000);
}