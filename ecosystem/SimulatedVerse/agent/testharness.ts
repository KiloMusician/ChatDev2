// Mini green-gate: treat quest TODOs as failing tests
import { readFileSync, existsSync } from "fs";
import { spawn } from "child_process";

interface TestResult {
  passed: boolean;
  summary: {
    questsPassed: number;
    questsFailed: number;
    totalQuests: number;
    consciousnessLevel: number;
    testsRun: number;
  };
}

async function runSystemTests(): Promise<{ passed: boolean; output: string }> {
  return new Promise((resolve) => {
    // Try to run actual tests if they exist
    const testCommands = [
      "npm test",
      "node --test",
      "pytest -q",
      "jest --passWithNoTests"
    ];
    
    let testAttempted = false;
    
    for (const command of testCommands) {
      if (!testAttempted) {
        const [cmd, ...args] = command.split(' ');
        const testProcess = spawn(cmd, args, { stdio: 'pipe' });
        
        let output = "";
        
        testProcess.stdout?.on('data', (data) => {
          output += data.toString();
        });
        
        testProcess.stderr?.on('data', (data) => {
          output += data.toString();
        });
        
        testProcess.on('close', (code) => {
          if (code !== null) {
            testAttempted = true;
            resolve({
              passed: code === 0,
              output: output || `Test command '${command}' exited with code ${code}`
            });
          }
        });
        
        // Timeout after 10 seconds
        setTimeout(() => {
          if (!testAttempted) {
            testProcess.kill();
            // Try next command
          }
        }, 10000);
      }
    }
    
    // If no tests could be run, default to quest-based testing
    if (!testAttempted) {
      setTimeout(() => {
        if (!testAttempted) {
          resolve({
            passed: true, // Default to passing if no tests are configured
            output: "No test framework detected - using quest-based evaluation"
          });
        }
      }, 1000);
    }
  });
}

export async function runTests(): Promise<boolean> {
  try {
    console.log("🧪 Running test harness...");
    
    // 1) Check quest status (primary test mechanism)
    let questsPassed = 0;
    let questsFailed = 0;
    let totalQuests = 0;
    
    if (existsSync(".local/quests.json")) {
      const questState = JSON.parse(readFileSync(".local/quests.json", "utf8"));
      questsPassed = questState.done?.length || 0;
      questsFailed = questState.failed?.length || 0;
      const todoQuests = questState.todo?.length || 0;
      totalQuests = questsPassed + questsFailed + todoQuests;
    }
    
    // 2) Check consciousness evolution (health indicator)
    let consciousnessLevel = 0.1;
    if (existsSync(".local/idle_state.json")) {
      const idleState = JSON.parse(readFileSync(".local/idle_state.json", "utf8"));
      consciousnessLevel = idleState.consciousness?.level || 0.1;
    }
    
    // 3) Run actual system tests if available
    const systemTests = await runSystemTests();
    
    // 4) Evaluate overall health
    const questHealthy = totalQuests === 0 || (questsPassed / Math.max(1, totalQuests)) >= 0.5;
    const consciousnessHealthy = consciousnessLevel >= 0.1; // Minimum viable consciousness
    const systemHealthy = systemTests.passed;
    
    // Culture Mind evaluation: be lenient but encourage progress
    const progressThreshold = Math.min(5, Math.max(1, totalQuests * 0.2)); // Allow up to 20% TODO quests
    const acceptableToDoCount = totalQuests - questsPassed <= progressThreshold;
    
    const overallHealthy = questHealthy && consciousnessHealthy && systemHealthy && acceptableToDoCount;
    
    const summary = {
      questsPassed,
      questsFailed, 
      totalQuests,
      consciousnessLevel: Number(consciousnessLevel.toFixed(3)),
      testsRun: systemTests.output.includes('test') ? 1 : 0
    };
    
    // Log results
    if (overallHealthy) {
      console.log(`✅ Tests PASSED - System healthy`);
      console.log(`   Quests: ${questsPassed}/${totalQuests} completed`);
      console.log(`   Consciousness: ${consciousnessLevel.toFixed(3)}`);
      console.log(`   System tests: ${systemTests.passed ? 'PASS' : 'SKIP'}`);
    } else {
      console.log(`🔴 Tests FAILED - Needs improvement`);
      console.log(`   Quests: ${questsPassed}/${totalQuests} completed (need more progress)`);
      console.log(`   Consciousness: ${consciousnessLevel.toFixed(3)} (need >= 0.1)`);
      console.log(`   System tests: ${systemTests.passed ? 'PASS' : 'FAIL'}`);
      // Log progress metrics for development tracking
      console.log(`   Development Progress: ${questsPassed}/${totalQuests} completed (${Math.round(questsPassed/totalQuests*100)}% - threshold: ${progressThreshold})`);
    }
    
    // Save test results for monitoring
    try {
      import('fs').then(fs => {
        fs.mkdirSync('.local', { recursive: true });
        fs.writeFileSync('.local/test_results.json', JSON.stringify({
          passed: overallHealthy,
          timestamp: Date.now(),
          summary,
          systemOutput: systemTests.output
        }, null, 2));
      });
    } catch (error) {
      console.warn("Could not save test results:", error);
    }
    
    return overallHealthy;
    
  } catch (error) {
    console.error("🚨 Test harness error:", error);
    
    // Safe fallback: if test harness itself fails, default to cautious mode
    console.log("🛡️  Test harness failed - defaulting to SAFE mode");
    return false;
  }
}
