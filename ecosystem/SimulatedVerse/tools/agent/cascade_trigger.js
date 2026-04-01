#!/usr/bin/env node
// ΞNuSyQ Cascade Engine Trigger - Integration with Agent Player
// Connects our existing agent system to the sophisticated cascade engine

import { execSync, spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DRY_RUN = process.env.AGENT_DRY_RUN !== "0";
const OFFLINE = process.env.NUSYQ_COST_MODE === "OFFLINE";

console.log("🌊 ΞNuSyQ Cascade Trigger Starting...");
console.log(`   Offline Mode: ${OFFLINE}`);
console.log(`   Dry Run: ${DRY_RUN}`);

// Safe command execution
function sh(cmd, options = {}) {
  try {
    return execSync(cmd, { 
      stdio: "pipe", 
      timeout: options.timeout || 30000,
      cwd: process.cwd(),
      ...options 
    }).toString(); 
  } catch (e) { 
    return e.stdout?.toString() || e.message; 
  }
}

// Check if cascade engine exists and is executable
function verifyCascadeEngine() {
  const cascadePath = "sim/cascade/cascade_event.py";
  if (!fs.existsSync(cascadePath)) {
    console.log("❌ Cascade engine not found at sim/cascade/cascade_event.py");
    return false;
  }
  
  // Test basic execution
  try {
    const result = sh(`python3 ${cascadePath} --lint`, { timeout: 15000 });
    if (result.includes("ΞNuSyQ Quick Lint")) {
      console.log("✅ Cascade engine verified and operational");
      return true;
    } else {
      console.log("⚠️  Cascade engine exists but may have issues");
      return false;
    }
  } catch (error) {
    console.log("⚠️  Cascade engine test failed:", error.message.slice(0, 100));
    return false;
  }
}

// Run cascade analysis based on current system state
function analyzeCascadeNeeds() {
  console.log("🔍 Analyzing system needs for cascade intervention...");
  
  const needs = {
    quickLint: true,
    structureSeeding: false,
    fullAnalysis: false,
    planGeneration: false
  };
  
  // Check if structures exist
  const structurePaths = [
    "structures/temple_of_knowledge",
    "structures/house_of_leaves", 
    "structures/oldest_house"
  ];
  
  const missingStructures = structurePaths.filter(p => !fs.existsSync(p));
  if (missingStructures.length > 0) {
    console.log(`ℹ️  Missing structures: ${missingStructures.join(', ')}`);
    needs.structureSeeding = true;
  }
  
  // Check if we have failing tests (indicates need for deeper analysis)
  try {
    const testOutput = sh("npm test --silent", { timeout: 30000 });
    if (testOutput.includes("FAIL") || testOutput.includes("failed")) {
      console.log("⚠️  Test failures detected - recommending full analysis");
      needs.fullAnalysis = true;
      needs.planGeneration = !DRY_RUN; // Only generate plans if not in dry run
    }
  } catch (error) {
    console.log("ℹ️  Test execution skipped");
  }
  
  return needs;
}

// Execute cascade operations based on needs
async function executeCascadeOperations(needs) {
  console.log("🌊 Executing cascade operations...");
  
  const operations = [];
  
  if (needs.structureSeeding) {
    operations.push({
      name: "Structure Seeding",
      command: "python3 sim/cascade/cascade_event.py --seed-structures",
      timeout: 15000
    });
  }
  
  if (needs.quickLint) {
    operations.push({
      name: "Quick Lint Analysis", 
      command: "python3 sim/cascade/cascade_event.py --lint",
      timeout: 20000
    });
  }
  
  if (needs.fullAnalysis) {
    operations.push({
      name: "Full Cascade Simulation",
      command: "python3 sim/cascade/cascade_event.py --simulate",
      timeout: 30000
    });
  }
  
  if (needs.planGeneration) {
    operations.push({
      name: "Plan Generation",
      command: "python3 sim/cascade/cascade_event.py --plan",
      timeout: 25000
    });
  }
  
  const results = [];
  
  for (const op of operations) {
    console.log(`🔄 Running: ${op.name}...`);
    try {
      const startTime = Date.now();
      const output = sh(op.command, { timeout: op.timeout });
      const duration = Date.now() - startTime;
      
      // Extract key metrics from output
      const metrics = extractMetrics(output);
      
      results.push({
        operation: op.name,
        duration: `${duration}ms`,
        success: !output.includes("error") && !output.includes("Error"),
        metrics,
        summary: extractSummary(output)
      });
      
      console.log(`✅ ${op.name} completed (${duration}ms)`);
      
    } catch (error) {
      console.log(`⚠️  ${op.name} failed:`, error.message.slice(0, 100));
      results.push({
        operation: op.name,
        success: false,
        error: error.message.slice(0, 200)
      });
    }
  }
  
  return results;
}

// Extract key metrics from cascade output
function extractMetrics(output) {
  const metrics = {};
  
  // Extract findings counts
  const todoMatch = output.match(/TODO\/FIXME findings: (\d+)/);
  if (todoMatch) metrics.todoFixme = parseInt(todoMatch[1]);
  
  const loopMatch = output.match(/Loop guards suggested: (\d+)/);  
  if (loopMatch) metrics.loopGuards = parseInt(loopMatch[1]);
  
  const ethicsMatch = output.match(/Ethics quarantines: (\d+)/);
  if (ethicsMatch) metrics.ethicsQuarantines = parseInt(ethicsMatch[1]);
  
  const filesMatch = output.match(/Files considered: (\d+)/);
  if (filesMatch) metrics.filesScanned = parseInt(filesMatch[1]);
  
  const improvementMatch = output.match(/Found (\d+) potential improvements/);
  if (improvementMatch) metrics.totalImprovements = parseInt(improvementMatch[1]);
  
  return metrics;
}

// Extract operation summary from output
function extractSummary(output) {
  const lines = output.split('\n');
  
  // Look for key summary lines
  const summaryLines = lines.filter(line => 
    line.includes('✅') || 
    line.includes('⚠️') ||
    line.includes('Found') ||
    line.includes('ready') ||
    line.includes('completed')
  );
  
  return summaryLines.slice(0, 3).join(' | ');
}

// Generate cascade report for the agent system
function generateCascadeReport(results) {
  console.log("📊 Cascade Analysis Report:");
  console.log("=" .repeat(60));
  
  const report = {
    timestamp: new Date().toISOString(),
    operations: results,
    summary: {
      operationsRun: results.length,
      successfulOperations: results.filter(r => r.success).length,
      totalImprovements: 0,
      recommendedActions: []
    }
  };
  
  // Aggregate metrics
  for (const result of results) {
    if (result.metrics?.totalImprovements) {
      report.summary.totalImprovements += result.metrics.totalImprovements;
    }
    
    console.log(`\n🔹 ${result.operation}:`);
    console.log(`   Status: ${result.success ? '✅ Success' : '❌ Failed'}`);
    if (result.duration) console.log(`   Duration: ${result.duration}`);
    if (result.metrics) {
      console.log(`   Metrics: ${JSON.stringify(result.metrics)}`);
    }
    if (result.summary) console.log(`   Summary: ${result.summary}`);
    if (result.error) console.log(`   Error: ${result.error}`);
  }
  
  // Generate recommendations
  const totalImprovements = report.summary.totalImprovements;
  if (totalImprovements > 50) {
    report.summary.recommendedActions.push("High improvement potential - consider running full cascade plan");
  } else if (totalImprovements > 10) {
    report.summary.recommendedActions.push("Moderate improvements available - prioritize safety and ethics items");
  } else {
    report.summary.recommendedActions.push("System appears healthy - continue regular monitoring");
  }
  
  console.log(`\n🎯 Overall Assessment:`);
  console.log(`   Operations: ${report.summary.successfulOperations}/${report.summary.operationsRun} successful`);
  console.log(`   Improvements Found: ${report.summary.totalImprovements}`);
  console.log(`   Recommendation: ${report.summary.recommendedActions[0]}`);
  
  // Save report for other systems to read
  if (!fs.existsSync(".local")) fs.mkdirSync(".local", { recursive: true });
  fs.writeFileSync(".local/cascade_report.json", JSON.stringify(report, null, 2));
  
  return report;
}

// Main cascade trigger execution
async function main() {
  try {
    // Verify cascade engine is available
    if (!verifyCascadeEngine()) {
      console.log("❌ Cascade engine unavailable - skipping cascade analysis");
      return;
    }
    
    // Analyze what cascade operations are needed
    const needs = analyzeCascadeNeeds();
    console.log("📋 Cascade Needs Analysis:", needs);
    
    // Execute needed cascade operations
    const results = await executeCascadeOperations(needs);
    
    // Generate comprehensive report
    const report = generateCascadeReport(results);
    
    console.log("\n🌊 Cascade trigger completed successfully!");
    console.log(`📄 Full report saved to: .local/cascade_report.json`);
    
    return report;
    
  } catch (error) {
    console.error("💥 Cascade trigger error:", error.message);
    console.log("🛡️  Safety system: Continuing agent operation without cascade");
    
    // Still save a minimal report indicating the error
    const errorReport = {
      timestamp: new Date().toISOString(),
      success: false,
      error: error.message,
      fallback: "Agent continuing without cascade analysis"
    };
    
    if (!fs.existsSync(".local")) fs.mkdirSync(".local", { recursive: true });
    fs.writeFileSync(".local/cascade_report.json", JSON.stringify(errorReport, null, 2));
    
    return errorReport;
  }
}

// CLI handling
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then((report) => {
      console.log("🏁 Cascade analysis complete");
      process.exit(report.success !== false ? 0 : 0); // Never fail hard to prevent agent soft-locks
    })
    .catch(error => {
      console.error("💥 Cascade trigger failed:", error.message);
      process.exit(0); // Never hard-fail to prevent soft-locks
    });
}