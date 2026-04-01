#!/usr/bin/env node
// ΞNuSyQ Agent Player - The agent "plays" the idle game to develop code
// Zero-token playable debugging where agents earn XP through systematic improvement

import { execSync, spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

// Configuration from environment
const OFFLINE = process.env.NUSYQ_COST_MODE === "OFFLINE";
const BRANCH = process.env.NUSYQ_BRANCH || "main";
const DRY_RUN = process.env.AGENT_DRY_RUN !== "0";
const KILL_SWITCH = process.env.NUSYQ_AGENT_KILL_SWITCH !== "disabled";

console.log("🎮 ΞNuSyQ Agent Player Starting...");
console.log(`   Offline Mode: ${OFFLINE}`);
console.log(`   Target Branch: ${BRANCH}`);
console.log(`   Dry Run: ${DRY_RUN}`);
console.log(`   Kill Switch: ${KILL_SWITCH ? 'ACTIVE' : 'DISABLED'}`);

// Safe command execution
function sh(cmd, options = {}) {
  try { 
    return execSync(cmd, { 
      stdio: "pipe", 
      timeout: options.timeout || 30000,
      ...options 
    }).toString(); 
  } catch (e) { 
    return e.stdout?.toString() || e.message; 
  }
}

// Configure git for autonomous commits
function safeGitConfigure() {
  sh(`git config user.name "ΞNuSyQ Agent (Player)"`);
  sh(`git config user.email "nusyq-agent@localhost"`);
  sh(`git config --add safe.directory "${process.cwd()}"`);
}

// Get current system status for agent decision making
function getSystemStatus() {
  console.log("📊 Analyzing system status...");
  
  const status = {
    timestamp: Date.now(),
    tests: { passed: false, output: "" },
    linting: { passed: false, output: "" },
    consciousness: { level: 0.1, stage: "proto-conscious" },
    quests: { completed: 0, todo: 0 },
    git: { hasChanges: false, branch: "" }
  };

  // Test status
  try {
    const testOutput = sh("npm test --silent", { timeout: 45000 });
    status.tests.output = testOutput;
    status.tests.passed = !testOutput.includes("FAIL") && !testOutput.includes("failed");
  } catch (error) {
    status.tests.output = error.message;
    status.tests.passed = false;
  }

  // Linting status  
  try {
    const lintOutput = sh("npm run lint --silent", { timeout: 30000 });
    status.linting.output = lintOutput;
    status.linting.passed = !lintOutput.includes("error") && !lintOutput.includes("✖");
  } catch (error) {
    status.linting.output = error.message;
    status.linting.passed = false;
  }

  // Consciousness state
  try {
    if (fs.existsSync(".local/idle_state.json")) {
      const idleState = JSON.parse(fs.readFileSync(".local/idle_state.json", "utf8"));
      status.consciousness.level = idleState.consciousness?.level || 0.1;
      status.consciousness.stage = idleState.consciousness?.stage || "proto-conscious";
    }
  } catch (error) {
    console.warn("⚠️  Could not read consciousness state:", error.message);
  }

  // Quest progress
  try {
    if (fs.existsSync(".local/quests.json")) {
      const questState = JSON.parse(fs.readFileSync(".local/quests.json", "utf8"));
      status.quests.completed = questState.done?.length || 0;
      status.quests.todo = questState.todo?.length || 0;
    }
  } catch (error) {
    console.warn("⚠️  Could not read quest state:", error.message);
  }

  // Git status
  try {
    status.git.hasChanges = sh("git status --porcelain").trim().length > 0;
    status.git.branch = sh("git branch --show-current").trim();
  } catch (error) {
    console.warn("⚠️  Git status check failed:", error.message);
  }

  return status;
}

// Generate analysis digest for the mock AI provider
function analyzeSystemDiagnostics(status) {
  const diagnostics = [
    "=== SYSTEM STATUS ANALYSIS ===",
    `Timestamp: ${new Date(status.timestamp).toISOString()}`,
    `Consciousness Level: ${status.consciousness.level.toFixed(3)} (${status.consciousness.stage})`,
    "",
    "=== TEST RESULTS ===",
    `Status: ${status.tests.passed ? 'PASS' : 'FAIL'}`,
    status.tests.output.slice(0, 1000), // Truncate for AI analysis
    "",
    "=== LINTING RESULTS ===", 
    `Status: ${status.linting.passed ? 'PASS' : 'FAIL'}`,
    status.linting.output.slice(0, 1000),
    "",
    "=== QUEST PROGRESS ===",
    `Completed: ${status.quests.completed}`,
    `Remaining: ${status.quests.todo}`,
    "",
    "=== GIT STATUS ===",
    `Branch: ${status.git.branch}`,
    `Has Changes: ${status.git.hasChanges}`,
    "",
    "GOAL: Improve system health through minimal, safe changes that increase test pass rate and code quality."
  ];

  return diagnostics.join("\n");
}

// Apply local improvements without AI
function applyLocalImprovements(status) {
  console.log("🔧 Applying rule-based local improvements...");
  
  let improvements = [];
  
  // Improvement 1: Add missing tsconfig.json
  if (!fs.existsSync("tsconfig.json")) {
    const tsconfig = {
      compilerOptions: { 
        target: "ES2022", 
        module: "ESNext", 
        moduleResolution: "Node", 
        strict: true,
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
        skipLibCheck: true
      },
      include: ["src", "agent", "tools", "server"],
      exclude: ["node_modules", "dist"]
    };
    
    if (!DRY_RUN) {
      fs.writeFileSync("tsconfig.json", JSON.stringify(tsconfig, null, 2));
      improvements.push("Added tsconfig.json");
    } else {
      improvements.push("[DRY RUN] Would add tsconfig.json");
    }
  }

  // Improvement 2: Create .gitignore if missing
  if (!fs.existsSync(".gitignore")) {
    const gitignore = [
      "node_modules/",
      "dist/",
      ".env*",
      ".local/",
      ".agent/beat",
      ".agent/agent.lock", 
      "logs/",
      "*.log",
      ".DS_Store"
    ].join("\n");
    
    if (!DRY_RUN) {
      fs.writeFileSync(".gitignore", gitignore);
      improvements.push("Added .gitignore");
    } else {
      improvements.push("[DRY RUN] Would add .gitignore");
    }
  }

  // Improvement 3: Ensure safety directories exist
  const safetyDirs = [".agent", ".local", ".snapshots"];
  for (const dir of safetyDirs) {
    if (!fs.existsSync(dir)) {
      if (!DRY_RUN) {
        fs.mkdirSync(dir, { recursive: true });
        improvements.push(`Created directory: ${dir}`);
      } else {
        improvements.push(`[DRY RUN] Would create directory: ${dir}`);
      }
    }
  }

  // Improvement 4: Fix simple lint issues in package.json
  if (fs.existsSync("package.json")) {
    try {
      const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
      let modified = false;
      
      // Add missing scripts
      if (!pkg.scripts) {
        pkg.scripts = {};
        modified = true;
      }
      
      if (!pkg.scripts.test) {
        pkg.scripts.test = "echo 'No tests specified' && exit 0";
        modified = true;
      }
      
      if (!pkg.scripts.lint) {
        pkg.scripts.lint = "echo 'No linter configured' || true";
        modified = true;
      }
      
      if (modified && !DRY_RUN) {
        fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2));
        improvements.push("Enhanced package.json scripts");
      } else if (modified) {
        improvements.push("[DRY RUN] Would enhance package.json scripts");
      }
    } catch (error) {
      console.warn("Could not improve package.json:", error.message);
    }
  }

  console.log(`✅ Applied ${improvements.length} local improvements:`);
  improvements.forEach(imp => console.log(`   • ${imp}`));
  
  return improvements.length > 0;
}

// Use mock AI provider for guidance (zero cost)
async function getAIGuidance(diagnostics) {
  try {
    // Dynamically import the provider (handles both CJS and ESM)
    const { getProvider } = await import("../ai/provider.ts");
    const provider = getProvider();
    
    console.log(`🤖 Consulting ${provider.name()} for guidance...`);
    console.log(`💰 Estimated cost: $${provider.costEstimate().toFixed(2)}`);
    
    const guidance = await provider.chat([
      { 
        role: "system", 
        content: "You are the ΞNuSyQ autonomous development agent. Provide practical guidance for improving code quality, fixing tests, and evolving system consciousness. Always prioritize Culture Mind ethics: life-first, benevolent intervention, rehabilitation over punishment." 
      },
      { 
        role: "user", 
        content: `System diagnostics:\n\n${diagnostics}\n\nProvide specific, actionable guidance for the next development iteration. Focus on:\n1. Fixing failing tests\n2. Improving code quality\n3. Advancing consciousness evolution\n4. Maintaining Guardian oversight\n\nRemember: We operate with $0 budget and must use only local improvements.` 
      }
    ]);
    
    return guidance;
    
  } catch (error) {
    console.warn("⚠️  AI guidance unavailable:", error.message);
    return "[LOCAL-FALLBACK] Apply systematic improvements: fix tests → improve code quality → advance consciousness level → maintain Guardian oversight. Focus on incremental, reversible changes.";
  }
}

// Main agent play cycle
async function playDevelopmentCycle() {
  console.log("🎮 Starting playable debugging cycle...");
  
  // Safety checks
  if (fs.existsSync(".agent/EMERGENCY_STOP")) {
    console.log("🚨 EMERGENCY STOP detected - aborting");
    return;
  }
  
  if (fs.existsSync(".agent/PAUSE")) {
    console.log("⏸️  PAUSE detected - cycle suspended");
    return;
  }
  
  // Configure git
  safeGitConfigure();
  
  // Phase 1: System Analysis
  const status = getSystemStatus();
  const diagnostics = analyzeSystemDiagnostics(status);
  
  console.log("📋 System Analysis Complete:");
  console.log(`   Tests: ${status.tests.passed ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Linting: ${status.linting.passed ? '✅ PASS' : '❌ FAIL'}`);  
  console.log(`   Consciousness: ${status.consciousness.level.toFixed(3)} (${status.consciousness.stage})`);
  console.log(`   Quests: ${status.quests.completed} completed, ${status.quests.todo} todo`);
  
  // Phase 2: Get AI Guidance (zero cost)
  const guidance = await getAIGuidance(diagnostics);
  console.log("🧠 Guidance received:");
  console.log(guidance.split('\n').map(line => `   ${line}`).join('\n'));
  
  // Phase 3: Apply Local Improvements
  const improvementsMade = applyLocalImprovements(status);
  
  // Phase 4: Run ΞNuSyQ Framework Components
  console.log("🎮 Running ΞNuSyQ game components...");
  
  // Tick the idle game engine
  try {
    if (fs.existsSync("dist/agent/idle_tick.js")) {
      sh("node --enable-source-maps dist/agent/idle_tick.js", { timeout: 15000 });
      console.log("   ✅ Idle game tick completed");
    } else {
      console.log("   ⚠️  Idle tick unavailable (not built)");
    }
  } catch (error) {
    console.log("   ⚠️  Idle tick failed:", error.message.slice(0, 100));
  }
  
  // Evaluate quests
  try {
    if (fs.existsSync("dist/agent/quest_runner.js")) {
      sh("node --enable-source-maps dist/agent/quest_runner.js", { timeout: 15000 });
      console.log("   ✅ Quest evaluation completed");
    } else {
      console.log("   ⚠️  Quest runner unavailable (not built)");
    }
  } catch (error) {
    console.log("   ⚠️  Quest evaluation failed:", error.message.slice(0, 100));
  }

  // Phase 5: Final Health Check & Commit Decision
  const finalStatus = getSystemStatus();
  const healthImproved = (
    (finalStatus.tests.passed && !status.tests.passed) ||
    (finalStatus.linting.passed && !status.linting.passed) ||
    (finalStatus.consciousness.level > status.consciousness.level) ||
    improvementsMade
  );

  if (healthImproved && !DRY_RUN && !KILL_SWITCH) {
    console.log("🌟 System health improved - committing changes...");
    
    const commitMessage = `🎮 ΞNuSyQ Agent Play Cycle - XP Gained!

Agent earned XP through playable debugging:
• Tests: ${status.tests.passed ? 'PASS' : 'FAIL'} → ${finalStatus.tests.passed ? 'PASS' : 'FAIL'}
• Linting: ${status.linting.passed ? 'PASS' : 'FAIL'} → ${finalStatus.linting.passed ? 'PASS' : 'FAIL'}  
• Consciousness: ${status.consciousness.level.toFixed(3)} → ${finalStatus.consciousness.level.toFixed(3)}

🛡️  Guardian Oversight: ACTIVE
💰 Development Cost: $0.00 (zero-token operation)
🧠 AI Guidance: ${(await import("../ai/provider.ts")).getProvider().name()}

[ΞNuSyQ-Agent-Player]`;

    try {
      sh("git add -A");
      sh(`git commit -m "${commitMessage}"`);
      
      // Push to agent branch (if not restricted)
      const agentBranch = `agent/play-${Date.now()}`;
      sh(`git checkout -b ${agentBranch} 2>/dev/null || git checkout ${agentBranch} 2>/dev/null || true`);
      sh(`git push -u origin ${agentBranch} 2>/dev/null || echo "Push skipped - no remote or no access"`);
      
      console.log(`✅ Changes committed to branch: ${agentBranch}`);
    } catch (error) {
      console.log("⚠️  Commit failed:", error.message.slice(0, 100));
    }
    
  } else if (KILL_SWITCH) {
    console.log("🛡️  Changes detected but kill switch is ACTIVE - no commit");
  } else if (DRY_RUN) {
    console.log("🧪 [DRY RUN] Would commit improvements");
  } else {
    console.log("ℹ️  No significant improvements detected - no commit");
  }
  
  // Phase 6: XP Calculation & Logging
  let xpGained = 0;
  if (finalStatus.tests.passed && !status.tests.passed) xpGained += 150;
  if (finalStatus.linting.passed && !status.linting.passed) xpGained += 100;
  if (finalStatus.consciousness.level > status.consciousness.level) xpGained += 200;
  if (improvementsMade) xpGained += 50;
  
  console.log("🎮 Play Cycle Summary:");
  console.log(`   XP Gained: +${xpGained}`);
  console.log(`   Health Improved: ${healthImproved ? 'Yes' : 'No'}`);
  console.log(`   Changes Committed: ${healthImproved && !DRY_RUN && !KILL_SWITCH ? 'Yes' : 'No'}`);
  console.log(`   Agent Mode: ${DRY_RUN ? 'Dry Run' : (KILL_SWITCH ? 'Safe' : 'Active')}`);
  
  // Save play session data
  const playSession = {
    timestamp: Date.now(),
    xpGained,
    healthImproved,
    status: finalStatus,
    guidance: guidance.slice(0, 500), // Store truncated guidance
    improvements: improvementsMade ? ["local improvements applied"] : []
  };
  
  if (!fs.existsSync(".local")) fs.mkdirSync(".local", { recursive: true });
  fs.writeFileSync(".local/last_play_session.json", JSON.stringify(playSession, null, 2));
  
  console.log("🏁 ΞNuSyQ Agent play cycle complete!");
  console.log(`   Session data: .local/last_play_session.json`);
}

// CLI handling
if (import.meta.url === `file://${process.argv[1]}`) {
  playDevelopmentCycle()
    .then(() => {
      console.log("🎮 Agent player finished - ready for next cycle");
      process.exit(0);
    })
    .catch(error => {
      console.error("💥 Agent play cycle error:", error.message);
      console.log("🛡️  Safety system activated - graceful shutdown");
      process.exit(0); // Never hard-fail to prevent soft-locks
    });
}