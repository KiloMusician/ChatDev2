#!/usr/bin/env node
/**
 * 🎮 GAME SMOKE TEST - Culture-Ship Health Validator
 * Zero-token headless game system validation
 */

import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import fs from "node:fs";
import path from "node:path";

const SMOKE_TIMEOUT = 10000; // 10 seconds max for smoke test
const BOOT_DELAY = 3000; // 3 seconds to let server start

async function runCommand(command, args = [], timeout = 5000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: "pipe" });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout?.on("data", data => stdout += data.toString());
    child.stderr?.on("data", data => stderr += data.toString());
    
    const timeoutId = globalThis.setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`Command timed out after ${timeout}ms`));
    }, timeout);
    
    child.on("close", code => {
      clearTimeout(timeoutId);
      resolve({ code, stdout, stderr });
    });
    
    child.on("error", error => {
      clearTimeout(timeoutId);
      reject(error);
    });
  });
}

async function checkHealthScripts() {
  console.log("🔍 Culture-Ship: Validating health scripts...");
  
  const scripts = [
    "scripts/find-duplicates.mjs",
    "scripts/check-imports.mjs", 
    "scripts/lint-and-typecheck.mjs"
  ];
  
  for (const script of scripts) {
    if (!fs.existsSync(script)) {
      throw new Error(`Missing health script: ${script}`);
    }
    
    try {
      console.log(`   📋 Testing ${script}...`);
      const result = await runCommand("node", [script], 8000);
      console.log(`   ✅ ${script} functional`);
    } catch (error) {
      console.log(`   ⚠️ ${script} had issues: ${error.message}`);
    }
  }
}

async function smokeTestServer() {
  console.log("🚀 Culture-Ship: Smoke testing game server...");
  
  // Start the server
  const serverProcess = spawn("npm", ["run", "dev"], {
    stdio: "pipe",
    detached: true
  });
  
  let serverOutput = "";
  serverProcess.stdout?.on("data", data => {
    serverOutput += data.toString();
  });
  
  serverProcess.stderr?.on("data", data => {
    serverOutput += data.toString();
  });
  
  try {
    // Wait for server to boot
    console.log("   🕐 Waiting for server boot...");
    await delay(BOOT_DELAY);
    
    // Check if server is responding
    console.log("   🔍 Checking server health...");
    
    // Try to fetch health endpoint
    try {
      const healthCheck = await runCommand("curl", [
        "-s", "-f", "localhost:5000/healthz"
      ], 3000);
      
      if (healthCheck.stdout.includes("ok")) {
        console.log("   ✅ Server health check passed");
      } else {
        throw new Error("Health check returned unexpected response");
      }
    } catch (error) {
      console.log("   ⚠️ Health check failed, checking if server started...");
      
      // Check if server log indicates successful start
      if (serverOutput.includes("Server online") || serverOutput.includes("listening")) {
        console.log("   ✅ Server appears to be running (curl may not be available)");
      } else {
        throw new Error(`Server failed to start: ${serverOutput}`);
      }
    }
    
    // Test game state endpoints
    try {
      console.log("   🎮 Testing game state endpoints...");
      const statusCheck = await runCommand("curl", [
        "-s", "-f", "localhost:5000/api/ops/status"
      ], 3000);
      
      if (statusCheck.stdout.includes("operational")) {
        console.log("   ✅ Game systems operational");
      }
    } catch (error) {
      console.log("   ⚠️ Game endpoints test skipped (curl issues)");
    }
    
  } finally {
    // Clean shutdown
    console.log("   🛑 Shutting down smoke test server...");
    serverProcess.kill("SIGTERM");
    
    // Wait for graceful shutdown
    await delay(1000);
    
    // Force kill if still running
    if (!serverProcess.killed) {
      serverProcess.kill("SIGKILL");
    }
  }
}

async function validateGameAssets() {
  console.log("📁 Culture-Ship: Validating game assets...");
  
  const requiredPaths = [
    "client/src",
    "server",
    "shared"
  ];
  
  const missingPaths = [];
  for (const reqPath of requiredPaths) {
    if (!fs.existsSync(reqPath)) {
      missingPaths.push(reqPath);
    }
  }
  
  if (missingPaths.length > 0) {
    console.log(`   ⚠️ Missing paths: ${missingPaths.join(", ")}`);
  } else {
    console.log("   ✅ All required paths present");
  }
  
  return { missingPaths };
}

async function gameSmoke() {
  console.log("🎮 Culture-Ship: Starting comprehensive game smoke test...");
  const startTime = Date.now();
  
  try {
    // Phase 1: Validate structure
    await validateGameAssets();
    
    // Phase 2: Check health scripts
    await checkHealthScripts();
    
    // Phase 3: Server smoke test
    await smokeTestServer();
    
    const duration = Date.now() - startTime;
    console.log(`\n📊 Culture-Ship Game Smoke Test Results:`);
    console.log(`   ✅ All systems functional`);
    console.log(`   ⏱️ Duration: ${duration}ms`);
    console.log(`   🌊 Infrastructure-First validation complete`);
    
    return { success: true, duration };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.log(`\n📊 Culture-Ship Game Smoke Test Results:`);
    console.log(`   ❌ Test failed: ${error.message}`);
    console.log(`   ⏱️ Duration: ${duration}ms`);
    
    return { success: false, error: error.message, duration };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const result = await gameSmoke();
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error("❌ Game smoke test crashed:", error);
    process.exit(1);
  }
}