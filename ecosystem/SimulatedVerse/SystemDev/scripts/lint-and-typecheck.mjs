#!/usr/bin/env node
/**
 * 🧹 LINT & TYPECHECK - Culture-Ship Health Analyzer
 * Zero-token local-first code quality validation
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

async function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    console.log(`🔧 Running: ${command} ${args.join(' ')}`);
    
    const child = spawn(command, args, {
      stdio: ["inherit", "pipe", "pipe"],
      ...options
    });
    
    let stdout = "";
    let stderr = "";
    
    child.stdout?.on("data", data => stdout += data.toString());
    child.stderr?.on("data", data => stderr += data.toString());
    
    child.on("close", code => {
      if (code === 0) {
        resolve({ success: true, stdout, stderr });
      } else {
        reject(new Error(`${command} failed with code ${code}\n${stderr}`));
      }
    });
    
    child.on("error", error => {
      reject(new Error(`Failed to start ${command}: ${error.message}`));
    });
  });
}

async function checkTypeScript() {
  console.log("📝 Culture-Ship: Checking TypeScript compilation...");
  
  try {
    // Check if tsconfig.json exists
    if (!fs.existsSync("tsconfig.json")) {
      console.log("⚠️ No tsconfig.json found, skipping TypeScript check");
      return { skipped: true, reason: "No tsconfig.json" };
    }
    
    await runCommand("npx", ["tsc", "--noEmit"]);
    console.log("✅ TypeScript compilation successful");
    return { success: true };
    
  } catch (error) {
    console.log("❌ TypeScript compilation failed:");
    console.log(error.message);
    return { success: false, error: error.message };
  }
}

async function checkESLint() {
  console.log("🔍 Culture-Ship: Running ESLint...");
  
  try {
    // Check if eslint config exists
    const eslintConfigs = [".eslintrc.js", ".eslintrc.json", "eslint.config.js"];
    const hasEslintConfig = eslintConfigs.some(config => fs.existsSync(config));
    
    if (!hasEslintConfig) {
      console.log("⚠️ No ESLint config found, skipping ESLint check");
      return { skipped: true, reason: "No ESLint config" };
    }
    
    await runCommand("npx", ["eslint", ".", "--ext", ".ts,.tsx,.js,.jsx"]);
    console.log("✅ ESLint passed");
    return { success: true };
    
  } catch (error) {
    console.log("❌ ESLint failed:");
    console.log(error.message);
    return { success: false, error: error.message };
  }
}

async function checkPrettier() {
  console.log("💅 Culture-Ship: Checking Prettier formatting...");
  
  try {
    // Check if prettier config exists
    const prettierConfigs = [".prettierrc", ".prettierrc.json", "prettier.config.js"];
    const hasPrettierConfig = prettierConfigs.some(config => fs.existsSync(config));
    
    if (!hasPrettierConfig) {
      console.log("⚠️ No Prettier config found, skipping Prettier check");
      return { skipped: true, reason: "No Prettier config" };
    }
    
    await runCommand("npx", ["prettier", "--check", "."]);
    console.log("✅ Prettier formatting correct");
    return { success: true };
    
  } catch (error) {
    console.log("❌ Prettier formatting issues found:");
    console.log(error.message);
    return { success: false, error: error.message };
  }
}

async function lintAndTypecheck() {
  console.log("🧹 Culture-Ship: Starting lint and typecheck cycle...");
  
  const results = {
    typescript: await checkTypeScript(),
    eslint: await checkESLint(),
    prettier: await checkPrettier(),
    timestamp: new Date().toISOString()
  };
  
  const failures = Object.values(results).filter(r => r.success === false).length;
  const skipped = Object.values(results).filter(r => r.skipped === true).length;
  
  console.log(`\n📊 Culture-Ship Lint & Typecheck Results:`);
  console.log(`   ✅ Passed: ${Object.values(results).filter(r => r.success === true).length}`);
  console.log(`   ❌ Failed: ${failures}`);
  console.log(`   ⚠️ Skipped: ${skipped}`);
  
  return results;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const results = await lintAndTypecheck();
    const hasFailures = Object.values(results).some(r => r.success === false);
    process.exit(hasFailures ? 1 : 0);
  } catch (error) {
    console.error("❌ Lint and typecheck failed:", error);
    process.exit(1);
  }
}